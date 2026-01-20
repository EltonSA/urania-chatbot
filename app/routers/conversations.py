"""
Rotas para gerenciar conversas
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, FileResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, distinct
from datetime import datetime
from io import BytesIO
import json

from app.database import get_db
from app.auth import get_current_user
from app.models import ChatSessionModel, ChatEventModel

router = APIRouter(prefix="/admin/conversations", tags=["Conversations"])


@router.get("/")
def list_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lista todas as conversas paginadas - apenas conversas com mensagens"""
    try:
        offset = (page - 1) * limit
        
        # Busca session_ids únicos que têm mensagens
        session_ids_with_messages = db.query(distinct(ChatEventModel.session_id)).filter(
            ChatEventModel.event_type.in_(["user_message", "bot_message"])
        ).all()
        
        session_ids_list = [row[0] for row in session_ids_with_messages] if session_ids_with_messages else []
        
        if not session_ids_list:
            return {
                "conversations": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 1
            }
        
        # Busca sessões que estão na lista, ordenadas por data de início (mais recente primeiro)
        sessions = db.query(ChatSessionModel).filter(
            ChatSessionModel.session_id.in_(session_ids_list)
        ).order_by(
            desc(ChatSessionModel.started_at)
        ).offset(offset).limit(limit).all()
        
        total = len(session_ids_list)
        
        conversations = []
        for session in sessions:
            try:
                # Conta mensagens da conversa
                message_count = db.query(ChatEventModel).filter(
                    ChatEventModel.session_id == session.session_id,
                    ChatEventModel.event_type.in_(["user_message", "bot_message"])
                ).count()
                
                # Busca primeira mensagem do usuário
                first_user_msg = db.query(ChatEventModel).filter(
                    ChatEventModel.session_id == session.session_id,
                    ChatEventModel.event_type == "user_message"
                ).order_by(ChatEventModel.created_at).first()
                
                preview = first_user_msg.content[:100] if first_user_msg and first_user_msg.content else "Sem mensagens"
                
                # Usa started_at como data principal, fallback para last_activity_at
                display_date = session.started_at if session.started_at else session.last_activity_at
                
                conversations.append({
                    "session_id": session.session_id,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
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
            "pages": (total + limit - 1) // limit if total > 0 else 1
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtém uma conversa específica com todas as mensagens"""
    # Verifica se a sessão existe
    session = db.query(ChatSessionModel).filter_by(session_id=session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversa não encontrada"
        )
    
    # Busca todas as mensagens da conversa
    events = db.query(ChatEventModel).filter(
        ChatEventModel.session_id == session_id,
        ChatEventModel.event_type.in_(["user_message", "bot_message"])
    ).order_by(ChatEventModel.created_at).all()
    
    messages = []
    for event in events:
        messages.append({
            "role": "user" if event.event_type == "user_message" else "assistant",
            "content": event.content or "",
            "timestamp": event.created_at.isoformat() if event.created_at else None
        })
    
    return {
        "session_id": session_id,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
        "resolved": session.resolved,
        "message_count": len(messages),
        "messages": messages
    }


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
    
    events = db.query(ChatEventModel).filter(
        ChatEventModel.session_id == session_id,
        ChatEventModel.event_type.in_(["user_message", "bot_message"])
    ).order_by(ChatEventModel.created_at).all()
    
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
    
    for event in events:
        role = "USUÁRIO" if event.event_type == "user_message" else "ASSISTENTE"
        timestamp = event.created_at.strftime('%d/%m/%Y %H:%M:%S') if event.created_at else ""
        lines.append(f"[{timestamp}] {role}:")
        lines.append(event.content or "")
        lines.append("")
    
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
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Biblioteca reportlab não instalada. Instale com: pip install reportlab"
        )
    
    session = db.query(ChatSessionModel).filter_by(session_id=session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversa não encontrada"
        )
    
    events = db.query(ChatEventModel).filter(
        ChatEventModel.session_id == session_id,
        ChatEventModel.event_type.in_(["user_message", "bot_message"])
    ).order_by(ChatEventModel.created_at).all()
    
    # Cria PDF em memória
    bio = BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='#1C8B3C',
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor='#0f172a',
        spaceAfter=6,
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 14
    
    # Conteúdo
    story = []
    
    # Cabeçalho
    story.append(Paragraph("CONVERSA DO CHATBOT", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(f"<b>ID da Conversa:</b> {session_id}", normal_style))
    started = session.started_at.strftime('%d/%m/%Y %H:%M:%S') if session.started_at else 'N/A'
    story.append(Paragraph(f"<b>Iniciada em:</b> {started}", normal_style))
    last_act = session.last_activity_at.strftime('%d/%m/%Y %H:%M:%S') if session.last_activity_at else 'N/A'
    story.append(Paragraph(f"<b>Última atividade:</b> {last_act}", normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Mensagens
    for event in events:
        role = "USUÁRIO" if event.event_type == "user_message" else "ASSISTENTE"
        timestamp = event.created_at.strftime('%d/%m/%Y %H:%M:%S') if event.created_at else ""
        color = "#1e40af" if event.event_type == "user_message" else "#1C8B3C"
        
        heading_text = f"<b><font color='{color}'>[{timestamp}] {role}</font></b>"
        story.append(Paragraph(heading_text, heading_style))
        
        content = (event.content or "").replace('\n', '<br/>')
        story.append(Paragraph(content, normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # Gera PDF
    doc.build(story)
    bio.seek(0)
    
    filename = f"conversa_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return Response(
        content=bio.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
