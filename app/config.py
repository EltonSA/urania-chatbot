"""
Configurações centralizadas da aplicação
"""
import os
from pathlib import Path
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings  # type: ignore
except ImportError:
    # Fallback para versões antigas do Pydantic
    from pydantic import BaseSettings

from pydantic import Field

# Diretório base da aplicação
BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente"""
    
    # Aplicação
    APP_NAME: str = "SaaS Chatbot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Modo debug")
    
    # Segurança
    SECRET_KEY: str = Field(default="change-me-in-production", description="Chave secreta para JWT")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_USERNAME: str = Field(default="admin", description="Usuário admin")
    ADMIN_PASSWORD: str = Field(default="admin", description="Senha admin")
    
    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Origens permitidas para CORS (separadas por vírgula)"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna lista de origens CORS"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    # Banco de dados
    DATABASE_URL: str = Field(
        default="",
        description="URL do banco de dados (deixe vazio para usar padrão)"
    )
    
    @property
    def database_url(self) -> str:
        """Retorna a URL do banco de dados com caminho absoluto"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Usa caminho absoluto para o banco de dados na pasta data
        data_dir = BASE_DIR / "data"
        data_dir.mkdir(exist_ok=True)  # Garante que a pasta data existe
        db_path = data_dir / "saas_chatbot.db"
        # SQLite no Windows funciona melhor com caminho absoluto
        db_path_str = str(db_path).replace("\\", "/")
        return f"sqlite:///{db_path_str}"
    
    def validate_production_settings(self) -> List[str]:
        """
        Valida configurações críticas para produção
        Retorna lista de avisos/erros
        """
        warnings = []
        
        if not self.DEBUG:
            # Validações apenas em produção
            if self.SECRET_KEY == "change-me-in-production":
                warnings.append("⚠️ CRÍTICO: SECRET_KEY ainda está com valor padrão! Configure uma chave segura no .env")
            
            if self.ADMIN_PASSWORD == "admin":
                warnings.append("⚠️ CRÍTICO: ADMIN_PASSWORD ainda está com valor padrão! Configure uma senha segura no .env")
            
            if not self.OPENAI_API_KEY:
                warnings.append("⚠️ AVISO: OPENAI_API_KEY não configurada. O chat não funcionará.")
        
        return warnings
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="Chave da API OpenAI")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="Modelo OpenAI a usar")
    
    # Uploads
    UPLOAD_DIR: str = Field(default="", description="Diretório de uploads (deixe vazio para usar padrão)")
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, description="Tamanho máximo de arquivo (50MB)")
    
    @property
    def upload_dir_path(self) -> Path:
        """Retorna o caminho do diretório de uploads"""
        if self.UPLOAD_DIR:
            return Path(self.UPLOAD_DIR)
        return BASE_DIR / "uploads"
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=["pdf", "gif"],
        description="Extensões permitidas"
    )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Habilitar rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Número de requisições por minuto")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Nível de log")
    LOG_FILE: Optional[str] = Field(default=None, description="Arquivo de log (opcional)")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Carrega variáveis de ambiente automaticamente
        extra = "ignore"


# Instância global de configurações
settings = Settings()

