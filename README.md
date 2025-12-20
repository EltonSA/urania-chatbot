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

### Desenvolvimento Local
- Python 3.8+
- pip
- 2GB RAM mínimo
- 1GB espaço em disco

### Produção (VPS/Servidor)

#### Requisitos Mínimos
- **CPU**: 1 core (2.0 GHz+)
- **RAM**: 1GB (2GB recomendado)
- **Disco**: 10GB espaço livre
- **Sistema Operacional**: Linux (Ubuntu 20.04+ / Debian 11+ / CentOS 8+)
- **Python**: 3.8 ou superior
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

## 🚀 Deploy em Produção

### Checklist de Deploy

1. **Configuração do Ambiente**
   - [ ] Python 3.8+ instalado
   - [ ] Ambiente virtual criado e ativado
   - [ ] Dependências instaladas (`pip install -r requirements.txt`)
   - [ ] Arquivo `.env` configurado com todas as variáveis

2. **Segurança**
   - [ ] `SECRET_KEY` alterada (não usar valor padrão)
   - [ ] `ADMIN_PASSWORD` alterada (não usar valor padrão)
   - [ ] `DEBUG=False` configurado
   - [ ] `CORS_ORIGINS` configurado apenas com domínios permitidos
   - [ ] Firewall configurado (porta 8000 ou 80/443)

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
- **bcrypt (passlib)** - Hash de senhas
- **Uvicorn** - Servidor ASGI de alta performance
- **OpenPyXL** - Exportação de dados para Excel

## 📄 Licença

Este projeto é de uso interno da **Urânia**.

## 📞 Suporte

Para dúvidas ou suporte técnico, entre em contato com a equipe de desenvolvimento.

---

**Urânia +** - Sistema de Chatbot Inteligente v1.0.0

