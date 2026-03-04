# ============================================
# Etapa 1: Builder (dependências Python)
# ============================================
FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Etapa 2: Imagem final
# ============================================
FROM python:3.13-slim

# Usuário não-root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Virtual env do builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Código da aplicação (raiz do projeto)
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup static/ ./static/
COPY --chown=appuser:appgroup scripts/ ./scripts/
COPY --chown=appuser:appgroup *.html ./

# Diretórios graváveis (data = SQLite, uploads = PDFs/GIFs)
# Criados com dono appuser para evitar "readonly database"
RUN mkdir -p data uploads/pdfs uploads/gifs \
    && chown -R appuser:appgroup data uploads

USER appuser

# 1 worker obrigatório com SQLite (evita 502).
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
