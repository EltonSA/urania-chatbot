"""
Gestão de usuários do painel (somente administrador).
"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import ROLE_ADMIN, get_password_hash, require_admin
from app.client_ip import get_client_ip
from app.config import settings
from app.database import get_db
from app.models import UserModel
from app.schemas import UserCreateBody, UserOut, UserUpdateBody
from app.utils import log_audit

router = APIRouter(prefix="/admin/users", tags=["Usuários"])


def _env_admin_username() -> str:
    """Nome de usuário reservado ao bootstrap (.env ADMIN_USERNAME)."""
    return (settings.ADMIN_USERNAME or "").strip()


def _is_env_managed_user(u: UserModel) -> bool:
    return u.username == _env_admin_username()


def _user_to_out(u: UserModel) -> UserOut:
    return UserOut(
        id=u.id,
        username=u.username,
        role=u.role,
        created_at=u.created_at,
        managed_by_env=_is_env_managed_user(u),
    )


def _count_admins(db: Session) -> int:
    return db.query(func.count(UserModel.id)).filter(UserModel.role == ROLE_ADMIN).scalar() or 0


@router.get("", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    users = db.query(UserModel).order_by(UserModel.username.asc()).all()
    return [_user_to_out(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreateBody,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    uname = body.username.strip()
    if uname == _env_admin_username():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este nome está reservado ao administrador do .env (ADMIN_USERNAME). Escolha outro nome.",
        )

    exists = db.query(UserModel).filter(UserModel.username == uname).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este nome de usuário já existe")

    u = UserModel(
        username=uname,
        password_hash=get_password_hash(body.password),
        role=body.role,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    log_audit(
        db,
        "user_created",
        "config",
        f"Usuário {u.username} ({u.role})",
        user=current_user.get("username"),
        ip=get_client_ip(request),
    )
    return _user_to_out(u)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdateBody,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    u = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    if _is_env_managed_user(u):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O usuário definido em ADMIN_USERNAME no .env só pode ser alterado no arquivo .env (e reinício do servidor).",
        )

    if body.password is None and body.role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe nova senha e/ou perfil",
        )

    admins = _count_admins(db)
    if u.role == ROLE_ADMIN and body.role == "user" and admins <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deve existir pelo menos um administrador",
        )

    if body.password is not None:
        u.password_hash = get_password_hash(body.password)
    if body.role is not None:
        u.role = body.role

    u.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(u)

    log_audit(
        db,
        "user_updated",
        "config",
        f"Usuário {u.username} atualizado",
        user=current_user.get("username"),
        ip=get_client_ip(request),
    )
    return _user_to_out(u)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> Response:
    u = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    if _is_env_managed_user(u):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O usuário definido em ADMIN_USERNAME no .env não pode ser excluído pelo painel.",
        )

    if u.role == ROLE_ADMIN and _count_admins(db) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível excluir o único administrador",
        )

    uname = u.username
    db.delete(u)
    db.commit()

    log_audit(
        db,
        "user_deleted",
        "config",
        f"Usuário {uname} removido",
        user=current_user.get("username"),
        ip=get_client_ip(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
