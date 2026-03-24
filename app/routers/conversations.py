"""
Rotas para gerenciar conversas
"""
import logging
import os
from enum import Enum
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime
from io import BytesIO

from app.database import get_db
from app.auth import get_current_user
from app.models import ChatSessionModel, ChatEventModel, FileModel
from app.utils import build_file_url
from app.date_range import parse_stats_date_range

router = APIRouter(prefix="/admin/conversations", tags=["Conversations"])
logger = logging.getLogger(__name__)


class SatisfactionFilter(str, Enum):
    """Filtro por resposta ao cartão de satisfação (resolveu / não / sem resposta)."""

    all = "all"
    yes = "yes"
    no = "no"
    none = "none"


def _reportlab_register_vera_font() -> str:
    """
    Registra a TTF Vera (vem com o pacote reportlab) para suportar português e Unicode no PDF.
    Retorna o nome da família a usar nos estilos ('Vera' ou 'Helvetica' se falhar).
    """
    try:
        import reportlab
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.fonts import addMapping
    except ImportError:
        return "Helvetica"
    if "Vera" in pdfmetrics.getRegisteredFontNames():
        return "Vera"
    fd = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
    vera = os.path.join(fd, "Vera.ttf")
    vera_bd = os.path.join(fd, "VeraBd.ttf")
    if not os.path.isfile(vera):
        logger.warning("reportlab: Vera.ttf não encontrado em %s", fd)
        return "Helvetica"
    try:
        pdfmetrics.registerFont(TTFont("Vera", vera))
        if os.path.isfile(vera_bd):
            pdfmetrics.registerFont(TTFont("VeraBd", vera_bd))
            addMapping("Vera", 0, 0, "Vera")
            addMapping("Vera", 1, 0, "VeraBd")
        return "Vera"
    except Exception as e:
        logger.warning("reportlab: falha ao registrar Vera: %s", e)
        return "Helvetica"

# Rótulos para linha do tempo / exportação
EVENT_LABELS_PT: Dict[str, str] = {
    "user_message": "Mensagem do usuário",
    "bot_message": "Resposta da IA",
    "chat_started": "Conversa iniciada",
    "openai_request_success": "Requisição à IA concluída",
    "openai_request_error": "Erro na requisição à IA",
    "pdf_sent": "PDF enviado ao usuário",
    "gif_sent": "GIF enviado ao usuário",
    "image_sent": "Imagem enviada ao usuário",
    "feedback_yes": "Feedback: resolveu (sim)",
    "feedback_no": "Feedback: não resolveu",
    "feedback_support": "Solicitou suporte",
    "support_redirected": "Direcionamento a suporte humano",
    "file_not_resolved": "Arquivo associado a 'não resolveu'",
    "file_resolved": "Arquivo associado a 'resolveu (sim)'",
}

MEDIA_EVENT_TYPES = frozenset({"pdf_sent", "gif_sent", "image_sent"})

_EVENT_TO_TYPE = {"pdf_sent": "pdf", "gif_sent": "gif", "image_sent": "image"}


def _parse_file_id(content: Optional[str]) -> Optional[int]:
    if not content:
        return None
    try:
        return int(str(content).strip())
    except ValueError:
        return None


def _attachment_payload(db: Session, file_id: int) -> Optional[Dict[str, Any]]:
    frow = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not frow:
        return None
    return {
        "file_id": frow.id,
        "type": frow.file_type,
        "title": frow.title or frow.original_name or f"Arquivo #{frow.id}",
        "url": build_file_url(frow),
    }


def build_thread_messages(db: Session, session_id: str) -> List[Dict[str, Any]]:
    """
    Monta o fio da conversa: cada resposta do assistente pode incluir anexos
    (PDF / GIF / imagem) registados logo após o evento bot_message.
    """
    types = ("user_message", "bot_message", "pdf_sent", "gif_sent", "image_sent")
    events = (
        db.query(ChatEventModel)
        .filter(
            ChatEventModel.session_id == session_id,
            ChatEventModel.event_type.in_(types),
        )
        .order_by(ChatEventModel.created_at)
        .all()
    )
    out: List[Dict[str, Any]] = []
    for ev in events:
        ts = ev.created_at.isoformat() if ev.created_at else None
        if ev.event_type == "user_message":
            out.append(
                {
                    "role": "user",
                    "content": ev.content or "",
                    "timestamp": ts,
                    "attachments": [],
                }
            )
        elif ev.event_type == "bot_message":
            out.append(
                {
                    "role": "assistant",
                    "content": ev.content or "",
                    "timestamp": ts,
                    "attachments": [],
                }
            )
        elif ev.event_type in MEDIA_EVENT_TYPES:
            fid = _parse_file_id(ev.content)
            if fid is None:
                continue
            payload = _attachment_payload(db, fid)
            if not payload:
                payload = {
                    "file_id": fid,
                    "type": _EVENT_TO_TYPE.get(ev.event_type, "file"),
                    "title": f"Arquivo #{fid} (não encontrado)",
                    "url": None,
                }
            if out and out[-1]["role"] == "assistant":
                out[-1]["attachments"].append(payload)
            else:
                out.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "timestamp": ts,
                        "attachments": [payload],
                    }
                )
    return out


def _format_ts_br(iso_ts: Optional[str]) -> str:
    if not iso_ts:
        return ""
    try:
        d = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        return d.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return iso_ts


def _timeline_row_dict(db: Session, ev: ChatEventModel) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "event_type": ev.event_type,
        "label": EVENT_LABELS_PT.get(ev.event_type, ev.event_type),
        "content": ev.content,
        "created_at": ev.created_at.isoformat() if ev.created_at else None,
    }
    if ev.event_type in MEDIA_EVENT_TYPES:
        fid = _parse_file_id(ev.content)
        if fid is not None:
            p = _attachment_payload(db, fid)
            if p:
                row["media"] = p
    return row


def _audit_line_content(db: Session, ev: ChatEventModel) -> str:
    base = (ev.content or "").replace("\n", " ").strip()
    if ev.event_type in MEDIA_EVENT_TYPES:
        fid = _parse_file_id(ev.content)
        if fid is not None:
            p = _attachment_payload(db, fid)
            if p:
                u = p.get("url") or ""
                return f'{p["title"]} ({p["type"]})' + (f" — {u}" if u else "")
    return base


@router.get("/")
def list_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    satisfaction: SatisfactionFilter = Query(
        SatisfactionFilter.all,
        description="all=todas | yes=Resolveu (Sim) | no=Não resolveu | none=Sem feedback",
    ),
    date_from: Optional[str] = Query(
        None,
        description="Data inicial (YYYY-MM-DD, UTC). Com date_to omite = desde 1970-01-01.",
    ),
    date_to: Optional[str] = Query(
        None,
        description="Data final (YYYY-MM-DD, UTC), inclusiva. Com date_from omite = até hoje (UTC).",
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lista conversas paginadas (com mensagens), com filtros por satisfação e por período (mensagens no intervalo)."""
    range_start, range_end = parse_stats_date_range(date_from, date_to)
    list_meta = (
        {
            "filtered": True,
            "date_from": range_start.strftime("%Y-%m-%d"),
            "date_to": range_end.strftime("%Y-%m-%d"),
        }
        if range_start is not None
        else {"filtered": False, "date_from": None, "date_to": None}
    )

    try:
        offset = (page - 1) * limit

        subq_base = (
            db.query(
                ChatEventModel.session_id.label("sid"),
                func.max(ChatEventModel.created_at).label("last_at"),
            )
            .filter(ChatEventModel.event_type.in_(["user_message", "bot_message"]))
        )
        if range_start is not None:
            subq_base = subq_base.filter(ChatEventModel.created_at >= range_start)
        if range_end is not None:
            subq_base = subq_base.filter(ChatEventModel.created_at <= range_end)
        subq = subq_base.group_by(ChatEventModel.session_id).subquery()

        count_q = (
            db.query(func.count(ChatSessionModel.id))
            .select_from(ChatSessionModel)
            .join(subq, ChatSessionModel.session_id == subq.c.sid)
        )
        if satisfaction == SatisfactionFilter.yes:
            count_q = count_q.filter(ChatSessionModel.resolved == 1)
        elif satisfaction == SatisfactionFilter.no:
            count_q = count_q.filter(ChatSessionModel.resolved == 0)
        elif satisfaction == SatisfactionFilter.none:
            count_q = count_q.filter(ChatSessionModel.resolved.is_(None))

        total = count_q.scalar() or 0

        if total == 0:
            return {
                "conversations": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 1,
                "satisfaction": satisfaction.value,
                **list_meta,
            }

        sessions_q = (
            db.query(ChatSessionModel)
            .join(subq, ChatSessionModel.session_id == subq.c.sid)
        )
        if satisfaction == SatisfactionFilter.yes:
            sessions_q = sessions_q.filter(ChatSessionModel.resolved == 1)
        elif satisfaction == SatisfactionFilter.no:
            sessions_q = sessions_q.filter(ChatSessionModel.resolved == 0)
        elif satisfaction == SatisfactionFilter.none:
            sessions_q = sessions_q.filter(ChatSessionModel.resolved.is_(None))

        sessions = (
            sessions_q.order_by(desc(subq.c.last_at), desc(ChatSessionModel.started_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        page_ids = [s.session_id for s in sessions]
        last_msg_map = {}
        if page_ids:
            last_q = (
                db.query(ChatEventModel.session_id, func.max(ChatEventModel.created_at))
                .filter(
                    ChatEventModel.session_id.in_(page_ids),
                    ChatEventModel.event_type.in_(["user_message", "bot_message"]),
                )
            )
            if range_start is not None:
                last_q = last_q.filter(ChatEventModel.created_at >= range_start)
            if range_end is not None:
                last_q = last_q.filter(ChatEventModel.created_at <= range_end)
            for sid, lat in last_q.group_by(ChatEventModel.session_id).all():
                last_msg_map[sid] = lat

        conversations = []
        for session in sessions:
            try:
                mc_q = db.query(ChatEventModel).filter(
                    ChatEventModel.session_id == session.session_id,
                    ChatEventModel.event_type.in_(["user_message", "bot_message"]),
                )
                if range_start is not None:
                    mc_q = mc_q.filter(ChatEventModel.created_at >= range_start)
                if range_end is not None:
                    mc_q = mc_q.filter(ChatEventModel.created_at <= range_end)
                message_count = mc_q.count()

                first_q = db.query(ChatEventModel).filter(
                    ChatEventModel.session_id == session.session_id,
                    ChatEventModel.event_type == "user_message",
                )
                if range_start is not None:
                    first_q = first_q.filter(ChatEventModel.created_at >= range_start)
                if range_end is not None:
                    first_q = first_q.filter(ChatEventModel.created_at <= range_end)
                first_user_msg = first_q.order_by(ChatEventModel.created_at).first()
                
                preview = first_user_msg.content[:100] if first_user_msg and first_user_msg.content else "Sem mensagens"
                
                last_msg_at = last_msg_map.get(session.session_id)
                display_date = last_msg_at or session.last_activity_at or session.started_at

                conversations.append({
                    "session_id": session.session_id,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
                    "last_message_at": last_msg_at.isoformat() if last_msg_at else None,
                    "display_date": display_date.isoformat() if display_date else None,
                    "message_count": message_count,
                    "preview": preview,
                    "resolved": session.resolved
                })
            except Exception as e:
                # Log erro mas continua com outras conversas
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erro ao processar conversa {session.session_id}: {e}")
                continue
        
        return {
            "conversations": conversations,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total > 0 else 1,
            "satisfaction": satisfaction.value,
            **list_meta,
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao listar conversas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar conversas: {str(e)}"
        )


@router.get("/{session_id}")
def get_conversation(
    session_id: str,
    include_timeline: bool = Query(False, description="Inclui todos os eventos (mídias, feedback, erros de IA, etc.)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtém uma conversa: mensagens usuário/IA e, opcionalmente, linha do tempo completa."""
    session = db.query(ChatSessionModel).filter_by(session_id=session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversa não encontrada"
        )

    messages = build_thread_messages(db, session_id)

    out = {
        "session_id": session_id,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
        "resolved": session.resolved,
        "message_count": len(messages),
        "messages": messages,
    }

    if include_timeline:
        all_ev = (
            db.query(ChatEventModel)
            .filter_by(session_id=session_id)
            .order_by(ChatEventModel.created_at)
            .all()
        )
        out["timeline"] = [_timeline_row_dict(db, ev) for ev in all_ev]

    return out


@router.get("/{session_id}/export/txt")
def export_conversation_txt(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Exporta conversa em formato TXT"""
    session = db.query(ChatSessionModel).filter_by(session_id=session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversa não encontrada"
        )
    
    thread = build_thread_messages(db, session_id)

    # Gera conteúdo TXT
    lines = []
    lines.append("=" * 60)
    lines.append("CONVERSA DO CHATBOT")
    lines.append("=" * 60)
    lines.append(f"ID da Conversa: {session_id}")
    lines.append(f"Iniciada em: {session.started_at.strftime('%d/%m/%Y %H:%M:%S') if session.started_at else 'N/A'}")
    lines.append(f"Última atividade: {session.last_activity_at.strftime('%d/%m/%Y %H:%M:%S') if session.last_activity_at else 'N/A'}")
    lines.append("=" * 60)
    lines.append("")

    for msg in thread:
        role = "USUÁRIO" if msg["role"] == "user" else "ASSISTENTE"
        timestamp = _format_ts_br(msg.get("timestamp"))
        lines.append(f"[{timestamp}] {role}:")
        if msg.get("content"):
            lines.append(msg["content"])
        for att in msg.get("attachments") or []:
            t = (att.get("type") or "arquivo").upper()
            title = att.get("title") or ""
            url = att.get("url") or ""
            lines.append(f"  ▸ {t}: {title}" + (f" — {url}" if url else ""))
        lines.append("")

    lines.append("=" * 60)
    lines.append("REGISTRO COMPLETO (auditoria — todos os eventos)")
    lines.append("=" * 60)
    lines.append("")
    all_events = (
        db.query(ChatEventModel)
        .filter_by(session_id=session_id)
        .order_by(ChatEventModel.created_at)
        .all()
    )
    for ev in all_events:
        ts = ev.created_at.strftime('%d/%m/%Y %H:%M:%S') if ev.created_at else ""
        label = EVENT_LABELS_PT.get(ev.event_type, ev.event_type)
        body = _audit_line_content(db, ev)
        lines.append(f"[{ts}] {label}" + (f": {body}" if body else ""))

    content = "\n".join(lines)
    
    # Cria arquivo em memória
    bio = BytesIO()
    bio.write(content.encode('utf-8'))
    bio.seek(0)
    
    filename = f"conversa_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    return Response(
        content=bio.read(),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{session_id}/export/pdf")
def export_conversation_pdf(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Exporta conversa em formato PDF"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Biblioteca reportlab não instalada no servidor. Execute: pip install reportlab",
        )

    session = db.query(ChatSessionModel).filter_by(session_id=session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversa não encontrada"
        )
    
    thread = build_thread_messages(db, session_id)

    font = _reportlab_register_vera_font()

    # Cria PDF em memória
    bio = BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Estilos (fonte TrueType evita erro com acentos em Helvetica embutida)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ConvPdfTitle',
        parent=styles['Heading1'],
        fontName=font,
        fontSize=16,
        textColor='#1C8B3C',
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        'ConvPdfHeading',
        parent=styles['Heading2'],
        fontName=font,
        fontSize=12,
        textColor='#0f172a',
        spaceAfter=6,
    )
    normal_style = ParagraphStyle(
        'ConvPdfNormal',
        parent=styles['Normal'],
        fontName=font,
        fontSize=10,
        leading=14,
    )
    
    # Conteúdo
    story = []
    
    # Cabeçalho
    story.append(Paragraph("CONVERSA DO CHATBOT", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    def _esc_xml(s: str) -> str:
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    story.append(Paragraph(f"<b>ID da Conversa:</b> {_esc_xml(session_id)}", normal_style))
    started = session.started_at.strftime('%d/%m/%Y %H:%M:%S') if session.started_at else 'N/A'
    story.append(Paragraph(f"<b>Iniciada em:</b> {started}", normal_style))
    last_act = session.last_activity_at.strftime('%d/%m/%Y %H:%M:%S') if session.last_activity_at else 'N/A'
    story.append(Paragraph(f"<b>Última atividade:</b> {last_act}", normal_style))
    story.append(Spacer(1, 0.3*inch))

    # Mensagens (texto + anexos enviados pela IA)
    for msg in thread:
        role = "USUÁRIO" if msg["role"] == "user" else "ASSISTENTE"
        timestamp = _format_ts_br(msg.get("timestamp"))
        color = "#1e40af" if msg["role"] == "user" else "#1C8B3C"

        heading_text = f"<b><font color='{color}'>[{timestamp}] {role}</font></b>"
        story.append(Paragraph(heading_text, heading_style))

        body = _esc_xml(msg.get("content") or "").replace("\n", "<br/>")
        if body:
            story.append(Paragraph(body, normal_style))
        for att in msg.get("attachments") or []:
            t = _esc_xml((att.get("type") or "").upper())
            title = _esc_xml(att.get("title") or "")
            url = _esc_xml(att.get("url") or "")
            line = f"• <b>{t}</b>: {title}"
            if url:
                line += f" — {url}"
            story.append(Paragraph(line, normal_style))
        story.append(Spacer(1, 0.2*inch))

    story.append(Spacer(1, 0.25*inch))
    story.append(Paragraph("<b>Registro completo (auditoria)</b>", heading_style))
    story.append(Spacer(1, 0.1*inch))
    all_events = (
        db.query(ChatEventModel)
        .filter_by(session_id=session_id)
        .order_by(ChatEventModel.created_at)
        .all()
    )
    for ev in all_events:
        ts = ev.created_at.strftime('%d/%m/%Y %H:%M:%S') if ev.created_at else ""
        label = EVENT_LABELS_PT.get(ev.event_type, ev.event_type)
        raw_body = _audit_line_content(db, ev)
        body = _esc_xml(raw_body).replace("\n", "<br/>")
        line = f"<b><font color='#64748b'>[{ts}]</font></b> {_esc_xml(label)}"
        if body:
            line += f": {body}"
        story.append(Paragraph(line, normal_style))
        story.append(Spacer(1, 0.08*inch))
    
    try:
        doc.build(story)
    except Exception as e:
        logger.exception("Falha ao gerar PDF da conversa %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao montar o PDF: {str(e)}",
        ) from e

    bio.seek(0)
    
    filename = f"conversa_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return Response(
        content=bio.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
