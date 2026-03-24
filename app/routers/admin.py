"""
Rotas administrativas
"""
from io import BytesIO
from typing import List, Optional, Any, Dict
from collections import Counter
from fastapi import APIRouter, HTTPException, Depends, Request, status, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import distinct, func, case, String, not_, desc
from openpyxl import Workbook

from app.database import get_db
from app.schemas import PromptBody, SystemSettingsBody
from app.auth import get_current_user
from app.utils import (
    get_setting,
    set_setting,
    ensure_upload_dirs,
    log_audit,
    branding_dir_path,
    resolve_branding_favicon,
)
from app.models import ChatEventModel, ChatSessionModel, FileModel, AuditLogModel
from app.config import settings
from app.date_range import parse_stats_date_range
import os
import sys
import subprocess
import logging
import tempfile
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])


def _apply_event_time_filter(q, start: Optional[datetime], end: Optional[datetime]):
    if start is not None:
        q = q.filter(ChatEventModel.created_at >= start)
    if end is not None:
        q = q.filter(ChatEventModel.created_at <= end)
    return q


def build_admin_stats_payload(
    db: Session,
    range_start: Optional[datetime],
    range_end: Optional[datetime],
) -> Dict[str, Any]:
    """Métricas baseadas em chat_events; opcionalmente filtradas por created_at."""
    from app.utils import build_file_url

    def ev_filter(event_type, single=True):
        if single:
            q = db.query(ChatEventModel).filter_by(event_type=event_type)
        else:
            q = db.query(ChatEventModel).filter(ChatEventModel.event_type.in_(event_type))
        return _apply_event_time_filter(q, range_start, range_end)

    total_messages = ev_filter(["user_message", "bot_message"], single=False).count()

    chats_q = db.query(distinct(ChatEventModel.session_id)).filter(
        ChatEventModel.event_type == "chat_started"
    )
    chats_q = _apply_event_time_filter(chats_q, range_start, range_end)
    chats_initiated = chats_q.count()

    pdfs_sent = ev_filter("pdf_sent").count()
    gifs_sent = ev_filter("gif_sent").count()
    images_sent = ev_filter("image_sent").count()
    resolved_yes = ev_filter("feedback_yes").count()
    resolved_no = ev_filter("feedback_no").count()
    resolved_total = resolved_yes + resolved_no
    support_redirected = ev_filter("support_redirected").count()
    openai_requests_success = ev_filter("openai_request_success").count()
    openai_requests_error = ev_filter("openai_request_error").count()
    openai_requests_total = openai_requests_success + openai_requests_error
    openai_error_rate = (
        round((openai_requests_error / openai_requests_total) * 100, 2)
        if openai_requests_total > 0
        else 0.0
    )
    resolution_rate = (
        round((resolved_yes / resolved_total) * 100, 1) if resolved_total else 0
    )

    # Sessões com chat_started no período vs. feedback sim/não no período
    swf_q = db.query(distinct(ChatEventModel.session_id)).filter(
        ChatEventModel.event_type.in_(["feedback_yes", "feedback_no"])
    )
    swf_q = _apply_event_time_filter(swf_q, range_start, range_end)
    sessions_with_feedback = set(row[0] for row in swf_q.all())

    ss_q = db.query(distinct(ChatEventModel.session_id)).filter(
        ChatEventModel.event_type == "chat_started"
    )
    ss_q = _apply_event_time_filter(ss_q, range_start, range_end)
    sessions_started = set(row[0] for row in ss_q.all())

    detractors = len(sessions_started - sessions_with_feedback)

    def _count_events_by_file_id(event_name: str) -> Dict[int, int]:
        q = db.query(ChatEventModel.content).filter_by(event_type=event_name)
        q = _apply_event_time_filter(q, range_start, range_end)
        out_counts: Dict[int, int] = {}
        for row in q.all():
            raw = row[0] if row[0] else None
            if not raw:
                continue
            try:
                fid = int(str(raw).strip())
            except (ValueError, TypeError):
                continue
            out_counts[fid] = out_counts.get(fid, 0) + 1
        return out_counts

    yes_by_file = _count_events_by_file_id("file_resolved")
    no_by_file = _count_events_by_file_id("file_not_resolved")
    all_feedback_file_ids = set(yes_by_file.keys()) | set(no_by_file.keys())

    files_dict: Dict[int, Any] = {}
    if all_feedback_file_ids:
        files = db.query(FileModel).filter(FileModel.id.in_(all_feedback_file_ids)).all()
        files_dict = {f.id: f for f in files}

    file_rows = []
    for fid in all_feedback_file_ids:
        cy = yes_by_file.get(fid, 0)
        cn = no_by_file.get(fid, 0)
        if cy == 0 and cn == 0:
            continue
        frow = files_dict.get(fid)
        if not frow or not frow.file_type:
            continue
        file_rows.append(
            {
                "file_id": frow.id,
                "file_type": str(frow.file_type).lower(),
                "title": str(frow.title or frow.original_name or "Sem título"),
                "url": build_file_url(frow),
                "clicks_yes": cy,
                "clicks_no": cn,
                "clicks_total": cy + cn,
                "count": cn,
            }
        )

    file_rows.sort(key=lambda x: (x["clicks_total"], x["clicks_no"]), reverse=True)
    files_feedback_stats = file_rows[:15]

    out: Dict[str, Any] = {
        "total_messages": total_messages,
        "chats_initiated": chats_initiated,
        "pdfs_sent": pdfs_sent,
        "gifs_sent": gifs_sent,
        "images_sent": images_sent,
        "resolved_yes": resolved_yes,
        "resolved_no": resolved_no,
        "resolved_total": resolved_total,
        "detractors": detractors,
        "support_redirected": support_redirected,
        "resolution_rate": resolution_rate,
        "files_not_resolved": files_feedback_stats,
        "files_feedback_stats": files_feedback_stats,
        "openai_requests_total": openai_requests_total,
        "openai_requests_success": openai_requests_success,
        "openai_requests_error": openai_requests_error,
        "openai_error_rate": openai_error_rate,
    }
    if range_start is not None and range_end is not None:
        out["date_from"] = range_start.strftime("%Y-%m-%d")
        out["date_to"] = range_end.strftime("%Y-%m-%d")
        out["filtered"] = True
    else:
        out["date_from"] = None
        out["date_to"] = None
        out["filtered"] = False
    return out


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
    current_user: dict = Depends(get_current_user),
    date_from: Optional[str] = Query(
        None,
        description="Data inicial (YYYY-MM-DD, UTC). Omita ambas as datas para todo o período.",
    ),
    date_to: Optional[str] = Query(
        None,
        description="Data final (YYYY-MM-DD, UTC), inclusiva.",
    ),
):
    """Estatísticas do sistema; filtro opcional por intervalo de datas nos eventos."""
    rs, re = parse_stats_date_range(date_from, date_to)
    return build_admin_stats_payload(db, rs, re)


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
    total_images = db.query(FileModel).filter_by(file_type="image").count()
    total_files = total_pdfs + total_gifs + total_images

    # Calcula tamanho total dos arquivos
    pdf_dir_str, gif_dir_str, image_dir_str = ensure_upload_dirs()
    total_size = 0

    for dir_str in (pdf_dir_str, gif_dir_str, image_dir_str):
        if os.path.isdir(dir_str):
            for filename in os.listdir(dir_str):
                filepath = os.path.join(dir_str, filename)
                if os.path.isfile(filepath):
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        logger.warning("Erro ao obter tamanho do arquivo: %s", filepath)
                        continue

    logger.info(
        "Estatísticas de arquivos: %s PDFs, %s GIFs, %s imagens, %s bytes",
        total_pdfs,
        total_gifs,
        total_images,
        total_size,
    )

    return {
        "total_pdfs": total_pdfs,
        "total_gifs": total_gifs,
        "total_images": total_images,
        "total_files": total_files,
        "total_size_bytes": total_size,
    }


@router.get("/system-settings")
def get_system_settings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtém configurações do sistema. Requer autenticação"""
    fav_path, _ = resolve_branding_favicon()
    return {
        "root_behavior": get_setting(db, "root_behavior") or "widget",
        "root_custom_url": get_setting(db, "root_custom_url") or "",
        "widget_enabled": get_setting(db, "widget_enabled") != "false",
        "satisfaction_support_button": get_setting(db, "satisfaction_support_button") != "false",
        "system_display_name": get_setting(db, "system_display_name") or "",
        "default_display_name": settings.APP_NAME,
        "has_custom_favicon": fav_path is not None,
        "app_version": settings.resolved_app_version,
        "app_version_env": settings.APP_VERSION,
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
        "satisfaction_support_button": (
            str(body.satisfaction_support_button).lower()
            if body.satisfaction_support_button is not None
            else None
        ),
    }
    for key, value in fields.items():
        if value is not None:
            old = get_setting(db, key)
            set_setting(db, key, value)
            if old != value:
                changes.append(f"{key}: {old} → {value}")
    if body.system_display_name is not None:
        old = get_setting(db, "system_display_name") or ""
        new_val = body.system_display_name
        set_setting(db, "system_display_name", new_val)
        if old != new_val:
            changes.append(f"system_display_name: {old!r} → {new_val!r}")

    if changes:
        log_audit(db, "settings_updated", "config", "; ".join(changes), user=current_user.get("sub"), ip=request.client.host if request.client else None)
    return {"ok": True}


MAX_BRANDING_FAVICON_BYTES = 512 * 1024


@router.post("/branding/favicon")
async def upload_branding_favicon(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Substitui o favicon do site (.ico ou .png, máx. 512 KB)."""
    fn = (file.filename or "").lower()
    ct = (file.content_type or "").lower()
    if fn.endswith(".ico") or "icon" in ct or "/ico" in ct:
        ext = "ico"
    elif fn.endswith(".png") or "png" in ct:
        ext = "png"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie um arquivo .ico ou .png",
        )
    data = await file.read()
    if len(data) > MAX_BRANDING_FAVICON_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo muito grande (máximo 512 KB)",
        )
    if len(data) < 32:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo inválido ou corrompido",
        )
    d = branding_dir_path()
    for name in ("favicon.ico", "favicon.png"):
        p = d / name
        if p.is_file():
            try:
                p.unlink()
            except OSError:
                pass
    out_name = "favicon.ico" if ext == "ico" else "favicon.png"
    out = d / out_name
    out.write_bytes(data)
    log_audit(
        db,
        "branding_favicon_uploaded",
        "config",
        out_name,
        user=current_user.get("sub"),
        ip=request.client.host if request.client else None,
    )
    return {"ok": True, "filename": out_name}


@router.delete("/branding/favicon")
def delete_branding_favicon(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Remove o favicon personalizado (volta ao /static/favicon.ico)."""
    d = branding_dir_path()
    removed = []
    for name in ("favicon.ico", "favicon.png"):
        p = d / name
        if p.is_file():
            try:
                p.unlink()
                removed.append(name)
            except OSError:
                pass
    if removed:
        log_audit(
            db,
            "branding_favicon_removed",
            "config",
            ", ".join(removed),
            user=current_user.get("sub"),
            ip=request.client.host if request.client else None,
        )
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
    current_user: dict = Depends(get_current_user),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
):
    """Exporta estatísticas para Excel (mesmo filtro de datas do dashboard)."""
    rs, re = parse_stats_date_range(date_from, date_to)
    stats = build_admin_stats_payload(db, rs, re)

    wb = Workbook()
    ws = wb.active
    ws.title = "Dashboard"

    if stats.get("filtered"):
        ws.append(["Período (UTC)", f"{stats['date_from']} a {stats['date_to']}"])
    else:
        ws.append(["Período", "Todo o histórico"])
    ws.append(["Métrica", "Valor"])
    ws.append(["Total de mensagens", stats["total_messages"]])
    ws.append(["Chats iniciados", stats["chats_initiated"]])
    ws.append(["PDFs enviados", stats["pdfs_sent"]])
    ws.append(["GIFs enviados", stats["gifs_sent"]])
    ws.append(["Imagens enviadas", stats.get("images_sent", 0)])
    ws.append(["Resoluções (Sim)", stats["resolved_yes"]])
    ws.append(["Resoluções (Total)", stats["resolved_total"]])
    ws.append(["Taxa de resolução (%)", stats["resolution_rate"]])
    ws.append([])  # Linha em branco
    ws.append(["=== Métricas OpenAI ===", ""])
    ws.append(["Total de requisições", stats.get("openai_requests_total", 0)])
    ws.append(["Requisições com sucesso", stats.get("openai_requests_success", 0)])
    ws.append(["Requisições com erro", stats.get("openai_requests_error", 0)])
    ws.append(["Taxa de erro (%)", stats.get("openai_error_rate", 0)])

    ff = stats.get("files_feedback_stats") or stats.get("files_not_resolved") or []
    if ff:
        ws.append([])
        ws.append(["=== Arquivos — feedback (último envio na sessão) ===", ""])
        ws.append(["Título", "Tipo", "Cliques em Sim", "Cliques em Não", "Total"])
        for row in ff:
            cy = int(row.get("clicks_yes") or 0)
            if "clicks_no" in row:
                cn = int(row.get("clicks_no") or 0)
            else:
                cn = int(row.get("count") or 0)
            ws.append(
                [
                    row.get("title", ""),
                    str(row.get("file_type", "")).upper(),
                    cy,
                    cn,
                    cy + cn,
                ]
            )

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

