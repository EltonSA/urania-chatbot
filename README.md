# Urânia + - Sistema de Chatbot Inteligente

Sistema profissional de chatbot SaaS desenvolvido para a **Urânia**, com gerenciamento inteligente de documentos (PDFs e GIFs), interface administrativa completa e dashboard de métricas em tempo real.

## 📖 Sobre o Sistema

O **Urânia +** é uma solução completa de atendimento automatizado que permite:

- 🤖 **Chatbot Inteligente** - Respostas automáticas usando IA (OpenAI GPT)
- 📄 **Gerenciamento de Documentos** - Upload e organização de PDFs e GIFs educativos
- 📊 **Dashboard de Métricas** - Análise de desempenho, feedbacks e perguntas frequentes
- 🔐 **Painel Administrativo** - Interface completa para gerenciar conteúdo e configurações
- 📱 **Widget de Chat** - Interface moderna e responsiva para os clientes
- 💬 **Widget Flutuante** - Botão de chat embeddable para qualquer página (único `<script>`)
- 📈 **Estatísticas Avançadas** - Métricas de resolução, detração e redirecionamento para suporte

## 🚀 Características Técnicas

- ✅ **Autenticação JWT** - Tokens seguros com cookies `httponly` e flag `secure` automática em produção
- ✅ **Senhas com bcrypt** - Hash bcrypt direto (sem passlib), compatível com Python 3.13+
- ✅ **Proteção brute force** - Bloqueio automático após 5 tentativas falhas de login por IP (15 min)
- ✅ **Rate Limiting robusto** - Proteção contra DDoS com limite de 10.000 IPs rastreados e cleanup automático
- ✅ **Validação de uploads** - Verificação de magic bytes (assinatura real) dos arquivos PDF e GIF
- ✅ **Proteção contra Open Redirect** - URLs de redirecionamento validadas como relativas
- ✅ **Logging Profissional** - Sistema completo de logs estruturados com auditoria
- ✅ **Arquitetura Modular** - Código organizado, escalável e manutenível
- ✅ **Validação de Dados** - Schemas Pydantic para todos os endpoints (incluindo configurações)
- ✅ **Tratamento de Erros** - Mensagens genéricas para o usuário, detalhes técnicos apenas nos logs
- ✅ **CORS Configurável** - Segurança configurável para diferentes ambientes
- ✅ **Documentação Automática** - Swagger/ReDoc integrado (apenas em desenvolvimento)
- ✅ **Categorização Inteligente** - IA agrupa perguntas similares automaticamente
- ✅ **Exportação de Dados** - Exportação de estatísticas para Excel
- ✅ **Logs de auditoria** - Registro de login, upload, edição, exclusão e alterações de configuração
- ✅ **Validação OpenAI gratuita** - Verificação da API key no startup sem consumir tokens

## 📋 Pré-requisitos

### Desenvolvimento Local
- Python 3.10+ (compatível com 3.13)
- pip
- 2GB RAM mínimo
- 1GB espaço em disco

### Produção (VPS/Servidor)

#### Requisitos Mínimos
- **CPU**: 1 core (2.0 GHz+)
- **RAM**: 1GB (2GB recomendado)
- **Disco**: 10GB espaço livre
- **Sistema Operacional**: Linux (Ubuntu 20.04+ / Debian 11+ / CentOS 8+)
- **Python**: 3.10 ou superior (compatível com 3.13)
- **Conexão**: Internet estável para API OpenAI

#### Requisitos Recomendados
- **CPU**: 2 cores (2.4 GHz+)
- **RAM**: 4GB
- **Disco**: 20GB+ (SSD recomendado)
- **Sistema Operacional**: Ubuntu 22.04 LTS ou Debian 12
- **Python**: 3.10 ou superior
- **Banco de Dados**: SQLite (padrão) ou PostgreSQL (para alta carga)
- **Servidor Web**: Nginx como reverse proxy (recomendado)
- **Process Manager**: PM2, Supervisor ou systemd

#### Para Alta Carga (1000+ usuários simultâneos)
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Disco**: 50GB+ SSD
- **Banco de Dados**: PostgreSQL ou MySQL
- **Load Balancer**: Nginx ou HAProxy
- **Workers**: 4-8 workers Uvicorn

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
- A rota raiz `/` é configurável pelo painel de Configurações (padrão: redirecionar para `/widget`)

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
- **Configurações**: http://localhost:8000/settings
- **Login**: http://localhost:8000/login
- **API**: http://localhost:8000
- **Documentação** (apenas em modo debug): http://localhost:8000/docs

### Docker

Build da imagem (na raiz do projeto):

```bash
docker build -t urania-plus .
```

Execução com variáveis de ambiente e volumes para persistir banco e uploads:

```bash
docker run -p 8000:8000 --env-file .env \
  -v urania-data:/app/data \
  -v urania-uploads:/app/uploads \
  urania-plus
```

- `--env-file .env` — carrega SECRET_KEY, ADMIN_PASSWORD, OPENAI_API_KEY, etc.
- `-v urania-data:/app/data` — persiste o SQLite
- `-v urania-uploads:/app/uploads` — persiste PDFs e GIFs enviados

A imagem usa usuário não-root e cria os diretórios `data/` e `uploads/` com permissão de escrita, evitando o erro "readonly database".

### Produção em VPS/Servidor

#### Opção 1: Uvicorn Direto (Simples)
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Opção 2: Com Nginx (Recomendado)

**1. Configure Nginx** (`/etc/nginx/sites-available/urania`):
```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**2. Execute a aplicação:**
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
```

#### Opção 3: Com PM2 (Gerenciamento de Processos)

**1. Instale PM2:**
```bash
npm install -g pm2
```

**2. Crie arquivo `ecosystem.config.js`:**
```javascript
module.exports = {
  apps: [{
    name: 'urania-chatbot',
    script: 'uvicorn',
    args: 'app.main:app --host 0.0.0.0 --port 8000 --workers 4',
    interpreter: 'python3',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    }
  }]
}
```

**3. Inicie com PM2:**
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

#### Opção 4: Com systemd (Serviço Linux)

**1. Crie arquivo `/etc/systemd/system/urania.service`:**
```ini
[Unit]
Description=Urânia + Chatbot API
After=network.target

[Service]
Type=simple
User=seu-usuario
WorkingDirectory=/caminho/para/projeto
Environment="PATH=/caminho/para/venv/bin"
ExecStart=/caminho/para/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

**2. Ative o serviço:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable urania
sudo systemctl start urania
sudo systemctl status urania
```

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
│   ├── auth.py               # Autenticação JWT + bcrypt
│   ├── utils.py              # Funções utilitárias (IA, busca, etc.)
│   ├── openai_status.py      # Status da conexão OpenAI
│   ├── routers/              # Rotas da API organizadas
│   │   ├── auth.py           # Login/logout + proteção brute force
│   │   ├── files.py          # Upload com validação de magic bytes
│   │   ├── chat.py           # Chat + registro de mensagens
│   │   ├── admin.py          # Estatísticas, backup e configurações
│   │   ├── pages.py          # Páginas HTML + proteção open redirect
│   │   ├── public_files.py   # Servir arquivos públicos
│   │   └── conversations.py  # Gerenciamento de conversas
│   └── middleware/           # Middlewares
│       └── rate_limit.py     # Rate limiting (anti-DDoS)
├── static/                   # Arquivos estáticos (CSS/JS)
│   ├── admin.css
│   ├── admin.js
│   ├── dashboard.css
│   ├── dashboard.js
│   └── chat-widget.js        # Widget flutuante embeddable
├── scripts/                  # Scripts utilitários
│   ├── backup.py             # Script de backup
│   ├── restore.py            # Script de restauração
│   └── fix_db_permissions.py # Ajusta permissões do SQLite (Linux)
├── data/                     # Banco de dados SQLite
│   └── saas_chatbot.db
├── uploads/                  # Arquivos enviados
│   ├── pdfs/                 # PDFs educativos
│   └── gifs/                 # GIFs explicativos
├── widget.html               # Interface do chat (widget)
├── admin.html                # Painel administrativo
├── dashboard.html            # Dashboard de métricas
├── login.html                # Página de login
├── settings.html             # Configurações do sistema
├── .dockerignore             # Ignora arquivos no build Docker
├── .env                      # Variáveis de ambiente (criar)
├── .env.example              # Exemplo de configuração
├── Dockerfile                # Build da imagem Docker
├── requirements.txt          # Dependências Python
└── README.md                 # Este arquivo
```

## 🤖 Como a IA Funciona e Seleciona Arquivos

O sistema usa um processo inteligente em duas etapas para decidir qual arquivo enviar ao cliente:

### Etapa 1: Busca de Arquivos Relevantes (Sistema)

Quando o cliente envia uma mensagem, o sistema busca automaticamente arquivos relevantes no banco de dados:

1. **Extração de palavras-chave**: O sistema extrai palavras da mensagem do cliente (mínimo 3 caracteres)
   - Exemplo: "Como alterar minha senha?" → ["como", "alterar", "minha", "senha"]

2. **Busca no banco de dados**: Procura nos campos `título` e `tags` dos arquivos
   - Usa busca parcial (LIKE) - encontra "senha" em "alterar senha", "esqueci senha", etc.
   - Limita a 8 arquivos mais relevantes

3. **Fallback**: Se não encontrar nada, retorna os 8 arquivos mais recentes

### Etapa 2: Decisão da IA (OpenAI GPT)

A IA recebe a lista pré-filtrada de arquivos e decide quais enviar:

1. **Análise contextual**: A IA analisa:
   - O contexto da conversa
   - A pergunta específica do cliente
   - Os arquivos disponíveis na lista
   - Qual arquivo melhor responde à dúvida

2. **Decisão inteligente**: A IA escolhe:
   - **GIFs** para passo a passo visual e demonstrações rápidas
   - **PDFs** para documentação completa e materiais extensos
   - **Nenhum arquivo** se a pergunta não requer material adicional

3. **Resposta estruturada**: A IA retorna um JSON com:
   - Texto da resposta
   - Lista de arquivos a anexar (se houver)
   - Se deve perguntar se resolveu o problema

### Exemplo Prático

```
Cliente: "Esqueci minha senha, como recupero?"

1. Sistema busca arquivos:
   ✅ Encontra: "001_02_Como_faco_se_esquecer_a_senha.gif" (tags: "senha, recuperar, esqueci")
   ✅ Encontra: "alterar_senha.pdf" (tags: "senha, alterar")

2. Sistema envia para IA:
   - Lista de arquivos encontrados
   - Mensagem do cliente
   - Histórico da conversa

3. IA decide:
   - GIF é mais adequado (passo a passo visual)
   - Responde: "Vou te mostrar como recuperar sua senha!"
   - Retorna: {"attachments": [{"type": "gif", "file_id": 5}]}

4. Sistema envia o GIF para o cliente
```

## 📝 Dicas para Cadastrar Arquivos

Para que a IA encontre e selecione os arquivos corretos, siga estas dicas:

### 1. Títulos Descritivos ✅

**❌ Evite:**
- "arquivo1.pdf"
- "documento.pdf"
- "gif_001.gif"

**✅ Use:**
- "Como alterar senha"
- "Tutorial de elaboração de horário"
- "Passo a passo para recuperar senha"

### 2. Tags Relevantes ✅

Adicione palavras-chave relacionadas ao conteúdo do arquivo:

**Exemplo para um arquivo sobre senha:**
```
Tags: senha, login, autenticação, recuperar, alterar, acesso
```

**Exemplo para um arquivo sobre horário:**
```
Tags: horário, turno, turma, grade, elaboração, criação
```

### 3. Organização por Contexto ✅

- Use tags consistentes para arquivos relacionados
- Agrupe arquivos do mesmo tema com tags similares
- Mantenha uma nomenclatura padronizada

### 4. Quando Usar GIF vs PDF

**Use GIF quando:**
- For um tutorial passo a passo visual
- Precisar mostrar uma demonstração rápida
- O conteúdo for curto e visual

**Use PDF quando:**
- For documentação completa
- O material for extenso
- Precisar de um guia detalhado

### 5. Boas Práticas

1. **Seja específico**: Títulos como "Como fazer X" são melhores que "Documento sobre X"
2. **Use sinônimos nas tags**: Adicione variações de palavras (ex: "senha", "password", "acesso")
3. **Organize por tema**: Agrupe arquivos relacionados com tags comuns
4. **Revise regularmente**: Verifique quais arquivos são mais usados no dashboard

### Exemplo de Cadastro Ideal

```
Título: Como alterar minha senha de acesso
Tipo: GIF
Tags: senha, alterar, mudar, acesso, login, autenticação, conta

Título: Guia completo de elaboração de horários
Tipo: PDF
Tags: horário, elaboração, criação, turno, turma, grade, planejamento
```

## 🔐 Autenticação

### Fluxo de Senha (bcrypt)

A senha do admin é protegida com hash bcrypt armazenado no banco de dados:

1. **Primeiro startup**: O sistema gera o hash bcrypt de `ADMIN_PASSWORD` e armazena no banco (`admin_password_hash`)
2. **Login**: Usa `bcrypt.verify()` para comparar a senha digitada com o hash armazenado
3. **Troca de senha**: Se `ADMIN_PASSWORD` for alterado no `.env`, o hash é regenerado automaticamente no próximo login

A senha em texto puro **nunca** é comparada diretamente.

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

### Logout

```bash
POST /auth/logout
```

Limpa o cookie `admin_token` e encerra a sessão. Botão "Sair" disponível em todas as páginas do painel.

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
- `GET /settings` - Configurações do sistema (requer autenticação)
- `GET /login` - Página de login

### API Pública
- `GET /` - Informações da API
- `POST /chat` - Chat com o bot (processa mensagens e retorna respostas)
- `POST /chat/feedback` - Feedback do usuário (Sim/Não)
- `GET /files/pdf/{id}` - Visualizar/Download de PDF
- `GET /files/gif/{id}` - Visualizar GIF

### API Administrativa (requerem autenticação JWT)
- `POST /auth/login` - Autenticação e obtenção de token (proteção brute force)
- `POST /auth/logout` - Encerra sessão e limpa cookie
- `POST /admin/files/upload` - Upload de arquivo com validação de magic bytes
- `GET /admin/files` - Listar todos os arquivos
- `GET /admin/files/stats` - Estatísticas de arquivos (tamanho, quantidade)
- `PUT /admin/files/{id}` - Atualizar arquivo (título, tags)
- `DELETE /admin/files/{id}` - Deletar arquivo
- `GET /admin/prompt` - Obter prompt do sistema
- `PUT /admin/prompt` - Atualizar prompt do sistema
- `GET /admin/stats` - Estatísticas completas do sistema
- `GET /admin/export.xlsx` - Exportar estatísticas para Excel
- `GET /admin/system-settings` - Obter configurações do sistema
- `PUT /admin/system-settings` - Salvar configurações (validação Pydantic)
- `GET /admin/audit-logs` - Logs de auditoria paginados
- `GET /admin/backup` - Download de backup completo
- `GET /admin/conversations/` - Listar conversas paginadas
- `GET /admin/conversations/{id}` - Detalhes de uma conversa
- `GET /admin/conversations/{id}/export/txt` - Exportar conversa em TXT
- `GET /admin/conversations/{id}/export/pdf` - Exportar conversa em PDF

## 🛡️ Segurança

- ✅ **Autenticação JWT** com cookies `httponly` + `samesite=lax` + `secure` automático em produção
- ✅ **Senhas com bcrypt direto** (sem passlib) — compatível com Python 3.13 e bcrypt 5.x
- ✅ **Proteção brute force** — 5 tentativas falhas por IP bloqueiam login por 15 minutos
- ✅ **Rate limiting robusto** — limite por IP com proteção contra exaustão de memória (máx. 10k IPs)
- ✅ **Validação de magic bytes** — uploads verificam assinatura real do arquivo (PDF: `%PDF`, GIF: `GIF89a`)
- ✅ **Proteção open redirect** — redirecionamentos aceitam apenas URLs relativas
- ✅ **CORS configurável** — origens restritas em produção, permissivo em desenvolvimento
- ✅ **Validação Pydantic completa** — todos os endpoints usam schemas tipados
- ✅ **Mensagens de erro seguras** — detalhes técnicos apenas nos logs, nunca expostos ao usuário
- ✅ **Logs de auditoria** — login, upload, edição, exclusão e alterações de configuração registrados
- ✅ **Docs desabilitados em produção** — Swagger/ReDoc só disponíveis com `DEBUG=True`
- ✅ **Validação de extensões e tamanho** — apenas PDF/GIF, máximo 50MB configurável

## 📝 Logging e Auditoria

### Logs de Aplicação

O sistema registra nos logs do servidor:
- Inicialização da aplicação e validação da conexão OpenAI
- Erros e exceções (detalhes nos logs, mensagens genéricas para o usuário)
- Tentativas de rate limit e bloqueio por brute force

Configure o nível de log no `.env`:
```
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Logs de Auditoria (banco de dados)

Todas as ações administrativas são registradas automaticamente no banco e consultáveis via painel (`/settings`) ou API (`/admin/audit-logs`):

| Ação | Categoria | Detalhe registrado |
|---|---|---|
| `login_success` | auth | Usuário e IP |
| `login_failed` | auth | Usuário tentado e IP |
| `logout` | auth | IP |
| `prompt_updated` | config | Quantidade de caracteres |
| `settings_updated` | config | Valores antigos → novos |
| `file_uploaded` | arquivo | Tipo, título e ID |
| `file_updated` | arquivo | Campos alterados (antigo → novo) |
| `file_deleted` | arquivo | Tipo, título e ID |
| `backup_created` | sistema | Nome do arquivo gerado |

## 🎯 Funcionalidades Principais

### Widget de Chat (Página Completa)
- Interface moderna e responsiva
- Suporte a anexos (PDFs e GIFs)
- Indicador de digitação em tempo real
- Feedback de resolução (Sim/Não)
- Redirecionamento para suporte humano via WhatsApp
- Histórico de conversas

### Widget Flutuante Embeddable (`chat-widget.js`)

Widget JavaScript que embute a rota `/widget` existente dentro de um iframe flutuante. Pode ser adicionado em qualquer página do sistema (ou site externo) com uma única tag `<script>`.

#### Arquitetura

O widget funciona em duas camadas:

1. **`chat-widget.js`** — Cria o botão flutuante, a janela com cabeçalho (minimizar, tela cheia, fechar) e um iframe
2. **`/widget?embed=1`** — O iframe carrega a rota `/widget` existente em modo embed (layout compacto, sem cabeçalho duplicado, com persistência via sessionStorage)

Isso significa que **toda a lógica do chat** (mensagens, anexos, feedback, status) fica centralizada no `widget.html`. Qualquer atualização no widget se reflete automaticamente no botão flutuante.

#### Como Usar

**Uso básico** — adicione antes do `</body>` em qualquer página:
```html
<script src="/static/chat-widget.js"></script>
```

**Uso em site externo** (ex.: site em `beta.urania.com.br`, chat em `iabeta.urania.com.br`):

A forma mais simples é **carregar o script a partir da URL do chatbot**. O widget usa a origem do script como URL da API, sem precisar configurar nada:

```html
<script src="https://iabeta.urania.com.br/static/chat-widget.js"></script>
```

Se preferir carregar o script de outro lugar, defina a URL do chat manualmente:

```html
<script>
  window.UraniaWidgetConfig = { apiUrl: 'https://iabeta.urania.com.br' };
</script>
<script src="https://beta.urania.com.br/static/chat-widget.js"></script>
```

> **Nota:** Para uso em domínios externos, adicione o domínio em `WIDGET_ALLOWED_ORIGINS` (e `CORS_ORIGINS` se necessário) no `.env`.

#### Configuração Avançada

Todas as opções podem ser configuradas via `window.UraniaWidgetConfig` ou via atributos `data-*` no script:

```html
<script>
  window.UraniaWidgetConfig = {
    apiUrl: '',                    // URL base da API (vazio = inferido da origem do script ou mesmo domínio)
    assistantName: 'Urânia +',     // Nome exibido no cabeçalho
    avatarUrl: 'https://...',      // URL do avatar do assistente
    primaryColor: '#1C8B3C',       // Cor principal do widget
    primaryDark: '#15803d',        // Cor escura (gradiente)
    zIndex: 99999,                 // Z-index do widget
    buttonSize: 62,                // Tamanho do botão flutuante (px)
    windowWidth: 400,              // Largura da janela do chat (px)
    windowHeight: 580              // Altura da janela do chat (px)
  };
</script>
<script src="/static/chat-widget.js"></script>
```

Ou via atributos `data-*`:
```html
<script
  src="/static/chat-widget.js"
  data-api-url="https://seu-dominio.com"
  data-assistant-name="Urânia +"
  data-primary-color="#1C8B3C">
</script>
```

#### Duas formas de acesso ao chat

| Rota | Descrição |
|---|---|
| `/widget` | Página completa do chat (acesso direto, layout padrão) |
| `/widget?embed=1` | Modo embed usado pelo iframe (layout compacto, sem cabeçalho, com persistência) |

#### Funcionalidades do Widget Flutuante

| Funcionalidade | Descrição |
|---|---|
| **Botão flutuante** | Canto inferior direito, com animação pulse para chamar atenção |
| **Abrir/fechar chat** | Clique no botão para abrir, X ou ESC para fechar |
| **Cabeçalho completo** | Avatar, nome do assistente, status online/offline, minimizar, tela cheia e fechar |
| **Mensagem de boas-vindas** | Exibida automaticamente ao abrir o chat (iframe pré-carregado) |
| **Tela cheia** | Botão para expandir o chat para tela inteira; ESC ou botão restaura ao normal |
| **Persistência na navegação** | Chat mantém mensagens e estado ao navegar entre páginas (sessionStorage) |
| **Sem histórico ao relogar** | Ao fechar aba ou relogar, chat volta limpo automaticamente |
| **Minimizar/restaurar** | Usuário pode minimizar e restaurar o chat a qualquer momento |
| **Indicador de digitação** | Animação de 3 pontos enquanto a IA processa |
| **Anexos PDF** | Visualizador inline com botões "Ampliar" e "Baixar" |
| **Anexos GIF/Imagens** | Miniaturas clicáveis que expandem em modal lightbox |
| **Feedback** | Card "Conseguiu resolver?" com Sim/Não |
| **Suporte WhatsApp** | Botão para falar com suporte humano (quando a IA redireciona) |
| **Badge de notificação** | Indicador no botão quando há mensagens não lidas (chat fechado) |
| **Responsivo** | Janela flutuante no desktop, tela cheia automática no mobile |
| **Tecla ESC** | Sai da tela cheia → fecha o chat (em cascata) |
| **CSS isolado** | Estilos não interferem na página hospedeira; scroll da página oculto em tela cheia |

### Painel de Configurações (`/settings`)

Página centralizada para gerenciar o comportamento do sistema:

| Configuração | Descrição |
|---|---|
| **Comportamento da URL raiz** | Define o que acontece ao acessar `/`: redirecionar para o chat, exibir página em branco, ou redirecionar para URL customizada |
| **Widget do Chat** | Toggle para ativar/desativar o widget flutuante em todos os sites de uma vez (útil para manutenção) |
| **Backup do Sistema** | Gera e baixa backup completo (banco, arquivos, configurações) |
| **Logs de Auditoria** | Histórico de todas as ações do sistema com filtros por categoria e paginação |

### Painel Administrativo
- Gerenciamento de arquivos (upload com validação de magic bytes, edição, exclusão)
- Configuração do prompt do sistema
- Busca e filtragem de arquivos
- Estatísticas de uploads (tipo, tamanho total)
- Interface drag-and-drop para uploads
- Visualização de arquivos diretamente no painel
- Gerenciamento de conversas (histórico, exportação TXT/PDF)

### Dashboard de Métricas
- Total de mensagens e chats iniciados (com registro correto de `user_message` e `bot_message`)
- Taxa de resolução (Sim/Não)
- Contagem de PDFs e GIFs enviados
- Detratores (usuários sem feedback)
- Redirecionamentos para suporte humano
- Top 10 perguntas frequentes (categorizadas por IA)
- Arquivos que não resolveram problemas
- Exportação de dados para Excel

## 🔄 Migração do Código Antigo

O código antigo (`main_LEGACY_DO_NOT_USE.py`) foi completamente substituído pela estrutura modular em `app/`. Ele está no `.gitignore` e **não deve ser executado** (não possui autenticação nem proteções de segurança).

Para usar a nova versão:

1. Mantenha os arquivos HTML e estáticos na raiz
2. Use `uvicorn app.main:app` em vez de `uvicorn main:app`
3. Configure o arquivo `.env` conforme descrito acima

## 🚀 Deploy em Produção

### Validação Automática

Antes de colocar em produção, execute o script de validação:

```bash
python scripts/validate_production.py
```

Este script verifica:
- ✅ Configurações de segurança (SECRET_KEY, ADMIN_PASSWORD, DEBUG, CORS)
- ✅ Diretórios necessários (data/, uploads/, backups/)
- ✅ Dependências instaladas
- ✅ Arquivo .env configurado

### Checklist de Deploy

Para um checklist completo e detalhado, consulte o arquivo [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md).

**Resumo rápido:**

1. **Configuração do Ambiente**
   - [ ] Python 3.8+ instalado
   - [ ] Ambiente virtual criado e ativado
   - [ ] Dependências instaladas (`pip install -r requirements.txt`)
   - [ ] Arquivo `.env` configurado com todas as variáveis
   - [ ] Execute `python scripts/validate_production.py` para validar

2. **Segurança**
   - [ ] `SECRET_KEY` alterada (não usar valor padrão)
   - [ ] `ADMIN_PASSWORD` alterada (não usar valor padrão)
   - [ ] `DEBUG=False` configurado
   - [ ] `CORS_ORIGINS` configurado apenas com domínios permitidos
   - [ ] `WIDGET_ALLOWED_ORIGINS` configurado com domínios que podem incorporar o widget
   - [ ] Firewall configurado (porta 8000 ou 80/443)
   - [ ] HTTPS configurado (cookie `secure` é ativado automaticamente com `DEBUG=False`)

3. **Banco de Dados**
   - [ ] Diretório `data/` criado e com permissões corretas
   - [ ] Banco de dados inicializado (criado automaticamente no primeiro acesso)

4. **Uploads**
   - [ ] Diretório `uploads/` criado e com permissões corretas
   - [ ] Subdiretórios `uploads/pdfs/` e `uploads/gifs/` criados

5. **Servidor Web (Opcional mas Recomendado)**
   - [ ] Nginx instalado e configurado
   - [ ] SSL/HTTPS configurado (Let's Encrypt recomendado)
   - [ ] Reverse proxy configurado

6. **Process Manager**
   - [ ] PM2, Supervisor ou systemd configurado
   - [ ] Auto-restart configurado
   - [ ] Logs configurados

### Estimativa de Recursos por Tráfego

| Usuários Simultâneos | CPU | RAM | Disco | Workers |
|---------------------|-----|-----|-------|---------|
| 1-50 | 1 core | 1GB | 10GB | 2 |
| 50-200 | 2 cores | 2GB | 20GB | 4 |
| 200-500 | 2-4 cores | 4GB | 50GB | 4-6 |
| 500-1000 | 4+ cores | 8GB | 100GB | 6-8 |
| 1000+ | 8+ cores | 16GB+ | 200GB+ | 8+ |

### Otimizações Recomendadas

1. **Use PostgreSQL em vez de SQLite** para alta carga:
   ```env
   DATABASE_URL=postgresql://user:password@localhost/urania_db
   ```

2. **Configure cache** (opcional):
   - Redis para cache de sessões
   - Cache de arquivos estáticos no Nginx

3. **Monitore recursos**:
   - Use `htop` ou `top` para monitorar CPU/RAM
   - Configure alertas de disco cheio
   - Monitore logs de erro

4. **Backup regular**:
   - Banco de dados (`data/saas_chatbot.db`)
   - Arquivos de upload (`uploads/`)
   - Configurações (`.env`)

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
- Se alterou a senha no `.env`, reinicie o servidor — o hash bcrypt será regenerado automaticamente

### Erro com bcrypt / passlib
- O sistema usa `bcrypt` diretamente (sem `passlib`), garantindo compatibilidade com Python 3.13+ e bcrypt 5.x
- Se vir erros como `module 'bcrypt' has no attribute '__about__'`, certifique-se de que `passlib` **não** está instalado: `pip uninstall passlib`
- Instale apenas: `pip install bcrypt>=4.1.0`

### Problemas de Performance
- Aumente o número de workers: `--workers 4` ou mais
- Use PostgreSQL em vez de SQLite para alta carga
- Configure Nginx como reverse proxy
- Monitore uso de memória e CPU

## 💡 Dicas de Uso

### Para Administradores

1. **Cadastre arquivos com títulos claros**: A IA usa o título para encontrar arquivos relevantes
2. **Adicione tags relevantes**: Quanto mais tags, melhor a busca
3. **Monitore o dashboard**: Veja quais arquivos são mais usados e quais não resolveram problemas
4. **Ajuste o prompt do sistema**: Personalize como a IA responde no painel admin
5. **Revise perguntas frequentes**: Use a categorização automática para identificar temas recorrentes

### Para Desenvolvedores

- O sistema busca arquivos antes de enviar para a IA
- A IA recebe apenas arquivos pré-filtrados (máximo 8)
- A busca usa `LIKE` no título e tags (case-insensitive)
- Arquivos são ordenados por data de criação (mais recentes primeiro)

## 🔧 Tecnologias Utilizadas

- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **Pydantic** - Validação de dados
- **OpenAI API** - Integração com GPT para respostas inteligentes
- **JWT (python-jose)** - Autenticação segura
- **bcrypt** - Hash de senhas (direto, sem passlib)
- **Uvicorn** - Servidor ASGI de alta performance
- **OpenPyXL** - Exportação de dados para Excel

## 💾 Backup e Migração

O sistema inclui ferramentas completas de backup e migração:

- **Script de Backup**: `python scripts/backup.py` - Faz backup completo (banco, arquivos, configurações)
- **Script de Restore**: `python scripts/restore.py <arquivo>` - Restaura backup completo
- **Endpoint Web**: `/admin/backup` - Download de backup via interface (requer autenticação)

Para documentação completa sobre backup e migração, consulte: [BACKUP_MIGRATION.md](BACKUP_MIGRATION.md)

### Backup Rápido

```bash
# Fazer backup
python scripts/backup.py

# Restaurar backup
python scripts/restore.py backups/urania_backup_YYYYMMDD_HHMMSS.tar.gz
```

## 📄 Licença

Este projeto é de uso interno da **Urânia**.

## 📞 Suporte

Para dúvidas ou suporte técnico, entre em contato com a equipe de desenvolvimento.

---

**Urânia +** - Sistema de Chatbot Inteligente v1.1.0

