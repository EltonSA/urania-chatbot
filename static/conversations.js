(function () {
  const state = {
    page: 1,
    limit: 25,
    totalPages: 1,
    selectedSessionId: null,
    satisfaction: "all",
  };

  function hasConvDateFilter() {
    var df = document.getElementById("conv-date-from");
    var dt = document.getElementById("conv-date-to");
    var a = df && df.value ? String(df.value).trim() : "";
    var b = dt && dt.value ? String(dt.value).trim() : "";
    return !!(a || b);
  }

  function buildConversationsListUrl() {
    var p = new URLSearchParams();
    p.set("page", String(state.page));
    p.set("limit", String(state.limit));
    p.set("satisfaction", state.satisfaction || "all");
    var df = document.getElementById("conv-date-from");
    var dt = document.getElementById("conv-date-to");
    var fromVal = df && df.value ? String(df.value).trim() : "";
    var toVal = dt && dt.value ? String(dt.value).trim() : "";
    if (fromVal) p.set("date_from", fromVal);
    if (toVal) p.set("date_to", toVal);
    return "/admin/conversations/?" + p.toString();
  }

  function updateConvPeriodHint(data) {
    var el = document.getElementById("conv-period-hint");
    if (!el || !data) return;
    if (data.filtered && data.date_from != null && data.date_to != null) {
      el.textContent =
        "Período aplicado: " +
        data.date_from +
        " a " +
        data.date_to +
        " (UTC) — só entram sessões com mensagem neste intervalo";
      el.classList.remove("text-gray-400");
      el.classList.add("text-brand-700");
    } else {
      el.textContent =
        "Período: todo o histórico · datas em UTC (como no dashboard)";
      el.classList.add("text-gray-400");
      el.classList.remove("text-brand-700");
    }
  }

  function resetDetailPanel() {
    state.selectedSessionId = null;
    var dp = document.getElementById("detail-panel");
    var de = document.getElementById("detail-empty");
    if (dp) dp.classList.add("hidden");
    if (de) de.classList.remove("hidden");
  }

  function getToken() {
    return localStorage.getItem("admin_token");
  }

  function getAuthHeaders() {
    const token = getToken();
    if (!token) return {};
    return {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
    };
  }

  function showError(msg) {
    const el = document.getElementById("conv-error");
    if (!el) return;
    el.textContent = msg;
    el.classList.toggle("hidden", !msg);
  }

  function formatDate(iso) {
    if (!iso) return "—";
    try {
      const d = new Date(iso);
      return d.toLocaleString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (e) {
      return iso;
    }
  }

  function resolvedLabel(v) {
    if (v === 1) return "Resolveu SIM";
    if (v === 0) return "Resolveu NÃO";
    return "Resolveu S/R";
  }

  async function fetchList() {
    showError("");
    const loading = document.getElementById("conv-list-loading");
    const list = document.getElementById("conv-list");
    const empty = document.getElementById("conv-list-empty");
    const headers = getAuthHeaders();
    if (!headers.Authorization) {
      window.location.href = "/login";
      return;
    }

    loading.classList.remove("hidden");
    list.classList.add("hidden");
    empty.classList.add("hidden");

    var df = document.getElementById("conv-date-from");
    var dt = document.getElementById("conv-date-to");
    var fromVal = df && df.value ? String(df.value).trim() : "";
    var toVal = dt && dt.value ? String(dt.value).trim() : "";
    if (fromVal && !toVal && dt) {
      dt.value = fromVal;
      toVal = fromVal;
    } else if (!fromVal && toVal && df) {
      df.value = toVal;
      fromVal = toVal;
    }
    if (fromVal && toVal && fromVal > toVal) {
      loading.classList.add("hidden");
      showError("A data inicial não pode ser posterior à data final.");
      return;
    }

    var url = buildConversationsListUrl();
    var res = await fetch(url, { headers });
    if (res.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (res.status === 400) {
      loading.classList.add("hidden");
      var detail = "Intervalo de datas inválido.";
      try {
        var errBody = await res.json();
        if (errBody && errBody.detail) {
          detail =
            typeof errBody.detail === "string" ? errBody.detail : detail;
        }
      } catch (e) {
        /* ignore */
      }
      showError(detail);
      return;
    }
    if (!res.ok) {
      loading.classList.add("hidden");
      showError("Não foi possível carregar a lista (" + res.status + ").");
      return;
    }

    var data = await res.json();
    showError("");
    updateConvPeriodHint(data);
    state.totalPages = data.pages || 1;
    const convs = data.conversations || [];

    loading.classList.add("hidden");

    document.getElementById("page-info").textContent =
      "Página " + state.page + " / " + state.totalPages;

    document.getElementById("btn-prev").disabled = state.page <= 1;
    document.getElementById("btn-next").disabled =
      state.page >= state.totalPages;

    if (convs.length === 0) {
      if (hasConvDateFilter()) {
        empty.textContent =
          "Nenhuma conversa com mensagens de usuário/IA neste período (UTC).";
      } else if (state.satisfaction === "all") {
        empty.textContent = "Nenhuma conversa com mensagens ainda.";
      } else {
        empty.textContent =
          "Nenhuma conversa corresponde a este filtro de satisfação.";
      }
      empty.classList.remove("hidden");
      return;
    }

    list.innerHTML = "";
    convs.forEach(function (c) {
      const li = document.createElement("li");
      const isSel = c.session_id === state.selectedSessionId;
      li.className =
        "px-4 py-3 cursor-pointer transition-colors hover:bg-brand-50/50 " +
        (isSel ? "bg-brand-50 border-l-4 border-brand-600" : "border-l-4 border-transparent");
      li.dataset.sessionId = c.session_id;

      const title = document.createElement("div");
      title.className = "text-sm font-medium text-gray-900 line-clamp-2";
      title.textContent = c.preview || "(sem texto)";

      const sub = document.createElement("div");
      sub.className = "text-[11px] text-gray-500 mt-1 flex flex-wrap gap-x-2 gap-y-0.5";
      sub.appendChild(
        document.createTextNode(formatDate(c.last_message_at || c.display_date))
      );
      sub.appendChild(document.createTextNode(" · "));
      sub.appendChild(
        document.createTextNode((c.message_count || 0) + " mensagens")
      );
      sub.appendChild(document.createTextNode(" · "));
      sub.appendChild(document.createTextNode(resolvedLabel(c.resolved)));

      li.appendChild(title);
      li.appendChild(sub);
      li.addEventListener("click", function () {
        state.selectedSessionId = c.session_id;
        fetchList();
        loadDetail(c.session_id);
      });
      list.appendChild(li);
    });

    list.classList.remove("hidden");
  }

  function renderAttachmentCard(att) {
    const box = document.createElement("div");
    box.className =
      "mt-2 rounded-lg border border-emerald-200/80 bg-white/90 px-2.5 py-2 text-xs shadow-sm";
    const kind = (att.type || "arquivo").toUpperCase();
    const line = document.createElement("div");
    line.className = "font-semibold text-emerald-900 flex flex-wrap items-center gap-2";
    const badge = document.createElement("span");
    badge.className =
      "inline-flex px-2 py-0.5 rounded-md text-[10px] uppercase tracking-wide bg-emerald-100 text-emerald-800";
    badge.textContent = kind === "IMAGE" ? "IMG" : kind;
    line.appendChild(badge);
    if (att.url) {
      const a = document.createElement("a");
      a.href = att.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.className = "text-brand-700 hover:underline font-medium break-all";
      a.textContent = att.title || "Abrir arquivo";
      line.appendChild(a);
    } else {
      const span = document.createElement("span");
      span.className = "text-gray-600 break-all";
      span.textContent = att.title || "Arquivo";
      line.appendChild(span);
    }
    box.appendChild(line);
    if (att.url && (att.type === "gif" || att.type === "image")) {
      const img = document.createElement("img");
      img.src = att.url;
      img.alt = att.title || "";
      img.className =
        "mt-2 max-h-40 w-auto max-w-full rounded-md border border-gray-200 object-contain cursor-zoom-in";
      img.loading = "lazy";
      img.addEventListener("click", function () {
        window.open(att.url, "_blank", "noopener,noreferrer");
      });
      box.appendChild(img);
    }
    return box;
  }

  function renderMessages(messages) {
    const wrap = document.getElementById("detail-messages");
    wrap.innerHTML = "";
    (messages || []).forEach(function (m) {
      const row = document.createElement("div");
      row.className =
        "rounded-xl px-3 py-2.5 text-sm whitespace-pre-wrap break-words " +
        (m.role === "user" ? "msg-user" : "msg-bot");
      const who = document.createElement("div");
      who.className = "text-[10px] font-bold uppercase tracking-wide opacity-70 mb-1";
      who.textContent =
        m.role === "user" ? "Usuário" : "Assistente (IA)";
      row.appendChild(who);
      const text = (m.content || "").trim();
      if (text) {
        const body = document.createElement("div");
        body.className = "leading-relaxed";
        body.textContent = m.content || "";
        row.appendChild(body);
      }
      const atts = m.attachments || [];
      if (atts.length > 0) {
        if (m.role === "assistant") {
          const sub = document.createElement("div");
          sub.className =
            "text-[10px] font-semibold text-emerald-800/90 uppercase tracking-wide mt-2 mb-1";
          sub.textContent = "Enviado ao usuário (mídia)";
          row.appendChild(sub);
        }
        atts.forEach(function (att) {
          row.appendChild(renderAttachmentCard(att));
        });
      }
      if (m.timestamp) {
        const ts = document.createElement("div");
        ts.className = "text-[10px] opacity-60 mt-1.5";
        ts.textContent = formatDate(m.timestamp);
        row.appendChild(ts);
      }
      wrap.appendChild(row);
    });
  }

  function renderTimeline(items) {
    const tb = document.getElementById("detail-timeline");
    tb.innerHTML = "";
    (items || []).forEach(function (ev) {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-gray-50/80";
      const td1 = document.createElement("td");
      td1.className = "px-3 py-2 whitespace-nowrap text-gray-500 align-top";
      td1.textContent = formatDate(ev.created_at);
      const td2 = document.createElement("td");
      td2.className = "px-3 py-2 font-medium text-gray-800 align-top";
      td2.textContent = ev.label || ev.event_type;
      const td3 = document.createElement("td");
      td3.className =
        "px-3 py-2 text-gray-600 align-top max-w-[280px] break-words";
      if (ev.media && ev.media.url) {
        const a = document.createElement("a");
        a.href = ev.media.url;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.className = "text-brand-700 font-medium hover:underline break-all";
        a.textContent =
          (ev.media.title || "Arquivo") +
          " (" +
          String(ev.media.type || "").toUpperCase() +
          ")";
        td3.appendChild(a);
        if (ev.media.type === "gif" || ev.media.type === "image") {
          const br = document.createElement("br");
          td3.appendChild(br);
          const im = document.createElement("img");
          im.src = ev.media.url;
          im.alt = "";
          im.className =
            "mt-1.5 max-h-16 rounded border border-gray-200 object-contain";
          im.loading = "lazy";
          td3.appendChild(im);
        }
      } else {
        td3.textContent = ev.content || "—";
      }
      tr.appendChild(td1);
      tr.appendChild(td2);
      tr.appendChild(td3);
      tb.appendChild(tr);
    });
  }

  async function loadDetail(sessionId) {
    showError("");
    const headers = getAuthHeaders();
    const detailEmpty = document.getElementById("detail-empty");
    const detailPanel = document.getElementById("detail-panel");

    detailEmpty.classList.add("hidden");
    detailPanel.classList.remove("hidden");

    document.getElementById("detail-session-id").textContent = sessionId;
    document.getElementById("detail-messages").innerHTML =
      '<div class="text-sm text-gray-500 py-4">Carregando…</div>';
    document.getElementById("detail-timeline").innerHTML = "";

    const url =
      "/admin/conversations/" +
      encodeURIComponent(sessionId) +
      "?include_timeline=true";
    const res = await fetch(url, { headers });
    if (res.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!res.ok) {
      document.getElementById("detail-messages").innerHTML =
        '<div class="text-sm text-red-600">Erro ao carregar esta conversa.</div>';
      return;
    }

    const data = await res.json();
    document.getElementById("detail-meta").textContent =
      "Início: " +
      formatDate(data.started_at) +
      " · Última atividade: " +
      formatDate(data.last_activity_at) +
      " · " +
      resolvedLabel(data.resolved);

    renderMessages(data.messages);
    renderTimeline(data.timeline || []);
  }

  async function downloadExport(kind) {
    const sid = state.selectedSessionId;
    if (!sid) return;
    const headers = getAuthHeaders();
    const path =
      kind === "pdf"
        ? "/admin/conversations/" +
          encodeURIComponent(sid) +
          "/export/pdf"
        : "/admin/conversations/" +
          encodeURIComponent(sid) +
          "/export/txt";
    const res = await fetch(path, { headers });
    if (res.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!res.ok) {
      let detail = "";
      try {
        const ct = (res.headers.get("content-type") || "").toLowerCase();
        if (ct.indexOf("application/json") !== -1) {
          const j = await res.json();
          if (typeof j.detail === "string") {
            detail = j.detail;
          } else if (j.detail != null) {
            detail = JSON.stringify(j.detail);
          }
        } else {
          const t = await res.text();
          if (t && t.length < 600) {
            detail = t.trim();
          }
        }
      } catch (e) {
        /* ignore */
      }
      showError(
        "Falha ao exportar (" +
          res.status +
          ")" +
          (detail ? ": " + detail : ".")
      );
      return;
    }
    const blob = await res.blob();
    const dispo = res.headers.get("Content-Disposition") || "";
    let fname = "conversa_" + sid.slice(0, 8) + (kind === "pdf" ? ".pdf" : ".txt");
    const m = /filename=([^;]+)/i.exec(dispo);
    if (m) fname = m[1].trim().replace(/"/g, "");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = fname;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  document.getElementById("btn-prev").addEventListener("click", function () {
    if (state.page > 1) {
      state.page--;
      fetchList();
    }
  });
  document.getElementById("btn-next").addEventListener("click", function () {
    if (state.page < state.totalPages) {
      state.page++;
      fetchList();
    }
  });

  document
    .getElementById("btn-export-txt")
    .addEventListener("click", function () {
      downloadExport("txt");
    });
  document
    .getElementById("btn-export-pdf")
    .addEventListener("click", function () {
      downloadExport("pdf");
    });

  const satSel = document.getElementById("conv-filter-satisfaction");
  if (satSel) {
    satSel.value = state.satisfaction;
    satSel.addEventListener("change", function () {
      state.satisfaction = satSel.value || "all";
      state.page = 1;
      resetDetailPanel();
      showError("");
      fetchList();
    });
  }

  var convApply = document.getElementById("conv-apply-dates");
  if (convApply) {
    convApply.addEventListener("click", function () {
      state.page = 1;
      resetDetailPanel();
      showError("");
      fetchList();
    });
  }
  var convClear = document.getElementById("conv-clear-dates");
  if (convClear) {
    convClear.addEventListener("click", function () {
      var df = document.getElementById("conv-date-from");
      var dt = document.getElementById("conv-date-to");
      if (df) df.value = "";
      if (dt) dt.value = "";
      state.page = 1;
      resetDetailPanel();
      showError("");
      fetchList();
    });
  }

  const logoutBtn = document.getElementById("btn-logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", function () {
      fetch("/auth/logout", { method: "POST", headers: getAuthHeaders() }).finally(
        function () {
          document.cookie = "admin_token=; Max-Age=0; path=/";
          localStorage.removeItem("admin_token");
          window.location.href = "/login";
        }
      );
    });
  }

  if (!getToken()) {
    window.location.href = "/login";
  } else {
    fetchList();
  }
})();
