/**
 * Aplica nome do sistema, versão, favicon e imagens vindos de GET /branding (público).
 * [data-brand-logo] = logo painel/login; [data-chat-avatar] = avatar no widget de chat.
 * [data-brand-version] = rótulo da versão (ex.: v1.0.0 ou hash Git).
 */
(function () {
  function formatVersion(v) {
    if (v == null || String(v).trim() === '') return '';
    var s = String(v).trim();
    // SHA Git (hex) — sem prefixo "v"
    if (/^[0-9a-f]{7,40}$/i.test(s)) return s;
    // describe / build metadata (1.0.0+abc, v1.0.0-3-gxxxx)
    if (/[+]/.test(s) || /-g[0-9a-f]+$/i.test(s)) return s;
    if (/^v/i.test(s)) return s;
    if (/^\d+\.\d+/.test(s)) return 'v' + s;
    return s;
  }

  function apply(b) {
    if (!b) return;
    var verLabel = formatVersion(b.version);
    if (verLabel) {
      document.querySelectorAll('[data-brand-version]').forEach(function (el) {
        el.textContent = verLabel;
      });
    }
    if (b.logo_url) {
      document.querySelectorAll('[data-brand-logo]').forEach(function (el) {
        el.src = b.logo_url;
      });
    }
    if (b.chat_avatar_url) {
      document.querySelectorAll('[data-chat-avatar]').forEach(function (el) {
        el.src = b.chat_avatar_url;
      });
    }
    if (typeof b.display_name !== 'string') return;
    var meta = document.querySelector('meta[name="page-title-part"]');
    var pagePart = meta && meta.content ? String(meta.content).trim() : '';
    if (pagePart) {
      document.title = pagePart + ' — ' + b.display_name;
    } else {
      var t = document.title;
      var idx = t.lastIndexOf(' - ');
      if (idx > 0) {
        document.title = t.slice(0, idx).trim() + ' — ' + b.display_name;
      } else {
        document.title = t ? t + ' — ' + b.display_name : b.display_name;
      }
    }
    if (b.favicon_url) {
      var links = document.querySelectorAll('link[rel="icon"], link[rel="shortcut icon"]');
      for (var i = 0; i < links.length; i++) links[i].href = b.favicon_url;
    }
    document.querySelectorAll('[data-brand-name]').forEach(function (el) {
      el.textContent = b.display_name;
    });
    document.querySelectorAll('[data-brand-logo-alt]').forEach(function (el) {
      el.setAttribute('alt', b.display_name);
    });
  }
  fetch('/branding')
    .then(function (r) {
      return r.json();
    })
    .then(apply)
    .catch(function () {});
})();
