"""
Schemas Pydantic para validação de dados
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class FileUpdateBody(BaseModel):
    """Schema para atualização de arquivo"""
    title: Optional[str] = None
    tags: Optional[str] = None


class FileOut(BaseModel):
    """Schema de saída para arquivo"""
    id: int
    title: Optional[str]
    file_type: str
    url: str
    tags: Optional[str]

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """Schema para mensagem de chat"""
    role: str  # "user" ou "assistant"
    content: str

    @validator("role")
    def validate_role(cls, v):
        if v not in ("user", "assistant"):
            raise ValueError("role deve ser 'user' ou 'assistant'")
        return v


class ChatRequest(BaseModel):
    """Schema para requisição de chat"""
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    history: List[ChatMessage] = Field(default_factory=list)


class AttachmentOut(BaseModel):
    """Schema para anexo na resposta"""
    type: str  # "gif" ou "pdf"
    url: str
    name: Optional[str] = None


class ChatResponse(BaseModel):
    """Schema para resposta do chat"""
    reply: str
    attachments: List[AttachmentOut] = Field(default_factory=list)
    should_ask_resolution: bool = False
    needs_human_support: bool = False


class PromptBody(BaseModel):
    """Schema para atualização de prompt"""
    prompt: str = Field(..., max_length=10000)


class FeedbackBody(BaseModel):
    """Schema para feedback"""
    session_id: str
    resolved: bool


class LoginRequest(BaseModel):
    """Schema para login"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema para resposta de token"""
    access_token: str
    token_type: str = "bearer"

