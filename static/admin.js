// Desabilita console.log em produção (mantém apenas console.error)
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
if (isProduction) {
    console.log = function() {}; // Remove logs em produção
    console.debug = function() {}; // Remove debug em produção
}

// Aguarda DOM estar pronto
let promptText, btnSavePrompt, promptStatus, uploadForm, uploadStatus, filesEmpty, filesList;
let statPdfs, statGifs, statImages, statTotalSize;
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
    statImages = document.getElementById("stat-images");
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

function sortFilesByIdAsc(arr) {
    return [...arr].sort((a, b) => (Number(a.id) || 0) - (Number(b.id) || 0));
}

/** Cartão de um recurso; em pastas use nested + hideGroupBadge para não repetir o selo "Grupo". */
function buildResourceItemElement(f, options) {
    const opts = options || {};
    const nested = !!opts.nested;
    const hideGroupBadge = !!opts.hideGroupBadge;
    const standalone = !!opts.standalone && !nested;

    const item = document.createElement("div");
    let itemClass = "resource-item" + (nested ? " resource-item-nested" : "");
    if (standalone) {
        itemClass += " resource-item--standalone";
        const ft0 = (f.file_type || "").toLowerCase();
        if (ft0 === "image") itemClass += " resource-item--standalone-img";
        else if (ft0 === "gif") itemClass += " resource-item--standalone-gif";
        else if (ft0 === "pdf") itemClass += " resource-item--standalone-pdf";
    }
    item.className = itemClass;
    item.dataset.fileId = f.id;

    const ft = (f.file_type || "").toLowerCase();
    const iconExtra = ft === "pdf" ? "pdf" : ft === "image" ? "image" : ft === "gif" ? "gif" : "";
    const iconSvg = ft === "pdf"
        ? '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
        : '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>';

    const header = document.createElement("div");
    header.className = "resource-item-header";

    const icon = document.createElement("div");
    icon.className = "resource-icon " + iconExtra;
    icon.innerHTML = iconSvg;
    header.appendChild(icon);

    const info = document.createElement("div");
    info.className = "resource-info";

    const titleRow = document.createElement("div");
    titleRow.className = "resource-header";

    const typePill = document.createElement("span");
    typePill.className = "resource-type-pill " + (ft === "pdf" ? "pdf" : ft === "image" ? "image" : ft === "gif" ? "gif" : "");
    const typeLabel = ft === "image" ? "IMAGEM" : (f.file_type || "").toUpperCase();
    typePill.textContent = typeLabel;
    titleRow.appendChild(typePill);

    if (f.group_id && !hideGroupBadge) {
        const gb = document.createElement("span");
        gb.className = "resource-group-badge";
        gb.textContent = "Grupo";
        gb.title = "Parte de um conjunto de imagens e/ou GIFs enviados juntos";
        titleRow.appendChild(gb);
    }

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

    if (f.description && f.description.trim()) {
        const descEl = document.createElement("div");
        descEl.className = "resource-desc";
        descEl.textContent = f.description.trim();
        info.appendChild(descEl);
    }

    header.appendChild(info);
    item.appendChild(header);

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
    return item;
}

function appendResourceOrganizeSection(title, subtitle, bodyEl) {
    const section = document.createElement("section");
    section.className = "resource-organize-section";
    const head = document.createElement("div");
    head.className = "resource-section-head";
    const h3 = document.createElement("h3");
    h3.className = "resource-section-title";
    h3.textContent = title;
    head.appendChild(h3);
    if (subtitle) {
        const p = document.createElement("p");
        p.className = "resource-section-sub";
        p.textContent = subtitle;
        head.appendChild(p);
    }
    section.appendChild(head);
    section.appendChild(bodyEl);
    filesList.appendChild(section);
}

/**
 * Sub-secção dentro de Imagens/GIFs/PDF: separa visualmente pastas (grupos) de ficheiros únicos.
 * kind: groups | groups-gif | standalone-image | standalone-gif | groups-mixed | pdf-list
 */
function createResourceSubblock(kind, title, hint) {
    const wrap = document.createElement("div");
    wrap.className = "resource-subblock resource-subblock--" + kind;
    const head = document.createElement("div");
    head.className = "resource-subblock-head";
    const h4 = document.createElement("h4");
    h4.className = "resource-subblock-title";
    h4.textContent = title;
    const hintEl = document.createElement("p");
    hintEl.className = "resource-subblock-hint";
    hintEl.textContent = hint;
    head.appendChild(h4);
    head.appendChild(hintEl);
    const body = document.createElement("div");
    body.className = "resource-subblock-body";
    wrap.appendChild(head);
    wrap.appendChild(body);
    return { wrap, body };
}

function getMediaFilesFromCatalog(catalog) {
    return catalog.filter(f => f.file_type === "image" || f.file_type === "gif");
}

/** Tipo real do grupo (usa `catalog` completo, ex. allFiles) para o filtro não partir grupos mistos. */
function classifyGroupKind(groupId, catalog) {
    const files = getMediaFilesFromCatalog(catalog).filter(f => f.group_id === groupId);
    const hasImage = files.some(f => f.file_type === "image");
    const hasGif = files.some(f => f.file_type === "gif");
    if (hasImage && hasGif) return "mixed";
    if (hasGif) return "gif";
    return "image";
}

function sortGroupIdsInPlace(gids, groupedMap) {
    gids.sort((a, b) => {
        const minA = Math.min(...groupedMap.get(a).map(x => x.id));
        const minB = Math.min(...groupedMap.get(b).map(x => x.id));
        return minA - minB;
    });
}

const FOLDER_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>';

/** Pasta de grupo: `folderKind` image | gif | mixed (ícone/cor). */
function createGroupFolderDetails(groupFiles, folderKind) {
    const files = sortFilesByIdAsc(groupFiles);
    let groupLabel = "(sem título)";
    for (let gi = 0; gi < files.length; gi++) {
        const t = (files[gi].title || "").trim();
        if (t) {
            groupLabel = t;
            break;
        }
    }
    const fk = folderKind === "gif" || folderKind === "image" || folderKind === "mixed" ? folderKind : "mixed";
    const details = document.createElement("details");
    details.className = "resource-folder";
    details.open = true;
    const sum = document.createElement("summary");
    const tit = document.createElement("div");
    tit.className = "resource-folder-title";
    const ic = document.createElement("div");
    ic.className = "resource-folder-icon resource-folder-icon--" + fk;
    ic.innerHTML = FOLDER_SVG;
    const span = document.createElement("span");
    span.className = "resource-folder-name";
    span.textContent = groupLabel;
    span.title = groupLabel;
    tit.appendChild(ic);
    tit.appendChild(span);
    const meta = document.createElement("span");
    meta.className = "resource-folder-meta";
    meta.textContent = files.length + " arquivo" + (files.length !== 1 ? "s" : "");
    sum.appendChild(tit);
    sum.appendChild(meta);
    const inner = document.createElement("div");
    inner.className = "resource-folder-items";
    files.forEach(f => inner.appendChild(buildResourceItemElement(f, { nested: true, hideGroupBadge: true })));
    details.appendChild(sum);
    details.appendChild(inner);
    return details;
}

function renderFiles(files, searchTerm = "") {
    if (!filesList) return;

    let filteredFiles = files;
    if (currentTypeFilter !== "all") {
        filteredFiles = files.filter(f =>
            (f.file_type || "").toLowerCase() === currentTypeFilter.toLowerCase()
        );
    }

    const st = (searchTerm || "").toLowerCase().trim();
    if (st) {
        filteredFiles = filteredFiles.filter(f => {
            const title = (f.title || "").toLowerCase();
            const tags = (f.tags || "").toLowerCase();
            const desc = (f.description || "").toLowerCase();
            return title.includes(st) || tags.includes(st) || desc.includes(st);
        });
    }

    filesList.innerHTML = "";

    if (!filteredFiles || filteredFiles.length === 0) {
        if (filesEmpty) {
            filesEmpty.textContent = st
                ? `Nenhum recurso encontrado para "${searchTerm}"`
                : "Nenhum recurso cadastrado ainda.";
            filesEmpty.style.display = "block";
        }
        if (filesList) filesList.style.display = "none";
        return;
    }

    if (filesEmpty) filesEmpty.style.display = "none";
    filesList.style.display = "flex";
    filesList.className = "resource-list resource-list-organized";

    const catalog = allFiles;
    const showPdf = currentTypeFilter === "all" || currentTypeFilter === "pdf";
    const showImageBlock = currentTypeFilter === "all" || currentTypeFilter === "image";
    const showGifBlock = currentTypeFilter === "all" || currentTypeFilter === "gif";

    const pdfs = sortFilesByIdAsc(filteredFiles.filter(f => f.file_type === "pdf"));
    const mediaOnly = filteredFiles.filter(f => f.file_type === "image" || f.file_type === "gif");

    const groupedMap = new Map();
    for (const f of mediaOnly) {
        if (!f.group_id) continue;
        if (!groupedMap.has(f.group_id)) groupedMap.set(f.group_id, []);
        groupedMap.get(f.group_id).push(f);
    }
    for (const arr of groupedMap.values()) {
        sortFilesByIdAsc(arr);
    }

    const groupIdsPresent = [...groupedMap.keys()];
    const imageOnlyGids = [];
    const gifOnlyGids = [];
    const mixedGids = [];
    for (const gid of groupIdsPresent) {
        const kind = classifyGroupKind(gid, catalog);
        if (kind === "mixed") mixedGids.push(gid);
        else if (kind === "gif") gifOnlyGids.push(gid);
        else imageOnlyGids.push(gid);
    }
    sortGroupIdsInPlace(imageOnlyGids, groupedMap);
    sortGroupIdsInPlace(gifOnlyGids, groupedMap);
    sortGroupIdsInPlace(mixedGids, groupedMap);

    const ungroupedImages = sortFilesByIdAsc(mediaOnly.filter(f => !f.group_id && f.file_type === "image"));
    const ungroupedGifs = sortFilesByIdAsc(mediaOnly.filter(f => !f.group_id && f.file_type === "gif"));

    if (showPdf && pdfs.length > 0) {
        const list = document.createElement("div");
        list.className = "resource-section-list resource-section-list--split";
        const sb = createResourceSubblock("pdf-list", "Lista de PDFs", "Cada cartão é um documento enviado em separado.");
        pdfs.forEach(f => sb.body.appendChild(buildResourceItemElement(f, { nested: false, hideGroupBadge: true, standalone: true })));
        list.appendChild(sb.wrap);
        appendResourceOrganizeSection("Documentos PDF", "Secção só de PDFs; abaixo, imagens e GIFs têm grupos e ficheiros únicos bem distintos.", list);
    }

    if (showImageBlock) {
        const list = document.createElement("div");
        list.className = "resource-section-list resource-section-list--split";
        const hasImageGroups = imageOnlyGids.length > 0 || (currentTypeFilter === "image" && mixedGids.length > 0);
        if (hasImageGroups) {
            const sb = createResourceSubblock(
                "groups",
                "Grupos (pastas)",
                "Vários ficheiros no mesmo envio — expanda para ver cada imagem."
            );
            imageOnlyGids.forEach(gid => sb.body.appendChild(createGroupFolderDetails(groupedMap.get(gid), "image")));
            if (currentTypeFilter === "image") {
                mixedGids.forEach(gid => sb.body.appendChild(createGroupFolderDetails(groupedMap.get(gid), "mixed")));
            }
            list.appendChild(sb.wrap);
        }
        if (ungroupedImages.length > 0) {
            const sb = createResourceSubblock(
                "standalone-image",
                "Ficheiros únicos",
                "Um único ficheiro por envio, sem pasta — não pertence a um grupo."
            );
            ungroupedImages.forEach(f =>
                sb.body.appendChild(buildResourceItemElement(f, { nested: false, hideGroupBadge: true, standalone: true }))
            );
            list.appendChild(sb.wrap);
        }
        if (list.children.length > 0) {
            appendResourceOrganizeSection(
                "Imagens",
                "Imagens estáticas. Com «Todos» ativo, grupos só de imagem ficam aqui; envios imagem+GIF em «Grupos mistos».",
                list
            );
        }
    }

    if (showGifBlock) {
        const list = document.createElement("div");
        list.className = "resource-section-list resource-section-list--split";
        const hasGifGroups = gifOnlyGids.length > 0 || (currentTypeFilter === "gif" && mixedGids.length > 0);
        if (hasGifGroups) {
            const sb = createResourceSubblock(
                "groups-gif",
                "Grupos (pastas)",
                "Vários GIFs no mesmo envio — expanda para listar cada um."
            );
            gifOnlyGids.forEach(gid => sb.body.appendChild(createGroupFolderDetails(groupedMap.get(gid), "gif")));
            if (currentTypeFilter === "gif") {
                mixedGids.forEach(gid => sb.body.appendChild(createGroupFolderDetails(groupedMap.get(gid), "mixed")));
            }
            list.appendChild(sb.wrap);
        }
        if (ungroupedGifs.length > 0) {
            const sb = createResourceSubblock(
                "standalone-gif",
                "Ficheiros únicos",
                "Um único GIF por envio, sem pasta — não pertence a um grupo."
            );
            ungroupedGifs.forEach(f =>
                sb.body.appendChild(buildResourceItemElement(f, { nested: false, hideGroupBadge: true, standalone: true }))
            );
            list.appendChild(sb.wrap);
        }
        if (list.children.length > 0) {
            appendResourceOrganizeSection(
                "GIFs",
                "GIFs animados. Com «Todos» ativo, grupos só de GIF ficam aqui; envios mistos em «Grupos mistos».",
                list
            );
        }
    }

    if (currentTypeFilter === "all" && mixedGids.length > 0) {
        const list = document.createElement("div");
        list.className = "resource-section-list resource-section-list--split";
        const sb = createResourceSubblock(
            "groups-mixed",
            "Pastas (imagem + GIF)",
            "O mesmo título de envio; a ordem abaixo é a usada no chat."
        );
        mixedGids.forEach(gid => sb.body.appendChild(createGroupFolderDetails(groupedMap.get(gid), "mixed")));
        list.appendChild(sb.wrap);
        appendResourceOrganizeSection(
            "Grupos mistos (imagens e GIFs)",
            "Só aparece na vista «Todos». Separa-se de grupos só-imagem e só-GIF.",
            list
        );
    }

    if (filesList.children.length === 0) {
        if (filesEmpty) {
            filesEmpty.textContent = st
                ? `Nenhum recurso encontrado para "${searchTerm}"`
                : "Nenhum recurso cadastrado ainda.";
            filesEmpty.style.display = "block";
        }
        filesList.style.display = "none";
    }
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
    
    let fileUrl = file.url;
    if (!fileUrl) {
        if (file.file_type === "pdf") fileUrl = `/files/pdf/${file.id}`;
        else if (file.file_type === "gif") fileUrl = `/files/gif/${file.id}`;
        else if (file.file_type === "image") fileUrl = `/files/image/${file.id}`;
    }
    
    if (file.file_type === "pdf") {
        const iframe = document.createElement("iframe");
        iframe.src = fileUrl;
        iframe.style.width = "100%";
        iframe.style.height = "70vh";
        iframe.style.border = "none";
        iframe.style.borderRadius = "8px";
        body.appendChild(iframe);
    } else if (file.file_type === "gif" || file.file_type === "image") {
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
    const originalDescription = file.description || '';
    
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

    const descInput = document.createElement('textarea');
    descInput.className = 'edit-input edit-desc-input';
    descInput.value = originalDescription;
    descInput.placeholder = 'Descrição para a IA (opcional)';
    descInput.rows = 2;
    
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

    const infoForDesc = itemElement.querySelector('.resource-info');
    if (infoForDesc) {
        descInput.style.display = 'block';
        infoForDesc.appendChild(descInput);
    }
    
    // Cria botões de ação
    const editActions = document.createElement('div');
    editActions.className = 'edit-actions';
    
    const btnSave = document.createElement('button');
    btnSave.type = 'button';
    btnSave.className = 'btn-small btn-save-edit';
    btnSave.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:3px;margin-top:-1px"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>Salvar';
    btnSave.addEventListener('click', () => saveEdit(file.id, titleInput.value, tagsInput.value, descInput.value, originalTitle, originalTags, originalDescription));
    
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
            saveEdit(file.id, titleInput.value, tagsInput.value, descInput.value, originalTitle, originalTags, originalDescription);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelEdit(file.id);
        }
    });

    descInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
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

            const descInputEl = item.querySelector('.edit-desc-input');
            if (descInputEl) {
                descInputEl.remove();
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

async function saveEdit(fileId, newTitle, newTags, newDescription, originalTitle, originalTags, originalDescription) {
    const nt = newTitle.trim();
    const ntags = newTags.trim();
    const ndesc = (newDescription || '').trim();
    const odesc = (originalDescription || '').trim();
    if (nt === originalTitle && ntags === originalTags && ndesc === odesc) {
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
                title: nt, 
                tags: ntags,
                description: ndesc || null
            })
        });

        if (!res.ok) {
            if (res.status === 401) {
                if (await login()) {
                    return saveEdit(fileId, newTitle, newTags, newDescription, originalTitle, originalTags, originalDescription);
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
            allFiles[fileIndex].description = data.description;
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
    if (!statImages) statImages = document.getElementById("stat-images");

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
        if (statImages) statImages.textContent = data.total_images || 0;
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

function setupResourceUploadPanels() {
    const tabSingle = document.getElementById("tab-upload-single");
    const tabGroup = document.getElementById("tab-upload-group");
    const panelSingle = document.querySelector('.upload-panel[data-panel="single"]');
    const panelGroup = document.querySelector('.upload-panel[data-panel="group"]');
    const groupInput = document.getElementById("group-file-input");
    const groupDesc = document.getElementById("group-desc-container");
    const formGroup = document.getElementById("upload-form-group");
    const uploadGroupStatus = document.getElementById("upload-group-status");

    function activateSingle() {
        if (tabSingle) {
            tabSingle.className = "flex-1 py-2 text-xs font-semibold rounded-md bg-white text-gray-900 shadow-sm border border-gray-100";
        }
        if (tabGroup) {
            tabGroup.className = "flex-1 py-2 text-xs font-semibold rounded-md text-gray-500 hover:text-gray-800";
        }
        if (panelSingle) panelSingle.classList.remove("hidden");
        if (panelGroup) panelGroup.classList.add("hidden");
    }

    function activateGroup() {
        if (tabGroup) {
            tabGroup.className = "flex-1 py-2 text-xs font-semibold rounded-md bg-white text-gray-900 shadow-sm border border-gray-100";
        }
        if (tabSingle) {
            tabSingle.className = "flex-1 py-2 text-xs font-semibold rounded-md text-gray-500 hover:text-gray-800";
        }
        if (panelGroup) panelGroup.classList.remove("hidden");
        if (panelSingle) panelSingle.classList.add("hidden");
    }

    if (tabSingle) tabSingle.addEventListener("click", activateSingle);
    if (tabGroup) tabGroup.addEventListener("click", activateGroup);

    function rebuildGroupDescFields(files) {
        if (!groupDesc) return;
        groupDesc.innerHTML = "";
        if (!files || !files.length) return;
        Array.from(files).forEach((file) => {
            const wrap = document.createElement("div");
            wrap.className = "rounded-lg border border-gray-200 bg-gray-50/50 p-2";
            const lab = document.createElement("label");
            lab.className = "block text-[10px] font-semibold text-gray-500 mb-1 truncate";
            lab.textContent = "Descrição — " + file.name;
            const ta = document.createElement("textarea");
            ta.className = "group-file-desc w-full rounded-md border border-gray-200 bg-white px-2 py-1.5 text-xs outline-none focus:border-cyan-500 resize-y min-h-[48px] font-[inherit]";
            ta.rows = 2;
            ta.placeholder = "O que esta imagem ou GIF mostra (a IA usa na resposta)";
            wrap.appendChild(lab);
            wrap.appendChild(ta);
            groupDesc.appendChild(wrap);
        });
    }

    if (groupInput) {
        groupInput.addEventListener("change", (e) => {
            rebuildGroupDescFields(e.target.files);
        });
    }

    if (formGroup) {
        formGroup.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (!uploadGroupStatus) return;
            uploadGroupStatus.textContent = "";
            uploadGroupStatus.classList.remove("error");

            const gInput = document.getElementById("group-file-input");
            const files = gInput && gInput.files ? gInput.files : null;
            if (!files || !files.length) {
                uploadGroupStatus.textContent = "Selecione pelo menos uma imagem ou GIF.";
                uploadGroupStatus.classList.add("error");
                return;
            }

            const title = (document.getElementById("group-title") && document.getElementById("group-title").value) || "";
            const tags = (document.getElementById("group-tags") && document.getElementById("group-tags").value) || "";
            const descEls = document.querySelectorAll("#group-desc-container .group-file-desc");
            const descriptions = Array.from(descEls).map((el) => el.value || "");

            const fd = new FormData();
            Array.from(files).forEach((f) => fd.append("files", f));
            fd.append("title", title);
            fd.append("tags", tags);
            fd.append("descriptions_json", JSON.stringify(descriptions));

            uploadGroupStatus.textContent = "Enviando...";
            try {
                const headers = getAuthHeadersFormData();
                const res = await fetch("/admin/files/upload-group", {
                    method: "POST",
                    headers: headers,
                    body: fd,
                });
                if (!res.ok) {
                    if (res.status === 401) {
                        window.location.href = "/login";
                        return;
                    }
                    const err = await res.text();
                    uploadGroupStatus.textContent = "Erro: " + (err || res.statusText);
                    uploadGroupStatus.classList.add("error");
                    return;
                }
                await res.json();
                uploadGroupStatus.textContent = "Grupo adicionado com sucesso.";
                formGroup.reset();
                if (groupDesc) groupDesc.innerHTML = "";
                await Promise.all([loadFiles(), loadFileStats()]);
                setTimeout(() => { uploadGroupStatus.textContent = ""; }, 2500);
            } catch (err) {
                console.error(err);
                uploadGroupStatus.textContent = "Erro ao enviar: " + (err.message || "falha");
                uploadGroupStatus.classList.add("error");
            }
        });
    }
}

// DRAG AND DROP FUNCTIONALITY
function syncSingleUploadAccept() {
    const sel = document.getElementById("file-type");
    const fi = document.getElementById("file-input");
    if (!sel || !fi) return;
    const v = sel.value;
    if (v === "pdf") fi.accept = ".pdf,application/pdf";
    else if (v === "gif") fi.accept = ".gif,image/gif";
    else fi.accept = ".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp";
}

function setupDragAndDrop() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview');
    const filePreviewName = filePreview.querySelector('.file-preview-name');
    const filePreviewSize = filePreview.querySelector('.file-preview-size');
    const dropZoneContent = dropZone.querySelector('.drop-zone-content');
    const fileTypeSelect = document.getElementById('file-type');

    if (!dropZone || !fileInput) return;

    syncSingleUploadAccept();
    if (fileTypeSelect) {
        fileTypeSelect.addEventListener('change', () => {
            syncSingleUploadAccept();
            fileInput.value = '';
            if (filePreview) filePreview.style.display = 'none';
            if (dropZoneContent) dropZoneContent.style.display = 'flex';
        });
    }

    // Click to select file — only when no file is selected yet
    dropZone.addEventListener('click', (e) => {
        if (e.target.closest('.file-preview') || e.target.closest('.file-preview-remove')) return;
        if (filePreview && filePreview.style.display !== 'none') return;
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
        const ext = file.name.split('.').pop().toLowerCase();
        const selectedType = document.getElementById('file-type')?.value || 'gif';
        let ok = false;
        if (selectedType === 'pdf' && ext === 'pdf') ok = true;
        if (selectedType === 'gif' && ext === 'gif') ok = true;
        if (selectedType === 'image' && ['png', 'jpg', 'jpeg', 'webp'].includes(ext)) ok = true;
        if (!ok) {
            alert('O arquivo não corresponde ao tipo selecionado (PDF, GIF ou imagem PNG/JPG/WebP).');
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

        if (fileTypeSelect && ext === 'pdf') {
            fileTypeSelect.value = 'pdf';
            syncSingleUploadAccept();
        } else if (fileTypeSelect && ext === 'gif') {
            fileTypeSelect.value = 'gif';
            syncSingleUploadAccept();
        } else if (fileTypeSelect && ['png', 'jpg', 'jpeg', 'webp'].includes(ext)) {
            fileTypeSelect.value = 'image';
            syncSingleUploadAccept();
        }
    }

    window.clearFileInput = function(e) {
        if (e) { e.stopPropagation(); e.preventDefault(); }
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
        setupResourceUploadPanels();
        setupDragAndDrop();
        setupBackupButton();
        setupLogout();
        init();
    });
} else {
    setupResourceUploadPanels();
    setupDragAndDrop();
    setupBackupButton();
    setupLogout();
    init();
}

function setupLogout() {
    var btn = document.getElementById('btn-logout');
    if (!btn) return;
    btn.addEventListener('click', function () {
        var t = getAuthToken();
        fetch('/auth/logout', { method: 'POST', headers: { 'Authorization': 'Bearer ' + (t || '') } })
            .finally(function () {
                document.cookie = 'admin_token=; Max-Age=0; path=/';
                localStorage.removeItem('admin_token');
                window.location.href = '/login';
            });
    });
}