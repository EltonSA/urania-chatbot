"""
Rotas para gerenciamento de arquivos
"""
import json
import os
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FileModel
from app.schemas import FileOut, FileUpdateBody
from app.auth import get_current_user
from app.utils import build_file_url, ensure_upload_dirs, log_audit
from app.config import settings
from app.client_ip import get_client_ip

logger = logging.getLogger(__name__)

MAGIC_BYTES = {
    "pdf": [b"%PDF"],
    "gif": [b"GIF87a", b"GIF89a"],
}


def _detect_image_format(content: bytes) -> Optional[str]:
    """Retorna 'png', 'jpeg' ou 'webp' se for imagem suportada."""
    if len(content) < 12:
        return None
    if content.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "webp"
    return None


def _validate_file_content(content: bytes, file_type: str):
    """Verifica se os magic bytes do arquivo correspondem ao tipo declarado"""
    if file_type == "image":
        if not _detect_image_format(content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo de imagem inválido. Use PNG, JPEG ou WebP.",
            )
        return
    signatures = MAGIC_BYTES.get(file_type)
    if not signatures:
        return
    if not any(content.startswith(sig) for sig in signatures):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O conteúdo do arquivo não corresponde ao tipo '{file_type}'. "
            f"Verifique se o arquivo é realmente um {file_type.upper()} válido.",
        )


def _folder_for_type(file_type: str, pdf_dir: str, gif_dir: str, image_dir: str) -> str:
    if file_type == "pdf":
        return pdf_dir
    if file_type == "gif":
        return gif_dir
    if file_type == "image":
        return image_dir
    raise HTTPException(status_code=400, detail="Tipo de arquivo inválido")


def _ext_for_image(content: bytes, original_name: str) -> str:
    fmt = _detect_image_format(content)
    if fmt == "jpeg":
        return ".jpg"
    if fmt == "png":
        return ".png"
    if fmt == "webp":
        return ".webp"
    base = os.path.splitext(original_name or "")[1].lower()
    if base in (".jpg", ".jpeg", ".png", ".webp"):
        return ".jpg" if base == ".jpeg" else base
    return ".img"


def _classify_group_file(content: bytes) -> str:
    """
    Retorna 'gif' ou 'image' para upload em grupo.
    PDF e outros formatos são rejeitados (grupo aceita só imagem estática e GIF).
    """
    if len(content) < 4:
        raise HTTPException(status_code=400, detail="Arquivo vazio ou inválido.")
    if content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF não pode fazer parte de um grupo. Use «Arquivo único» ou selecione apenas imagens e GIFs.",
        )
    if any(content.startswith(sig) for sig in MAGIC_BYTES["gif"]):
        return "gif"
    if _detect_image_format(content):
        return "image"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Cada arquivo do grupo deve ser imagem (PNG, JPEG, WebP) ou GIF.",
    )


router = APIRouter(prefix="/admin/files", tags=["Arquivos"])


@router.post("/upload", response_model=FileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    file_type: str = Form(...),
    title: str = Form(""),
    tags: str = Form(""),
    description: str = Form(""),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload de um arquivo (PDF, GIF ou imagem estática).
    Requer autenticação
    """
    file_type = (file_type or "").lower().strip()
    allowed = list(settings.ALLOWED_EXTENSIONS) if settings.ALLOWED_EXTENSIONS else ["pdf", "gif", "image"]
    if file_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"file_type deve ser um de: {', '.join(allowed)}",
        )

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo muito grande. Tamanho máximo: {settings.MAX_FILE_SIZE / 1024 / 1024}MB",
        )

    _validate_file_content(content, file_type)

    pdf_dir, gif_dir, image_dir = ensure_upload_dirs()
    folder = _folder_for_type(file_type, pdf_dir, gif_dir, image_dir)

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    orig = (file.filename or "arquivo").replace(" ", "_")
    if file_type == "image":
        ext = _ext_for_image(content, orig)
        safe_name = f"{timestamp}_img{ext}"
    else:
        safe_name = f"{timestamp}_{orig}"
    filepath = os.path.join(folder, safe_name)

    with open(filepath, "wb") as f:
        f.write(content)

    db_file = FileModel(
        filename=safe_name,
        original_name=file.filename or safe_name,
        file_type=file_type,
        title=title or (file.filename or safe_name),
        tags=tags,
        description=(description or "").strip() or None,
        group_id=None,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    logger.info("Arquivo salvo no banco: ID %s, título: %s", db_file.id, db_file.title)
    log_audit(
        db,
        "file_uploaded",
        "arquivo",
        f"{file_type.upper()}: {db_file.title} (ID {db_file.id})",
        user=current_user.get("sub"),
        ip=get_client_ip(request),
    )

    return FileOut(
        id=db_file.id,
        title=db_file.title,
        file_type=db_file.file_type,
        url=build_file_url(db_file),
        tags=db_file.tags,
        description=db_file.description,
        group_id=db_file.group_id,
    )


@router.post("/upload-group", response_model=List[FileOut], status_code=status.HTTP_201_CREATED)
async def upload_group_media(
    request: Request,
    files: List[UploadFile] = File(...),
    title: str = Form(""),
    tags: str = Form(""),
    descriptions_json: str = Form("[]"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload de várias imagens (PNG/JPEG/WebP) e/ou GIFs como um grupo: mesmo group_id,
    título/tags compartilhados, descrição individual por arquivo (JSON na ordem dos ficheiros).
    PDF não é aceito neste endpoint.
    """
    if not files:
        raise HTTPException(status_code=400, detail="Envie pelo menos uma imagem ou GIF.")

    try:
        descriptions = json.loads(descriptions_json or "[]")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="descriptions_json deve ser um JSON array.")

    if not isinstance(descriptions, list):
        raise HTTPException(status_code=400, detail="descriptions_json deve ser um array.")

    while len(descriptions) < len(files):
        descriptions.append("")
    descriptions = descriptions[: len(files)]

    pdf_dir, gif_dir, image_dir = ensure_upload_dirs()
    group_id = str(uuid.uuid4())
    out: List[FileOut] = []

    for idx, up in enumerate(files):
        content = await up.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Arquivo {idx + 1} excede o tamanho máximo permitido.",
            )
        file_type = _classify_group_file(content)
        _validate_file_content(content, file_type)

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        if file_type == "gif":
            safe_name = f"{timestamp}_{group_id[:8]}_{idx}.gif"
            folder = gif_dir
        else:
            ext = _ext_for_image(content, up.filename or "")
            safe_name = f"{timestamp}_{group_id[:8]}_{idx}{ext}"
            folder = image_dir
        filepath = os.path.join(folder, safe_name)

        with open(filepath, "wb") as f:
            f.write(content)

        desc = str(descriptions[idx] if idx < len(descriptions) else "").strip() or None
        t = title.strip() or (up.filename or safe_name)

        db_file = FileModel(
            filename=safe_name,
            original_name=up.filename or safe_name,
            file_type=file_type,
            title=t,
            tags=tags,
            description=desc,
            group_id=group_id,
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        out.append(
            FileOut(
                id=db_file.id,
                title=db_file.title,
                file_type=db_file.file_type,
                url=build_file_url(db_file),
                tags=db_file.tags,
                description=db_file.description,
                group_id=db_file.group_id,
            )
        )

    log_audit(
        db,
        "file_group_uploaded",
        "arquivo",
        f"Grupo imagens/GIFs ({len(out)} arquivos) group_id={group_id}: {title or 'sem título'}",
        user=current_user.get("sub"),
        ip=get_client_ip(request),
    )
    return out


@router.get("", response_model=List[FileOut])
def list_files(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Lista todos os arquivos. Requer autenticação"""
    files = db.query(FileModel).order_by(FileModel.created_at.desc()).all()
    logger.info("Listando %s arquivos do banco de dados", len(files))

    result = [
        FileOut(
            id=f.id,
            title=f.title,
            file_type=f.file_type,
            url=build_file_url(f),
            tags=f.tags,
            description=f.description,
            group_id=f.group_id,
        )
        for f in files
    ]

    logger.info("Retornando %s arquivos", len(result))
    return result


@router.put("/{file_id}")
def update_file(
    file_id: int,
    body: FileUpdateBody,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Atualiza arquivo. Requer autenticação"""
    file = db.query(FileModel).get(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo não encontrado",
        )

    changes = []
    if body.title is not None and body.title != file.title:
        changes.append(f"título: {file.title} → {body.title}")
        file.title = body.title
    if body.tags is not None and body.tags != file.tags:
        changes.append(f"tags: {file.tags} → {body.tags}")
        file.tags = body.tags
    if body.description is not None:
        norm_desc = (body.description or "").strip() or None
        if norm_desc != file.description:
            changes.append("descrição atualizada")
            file.description = norm_desc

    db.commit()
    db.refresh(file)

    if changes:
        log_audit(
            db,
            "file_updated",
            "arquivo",
            f"ID {file_id}: {'; '.join(changes)}",
            user=current_user.get("sub"),
            ip=get_client_ip(request),
        )

    return {
        "id": file.id,
        "title": file.title,
        "tags": file.tags,
        "description": file.description,
        "file_type": file.file_type,
        "url": build_file_url(file),
        "group_id": file.group_id,
    }


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Deleta arquivo. Requer autenticação"""
    file = db.query(FileModel).get(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo não encontrado",
        )

    file_info = f"{file.file_type.upper()}: {file.title} (ID {file.id})"

    pdf_dir, gif_dir, image_dir = ensure_upload_dirs()
    folder = _folder_for_type(file.file_type, pdf_dir, gif_dir, image_dir)
    filepath = os.path.join(folder, file.filename)

    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        logger.error("Erro ao remover arquivo físico %s: %s", filepath, e)

    db.delete(file)
    db.commit()
    log_audit(
        db,
        "file_deleted",
        "arquivo",
        file_info,
        user=current_user.get("sub"),
        ip=get_client_ip(request),
    )
    return {"ok": True}
