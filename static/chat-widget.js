/**
 * Urânia + Chat Widget (Flutuante)
 *
 * Embute o /widget existente dentro de um iframe flutuante.
 *
 * Uso (mesmo domínio):
 *   <script src="/static/chat-widget.js"></script>
 *
 * Uso (domínio separado - ex: chat em iabeta.urania.com.br):
 *   <script>
 *     window.UraniaWidgetConfig = {
 *       apiUrl: 'https://iabeta.urania.com.br'
 *     };
 *   </script>
 *   <script src="https://iabeta.urania.com.br/static/chat-widget.js"></script>
 *
 * Configurações disponíveis (window.UraniaWidgetConfig):
 *   apiUrl        - URL base do serviço de chat (obrigatório se cross-domain)
 *   assistantName - Nome exibido no header (padrão: 'Urânia +')
 *   avatarUrl     - URL da imagem do avatar
 *   primaryColor  - Cor principal (padrão: '#1C8B3C')
 *   primaryDark   - Cor escura do gradiente (padrão: '#15803d')
 */
(function () {
  'use strict';

  if (window.__ucwLoaded) return;
  window.__ucwLoaded = true;

  // Não carregar na própria página /widget
  if (window.location.pathname === '/widget') return;

  /* ================================================================
     CONFIGURAÇÃO
     ================================================================ */
  var scriptTag =
    document.currentScript ||
    document.querySelector('script[src*="chat-widget"]');

  var DEFAULTS = {
    apiUrl: '',
    assistantName: 'Urânia +',
    avatarUrl:
      'https://i.postimg.cc/633Wxf2R/Whats-App-Image-2025-11-05-at-09-27-39.jpg',
    primaryColor: '#1C8B3C',
    primaryDark: '#15803d',
    zIndex: 99999,
    buttonSize: 62,
    windowWidth: 400,
    windowHeight: 580,
  };

  var C = {};
  (function loadCfg() {
    for (var k in DEFAULTS) C[k] = DEFAULTS[k];
    if (window.UraniaWidgetConfig) {
      for (var k2 in window.UraniaWidgetConfig) C[k2] = window.UraniaWidgetConfig[k2];
    }
    if (scriptTag) {
      var d = scriptTag.dataset;
      if (d.apiUrl) C.apiUrl = d.apiUrl;
      if (d.assistantName) C.assistantName = d.assistantName;
      if (d.avatarUrl) C.avatarUrl = d.avatarUrl;
      if (d.primaryColor) C.primaryColor = d.primaryColor;
      if (!C.apiUrl && scriptTag.src) {
        try {
          C.apiUrl = new URL(scriptTag.src).origin;
        } catch (_) {}
      }
    }
  })();

  var API = C.apiUrl || '';
  var WIDGET_URL = API ? (API.replace(/\/$/, '') + '/widget?embed=1') : '/widget?embed=1';
  var TRUSTED_ORIGIN = API ? (function () { try { return new URL(API).origin; } catch (_) { return window.location.origin; } })() : window.location.origin;

  /* ================================================================
     SESSION STORAGE (estado abrir/minimizar)
     ================================================================ */
  function sGet(k) { try { return sessionStorage.getItem(k); } catch (_) { return null; } }
  function sSet(k, v) { try { sessionStorage.setItem(k, v); } catch (_) { /* noop */ } }
  function sRem(k) { try { sessionStorage.removeItem(k); } catch (_) { /* noop */ } }

  /* ================================================================
     CSS
     ================================================================ */
  function injectCSS() {
    if (document.getElementById('ucw-css')) return;
    var s = document.createElement('style');
    s.id = 'ucw-css';
    s.textContent = [
      '#ucw-root,#ucw-root *,#ucw-root *::before,#ucw-root *::after{box-sizing:border-box!important;margin:0!important;padding:0!important;',
      'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Inter","Roboto",sans-serif!important;',
      '-webkit-font-smoothing:antialiased!important;border-style:none!important;line-height:1.5!important}',
      '#ucw-root img{display:block!important;max-width:100%!important;height:auto!important}',
      '#ucw-root button{cursor:pointer!important;appearance:none!important}',

      '#ucw-root{position:fixed;bottom:24px;right:24px;z-index:' + C.zIndex + '}',

      /* Botão flutuante */
      '.ucw-trigger{width:' + C.buttonSize + 'px;height:' + C.buttonSize + 'px;border-radius:50%;border:3px solid ' + C.primaryColor + '!important;cursor:pointer;',
      'background:#fff;overflow:hidden;',
      'color:#fff;display:flex;align-items:center;justify-content:center;position:relative;outline:none;padding:0!important;',
      'box-shadow:0 6px 24px rgba(28,139,60,.4),0 2px 8px rgba(0,0,0,.1);',
      'transition:all .3s cubic-bezier(.4,0,.2,1);animation:ucwBounce .6s cubic-bezier(.34,1.56,.64,1) both}',
      '.ucw-trigger:hover{transform:scale(1.1);box-shadow:0 8px 32px rgba(28,139,60,.5)}',
      '.ucw-trigger:active{transform:scale(.95)}',
      '.ucw-trigger svg{width:28px;height:28px;transition:all .3s}',
      '.ucw-trigger .ucw-ic-avatar{display:block;width:100%;height:100%;border-radius:50%;overflow:hidden}',
      '.ucw-trigger .ucw-ic-avatar img{width:100%!important;height:100%!important;object-fit:cover!important;display:block!important}',
      '.ucw-trigger .ucw-ic-x{display:none}',
      '.ucw-trigger.open{background:linear-gradient(135deg,' + C.primaryColor + ' 0%,' + C.primaryDark + ' 100%)!important;border-color:transparent!important}',
      '.ucw-trigger.open .ucw-ic-avatar{display:none}.ucw-trigger.open .ucw-ic-x{display:block}',
      '.ucw-trigger::before{content:"";position:absolute;inset:-4px;border-radius:50%;',
      'border:2px solid ' + C.primaryColor + ';opacity:0;animation:ucwPulse 2.5s ease-out infinite}',
      '.ucw-trigger.open::before{animation:none;opacity:0}',

      /* Badge */
      '.ucw-badge{position:absolute;top:-2px;right:-2px;min-width:18px;height:18px;padding:0 5px;',
      'background:#ef4444;border-radius:9px;border:2px solid #fff;font-size:10px;font-weight:700;',
      'color:#fff;display:none;align-items:center;justify-content:center;line-height:1}',
      '.ucw-badge.show{display:flex}',

      /* Janela do chat */
      '.ucw-win{position:absolute;bottom:' + (C.buttonSize + 16) + 'px;right:0;',
      'width:' + C.windowWidth + 'px;height:' + C.windowHeight + 'px;max-height:calc(100vh - 100px);',
      'background:#fff;border-radius:20px;display:flex;flex-direction:column;overflow:hidden;',
      'box-shadow:0 20px 60px rgba(0,0,0,.15),0 4px 16px rgba(0,0,0,.08);',
      'border:1px solid rgba(226,232,240,.6);',
      'opacity:0;transform:translateY(20px) scale(.95);pointer-events:none;',
      'transition:all .35s cubic-bezier(.4,0,.2,1)}',
      '.ucw-win.open{opacity:1;transform:translateY(0) scale(1);pointer-events:all}',
      '.ucw-win.min{height:56px;min-height:56px;border-radius:16px}',
      '.ucw-win.min .ucw-hdr{min-height:56px!important;padding:0 14px!important;border-radius:16px!important}',
      '.ucw-win.min .ucw-hdr-av{width:34px!important;height:34px!important}',
      '.ucw-win.min .ucw-hdr-l{gap:10px!important}',
      '.ucw-win.min .ucw-hdr-name{font-size:14px!important}',
      '.ucw-win.min .ucw-hdr-status{font-size:11px!important;gap:4px!important}',
      '.ucw-win.min .ucw-hdr-acts{gap:2px!important}',
      '.ucw-win.min .ucw-hdr-info{display:flex!important;align-items:center!important;gap:8px!important}',
      '.ucw-win.min .ucw-hdr-name{white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}',
      '.ucw-win.min .ucw-hdr-status{margin:0!important}',
      '.ucw-win.min .ucw-dot{width:6px!important;height:6px!important}',
      '.ucw-win.min .ucw-hdr-btn{width:28px!important;height:28px!important;border-radius:6px!important}',
      '.ucw-win.min .ucw-hdr-btn svg{width:15px!important;height:15px!important}',

      /* Modo tela cheia */
      '.ucw-win.full{position:fixed!important;inset:0!important;width:100%!important;height:100%!important;',
      'max-height:100%!important;border-radius:0!important;z-index:' + (C.zIndex + 5) + '}',
      'html.ucw-noscroll,html.ucw-noscroll body{overflow:hidden!important}',
      '.ucw-win.full .ucw-hdr{border-radius:0;padding:14px 32px}',
      '.ucw-win.full .ucw-hdr-acts{gap:3px;margin-right:6px}',
      '.ucw-win.full .ucw-hdr-btn{background:rgba(255,255,255,.25)!important}',
      '.ucw-win.full .ucw-hdr-btn:hover{background:rgba(255,255,255,.4)!important}',
      '.ucw-trigger.hidden{opacity:0;pointer-events:none;transform:scale(0)}',

      /* Cabeçalho */
      '.ucw-hdr{background:linear-gradient(135deg,' + C.primaryColor + ' 0%,#16a34a 50%,' + C.primaryDark + ' 100%)!important;',
      'color:#fff!important;padding:14px 16px!important;display:flex!important;align-items:center!important;justify-content:space-between!important;',
      'flex-shrink:0!important;min-height:62px!important;user-select:none!important;cursor:pointer!important;border:none!important}',
      '.ucw-hdr-l{display:flex!important;align-items:center!important;gap:12px!important;min-width:0!important}',
      '.ucw-hdr-av{width:40px!important;height:40px!important;border-radius:50%!important;overflow:hidden!important;flex-shrink:0!important;border:2px solid rgba(255,255,255,.3)!important}',
      '.ucw-hdr-av img{width:100%!important;height:100%!important;object-fit:cover!important;display:block!important}',
      '.ucw-hdr-name{font-size:16px!important;font-weight:700!important;letter-spacing:-.01em!important;color:#fff!important}',
      '.ucw-hdr-status{font-size:12px!important;font-weight:500!important;opacity:.9!important;display:flex!important;align-items:center!important;gap:5px!important;color:#fff!important}',
      '.ucw-dot{width:7px!important;height:7px!important;border-radius:50%!important;background:#4ade80!important;display:inline-block!important;',
      'box-shadow:0 0 6px rgba(74,222,128,.6)!important;animation:ucwDotPulse 2s ease-in-out infinite!important}',
      '.ucw-dot.off{background:#94a3b8!important;box-shadow:none!important;animation:none!important}',
      '.ucw-hdr-acts{display:flex!important;gap:4px!important;flex-shrink:0!important}',
      '.ucw-hdr-btn{width:32px!important;height:32px!important;border:none!important;background:rgba(255,255,255,.15)!important;color:#fff!important;border-radius:8px!important;',
      'cursor:pointer!important;display:flex!important;align-items:center!important;justify-content:center!important;transition:all .2s!important;font-size:18px!important;line-height:1!important;padding:0!important;margin:0!important}',
      '.ucw-hdr-btn:hover{background:rgba(255,255,255,.25)!important;transform:scale(1.05)!important}',
      '.ucw-hdr-btn svg{width:18px!important;height:18px!important;display:block!important}',

      /* Iframe */
      '.ucw-frame{flex:1;border:none;width:100%;display:block;background:#fff}',
      '.ucw-win.min .ucw-frame{display:none}',

      /* Animações */
      '@keyframes ucwBounce{0%{transform:scale(0);opacity:0}60%{transform:scale(1.15)}100%{transform:scale(1);opacity:1}}',
      '@keyframes ucwPulse{0%{transform:scale(1);opacity:.6}100%{transform:scale(1.5);opacity:0}}',
      '@keyframes ucwDotPulse{0%,100%{opacity:1}50%{opacity:.5}}',

      /* Responsivo */
      '@media(max-width:480px){',
      '#ucw-root{bottom:16px;right:16px}',
      '.ucw-win{position:fixed!important;inset:0!important;width:100%!important;height:100%!important;',
      'max-height:100vh!important;border-radius:0!important;bottom:0!important;right:0!important}',
      '.ucw-win.min{inset:auto 0 0 0!important;height:62px!important;border-radius:16px 16px 0 0!important}',
      '}',
    ].join('\n');
    document.head.appendChild(s);
  }

  /* ================================================================
     ÍCONES SVG
     ================================================================ */
  var ICO = {
    chat: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    min: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>',
    expand: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>',
    shrink: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/></svg>',
  };

  /* ================================================================
     DOM
     ================================================================ */
  var $ = {};

  function buildDOM() {
    var root = document.createElement('div');
    root.id = 'ucw-root';

    /* Botão flutuante */
    var trig = document.createElement('button');
    trig.className = 'ucw-trigger';
    trig.setAttribute('aria-label', 'Abrir chat');
    trig.innerHTML =
      '<span class="ucw-ic-avatar"><img src="' + C.avatarUrl + '" alt="Chat"></span>' +
      '<span class="ucw-ic-x">' + ICO.x + '</span>' +
      '<span class="ucw-badge"></span>';

    /* Janela do chat */
    var win = document.createElement('div');
    win.className = 'ucw-win';

    /* Cabeçalho */
    var hdr = document.createElement('div');
    hdr.className = 'ucw-hdr';
    hdr.innerHTML =
      '<div class="ucw-hdr-l">' +
      '  <div class="ucw-hdr-av"><img src="' + C.avatarUrl + '" alt="Avatar"></div>' +
      '  <div class="ucw-hdr-info">' +
      '    <div class="ucw-hdr-name">' + escHtml(C.assistantName) + '</div>' +
      '    <div class="ucw-hdr-status"><span class="ucw-dot"></span><span class="ucw-st-txt">Online</span></div>' +
      '  </div>' +
      '</div>' +
      '<div class="ucw-hdr-acts">' +
      '  <button class="ucw-hdr-btn ucw-btn-min" aria-label="Minimizar">' + ICO.min + '</button>' +
      '  <button class="ucw-hdr-btn ucw-btn-full" aria-label="Tela cheia">' + ICO.expand + '</button>' +
      '  <button class="ucw-hdr-btn ucw-btn-close" aria-label="Fechar">' + ICO.x + '</button>' +
      '</div>';

    /* Iframe */
    var iframe = document.createElement('iframe');
    iframe.className = 'ucw-frame';
    iframe.setAttribute('title', 'Chat');

    win.appendChild(hdr);
    win.appendChild(iframe);
    root.appendChild(win);
    root.appendChild(trig);
    document.body.appendChild(root);

    $ = {
      root: root,
      trig: trig,
      badge: trig.querySelector('.ucw-badge'),
      win: win,
      hdr: hdr,
      btnMin: hdr.querySelector('.ucw-btn-min'),
      btnFull: hdr.querySelector('.ucw-btn-full'),
      btnClose: hdr.querySelector('.ucw-btn-close'),
      dot: hdr.querySelector('.ucw-dot'),
      stTxt: hdr.querySelector('.ucw-st-txt'),
      iframe: iframe,
    };
  }

  function escHtml(s) {
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  /* ================================================================
     ESTADO
     ================================================================ */
  var isOpen = false;
  var isMin = false;
  var isFull = false;
  var iframeLoaded = false;

  function loadIframe() {
    if (!iframeLoaded) {
      $.iframe.src = WIDGET_URL;
      iframeLoaded = true;
    }
  }

  function openChat() {
    isOpen = true;
    isMin = false;
    loadIframe();
    $.win.classList.add('open');
    $.win.classList.remove('min');
    $.trig.classList.add('open');
    sSet('ucw_open', '1');
    sRem('ucw_min');
    $.badge.classList.remove('show');

    if (sGet('ucw_full') === '1') goFull();
  }

  function closeChat() {
    isOpen = false;
    isMin = false;
    if (isFull) exitFull();
    $.win.classList.remove('open', 'min');
    $.trig.classList.remove('open');
    sRem('ucw_open');
    sRem('ucw_min');
  }

  function minimize() {
    if (isFull) exitFull();
    isMin = true;
    $.win.classList.add('min');
    sSet('ucw_min', '1');
  }

  function maximize() {
    isMin = false;
    $.win.classList.remove('min');
    sRem('ucw_min');
  }

  function goFull() {
    isFull = true;
    isMin = false;
    $.win.classList.add('full');
    $.win.classList.remove('min');
    $.trig.classList.add('hidden');
    document.documentElement.classList.add('ucw-noscroll');
    $.btnFull.innerHTML = ICO.shrink;
    $.btnFull.setAttribute('aria-label', 'Restaurar');
    sSet('ucw_full', '1');
    sRem('ucw_min');
  }

  function exitFull() {
    isFull = false;
    $.win.classList.remove('full');
    $.trig.classList.remove('hidden');
    document.documentElement.classList.remove('ucw-noscroll');
    $.btnFull.innerHTML = ICO.expand;
    $.btnFull.setAttribute('aria-label', 'Tela cheia');
    sRem('ucw_full');
  }

  function toggleFull() {
    isFull ? exitFull() : goFull();
  }

  function toggle() {
    isOpen ? closeChat() : openChat();
  }

  /* ================================================================
     STATUS CHECK
     ================================================================ */
  function checkStatus() {
    fetch(API + '/chat/status')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.widget_enabled === false) {
          if ($.root) $.root.style.display = 'none';
          return;
        }
        if (d.allowed_origins && d.allowed_origins.length > 0) {
          var currentOrigin = window.location.origin;
          var isAllowed = d.allowed_origins.some(function (o) { return o === currentOrigin; });
          if (!isAllowed && currentOrigin !== TRUSTED_ORIGIN) {
            console.warn('[UraniaChat] Origem ' + currentOrigin + ' não autorizada.');
            if ($.root) $.root.style.display = 'none';
            return;
          }
        }
        if ($.root) $.root.style.display = '';
        var ok = d.available !== false;
        if ($.dot) $.dot.classList.toggle('off', !ok);
        if ($.stTxt) $.stTxt.textContent = ok ? 'Online' : 'Indisponível';
      })
      .catch(function () {
        if ($.dot) $.dot.classList.add('off');
        if ($.stTxt) $.stTxt.textContent = 'Indisponível';
      });
  }

  /* ================================================================
     EVENTOS
     ================================================================ */
  function bind() {
    $.trig.addEventListener('click', toggle);

    $.btnMin.addEventListener('click', function (e) {
      e.stopPropagation();
      isMin ? maximize() : minimize();
    });

    $.btnFull.addEventListener('click', function (e) {
      e.stopPropagation();
      toggleFull();
    });

    $.btnClose.addEventListener('click', function (e) {
      e.stopPropagation();
      closeChat();
    });

    $.hdr.addEventListener('click', function (e) {
      if (e.target.closest('.ucw-hdr-btn')) return;
      if (isMin) maximize();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && isOpen) {
        if (isFull) { exitFull(); return; }
        closeChat();
      }
    });

    window.addEventListener('message', function (e) {
      if (!e.data || typeof e.data !== 'object') return;
      if (e.origin !== TRUSTED_ORIGIN) return;
      if (e.data.type === 'ucw-status') {
        var ok = e.data.available;
        if ($.dot) $.dot.classList.toggle('off', !ok);
        if ($.stTxt) $.stTxt.textContent = ok ? 'Online' : 'Indisponível';
      }
      if (e.data.type === 'ucw-new-message' && !isOpen) {
        $.badge.textContent = '!';
        $.badge.classList.add('show');
      }
    });
  }

  /* ================================================================
     INIT
     ================================================================ */
  function init() {
    injectCSS();
    buildDOM();
    bind();
    checkStatus();

    if (sGet('ucw_open') === '1') {
      openChat();
      if (sGet('ucw_min') === '1') minimize();
      else if (sGet('ucw_full') === '1') goFull();
    } else {
      // Pre-carrega o iframe para a mensagem inicial estar pronta ao abrir
      setTimeout(loadIframe, 800);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
