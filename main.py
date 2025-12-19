import os
import re
import json
import uuid
from io import BytesIO
from datetime import datetime
from typing import List, Optional
from collections import Counter

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, or_, distinct
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from openpyxl import Workbook
import openai  # openai 1.x


# =========================
# CONFIGURAÇÕES GERAIS
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "saas_chatbot.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
print(f"Usando banco de dados SQLite em: {DB_PATH}")

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
PDF_DIR = os.path.join(UPLOAD_DIR, "pdfs")
GIF_DIR = os.path.join(UPLOAD_DIR, "gifs")

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(GIF_DIR, exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("⚠️ AVISO: defina a variável de ambiente OPENAI_API_KEY antes de usar o /chat")


# =========================
# BANCO DE DADOS
# =========================

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class FileModel(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # "pdf" ou "gif"
    title = Column(String, nullable=True)
    tags = Column(String, nullable=True)  # separado por vírgula
    created_at = Column(DateTime, default=datetime.utcnow)


class SettingModel(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text, nullable=True)


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Integer, nullable=True)  # 1=sim, 0=nao, None=sem feedback


class ChatEventModel(Base):
    __tablename__ = "chat_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# MODELOS Pydantic
# =========================

class FileUpdateBody(BaseModel):
    title: Optional[str] = None
    tags: Optional[str] = None


class FileOut(BaseModel):
    id: int
    title: Optional[str]
    file_type: str
    url: str
    tags: Optional[str]

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    role: str  # "user" ou "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: List[ChatMessage] = Field(default_factory=list)


class AttachmentOut(BaseModel):
    type: str  # "gif" ou "pdf"
    url: str
    name: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    attachments: List[AttachmentOut] = Field(default_factory=list)
    should_ask_resolution: bool = False


class PromptBody(BaseModel):
    prompt: str


class FeedbackBody(BaseModel):
    session_id: str
    resolved: bool


# =========================
# APP FASTAPI
# =========================

app = FastAPI(title="SaaS Chatbot com PDFs e GIFs", version="0.3.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# HELPERS
# =========================

def build_file_url(file: FileModel) -> str:
    if file.file_type == "pdf":
        return f"/files/pdf/{file.id}"
    if file.file_type == "gif":
        return f"/files/gif/{file.id}"
    return ""


def get_setting(db: Session, key: str) -> Optional[str]:
    setting = db.query(SettingModel).filter_by(key=key).first()
    return setting.value if setting else None


def set_setting(db: Session, key: str, value: str):
    setting = db.query(SettingModel).filter_by(key=key).first()
    if setting:
        setting.value = value
    else:
        setting = SettingModel(key=key, value=value)
        db.add(setting)
    db.commit()


def get_or_create_session(db: Session, session_id: Optional[str]) -> str:
    if not session_id:
        session_id = uuid.uuid4().hex

    s = db.query(ChatSessionModel).filter_by(session_id=session_id).first()
    if not s:
        s = ChatSessionModel(session_id=session_id)
        db.add(s)
        db.commit()
        db.refresh(s)
    else:
        s.last_activity_at = datetime.utcnow()
        db.commit()

    return session_id


def log_event(db: Session, session_id: str, event_type: str, content: Optional[str] = None):
    ev = ChatEventModel(session_id=session_id, event_type=event_type, content=content)
    db.add(ev)

    s = db.query(ChatSessionModel).filter_by(session_id=session_id).first()
    if s:
        s.last_activity_at = datetime.utcnow()

    db.commit()


def search_relevant_files(db: Session, query: str, limit: int = 8) -> List[FileModel]:
    words = re.split(r"\W+", (query or "").lower())
    words = [w for w in words if len(w) >= 3]

    query_db = db.query(FileModel)

    if not words:
        return query_db.order_by(FileModel.created_at.desc()).limit(limit).all()

    conditions = []
    for w in words:
        pattern = f"%{w}%"
        conditions.append(FileModel.title.ilike(pattern))
        conditions.append(FileModel.tags.ilike(pattern))

    files = (
        query_db
        .filter(or_(*conditions))
        .order_by(FileModel.created_at.desc())
        .limit(limit)
        .all()
    )

    if not files:
        files = query_db.order_by(FileModel.created_at.desc()).limit(limit).all()

    return files


def build_system_prompt(files: List[FileModel], custom_prompt: str = "") -> str:
    files_description = []
    for f in files:
        files_description.append(
            f'- ID: {f.id}, tipo: {f.file_type}, título: "{f.title or f.original_name}", tags: {f.tags or ""}'
        )
    files_block = "\n".join(files_description) if files_description else "Nenhum arquivo relevante encontrado."

    base_rules = f"""
Você é um assistente de suporte que atende clientes no site.

Você tem acesso a materiais (PDFs e GIFs) que podem ser enviados ao usuário.
Cada material tem: ID, tipo (pdf/gif), título, tags.

MATERIAIS DISPONÍVEIS:
{files_block}

Sua resposta DEVE ser SEMPRE um JSON válido, exatamente no formato:

{{
  "reply": "texto da resposta ao usuário",
  "attachments": [
    {{
      "type": "gif" ou "pdf",
      "file_id": ID_DO_ARQUIVO,
      "name": "nome legível (opcional)"
    }}
  ],
  "should_ask_resolution": true ou false
}}

Regras IMPORTANTES:
- Se não precisar enviar nada, use "attachments": [].
- Só use IDs que estejam na lista de materiais disponíveis.
- Use GIFs quando ajudarem a explicar (passo a passo visual).
- Use PDFs quando forem materiais mais completos.
- NUNCA saia do formato JSON.

Regra do should_ask_resolution:
- Use true APENAS quando a mensagem do usuário for uma dúvida/solicitação de suporte.
- Use false quando for cumprimento, conversa, agradecimento, teste de mensagem, ou fora de suporte.
- Se estiver em dúvida, prefira false.
""".strip()

    if custom_prompt and custom_prompt.strip():
        return custom_prompt.strip() + "\n\n" + base_rules
    return base_rules


def ensure_chat_started_on_first_user_message(db: Session, session_id: str):
    """
    Garante que 'chat_started' seja gravado UMA ÚNICA vez por sessão,
    exatamente na primeira mensagem do usuário.
    """
    first_user_msg = (
        db.query(ChatEventModel)
        .filter_by(session_id=session_id, event_type="user_message")
        .first()
    )
    if not first_user_msg:
        log_event(db, session_id, "chat_started")


# =========================
# ENDPOINTS DE ARQUIVOS
# =========================

@app.post("/admin/upload", response_model=FileOut)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    title: str = Form(""),
    tags: str = Form(""),
    db: Session = Depends(get_db)
):
    file_type = (file_type or "").lower().strip()
    if file_type not in ("pdf", "gif"):
        raise HTTPException(status_code=400, detail="file_type deve ser 'pdf' ou 'gif'")

    folder = PDF_DIR if file_type == "pdf" else GIF_DIR

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = f"{timestamp}_{(file.filename or 'arquivo').replace(' ', '_')}"
    filepath = os.path.join(folder, safe_name)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    db_file = FileModel(
        filename=safe_name,
        original_name=file.filename or safe_name,
        file_type=file_type,
        title=title or (file.filename or safe_name),
        tags=tags
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return FileOut(
        id=db_file.id,
        title=db_file.title,
        file_type=db_file.file_type,
        url=build_file_url(db_file),
        tags=db_file.tags
    )


@app.get("/admin/files", response_model=List[FileOut])
def list_files(db: Session = Depends(get_db)):
    files = db.query(FileModel).order_by(FileModel.created_at.desc()).all()
    return [
        FileOut(
            id=f.id,
            title=f.title,
            file_type=f.file_type,
            url=build_file_url(f),
            tags=f.tags
        )
        for f in files
    ]


@app.put("/admin/files/{file_id}")
def update_file(file_id: int, body: FileUpdateBody, db: Session = Depends(get_db)):
    file = db.query(FileModel).get(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    if body.title is not None:
        file.title = body.title
    if body.tags is not None:
        file.tags = body.tags

    db.commit()
    db.refresh(file)

    return {
        "id": file.id,
        "title": file.title,
        "tags": file.tags,
        "file_type": file.file_type,
        "url": build_file_url(file),
    }


@app.delete("/admin/files/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db)):
    file = db.query(FileModel).get(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    folder = PDF_DIR if file.file_type == "pdf" else GIF_DIR
    filepath = os.path.join(folder, file.filename)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Erro ao remover arquivo físico {filepath}: {e}")

    db.delete(file)
    db.commit()
    return {"ok": True}


@app.get("/files/pdf/{file_id}")
def serve_pdf(file_id: int, db: Session = Depends(get_db)):
    file = db.query(FileModel).get(file_id)
    if not file or file.file_type != "pdf":
        raise HTTPException(status_code=404, detail="PDF não encontrado")

    filepath = os.path.join(PDF_DIR, file.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Arquivo físico não encontrado")

    return FileResponse(filepath, media_type="application/pdf")


@app.get("/files/gif/{file_id}")
def serve_gif(file_id: int, db: Session = Depends(get_db)):
    file = db.query(FileModel).get(file_id)
    if not file or file.file_type != "gif":
        raise HTTPException(status_code=404, detail="GIF não encontrado")

    filepath = os.path.join(GIF_DIR, file.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Arquivo físico não encontrado")

    return FileResponse(filepath, media_type="image/gif")


# =========================
# ENDPOINTS DE PROMPT
# =========================

@app.get("/admin/prompt")
def get_prompt(db: Session = Depends(get_db)):
    prompt = get_setting(db, "system_prompt") or ""
    return {"prompt": prompt}


@app.put("/admin/prompt")
def save_prompt(body: PromptBody, db: Session = Depends(get_db)):
    set_setting(db, "system_prompt", body.prompt or "")
    return {"ok": True}


# =========================
# FEEDBACK (RESOLVEU?)
# =========================

@app.post("/feedback")
def feedback(body: FeedbackBody, db: Session = Depends(get_db)):
    s = db.query(ChatSessionModel).filter_by(session_id=body.session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")

    s.resolved = 1 if body.resolved else 0
    s.last_activity_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


# =========================
# CHAT (API)
# =========================

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    if not openai.api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY não configurada no servidor.")

    # sessão (garante que a sessão exista)
    session_id = get_or_create_session(db, req.session_id)

    # chat iniciado = primeira mensagem do usuário
    ensure_chat_started_on_first_user_message(db, session_id)

    # registra pergunta do usuário
    log_event(db, session_id, "user_message", content=req.message)

    relevant_files = search_relevant_files(db, req.message, limit=8)
    custom_prompt = get_setting(db, "system_prompt") or ""
    system_prompt = build_system_prompt(relevant_files, custom_prompt)

    messages = [{"role": "system", "content": system_prompt}]

    if req.history:
        for m in req.history:
            messages.append({"role": m.role, "content": m.content})

    messages.append({"role": "user", "content": req.message})

    try:
        completion = openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content
    except Exception as e:
        print("Erro ao chamar OpenAI:", e)
        raise HTTPException(status_code=500, detail="Erro ao chamar o modelo de IA.")

    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        data = {}

    reply_text = data.get("reply", "") or ""
    raw_attachments = data.get("attachments", []) or []
    should_ask_resolution = bool(data.get("should_ask_resolution", False))

    # registra resposta do bot
    log_event(db, session_id, "bot_message", content=reply_text)

    attachments_out: List[AttachmentOut] = []

    for att in raw_attachments:
        file_id = att.get("file_id")
        att_type = att.get("type")
        name = att.get("name")

        if file_id is None or att_type not in ("pdf", "gif"):
            continue

        file = db.query(FileModel).get(int(file_id))
        if not file or file.file_type != att_type:
            continue

        url = build_file_url(file)
        attachments_out.append(AttachmentOut(type=att_type, url=url, name=name or file.title))

        if att_type == "pdf":
            log_event(db, session_id, "pdf_sent", content=str(file.id))
        elif att_type == "gif":
            log_event(db, session_id, "gif_sent", content=str(file.id))

    return ChatResponse(
        reply=reply_text,
        attachments=attachments_out,
        should_ask_resolution=should_ask_resolution
    )


# =========================
# DASHBOARD (API)
# =========================

@app.get("/admin/stats")
def admin_stats(db: Session = Depends(get_db)):
    total_messages = (
        db.query(ChatEventModel)
        .filter(ChatEventModel.event_type.in_(["user_message", "bot_message"]))
        .count()
    )

    # chats iniciados = sessões únicas que tiveram evento chat_started
    chats_initiated = (
        db.query(distinct(ChatEventModel.session_id))
        .filter(ChatEventModel.event_type == "chat_started")
        .count()
    )

    pdfs_sent = db.query(ChatEventModel).filter_by(event_type="pdf_sent").count()
    gifs_sent = db.query(ChatEventModel).filter_by(event_type="gif_sent").count()

    resolved_total = db.query(ChatSessionModel).filter(ChatSessionModel.resolved.in_([0, 1])).count()
    resolved_yes = db.query(ChatSessionModel).filter_by(resolved=1).count()
    resolution_rate = round((resolved_yes / resolved_total) * 100, 1) if resolved_total else 0

    user_msgs = db.query(ChatEventModel).filter_by(event_type="user_message").all()
    texts = [m.content.strip() for m in user_msgs if m.content and m.content.strip()]
    counter = Counter(texts)
    top_questions = [{"question": q, "count": c} for q, c in counter.most_common(10)]

    return {
        "total_messages": total_messages,
        "chats_initiated": chats_initiated,
        "pdfs_sent": pdfs_sent,
        "gifs_sent": gifs_sent,
        "resolved_yes": resolved_yes,
        "resolved_total": resolved_total,
        "resolution_rate": resolution_rate,
        "top_questions": top_questions,
    }


@app.get("/admin/export.xlsx")
def export_excel(db: Session = Depends(get_db)):
    stats = admin_stats(db)

    wb = Workbook()
    ws = wb.active
    ws.title = "Dashboard"

    ws.append(["Métrica", "Valor"])
    ws.append(["Total de mensagens", stats["total_messages"]])
    ws.append(["Chats iniciados", stats["chats_initiated"]])
    ws.append(["PDFs enviados", stats["pdfs_sent"]])
    ws.append(["GIFs enviados", stats["gifs_sent"]])
    ws.append(["Resoluções (Sim)", stats["resolved_yes"]])
    ws.append(["Resoluções (Total)", stats["resolved_total"]])
    ws.append(["Taxa de resolução (%)", stats["resolution_rate"]])

    ws2 = wb.create_sheet("Perguntas_frequentes")
    ws2.append(["Pergunta", "Ocorrências"])
    for item in stats["top_questions"]:
        ws2.append([item["question"], item["count"]])

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=dashboard.xlsx"}
    )


# =========================
# PÁGINAS HTML
# =========================

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return FileResponse(os.path.join(BASE_DIR, "admin.html"))


@app.get("/widget", response_class=HTMLResponse)
def widget_page():
    return FileResponse(os.path.join(BASE_DIR, "widget.html"))


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    return FileResponse(os.path.join(BASE_DIR, "dashboard.html"))


@app.get("/")
def root():
    return {
        "message": "SaaS Chatbot com PDFs e GIFs está rodando.",
        "admin": "/admin",
        "widget": "/widget",
        "dashboard": "/dashboard",
        "docs": "/docs"
    }


# =========================
# STATIC
# =========================

STATIC_DIR = os.path.join(BASE_DIR, "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
