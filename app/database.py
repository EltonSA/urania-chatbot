"""
Configuração do banco de dados
"""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Engine do banco de dados
db_url = settings.database_url
logger.info(f"Conectando ao banco de dados: {db_url}")

# Verifica se o arquivo do banco existe
from pathlib import Path
db_path_str = db_url.replace("sqlite:///", "")
db_path = Path(db_path_str)
if db_path.exists():
    logger.info(f"Banco de dados encontrado: {db_path.absolute()}")
    # Verifica tamanho do banco
    size_mb = db_path.stat().st_size / (1024 * 1024)
    logger.info(f"Tamanho do banco: {size_mb:.2f} MB")
else:
    logger.warning(f"Banco de dados não encontrado em: {db_path.absolute()}")

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
    echo=False  # Mude para True para ver SQL queries no log
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obter sessão do banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas
    Apenas cria tabelas se não existirem (não sobrescreve dados existentes)
    """
    from app.models import FileModel, SettingModel, ChatSessionModel, ChatEventModel
    # create_all só cria tabelas que não existem, não apaga dados
    Base.metadata.create_all(bind=engine, checkfirst=True)
    logger.info("Banco de dados verificado e tabelas criadas (se necessário)")

