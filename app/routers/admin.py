"""
Rotas administrativas
"""
from io import BytesIO
from typing import List
from collections import Counter
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import distinct, func, case, String, not_, desc
from openpyxl import Workbook

from app.database import get_db
from app.schemas import PromptBody, SystemSettingsBody
from app.auth import get_current_user
from app.utils import get_setting, set_setting, ensure_upload_dirs, log_audit
from app.models import ChatEventModel, ChatSessionModel, FileModel, FileModel, AuditLogModel
from app.config import settings
import os
import sys
import subprocess
import logging
import tempfile
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Salva prompt customizado. Requer autenticação"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Salvando prompt: {len(body.prompt)} caracteres")
    set_setting(db, "system_prompt", body.prompt or "")
    
    saved_prompt = get_setting(db, "system_prompt")
    logger.info(f"Prompt salvo confirmado: {len(saved_prompt) if saved_prompt else 0} caracteres")
    
    log_audit(db, "prompt_updated", "config", f"Prompt atualizado ({len(body.prompt or '')} caracteres)", user=current_user.get("sub"), ip=request.client.host if request.client else None)
    
    return {"ok": True}


@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Estatísticas do sistema. Requer autenticação - OTIMIZADO"""
    from app.utils import build_file_url
    
    # Agrega contagens de eventos em queries otimizadas (agrupadas por tipo)
    # Total de mensagens
    total_messages = db.query(ChatEventModel).filter(
        ChatEventModel.event_type.in_(["user_message", "bot_message"])
    ).count()
    
    # Chats iniciados
    chats_initiated = db.query(distinct(ChatEventModel.session_id)).filter(
        ChatEventModel.event_type == "chat_started"
    ).count()
    
    # Contagens simples por tipo de evento
    pdfs_sent = db.query(ChatEventModel).filter_by(event_type="pdf_sent").count()
    gifs_sent = db.query(ChatEventModel).filter_by(event_type="gif_sent").count()
    resolved_yes = db.query(ChatEventModel).filter_by(event_type="feedback_yes").count()
    resolved_no = db.query(ChatEventModel).filter_by(event_type="feedback_no").count()
    resolved_total = resolved_yes + resolved_no
    support_redirected = db.query(ChatEventModel).filter_by(event_type="support_redirected").count()
    openai_requests_success = db.query(ChatEventModel).filter_by(event_type="openai_request_success").count()
    openai_requests_error = db.query(ChatEventModel).filter_by(event_type="openai_request_error").count()
    openai_requests_total = openai_requests_success + openai_requests_error
    openai_error_rate = round((openai_requests_error / openai_requests_total) * 100, 2) if openai_requests_total > 0 else 0.0
    resolution_rate = round((resolved_yes / resolved_total) * 100, 1) if resolved_total else 0
    
    # Detratores: sessões que tiveram chat_started mas nunca deram feedback
    sessions_with_feedback = set(
        row[0] for row in db.query(distinct(ChatEventModel.session_id)).filter(
            ChatEventModel.event_type.in_(["feedback_yes", "feedback_no"])
        ).all()
    )
    sessions_started = set(
        row[0] for row in db.query(distinct(ChatEventModel.session_id)).filter(
            ChatEventModel.event_type == "chat_started"
        ).all()
    )
    detractors = len(sessions_started - sessions_with_feedback)

    # Arquivos que não resolveram - OTIMIZADO: agrupa eventos e busca arquivos em batch
    files_not_resolved_events = db.query(ChatEventModel.content).filter_by(
        event_type="file_not_resolved"
    ).all()
    
    # Conta ocorrências por file_id
    file_id_counts = {}
    file_ids_to_fetch = set()
    for row in files_not_resolved_events:
        file_id = row[0] if row[0] else None
        if file_id:
            try:
                file_id_int = int(file_id)
                file_id_counts[file_id_int] = file_id_counts.get(file_id_int, 0) + 1
                file_ids_to_fetch.add(file_id_int)
            except (ValueError, TypeError):
                continue
    
    # Busca todos os arquivos de uma vez (evita N+1)
    files_dict = {}
    if file_ids_to_fetch:
        files = db.query(FileModel).filter(FileModel.id.in_(file_ids_to_fetch)).all()
        files_dict = {f.id: f for f in files}
    
    # Constrói lista final
    files_not_resolved_list = []
    for file_id, count in sorted(file_id_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        file = files_dict.get(file_id)
        if file and file.file_type:
            files_not_resolved_list.append({
                "file_id": file.id,
                "file_type": str(file.file_type).lower(),
                "title": str(file.title or file.original_name or "Sem título"),
                "url": build_file_url(file),
                "count": count
            })

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


@router.get("/system-settings")
def get_system_settings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtém configurações do sistema. Requer autenticação"""
    return {
        "root_behavior": get_setting(db, "root_behavior") or "widget",
        "root_custom_url": get_setting(db, "root_custom_url") or "",
        "widget_enabled": get_setting(db, "widget_enabled") != "false",
    }


@router.put("/system-settings")
def save_system_settings(
    body: SystemSettingsBody,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Salva configurações do sistema. Requer autenticação"""
    changes = []
    fields = {
        "root_behavior": body.root_behavior,
        "root_custom_url": body.root_custom_url,
        "widget_enabled": str(body.widget_enabled).lower() if body.widget_enabled is not None else None,
    }
    for key, value in fields.items():
        if value is not None:
            old = get_setting(db, key)
            set_setting(db, key, value)
            if old != value:
                changes.append(f"{key}: {old} → {value}")
    if changes:
        log_audit(db, "settings_updated", "config", "; ".join(changes), user=current_user.get("sub"), ip=request.client.host if request.client else None)
    return {"ok": True}


@router.get("/audit-logs")
def get_audit_logs(
    page: int = 1,
    limit: int = 50,
    category: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtém logs de auditoria com paginação. Requer autenticação"""
    query = db.query(AuditLogModel).order_by(desc(AuditLogModel.created_at))
    if category:
        query = query.filter(AuditLogModel.category == category)
    total = query.count()
    logs = query.offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "category": log.category,
                "user": log.user,
                "detail": log.detail,
                "ip": log.ip,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
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
    request: Request,
    db: Session = Depends(get_db),
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
        # Tenta múltiplos locais possíveis (onde o script pode ter criado)
        possible_backup_dirs = [
            Path(__file__).parent.parent.parent / "backups",
            Path(tempfile.gettempdir()) / "urania_backups",
            Path.cwd() / "backups"
        ]
        
        backup_files = []
        for backup_dir in possible_backup_dirs:
            if backup_dir.exists():
                try:
                    files = sorted(
                        backup_dir.glob("urania_backup_*.tar.gz"),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True
                    )
                    backup_files.extend(files)
                except (PermissionError, OSError):
                    continue
        
        # Se não encontrou, tenta buscar em qualquer lugar do projeto
        if not backup_files:
            project_root = Path(__file__).parent.parent.parent
            try:
                backup_files = sorted(
                    project_root.rglob("urania_backup_*.tar.gz"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )
            except (PermissionError, OSError):
                pass
        
        if not backup_files:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Arquivo de backup não foi criado. Verifique as permissões do diretório e os logs do script."
            )
        
        latest_backup = backup_files[0]
        
        logger.info(f"Backup criado com sucesso: {latest_backup.name}")
        log_audit(db, "backup_created", "sistema", f"Backup: {latest_backup.name}", user=current_user.get("sub"), ip=request.client.host if request.client else None)
        
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

