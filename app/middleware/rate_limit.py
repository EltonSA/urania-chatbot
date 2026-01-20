"""
Rate limiting middleware
"""
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting"""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(list)
        self.cleanup_interval = timedelta(minutes=5)
        self.last_cleanup = datetime.utcnow()
    
    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Limpa requisições antigas periodicamente
        if datetime.utcnow() - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_requests()
            self.last_cleanup = datetime.utcnow()
        
        # Obtém IP do cliente
        client_ip = request.client.host if request.client else "unknown"
        
        # Verifica rate limit
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Remove requisições antigas deste IP
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > minute_ago
        ]
        
        # Verifica se excedeu o limite
        if len(self.requests[client_ip]) >= settings.RATE_LIMIT_REQUESTS:
            logger.warning(f"Rate limit excedido para IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas requisições. Tente novamente em alguns instantes."
            )
        
        # Registra requisição
        self.requests[client_ip].append(now)
        
        return await call_next(request)
    
    def _cleanup_old_requests(self):
        """Remove requisições antigas de todos os IPs"""
        minute_ago = datetime.utcnow() - timedelta(minutes=1)
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                req_time for req_time in self.requests[ip]
                if req_time > minute_ago
            ]
            if not self.requests[ip]:
                del self.requests[ip]

