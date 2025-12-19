# Urânia + - Sistema de Chatbot Inteligente

Sistema profissional de chatbot SaaS desenvolvido para a **Urânia**, com gerenciamento inteligente de documentos (PDFs e GIFs), interface administrativa completa e dashboard de métricas em tempo real.

## 📖 Sobre o Sistema

O **Urânia +** é uma solução completa de atendimento automatizado que permite:

- 🤖 **Chatbot Inteligente** - Respostas automáticas usando IA (OpenAI GPT)
- 📄 **Gerenciamento de Documentos** - Upload e organização de PDFs e GIFs educativos
- 📊 **Dashboard de Métricas** - Análise de desempenho, feedbacks e perguntas frequentes
- 🔐 **Painel Administrativo** - Interface completa para gerenciar conteúdo e configurações
- 📱 **Widget de Chat** - Interface moderna e responsiva para os clientes
- 📈 **Estatísticas Avançadas** - Métricas de resolução, detração e redirecionamento para suporte

## 🚀 Características Técnicas

- ✅ **Autenticação JWT** - Sistema seguro de autenticação com tokens
- ✅ **Rate Limiting** - Proteção contra abuso e sobrecarga
- ✅ **Logging Profissional** - Sistema completo de logs estruturados
- ✅ **Arquitetura Modular** - Código organizado, escalável e manutenível
- ✅ **Validação de Dados** - Schemas Pydantic para validação robusta
- ✅ **Tratamento de Erros** - Tratamento adequado de exceções
- ✅ **CORS Configurável** - Segurança configurável para diferentes ambientes
- ✅ **Documentação Automática** - Swagger/ReDoc integrado (apenas em desenvolvimento)
- ✅ **Categorização Inteligente** - IA agrupa perguntas similares automaticamente
- ✅ **Exportação de Dados** - Exportação de estatísticas para Excel

## 📋 Pré-requisitos

- Python 3.8+
- pip

## 🔧 Instalação

1. **Clone o repositório** (ou use o código existente)

2. **Crie um ambiente virtual** (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**:
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

Edite o arquivo `.env` e configure:
- `SECRET_KEY`: Gere uma chave secreta forte (obrigatório em produção)
- `ADMIN_PASSWORD`: Defina uma senha segura para o admin (obrigatório em produção)
- `OPENAI_API_KEY`: Sua chave da API OpenAI (obrigatório para chat)
- `CORS_ORIGINS`: Origens permitidas (ajuste conforme necessário)
- `DEBUG`: Defina como `False` em produção

**Para gerar uma SECRET_KEY segura:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

**⚠️ IMPORTANTE PARA PRODUÇÃO:**
- Altere `SECRET_KEY` e `ADMIN_PASSWORD` dos valores padrão
- Defina `DEBUG=False`
- Configure `CORS_ORIGINS` apenas com seus domínios permitidos
- As documentações (`/docs` e `/redoc`) serão desabilitadas automaticamente quando `DEBUG=False`

## 🏃 Executando

### Desenvolvimento

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Produção

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

A aplicação estará disponível em:
- **Widget de Chat**: http://localhost:8000/widget
- **Painel Admin**: http://localhost:8000/admin
- **Dashboard**: http://localhost:8000/dashboard
- **Login**: http://localhost:8000/login
- **API**: http://localhost:8000
- **Documentação** (apenas em modo debug): http://localhost:8000/docs

## 📁 Estrutura do Projeto

```
.
├── app/                     # Aplicação principal (backend)
│   ├── __init__.py
│   ├── main.py              # Aplicação FastAPI principal
│   ├── config.py             # Configurações centralizadas
│   ├── database.py           # Configuração do banco de dados
│   ├── models.py             # Modelos SQLAlchemy
│   ├── schemas.py            # Schemas Pydantic (validação)
│   ├── auth.py               # Autenticação JWT
│   ├── utils.py              # Funções utilitárias (IA, busca, etc.)
│   ├── routers/              # Rotas da API organizadas
│   │   ├── auth.py           # Autenticação
│   │   ├── files.py          # Gerenciamento de arquivos
│   │   ├── chat.py           # Endpoint do chat
│   │   ├── admin.py          # Estatísticas e exportação
│   │   ├── pages.py          # Páginas HTML
│   │   └── public_files.py   # Servir arquivos públicos
│   └── middleware/           # Middlewares
│       └── rate_limit.py     # Rate limiting
├── static/                   # Arquivos estáticos (CSS/JS)
│   ├── admin.css
│   ├── admin.js
│   ├── dashboard.css
│   └── dashboard.js
├── data/                     # Banco de dados SQLite
│   └── saas_chatbot.db
├── uploads/                  # Arquivos enviados
│   ├── pdfs/                 # PDFs educativos
│   └── gifs/                 # GIFs explicativos
├── widget.html               # Interface do chat (widget)
├── admin.html                # Painel administrativo
├── dashboard.html            # Dashboard de métricas
├── login.html                # Página de login
├── .env                      # Variáveis de ambiente (criar)
├── .env.example              # Exemplo de configuração
├── requirements.txt          # Dependências Python
└── README.md                 # Este arquivo
```

## 🔐 Autenticação

### Login

```bash
POST /auth/login
{
  "username": "admin",
  "password": "sua-senha"
}
```

Resposta:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Usando o Token

Para acessar rotas protegidas, inclua o token no header:
```
Authorization: Bearer eyJ...
```

## 📚 Endpoints Principais

### Páginas Web
- `GET /widget` - Widget de chat para clientes
- `GET /admin` - Painel administrativo (requer autenticação)
- `GET /dashboard` - Dashboard de métricas (requer autenticação)
- `GET /login` - Página de login

### API Pública
- `GET /` - Informações da API
- `POST /chat` - Chat com o bot (processa mensagens e retorna respostas)
- `POST /chat/feedback` - Feedback do usuário (Sim/Não)
- `GET /files/pdf/{id}` - Visualizar/Download de PDF
- `GET /files/gif/{id}` - Visualizar GIF

### API Administrativa (requerem autenticação JWT)
- `POST /auth/login` - Autenticação e obtenção de token
- `POST /admin/files/upload` - Upload de arquivo (PDF/GIF)
- `GET /admin/files` - Listar todos os arquivos
- `GET /admin/files/stats` - Estatísticas de arquivos (tamanho, quantidade)
- `PUT /admin/files/{id}` - Atualizar arquivo (título, tags)
- `DELETE /admin/files/{id}` - Deletar arquivo
- `GET /admin/prompt` - Obter prompt do sistema
- `PUT /admin/prompt` - Atualizar prompt do sistema
- `GET /admin/stats` - Estatísticas completas do sistema
- `GET /admin/export.xlsx` - Exportar estatísticas para Excel

## 🛡️ Segurança

- ✅ Autenticação JWT
- ✅ Rate limiting configurável
- ✅ CORS configurável
- ✅ Validação de tamanho de arquivo
- ✅ Validação de extensões permitidas
- ✅ Senhas hasheadas (bcrypt)

## 📝 Logging

O sistema registra:
- Inicialização da aplicação
- Erros e exceções
- Tentativas de rate limit
- Operações críticas

Configure o nível de log no `.env`:
```
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🎯 Funcionalidades Principais

### Widget de Chat
- Interface moderna e responsiva
- Suporte a anexos (PDFs e GIFs)
- Indicador de digitação em tempo real
- Feedback de resolução (Sim/Não)
- Redirecionamento para suporte humano via WhatsApp
- Histórico de conversas

### Painel Administrativo
- Gerenciamento de arquivos (upload, edição, exclusão)
- Configuração do prompt do sistema
- Busca e filtragem de arquivos
- Estatísticas de uploads (tipo, tamanho total)
- Interface drag-and-drop para uploads
- Visualização de arquivos diretamente no painel

### Dashboard de Métricas
- Total de mensagens e chats iniciados
- Taxa de resolução (Sim/Não)
- Contagem de PDFs e GIFs enviados
- Detratores (usuários sem feedback)
- Redirecionamentos para suporte humano
- Top 10 perguntas frequentes (categorizadas por IA)
- Arquivos que não resolveram problemas
- Exportação de dados para Excel

## 🔄 Migração do Código Antigo

O código antigo em `main.py` foi refatorado para uma estrutura modular. Para usar a nova versão:

1. Mantenha os arquivos HTML e estáticos na raiz
2. Use `uvicorn app.main:app` em vez de `uvicorn main:app`
3. Configure o arquivo `.env` conforme descrito acima

## 🐛 Troubleshooting

### Erro: "SECRET_KEY não configurada"
- Configure `SECRET_KEY` no arquivo `.env`

### Erro: "OPENAI_API_KEY não configurada"
- Configure `OPENAI_API_KEY` no arquivo `.env`

### Erro: "ModuleNotFoundError"
- Certifique-se de que todas as dependências estão instaladas: `pip install -r requirements.txt`

### Erro de autenticação
- Verifique se o usuário e senha estão corretos no `.env`
- Verifique se o token está sendo enviado corretamente no header

## 🔧 Tecnologias Utilizadas

- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **Pydantic** - Validação de dados
- **OpenAI API** - Integração com GPT para respostas inteligentes
- **JWT (python-jose)** - Autenticação segura
- **bcrypt (passlib)** - Hash de senhas
- **Uvicorn** - Servidor ASGI de alta performance
- **OpenPyXL** - Exportação de dados para Excel

## 📄 Licença

Este projeto é de uso interno da **Urânia**.

## 📞 Suporte

Para dúvidas ou suporte técnico, entre em contato com a equipe de desenvolvimento.

---

**Urânia +** - Sistema de Chatbot Inteligente v1.0.0

