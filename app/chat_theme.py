"""
Tema visual apenas da página /widget (chat embutido).
Persistido em settings.chat_theme (JSON).
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.utils import get_setting, set_setting

HEX_RE = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")
BUBBLE_RADIUS_RE = re.compile(r"^\d{1,2}px$")

DEFAULT_CHAT_THEME: Dict[str, str] = {
    "primary": "#1C8B3C",
    "primary_mid": "#16a34a",
    "primary_dark": "#15803d",
    "user_bg": "#ffffff",
    "user_border": "#e5e7eb",
    "user_text": "#0f172a",
    "page_from": "#ecfdf5",
    "page_via": "#ffffff",
    "page_to": "#f8fafc",
    "chat_box_bg": "rgba(249, 250, 251, 0.35)",
    "input_focus": "#22c55e",
    "bubble_radius": "20px",
    "pdf_header_bg": "#f0fdf4",
    "pdf_title": "#065f46",
}

# Chaves que devem ser #RRGGBB (ou #RGB)
_HEX_KEYS = frozenset(
    {
        "primary",
        "primary_mid",
        "primary_dark",
        "user_bg",
        "user_border",
        "user_text",
        "page_from",
        "page_via",
        "page_to",
        "input_focus",
        "pdf_header_bg",
        "pdf_title",
    }
)


def normalize_hex(value: str) -> str:
    s = value.strip()
    if not HEX_RE.match(s):
        raise ValueError(f"Cor hexadecimal inválida: {value!r}")
    if len(s) == 4:
        return "#" + s[1] * 2 + s[2] * 2 + s[3] * 2
    return s.lower()


def validate_theme_key(key: str, value: Any) -> str:
    if value is None:
        raise ValueError("valor vazio")
    s = str(value).strip()
    if not s:
        raise ValueError("valor vazio")
    if key == "chat_box_bg":
        if len(s) > 80 or "\n" in s:
            raise ValueError("Fundo da área do chat inválido")
        return s
    if key == "bubble_radius":
        if not BUBBLE_RADIUS_RE.match(s):
            raise ValueError("Raio deve ser como 20px (10–28)")
        px = int(s[:-2])
        if px < 10 or px > 28:
            raise ValueError("Raio entre 10px e 28px")
        return s
    if key in _HEX_KEYS:
        return normalize_hex(s)
    raise ValueError(f"Chave de tema desconhecida: {key}")


def load_merged_chat_theme(db: Session) -> Dict[str, str]:
    out = dict(DEFAULT_CHAT_THEME)
    raw = get_setting(db, "chat_theme")
    if not raw:
        return out
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            for k, v in data.items():
                if k not in out or not isinstance(v, str) or not v.strip():
                    continue
                try:
                    out[k] = validate_theme_key(k, v)
                except ValueError:
                    pass
    except (json.JSONDecodeError, TypeError):
        pass
    return out


def save_chat_theme_partial(db: Session, partial: Dict[str, Any]) -> Dict[str, str]:
    current = load_merged_chat_theme(db)
    for key, val in partial.items():
        if val is None:
            continue
        if key not in DEFAULT_CHAT_THEME:
            continue
        s = str(val).strip()
        if not s:
            continue
        validated = validate_theme_key(key, s)
        current[key] = validated
    set_setting(db, "chat_theme", json.dumps(current, ensure_ascii=False))
    return current


def reset_chat_theme(db: Session) -> None:
    set_setting(db, "chat_theme", json.dumps(DEFAULT_CHAT_THEME, ensure_ascii=False))
