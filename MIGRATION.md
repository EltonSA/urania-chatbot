# Guia de Migração

Este documento explica como migrar do código antigo (`main.py`) para a nova estrutura profissional.

## Mudanças Principais

### 1. Estrutura de Pastas

O código foi reorganizado em uma estrutura modular:

```
app/
├── main.py          # Aplicação principal (substitui main.py antigo)
├── config.py        # Configurações centralizadas
├── database.py      # Configuração do banco
├── models.py        # Modelos do banco
├── schemas.py       # Schemas Pydantic
├── auth.py          # Autenticação JWT
├── utils.py         # Funções utilitárias
├── routers/         # Rotas organizadas
└── middleware/      # Middlewares
```

### 2. Autenticação

**ANTES:** Nenhuma autenticação
**AGORA:** Sistema JWT completo

- Todas as rotas `/admin/*` agora requerem autenticação
- Faça login em `/auth/login` para obter token
- Use o token no header: `Authorization: Bearer <token>`

### 3. Configuração

**ANTES:** Variáveis hardcoded no código
**AGORA:** Arquivo `.env` para configuração

Crie um arquivo `.env` na raiz do projeto (veja `.env.example`).

### 4. Execução

**ANTES:**
```bash
uvicorn main:app --reload
```

**AGORA:**
```bash
uvicorn app.main:app --reload
```

Ou use o script:
```bash
python run.py
```

### 5. Endpoints

A maioria dos endpoints permanece igual, mas:

- `/admin/upload` → Agora requer autenticação
- `/admin/files` → Agora requer autenticação
- `/admin/prompt` → Agora requer autenticação
- `/admin/stats` → Agora requer autenticação
- `/files/pdf/{id}` → Continua público (sem autenticação)
- `/files/gif/{id}` → Continua público (sem autenticação)

### 6. Modelo OpenAI

**ANTES:** `gpt-4.1-mini` (pode não existir)
**AGORA:** `gpt-4o-mini` (configurável via `.env`)

## Passos para Migração

1. **Instale as novas dependências:**
```bash
pip install -r requirements.txt
```

2. **Crie o arquivo `.env`:**
```bash
cp .env.example .env
```

3. **Configure o `.env`:**
   - Gere uma `SECRET_KEY` segura
   - Configure `ADMIN_PASSWORD`
   - Configure `OPENAI_API_KEY`
   - Ajuste `CORS_ORIGINS` se necessário

4. **Teste a aplicação:**
```bash
python run.py
```

5. **Atualize seus clientes frontend:**
   - Adicione autenticação para rotas admin
   - Use o endpoint `/auth/login` para obter token
   - Inclua o token nas requisições admin

## Compatibilidade

- O banco de dados SQLite existente continuará funcionando
- Os arquivos HTML e estáticos não precisam ser alterados
- Os uploads existentes continuarão funcionando

## Suporte

Se encontrar problemas na migração, verifique:
1. Se todas as dependências estão instaladas
2. Se o arquivo `.env` está configurado corretamente
3. Se o banco de dados está acessível
4. Os logs da aplicação para erros

