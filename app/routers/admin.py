"""
Rotas administrativas
"""
from io import BytesIO
from typing import List
from collections import Counter
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from openpyxl import Workbook

from app.database import get_db
from app.schemas import PromptBody
from app.auth import get_current_user
from app.utils import get_setting, set_setting, ensure_upload_dirs
from app.models import ChatEventModel, ChatSessionModel, FileModel, FileModel
from app.config import settings
import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/prompt")
def get_prompt(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtém prompt customizado. Requer autenticação"""
    import logging
    logger = logging.getLogger(__name__)
    
    prompt = get_setting(db, "system_prompt") or ""
    logger.info(f"Prompt obtido do banco: {len(prompt)} caracteres")
    
    return {"prompt": prompt}


@router.put("/prompt")
def save_prompt(
    body: PromptBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Salva prompt customizado. Requer autenticação"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Salvando prompt: {len(body.prompt)} caracteres")
    set_setting(db, "system_prompt", body.prompt or "")
    
    # Verifica se foi salvo
    saved_prompt = get_setting(db, "system_prompt")
    logger.info(f"Prompt salvo confirmado: {len(saved_prompt) if saved_prompt else 0} caracteres")
    
    return {"ok": True}


@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Estatísticas do sistema. Requer autenticação"""
    total_messages = (
        db.query(ChatEventModel)
        .filter(ChatEventModel.event_type.in_(["user_message", "bot_message"]))
        .count()
    )

    # Chats iniciados = sessões únicas que tiveram evento chat_started
    chats_initiated = (
        db.query(distinct(ChatEventModel.session_id))
        .filter(ChatEventModel.event_type == "chat_started")
        .count()
    )

    pdfs_sent = db.query(ChatEventModel).filter_by(event_type="pdf_sent").count()
    gifs_sent = db.query(ChatEventModel).filter_by(event_type="gif_sent").count()

    # Conta feedbacks pelos eventos (permite múltiplos feedbacks por sessão)
    resolved_yes = db.query(ChatEventModel).filter_by(event_type="feedback_yes").count()
    resolved_no = db.query(ChatEventModel).filter_by(event_type="feedback_no").count()
    resolved_total = resolved_yes + resolved_no
    
    # Detratores = sessões que tiveram chat_started mas nunca deram feedback
    sessions_with_feedback_ids = [
        row[0] for row in db.query(distinct(ChatEventModel.session_id)).filter(
            ChatEventModel.event_type.in_(["feedback_yes", "feedback_no"])
        ).all()
    ]
    sessions_started_ids = [
        row[0] for row in db.query(distinct(ChatEventModel.session_id)).filter(
            ChatEventModel.event_type == "chat_started"
        ).all()
    ]
    detractors = len([s for s in sessions_started_ids if s not in sessions_with_feedback_ids])
    
    resolution_rate = round((resolved_yes / resolved_total) * 100, 1) if resolved_total else 0

    # Arquivos que não resolveram (quando usuário clicou "Não")
    from app.utils import build_file_url
    files_not_resolved = db.query(ChatEventModel).filter_by(event_type="file_not_resolved").all()
    files_not_resolved_stats = {}
    for event in files_not_resolved:
        file_id = event.content
        if file_id:
            try:
                file = db.query(FileModel).get(int(file_id))
                if file and file.file_type:
                    key = f"{file.file_type}_{file.id}"
                    if key not in files_not_resolved_stats:
                        files_not_resolved_stats[key] = {
                            "file_id": file.id,
                            "file_type": str(file.file_type).lower(),
                            "title": str(file.title or file.original_name or "Sem título"),
                            "url": build_file_url(file),
                            "count": 0
                        }
                    files_not_resolved_stats[key]["count"] += 1
            except (ValueError, TypeError, AttributeError):
                continue
    
    files_not_resolved_list = sorted(
        files_not_resolved_stats.values(), 
        key=lambda x: x["count"], 
        reverse=True
    )[:10]

    # Direcionamentos para suporte
    support_redirected = db.query(ChatEventModel).filter_by(event_type="support_redirected").count()

    # Métricas de comunicação com OpenAI
    openai_requests_success = db.query(ChatEventModel).filter_by(event_type="openai_request_success").count()
    openai_requests_error = db.query(ChatEventModel).filter_by(event_type="openai_request_error").count()
    openai_requests_total = openai_requests_success + openai_requests_error
    openai_error_rate = round((openai_requests_error / openai_requests_total) * 100, 2) if openai_requests_total > 0 else 0.0

    # Perguntas mais frequentes - categorizadas por IA
    from app.utils import categorize_questions
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        user_msgs = db.query(ChatEventModel).filter_by(event_type="user_message").all()
        texts = [m.content.strip() for m in user_msgs if m.content and m.content.strip()]
        
        # Categoriza perguntas similares
        top_questions = categorize_questions(texts)
        
        # Garante que sempre retorne uma lista válida
        if not isinstance(top_questions, list):
            logger.warning("categorize_questions não retornou lista válida, usando fallback")
            from collections import Counter
            counter = Counter(texts)
            top_questions = [{"category": q, "count": c, "examples": [q]} for q, c in counter.most_common(10)]
    except Exception as e:
        logger.error(f"Erro ao categorizar perguntas: {e}", exc_info=True)
        # Fallback seguro
        user_msgs = db.query(ChatEventModel).filter_by(event_type="user_message").all()
        texts = [m.content.strip() for m in user_msgs if m.content and m.content.strip()]
        from collections import Counter
        counter = Counter(texts)
        top_questions = [{"category": q, "count": c, "examples": [q]} for q, c in counter.most_common(10)]

    return {
        "total_messages": total_messages,
        "chats_initiated": chats_initiated,
        "pdfs_sent": pdfs_sent,
        "gifs_sent": gifs_sent,
        "resolved_yes": resolved_yes,
        "resolved_no": resolved_no,
        "resolved_total": resolved_total,
        "detractors": detractors,
        "support_redirected": support_redirected,
        "resolution_rate": resolution_rate,
        "files_not_resolved": files_not_resolved_list,
        "top_questions": top_questions,
        "openai_requests_total": openai_requests_total,
        "openai_requests_success": openai_requests_success,
        "openai_requests_error": openai_requests_error,
        "openai_error_rate": openai_error_rate,
    }


@router.get("/files/stats")
def files_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Estatísticas de arquivos (quantidade e tamanho total). Requer autenticação"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Conta arquivos por tipo no banco
    total_pdfs = db.query(FileModel).filter_by(file_type="pdf").count()
    total_gifs = db.query(FileModel).filter_by(file_type="gif").count()
    total_files = total_pdfs + total_gifs
    
    # Calcula tamanho total dos arquivos
    pdf_dir_str, gif_dir_str = ensure_upload_dirs()
    total_size = 0
    
    # Soma tamanho dos PDFs
    if os.path.isdir(pdf_dir_str):
        for filename in os.listdir(pdf_dir_str):
            filepath = os.path.join(pdf_dir_str, filename)
            if os.path.isfile(filepath):
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    logger.warning(f"Erro ao obter tamanho do arquivo: {filepath}")
                    continue
    
    # Soma tamanho dos GIFs
    if os.path.isdir(gif_dir_str):
        for filename in os.listdir(gif_dir_str):
            filepath = os.path.join(gif_dir_str, filename)
            if os.path.isfile(filepath):
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    logger.warning(f"Erro ao obter tamanho do arquivo: {filepath}")
                    continue
    
    logger.info(f"Estatísticas de arquivos: {total_pdfs} PDFs, {total_gifs} GIFs, {total_size} bytes")
    
    return {
        "total_pdfs": total_pdfs,
        "total_gifs": total_gifs,
        "total_files": total_files,
        "total_size_bytes": total_size
    }


@router.get("/export.xlsx")
def export_excel(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Exporta estatísticas para Excel. Requer autenticação"""
    stats = admin_stats(db, current_user)

    wb = Workbook()
    ws = wb.active
    ws.title = "Dashboard"

    ws.append(["Métrica", "Valor"])
    ws.append(["Total de mensagens", stats["total_messages"]])
    ws.append(["Chats iniciados", stats["chats_initiated"]])
    ws.append(["PDFs enviados", stats["pdfs_sent"]])
    ws.append(["GIFs enviados", stats["gifs_sent"]])
    ws.append(["Resoluções (Sim)", stats["resolved_yes"]])
    ws.append(["Resoluções (Total)", stats["resolved_total"]])
    ws.append(["Taxa de resolução (%)", stats["resolution_rate"]])
    ws.append([])  # Linha em branco
    ws.append(["=== Métricas OpenAI ===", ""])
    ws.append(["Total de requisições", stats.get("openai_requests_total", 0)])
    ws.append(["Requisições com sucesso", stats.get("openai_requests_success", 0)])
    ws.append(["Requisições com erro", stats.get("openai_requests_error", 0)])
    ws.append(["Taxa de erro (%)", stats.get("openai_error_rate", 0)])

    ws2 = wb.create_sheet("Perguntas_frequentes")
    ws2.append(["Categoria", "Ocorrências", "Exemplos"])
    for item in stats["top_questions"]:
        category = item.get("category") or item.get("question", "Sem categoria")
        examples = ", ".join(item.get("examples", [])) if item.get("examples") else ""
        ws2.append([category, item.get("count", 0), examples])

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=dashboard.xlsx"}
    )


@router.get("/backup")
def create_backup(
    current_user: dict = Depends(get_current_user)
):
    """
    Cria um backup completo do sistema (banco, arquivos, configurações).
    Requer autenticação.
    Retorna arquivo .tar.gz para download.
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Executa o script de backup
        script_path = Path(__file__).parent.parent.parent / "scripts" / "backup.py"
        
        if not script_path.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Script de backup não encontrado"
            )
        
        # Executa o script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos de timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Erro ao executar backup: {result.stderr}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao criar backup: {result.stderr}"
            )
        
        # Encontra o arquivo de backup mais recente
        backup_dir = Path(__file__).parent.parent.parent / "backups"
        backup_files = sorted(
            backup_dir.glob("urania_backup_*.tar.gz"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not backup_files:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Arquivo de backup não foi criado"
            )
        
        latest_backup = backup_files[0]
        
        logger.info(f"Backup criado com sucesso: {latest_backup.name}")
        
        # Retorna o arquivo para download
        return FileResponse(
            path=str(latest_backup),
            filename=latest_backup.name,
            media_type="application/gzip"
        )
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout ao criar backup")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Timeout ao criar backup. Tente novamente."
        )
    except Exception as e:
        logger.error(f"Erro ao criar backup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar backup: {str(e)}"
        )

