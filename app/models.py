"""
Modelos do banco de dados
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base


class FileModel(Base):
    """Modelo para arquivos (PDF, GIF, imagens estáticas)"""
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # "pdf", "gif" ou "image"
    title = Column(String, nullable=True)
    tags = Column(String, nullable=True)  # separado por vírgula
    description = Column(Text, nullable=True)  # texto para a IA e para enriquecer respostas
    group_id = Column(String(64), nullable=True, index=True)  # mesmo UUID = grupo (imagens e/ou GIFs; PDF não usa grupo)
    created_at = Column(DateTime, default=datetime.utcnow)


class SettingModel(Base):
    """Modelo para configurações do sistema"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text, nullable=True)


class ChatSessionModel(Base):
    """Modelo para sessões de chat"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Integer, nullable=True)  # 1=sim, 0=nao, None=sem feedback


class ChatEventModel(Base):
    """Modelo para eventos do chat"""
    __tablename__ = "chat_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLogModel(Base):
    """Modelo para logs de auditoria do sistema"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, index=True, nullable=False)
    category = Column(String, index=True, nullable=False)
    user = Column(String, nullable=True)
    detail = Column(Text, nullable=True)
    ip = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class UserModel(Base):
    """Usuários do painel (admin ou usuário comum)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="user")  # "admin" | "user"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

