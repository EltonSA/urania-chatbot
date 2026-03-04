"""
Aplicação principal FastAPI
"""
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import auth, files, chat, admin, pages, public_files, conversations
from app.middleware.rate_limit import RateLimitMiddleware
from app.utils import validate_openai_connection
from app.openai_status import set_status

# Configuração de logging
handlers = []
if settings.LOG_FILE:
    try:
        handlers.append(logging.FileHandler(settings.LOG_FILE))
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Não foi possível criar arquivo de log {settings.LOG_FILE}: {e}")
        handlers.append(logging.StreamHandler())
else:
    handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=handlers
)

logger = logging.getLogger(__name__)

# Cria aplicação FastAPI
# Desabilita docs em produção (DEBUG=False)
docs_url = "/docs" if settings.DEBUG else None
redoc_url = "/redoc" if settings.DEBUG else None

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema profissional de chatbot SaaS com gerenciamento de PDFs e GIFs",
    docs_url=docs_url,
    redoc_url=redoc_url
)

# CORS
# Em produção, é recomendado ser mais restritivo
allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"] if not settings.DEBUG else ["*"]
allowed_headers = ["Content-Type", "Authorization", "X-Requested-With"] if not settings.DEBUG else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=allowed_methods,
    allow_headers=allowed_headers,
)

# Rate limiting
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)

# Inicializa banco de dados
@app.on_event("startup")
async def startup_event():
    """Evento de inicialização"""
    logger.info(f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Modo debug: {settings.DEBUG}")
    
    # Valida configurações de produção
    production_warnings = settings.validate_production_settings()
    for warning in production_warnings:
        logger.warning(warning)
    
    # Verifica configurações importantes
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY não configurada! O chat não funcionará.")
        logger.warning("Configure OPENAI_API_KEY no arquivo .env")
        # Mensagem genérica para usuário (detalhes técnicos ficam nos logs)
        set_status(False, "Serviço de IA temporariamente indisponível")
    else:
        logger.info(f"OPENAI_API_KEY configurada (modelo: {settings.OPENAI_MODEL})")
        
        # Valida conexão com OpenAI
        logger.info("Validando conexão com API OpenAI...")
        is_available, error_msg = validate_openai_connection()
        
        set_status(is_available, error_msg)
        
        if is_available:
            logger.info("✅ Conexão com OpenAI validada com sucesso!")
        else:
            logger.error(f"❌ Falha na validação da conexão OpenAI: {error_msg}")
            logger.error("⚠️ O chat será bloqueado até que a conexão seja restaurada")
    
    init_db()
    logger.info("Banco de dados inicializado")
    
    # Garante hash bcrypt da senha admin no banco
    try:
        from sqlalchemy.exc import IntegrityError
        from app.database import SessionLocal
        from app.utils import get_setting, set_setting
        from app.auth import get_password_hash, verify_password
        db = SessionLocal()
        try:
            existing_hash = get_setting(db, "admin_password_hash")
            if not existing_hash:
                hashed = get_password_hash(settings.ADMIN_PASSWORD)
                set_setting(db, "admin_password_hash", hashed)
                logger.info("Hash bcrypt da senha admin gerado e armazenado no banco")
            else:
                if not verify_password(settings.ADMIN_PASSWORD, existing_hash):
                    new_hash = get_password_hash(settings.ADMIN_PASSWORD)
                    set_setting(db, "admin_password_hash", new_hash)
                    logger.info("Senha admin alterada no .env — hash bcrypt regenerado")
                else:
                    logger.info("Hash bcrypt da senha admin OK")
        finally:
            db.close()
    except IntegrityError:
        # Outro worker já inseriu admin_password_hash (múltiplos workers)
        logger.info("Hash da senha admin já definido por outro processo")
    except Exception as e:
        logger.warning("Não foi possível inicializar hash da senha no banco: %s", e)
    
    # Garante diretórios de upload
    try:
        from app.utils import ensure_upload_dirs
        ensure_upload_dirs()
        logger.info("Diretórios de upload verificados")
    except Exception as e:
        logger.warning("Diretórios de upload: %s", e)

# Health check (para Coolify, load balancers e proxies)
@app.get("/health")
def health():
    """Retorna 200 se a aplicação está no ar. Usado por Coolify e proxies."""
    return {"status": "ok"}

# Inclui routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(public_files.router)  # Arquivos públicos (sem auth)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(conversations.router)
app.include_router(pages.router)

# Arquivos estáticos
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

logger.info("Aplicação configurada com sucesso")

