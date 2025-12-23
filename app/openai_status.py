"""
Módulo para gerenciar o status da conexão OpenAI
"""
from datetime import datetime
from typing import Optional, Dict

# Variável global para armazenar o status da conexão OpenAI
_connection_status: Dict = {
    "available": False,
    "error_message": None,
    "last_check": None
}


def get_status() -> Dict:
    """Retorna o status atual da conexão OpenAI"""
    return _connection_status.copy()


def set_status(available: bool, error_message: Optional[str] = None):
    """Define o status da conexão OpenAI"""
    global _connection_status
    _connection_status = {
        "available": available,
        "error_message": error_message,
        "last_check": datetime.utcnow()
    }


def is_available() -> bool:
    """Verifica se a conexão OpenAI está disponível"""
    return _connection_status.get("available", False)


def get_error_message() -> Optional[str]:
    """Retorna a mensagem de erro, se houver"""
    return _connection_status.get("error_message")


