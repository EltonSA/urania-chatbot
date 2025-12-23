# 💾 Guia Completo de Backup e Migração do Urânia +

Este documento detalha como realizar backups completos do sistema Urânia +, restaurar dados e migrar a aplicação para um novo servidor sem perda de informações.

---

## 🎯 O que é incluído no Backup?

Um backup completo do Urânia + inclui todos os dados essenciais para a operação do chatbot:

1. **Banco de Dados SQLite**: O arquivo `database.db` que contém:
   - Histórico de conversas (`chat_events`, `chat_sessions`)
   - Informações dos arquivos (`files`)
   - Configurações do sistema (`settings`, como o prompt da IA)
   - Usuários e senhas (hashes)

2. **Arquivos de Upload**: Todo o conteúdo dos diretórios `uploads/pdfs/` e `uploads/gifs/`.

3. **Informações do Backup**: Um arquivo `backup_info.json` com metadados sobre o backup.

Todos esses itens são compactados em um único arquivo `.tar.gz` para facilitar o armazenamento e a transferência.

---

## 🚀 Como Fazer Backup

Existem três métodos principais para criar um backup:

### Método 1: Via Interface Web (Recomendado para Uso Rápido)

Este método é conveniente para backups rápidos e manuais através do navegador.

1. **Acesse o Painel Administrativo**:
   - Abra seu navegador e vá para `http://localhost:8000/admin` (ou o URL do seu servidor).
   - Faça login com suas credenciais de administrador.

2. **Clique no botão "💾 Fazer Backup"**:
   - No cabeçalho superior direito, localize e clique no botão "💾 Fazer Backup".

3. **Aguarde o download**:
   - O botão exibirá uma animação de "Criando backup..." e, em seguida, "Baixando...".
   - O navegador fará o download automático do arquivo `.tar.gz`.
   - O nome do arquivo será similar a `urania_backup_YYYYMMDD_HHMMSS.tar.gz`.

**Observações:**
- Este método requer que o servidor FastAPI esteja em execução.
- O processo pode levar alguns segundos, dependendo do tamanho dos seus arquivos de upload.
- Requer autenticação (você precisa estar logado).

### Método 2: Via Script Python (Recomendado para Automação e Servidores)

Este método é ideal para ser executado diretamente no servidor ou em scripts de automação.

1. **Acesse o diretório raiz do projeto**:
   ```bash
   cd /caminho/para/seu/projeto/urania-chatbot
   ```

2. **Execute o script de backup**:
   ```bash
   python scripts/backup.py
   ```

3. **Verifique o backup**:
   - Um novo arquivo `.tar.gz` será criado no diretório `backups/`.
   - Exemplo: `backups/urania_backup_20251223_143022.tar.gz`

**Saída esperada no console:**
```
============================================================
Backup do Sistema Urania +
============================================================

[1/3] Copiando banco de dados...
   OK - Banco encontrado: 0.11 MB
[2/3] Copiando arquivos de upload...
   OK - 3 PDFs, 16 GIFs (17.66 MB)
[3/3] Criando arquivo compactado...
   OK - Banco de dados adicionado
   OK - Arquivos de upload adicionados
   OK - Informacoes do backup adicionadas

============================================================
BACKUP CONCLUIDO COM SUCESSO!
============================================================
Arquivo: urania_backup_20251223_134550.tar.gz
Tamanho: 13.37 MB
Banco de dados: Incluido
Documentos: 3 PDFs, 16 GIFs

Para restaurar: python scripts/restore.py urania_backup_20251223_134550.tar.gz
============================================================
```

### Método 3: Backup Automatizado (Cron Job)

Para fazer backup automático diário, configure um cron job:

```bash
# Edite o crontab
crontab -e

# Adicione esta linha (backup diário às 2h da manhã)
0 2 * * * cd /caminho/para/urania && python scripts/backup.py >> logs/backup.log 2>&1
```

**Dica:** Configure também uma limpeza de backups antigos:

```bash
# Remove backups com mais de 30 dias
0 3 * * * find /caminho/para/urania/backups -name "urania_backup_*.tar.gz" -mtime +30 -delete
```

### Método 4: Backup Manual (Alternativa)

Se você preferir um controle mais granular ou tiver problemas com os scripts, pode fazer o backup manualmente:

1. **Pare a aplicação FastAPI** (se estiver em execução).
2. **Copie os seguintes diretórios/arquivos**:
   - `data/saas_chatbot.db` (banco de dados)
   - `uploads/` (contém `pdfs/` e `gifs/`)
   - `.env` (se você o configurou - **mantenha seguro!**)
3. **Compacte-os** em um arquivo `.zip` ou `.tar.gz`.

---

## 🔄 Como Restaurar um Backup

A restauração de um backup sobrescreverá o banco de dados e os arquivos de upload existentes. **É altamente recomendável fazer um backup do estado atual antes de restaurar.**

1. **Pare a aplicação FastAPI** (se estiver em execução).

2. **Acesse o diretório raiz do projeto**:
   ```bash
   cd /caminho/para/seu/projeto/urania-chatbot
   ```

3. **Localize o arquivo de backup**:
   - Certifique-se de que o arquivo `.tar.gz` que você deseja restaurar esteja acessível (ex: no diretório `backups/`).

4. **Execute o script de restauração**:
   ```bash
   python scripts/restore.py backups/urania_backup_YYYYMMDD_HHMMSS.tar.gz
   ```
   - Substitua `backups/urania_backup_YYYYMMDD_HHMMSS.tar.gz` pelo caminho real do seu arquivo de backup.

5. **Reinicie a aplicação FastAPI**:
   ```bash
   python run.py
   # ou
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

**Saída esperada no console:**
```
============================================================
Restore do Sistema Urânia +
============================================================
Arquivo: urania_backup_20251223_143022.tar.gz

[1/3] Extraindo arquivo de backup...
   OK - Arquivo extraído
[2/3] Restaurando banco de dados...
   OK - Backup do banco atual criado: saas_chatbot.db.pre_restore_20251223_143500
   OK - Banco de dados restaurado: 0.11 MB
   OK - Banco de dados inicializado
[3/3] Restaurando arquivos de upload...
   OK - Backup dos uploads atuais criado: uploads_old_20251223_143500
   OK - Arquivos restaurados: 3 PDFs, 16 GIFs

============================================================
RESTORE CONCLUIDO COM SUCESSO!
============================================================

IMPORTANTE:
   1. Verifique se o arquivo .env está configurado corretamente
   2. Reinicie o servidor para aplicar as mudanças
   3. Verifique se os arquivos foram restaurados corretamente
```

**⚠️ IMPORTANTE:**
- O script cria backups automáticos dos arquivos atuais antes de sobrescrever.
- Verifique se o arquivo `.env` está configurado corretamente após a restauração.
- Reinicie o servidor para aplicar as mudanças.

---

## 🚚 Como Migrar o Sistema para Outro Servidor

A migração envolve transferir a aplicação e seus dados para um novo ambiente.

### Checklist de Migração

#### 1. No Servidor Antigo:

- [ ] **Faça um backup completo** usando o `scripts/backup.py` (Método 2) ou via interface web (Método 1).
- [ ] **Transfira o arquivo `.tar.gz`** gerado para o seu computador local ou diretamente para o novo servidor (via `scp`, `sftp`, etc.).
- [ ] **Copie o arquivo `.env`** do servidor antigo. Ele contém suas chaves secretas e configurações específicas. **Mantenha-o seguro!**

#### 2. No Novo Servidor:

- [ ] **Instale os pré-requisitos**: Python 3.8+, pip, etc. (conforme `README.md`).
- [ ] **Clone o repositório do Urânia +** (ou transfira os arquivos do projeto):
   ```bash
   git clone https://github.com/EltonSA/urania-chatbot.git
   cd urania-chatbot
   ```
- [ ] **Crie um ambiente virtual** e instale as dependências:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
- [ ] **Transfira o arquivo `.env`** copiado do servidor antigo para o diretório raiz do projeto no novo servidor.
- [ ] **Transfira o arquivo de backup `.tar.gz`** para o diretório `backups/` do novo projeto.
- [ ] **Restaure o backup** usando o `scripts/restore.py` (conforme a seção "Como Restaurar um Backup").
- [ ] **Reinicie a aplicação** (`python run.py` ou seu comando de produção).
- [ ] **Verifique a funcionalidade**: Acesse o admin, dashboard e widget para confirmar que tudo está funcionando como esperado.

### Transferência do Backup

**Opção A: Via SCP (recomendado)**
```bash
# Do servidor antigo
scp backups/urania_backup_*.tar.gz usuario@novo-servidor:/caminho/destino/
```

**Opção B: Via FTP/SFTP**
- Use um cliente FTP (FileZilla, WinSCP, etc.)
- Faça upload do arquivo `.tar.gz`

**Opção C: Via Cloud Storage**
- Faça upload para Google Drive, Dropbox, AWS S3, etc.
- Baixe no novo servidor

**Opção D: Via Interface Web**
- Faça backup via interface web no servidor antigo
- Baixe o arquivo no seu computador
- Faça upload para o novo servidor

### Configuração do Novo Servidor

#### Configuração do Servidor Web (Nginx - Opcional mas Recomendado)

Se usar Nginx como reverse proxy, atualize a configuração:

```nginx
server {
    listen 80;
    server_name novo-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Configuração do Process Manager

**Com systemd:**
```bash
# Crie arquivo: /etc/systemd/system/urania.service
[Unit]
Description=Urânia + Chatbot
After=network.target

[Service]
Type=simple
User=seu-usuario
WorkingDirectory=/caminho/para/urania
Environment="PATH=/caminho/para/urania/venv/bin"
ExecStart=/caminho/para/urania/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target

# Ative o serviço
sudo systemctl enable urania
sudo systemctl start urania
```

**Com PM2:**
```bash
pm2 start uvicorn --name urania -- app.main:app --host 0.0.0.0 --port 8000 --workers 4
pm2 save
pm2 startup
```

---

## ⚠️ Troubleshooting

### Erro: "Arquivo de backup não encontrado"
- Verifique o caminho do arquivo `.tar.gz` no comando `restore.py`.
- Certifique-se de que o arquivo existe e está acessível.

### Erro: "Erro ao executar backup: Permission denied"
- Certifique-se de que o usuário que executa o script tem permissões de leitura/escrita nos diretórios `data/`, `uploads/` e `backups/`.
- No Linux/Mac, você pode precisar usar `sudo` ou ajustar permissões:
  ```bash
  chmod -R 755 data/ uploads/ backups/
  ```

### Erro: "Timeout ao criar backup"
- Se você tem muitos arquivos de upload, o backup pode demorar.
- Aumente o `timeout` no `admin.py` (padrão: 300 segundos) ou faça o backup via script diretamente no servidor.

### Erro: "Banco de dados está em uso"
- Pare o servidor FastAPI antes de fazer backup/restore:
  ```bash
  sudo systemctl stop urania
  # ou
  pm2 stop urania
  ```
- Execute o backup/restore
- Reinicie o servidor:
  ```bash
  sudo systemctl start urania
  # ou
  pm2 start urania
  ```

### Erro: "Espaço em disco insuficiente"
- Verifique espaço disponível:
  ```bash
  df -h
  ```
- Limpe backups antigos:
  ```bash
  find backups/ -name "*.tar.gz" -mtime +30 -delete
  ```
- Ou faça backup em outro local e mova depois.

### Erro: "UnicodeEncodeError" (Windows)
- O script já trata este erro automaticamente removendo emojis.
- Se ainda ocorrer, verifique se está usando Python 3.8+.

### Após restauração, dados antigos ainda aparecem
- Certifique-se de que a aplicação FastAPI foi **reiniciada** após a restauração.
- Limpe o cache do navegador (Ctrl+F5).

### Backup via interface web não inicia download
- Verifique se está autenticado (faça login novamente).
- Verifique os logs do servidor para erros.
- Tente fazer backup via script Python diretamente.

---

## ✨ Dicas e Boas Práticas

- **Backups Regulares**: Configure backups automáticos (ex: via `cron` no Linux) para garantir que você sempre tenha uma cópia recente dos seus dados.
- **Armazenamento Seguro**: Guarde seus arquivos de backup em um local seguro e externo ao servidor principal (ex: armazenamento em nuvem, outro servidor).
- **Teste de Restauração**: Periodicamente, teste a restauração de um backup em um ambiente de desenvolvimento para garantir que o processo funcione e que os dados estejam íntegros.
- **Controle de Versão**: Mantenha o código da sua aplicação em um sistema de controle de versão (como Git/GitHub). O backup de dados é separado do backup de código.
- **Logs**: Monitore os logs da aplicação e dos scripts de backup/restauração para identificar e resolver problemas rapidamente.
- **Valores Sensíveis**: Lembre-se de que o arquivo `.env` com valores sensíveis (SECRET_KEY, ADMIN_PASSWORD, OPENAI_API_KEY) **não** está incluído no backup por segurança. Configure manualmente após a restauração.
- **Múltiplos Backups**: Mantenha múltiplos backups (diário, semanal, mensal) para ter opções de restauração em diferentes pontos no tempo.

---

## 📊 Estrutura do Arquivo de Backup

O arquivo `.tar.gz` contém a seguinte estrutura:

```
urania_backup_YYYYMMDD_HHMMSS.tar.gz
├── database.db              # Cópia do banco SQLite
├── uploads/
│   ├── pdfs/               # Todos os PDFs
│   └── gifs/               # Todos os GIFs
└── backup_info.json        # Informações do backup (metadados)
```

O arquivo `backup_info.json` contém:
- Timestamp do backup
- Versão da aplicação
- Contagem de arquivos (PDFs e GIFs)
- Tamanho total dos arquivos
- Informações sobre o que foi incluído

---

## 📞 Suporte

Se encontrar problemas durante backup ou migração:

1. Verifique os logs: `logs/app.log` (se configurado)
2. Consulte a seção [Troubleshooting](#-troubleshooting) acima
3. Verifique se todas as dependências estão instaladas
4. Certifique-se de que o Python e as bibliotecas estão atualizadas
5. Verifique permissões de arquivos e diretórios

---

**Última atualização:** Dezembro 2024  
**Versão do sistema:** 1.0.0
