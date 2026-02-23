// Desabilita console.log em produção (mantém apenas console.error)
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
if (isProduction) {
    console.log = function() {}; // Remove logs em produção
    console.debug = function() {}; // Remove debug em produção
}

// Aguarda DOM estar pronto
let promptText, btnSavePrompt, promptStatus, uploadForm, uploadStatus, filesEmpty, filesList;
let statPdfs, statGifs, statTotalSize;
let fileSearch, clearSearchBtn;
let allFiles = []; // Armazena todos os arquivos para filtro
let currentTypeFilter = "all"; // Filtro atual por tipo

function initElements() {
    promptText = document.getElementById("prompt-text");
    btnSavePrompt = document.getElementById("btn-save-prompt");
    promptStatus = document.getElementById("prompt-status");
    uploadForm = document.getElementById("upload-form");
    uploadStatus = document.getElementById("upload-status");
    filesEmpty = document.getElementById("files-empty");
    filesList = document.getElementById("files-list");
    statPdfs = document.getElementById("stat-pdfs");
    statGifs = document.getElementById("stat-gifs");
    statTotalSize = document.getElementById("stat-total-size");
    fileSearch = document.getElementById("file-search");
    clearSearchBtn = document.getElementById("clear-search");
    
    if (!promptText || !filesList) {
        console.error("Elementos do DOM não encontrados!");
        return false;
    }
    return true;
}

// AUTENTICAÇÃO
function getAuthToken() {
    return localStorage.getItem('admin_token');
}

let authToken = getAuthToken();

async function login() {
    // Redireciona para página de login
    window.location.href = '/login';
    return false;
}

function getAuthHeaders() {
    // Atualiza token a cada requisição (pode ter mudado)
    const token = getAuthToken();
    if (!token) {
        console.error("Token não encontrado no localStorage!");
        // Log removido por segurança
        return {};
    }
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
    // Log removido por segurança (não expor token)
    return headers;
}

function getAuthHeadersFormData() {
    // Atualiza token a cada requisição (pode ter mudado)
    const token = getAuthToken();
    if (!token) {
        console.error("Token não encontrado!");
        return {};
    }
    // NÃO inclui Content-Type - o navegador define automaticamente com boundary para FormData
    return {
        'Authorization': `Bearer ${token}`
    };
}

// PROMPT
async function loadPrompt() {
if (!promptText) {
    console.error("Elemento promptText não encontrado! Tentando re-inicializar...");
    if (!initElements() || !promptText) {
        console.error("Não foi possível encontrar promptText");
        return;
    }
}

try {
    const headers = getAuthHeaders();
    
    if (!headers.Authorization) {
        console.error("Token não encontrado nos headers!");
        window.location.href = '/login';
        return;
    }
    
    const res = await fetch("/admin/prompt", {
        headers: headers
    });
    
    if (!res.ok) {
        if (res.status === 401) {
            window.location.href = '/login';
            return;
        }
        const errorText = await res.text();
        console.error("Erro ao carregar prompt:", res.status, errorText);
        alert(`Erro ao carregar prompt: ${res.status} - ${errorText}`);
        return;
    }
    const data = await res.json();
    
    if (!promptText) {
        console.error("promptText não encontrado após carregar dados! Re-inicializando...");
        if (!initElements() || !promptText) {
            console.error("Não foi possível encontrar promptText após re-inicialização");
            return;
        }
    }
    
    promptText.value = data.prompt || "";
    // Prompt carregado com sucesso
} catch (err) {
    console.error("Erro ao carregar prompt:", err);
    alert(`Erro ao carregar prompt: ${err.message}`);
}
}

async function savePrompt() {
if (!promptText) {
    console.error("Elemento promptText não encontrado!");
    return;
}

const value = promptText.value || "";
const originalText = btnSavePrompt.textContent;
const originalHTML = btnSavePrompt.innerHTML;

btnSavePrompt.disabled = true;
btnSavePrompt.textContent = "Salvando...";
promptStatus.textContent = "Salvando...";
promptStatus.classList.remove("error", "success");
promptStatus.classList.add("show");

try {
    const headers = getAuthHeaders();
    
    const res = await fetch("/admin/prompt", {
    method: "PUT",
    headers: headers,
    body: JSON.stringify({ prompt: value })
    });

    if (!res.ok) {
        if (res.status === 401) {
            window.location.href = '/login';
            return;
        }
        const errorText = await res.text();
        console.error("Erro ao salvar prompt:", res.status, errorText);
        promptStatus.textContent = "Erro ao salvar: " + (errorText || res.statusText);
        promptStatus.classList.add("error");
        return;
    }

    const data = await res.json();
    
    // Feedback visual de sucesso
    promptStatus.textContent = "Prompt salvo com sucesso!";
    promptStatus.classList.remove("error");
    promptStatus.classList.add("success", "show");
    
    // Animação no botão
    btnSavePrompt.style.background = "linear-gradient(135deg, #16a34a 0%, #15803d 100%)";
    btnSavePrompt.textContent = "Salvo!";
    btnSavePrompt.disabled = false;
    
    // Restaura após 3 segundos
    setTimeout(() => { 
        promptStatus.textContent = "";
        promptStatus.classList.remove("success", "show");
        btnSavePrompt.style.background = "";
        btnSavePrompt.textContent = originalText;
        btnSavePrompt.innerHTML = originalHTML;
    }, 3000);
} catch (err) {
    console.error("Erro ao salvar prompt:", err);
    promptStatus.textContent = "Erro ao salvar: " + err.message;
    promptStatus.classList.add("error");
} finally {
    btnSavePrompt.disabled = false;
}
}

// Event listeners serão adicionados na função init()

// LISTA DE RECURSOS
async function loadFiles() {
if (!filesList) {
    console.error("filesList não encontrado! Tentando novamente...");
    if (!initElements()) {
        console.error("Não foi possível inicializar elementos");
        return;
    }
}

try {
    const headers = getAuthHeaders();
    
    if (!headers.Authorization) {
        console.error("Token não encontrado nos headers!");
        window.location.href = '/login';
        return;
    }
    
    const res = await fetch("/admin/files", {
        headers: headers
    });
    
    if (!res.ok) {
        if (res.status === 401) {
            window.location.href = '/login';
            return;
        }
        const errorText = await res.text();
        console.error("Erro ao carregar arquivos:", res.status, errorText);
        alert(`Erro ao carregar arquivos: ${res.status} - ${errorText}`);
        return;
    }
    const files = await res.json();
    if (files.length > 0) {
    }

    // Armazena todos os arquivos para filtro
    allFiles = files || [];

    if (!filesList) {
        console.error("filesList ainda não encontrado após requisição!");
        return;
    }

    // Renderiza os arquivos (com filtro se houver)
    const searchTerm = fileSearch ? fileSearch.value.toLowerCase().trim() : "";
    renderFiles(allFiles, searchTerm);
} catch (err) {
    console.error("Erro ao carregar arquivos:", err);
}
}

function renderFiles(files, searchTerm = "") {
    if (!filesList) return;

    // Filtra por tipo primeiro
    let filteredFiles = files;
    if (currentTypeFilter !== "all") {
        filteredFiles = files.filter(f => 
            (f.file_type || "").toLowerCase() === currentTypeFilter.toLowerCase()
        );
    }

    // Depois filtra por termo de busca
    if (searchTerm) {
        filteredFiles = filteredFiles.filter(f => {
            const title = (f.title || "").toLowerCase();
            const tags = (f.tags || "").toLowerCase();
            return title.includes(searchTerm) || tags.includes(searchTerm);
        });
    }

    filesList.innerHTML = "";

    if (!filteredFiles || filteredFiles.length === 0) {
        // Nenhum arquivo encontrado
        if (filesEmpty) {
            filesEmpty.textContent = searchTerm 
                ? `Nenhum recurso encontrado para "${searchTerm}"`
                : "Nenhum recurso cadastrado ainda.";
            filesEmpty.style.display = "block";
        }
        if (filesList) filesList.style.display = "none";
        return;
    }

    // Renderizando arquivos
    if (filesEmpty) filesEmpty.style.display = "none";
    if (filesList) filesList.style.display = "grid";

    filteredFiles.forEach(f => {
    const item = document.createElement("div");
    item.className = "resource-item";
    item.dataset.fileId = f.id; // Adiciona ID para facilitar busca

    // Header com ícone e informações principais
    const header = document.createElement("div");
    header.className = "resource-item-header";

    const icon = document.createElement("div");
    icon.className = "resource-icon " + (f.file_type === "pdf" ? "pdf" : "gif");
    icon.innerHTML = f.file_type === "pdf" ? '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>' : '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>';
    header.appendChild(icon);

    const info = document.createElement("div");
    info.className = "resource-info";

    const titleRow = document.createElement("div");
    titleRow.className = "resource-header";

    // Tipo primeiro (mais destaque)
    const typePill = document.createElement("span");
    typePill.className = "resource-type-pill " + (f.file_type === "pdf" ? "pdf" : "");
    typePill.textContent = f.file_type.toUpperCase();
    titleRow.appendChild(typePill);

    // Título depois
    const title = document.createElement("div");
    title.className = "resource-title";
    title.textContent = f.title || "(sem título)";
    titleRow.appendChild(title);

    info.appendChild(titleRow);

    if (f.tags && f.tags.trim()) {
        const tags = document.createElement("div");
        tags.className = "resource-tags";
        tags.textContent = f.tags;
        info.appendChild(tags);
    }

    header.appendChild(info);
    item.appendChild(header);

    // Ações
    const actions = document.createElement("div");
    actions.className = "resource-actions";

    const btnView = document.createElement("button");
    btnView.type = "button";
    btnView.className = "btn-small btn-view";
    btnView.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3px;margin-top:-1px"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>Visualizar';
    btnView.addEventListener("click", () => viewFile(f));
    actions.appendChild(btnView);

    const btnEdit = document.createElement("button");
    btnEdit.type = "button";
    btnEdit.className = "btn-small btn-edit";
    btnEdit.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3px;margin-top:-1px"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>Editar';
    btnEdit.addEventListener("click", () => editFile(f));
    actions.appendChild(btnEdit);

    const btnDelete = document.createElement("button");
    btnDelete.type = "button";
    btnDelete.className = "btn-small btn-delete";
    btnDelete.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3px;margin-top:-1px"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>Excluir';
    btnDelete.addEventListener("click", () => deleteFile(f.id));
    actions.appendChild(btnDelete);

    item.appendChild(actions);

    filesList.appendChild(item);
    });
}

function filterFiles(searchTerm) {
    renderFiles(allFiles, searchTerm);
}

// VISUALIZAR ARQUIVO
function viewFile(file) {
    const modal = document.getElementById("file-viewer-modal");
    const title = document.getElementById("file-viewer-title");
    const body = document.getElementById("file-viewer-body");
    
    if (!modal || !title || !body) {
        console.error("Elementos do modal não encontrados");
        return;
    }
    
    title.textContent = file.title || "Visualizando arquivo";
    body.innerHTML = "";
    
    const fileUrl = file.url || (file.file_type === "pdf" 
        ? `/files/pdf/${file.id}` 
        : `/files/gif/${file.id}`);
    
    if (file.file_type === "pdf") {
        const iframe = document.createElement("iframe");
        iframe.src = fileUrl;
        iframe.style.width = "100%";
        iframe.style.height = "70vh";
        iframe.style.border = "none";
        iframe.style.borderRadius = "8px";
        body.appendChild(iframe);
    } else if (file.file_type === "gif") {
        const img = document.createElement("img");
        img.src = fileUrl;
        img.style.maxWidth = "100%";
        img.style.maxHeight = "70vh";
        img.style.borderRadius = "8px";
        img.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.1)";
        body.appendChild(img);
    }
    
    modal.classList.add("active");
    document.body.style.overflow = "hidden";
}

function closeFileViewer() {
    const modal = document.getElementById("file-viewer-modal");
    if (modal) {
        modal.classList.remove("active");
        document.body.style.overflow = "";
    }
}

// Fechar modal ao clicar fora
document.addEventListener("click", (e) => {
    const modal = document.getElementById("file-viewer-modal");
    if (modal && e.target === modal) {
        closeFileViewer();
    }
});

// Fechar modal com ESC
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeFileViewer();
    }
});

// Estado de edição
let editingFileId = null;

function editFile(file) {
    // Se já está editando outro arquivo, cancela a edição anterior
    if (editingFileId && editingFileId !== file.id) {
        cancelEdit(editingFileId);
    }
    
    // Se já está editando este arquivo, cancela
    if (editingFileId === file.id) {
        cancelEdit(file.id);
        return;
    }
    
    editingFileId = file.id;
    
    // Encontra o item na lista
    const items = document.querySelectorAll('.resource-item');
    let itemElement = null;
    items.forEach(item => {
        if (String(item.dataset.fileId) === String(file.id)) {
            itemElement = item;
        }
    });
    
    if (!itemElement) return;
    
    // Adiciona classe de edição
    itemElement.classList.add('editing');
    
    // Encontra elementos
    const titleEl = itemElement.querySelector('.resource-title');
    const tagsEl = itemElement.querySelector('.resource-tags');
    const actionsEl = itemElement.querySelector('.resource-actions');
    
    if (!titleEl || !actionsEl) return;
    
    // Salva valores originais
    const originalTitle = file.title || '';
    const originalTags = file.tags || '';
    
    // Cria inputs de edição
    const titleInput = document.createElement('input');
    titleInput.type = 'text';
    titleInput.className = 'edit-input edit-title-input';
    titleInput.value = originalTitle;
    titleInput.placeholder = 'Título do arquivo';
    
    const tagsInput = document.createElement('input');
    tagsInput.type = 'text';
    tagsInput.className = 'edit-input edit-tags-input';
    tagsInput.value = originalTags;
    tagsInput.placeholder = 'Tags (separadas por vírgula)';
    
    // Substitui título
    const titleContainer = titleEl.parentElement;
    titleEl.style.display = 'none';
    titleInput.style.display = 'block';
    titleContainer.insertBefore(titleInput, titleEl);
    
    // Substitui tags
    if (tagsEl) {
        tagsEl.style.display = 'none';
        tagsInput.style.display = 'block';
        tagsEl.parentElement.insertBefore(tagsInput, tagsEl);
    } else {
        // Se não tinha tags, adiciona o input
        const infoEl = itemElement.querySelector('.resource-info');
        if (infoEl) {
            tagsInput.style.display = 'block';
            infoEl.appendChild(tagsInput);
        }
    }
    
    // Cria botões de ação
    const editActions = document.createElement('div');
    editActions.className = 'edit-actions';
    
    const btnSave = document.createElement('button');
    btnSave.type = 'button';
    btnSave.className = 'btn-small btn-save-edit';
    btnSave.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3px;margin-top:-1px"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>Salvar';
    btnSave.addEventListener('click', () => saveEdit(file.id, titleInput.value, tagsInput.value, originalTitle, originalTags));
    
    const btnCancel = document.createElement('button');
    btnCancel.type = 'button';
    btnCancel.className = 'btn-small btn-cancel-edit';
    btnCancel.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3px;margin-top:-1px"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>Cancelar';
    btnCancel.addEventListener('click', () => cancelEdit(file.id));
    
    editActions.appendChild(btnSave);
    editActions.appendChild(btnCancel);
    
    // Esconde ações originais e mostra ações de edição
    actionsEl.style.display = 'none';
    actionsEl.parentElement.insertBefore(editActions, actionsEl);
    
    // Foca no input de título
    setTimeout(() => titleInput.focus(), 100);
    
    // Salva ao pressionar Enter no título
    titleInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            tagsInput.focus();
        }
    });
    
    // Salva ao pressionar Enter nas tags ou Escape para cancelar
    tagsInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveEdit(file.id, titleInput.value, tagsInput.value, originalTitle, originalTags);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelEdit(file.id);
        }
    });
}

function cancelEdit(fileId) {
    editingFileId = null;
    
    const items = document.querySelectorAll('.resource-item');
    items.forEach(item => {
        if (String(item.dataset.fileId) === String(fileId)) {
            item.classList.remove('editing');
            
            // Remove inputs
            const titleInput = item.querySelector('.edit-title-input');
            const tagsInput = item.querySelector('.edit-tags-input');
            const editActions = item.querySelector('.edit-actions');
            
            if (titleInput) {
                const titleEl = item.querySelector('.resource-title');
                if (titleEl) {
                    titleEl.style.display = '';
                    titleInput.remove();
                }
            }
            
            if (tagsInput) {
                const tagsEl = item.querySelector('.resource-tags');
                if (tagsEl) {
                    tagsEl.style.display = '';
                    tagsInput.remove();
                } else {
                    tagsInput.remove();
                }
            }
            
            if (editActions) {
                const actionsEl = item.querySelector('.resource-actions');
                if (actionsEl) {
                    actionsEl.style.display = '';
                    editActions.remove();
                }
            }
        }
    });
}

async function saveEdit(fileId, newTitle, newTags, originalTitle, originalTags) {
    // Se não mudou nada, apenas cancela
    if (newTitle.trim() === originalTitle && newTags.trim() === originalTags) {
        cancelEdit(fileId);
        return;
    }
    
    const item = document.querySelector(`.resource-item[data-file-id="${fileId}"]`);
    if (!item) return;
    
    // Mostra loading
    const btnSave = item.querySelector('.btn-save-edit');
    if (btnSave) {
        btnSave.disabled = true;
        btnSave.innerHTML = 'Salvando...';
    }
    
    try {
        const headers = getAuthHeaders();
        headers['Content-Type'] = 'application/json';
        
        const res = await fetch(`/admin/files/${fileId}`, {
            method: "PUT",
            headers: headers,
            body: JSON.stringify({ 
                title: newTitle.trim(), 
                tags: newTags.trim() 
            })
        });

        if (!res.ok) {
            if (res.status === 401) {
                if (await login()) {
                    return saveEdit(fileId, newTitle, newTags, originalTitle, originalTags);
                }
            }
            throw new Error("Erro ao atualizar recurso");
        }

        const data = await res.json();
        
        // Atualiza o arquivo na lista local
        const fileIndex = allFiles.findIndex(f => f.id === fileId);
        if (fileIndex !== -1) {
            allFiles[fileIndex].title = data.title;
            allFiles[fileIndex].tags = data.tags;
        }
        
        // Recarrega a lista e estatísticas
        await Promise.all([loadFiles(), loadFileStats()]);
        
        // Feedback visual de sucesso
        if (btnSave) {
            btnSave.innerHTML = 'Salvo!';
            setTimeout(() => {
                cancelEdit(fileId);
            }, 500);
        }
        
    } catch (err) {
        // Erro ao editar recurso
        if (btnSave) {
            btnSave.disabled = false;
            btnSave.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3px;margin-top:-1px"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>Salvar';
        }
        alert("Erro ao atualizar recurso: " + (err.message || "Erro desconhecido"));
    }
}

async function deleteFile(fileId) {
const confirmDelete = window.confirm(
    "Tem certeza que deseja excluir este recurso? Essa ação não pode ser desfeita."
);
if (!confirmDelete) return;

try {
    const res = await fetch(`/admin/files/${fileId}`, {
    method: "DELETE",
    headers: getAuthHeaders()
    });

    if (!res.ok) {
        if (res.status === 401) {
            if (await login()) {
                return deleteFile(fileId);
            }
        }
        alert("Erro ao excluir recurso.");
        return;
    }

    await Promise.all([loadFiles(), loadFileStats()]);
} catch (err) {
    console.error("Erro ao excluir recurso:", err);
    alert("Erro ao excluir recurso.");
}
}

// Event listener do uploadForm será adicionado na função init()

async function init() {
// Logs de debug removidos para produção

// Inicializa elementos
if (!initElements()) {
    console.error("Erro ao inicializar elementos do DOM");
    // Tentando novamente em 100ms
    setTimeout(init, 100);
    return;
}

// Elementos inicializados

// Adiciona event listeners APENAS após elementos serem encontrados
if (btnSavePrompt) {
    btnSavePrompt.addEventListener("click", (e) => {
        e.preventDefault();
        savePrompt();
    });
    // Event listener do btnSavePrompt adicionado
} else {
    console.error("btnSavePrompt não encontrado para adicionar event listener!");
}

if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!uploadStatus) {
            console.error("uploadStatus não encontrado!");
            return;
        }
        
        uploadStatus.textContent = "";
        uploadStatus.classList.remove("error");

        const formData = new FormData(uploadForm);
        const file = formData.get("file");
        if (!file || !file.name) {
            uploadStatus.textContent = "Selecione um arquivo.";
            uploadStatus.classList.add("error");
            return;
        }

        uploadStatus.textContent = "Enviando...";
        try {
            const headers = getAuthHeadersFormData();
            
            const res = await fetch("/admin/files/upload", {
            method: "POST",
            headers: headers,
            body: formData
            });

            if (!res.ok) {
                if (res.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                const errorText = await res.text();
                console.error("Erro no upload:", res.status, errorText);
                uploadStatus.textContent = "Erro ao enviar: " + (errorText || res.statusText);
                uploadStatus.classList.add("error");
                return;
            }

            const data = await res.json();
            // Arquivo enviado com sucesso
            uploadStatus.textContent = "Recurso adicionado com sucesso.";
            uploadForm.reset();
            if (window.clearFileInput) window.clearFileInput();
            await Promise.all([loadFiles(), loadFileStats()]);
            setTimeout(() => { uploadStatus.textContent = ""; }, 2000);
        } catch (err) {
            console.error("Erro no upload:", err);
            uploadStatus.textContent = "Erro ao enviar: " + err.message;
            uploadStatus.classList.add("error");
        }
    });
    // Event listener do uploadForm adicionado
} else {
    console.error("uploadForm não encontrado para adicionar event listener!");
}

// FILTROS POR TIPO
const filterButtons = document.querySelectorAll(".filter-btn");
filterButtons.forEach(btn => {
    btn.addEventListener("click", () => {
        // Remove active de todos
        filterButtons.forEach(b => b.classList.remove("active"));
        // Adiciona active no clicado
        btn.classList.add("active");
        // Atualiza filtro
        currentTypeFilter = btn.dataset.filter || "all";
        // Reaplica filtros
        const searchTerm = fileSearch ? fileSearch.value.toLowerCase().trim() : "";
        filterFiles(searchTerm);
    });
});

// BARRA DE PESQUISA
if (fileSearch) {
    fileSearch.addEventListener("input", (e) => {
        const searchTerm = e.target.value.toLowerCase().trim();
        filterFiles(searchTerm);
        
        if (searchTerm.length > 0) {
            if (clearSearchBtn) clearSearchBtn.style.display = "flex";
        } else {
            if (clearSearchBtn) clearSearchBtn.style.display = "none";
        }
    });
    
    fileSearch.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            fileSearch.value = "";
            if (clearSearchBtn) clearSearchBtn.style.display = "none";
            filterFiles("");
        }
    });
    // Event listener da barra de pesquisa adicionado
} else {
    // Barra de pesquisa não encontrada
}

if (clearSearchBtn) {
    clearSearchBtn.addEventListener("click", () => {
        if (fileSearch) {
            fileSearch.value = "";
            clearSearchBtn.style.display = "none";
            filterFiles("");
            fileSearch.focus();
        }
    });
    // Event listener do botão limpar pesquisa adicionado
}

// Atualiza token antes de verificar
authToken = getAuthToken();
// Log de token removido por segurança

// Verifica se tem token, se não tiver, redireciona para login
if (!authToken) {
    // Sem token, redirecionando para login
    window.location.href = '/login';
    return;
}

try {
    await Promise.all([loadPrompt(), loadFiles(), loadFileStats()]);
    // Inicialização concluída
} catch (err) {
    console.error("Erro na inicialização:", err);
    alert("Erro ao inicializar: " + err.message);
}
}

// ESTATÍSTICAS DE ARQUIVOS
async function loadFileStats() {
    if (!statPdfs || !statGifs || !statTotalSize) {
        // Elementos de estatísticas não encontrados
        return;
    }

    try {
        const headers = getAuthHeaders();
        
        if (!headers.Authorization) {
            console.error("Token não encontrado nos headers!");
            return;
        }
        
        const res = await fetch("/admin/files/stats", {
            headers: headers
        });
        
        if (!res.ok) {
            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }
            const errorText = await res.text();
            console.error("Erro ao carregar estatísticas:", res.status, errorText);
            return;
        }
        
        const data = await res.json();
        // Estatísticas recebidas
        
        if (statPdfs) statPdfs.textContent = data.total_pdfs || 0;
        if (statGifs) statGifs.textContent = data.total_gifs || 0;
        if (statTotalSize) {
            statTotalSize.textContent = formatFileSize(data.total_size_bytes || 0);
        }
    } catch (err) {
        console.error("Erro ao carregar estatísticas de arquivos:", err);
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Teste imediato para verificar se o script está carregando
// Log de inicialização removido para produção

// ====== BACKUP ======
function showBackupModal(title, message, status, progress = 0) {
    const modal = document.getElementById("backup-download-modal");
    const modalTitle = document.getElementById("backup-modal-title");
    const modalMessage = document.getElementById("backup-modal-message");
    const modalStatus = document.getElementById("backup-modal-status");
    const progressBar = document.getElementById("backup-progress-bar");
    
    if (modal) {
        modal.classList.add("active");
        if (modalTitle) modalTitle.textContent = title;
        if (modalMessage) modalMessage.textContent = message;
        if (modalStatus) modalStatus.textContent = status;
        if (progressBar) progressBar.style.width = progress + "%";
    }
}

function hideBackupModal() {
    const modal = document.getElementById("backup-download-modal");
    if (modal) {
        modal.classList.remove("active");
    }
}

async function createBackup() {
    const btnBackup = document.getElementById("btn-backup");
    if (!btnBackup) {
        console.error("Botão de backup não encontrado!");
        return;
    }
    
    // Salva o estado original
    const originalText = btnBackup.textContent;
    const originalHTML = btnBackup.innerHTML;
    
    // Desabilita o botão e mostra loading com animação
    btnBackup.classList.add("loading");
    btnBackup.textContent = "Criando backup";
    btnBackup.disabled = true;
    
    // Mostra modal de download
    showBackupModal("Criando Backup", "Preparando os arquivos...", "Iniciando processo de backup", 10);
    
    // Iniciando backup
    
    try {
        const token = getAuthToken();
        if (!token) {
            hideBackupModal();
            alert("Você precisa estar autenticado para fazer backup.");
            window.location.href = '/login';
            return;
        }
        
        showBackupModal("Criando Backup", "Conectando ao servidor...", "Verificando autenticação", 20);
        
        // Fazendo requisição para /admin/backup
        
        // Faz a requisição
        showBackupModal("Criando Backup", "Processando backup...", "Executando script de backup", 40);
        
        const res = await fetch("/admin/backup", {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        // Resposta recebida
        
        if (!res.ok) {
            hideBackupModal();
            if (res.status === 401) {
                alert("Sessão expirada. Por favor, faça login novamente.");
                window.location.href = '/login';
                return;
            }
            
            const errorText = await res.text().catch(() => "Erro desconhecido");
            console.error("Erro na resposta:", errorText);
            throw new Error(`Erro ao criar backup: ${res.status} - ${errorText}`);
        }
        
        showBackupModal("Criando Backup", "Backup criado com sucesso!", "Preparando download...", 70);
        
        // Obtém o nome do arquivo do header Content-Disposition ou usa padrão
        const contentDisposition = res.headers.get("Content-Disposition");
        let filename = "urania_backup.tar.gz";
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1].replace(/['"]/g, '');
            }
        }
        
        // Nome do arquivo obtido
        
        showBackupModal("Baixando Backup", `Arquivo: ${filename}`, "Transferindo arquivo...", 80);
        
        // Cria blob e faz download
        const blob = await res.blob();
        
        // Blob criado
        
        // Verifica se o blob não está vazio
        if (blob.size === 0) {
            hideBackupModal();
            throw new Error("Arquivo de backup está vazio");
        }
        
        const sizeMB = (blob.size / 1024 / 1024).toFixed(2);
        // Download iniciado
        
        showBackupModal("Baixando Backup", `Arquivo: ${filename}`, `Tamanho: ${sizeMB} MB - Iniciando download...`, 90);
        
        // Cria link de download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        
        // Força o download
        a.click();
        
        // Mostra sucesso no modal
        showBackupModal("Download Concluído!", `Arquivo: ${filename}`, `Tamanho: ${sizeMB} MB - Download iniciado!`, 100);
        
        // Aguarda um pouco antes de limpar (para garantir que o download iniciou)
        setTimeout(() => {
            window.URL.revokeObjectURL(url);
            if (a.parentNode) {
                document.body.removeChild(a);
            }
        }, 500);
        
        // Fecha o modal após 2 segundos
        setTimeout(() => {
            hideBackupModal();
            
            // Sucesso - remove animação e mostra mensagem no botão
            btnBackup.classList.remove("loading");
            btnBackup.disabled = false;
            btnBackup.textContent = "Download concluído!";
            btnBackup.style.background = "linear-gradient(135deg, #16a34a 0%, #15803d 100%)";
            btnBackup.style.animation = "none";
            
            // Backup concluído com sucesso
            
            // Restaura após 3 segundos
            setTimeout(() => {
                btnBackup.textContent = originalText;
                btnBackup.innerHTML = originalHTML;
                btnBackup.style.background = "";
                btnBackup.style.animation = "";
            }, 3000);
        }, 2000);
        
    } catch (err) {
        console.error("Erro ao criar backup:", err);
        
        // Mostra erro no modal
        showBackupModal("Erro no Backup", err.message, "Tente novamente mais tarde", 0);
        
        setTimeout(() => {
            hideBackupModal();
            alert("Erro ao criar backup: " + err.message);
        }, 3000);
        
        // Restaura estado original em caso de erro
        btnBackup.classList.remove("loading");
        btnBackup.disabled = false;
        btnBackup.textContent = originalText;
        btnBackup.innerHTML = originalHTML;
        btnBackup.style.background = "";
        btnBackup.style.animation = "";
    }
}

// Adiciona event listener ao botão de backup
function setupBackupButton() {
    const btnBackup = document.getElementById("btn-backup");
    if (btnBackup) {
        // Remove event listeners anteriores para evitar duplicação
        const newBtn = btnBackup.cloneNode(true);
        btnBackup.parentNode.replaceChild(newBtn, btnBackup);
        
        newBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            // Botão de backup clicado
            createBackup();
            return false;
        });
        
        // Também previne o comportamento padrão no href
        newBtn.setAttribute("href", "javascript:void(0)");
        newBtn.setAttribute("onclick", "return false;");
        // Botão de backup configurado
    } else {
        console.warn("Botão de backup não encontrado no DOM");
    }
}

// Tenta configurar imediatamente (se DOM já estiver pronto)
if (document.readyState === 'loading') {
    document.addEventListener("DOMContentLoaded", setupBackupButton);
} else {
    // DOM já está pronto
    setupBackupButton();
}

// DRAG AND DROP FUNCTIONALITY
function setupDragAndDrop() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview');
    const filePreviewName = filePreview.querySelector('.file-preview-name');
    const filePreviewSize = filePreview.querySelector('.file-preview-size');
    const dropZoneContent = dropZone.querySelector('.drop-zone-content');

    if (!dropZone || !fileInput) return;

    // Click to select file
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drag-over');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drag-over');
        }, false);
    });

    // Handle dropped files
    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect(files[0]);
        }
    }, false);

    // Handle file input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        // Validate file type
        const fileType = file.name.split('.').pop().toLowerCase();
        if (fileType !== 'pdf' && fileType !== 'gif') {
            alert('Por favor, selecione um arquivo PDF ou GIF.');
            fileInput.value = '';
            return;
        }

        // Validate file size (50MB)
        if (file.size > 50 * 1024 * 1024) {
            alert('O arquivo é muito grande. Tamanho máximo: 50MB');
            fileInput.value = '';
            return;
        }

        // Show preview
        filePreviewName.textContent = file.name;
        filePreviewSize.textContent = formatFileSize(file.size);
        filePreview.style.display = 'flex';
        dropZoneContent.style.display = 'none';

        // Update file type select if needed
        const fileTypeSelect = document.getElementById('file-type');
        if (fileTypeSelect && fileType === 'pdf') {
            fileTypeSelect.value = 'pdf';
        } else if (fileTypeSelect && fileType === 'gif') {
            fileTypeSelect.value = 'gif';
        }
    }

    window.clearFileInput = function() {
        fileInput.value = '';
        filePreview.style.display = 'none';
        dropZoneContent.style.display = 'flex';
    };

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
}

// Aguarda DOM estar pronto antes de inicializar
if (document.readyState === 'loading') {
    // DOM ainda carregando, aguardando DOMContentLoaded
    document.addEventListener('DOMContentLoaded', () => {
        // DOMContentLoaded disparado
        setupDragAndDrop();
        setupBackupButton();
        init();
    });
} else {
    // DOM já está pronto
    // DOM já está pronto, inicializando imediatamente
    setupDragAndDrop();
    setupBackupButton();
    init();
}