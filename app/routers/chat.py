"""
Rotas do chat
"""
import json
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from openai import OpenAI
import logging

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse, AttachmentOut, FeedbackBody
from app.utils import (
    get_or_create_session,
    ensure_chat_started_on_first_user_message,
    log_event,
    search_relevant_files,
    build_system_prompt,
    build_file_url,
    get_setting
)
from app.models import FileModel, ChatEventModel
from app.config import settings

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Endpoint principal do chat
    Processa mensagem do usuário e retorna resposta do bot
    """
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY não configurada no servidor."
        )
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Sessão (garante que a sessão exista)
    session_id = get_or_create_session(db, req.session_id)

    # Chat iniciado = primeira mensagem do usuário
    ensure_chat_started_on_first_user_message(db, session_id)

    # Registra pergunta do usuário
    log_event(db, session_id, "user_message", content=req.message)

    # Busca arquivos relevantes
    relevant_files = search_relevant_files(db, req.message, limit=8)
    custom_prompt = get_setting(db, "system_prompt") or ""
    system_prompt = build_system_prompt(relevant_files, custom_prompt)

    messages = [{"role": "system", "content": system_prompt}]

    if req.history:
        for m in req.history:
            messages.append({"role": m.role, "content": m.content})

    messages.append({"role": "user", "content": req.message})

    try:
        logger.info(f"Chamando OpenAI com modelo: {settings.OPENAI_MODEL}")
        logger.debug(f"API Key presente: {bool(settings.OPENAI_API_KEY)}")
        logger.debug(f"API Key prefix: {settings.OPENAI_API_KEY[:10] if settings.OPENAI_API_KEY else 'None'}...")
        
        completion = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content
        logger.info("Resposta da OpenAI recebida com sucesso")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Erro ao chamar OpenAI: {error_msg}", exc_info=True)
        
        # Mensagens de erro mais específicas
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            detail = "Erro de autenticação com a API OpenAI. Verifique se a OPENAI_API_KEY está correta no arquivo .env"
        elif "rate limit" in error_msg.lower():
            detail = "Limite de requisições da API OpenAI atingido. Tente novamente mais tarde."
        elif "insufficient_quota" in error_msg.lower():
            detail = "Cota da API OpenAI insuficiente. Verifique seu plano na OpenAI."
        else:
            detail = f"Erro ao chamar o modelo de IA: {error_msg}"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON da OpenAI: {e}")
        data = {}

    reply_text = data.get("reply", "") or ""
    raw_attachments = data.get("attachments", []) or []
    should_ask_resolution = bool(data.get("should_ask_resolution", False))
    needs_human_support = bool(data.get("needs_human_support", False))

    # Registra resposta do bot
    log_event(db, session_id, "bot_message", content=reply_text)
    
    # Se precisa de suporte humano, registra o evento
    if needs_human_support:
        log_event(db, session_id, "support_redirected")

    attachments_out: List[AttachmentOut] = []

    for att in raw_attachments:
        file_id = att.get("file_id")
        att_type = att.get("type")
        name = att.get("name")

        if file_id is None or att_type not in ("pdf", "gif"):
            continue

        try:
            file = db.query(FileModel).get(int(file_id))
            if not file or file.file_type != att_type:
                continue

            url = build_file_url(file)
            attachments_out.append(AttachmentOut(type=att_type, url=url, name=name or file.title))

            if att_type == "pdf":
                log_event(db, session_id, "pdf_sent", content=str(file.id))
            elif att_type == "gif":
                log_event(db, session_id, "gif_sent", content=str(file.id))
        except (ValueError, TypeError) as e:
            logger.warning(f"Erro ao processar anexo: {e}")
            continue

    return ChatResponse(
        reply=reply_text,
        attachments=attachments_out,
        should_ask_resolution=should_ask_resolution,
        needs_human_support=needs_human_support
    )


@router.post("/feedback")
def feedback(body: FeedbackBody, db: Session = Depends(get_db)):
    """
    Endpoint para feedback do usuário (resolveu ou não)
    Agora registra cada feedback como um evento separado, permitindo múltiplos feedbacks por sessão
    """
    from app.models import ChatSessionModel
    
    # Garante que a sessão existe (cria se não existir)
    session_id = get_or_create_session(db, body.session_id)
    s = db.query(ChatSessionModel).filter_by(session_id=session_id).first()
    
    if not s:
        # Se ainda não existir após get_or_create_session, cria manualmente
        s = ChatSessionModel(session_id=session_id)
        db.add(s)
        db.commit()
        db.refresh(s)

    # Atualiza o último feedback da sessão (para compatibilidade)
    s.resolved = 1 if body.resolved else 0
    from datetime import datetime
    s.last_activity_at = datetime.utcnow()
    
    # REGISTRA CADA FEEDBACK COMO UM EVENTO SEPARADO
    # Isso permite contar todos os feedbacks, mesmo na mesma sessão
    event_type = "feedback_yes" if body.resolved else "feedback_no"
    log_event(db, session_id, event_type)
    
    # Se não resolveu, registra qual arquivo foi enviado antes do feedback
    if not body.resolved:
        # Busca o último PDF ou GIF enviado nesta sessão
        last_pdf = db.query(ChatEventModel).filter_by(
            session_id=session_id, 
            event_type="pdf_sent"
        ).order_by(ChatEventModel.created_at.desc()).first()
        
        last_gif = db.query(ChatEventModel).filter_by(
            session_id=session_id, 
            event_type="gif_sent"
        ).order_by(ChatEventModel.created_at.desc()).first()
        
        # Determina qual foi o último arquivo enviado
        last_file = None
        if last_pdf and last_gif:
            last_file = last_pdf if last_pdf.created_at > last_gif.created_at else last_gif
        elif last_pdf:
            last_file = last_pdf
        elif last_gif:
            last_file = last_gif
        
        if last_file:
            log_event(db, session_id, "file_not_resolved", content=last_file.content)
    
    db.commit()
    return {"ok": True}

