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
        console.log("localStorage completo:", {...localStorage});
        return {};
    }
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
    console.log("Headers criados:", headers);
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
    console.log("Carregando prompt...");
    const headers = getAuthHeaders();
    console.log("Headers:", headers);
    
    if (!headers.Authorization) {
        console.error("Token não encontrado nos headers!");
        window.location.href = '/login';
        return;
    }
    
    const res = await fetch("/admin/prompt", {
        headers: headers
    });
    
    console.log("Resposta prompt:", res.status, res.statusText);
    
    if (!res.ok) {
        if (res.status === 401) {
            console.log("Token inválido, redirecionando para login");
            window.location.href = '/login';
            return;
        }
        const errorText = await res.text();
        console.error("Erro ao carregar prompt:", res.status, errorText);
        alert(`Erro ao carregar prompt: ${res.status} - ${errorText}`);
        return;
    }
    const data = await res.json();
    console.log("Prompt carregado:", data.prompt ? `${data.prompt.length} caracteres` : "vazio");
    console.log("Dados recebidos:", data);
    
    if (!promptText) {
        console.error("promptText não encontrado após carregar dados! Re-inicializando...");
        if (!initElements() || !promptText) {
            console.error("Não foi possível encontrar promptText após re-inicialização");
            return;
        }
    }
    
    promptText.value = data.prompt || "";
    console.log("Prompt definido no textarea:", promptText.value.length, "caracteres");
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
btnSavePrompt.disabled = true;
promptStatus.textContent = "Salvando...";
promptStatus.classList.remove("error");

try {
    console.log("Salvando prompt...", value.length, "caracteres");
    const headers = getAuthHeaders();
    console.log("Headers:", headers);
    
    const res = await fetch("/admin/prompt", {
    method: "PUT",
    headers: headers,
    body: JSON.stringify({ prompt: value })
    });

    console.log("Resposta save prompt:", res.status, res.statusText);

    if (!res.ok) {
        if (res.status === 401) {
            console.log("Token inválido, redirecionando para login");
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
    console.log("Prompt salvo com sucesso:", data);
    promptStatus.textContent = "Prompt salvo com sucesso.";
    setTimeout(() => { promptStatus.textContent = ""; }, 2000);
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
    console.log("Carregando arquivos...");
    const headers = getAuthHeaders();
    console.log("Headers:", headers);
    
    if (!headers.Authorization) {
        console.error("Token não encontrado nos headers!");
        window.location.href = '/login';
        return;
    }
    
    const res = await fetch("/admin/files", {
        headers: headers
    });
    
    console.log("Resposta arquivos:", res.status, res.statusText);
    
    if (!res.ok) {
        if (res.status === 401) {
            console.log("Token inválido, redirecionando para login");
            window.location.href = '/login';
            return;
        }
        const errorText = await res.text();
        console.error("Erro ao carregar arquivos:", res.status, errorText);
        alert(`Erro ao carregar arquivos: ${res.status} - ${errorText}`);
        return;
    }
    const files = await res.json();
    console.log("Arquivos recebidos:", files.length);
    if (files.length > 0) {
        console.log("Primeiro arquivo:", files[0]);
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
        console.log("Nenhum arquivo encontrado" + (searchTerm ? " para: " + searchTerm : ""));
        if (filesEmpty) {
            filesEmpty.textContent = searchTerm 
                ? `Nenhum recurso encontrado para "${searchTerm}"`
                : "Nenhum recurso cadastrado ainda.";
            filesEmpty.style.display = "block";
        }
        if (filesList) filesList.style.display = "none";
        return;
    }

    console.log("Renderizando", filteredFiles.length, "arquivos" + (searchTerm ? " (filtrados)" : ""));
    if (filesEmpty) filesEmpty.style.display = "none";
    if (filesList) filesList.style.display = "grid";

    filteredFiles.forEach(f => {
    const item = document.createElement("div");
    item.className = "resource-item";

    // Header com ícone e informações principais
    const header = document.createElement("div");
    header.className = "resource-item-header";

    const icon = document.createElement("div");
    icon.className = "resource-icon " + (f.file_type === "pdf" ? "pdf" : "gif");
    icon.textContent = f.file_type === "pdf" ? "📄" : "🖼️";
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
    btnView.textContent = "👁️ Visualizar";
    btnView.addEventListener("click", () => viewFile(f));
    actions.appendChild(btnView);

    const btnEdit = document.createElement("button");
    btnEdit.type = "button";
    btnEdit.className = "btn-small btn-edit";
    btnEdit.textContent = "✏️ Editar";
    btnEdit.addEventListener("click", () => editFile(f));
    actions.appendChild(btnEdit);

    const btnDelete = document.createElement("button");
    btnDelete.type = "button";
    btnDelete.className = "btn-small btn-delete";
    btnDelete.textContent = "🗑️ Excluir";
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

async function editFile(file) {
const newTitle = window.prompt("Editar título:", file.title || "");
if (newTitle === null) return;

const newTags = window.prompt("Editar tags (separadas por vírgula):", file.tags || "");
if (newTags === null) return;

try {
    const res = await fetch(`/admin/files/${file.id}`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify({ title: newTitle, tags: newTags })
    });

    if (!res.ok) {
        if (res.status === 401) {
            if (await login()) {
                return editFile(file);
            }
        }
        alert("Erro ao atualizar recurso.");
        return;
    }

    await Promise.all([loadFiles(), loadFileStats()]);
} catch (err) {
    console.error("Erro ao editar recurso:", err);
    alert("Erro ao editar recurso.");
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
console.log("=== INICIALIZANDO ADMIN ===");
console.log("Estado do DOM:", document.readyState);
console.log("URL atual:", window.location.href);

// Inicializa elementos
if (!initElements()) {
    console.error("Erro ao inicializar elementos do DOM");
    console.log("Tentando novamente em 100ms...");
    setTimeout(init, 100);
    return;
}

console.log("Elementos encontrados:");
console.log("  - promptText:", !!promptText);
console.log("  - filesList:", !!filesList);
console.log("  - btnSavePrompt:", !!btnSavePrompt);
console.log("  - uploadForm:", !!uploadForm);

// Adiciona event listeners APENAS após elementos serem encontrados
if (btnSavePrompt) {
    btnSavePrompt.addEventListener("click", (e) => {
        e.preventDefault();
        savePrompt();
    });
    console.log("Event listener do btnSavePrompt adicionado");
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
            console.log("Enviando arquivo...");
            const headers = getAuthHeadersFormData();
            console.log("Headers upload:", headers);
            
            const res = await fetch("/admin/files/upload", {
            method: "POST",
            headers: headers,
            body: formData
            });

            console.log("Resposta upload:", res.status, res.statusText);

            if (!res.ok) {
                if (res.status === 401) {
                    console.log("Token inválido, redirecionando para login");
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
            console.log("Arquivo enviado com sucesso:", data);
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
    console.log("Event listener do uploadForm adicionado");
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
    console.log("Event listener da barra de pesquisa adicionado");
} else {
    console.log("Barra de pesquisa não encontrada");
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
    console.log("Event listener do botão limpar pesquisa adicionado");
}

// Atualiza token antes de verificar
authToken = getAuthToken();
console.log("Token presente:", !!authToken);
console.log("Token:", authToken ? authToken.substring(0, 20) + "..." : "não encontrado");

// Verifica se tem token, se não tiver, redireciona para login
if (!authToken) {
    console.log("Sem token, redirecionando para login");
    window.location.href = '/login';
    return;
}

console.log("Carregando dados...");
try {
    await Promise.all([loadPrompt(), loadFiles(), loadFileStats()]);
    console.log("=== INICIALIZAÇÃO CONCLUÍDA ===");
    console.log("Prompt carregado:", promptText ? promptText.value.length + " caracteres" : "NÃO");
    console.log("Arquivos carregados:", filesList ? filesList.children.length + " itens" : "NÃO");
} catch (err) {
    console.error("Erro na inicialização:", err);
    alert("Erro ao inicializar: " + err.message);
}
}

// ESTATÍSTICAS DE ARQUIVOS
async function loadFileStats() {
    if (!statPdfs || !statGifs || !statTotalSize) {
        console.log("Elementos de estatísticas não encontrados");
        return;
    }

    try {
        console.log("Carregando estatísticas de arquivos...");
        const headers = getAuthHeaders();
        
        if (!headers.Authorization) {
            console.error("Token não encontrado nos headers!");
            return;
        }
        
        const res = await fetch("/admin/files/stats", {
            headers: headers
        });
        
        console.log("Resposta stats:", res.status, res.statusText);
        
        if (!res.ok) {
            if (res.status === 401) {
                console.log("Token inválido, redirecionando para login");
                window.location.href = '/login';
                return;
            }
            const errorText = await res.text();
            console.error("Erro ao carregar estatísticas:", res.status, errorText);
            return;
        }
        
        const data = await res.json();
        console.log("Estatísticas recebidas:", data);
        
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
console.log("=== ADMIN.JS CARREGADO ===");
console.log("Timestamp:", new Date().toISOString());

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
    console.log("DOM ainda carregando, aguardando DOMContentLoaded...");
    document.addEventListener('DOMContentLoaded', () => {
        console.log("DOMContentLoaded disparado!");
        setupDragAndDrop();
        init();
    });
} else {
    // DOM já está pronto
    console.log("DOM já está pronto, inicializando imediatamente...");
    setupDragAndDrop();
    init();
}