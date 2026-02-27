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
from app.openai_status import get_status, is_available, set_status

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


@router.get("/status")
def chat_status(db: Session = Depends(get_db)):
    """
    Endpoint para verificar o status da conexão com OpenAI.
    Usado pelo frontend para verificar se o chat está disponível.
    Retorna mensagens genéricas para o usuário (sem detalhes técnicos).
    """
    status = get_status()
    
    widget_enabled = get_setting(db, "widget_enabled")
    status["widget_enabled"] = widget_enabled != "false"
    
    # Se a mensagem de erro contém informações técnicas sobre API key, substitui por genérica
    error_message = status.get("error_message")
    if error_message:
        # Filtra mensagens técnicas que não devem aparecer para o usuário
        technical_keywords = [
            "OPENAI_API_KEY",
            "api_key",
            "token.*inválido",
            "token.*não autorizado",
            "authentication.*error"
        ]
        
        # Verifica se a mensagem contém informações técnicas
        is_technical = any(
            keyword.lower() in error_message.lower() 
            for keyword in ["OPENAI_API_KEY", "api_key", "token inválido", "token não autorizado"]
        )
        
        if is_technical:
            return {
                "available": False,
                "error_message": "Serviço de IA temporariamente indisponível",
                "last_check": status.get("last_check")
            }
    
    if settings.WHATSAPP_NUMBER:
        status["whatsapp_number"] = settings.WHATSAPP_NUMBER
    
    allowed = settings.widget_allowed_origins_list
    if allowed:
        status["allowed_origins"] = allowed
    
    return status


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Endpoint principal do chat
    Processa mensagem do usuário e retorna resposta do bot
    """
    # Verifica se a conexão OpenAI está disponível
    if not is_available():
        status = get_status()
        error_msg = status.get("error_message", "Serviço de IA temporariamente indisponível")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_msg
        )
    
    if not settings.OPENAI_API_KEY:
        # Log técnico para admin, mas mensagem genérica para usuário
        logger.error("OPENAI_API_KEY não configurada no servidor")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de IA temporariamente indisponível"
        )
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Sessão (garante que a sessão exista)
    session_id = get_or_create_session(db, req.session_id)

    # Chat iniciado = primeira mensagem do usuário
    ensure_chat_started_on_first_user_message(db, session_id)

    # Busca arquivos relevantes
    relevant_files = search_relevant_files(db, req.message, limit=8)
    custom_prompt = get_setting(db, "system_prompt") or ""
    system_prompt = build_system_prompt(relevant_files, custom_prompt)

    messages = [{"role": "system", "content": system_prompt}]

    if req.history:
        for m in req.history:
            messages.append({"role": m.role, "content": m.content})

    messages.append({"role": "user", "content": req.message})

    log_event(db, session_id, "user_message", content=req.message)

    try:
        logger.info(f"Chamando OpenAI com modelo: {settings.OPENAI_MODEL}")
        # Não logar informações sensíveis em produção
        
        completion = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content
        logger.info("Resposta da OpenAI recebida com sucesso")
        
        # Registra requisição bem-sucedida
        log_event(db, session_id, "openai_request_success")
        
        # Se chegou aqui, a conexão está funcionando - atualiza status para disponível
        if not is_available():
            set_status(True, None)
            logger.info("✅ Conexão OpenAI restaurada!")
            
    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Erro ao chamar OpenAI: {error_msg}", exc_info=True)
        
        # Determina o tipo de erro para registro
        error_type = "unknown"
        if "api_key" in error_msg or "authentication" in error_msg or "invalid" in error_msg:
            error_type = "authentication"
        elif "rate limit" in error_msg:
            error_type = "rate_limit"
        elif "insufficient_quota" in error_msg or "quota" in error_msg:
            error_type = "quota"
        elif "timeout" in error_msg or "connection" in error_msg:
            error_type = "timeout"
        
        # Registra requisição com erro (inclui tipo de erro no content)
        log_event(db, session_id, "openai_request_error", content=error_type)
        
        # Atualiza o status para indisponível quando houver erro
        # Mensagens de erro mais específicas (mas genéricas para usuário)
        if error_type == "authentication":
            # Log técnico para admin
            logger.error("Erro de autenticação com API OpenAI - token inválido ou não autorizado")
            detail = "Serviço de IA temporariamente indisponível"
            set_status(False, detail)
        elif error_type == "rate_limit":
            detail = "Limite de requisições da API OpenAI atingido. Tente novamente mais tarde."
            set_status(False, detail)
        elif error_type == "quota":
            detail = "Cota da API OpenAI insuficiente. Verifique seu plano na OpenAI."
            set_status(False, detail)
        elif error_type == "timeout":
            detail = "Serviço OpenAI temporariamente indisponível"
            set_status(False, detail)
        else:
            detail = "Serviço de IA temporariamente indisponível. Tente novamente mais tarde."
            set_status(False, detail)
        
        logger.warning(f"⚠️ Status OpenAI atualizado para indisponível: {detail}")
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
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

