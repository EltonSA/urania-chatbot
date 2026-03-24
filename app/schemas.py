"""
Schemas Pydantic para validação de dados
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class FileUpdateBody(BaseModel):
    """Schema para atualização de arquivo"""
    title: Optional[str] = None
    tags: Optional[str] = None
    description: Optional[str] = None


class FileOut(BaseModel):
    """Schema de saída para arquivo"""
    id: int
    title: Optional[str]
    file_type: str
    url: str
    tags: Optional[str]
    description: Optional[str] = None
    group_id: Optional[str] = None

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
    type: str  # "gif", "pdf" ou "image"
    url: str
    name: Optional[str] = None


class ReplyStepOut(BaseModel):
    """Um passo: texto do assistente seguido (no cliente) de anexo(s), com pausa entre texto e mídia."""
    text: str = ""
    attachments: List[AttachmentOut] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Schema para resposta do chat"""
    reply: str = ""
    attachments: List[AttachmentOut] = Field(default_factory=list)
    reply_steps: List[ReplyStepOut] = Field(default_factory=list)
    should_ask_resolution: bool = False
    needs_human_support: bool = False


class PromptBody(BaseModel):
    """Schema para atualização de prompt"""
    prompt: str = Field(..., max_length=10000)


class FeedbackBody(BaseModel):
    """Schema para feedback (Sim/Não ou solicitação de suporte)"""
    session_id: str
    resolved: bool = False
    action: Optional[str] = Field(
        default=None,
        description="Se 'support', registra pedido de suporte humano e ignora resolved",
    )


class ChatThemeSettings(BaseModel):
    """Cores e raios do chat (/widget). Campos omitidos no PUT não são alterados."""

    primary: Optional[str] = Field(None, max_length=16)
    primary_mid: Optional[str] = Field(None, max_length=16)
    primary_dark: Optional[str] = Field(None, max_length=16)
    user_bg: Optional[str] = Field(None, max_length=16)
    user_border: Optional[str] = Field(None, max_length=16)
    user_text: Optional[str] = Field(None, max_length=16)
    page_from: Optional[str] = Field(None, max_length=16)
    page_via: Optional[str] = Field(None, max_length=16)
    page_to: Optional[str] = Field(None, max_length=16)
    chat_box_bg: Optional[str] = Field(None, max_length=80)
    input_focus: Optional[str] = Field(None, max_length=16)
    bubble_radius: Optional[str] = Field(None, max_length=8)
    pdf_header_bg: Optional[str] = Field(None, max_length=16)
    pdf_title: Optional[str] = Field(None, max_length=16)


class SystemSettingsBody(BaseModel):
    """Schema para configurações do sistema"""
    root_behavior: Optional[str] = Field(None, pattern=r"^(widget|blank|custom)$")
    root_custom_url: Optional[str] = Field(None, max_length=500)
    widget_enabled: Optional[bool] = None
    satisfaction_support_button: Optional[bool] = None
    system_display_name: Optional[str] = Field(None, max_length=120)
    chat_theme: Optional[ChatThemeSettings] = None

    @validator("system_display_name")
    def strip_display_name(cls, v):
        if v is None:
            return None
        s = v.strip()
        if "\n" in s or "\r" in s:
            raise ValueError("Nome não pode conter quebras de linha")
        return s

    @validator("root_custom_url")
    def validate_safe_url(cls, v):
        if v is not None and v != "":
            if v.startswith("//"):
                raise ValueError("URL inválida")
            if not v.startswith("/") and not v.startswith("http://") and not v.startswith("https://"):
                raise ValueError("URL deve ser relativa (/) ou absoluta (https://)")
        return v


class LoginRequest(BaseModel):
    """Schema para login"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema para resposta de token"""
    access_token: str
    token_type: str = "bearer"

