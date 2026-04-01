/**
 * Oculta links [data-require-admin] quando o usuário não é administrador.
 * Depende de GET /auth/me com Bearer (localStorage admin_token).
 */
(function () {
  function token() {
    try {
      return localStorage.getItem('admin_token');
    } catch (e) {
      return null;
    }
  }
  function run() {
    var t = token();
    if (!t) return;
    fetch('/auth/me', { headers: { Authorization: 'Bearer ' + t } })
      .then(function (r) {
        if (!r.ok) return null;
        return r.json();
      })
      .then(function (data) {
        if (!data || data.role === 'admin') return;
        document.querySelectorAll('[data-require-admin]').forEach(function (el) {
          el.remove();
        });
      })
      .catch(function () {});
  }
  run();
})();
