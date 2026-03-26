/**
 * Aplica tema do chat (GET /branding → chat_theme) em variáveis CSS no documento.
 * Só carregar na página /widget.
 */
(function () {
  var MAP = {
    primary: '--chat-primary',
    primary_mid: '--chat-primary-mid',
    primary_dark: '--chat-primary-dark',
    user_bg: '--chat-user-bg',
    user_border: '--chat-user-border',
    user_text: '--chat-user-text',
    page_from: '--chat-page-from',
    page_via: '--chat-page-via',
    page_to: '--chat-page-to',
    chat_box_bg: '--chat-box-bg',
    input_focus: '--chat-input-focus',
    bubble_radius: '--chat-bubble-radius',
    pdf_header_bg: '--chat-pdf-header-bg',
    pdf_title: '--chat-pdf-title',
  };

  function apply(t) {
    if (!t) return;
    var r = document.documentElement;
    Object.keys(MAP).forEach(function (k) {
      if (t[k]) r.style.setProperty(MAP[k], t[k]);
    });
  }

  fetch('/branding', { cache: 'no-store' })
    .then(function (res) {
      return res.json();
    })
    .then(function (b) {
      apply(b.chat_theme);
    })
    .catch(function () {});
})();
