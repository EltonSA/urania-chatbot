"""
Resolve o IP real do cliente atrás de proxy reverso.

Usa X-Forwarded-For (primeiro endereço da lista = cliente original) e X-Real-IP
quando TRUST_FORWARDED_HEADERS está ativo; caso contrário apenas request.client.
"""
from __future__ import annotations

import ipaddress
from fastapi import Request

from app.config import settings


def _normalize_ip(candidate: str) -> str | None:
    s = candidate.strip()
    if not s:
        return None
    if "%" in s:
        s = s.split("%", 1)[0]
    try:
        ipaddress.ip_address(s)
    except ValueError:
        return None
    return s


def get_client_ip(request: Request) -> str:
    """
    IP do cliente. Com proxy reverso (nginx, etc.), confiar no primeiro valor de
    X-Forwarded-For ou em X-Real-IP — o ASGI já vê o socket como o IP do proxy.
    """
    if settings.TRUST_FORWARDED_HEADERS:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            for part in xff.split(","):
                ip = _normalize_ip(part)
                if ip:
                    return ip
        xri = request.headers.get("x-real-ip")
        if xri:
            ip = _normalize_ip(xri)
            if ip:
                return ip

    if request.client:
        return request.client.host
    return "unknown"
