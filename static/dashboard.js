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
/** Se o utilizador clica em «Aplicar» durante um carregamento, agenda um novo pedido (evita ignorar o filtro em silêncio). */
let loadStatsQueued = false;
let dashDateDebounceTimer = null;

function scheduleNextLoad() {
  if (loadStatsTimeout) {
    clearTimeout(loadStatsTimeout);
  }
  loadStatsTimeout = setTimeout(() => {
    loadStats(false);
  }, 10000);
}

function getDashboardDateQuery() {
  const dfEl = document.getElementById("dash-date-from");
  const dtEl = document.getElementById("dash-date-to");
  const fromVal = dfEl && dfEl.value ? String(dfEl.value).trim() : "";
  const toVal = dtEl && dtEl.value ? String(dtEl.value).trim() : "";
  const params = new URLSearchParams();
  if (fromVal) params.set("date_from", fromVal);
  if (toVal) params.set("date_to", toVal);
  const s = params.toString();
  return s ? ("?" + s) : "";
}

function showDashFilterError(message) {
  const el = document.getElementById("dash-filter-error");
  if (!el) return;
  if (message) {
    el.textContent = message;
    el.classList.remove("hidden");
  } else {
    el.textContent = "";
    el.classList.add("hidden");
  }
}

function updateDashboardPeriodHint(data) {
  const el = document.getElementById("dashboard-period-hint");
  if (!el || !data) return;
  if (data.filtered && data.date_from != null && data.date_to != null) {
    el.textContent = "Período aplicado: " + data.date_from + " a " + data.date_to + " (UTC)";
    el.classList.remove("text-gray-500");
    el.classList.add("text-brand-700");
  } else {
    el.textContent = "Período: todo o histórico";
    el.classList.add("text-gray-500");
    el.classList.remove("text-brand-700");
  }
}

async function loadStats(showLoading = true){
  // Evita pedidos em paralelo; pedidos manuais (Aplicar / limpar filtro) ficam em fila em vez de serem ignorados.
  if (isLoading) {
    if (showLoading) {
      loadStatsQueued = true;
    }
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
    const dfEl = document.getElementById("dash-date-from");
    const dtEl = document.getElementById("dash-date-to");
    let fromVal = dfEl && dfEl.value ? String(dfEl.value).trim() : "";
    let toVal = dtEl && dtEl.value ? String(dtEl.value).trim() : "";
    if (fromVal && !toVal && dtEl) {
      dtEl.value = fromVal;
      toVal = fromVal;
    } else if (!fromVal && toVal && dfEl) {
      dfEl.value = toVal;
      fromVal = toVal;
    }
    if (fromVal && toVal && fromVal > toVal) {
      showDashFilterError("A data inicial não pode ser posterior à data final.");
      return;
    }

    const startTime = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
    const statsUrl = "/admin/stats" + getDashboardDateQuery();
    const res = await fetch(statsUrl, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });
    
    if (!res.ok) {
      if (res.status === 401) {
        console.log("Token inválido, redirecionando para login");
        window.location.href = '/login';
        return;
      }
      if (res.status === 400) {
        let detail = "Intervalo de datas inválido.";
        try {
          const errBody = await res.json();
          if (errBody && errBody.detail) {
            detail = typeof errBody.detail === "string" ? errBody.detail : detail;
          }
        } catch (_) { /* ignore */ }
        showDashFilterError(detail);
        return;
      }
      console.error("Erro ao carregar estatísticas:", res.status);
      showDashFilterError("Não foi possível carregar as estatísticas.");
      return;
    }
    
    const data = await res.json();
    showDashFilterError("");
    updateDashboardPeriodHint(data);

    const mTotal = document.getElementById("m_total");
    const mChats = document.getElementById("m_chats");
    const mPdfs = document.getElementById("m_pdfs");
    const mGifs = document.getElementById("m_gifs");
    const mImages = document.getElementById("m_images");
    const mResolvedYes = document.getElementById("m_resolved_yes");
    const mResolvedNo = document.getElementById("m_resolved_no");
    const mDetractors = document.getElementById("m_detractors");
    const mSupport = document.getElementById("m_support");
    
    if(mTotal) mTotal.textContent = data.total_messages ?? 0;
    if(mChats) mChats.textContent = data.chats_initiated ?? 0;
    if(mPdfs) mPdfs.textContent = data.pdfs_sent ?? 0;
    if(mGifs) mGifs.textContent = data.gifs_sent ?? 0;
    if(mImages) mImages.textContent = data.images_sent ?? 0;
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

    // Arquivos — feedback Sim / Não (por último envio na sessão)
    const filesList = document.getElementById("files_not_resolved");
    const filesEmpty = document.getElementById("files_empty");
    if(filesList){
      filesList.innerHTML = "";
      const files = data.files_feedback_stats || data.files_not_resolved || [];
      
      if(files.length === 0){
        if(filesEmpty) filesEmpty.style.display = "flex";
      } else {
        if(filesEmpty) filesEmpty.style.display = "none";
        files.forEach(item => {
          const fileType = String(item.file_type || "").toLowerCase().trim();
          const titleText = String(item.title || item.original_name || "Sem título").trim();
          const nYes = item.clicks_yes != null ? Number(item.clicks_yes) : 0;
          const nNo = item.clicks_no != null ? Number(item.clicks_no) : Number(item.count || 0);
          const nTotal = item.clicks_total != null ? Number(item.clicks_total) : (nYes + nNo);
          
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
          } else if(fileType === "image"){
            typeBadge.classList.add("badge-image");
            typeBadge.innerHTML = '<span class="badge-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg></span><span class="badge-text">IMG</span>';
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
          meta.className = "file-meta space-y-1";
          const line1 = document.createElement("div");
          line1.className = "flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-gray-600";
          const spanY = document.createElement("span");
          const lblY = document.createElement("span");
          lblY.className = "text-gray-400 font-medium";
          lblY.textContent = "Resolveu (Sim): ";
          const numY = document.createElement("strong");
          numY.className = "text-emerald-700 tabular-nums";
          numY.textContent = String(nYes);
          spanY.appendChild(lblY);
          spanY.appendChild(numY);
          const spanN = document.createElement("span");
          const lblN = document.createElement("span");
          lblN.className = "text-gray-400 font-medium";
          lblN.textContent = "Resolveu (Não): ";
          const numN = document.createElement("strong");
          numN.className = "text-rose-700 tabular-nums";
          numN.textContent = String(nNo);
          spanN.appendChild(lblN);
          spanN.appendChild(numN);
          line1.appendChild(spanY);
          line1.appendChild(spanN);
          const line2 = document.createElement("div");
          line2.className = "text-[10px] text-gray-400";
          line2.textContent = "Total de respostas no cartão ligadas a este arquivo (no período): " + nTotal;
          meta.appendChild(line1);
          meta.appendChild(line2);
          
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
              } else if(fileType === "gif" || fileType === "image"){
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
              } else {
                window.open(item.url, "_blank");
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
    showDashFilterError("Erro de rede ao carregar estatísticas.");
  } finally {
    isLoading = false;
    if (loadingOverlay) {
      loadingOverlay.style.display = "none";
    }
    if (loadStatsQueued) {
      loadStatsQueued = false;
      loadStats(true);
    } else if (getAuthToken()) {
      scheduleNextLoad();
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

  const dfEl = document.getElementById("dash-date-from");
  const dtEl = document.getElementById("dash-date-to");
  let fromVal = dfEl && dfEl.value ? String(dfEl.value).trim() : "";
  let toVal = dtEl && dtEl.value ? String(dtEl.value).trim() : "";
  if (fromVal && !toVal && dtEl) {
    dtEl.value = fromVal;
    toVal = fromVal;
  } else if (!fromVal && toVal && dfEl) {
    dfEl.value = toVal;
    fromVal = toVal;
  }
  if (fromVal && toVal && fromVal > toVal) {
    alert("A data inicial não pode ser posterior à data final.");
    return;
  }

  try {
    const response = await fetch("/admin/export.xlsx" + getDashboardDateQuery(), {
      method: "GET",
      headers: getAuthHeaders(),
      cache: "no-store",
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
  // Primeira carga; o próximo poll de 10s é agendado no finally de loadStats
  loadStats(true);
  
  // Adiciona evento ao botão de exportar
  const exportBtn = document.getElementById("export-excel-btn");
  if (exportBtn) {
    exportBtn.addEventListener("click", (e) => {
      e.preventDefault();
      exportExcel();
    });
  }

  const dashApply = document.getElementById("dash-apply-filter");
  if (dashApply) {
    dashApply.addEventListener("click", () => loadStats(true));
  }
  const dashClear = document.getElementById("dash-clear-filter");
  if (dashClear) {
    dashClear.addEventListener("click", () => {
      const df = document.getElementById("dash-date-from");
      const dt = document.getElementById("dash-date-to");
      if (df) df.value = "";
      if (dt) dt.value = "";
      showDashFilterError("");
      loadStats(true);
    });
  }

  function scheduleDashboardDateReload() {
    if (dashDateDebounceTimer) {
      clearTimeout(dashDateDebounceTimer);
    }
    dashDateDebounceTimer = setTimeout(() => {
      dashDateDebounceTimer = null;
      loadStats(true);
    }, 400);
  }
  ["dash-date-from", "dash-date-to"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("change", scheduleDashboardDateReload);
    }
  });
  
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
