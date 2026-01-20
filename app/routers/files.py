"""
Rotas para gerenciamento de arquivos
"""
import os
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FileModel
from app.schemas import FileOut, FileUpdateBody
from app.auth import get_current_user
from app.utils import build_file_url, ensure_upload_dirs
from app.config import settings

router = APIRouter(prefix="/admin/files", tags=["Arquivos"])


@router.post("/upload", response_model=FileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    title: str = Form(""),
    tags: str = Form(""),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload de arquivo (PDF ou GIF)
    Requer autenticação
    """
    file_type = (file_type or "").lower().strip()
    if file_type not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"file_type deve ser um de: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Verifica tamanho do arquivo
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo muito grande. Tamanho máximo: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    pdf_dir, gif_dir = ensure_upload_dirs()
    folder = pdf_dir if file_type == "pdf" else gif_dir

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = f"{timestamp}_{(file.filename or 'arquivo').replace(' ', '_')}"
    filepath = os.path.join(folder, safe_name)

    with open(filepath, "wb") as f:
        f.write(content)

    import logging
    logger = logging.getLogger(__name__)
    
    db_file = FileModel(
        filename=safe_name,
        original_name=file.filename or safe_name,
        file_type=file_type,
        title=title or (file.filename or safe_name),
        tags=tags
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    logger.info(f"Arquivo salvo no banco: ID {db_file.id}, título: {db_file.title}")

    return FileOut(
        id=db_file.id,
        title=db_file.title,
        file_type=db_file.file_type,
        url=build_file_url(db_file),
        tags=db_file.tags
    )


@router.get("", response_model=List[FileOut])
def list_files(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lista todos os arquivos. Requer autenticação"""
    import logging
    logger = logging.getLogger(__name__)
    
    files = db.query(FileModel).order_by(FileModel.created_at.desc()).all()
    logger.info(f"Listando {len(files)} arquivos do banco de dados")
    
    result = [
        FileOut(
            id=f.id,
            title=f.title,
            file_type=f.file_type,
            url=build_file_url(f),
            tags=f.tags
        )
        for f in files
    ]
    
    logger.info(f"Retornando {len(result)} arquivos")
    return result


@router.put("/{file_id}")
def update_file(
    file_id: int,
    body: FileUpdateBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Atualiza arquivo. Requer autenticação"""
    file = db.query(FileModel).get(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo não encontrado"
        )

    if body.title is not None:
        file.title = body.title
    if body.tags is not None:
        file.tags = body.tags

    db.commit()
    db.refresh(file)

    return {
        "id": file.id,
        "title": file.title,
        "tags": file.tags,
        "file_type": file.file_type,
        "url": build_file_url(file),
    }


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Deleta arquivo. Requer autenticação"""
    file = db.query(FileModel).get(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo não encontrado"
        )

    pdf_dir, gif_dir = ensure_upload_dirs()
    folder = pdf_dir if file.file_type == "pdf" else gif_dir
    filepath = os.path.join(folder, file.filename)
    
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao remover arquivo físico {filepath}: {e}")

    db.delete(file)
    db.commit()
    return {"ok": True}



