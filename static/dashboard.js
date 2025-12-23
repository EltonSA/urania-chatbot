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

async function loadStats(){
  const token = getAuthToken();
  if (!token) {
    console.log("Sem token, redirecionando para login");
    window.location.href = '/login';
    return;
  }

  try {
    const res = await fetch("/admin/stats", {
      headers: getAuthHeaders()
    });
    
    if (!res.ok) {
      if (res.status === 401) {
        console.log("Token inválido, redirecionando para login");
        window.location.href = '/login';
        return;
      }
      console.error("Erro ao carregar estatísticas:", res.status);
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

    // Perguntas mais frequentes - categorizadas
    const questionsList = document.getElementById("top_questions");
    const questionsEmpty = document.getElementById("questions_empty");
    if(questionsList){
      try {
        const questions = data.top_questions || [];
        
        // Só atualiza se houver dados válidos
        if(Array.isArray(questions) && questions.length > 0){
          questionsList.innerHTML = "";
          if(questionsEmpty) questionsEmpty.style.display = "none";
          
          questions.forEach((item, index) => {
            try {
              const card = document.createElement("div");
              card.className = "modern-card question-card";
              
              const rank = document.createElement("div");
              rank.className = "rank-badge";
              rank.textContent = `#${index + 1}`;
              
              const content = document.createElement("div");
              content.className = "card-content";
              
              const category = document.createElement("div");
              category.className = "question-text";
              category.textContent = item.category || item.question || "Sem categoria";
              
              // Mostra exemplos se existirem
              if(item.examples && Array.isArray(item.examples) && item.examples.length > 0 && item.examples[0] !== item.category){
                const examples = document.createElement("div");
                examples.className = "question-examples";
                examples.textContent = `Ex: ${item.examples.slice(0, 2).join(", ")}`;
                content.appendChild(examples);
              }
              
              const count = document.createElement("div");
              count.className = "question-count";
              count.innerHTML = `<span class="count-number">${item.count || 0}</span> <span class="count-label">vezes</span>`;
              
              content.appendChild(category);
              content.appendChild(count);
              
              card.appendChild(rank);
              card.appendChild(content);
              questionsList.appendChild(card);
            } catch(itemErr) {
              console.error("Erro ao renderizar item de pergunta:", itemErr, item);
            }
          });
        } else {
          // Só mostra empty state se realmente não houver dados
          if(questions.length === 0){
            questionsList.innerHTML = "";
            if(questionsEmpty) questionsEmpty.style.display = "flex";
          }
          // Se questions não for array válido, mantém o conteúdo atual
        }
      } catch(err) {
        console.error("Erro ao processar perguntas:", err);
        // Não limpa o conteúdo em caso de erro
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
            typeBadge.innerHTML = '<span class="badge-icon">📄</span><span class="badge-text">PDF</span>';
          } else if(fileType === "gif"){
            typeBadge.classList.add("badge-gif");
            typeBadge.innerHTML = '<span class="badge-icon">🎬</span><span class="badge-text">GIF</span>';
          } else {
            typeBadge.classList.add("badge-unknown");
            typeBadge.innerHTML = '<span class="badge-icon">📎</span><span class="badge-text">FILE</span>';
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
            viewBtn.innerHTML = '<span class="btn-icon">👁️</span><span class="btn-text">Ver</span>';
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
  } catch (err) {
    console.error("Erro ao carregar estatísticas:", err);
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
  loadStats();
  setInterval(loadStats, 8000);
  
  // Adiciona evento ao botão de exportar
  const exportBtn = document.getElementById("export-excel-btn");
  if (exportBtn) {
    exportBtn.addEventListener("click", (e) => {
      e.preventDefault();
      exportExcel();
    });
  }
}
