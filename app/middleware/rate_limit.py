"""
Rate limiting middleware

Conta pedidos por IP por minuto. Pedidos leves e públicos (GET /branding, /chat/status,
estáticos, página /widget, preflight CORS) não entram no contador — o widget embutido
gera muitos GET legítimos (iframe + pai + troca de abas) e esgotava o limite global.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.config import settings
from app.client_ip import get_client_ip
import logging

logger = logging.getLogger(__name__)

MAX_TRACKED_IPS = 10_000


def _is_exempt_from_rate_limit(request: Request) -> bool:
    """Não contar para o limite: leituras públicas frequentes e preflight CORS."""
    if request.method == "OPTIONS":
        return True
    if request.method != "GET":
        return False
    path = request.url.path
    if path == "/health":
        return True
    if path.startswith("/static/"):
        return True
    if path.startswith("/branding"):
        return True
    if path == "/chat/status":
        return True
    if path == "/widget":
        return True
    # Anexos do chat (PDF/GIF/imagem) — muitos GET ao abrir conversa com mídia
    if path.startswith("/files/pdf/") or path.startswith("/files/gif/") or path.startswith("/files/image/"):
        return True
    return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting com proteção contra exaustão de memória"""

    def __init__(self, app):
        super().__init__(app)
        self.requests: dict[str, list[datetime]] = defaultdict(list)
        self.cleanup_interval = timedelta(minutes=1)
        self.last_cleanup = datetime.utcnow()

    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        if _is_exempt_from_rate_limit(request):
            return await call_next(request)

        now = datetime.utcnow()

        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup(now)
            self.last_cleanup = now

        client_ip = get_client_ip(request)
        minute_ago = now - timedelta(minutes=1)

        timestamps = self.requests[client_ip]
        self.requests[client_ip] = [t for t in timestamps if t > minute_ago]

        if len(self.requests[client_ip]) >= settings.RATE_LIMIT_REQUESTS:
            logger.warning(f"Rate limit excedido para IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Muitas requisições. Tente novamente em alguns instantes."}
            )

        self.requests[client_ip].append(now)

        return await call_next(request)

    def _cleanup(self, now: datetime):
        """Remove IPs inativos e limita crescimento do dicionário"""
        minute_ago = now - timedelta(minutes=1)

        for ip in list(self.requests.keys()):
            self.requests[ip] = [t for t in self.requests[ip] if t > minute_ago]
            if not self.requests[ip]:
                del self.requests[ip]

        if len(self.requests) > MAX_TRACKED_IPS:
            sorted_ips = sorted(
                self.requests.keys(),
                key=lambda ip: self.requests[ip][-1] if self.requests[ip] else datetime.min
            )
            to_remove = len(self.requests) - MAX_TRACKED_IPS
            for ip in sorted_ips[:to_remove]:
                del self.requests[ip]
            logger.warning(f"Rate limiter: removidos {to_remove} IPs antigos (limite: {MAX_TRACKED_IPS})")

