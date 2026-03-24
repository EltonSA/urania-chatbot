"""
Rotas públicas para servir arquivos (sem autenticação)
"""
import os
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from app.database import get_db
from app.models import FileModel
from app.utils import ensure_upload_dirs

router = APIRouter(tags=["Arquivos Públicos"])


@router.get("/files/pdf/{file_id}")
def serve_pdf(file_id: int, db: Session = Depends(get_db)):
    """Serve arquivo PDF (público)"""
    file = db.query(FileModel).get(file_id)
    if not file or file.file_type != "pdf":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF não encontrado"
        )

    pdf_dir, _, _ = ensure_upload_dirs()
    filepath = os.path.join(pdf_dir, file.filename)
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo físico não encontrado"
        )

    return FileResponse(filepath, media_type="application/pdf")


@router.get("/files/gif/{file_id}")
def serve_gif(file_id: int, db: Session = Depends(get_db)):
    """Serve arquivo GIF (público)"""
    file = db.query(FileModel).get(file_id)
    if not file or file.file_type != "gif":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GIF não encontrado"
        )

    _, gif_dir, _ = ensure_upload_dirs()
    filepath = os.path.join(gif_dir, file.filename)
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo físico não encontrado"
        )

    return FileResponse(filepath, media_type="image/gif")


def _image_media_type(filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "application/octet-stream")


@router.get("/files/image/{file_id}")
def serve_image(file_id: int, db: Session = Depends(get_db)):
    """Serve imagem estática PNG/JPEG/WebP (público)"""
    file = db.query(FileModel).get(file_id)
    if not file or file.file_type != "image":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagem não encontrada",
        )

    _, _, image_dir = ensure_upload_dirs()
    filepath = os.path.join(image_dir, file.filename)
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo físico não encontrado",
        )

    return FileResponse(filepath, media_type=_image_media_type(file.filename))
