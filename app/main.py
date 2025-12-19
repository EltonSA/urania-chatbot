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
from app.routers import auth, files, chat, admin, pages, public_files
from app.middleware.rate_limit import RateLimitMiddleware

# Configuração de logging
handlers = []
if settings.LOG_FILE:
    try:
        handlers.append(logging.FileHandler(settings.LOG_FILE))
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível criar arquivo de log {settings.LOG_FILE}: {e}")
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
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema profissional de chatbot SaaS com gerenciamento de PDFs e GIFs",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    
    # Verifica configurações importantes
    if not settings.OPENAI_API_KEY:
        logger.warning("⚠️ OPENAI_API_KEY não configurada! O chat não funcionará.")
        logger.warning("   Configure OPENAI_API_KEY no arquivo .env")
    else:
        logger.info(f"✅ OPENAI_API_KEY configurada (modelo: {settings.OPENAI_MODEL})")
    
    init_db()
    logger.info("Banco de dados inicializado")
    
    # Garante diretórios de upload
    from app.utils import ensure_upload_dirs
    ensure_upload_dirs()
    logger.info("Diretórios de upload verificados")

# Inclui routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(public_files.router)  # Arquivos públicos (sem auth)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(pages.router)

# Arquivos estáticos
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

logger.info("Aplicação configurada com sucesso")

