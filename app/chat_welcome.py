"""
Mensagem inicial do chat (/widget e iframe do widget flutuante).
Persistida em settings.chat_welcome_message (texto).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.utils import get_setting, set_setting

DEFAULT_CHAT_WELCOME_MESSAGE = (
    "Olá! 👋\n\n"
    "Eu sou o Professor Horácio, assistente virtual do URÂNIA+ 💚\n\n"
    "Qual é sua dúvida?"
)

MAX_WELCOME_LEN = 2500


def normalize_welcome_text(value: str) -> str:
    if value is None:
        return DEFAULT_CHAT_WELCOME_MESSAGE
    s = str(value).replace("\r\n", "\n").replace("\r", "\n")
    if "\x00" in s:
        raise ValueError("Texto inválido")
    s = s.strip()
    if not s:
        return DEFAULT_CHAT_WELCOME_MESSAGE
    if len(s) > MAX_WELCOME_LEN:
        raise ValueError(f"Texto muito longo (máximo {MAX_WELCOME_LEN} caracteres)")
    return s


def load_chat_welcome_message(db: Session) -> str:
    raw = get_setting(db, "chat_welcome_message")
    if raw is None:
        return DEFAULT_CHAT_WELCOME_MESSAGE
    try:
        return normalize_welcome_text(raw)
    except ValueError:
        return DEFAULT_CHAT_WELCOME_MESSAGE


def save_chat_welcome_message(db: Session, text: str) -> str:
    normalized = normalize_welcome_text(text)
    set_setting(db, "chat_welcome_message", normalized)
    return normalized


def reset_chat_welcome_message(db: Session) -> None:
    set_setting(db, "chat_welcome_message", DEFAULT_CHAT_WELCOME_MESSAGE)
