"""
Rotas do chat
"""
import json
from typing import List, Set
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from openai import OpenAI
import logging

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse, AttachmentOut, FeedbackBody, ReplyStepOut
from app.utils import (
    get_or_create_session,
    ensure_chat_started_on_first_user_message,
    log_event,
    search_relevant_files,
    build_system_prompt,
    build_file_url,
    get_setting,
    expand_attachment_files,
)
from app.models import FileModel, ChatEventModel
from app.config import settings
from app.openai_status import get_status, is_available, set_status

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


def _resolve_raw_attachments(
    db: Session,
    session_id: str,
    raw_attachments: list,
    seen_attachment_ids: Set[int],
    *,
    expand_groups: bool = True,
) -> List[AttachmentOut]:
    """
    expand_groups: em reply_steps deve ser False — cada passo é um único arquivo;
    senão um file_id de grupo (imagem/GIF) viraria várias mídias no mesmo passo.
    """
    out: List[AttachmentOut] = []
    for att in raw_attachments:
        if not isinstance(att, dict):
            continue
        file_id = att.get("file_id")
        att_type = att.get("type")
        name = att.get("name")
        if file_id is None or att_type not in ("pdf", "gif", "image"):
            continue
        try:
            file = db.query(FileModel).get(int(file_id))
            if not file or file.file_type != att_type:
                continue
            expanded = expand_attachment_files(db, file) if expand_groups else [file]
            for i, frow in enumerate(expanded):
                if frow.id in seen_attachment_ids:
                    continue
                seen_attachment_ids.add(frow.id)
                url = build_file_url(frow)
                disp_name = (name or frow.title) if i == 0 else frow.title
                out.append(AttachmentOut(type=frow.file_type, url=url, name=disp_name))
                if frow.file_type == "pdf":
                    log_event(db, session_id, "pdf_sent", content=str(frow.id))
                elif frow.file_type == "gif":
                    log_event(db, session_id, "gif_sent", content=str(frow.id))
                elif frow.file_type == "image":
                    log_event(db, session_id, "image_sent", content=str(frow.id))
        except (ValueError, TypeError) as e:
            logger.warning("Erro ao processar anexo: %s", e)
            continue
    return out


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

    status["satisfaction_support_enabled"] = get_setting(db, "satisfaction_support_button") != "false"

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
    raw_reply_steps = data.get("reply_steps")
    should_ask_resolution = bool(data.get("should_ask_resolution", False))
    needs_human_support = bool(data.get("needs_human_support", False))

    seen_ids: Set[int] = set()
    reply_steps_out: List[ReplyStepOut] = []

    if isinstance(raw_reply_steps, list) and len(raw_reply_steps) > 0:
        for step in raw_reply_steps:
            if not isinstance(step, dict):
                continue
            st_text = step.get("text")
            st_text = (st_text if isinstance(st_text, str) else "") or ""
            st_raw = step.get("attachments")
            if not isinstance(st_raw, list):
                st_raw = []
            # Um anexo por passo (texto → imagem → texto → imagem no cliente)
            if len(st_raw) > 1:
                st_raw = st_raw[:1]
            resolved = _resolve_raw_attachments(
                db, session_id, st_raw, seen_ids, expand_groups=False
            )
            if st_text.strip() or resolved:
                reply_steps_out.append(ReplyStepOut(text=st_text.strip(), attachments=resolved))

    attachments_out: List[AttachmentOut] = []
    if reply_steps_out:
        attachments_out = []
    else:
        attachments_out = _resolve_raw_attachments(db, session_id, raw_attachments, seen_ids)

    step_texts = [s.text for s in reply_steps_out if s.text]
    log_content_parts = [p for p in [reply_text.strip()] + step_texts if p]
    log_event(db, session_id, "bot_message", content="\n\n".join(log_content_parts) if log_content_parts else reply_text)

    if needs_human_support:
        log_event(db, session_id, "support_redirected")

    return ChatResponse(
        reply=reply_text,
        attachments=attachments_out,
        reply_steps=reply_steps_out,
        should_ask_resolution=should_ask_resolution,
        needs_human_support=needs_human_support,
    )


@router.post("/feedback")
def feedback(body: FeedbackBody, db: Session = Depends(get_db)):
    """
    Endpoint para feedback do usuário (resolveu ou não)
    Agora registra cada feedback como um evento separado, permitindo múltiplos feedbacks por sessão
    """
    from app.models import ChatSessionModel
    from datetime import datetime

    session_id = get_or_create_session(db, body.session_id)
    s = db.query(ChatSessionModel).filter_by(session_id=session_id).first()

    if not s:
        s = ChatSessionModel(session_id=session_id)
        db.add(s)
        db.commit()
        db.refresh(s)

    if body.action == "support":
        if get_setting(db, "satisfaction_support_button") == "false":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solicitação de suporte por este botão está desativada.",
            )
        s.resolved = None
        s.last_activity_at = datetime.utcnow()
        log_event(db, session_id, "feedback_support")
        log_event(db, session_id, "support_redirected")
        db.commit()
        return {"ok": True}

    s.resolved = 1 if body.resolved else 0
    s.last_activity_at = datetime.utcnow()

    event_type = "feedback_yes" if body.resolved else "feedback_no"
    log_event(db, session_id, event_type)

    last_pdf = (
        db.query(ChatEventModel)
        .filter_by(session_id=session_id, event_type="pdf_sent")
        .order_by(ChatEventModel.created_at.desc())
        .first()
    )
    last_gif = (
        db.query(ChatEventModel)
        .filter_by(session_id=session_id, event_type="gif_sent")
        .order_by(ChatEventModel.created_at.desc())
        .first()
    )
    last_image = (
        db.query(ChatEventModel)
        .filter_by(session_id=session_id, event_type="image_sent")
        .order_by(ChatEventModel.created_at.desc())
        .first()
    )
    candidates = [x for x in (last_pdf, last_gif, last_image) if x is not None]
    last_file = max(candidates, key=lambda x: x.created_at) if candidates else None

    if last_file:
        if body.resolved:
            log_event(db, session_id, "file_resolved", content=last_file.content)
        else:
            log_event(db, session_id, "file_not_resolved", content=last_file.content)

    db.commit()
    return {"ok": True}

