"""
Funções utilitárias
"""
import os
import re
import uuid
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import FileModel
from app.config import settings

logger = logging.getLogger(__name__)


def validate_openai_connection() -> Tuple[bool, Optional[str]]:
    """
    Valida a conexão com a API OpenAI usando client.models.list()
    que é gratuito (não consome tokens).
    """
    if not settings.OPENAI_API_KEY:
        return False, "Serviço de IA temporariamente indisponível"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=10)

        client.models.list()

        return True, None

    except Exception as e:
        error_msg = str(e).lower()

        if "api_key" in error_msg or "authentication" in error_msg or "invalid" in error_msg:
            return False, "Token da API OpenAI inválido ou não autorizado"
        elif "rate limit" in error_msg:
            return False, "Limite de requisições da API OpenAI atingido"
        elif "insufficient_quota" in error_msg or "quota" in error_msg:
            return False, "Cota da API OpenAI insuficiente. Verifique seu plano"
        elif "timeout" in error_msg or "connection" in error_msg:
            return False, "Serviço OpenAI temporariamente indisponível"
        else:
            return False, "Erro ao conectar com OpenAI"


def build_file_url(file: FileModel) -> str:
    """Constrói URL do arquivo"""
    if file.file_type == "pdf":
        return f"/files/pdf/{file.id}"
    if file.file_type == "gif":
        return f"/files/gif/{file.id}"
    if file.file_type == "image":
        return f"/files/image/{file.id}"
    return ""


def get_setting(db: Session, key: str) -> Optional[str]:
    """Obtém configuração do banco"""
    from app.models import SettingModel
    setting = db.query(SettingModel).filter_by(key=key).first()
    return setting.value if setting else None


def set_setting(db: Session, key: str, value: str):
    """Define configuração no banco"""
    from app.models import SettingModel
    setting = db.query(SettingModel).filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = SettingModel(key=key, value=value)
        db.add(setting)
    db.commit()


def log_audit(db: Session, action: str, category: str, detail: str = None, user: str = None, ip: str = None):
    """Registra uma ação no log de auditoria"""
    from app.models import AuditLogModel
    entry = AuditLogModel(action=action, category=category, detail=detail, user=user, ip=ip)
    db.add(entry)
    db.commit()


def get_or_create_session(db: Session, session_id: Optional[str]) -> str:
    """Obtém ou cria sessão de chat"""
    from app.models import ChatSessionModel
    
    if not session_id:
        session_id = uuid.uuid4().hex

    s = db.query(ChatSessionModel).filter_by(session_id=session_id).first()
    if not s:
        s = ChatSessionModel(session_id=session_id)
        db.add(s)
        db.commit()
        db.refresh(s)
    else:
        s.last_activity_at = datetime.utcnow()
        db.commit()

    return session_id


def log_event(db: Session, session_id: str, event_type: str, content: Optional[str] = None):
    """Registra evento no chat - garante que seja salvo mesmo em caso de erro"""
    from app.models import ChatEventModel, ChatSessionModel
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        ev = ChatEventModel(session_id=session_id, event_type=event_type, content=content)
        db.add(ev)

        s = db.query(ChatSessionModel).filter_by(session_id=session_id).first()
        if s:
            s.last_activity_at = datetime.utcnow()

        db.commit()
    except Exception as e:
        logger.error(f"Erro ao salvar evento {event_type} para sessão {session_id}: {e}", exc_info=True)
        db.rollback()
        # Tenta novamente
        try:
            ev = ChatEventModel(session_id=session_id, event_type=event_type, content=content)
            db.add(ev)
            db.commit()
        except Exception as e2:
            logger.error(f"Erro ao tentar salvar evento novamente: {e2}", exc_info=True)
            db.rollback()


def search_relevant_files(db: Session, query: str, limit: int = 8) -> List[FileModel]:
    """Busca arquivos relevantes baseado na query"""
    words = re.split(r"\W+", (query or "").lower())
    words = [w for w in words if len(w) >= 3]

    query_db = db.query(FileModel)

    if not words:
        return query_db.order_by(FileModel.created_at.desc()).limit(limit).all()

    conditions = []
    for w in words:
        pattern = f"%{w}%"
        conditions.append(FileModel.title.ilike(pattern))
        conditions.append(FileModel.tags.ilike(pattern))
        conditions.append(FileModel.description.ilike(pattern))

    files = (
        query_db
        .filter(or_(*conditions))
        .order_by(FileModel.created_at.desc())
        .limit(limit)
        .all()
    )

    if not files:
        files = query_db.order_by(FileModel.created_at.desc()).limit(limit).all()

    return files


def build_system_prompt(files: List[FileModel], custom_prompt: str = "") -> str:
    """Constrói prompt do sistema para o OpenAI"""
    files_description = []
    for f in files:
        desc = (f.description or "").strip()
        desc_part = f', descrição: "{desc}"' if desc else ""
        group_part = f", grupo: {f.group_id}" if f.group_id else ""
        files_description.append(
            f'- ID: {f.id}, tipo: {f.file_type}, título: "{f.title or f.original_name}", tags: {f.tags or ""}{desc_part}{group_part}'
        )
    files_block = "\n".join(files_description) if files_description else "Nenhum arquivo relevante encontrado."

    base_rules = f"""
Você é um assistente de suporte que atende clientes no site.

Você tem acesso a materiais (PDF, GIF animado e imagens PNG/JPG/WebP) que podem ser enviados ao usuário.
Cada material tem: ID, tipo (pdf/gif/image), título, tags e opcionalmente uma descrição (use a descrição para contextualizar e para redigir a resposta em "reply" quando fizer sentido).
Vários itens podem compartilhar o mesmo "grupo" (apenas imagens estáticas e GIFs; PDF não entra em grupo): cada item do grupo tem seu próprio ID e sua própria descrição no cadastro.

MATERIAIS DISPONÍVEIS:
{files_block}

Sua resposta DEVE ser SEMPRE um JSON válido.

Quando for enviar uma ou mais imagens (passo a passo ou grupo), use OBRIGATORIAMENTE "reply_steps". O cliente exibe na ordem: texto do passo → pausa → imagem daquele passo → pausa → próximo passo (e assim por diante).

{{
  "reply": "opcional: só uma saudação ou contexto muito curto; NÃO coloque aqui o passo a passo nem antecipe imagens",
  "reply_steps": [
    {{
      "text": "Passo 1 — explicação COM SUAS PRÓPRIAS PALAVRAS (descrição do cadastro = só roteiro factual, não copiar literalmente).",
      "attachments": [ {{ "type": "image", "file_id": ID_DA_IMAGEM_1 }} ]
    }},
    {{
      "text": "Passo 2 — próxima explicação com suas palavras.",
      "attachments": [ {{ "type": "image", "file_id": ID_DA_IMAGEM_2 }} ]
    }}
  ],
  "attachments": [],
  "should_ask_resolution": true ou false
}}

Regras OBRIGATÓRIAS para reply_steps:
- Cada elemento do array reply_steps = EXATAMENTE UM objeto em "attachments" (uma única imagem/PDF/GIF por passo). NUNCA coloque dois ou mais file_id no mesmo passo.
- NUNCA agrupe todas as imagens no primeiro passo. A ordem correta é: passo1 com texto1 + só imagem1, depois passo2 com texto2 + só imagem2, etc.
- Itens do mesmo grupo (imagem ou GIF): cada um tem seu próprio ID — use um reply_steps por item, na ordem (1, 2, 3…), cada "text" alinhado à descrição daquele ID; em "attachments" use "type": "image" ou "gif" conforme o material.
- O campo "reply" não substitui os textos dos passos; não use "reply" para explicar passos que têm imagens — use o "text" de cada passo.

Quando for apenas um PDF, um GIF ou um caso simples sem sequência, pode usar o formato clássico (sem reply_steps):

{{
  "reply": "texto da resposta ao usuário",
  "attachments": [ {{ "type": "gif" ou "pdf" ou "image", "file_id": ID, "name": "opcional" }} ],
  "reply_steps": [],
  "should_ask_resolution": true ou false
}}

Regras IMPORTANTES:
- Se usar "reply_steps", deixe "attachments" como lista vazia [] na raiz.
- Se não precisar enviar mídia, use "attachments": [] e "reply_steps": [].
- Só use IDs que estejam na lista de materiais disponíveis.
- Use GIFs quando ajudarem a explicar (passo a passo visual).
- Use imagens (type "image") para ilustrações estáticas; use PDFs para materiais mais longos.
- NUNCA saia do formato JSON.

Regra do should_ask_resolution:
- Use true APENAS quando a mensagem do usuário for uma dúvida/solicitação de suporte.
- Use false quando for cumprimento, conversa, agradecimento, teste de mensagem, ou fora de suporte.
- Se estiver em dúvida, prefira false.

IMPORTANTE - Direcionamento para Suporte Humano:
- Se o usuário insistir em falar com um humano, atendente, suporte humano, ou pessoa real, você DEVE:
  1. Oferecer educadamente direcionar para o suporte via WhatsApp
  2. Incluir no JSON: "needs_human_support": true
  3. Na resposta, mencione que pode ajudar via WhatsApp no número disponível
- Se o usuário pedir para falar com humano mais de uma vez na conversa, SEMPRE direcione para suporte.
""".strip()

    if custom_prompt and custom_prompt.strip():
        return custom_prompt.strip() + "\n\n" + base_rules
    return base_rules


def ensure_chat_started_on_first_user_message(db: Session, session_id: str):
    """
    Garante que 'chat_started' seja gravado UMA ÚNICA vez por sessão,
    exatamente na primeira mensagem do usuário.
    """
    from app.models import ChatEventModel
    
    first_user_msg = (
        db.query(ChatEventModel)
        .filter_by(session_id=session_id, event_type="user_message")
        .first()
    )
    if not first_user_msg:
        log_event(db, session_id, "chat_started")


def expand_attachment_files(db: Session, file: FileModel) -> List[FileModel]:
    """Uma entrada de anexo vira todos os itens do mesmo grupo (imagem ou GIF), se houver group_id."""
    if file.group_id and file.file_type in ("image", "gif"):
        return (
            db.query(FileModel)
            .filter(
                FileModel.group_id == file.group_id,
                FileModel.file_type.in_(("image", "gif")),
            )
            .order_by(FileModel.id.asc())
            .all()
        )
    return [file]


def ensure_upload_dirs():
    """Garante que os diretórios de upload existam"""
    upload_dir = settings.upload_dir_path
    pdf_dir = upload_dir / "pdfs"
    gif_dir = upload_dir / "gifs"
    image_dir = upload_dir / "images"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    gif_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    return str(pdf_dir), str(gif_dir), str(image_dir)


