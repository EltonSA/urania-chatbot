// Desabilita console.log em produção (mantém apenas console.error)
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
if (isProduction) {
    console.log = function() {}; // Remove logs em produção
    console.debug = function() {}; // Remove debug em produção
}

// AUTENTICAÇÃO
function getAuthToken() {
    return localStorage.getItem('admin_token');
}

function getAuthHeaders() {
    const token = getAuthToken();
    if (!token) {
        console.error("Token não encontrado!");
        return {};
    }
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

let isLoading = false;
let loadStatsTimeout = null;

async function loadStats(showLoading = true){
  // Evita múltiplas requisições simultâneas
  if (isLoading) {
    return;
  }
  
  const token = getAuthToken();
  if (!token) {
    console.log("Sem token, redirecionando para login");
    window.location.href = '/login';
    return;
  }

  isLoading = true;
  const loadingOverlay = document.getElementById("loading-overlay");
  if (showLoading && loadingOverlay) {
    loadingOverlay.style.display = "flex";
  }

  try {
    const startTime = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
    const res = await fetch("/admin/stats", {
      headers: getAuthHeaders(),
      cache: 'no-cache' // Evita cache do navegador
    });
    
    if (!res.ok) {
      if (res.status === 401) {
        console.log("Token inválido, redirecionando para login");
        isLoading = false;
        if (loadingOverlay) loadingOverlay.style.display = "none";
        window.location.href = '/login';
        return;
      }
      console.error("Erro ao carregar estatísticas:", res.status);
      isLoading = false;
      if (loadingOverlay) loadingOverlay.style.display = "none";
      return;
    }
    
    const data = await res.json();

    const mTotal = document.getElementById("m_total");
    const mChats = document.getElementById("m_chats");
    const mPdfs = document.getElementById("m_pdfs");
    const mGifs = document.getElementById("m_gifs");
    const mResolvedYes = document.getElementById("m_resolved_yes");
    const mResolvedNo = document.getElementById("m_resolved_no");
    const mDetractors = document.getElementById("m_detractors");
    const mSupport = document.getElementById("m_support");
    
    if(mTotal) mTotal.textContent = data.total_messages ?? 0;
    if(mChats) mChats.textContent = data.chats_initiated ?? 0;
    if(mPdfs) mPdfs.textContent = data.pdfs_sent ?? 0;
    if(mGifs) mGifs.textContent = data.gifs_sent ?? 0;
    if(mResolvedYes) mResolvedYes.textContent = data.resolved_yes ?? 0;
    if(mResolvedNo) mResolvedNo.textContent = data.resolved_no ?? 0;
    if(mDetractors) mDetractors.textContent = data.detractors ?? 0;
    if(mSupport) mSupport.textContent = data.support_redirected ?? 0;

    const rate = Number(data.resolution_rate ?? 0);
    const resolutionEl = document.getElementById("m_resolution");
    const barResolutionEl = document.getElementById("bar_resolution");
    if(resolutionEl) resolutionEl.textContent = rate.toFixed(1);
    if(barResolutionEl) barResolutionEl.style.width = Math.max(0, Math.min(100, rate)) + "%";

    // Métricas OpenAI
    const mOpenaiTotal = document.getElementById("m_openai_total");
    const mOpenaiErrors = document.getElementById("m_openai_errors");
    const mOpenaiErrorRate = document.getElementById("m_openai_error_rate");
    const barOpenaiError = document.getElementById("bar_openai_error");
    
    if(mOpenaiTotal) mOpenaiTotal.textContent = data.openai_requests_total ?? 0;
    if(mOpenaiErrors) mOpenaiErrors.textContent = data.openai_requests_error ?? 0;
    
    const openaiErrorRate = Number(data.openai_error_rate ?? 0);
    if(mOpenaiErrorRate) mOpenaiErrorRate.textContent = openaiErrorRate.toFixed(2);
    if(barOpenaiError) {
      barOpenaiError.style.width = Math.max(0, Math.min(100, openaiErrorRate)) + "%";
      // Adiciona classe de cor baseada na taxa de erro
      barOpenaiError.className = "barfill";
      if(openaiErrorRate > 10) {
        barOpenaiError.style.background = "#ef4444"; // Vermelho para taxa alta
      } else if(openaiErrorRate > 5) {
        barOpenaiError.style.background = "#f59e0b"; // Laranja para taxa média
      } else {
        barOpenaiError.style.background = "#10b981"; // Verde para taxa baixa
      }
    }

    // Arquivos que não resolveram - novo design
    const filesList = document.getElementById("files_not_resolved");
    const filesEmpty = document.getElementById("files_empty");
    if(filesList){
      filesList.innerHTML = "";
      const files = data.files_not_resolved || [];
      
      if(files.length === 0){
        if(filesEmpty) filesEmpty.style.display = "flex";
      } else {
        if(filesEmpty) filesEmpty.style.display = "none";
        files.forEach(item => {
          const fileType = String(item.file_type || "").toLowerCase().trim();
          const titleText = String(item.title || item.original_name || "Sem título").trim();
          
          const card = document.createElement("div");
          card.className = "modern-card file-card";
          
          const leftSection = document.createElement("div");
          leftSection.className = "file-card-left";
          
          const typeBadge = document.createElement("div");
          typeBadge.className = "file-type-badge-large";
          if(fileType === "pdf"){
            typeBadge.classList.add("badge-pdf");
            typeBadge.innerHTML = '<span class="badge-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg></span><span class="badge-text">PDF</span>';
          } else if(fileType === "gif"){
            typeBadge.classList.add("badge-gif");
            typeBadge.innerHTML = '<span class="badge-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg></span><span class="badge-text">GIF</span>';
          } else {
            typeBadge.classList.add("badge-unknown");
            typeBadge.innerHTML = '<span class="badge-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg></span><span class="badge-text">FILE</span>';
          }
          
          const fileInfo = document.createElement("div");
          fileInfo.className = "file-info";
          
          const title = document.createElement("div");
          title.className = "file-title";
          title.textContent = titleText;
          
          const meta = document.createElement("div");
          meta.className = "file-meta";
          meta.innerHTML = `<span class="count-badge">${item.count || 0} "Não"</span>`;
          
          fileInfo.appendChild(title);
          fileInfo.appendChild(meta);
          
          leftSection.appendChild(typeBadge);
          leftSection.appendChild(fileInfo);
          
          const rightSection = document.createElement("div");
          rightSection.className = "file-card-right";
          
          if(item.url){
            const viewBtn = document.createElement("button");
            viewBtn.className = "btn-view-file-modern";
            viewBtn.innerHTML = '<span class="btn-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg></span><span class="btn-text">Abrir</span>';
            viewBtn.onclick = () => {
              if(fileType === "pdf"){
                window.open(item.url, "_blank");
              } else if(fileType === "gif"){
                const modal = document.createElement("div");
                modal.className = "file-modal-overlay";
                modal.onclick = (e) => {
                  if(e.target === modal) modal.remove();
                };
                const modalContent = document.createElement("div");
                modalContent.className = "file-modal-content";
                modalContent.onclick = (e) => e.stopPropagation();
                const closeBtn = document.createElement("button");
                closeBtn.className = "file-modal-close";
                closeBtn.textContent = "×";
                closeBtn.onclick = () => modal.remove();
                const img = document.createElement("img");
                img.src = item.url;
                img.style.maxWidth = "100%";
                img.style.maxHeight = "80vh";
                modalContent.appendChild(closeBtn);
                modalContent.appendChild(img);
                modal.appendChild(modalContent);
                document.body.appendChild(modal);
              }
            };
            rightSection.appendChild(viewBtn);
          }
          
          card.appendChild(leftSection);
          card.appendChild(rightSection);
          filesList.appendChild(card);
        });
      }
    }
    
    if (typeof performance !== 'undefined' && performance.now) {
      const loadTime = performance.now() - startTime;
      if (loadTime > 1000) {
        console.log(`Stats carregadas em ${loadTime.toFixed(0)}ms`);
      }
    }
  } catch (err) {
    console.error("Erro ao carregar estatísticas:", err);
  } finally {
    isLoading = false;
    if (loadingOverlay) {
      loadingOverlay.style.display = "none";
    }
  }
}

// Função para exportar Excel
async function exportExcel() {
  const token = getAuthToken();
  if (!token) {
    alert("Você precisa estar autenticado para exportar os dados.");
    window.location.href = '/login';
    return;
  }

  try {
    const response = await fetch("/admin/export.xlsx", {
      method: "GET",
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      if (response.status === 401) {
        alert("Sessão expirada. Por favor, faça login novamente.");
        window.location.href = '/login';
        return;
      }
      throw new Error(`Erro ao exportar: ${response.status}`);
    }

    // Obtém o blob do arquivo
    const blob = await response.blob();
    
    // Cria um link temporário para download
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "dashboard.xlsx";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Erro ao exportar Excel:", err);
    alert("Erro ao exportar os dados. Tente novamente.");
  }
}

// Verifica autenticação antes de carregar
const authToken = getAuthToken();
if (!authToken) {
  window.location.href = '/login';
} else {
  // Carrega imediatamente na primeira vez
  loadStats(true);
  
  // Atualiza a cada 10 segundos (aumentado de 8s para reduzir carga)
  // Usa timeout em vez de setInterval para evitar sobreposição
  function scheduleNextLoad() {
    if (loadStatsTimeout) {
      clearTimeout(loadStatsTimeout);
    }
    loadStatsTimeout = setTimeout(() => {
      loadStats(false); // Não mostra loading nas atualizações automáticas
      scheduleNextLoad();
    }, 10000);
  }
  scheduleNextLoad();
  
  // Adiciona evento ao botão de exportar
  const exportBtn = document.getElementById("export-excel-btn");
  if (exportBtn) {
    exportBtn.addEventListener("click", (e) => {
      e.preventDefault();
      exportExcel();
    });
  }
  
  // Logout
  const logoutBtn = document.getElementById("btn-logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      fetch('/auth/logout', { method: 'POST', headers: getAuthHeaders() })
        .finally(() => {
          document.cookie = 'admin_token=; Max-Age=0; path=/';
          localStorage.removeItem('admin_token');
          window.location.href = '/login';
        });
    });
  }

  // Limpa timeout quando a página é fechada
  window.addEventListener("beforeunload", () => {
    if (loadStatsTimeout) {
      clearTimeout(loadStatsTimeout);
    }
  });
}
