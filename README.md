# SaaS Chatbot Urnânia


## 🚀 Características

- ✅ **Autenticação JWT** - Sistema seguro de autenticação
- ✅ **Rate Limiting** - Proteção contra abuso
- ✅ **Logging Profissional** - Sistema completo de logs
- ✅ **Arquitetura Modular** - Código organizado e manutenível
- ✅ **Validação de Dados** - Schemas Pydantic para validação
- ✅ **Tratamento de Erros** - Erros tratados adequadamente
- ✅ **CORS Configurável** - Segurança configurável
- ✅ **Documentação Automática** - Swagger/ReDoc integrado

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
cp .env.example .env
```

Edite o arquivo `.env` e configure:
- `SECRET_KEY`: Gere uma chave secreta forte (obrigatório)
- `ADMIN_PASSWORD`: Defina uma senha segura para o admin (obrigatório)
- `OPENAI_API_KEY`: Sua chave da API OpenAI (obrigatório para chat)
- `CORS_ORIGINS`: Origens permitidas (ajuste conforme necessário)

**Para gerar uma SECRET_KEY segura:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

## 🏃 Executando

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A aplicação estará disponível em:
- API: http://localhost:8000
- Documentação: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📁 Estrutura do Projeto

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicação principal
│   ├── config.py            # Configurações
│   ├── database.py          # Configuração do banco
│   ├── models.py            # Modelos do banco de dados
│   ├── schemas.py           # Schemas Pydantic
│   ├── auth.py              # Autenticação
│   ├── utils.py             # Funções utilitárias
│   ├── routers/             # Rotas organizadas
│   │   ├── auth.py
│   │   ├── files.py
│   │   ├── chat.py
│   │   ├── admin.py
│   │   └── pages.py
│   └── middleware/          # Middlewares
│       └── rate_limit.py
├── static/                  # Arquivos estáticos
├── uploads/                 # Arquivos enviados
├── .env                     # Variáveis de ambiente (criar)
├── .env.example             # Exemplo de configuração
├── requirements.txt         # Dependências
└── README.md                # Este arquivo
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

### Públicos
- `GET /` - Informações da API
- `POST /chat` - Chat com o bot
- `POST /chat/feedback` - Feedback do usuário
- `GET /files/pdf/{id}` - Download de PDF
- `GET /files/gif/{id}` - Download de GIF

### Protegidos (requerem autenticação)
- `POST /admin/files/upload` - Upload de arquivo
- `GET /admin/files` - Listar arquivos
- `PUT /admin/files/{id}` - Atualizar arquivo
- `DELETE /admin/files/{id}` - Deletar arquivo
- `GET /admin/prompt` - Obter prompt
- `PUT /admin/prompt` - Atualizar prompt
- `GET /admin/stats` - Estatísticas
- `GET /admin/export.xlsx` - Exportar estatísticas

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

## 📄 Licença

Este projeto é de uso interno.

## 👨‍💻 Desenvolvido com

- FastAPI
- SQLAlchemy
- Pydantic
- OpenAI API
- JWT (python-jose)
- bcrypt (passlib)

