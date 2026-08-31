/* DEI Chatbot Dashboard logic */
(function () {
  'use strict';

  /* ====================================================================== *
   *  LUCIDE ICON SYSTEM (v1.1.9) — inline SVG, no CDN, MIT-licensed paths
   *  Usage: ico('save') → '<svg ...>...</svg>'  |  ico('save', 18) for size
   * ====================================================================== */
  var ICONS = {
    // Sidebar nav
    'bar-chart-3':       '<path d="M3 3v18h18"/><path d="M8 17V9"/><path d="M13 17V5"/><path d="M18 17v-3"/>',
    'message-circle':    '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    'book-open':         '<path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>',
    'pen-tool':          '<path d="M15.707 21.293a1 1 0 0 1-1.414 0l-1.586-1.586a1 1 0 0 1 0-1.414l5.586-5.586a1 1 0 0 1 1.414 0l1.586 1.586a1 1 0 0 1 0 1.414z"/><path d="m18 13-1.375-6.874a1 1 0 0 0-.746-.776L3.235 2.028a1 1 0 0 0-1.207 1.207L5.35 15.879a1 1 0 0 0 .776.746L13 18"/><path d="m2.3 2.3 7.286 7.286"/><circle cx="11" cy="11" r="2"/>',
    'flask-conical':     '<path d="M14 2v6a2 2 0 0 0 .245.96l5.51 10.08A2 2 0 0 1 18 22H6a2 2 0 0 1-1.755-2.96l5.51-10.08A2 2 0 0 0 10 8V2"/><path d="M6.453 15h11.094"/><path d="M8.5 2h7"/>',
    'settings':          '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    'users':             '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    'rocket':            '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>',
    // Card headers
    'activity':          '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.5.5 0 0 1-.96 0L9.24 2.18a.5.5 0 0 0-.96 0l-2.35 8.36A2 2 0 0 1 4 12H2"/>',
    'wallet':            '<path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/>',
    'shield-check':      '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    'save':              '<path d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7"/><path d="M7 3v4a1 1 0 0 0 1 1h7"/>',
    'trash-2':           '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>',
    'log-out':           '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/>',
    // Banners / status
    'octagon-alert':     '<path d="M12 16h.01"/><path d="M12 8v4"/><path d="M15.312 2a2 2 0 0 1 1.414.586l4.688 4.688A2 2 0 0 1 22 8.688v6.624a2 2 0 0 1-.586 1.414l-4.688 4.688a2 2 0 0 1-1.414.586H8.688a2 2 0 0 1-1.414-.586l-4.688-4.688A2 2 0 0 1 2 15.312V8.688a2 2 0 0 1 .586-1.414l4.688-4.688A2 2 0 0 1 8.688 2z"/>',
    'triangle-alert':    '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    'clock-3':           '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16.5 12"/>',
    'ban':               '<circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/>',
    'check-circle-2':    '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    // Avatar Icon Mode (v1.1.9 hybrid)
    'bot':               '<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>',
    'hand':              '<path d="M18 11V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2"/><path d="M14 10V4a2 2 0 0 0-2-2a2 2 0 0 0-2 2v2"/><path d="M10 10.5V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/>',
    'smile':             '<circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" x2="9.01" y1="9" y2="9"/><line x1="15" x2="15.01" y1="9" y2="9"/>',
    'headphones':        '<path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H4a1 1 0 0 1-1-1zm18 0h-3a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h2a1 1 0 0 0 1-1zM3 14a9 9 0 0 1 18 0"/>',
    'user-round':        '<circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 0 0-16 0"/>',
    'briefcase-business':'<path d="M12 12h.01"/><path d="M16 6V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/><path d="M22 13a18.15 18.15 0 0 1-20 0"/><rect width="20" height="14" x="2" y="6" rx="2"/>',
    'phone':             '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>',
    'sparkles':          '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/><path d="M4 17v2"/><path d="M5 18H3"/>',
    'mail':              '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    'life-buoy':         '<circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/><circle cx="12" cy="12" r="4"/>',
    'crown':             '<path d="M11.562 3.266a.5.5 0 0 1 .876 0L15.39 8.87a1 1 0 0 0 1.516.294L21.183 5.5a.5.5 0 0 1 .798.519l-2.834 10.246a1 1 0 0 1-.956.734H5.81a1 1 0 0 1-.957-.734L2.02 6.02a.5.5 0 0 1 .798-.519l4.276 3.664a1 1 0 0 0 1.516-.294z"/><path d="M5 21h14"/>',
  };
  /* v1.2.26: ikon tambahan. Ditaruh di objek TERPISAH lalu digabungkan,
     supaya peta ICONS asli tidak perlu disentuh. */
  var ICONS_EXTRA = {
    'search':        '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    'circle-help':   '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    'upload':        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>',
    'download':      '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
    'copy':          '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    'clipboard-list':'<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
    'bell':          '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    'bell-off':      '<path d="M8.7 3A6 6 0 0 1 18 8a21.3 21.3 0 0 0 .6 5"/><path d="M17 17H3s3-2 3-9a4.67 4.67 0 0 1 .3-1.7"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/><path d="m2 2 20 20"/>',
    'rotate-cw':     '<path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/>',
    'corner-up-left':'<polyline points="9 14 4 9 9 4"/><path d="M20 20v-7a4 4 0 0 0-4-4H4"/>',
    'wrench':        '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
    'x':             '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    'arrow-left':    '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
    'globe':         '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    'paperclip':     '<path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>',
    'menu':          '<line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/>',
    'chevron-down':  '<path d="m6 9 6 6 6-6"/>'
  };
  for (var _ikey in ICONS_EXTRA) {
    if (Object.prototype.hasOwnProperty.call(ICONS_EXTRA, _ikey)) ICONS[_ikey] = ICONS_EXTRA[_ikey];
  }

  function ico(name, size, extraAttrs) {
    var path = ICONS[name];
    if (!path) return '';
    var sz = size || 18;
    var attrs = extraAttrs || '';
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + sz + '" height="' + sz +
           '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide" ' + attrs + '>' +
           path + '</svg>';
  }
  // Expose for inline replacement of static markup
  window._ico = ico;

  /* ---- base + api ------------------------------------------------------ */
  var path = window.location.pathname;
  var idx = path.indexOf('/dashboard/chatbot-ai');
  var base = idx >= 0 ? path.slice(0, idx) : path.replace(/\/[^\/]*$/, '');
  var SITE_BASE = window.location.origin + base;        // e.g. https://domain.com
  var API = SITE_BASE + '/api/index.php';

  var token = localStorage.getItem('dei_token');
  var user = JSON.parse(localStorage.getItem('dei_user') || 'null');
  if (!token || !user) { location.href = 'login.html'; return; }

  function logout() {
    localStorage.removeItem('dei_token');
    localStorage.removeItem('dei_user');
    location.href = 'login.html';
  }

  function api(action, opts) {
    opts = opts || {};
    var sep = '&_=' + Date.now();   // cache-buster: dodge any server/proxy caching of repeated API URLs
    var url = API + '?action=' + action + (opts.query || '') + sep;
    var conf = { method: opts.method || 'GET', headers: { 'X-Auth-Token': token }, cache: 'no-store' };
    if (opts.body) { conf.headers['Content-Type'] = 'application/json'; conf.body = JSON.stringify(opts.body); }
    return fetch(url, conf).then(function (r) {
      // Rotate token if server provided a refreshed one (idle window slid forward).
      var fresh = r.headers.get('X-Auth-Refresh');
      if (fresh) {
        try { token = fresh; localStorage.setItem('dei_token', fresh); } catch (e) {}
      }
      if (r.status === 401) { logout(); throw new Error('unauth'); }
      return r.text().then(function (txt) {
        if (!txt) { console.warn('[api] respons kosong untuk', action); return { ok: false, error: 'Respons kosong dari server.' }; }
        try { return JSON.parse(txt); }
        catch (e) { console.warn('[api] JSON tidak valid untuk', action, '-', txt.slice(0, 120)); return { ok: false, error: 'Respons tidak valid.' }; }
      });
    });
  }

  /* ---- helpers --------------------------------------------------------- */
  var $ = function (s) { return document.querySelector(s); };
  var $$ = function (s) { return Array.prototype.slice.call(document.querySelectorAll(s)); };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  var toastT;
  function toast(msg, isErr) {
    var t = $('#toast'); t.textContent = msg; t.className = 'toast show' + (isErr ? ' err' : '');
    clearTimeout(toastT); toastT = setTimeout(function () { t.className = 'toast'; }, 2600);
  }

  /* ---- role + nav ------------------------------------------------------ */
  var role = user.role || 'admin';
  var ROLE_LABEL = { super_admin: 'Super Admin', admin: 'Admin', wa_agent: 'WA Agent' };
  function can(allowed) {           // allowed = "role1,role2,..." or array
    if (!allowed || allowed === 'any') return true;
    var arr = Array.isArray(allowed) ? allowed : String(allowed).split(',');
    return arr.indexOf(role) !== -1;
  }
  $('#whoName').textContent = user.name || user.username;
  $('#whoRole').textContent = ROLE_LABEL[role] || role;
  $('#logout').onclick = logout;
  // v1.1.8: Mobile sidebar — backdrop, click-outside-to-close, auto-close on tab switch
  function toggleSide(force) {
    var side = document.getElementById('side');
    var willOpen = force !== undefined ? force : !side.classList.contains('open');
    side.classList.toggle('open', willOpen);
    document.body.classList.toggle('side-open', willOpen);
  }
  $('#menuBtn').onclick = function () { toggleSide(); };
  // Click backdrop (anywhere outside sidebar when open) → close
  document.addEventListener('click', function (e) {
    if (!document.body.classList.contains('side-open')) return;
    var side = document.getElementById('side');
    var btn = document.getElementById('menuBtn');
    if (!side.contains(e.target) && !btn.contains(e.target)) toggleSide(false);
  });
  // ESC to close
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && document.body.classList.contains('side-open')) toggleSide(false);
  });

  // hide nav items not allowed for this role
  $$('#nav button').forEach(function (b) {
    if (!can(b.dataset.role)) b.classList.add('hide');
    // v1.1.9: inject Lucide icon
    var iconName = b.dataset.icon;
    if (iconName) {
      var icSpan = b.querySelector('.ic');
      if (icSpan) icSpan.innerHTML = ico(iconName, 18);
    }
  });
  // v1.2.26: isi semua elemen ber-atribut data-ico dengan ikonnya.
  // Menyusul pola nav sidebar — markup HTML cukup menyebut nama ikonnya.
  function fillDataIcons(scope) {
    var akar = scope || document;
    Array.prototype.slice.call(akar.querySelectorAll('[data-ico]')).forEach(function (el) {
      if (el.dataset.icoDone) return;
      var svg = ico(el.dataset.ico, +(el.dataset.icoSize || 15), 'style="vertical-align:-3px"');
      if (svg) { el.innerHTML = svg; el.dataset.icoDone = '1'; }
    });
  }
  window._fillDataIcons = fillDataIcons;
  fillDataIcons();

  // hide secret-only cards (API/WA Cloud API/Telegram) for non super_admin
  $$('[data-role-card]').forEach(function (el) {
    if (!can(el.dataset.roleCard)) el.classList.add('hide');
  });

  var loaded = {};
  function showTab(tab) {
    $$('#nav button').forEach(function (b) { b.classList.toggle('active', b.dataset.tab === tab); });
    $$('.panel').forEach(function (p) { p.classList.remove('active'); });
    var panel = $('#panel-' + tab);
    if (panel) panel.classList.add('active');
    $('#side').classList.remove('open');
    document.body.classList.remove('side-open');   // v1.1.8: also drop backdrop
    // v1.2.39 fase7b: loader di baris bawah hanya jalan SEKALI per tab
    // (dijaga oleh loaded[tab]), jadi reset tampilan mobile HARUS di sini --
    // showTab() selalu jalan tiap menu dipilih. Memilih menu "Percakapan WA"
    // diperlakukan sama dengan menekan tombol Back: kembali ke DAFTAR
    // percakapan di posisi paling atas, bukan nyangkut di thread terakhir.
    if (tab === 'wachat') {
      var _wrapNav = document.querySelector('.wachat-wrap');
      if (_wrapNav) _wrapNav.classList.remove('showing-thread');
      if (window.scrollTo) window.scrollTo(0, 0);
    }
    if (!loaded[tab]) { loaded[tab] = true; if (loaders[tab]) loaders[tab](); }
  }
  $$('#nav button').forEach(function (b) { b.onclick = function () { showTab(b.dataset.tab); }; });

  /* ====================================================================== *
   *  REPORTS
   * ====================================================================== */
  function reportQuery() {
    var f = $('#repFrom') ? $('#repFrom').value : '';
    var t = $('#repTo') ? $('#repTo').value : '';
    var c = $('#repChannel') ? $('#repChannel').value : 'all';
    return '&from=' + encodeURIComponent(f) + '&to=' + encodeURIComponent(t) + '&channel=' + encodeURIComponent(c);
  }

  function utmRows(arr) {
    return arr.length
      ? arr.map(function (r) {
          return '<tr><td><span class="tag' + (r.label.charAt(0) === '(' ? ' none' : '') + '">' + esc(r.label) + '</span></td>' +
            '<td style="text-align:right" class="mono">' + r.count + '</td>' +
            '<td style="text-align:right" class="mono">' + (r.users != null ? r.users : '–') + '</td></tr>';
        }).join('')
      : emptyRow(3);
  }

  function loadReports() {
    api('report', { query: reportQuery() }).then(function (res) {
      if (!res.ok) return;
      var s = res.stats;
      $('#statCards').innerHTML =
        statCard(s.total, 'Total Percakapan') +
        statCard(s.today, 'Hari Ini') +
        statCard(s.kb_entries, 'Entri KB') +
        statCard(s.unique_ips, 'Pengunjung Unik');

      $('#tblSource').innerHTML   = utmRows(res.by_source || []);
      $('#tblMedium').innerHTML   = utmRows(res.by_medium || []);
      $('#tblSrcMed').innerHTML   = utmRows(res.by_source_medium || []);
      $('#tblCampaign').innerHTML = utmRows(res.by_campaign || []);

      if ($('#tblChannel')) {
        var byCh = res.by_channel || [];
        $('#tblChannel').innerHTML = byCh.length
          ? byCh.map(function (r) { var lbl = r.label === 'whatsapp' ? ico('message-circle',13) + ' WhatsApp' : (r.label === 'web' ? ico('globe',13) + ' Web' : esc(r.label)); return '<tr><td>' + lbl + '</td><td style="text-align:right" class="mono">' + r.count + '</td></tr>'; }).join('')
          : emptyRow(2);
      }

      $('#pieSrcMed').innerHTML  = svgPie(res.by_source_medium || []);
      $('#lineTrend').innerHTML  = svgTrend(res.trend || []);
    });
    loadLogs();
  }

  /* ---- inline SVG charts (no external libs) ---------------------------- */
  var PIE_COLORS = ['#140383', '#4338ca', '#6366f1', '#8b5cf6', '#a855f7', '#c084fc', '#e879f9', '#94a3b8'];

  function svgPie(arr) {
    var data = arr.slice(0, 7);
    var rest = arr.slice(7).reduce(function (a, r) { return a + r.count; }, 0);
    if (rest > 0) data.push({ label: 'lainnya', count: rest });
    var total = data.reduce(function (a, r) { return a + r.count; }, 0);
    if (!total) return '<div style="color:var(--muted);padding:24px;text-align:center">Belum ada data.</div>';
    var cx = 90, cy = 90, r = 80, ang = -Math.PI / 2, seg = '';
    data.forEach(function (d, i) {
      var frac = d.count / total, a2 = ang + frac * 2 * Math.PI;
      var x1 = cx + r * Math.cos(ang), y1 = cy + r * Math.sin(ang);
      var x2 = cx + r * Math.cos(a2), y2 = cy + r * Math.sin(a2);
      var large = frac > 0.5 ? 1 : 0;
      if (frac >= 0.9999) { // single slice = full circle
        seg += '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="' + PIE_COLORS[i % PIE_COLORS.length] + '"/>';
      } else {
        seg += '<path d="M' + cx + ',' + cy + ' L' + x1.toFixed(2) + ',' + y1.toFixed(2) + ' A' + r + ',' + r + ' 0 ' + large + ',1 ' + x2.toFixed(2) + ',' + y2.toFixed(2) + ' Z" fill="' + PIE_COLORS[i % PIE_COLORS.length] + '"/>';
      }
      ang = a2;
    });
    var legend = data.map(function (d, i) {
      var pct = Math.round(d.count / total * 100);
      return '<div style="display:flex;align-items:center;gap:6px;font-size:12px;margin:2px 0">' +
        '<span style="width:10px;height:10px;border-radius:2px;background:' + PIE_COLORS[i % PIE_COLORS.length] + ';display:inline-block"></span>' +
        '<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(d.label) + '</span>' +
        '<span class="mono" style="color:var(--muted)">' + d.count + ' · ' + pct + '%</span></div>';
    }).join('');
    return '<div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap">' +
      '<svg viewBox="0 0 180 180" width="180" height="180">' + seg + '</svg>' +
      '<div style="flex:1;min-width:160px">' + legend + '</div></div>';
  }

  function svgTrend(arr) {
    if (!arr.length) return '<div style="color:var(--muted);padding:24px;text-align:center">Belum ada data.</div>';
    var W = 520, H = 200, padL = 30, padB = 22, padT = 10, padR = 10;
    var max = Math.max(1, arr.reduce(function (m, d) { return Math.max(m, d.count, d.users); }, 0));
    var n = arr.length;
    var xw = (W - padL - padR), yh = (H - padT - padB);
    function X(i) { return padL + (n <= 1 ? xw / 2 : (i / (n - 1)) * xw); }
    function Y(v) { return padT + yh - (v / max) * yh; }
    function poly(key, color) {
      var pts = arr.map(function (d, i) { return X(i).toFixed(1) + ',' + Y(d[key]).toFixed(1); }).join(' ');
      var dots = arr.map(function (d, i) { return '<circle cx="' + X(i).toFixed(1) + '" cy="' + Y(d[key]).toFixed(1) + '" r="2.5" fill="' + color + '"/>'; }).join('');
      return '<polyline points="' + pts + '" fill="none" stroke="' + color + '" stroke-width="2"/>' + dots;
    }
    var grid = '', steps = 4;
    for (var g = 0; g <= steps; g++) {
      var yy = padT + (g / steps) * yh, val = Math.round(max * (1 - g / steps));
      grid += '<line x1="' + padL + '" y1="' + yy.toFixed(1) + '" x2="' + (W - padR) + '" y2="' + yy.toFixed(1) + '" stroke="var(--line)" stroke-width="1"/>';
      grid += '<text x="' + (padL - 4) + '" y="' + (yy + 3).toFixed(1) + '" text-anchor="end" font-size="9" fill="var(--muted)">' + val + '</text>';
    }
    var labels = '';
    var every = Math.ceil(n / 8);
    arr.forEach(function (d, i) {
      if (i % every === 0 || i === n - 1) labels += '<text x="' + X(i).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="middle" font-size="8.5" fill="var(--muted)">' + d.date.slice(5) + '</text>';
    });
    return '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" style="max-width:540px">' + grid + poly('count', '#140383') + poly('users', '#a855f7') + labels + '</svg>' +
      '<div style="display:flex;gap:16px;font-size:12px;margin-top:6px">' +
      '<span style="display:flex;align-items:center;gap:5px"><span style="width:14px;height:3px;background:#140383;display:inline-block"></span>Percakapan</span>' +
      '<span style="display:flex;align-items:center;gap:5px"><span style="width:14px;height:3px;background:#a855f7;display:inline-block"></span>Pengunjung unik</span></div>';
  }
  function statCard(v, l) { return '<div class="stat"><div class="v">' + v + '</div><div class="l">' + l + '</div></div>'; }
  function emptyRow(cols) { return '<tr><td colspan="' + cols + '" style="color:var(--muted);text-align:center;padding:24px">Belum ada data.</td></tr>'; }

  function loadLogs() {
    api('get_logs', { query: '&limit=200' }).then(function (res) {
      if (!res.ok) return;
      var b = $('#tblLogs');
      if (!res.logs.length) { b.innerHTML = emptyRow(6); return; }
      b.innerHTML = res.logs.map(function (l) {
        var src = l.utm_source ? '<span class="tag">' + esc(l.utm_source) + '</span>' : '<span class="tag none">(direct)</span>';
        var med = l.utm_medium ? '<span class="tag">' + esc(l.utm_medium) + '</span>' : '<span class="tag none">(none)</span>';
        return '<tr>' +
          '<td class="mono" style="white-space:nowrap;font-size:11.5px">' + esc(l.ts) + '</td>' +
          '<td class="q">' + esc(l.q) + '</td>' +
          '<td class="a">' + esc((l.a || '').slice(0, 160)) + ((l.a || '').length > 160 ? '…' : '') + '</td>' +
          '<td>' + src + '</td><td>' + med + '</td>' +
          '<td class="mono" style="font-size:11.5px;color:var(--muted)">' + esc(l.page || '') + '</td>' +
          '</tr>';
      }).join('');
    });
  }

  function initReportsControls() {
    var today = new Date().toISOString().slice(0, 10);
    var monthAgo = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);
    if ($('#repFrom')) $('#repFrom').value = monthAgo;
    if ($('#repTo')) $('#repTo').value = today;
    if ($('#btnApply')) $('#btnApply').onclick = loadReports;
    $('#btnExport').onclick = function () {
      var from = $('#repFrom') ? $('#repFrom').value : '';
      var to = $('#repTo') ? $('#repTo').value : '';
      var url = API + '?action=export_logs&token=' + encodeURIComponent(token) +
        '&from=' + encodeURIComponent(from) + '&to=' + encodeURIComponent(to);
      window.location.href = url;
      toast('Mengunduh CSV…');
    };
  }

  /* ====================================================================== *
   *  KNOWLEDGE BASE
   * ====================================================================== */
  /* ---- v1.2.13: daftar kategori notif (dinamis) ---------------------- */
  var deiCatList  = ['Sales', 'Operation', 'Marketing', 'Engineering', 'Owner', 'IT'];  // fallback sebelum fetch
  var deiCatFixed = ['Sales', 'Operation', 'Marketing', 'Engineering', 'Owner', 'IT'];
  var deiCatLoaded = false;
  function ensureCategories(cb) {
    if (deiCatLoaded) { cb && cb(); return; }
    api('get_categories').then(function (res) {
      if (res && res.ok) {
        deiCatList  = res.categories || deiCatList;
        deiCatFixed = res.fixed || deiCatFixed;
        deiCatLoaded = true;
      }
      cb && cb();
    });
  }
  // Bangun checkbox kategori di form pengguna dari daftar dinamis
  function renderUserCategories(selected) {
    var box = document.getElementById('u_categories');
    if (!box) return;
    var sel = selected || [];
    box.innerHTML = deiCatList.map(function (c) {
      var checked = (sel.indexOf(c) !== -1) ? ' checked' : '';
      return '<label style="display:flex;gap:5px;align-items:center;font-size:13px;cursor:pointer">' +
             '<input type="checkbox" class="u_cat" value="' + esc(c) + '"' + checked + '> ' + esc(c) + '</label>';
    }).join('') || '<span class="help">Belum ada kategori.</span>';
  }
  // Manager kategori (panel KB, super_admin only)
  function renderCatManager() {
    var box = document.getElementById('catManager');
    if (!box) return;
    if (user.role !== 'super_admin') { box.style.display = 'none'; return; }
    box.style.display = '';
    var list = document.getElementById('catList');
    list.innerHTML = deiCatList.map(function (c) {
      var isFixed = deiCatFixed.indexOf(c) !== -1;
      var del = isFixed ? '' : ' <a href="#" class="cat-del" data-c="' + esc(c) + '" style="text-decoration:none" title="Hapus">&times;</a>';
      var bg = isFixed ? '#e5e7eb' : '#dbeafe';
      return '<span class="tag" style="background:' + bg + ';padding:5px 10px">' + esc(c) + del + '</span>';
    }).join('');
    Array.prototype.slice.call(list.querySelectorAll('.cat-del')).forEach(function (a) {
      a.onclick = function (ev) {
        ev.preventDefault();
        var c = a.dataset.c;
        if (!confirm('Hapus kategori "' + c + '"?')) return;
        api('delete_category', { method: 'POST', body: { category: c } }).then(function (r) {
          if (r.ok) { deiCatList = r.categories || deiCatList; toast('Kategori dihapus.'); renderCatManager(); renderKb(); }
          else toast(r.error || 'Gagal menghapus.', true);
        });
      };
    });
    var btn = document.getElementById('btnAddCat');
    if (btn) btn.onclick = function () {
      var input = document.getElementById('catNew');
      var v = (input.value || '').trim();
      if (!v) { toast('Nama kategori wajib diisi.', true); return; }
      api('add_category', { method: 'POST', body: { category: v } }).then(function (r) {
        if (r.ok) { deiCatList = r.categories || deiCatList; input.value = ''; toast('Kategori ditambahkan.'); renderCatManager(); renderKb(); }
        else toast(r.error || 'Gagal menambah.', true);
      });
    };
  }
  var kbData = [];
  function loadKb() {
    ensureCategories(function () {   // v1.2.13: kategori dulu supaya dropdown topik lengkap
      renderCatManager();
      api('get_kb').then(function (res) { if (res.ok) { kbData = res.kb || []; renderKb(); } });
    });
    $('#btnAddKb').onclick = function () {
      kbData.unshift({ id: 'kb_' + Date.now(), category: '', title: '', content: '', topic: '' });
      renderKb();
    };
    $('#btnSaveKb').onclick = saveKb;
    $('#kbSearch').oninput = renderKb;
    $('#btnImportCsv').onclick = function () { var f = $('#kbCsvFile'); f.value = ''; f.click(); };
    $('#kbCsvFile').onchange = function (e) { importKbCsv(e.target.files && e.target.files[0]); e.target.value = ''; };
    $('#btnCsvTemplate').onclick = function (e) { e.preventDefault(); downloadKbTemplate(); };
    // v1.2.22: tab daftar harga
    $$('.kb-tab').forEach(function (b) {
      b.onclick = function () { switchKbTab(b.dataset.kbtab); };
    });
    $('#btnAddPrice').onclick = function () {
      priceData.push({ id: 'pr_' + Date.now(), item: '', price: '', note: '' });
      renderPricelist();
    };
    $('#btnSavePrice').onclick = savePricelist;
    $('#btnFindDup').onclick = findKbDuplicates;   // v1.2.23
    $('#btnFindGaps').onclick = findKbGaps;       // v1.2.24
  }
  /* ---- v1.2.24/25: pertanyaan belum terjawab ------------------------- */
  var gapData = [];
  var gapVerdict = {};   // indeks -> true kalau AI menilai benar-benar gagal

  function findKbGaps(showHidden) {
    var box = document.getElementById('gapResult');
    box.style.display = '';
    box.innerHTML = '<div style="color:var(--muted)">Memindai log percakapan...</div>';
    gapVerdict = {};
    api('kb_find_gaps', { query: showHidden ? '&show_hidden=1' : '' }).then(function (res) {
      if (!res || !res.ok) {
        box.innerHTML = '<div style="color:#b91c1c">' + esc((res && res.error) || 'Gagal memindai.') + '</div>';
        return;
      }
      gapData = res.gaps || [];
      renderKbGaps(res, showHidden);
    });
  }

  function renderKbGaps(res, showHidden) {
    var box = document.getElementById('gapResult');
    if (!gapData.length) {
      box.innerHTML = '<strong>Tidak ada pertanyaan yang gagal dijawab.</strong><br>' +
        '<span class="help">Dari ' + res.scanned + ' percakapan yang dipindai.' +
        (res.hidden ? ' (' + res.hidden + ' disembunyikan)' : '') + '</span>' +
        (res.hidden ? '<br><button class="btn ghost sm" id="btnShowHidden" style="margin-top:8px">Tampilkan yang disembunyikan</button>' : '');
      if (res.hidden) document.getElementById('btnShowHidden').onclick = function () { findKbGaps(true); };
      return;
    }

    var h = '<h3 style="margin-top:0">Pertanyaan Belum Terjawab</h3>' +
      '<p style="margin:0 0 4px">Dari <strong>' + res.scanned + '</strong> percakapan, ada <strong>' +
      gapData.length + '</strong> pertanyaan berbeda.' +
      (res.hidden ? ' <span class="help">(' + res.hidden + ' disembunyikan)</span>' : '') + '</p>' +
      '<p style="color:var(--muted);font-size:13px;line-height:1.5;margin:0 0 10px">' +
      'Diurutkan dari yang paling sering ditanyakan. Menambahkan membuat entri KB berisi ' +
      'pertanyaannya saja &mdash; <strong>jawabannya Anda yang tulis</strong>. Entri tanpa jawaban ' +
      'tidak dikirim ke bot, jadi aman menumpuk dulu.</p>' +
      '<div class="toolbar" style="margin-bottom:10px">' +
        '<button class="btn ghost sm" id="btnVerifyGaps">' + ico('sparkles',14) + ' Saring dengan AI</button>' +
        (showHidden ? '<button class="btn ghost sm" id="btnRestoreGaps">Pulihkan semua yang disembunyikan</button>' : '') +
        '<span class="help" id="gapVerifyInfo" style="margin-left:auto"></span>' +
      '</div>';

    h += gapData.map(function (g, i) {
      var kanal = (g.channels || []).join(', ');
      var v = gapVerdict[i];
      var redup = (v === false) ? 'opacity:.45;' : '';
      var tanda = (v === false)
        ? ' <span class="tag" style="background:#e5e7eb;color:#374151;font-size:11px">AI: sudah terjawab</span>'
        : (v === true ? ' <span class="tag" style="background:#fee2e2;color:#b91c1c;font-size:11px">Jawaban kurang akurat</span>' : '');
      return '<div class="row" data-gap="' + i + '" style="align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--line);' + redup + '">' +
        '<span class="tag" style="background:#fef3c7;color:#92400e;min-width:44px;text-align:center">' + g.count + '&times;</span>' +
        '<div style="flex:1">' + esc(g.question) + tanda +
          '<div class="help" style="font-size:11px">' + esc(kanal) +
          (g.last_ts ? ' &middot; terakhir ' + esc(g.last_ts.slice(0, 10)) : '') + '</div>' +
        '</div>' +
        '<button class="btn ghost sm gap-add">+ Tambah ke KB</button>' +
        '<button class="btn ghost sm gap-hide" title="Sembunyikan, jangan tampilkan lagi">&times;</button>' +
      '</div>';
    }).join('');
    box.innerHTML = h;

    document.getElementById('btnVerifyGaps').onclick = verifyKbGaps;
    var btnRestore = document.getElementById('btnRestoreGaps');
    if (btnRestore) btnRestore.onclick = function () {
      if (!confirm('Tampilkan kembali semua pertanyaan yang pernah disembunyikan?')) return;
      api('kb_restore_gaps', { method: 'POST' }).then(function (r) {
        if (r && r.ok) { toast('Dipulihkan.'); findKbGaps(false); }
      });
    };

    Array.prototype.slice.call(box.querySelectorAll('.row[data-gap]')).forEach(function (row) {
      var i = +row.dataset.gap;
      var g = gapData[i];
      row.querySelector('.gap-add').onclick = function () {
        var btn = this;
        btn.disabled = true;
        api('kb_add_gap', { method: 'POST', body: { question: g.question } }).then(function (r) {
          if (r && r.ok) {
            btn.textContent = '\u2713 Ditambahkan';
            toast('Ditambahkan ke KB kategori "Perlu Diisi" \u2014 isinya masih kosong.');
            api('get_kb').then(function (k) { if (k.ok) { kbData = k.kb || []; renderKb(); } });
          } else { btn.disabled = false; toast((r && r.error) || 'Gagal.', true); }
        });
      };
      row.querySelector('.gap-hide').onclick = function () {
        api('kb_dismiss_gap', { method: 'POST', body: { key: g.key } }).then(function (r) {
          if (r && r.ok) { row.style.display = 'none'; toast('Disembunyikan.'); }
          else toast((r && r.error) || 'Gagal.', true);
        });
      };
    });
  }

  // AI hanya MEMILAH — tidak menulis jawaban, tidak menghapus apa pun.
  // Satu panggilan untuk seluruh daftar = 1 jatah kuota.
  function verifyKbGaps() {
    if (!gapData.length) return;
    if (!confirm('Saring ' + gapData.length + ' pertanyaan dengan AI?\n\nMemakai 1 jatah kuota chat.')) return;
    var info = document.getElementById('gapVerifyInfo');
    info.textContent = 'Menyaring...';
    var kirim = gapData.map(function (g) { return { question: g.question, sample_a: g.sample_a || '' }; });
    api('kb_verify_gaps', { method: 'POST', body: { items: kirim } }).then(function (r) {
      if (!r || !r.ok) { info.textContent = ''; toast((r && r.error) || 'Penyaringan gagal.', true); return; }
      gapVerdict = {};
      for (var i = 0; i < gapData.length; i++) gapVerdict[i] = (r.failed.indexOf(i) !== -1);
      var jmlGagal = r.failed.length;
      var jmlSalah = gapData.length - jmlGagal;
      renderKbGaps({ scanned: '-', hidden: 0 }, false);
      document.getElementById('gapVerifyInfo').textContent =
        jmlGagal + ' benar gagal, ' + jmlSalah + ' sebenarnya sudah terjawab';
      if (jmlSalah) {
        toast(jmlSalah + ' pertanyaan ditandai sudah terjawab \u2014 diredupkan, bisa disembunyikan.');
      }
    });
  }

  /* ---- v1.2.23: analisa duplikat KB ---------------------------------- */
  function findKbDuplicates() {
    var box = document.getElementById('dupResult');
    box.style.display = '';
    box.innerHTML = '<div style="color:var(--muted)">Menganalisa...</div>';
    api('kb_find_duplicates').then(function (res) {
      if (!res || !res.ok) {
        box.innerHTML = '<div style="color:#b91c1c">' + esc((res && res.error) || 'Gagal menganalisa.') + '</div>';
        return;
      }
      if (!res.removed) {
        box.innerHTML = '<strong>Tidak ada duplikat.</strong><br>' +
          '<span class="help">' + res.total + ' entri, semuanya berisi teks berbeda.</span>';
        return;
      }
      var h = '<h3 style="margin-top:0">Hasil Analisa Duplikat</h3>' +
        '<div class="grid2" style="margin-bottom:10px">' +
          '<div><span class="help">Entri sekarang</span><br><strong style="font-size:18px">' + res.total + '</strong></div>' +
          '<div><span class="help">Setelah digabung</span><br><strong style="font-size:18px">' + res.unique + '</strong></div>' +
        '</div>' +
        '<p style="margin:0 0 10px">Ada <strong>' + res.removed + '</strong> entri kembar dalam ' +
        res.group_count + ' kelompok. Isinya sama persis, hanya kalimat tanyanya berbeda.</p>';

      if (res.groups && res.groups.length) {
        h += '<div style="margin-bottom:10px"><span class="help">Yang paling banyak digandakan:</span><br>';
        h += res.groups.map(function (g) {
          return '<div style="font-size:13px;padding:2px 0">' +
                 '<span class="tag" style="background:#e5e7eb;color:#374151">' + g.count + '&times;</span> ' +
                 esc(g.title) + '</div>';
        }).join('');
        h += '</div>';
      }

      if (res.conflicts && res.conflicts.length) {
        h += '<p style="color:#b91c1c;font-size:13px">Perhatian: ' + res.conflicts.length +
             ' kelompok punya tag topik berbeda antar duplikatnya. Yang pertama akan dipakai.</p>';
      }

      h += '<p style="color:var(--muted);font-size:13px;line-height:1.5">' +
           'Penggabungan menyimpan satu entri per isi, memakai judul terpendek, dan ' +
           'mempertahankan tag topik yang sudah ada. Jawaban bot tidak berubah &mdash; ' +
           'yang dihapus hanya salinan kalimat tanya. Cadangan dibuat otomatis.</p>' +
           '<button class="btn" id="btnMergeDup">Gabungkan ' + res.total + ' &rarr; ' + res.unique + '</button>';
      box.innerHTML = h;

      document.getElementById('btnMergeDup').onclick = function () {
        if (!confirm('Gabungkan ' + res.total + ' entri jadi ' + res.unique + '?\n\n' +
                     res.removed + ' entri kembar akan dihapus.\nCadangan dibuat otomatis di server.')) return;
        api('kb_merge_duplicates', { method: 'POST' }).then(function (r) {
          if (r && r.ok) {
            toast('Digabungkan: ' + r.before + ' -> ' + r.after + ' entri.');
            box.innerHTML = '<strong>Selesai.</strong> ' + r.before + ' &rarr; ' + r.after +
              ' entri.<br><span class="help">Cadangan: ' + esc(r.backup) + '</span>';
            api('get_kb').then(function (k) { if (k.ok) { kbData = k.kb || []; renderKb(); } });
          } else {
            toast((r && r.error) || 'Gagal menggabungkan.', true);
          }
        });
      };
    });
  }

  /* ---- v1.2.22: daftar harga ----------------------------------------- */
  var priceData = [];

  function switchKbTab(which) {
    $$('.kb-tab').forEach(function (b) { b.classList.toggle('active', b.dataset.kbtab === which); });
    var entri = document.getElementById('kbTabEntri');
    var harga = document.getElementById('kbTabHarga');
    if (entri) entri.style.display = (which === 'entri') ? '' : 'none';
    if (harga) harga.style.display = (which === 'harga') ? '' : 'none';
    if (which === 'harga' && !priceData.length) fetchPricelist();
  }

  function fetchPricelist() {
    api('get_pricelist').then(function (res) {
      if (!res || !res.ok) { toast((res && res.error) || 'Gagal memuat daftar harga.', true); return; }
      priceData = res.items || [];
      var meta = document.getElementById('priceMeta');
      if (meta) {
        meta.textContent = res.updated_at
          ? ('Diperbarui ' + res.updated_at.slice(0, 16) + (res.updated_by ? ' oleh ' + res.updated_by : ''))
          : 'Belum pernah disimpan';
      }
      renderPricelist();
    });
  }

  function renderPricelist() {
    if (!priceData.length) {
      $('#priceList').innerHTML = '<div style="text-align:center;color:var(--muted);padding:20px">' +
        'Belum ada harga. Klik "+ Tambah Baris" untuk mulai.</div>';
      return;
    }
    $('#priceList').innerHTML = priceData.map(function (p, i) {
      return '<div class="row" data-pi="' + i + '" style="gap:8px;align-items:flex-start">' +
        '<input type="text" class="pr-item"  placeholder="Nama item"  value="' + esc(p.item || '') + '" style="flex:2">' +
        '<input type="text" class="pr-price" placeholder="Harga"      value="' + esc(p.price || '') + '" style="flex:1">' +
        '<input type="text" class="pr-note"  placeholder="Catatan (opsional)" value="' + esc(p.note || '') + '" style="flex:2">' +
        '<button class="btn danger sm pr-del" title="Hapus baris">&times;</button>' +
      '</div>';
    }).join('');
    $$('#priceList .row[data-pi]').forEach(function (row) {
      var i = +row.dataset.pi;
      row.querySelector('.pr-item').oninput  = function (e) { priceData[i].item  = e.target.value; };
      row.querySelector('.pr-price').oninput = function (e) { priceData[i].price = e.target.value; };
      row.querySelector('.pr-note').oninput  = function (e) { priceData[i].note  = e.target.value; };
      row.querySelector('.pr-del').onclick   = function () { priceData.splice(i, 1); renderPricelist(); };
    });
  }

  function savePricelist() {
    // baris tanpa nama item dibuang di backend; peringatkan kalau ada harga kosong
    var tanpaHarga = priceData.filter(function (p) {
      return (p.item || '').trim() && !(p.price || '').trim();
    }).length;
    if (tanpaHarga && !confirm(tanpaHarga + ' baris punya nama tapi harganya kosong.\nBaris itu tidak akan dipakai bot. Tetap simpan?')) return;
    api('save_pricelist', { method: 'POST', body: { items: priceData } }).then(function (res) {
      if (res && res.ok) { toast('Daftar harga disimpan (' + res.count + ' item).'); fetchPricelist(); }
      else toast((res && res.error) || 'Gagal menyimpan.', true);
    });
  }

  // v1.2.12: build <option> untuk dropdown topik KB
  function kbTopicOptions(selected) {
    var topics = [''].concat(deiCatList);  // v1.2.13: dinamis
    return topics.map(function (t) {
      var label = t || '— Umum —';
      var sel = (selected === t) ? ' selected' : '';
      return '<option value="' + t + '"' + sel + '>' + label + '</option>';
    }).join('');
  }
  function renderKb() {
    var term = ($('#kbSearch').value || '').toLowerCase();
    var html = kbData.map(function (e, i) {
      if (term && (e.title + ' ' + e.content + ' ' + e.category).toLowerCase().indexOf(term) === -1) return '';
      return '<div class="card" data-i="' + i + '">' +
        '<div class="grid2">' +
        '<div class="row"><label class="fl">Judul</label><input type="text" class="kb-title" value="' + esc(e.title) + '"></div>' +
        '<div class="row"><label class="fl">Kategori</label><input type="text" class="kb-cat" value="' + esc(e.category) + '"></div>' +
        '</div>' +
        '<div class="row"><label class="fl">Topik (routing notif)</label>' +
          '<select class="kb-topic">' + kbTopicOptions(e.topic || '') + '</select>' +
        '</div>' +
        '<div class="row"><label class="fl">Isi</label><textarea class="kb-content">' + esc(e.content) + '</textarea></div>' +
        '<button class="btn danger sm kb-del">' + ico('trash-2',14) + ' Hapus entri</button>' +
        '</div>';
    }).join('');
    $('#kbList').innerHTML = html || '<div class="card" style="text-align:center;color:var(--muted)">Tidak ada entri.</div>';
    $$('#kbList .card[data-i]').forEach(function (card) {
      var i = +card.dataset.i;
      card.querySelector('.kb-title').oninput = function (e) { kbData[i].title = e.target.value; };
      card.querySelector('.kb-cat').oninput = function (e) { kbData[i].category = e.target.value; };
      card.querySelector('.kb-content').oninput = function (e) { kbData[i].content = e.target.value; };
      var _kbTopicEl = card.querySelector('.kb-topic');
      if (_kbTopicEl) _kbTopicEl.onchange = function (e) { kbData[i].topic = e.target.value; };  // v1.2.12
      card.querySelector('.kb-del').onclick = function () { kbData.splice(i, 1); renderKb(); };
    });
  }
  function saveKb() {
    api('save_kb', { method: 'POST', body: { kb: kbData } }).then(function (res) {
      if (res.ok) toast('Knowledge base disimpan (' + res.count + ' entri).');
      else toast(res.error || 'Gagal menyimpan.', true);
    });
  }

  /* ---- CSV import: kolom category, question, answer ---- */
  function parseCsv(text) {
    text = String(text).replace(/^\uFEFF/, '');           // buang BOM
    var head = (text.split(/\r\n|\n|\r/)[0] || '');
    var nC = (head.match(/,/g) || []).length,
        nS = (head.match(/;/g) || []).length,
        nT = (head.match(/\t/g) || []).length;
    var delim = ',';
    if (nS >= nC && nS >= nT && nS > 0) delim = ';';
    else if (nT > nC && nT > nS) delim = '\t';
    var rows = [], row = [], field = '', i = 0, inQ = false;
    while (i < text.length) {
      var ch = text[i];
      if (inQ) {
        if (ch === '"') {
          if (text[i + 1] === '"') { field += '"'; i += 2; continue; }
          inQ = false; i++; continue;
        }
        field += ch; i++; continue;
      }
      if (ch === '"') { inQ = true; i++; continue; }
      if (ch === delim) { row.push(field); field = ''; i++; continue; }
      if (ch === '\r') { i++; continue; }
      if (ch === '\n') { row.push(field); rows.push(row); row = []; field = ''; i++; continue; }
      field += ch; i++;
    }
    if (field !== '' || row.length) { row.push(field); rows.push(row); }
    return rows;
  }

  function importKbCsv(file) {
    if (!file) return;
    var reader = new FileReader();
    reader.onerror = function () { toast('Gagal membuka file.', true); };
    reader.onload = function () {
      try {
        var rows = parseCsv(reader.result);
        if (!rows.length) { toast('File CSV kosong.', true); return; }
        var first = rows[0].map(function (c) { return String(c).trim().toLowerCase(); });
        var headerWords = ['category', 'question', 'answer', 'kategori', 'pertanyaan', 'jawaban'];
        var hasHeader = first.some(function (c) { return headerWords.indexOf(c) !== -1; });
        var added = 0, skipped = 0;
        for (var r = hasHeader ? 1 : 0; r < rows.length; r++) {
          var cols = rows[r] || [];
          var category = (cols[0] || '').trim();
          var question = (cols[1] || '').trim();
          var answer = (cols[2] || '').trim();
          if (!category && !question && !answer) continue;   // baris kosong
          if (!answer) { skipped++; continue; }               // wajib ada jawaban
          kbData.unshift({ id: 'kb_' + Date.now() + '_' + r, category: category, title: question, content: answer, topic: '' });
          added++;
        }
        renderKb();
        if (added) {
          var msg = added + ' entri ditambahkan dari CSV — klik "Simpan Perubahan" untuk menyimpan.';
          if (skipped) msg += ' (' + skipped + ' baris dilewati karena kolom answer kosong.)';
          toast(msg);
        } else {
          toast('Tidak ada baris valid. Pastikan urutan kolom: category, question, answer.', true);
        }
      } catch (err) {
        toast('Gagal membaca CSV: ' + (err && err.message ? err.message : 'format tidak dikenali'), true);
      }
    };
    reader.readAsText(file, 'UTF-8');
  }

  function downloadKbTemplate() {
    var csv = '\uFEFF' + 'category,question,answer\r\n' +
      '"Layanan","Apa saja layanan yang Anda tawarkan?","Kami menyediakan layanan konsultasi, pelatihan, dan pendampingan."\r\n' +
      '"Harga","Berapa biaya layanannya?","Biaya menyesuaikan kebutuhan. Silakan hubungi kami untuk penawaran."\r\n' +
      '"Kontak","Bagaimana cara menghubungi tim Anda?","Anda bisa menghubungi kami via WhatsApp pada jam kerja 09.00-17.00 WIB."\r\n';
    var blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'template-knowledge-base.csv';
    document.body.appendChild(a); a.click();
    setTimeout(function () { document.body.removeChild(a); URL.revokeObjectURL(a.href); }, 0);
  }

  /* ====================================================================== *
   *  CONTENT (Reply & Appearance)
   * ====================================================================== */
  var settingsCache = null;
  function loadContent() {
    api('get_settings').then(function (res) {
      if (!res.ok) return;
      settingsCache = res.settings;
      fillContent(res.settings);
    });
    $('#btnAddQuick').onclick = function () { addQuickRow(''); };
    $('#btnSaveContent').onclick = saveContent;
    $('#c_color').oninput = function () { $('#c_color_hex').value = $('#c_color').value; };
    $('#c_color_hex').oninput = function () { var v = $('#c_color_hex').value; if (/^#[0-9a-fA-F]{6}$/.test(v)) $('#c_color').value = v; };

    // v1.1.6+v1.1.9: Avatar event wiring
    document.getElementById('c_avatar_type_emoji').onchange = function () { toggleAvatarRows('emoji'); };
    document.getElementById('c_avatar_type_icon').onchange  = function () { toggleAvatarRows('icon'); };
    document.getElementById('c_avatar_type_image').onchange = function () { toggleAvatarRows('image'); };
    document.getElementById('c_avatar_emoji_picker').onchange = updateEmojiPreview;
    document.getElementById('c_avatar_emoji_custom').oninput = updateEmojiPreview;
    document.getElementById('c_avatar_icon_picker').onchange = updateIconPreview;
    document.getElementById('c_avatar_file').onchange = handleAvatarFile;
    document.getElementById('c_avatar_image_clear').onclick = function () {
      document.getElementById('c_avatar_image').value = '';
      document.getElementById('c_avatar_image_preview').style.display = 'none';
      this.style.display = 'none';
      document.getElementById('c_avatar_file').value = '';
      document.getElementById('c_avatar_image_status').textContent = 'Maks 2 MB · Otomatis di-resize jadi 96×96 px PNG (crop center) · Format: PNG/JPG/WEBP';
      document.getElementById('c_avatar_image_status').style.color = '';
    };
  }

  /**
   * v1.1.6: Client-side avatar resize via Canvas API, then upload.
   *
   * Flow: read file → validate size/type → load as Image → draw on 96×96 canvas
   * (crop center, like CSS background-size:cover) → toBlob PNG → POST to upload_avatar.
   * Server validates again + writes file → returns relative URL.
   */
  function handleAvatarFile(ev) {
    var file = ev.target.files[0];
    var statusEl = document.getElementById('c_avatar_image_status');
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      statusEl.textContent = '✗ Ukuran file melebihi 2 MB.';
      statusEl.style.color = '#c4302b';
      ev.target.value = '';
      return;
    }
    if (!/^image\/(png|jpe?g|webp)$/.test(file.type)) {
      statusEl.textContent = '✗ Format harus PNG, JPG, atau WEBP.';
      statusEl.style.color = '#c4302b';
      ev.target.value = '';
      return;
    }
    statusEl.textContent = 'Memproses gambar…';
    statusEl.style.color = '';
    var reader = new FileReader();
    reader.onload = function (e) {
      var img = new Image();
      img.onload = function () {
        // Crop center to square, then scale to 96×96
        var size = Math.min(img.naturalWidth, img.naturalHeight);
        var sx = (img.naturalWidth - size) / 2;
        var sy = (img.naturalHeight - size) / 2;
        var canvas = document.createElement('canvas');
        canvas.width = 96; canvas.height = 96;
        var ctx = canvas.getContext('2d');
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(img, sx, sy, size, size, 0, 0, 96, 96);
        // Preview immediately
        var previewUrl = canvas.toDataURL('image/png');
        var prev = document.getElementById('c_avatar_image_preview');
        prev.src = previewUrl;
        prev.style.display = '';

        canvas.toBlob(function (blob) {
          var fd = new FormData();
          fd.append('avatar', blob, 'avatar.png');
          var xhr = new XMLHttpRequest();
          xhr.open('POST', 'api/index.php?action=upload_avatar');
          xhr.setRequestHeader('X-Auth-Token', token);
          xhr.onload = function () {
            try {
              var res = JSON.parse(xhr.responseText);
              if (res.ok) {
                document.getElementById('c_avatar_image').value = res.url;
                document.getElementById('c_avatar_image_clear').style.display = '';
                statusEl.textContent = '✓ Tersimpan: ' + res.url + ' · ' + Math.round((res.size || 0)/1024) + ' KB. Klik Simpan untuk apply.';
                statusEl.style.color = '#16a34a';
              } else {
                statusEl.textContent = '✗ ' + (res.error || 'Upload gagal.');
                statusEl.style.color = '#c4302b';
              }
            } catch (e) {
              statusEl.textContent = '✗ Server error (lihat console).';
              statusEl.style.color = '#c4302b';
              console.error(xhr.responseText);
            }
          };
          xhr.onerror = function () {
            statusEl.textContent = '✗ Network error.';
            statusEl.style.color = '#c4302b';
          };
          xhr.send(fd);
        }, 'image/png');
      };
      img.onerror = function () {
        statusEl.textContent = '✗ Gagal memuat gambar.';
        statusEl.style.color = '#c4302b';
      };
      img.src = e.target.result;
    };
    reader.onerror = function () {
      statusEl.textContent = '✗ Gagal membaca file.';
      statusEl.style.color = '#c4302b';
    };
    reader.readAsDataURL(file);
  }
  function fillContent(s) {
    var b = s.bot || {}, a = s.appearance || {};
    $('#c_bot_name').value = b.bot_name || '';
    $('#c_greeting').value = b.greeting || '';
    $('#c_birthday_greeting').value = b.birthday_greeting || '';
    // v1.2.39 fase8: field ucapan ulang tahun hanya relevan kalau WhatsApp
    // Bot aktif (provider apa pun -- Meta atau Fonnte).
    // v1.2.39 fase8b: hanya Fonnte -- Meta menolak teks bebas di luar
    // jendela 24 jam, jadi ucapan ulang tahun tidak bisa diandalkan.
    var _waOnBd = !!(s.whatsapp_api && s.whatsapp_api.enabled && s.whatsapp_api.provider === 'fonnte');
    if ($('#row_birthday_greeting'))  $('#row_birthday_greeting').style.display  = _waOnBd ? '' : 'none';
    if ($('#hint_birthday_greeting')) $('#hint_birthday_greeting').style.display = _waOnBd ? '' : 'none';
    $('#c_prompt').value = b.system_prompt || '';

    // v1.2.3: populate structured fields
    (function fillStructured() {
      if ($('#c_user_address'))   $('#c_user_address').value   = b.user_address   || '';
      if ($('#c_language_style')) $('#c_language_style').value = b.language_style || '';

      // Languages multi-select
      var langs = Array.isArray(b.languages) ? b.languages : [];
      document.querySelectorAll('.c_lang').forEach(function(cb) {
        cb.checked = langs.indexOf(cb.value) !== -1;
      });
      var behaviorRow = document.getElementById('c_lang_behavior_row');
      if (behaviorRow) behaviorRow.style.display = (langs.length > 1) ? '' : 'none';
      if ($('#c_language_prompt_behavior')) $('#c_language_prompt_behavior').value = b.language_prompt_behavior || 'ask_user';

      // Response rules
      var rules = b.response_rules || {};
      if ($('#c_rule_no_asterisk'))  $('#c_rule_no_asterisk').checked  = !!rules.no_asterisk;
      if ($('#c_rule_one_question')) $('#c_rule_one_question').checked = !!rules.one_question_at_a_time;
      if ($('#c_rule_summary'))      $('#c_rule_summary').checked      = !!rules.summary_before_confirm;
      if ($('#c_rule_emoji'))        $('#c_rule_emoji').checked        = !!rules.use_emoji;
      if ($('#c_rule_concise'))      $('#c_rule_concise').checked      = !!rules.concise_response;

      // Fallback behavior
      var fallback = b.fallback_behavior || '';
      document.querySelectorAll('input[name="c_fallback"]').forEach(function(r) {
        r.checked = (r.value === fallback);
      });

      // Wire language checkbox change -> show/hide behavior dropdown
      document.querySelectorAll('.c_lang').forEach(function(cb) {
        cb.onchange = function() {
          var checkedCount = document.querySelectorAll('.c_lang:checked').length;
          document.getElementById('c_lang_behavior_row').style.display = (checkedCount > 1) ? '' : 'none';
        };
      });

      // Wire preview button
      var btn = document.getElementById('btnPreviewPrompt');
      if (btn && !btn.dataset.wired) {
        btn.onclick = previewGeneratedPrompt;
        btn.dataset.wired = 'true';
      }
    })();
    $('#quickRows').innerHTML = '';
    _quickRepliesData = (b.quick_replies || []).slice();
    renderQuickRows();
    $('#c_color').value = a.primary_color || '#140383';
    $('#c_color_hex').value = a.primary_color || '#140383';
    $('#c_position').value = a.position || 'right';

    // v1.1.6+v1.1.9: Avatar — radio type (emoji/icon/image) + 3 picker
    var atype = a.avatar_type
              || (a.avatar_image ? 'image' : (a.avatar_icon_name ? 'icon' : 'emoji'));
    var ae = a.avatar_emoji || '🤖';
    var aiName = a.avatar_icon_name || 'bot';
    var ai = a.avatar_image || '';
    document.getElementById('c_avatar_type_emoji').checked = atype === 'emoji';
    document.getElementById('c_avatar_type_icon').checked  = atype === 'icon';
    document.getElementById('c_avatar_type_image').checked = atype === 'image';
    toggleAvatarRows(atype);

    // Emoji: kalau ada di dropdown preset, pakai; kalau tidak, mode custom
    var picker = document.getElementById('c_avatar_emoji_picker');
    var custom = document.getElementById('c_avatar_emoji_custom');
    var presetVals = [];
    for (var i=0; i<picker.options.length; i++) presetVals.push(picker.options[i].value);
    if (presetVals.indexOf(ae) !== -1) {
      picker.value = ae;
      custom.style.display = 'none';
      custom.value = '';
    } else if (ae) {
      picker.value = '__custom__';
      custom.style.display = '';
      custom.value = ae;
    } else {
      picker.value = '🤖';
    }
    updateEmojiPreview();

    // Icon picker (v1.1.9)
    var iconPicker = document.getElementById('c_avatar_icon_picker');
    var iconOpts = [];
    for (var j=0; j<iconPicker.options.length; j++) iconOpts.push(iconPicker.options[j].value);
    iconPicker.value = iconOpts.indexOf(aiName) !== -1 ? aiName : 'bot';
    updateIconPreview();

    // Image preview kalau ada
    document.getElementById('c_avatar_image').value = ai;
    var imgPrev = document.getElementById('c_avatar_image_preview');
    var clearBtn = document.getElementById('c_avatar_image_clear');
    if (ai) {
      imgPrev.src = ai + (ai.indexOf('?')<0 ? '?t=' + Date.now() : '');
      imgPrev.style.display = '';
      clearBtn.style.display = '';
    } else {
      imgPrev.style.display = 'none';
      clearBtn.style.display = 'none';
    }

    $('#c_offset_bottom').value = a.offset_bottom != null ? a.offset_bottom : 24;
    $('#c_offset_right').value = a.offset_right != null ? a.offset_right : 24;
  }

  function toggleAvatarRows(type) {
    document.getElementById('c_avatar_emoji_row').style.display = type === 'emoji' ? '' : 'none';
    document.getElementById('c_avatar_icon_row').style.display  = type === 'icon'  ? '' : 'none';
    document.getElementById('c_avatar_image_row').style.display = type === 'image' ? '' : 'none';
  }

  function updateEmojiPreview() {
    var picker = document.getElementById('c_avatar_emoji_picker');
    var custom = document.getElementById('c_avatar_emoji_custom');
    var preview = document.getElementById('c_avatar_emoji_preview');
    if (picker.value === '__custom__') {
      custom.style.display = '';
      preview.textContent = custom.value || '🤖';
    } else {
      custom.style.display = 'none';
      preview.textContent = picker.value;
    }
  }

  function updateIconPreview() {
    var picker = document.getElementById('c_avatar_icon_picker');
    var preview = document.getElementById('c_avatar_icon_preview');
    if (picker && preview) preview.innerHTML = ico(picker.value, 28);
  }

  function currentEmojiValue() {
    var picker = document.getElementById('c_avatar_emoji_picker');
    var custom = document.getElementById('c_avatar_emoji_custom');
    return picker.value === '__custom__' ? (custom.value.trim() || '🤖') : picker.value;
  }
  // v1.1.10 fix: array-based quick replies (avoid DOM sync bugs)
  var _quickRepliesData = [];
  function addQuickRow(val) {
    _quickRepliesData.push(val || '');
    renderQuickRows();
  }
  function renderQuickRows() {
    var container = $('#quickRows');
    container.innerHTML = '';
    _quickRepliesData.forEach(function (val, idx) {
      var row = document.createElement('div'); row.className = 'qr';
      var inp = document.createElement('input'); inp.type = 'text'; inp.value = val || '';
      inp.oninput = function () { _quickRepliesData[idx] = this.value; };
      var del = document.createElement('button'); del.type = 'button'; del.innerHTML = ico('x',14);
      del.onclick = function () {
        _quickRepliesData.splice(idx, 1);
        renderQuickRows();
      };
      row.appendChild(inp); row.appendChild(del); container.appendChild(row);
    });
  }
  function collectContent() {
    var quicks = _quickRepliesData.map(function (v) { return String(v || '').trim(); }).filter(Boolean);
    var avatarType = 'emoji';
    if (document.getElementById('c_avatar_type_icon').checked)  avatarType = 'icon';
    if (document.getElementById('c_avatar_type_image').checked) avatarType = 'image';
    return {
      bot: {
        bot_name: $('#c_bot_name').value,
        greeting: $('#c_greeting').value,
        birthday_greeting: $('#c_birthday_greeting').value,
        quick_replies: quicks,
        system_prompt: $('#c_prompt').value,
        // v1.2.3: structured fields
        user_address: ($('#c_user_address') ? $('#c_user_address').value : ''),
        language_style: ($('#c_language_style') ? $('#c_language_style').value : ''),
        languages: Array.prototype.slice.call(document.querySelectorAll('.c_lang:checked')).map(function(cb){return cb.value;}),
        language_prompt_behavior: ($('#c_language_prompt_behavior') ? $('#c_language_prompt_behavior').value : 'ask_user'),
        response_rules: {
          no_asterisk:            ($('#c_rule_no_asterisk')  && $('#c_rule_no_asterisk').checked),
          one_question_at_a_time: ($('#c_rule_one_question') && $('#c_rule_one_question').checked),
          summary_before_confirm: ($('#c_rule_summary')      && $('#c_rule_summary').checked),
          use_emoji:              ($('#c_rule_emoji')        && $('#c_rule_emoji').checked),
          concise_response:       ($('#c_rule_concise')      && $('#c_rule_concise').checked)
        },
        fallback_behavior: (function(){
          var r = document.querySelector('input[name="c_fallback"]:checked');
          return r ? r.value : '';
        })()
      },
      appearance: {
        primary_color: $('#c_color_hex').value || '#140383',
        position: $('#c_position').value,
        avatar_type:      avatarType,
        avatar_emoji:     currentEmojiValue(),
        avatar_icon_name: document.getElementById('c_avatar_icon_picker').value || 'bot',
        avatar_image:     document.getElementById('c_avatar_image').value || '',
        offset_bottom: +$('#c_offset_bottom').value || 24,
        offset_right: +$('#c_offset_right').value || 24
      }
    };
  }
  // v1.2.3: Generate prompt preview (mirror backend buildStructuredPromptPrefix)
  function previewGeneratedPrompt() {
    var data = collectContent();
    var b = data.bot;
    var parts = [];
    // Languages
    if (b.languages && b.languages.length > 1) {
      var langMap = {id:'Bahasa Indonesia', en:'English', zh:'Mandarin', ar:'Arabic', ja:'Japanese'};
      var names = b.languages.map(function(l){return langMap[l]||l;});
      parts.push("BAHASA: Anda mendukung " + names.join(', ') + ".");
      if (b.language_prompt_behavior === 'ask_user') {
        parts.push("Setelah greeting, tanyakan user ingin melanjutkan dalam bahasa apa.");
      } else if (b.language_prompt_behavior === 'auto_detect') {
        parts.push("Deteksi bahasa dari pesan user, respond dalam bahasa yang sama.");
      }
    }
    if (b.user_address) parts.push('Sapa user dengan "' + b.user_address + '".');
    var styleMap = {formal:'Gunakan bahasa formal profesional.', semi_formal:'Gunakan bahasa semi-formal, ramah namun tetap profesional.', casual:'Gunakan bahasa casual friendly, seperti teman.', enthusiastic:'Gunakan bahasa antusias dengan energy tinggi.'};
    if (styleMap[b.language_style]) parts.push(styleMap[b.language_style]);
    var r = b.response_rules || {};
    if (r.no_asterisk)            parts.push("JANGAN pakai tanda * atau ** di jawaban (no markdown formatting).");
    if (r.one_question_at_a_time) parts.push("Tanya hanya 1 pertanyaan per turn, jangan langsung banyak.");
    if (r.summary_before_confirm) parts.push("Buat summary sebelum minta konfirmasi user.");
    if (r.use_emoji)              parts.push("Gunakan emoji ramah secukupnya.");
    if (r.concise_response)       parts.push("Jawaban maksimal 3 kalimat.");
    var fallMap = {
      say_dont_know: "Kalau tidak tahu jawaban dari knowledge base, katakan dengan sopan bahwa Anda belum memiliki info.",
      ask_contact:   'PENTING: Kalau tidak tahu jawaban dari knowledge base, JANGAN bilang "tidak tahu" atau "tidak memiliki info detail". Langsung tanyakan nama dan no HP user untuk dihubungi kembali oleh tim kami.',
      redirect_wa:   "Kalau tidak tahu jawaban, arahkan user untuk chat langsung dengan admin via WhatsApp."
    };
    if (fallMap[b.fallback_behavior]) parts.push(fallMap[b.fallback_behavior]);

    var prefix = parts.join("\n");
    var persona = b.system_prompt || '';
    var final = prefix ? (prefix + "\n\n=== INSTRUKSI TAMBAHAN ===\n" + persona) : persona;

    if (!prefix) {
      alert('Struktur kosong — sistem akan pakai Persona/Instruksi AI existing di textarea.\n\nPreview persona sekarang:\n\n' + (persona.slice(0, 500) + (persona.length > 500 ? '...(truncated)' : '')));
    } else {
      alert('=== GENERATED PROMPT PREVIEW ===\n\n' + final.slice(0, 1500) + (final.length > 1500 ? '\n\n...(truncated for preview)' : ''));
    }
  }

  function saveContent() {
    // v1.2.3: warn kalau textarea system_prompt dikosongkan
    var promptText = ($('#c_prompt').value || '').trim();
    if (promptText === '' && settingsCache && settingsCache.bot && (settingsCache.bot.system_prompt || '').trim() !== '') {
      if (!confirm('Anda mengosongkan "Persona / Instruksi AI" (System Prompt).\n\nInstruksi custom Anda akan hilang. Chatbot akan lebih generic.\n\nLanjutkan simpan?')) return;
    }
    api('save_settings', { method: 'POST', body: { settings: collectContent() } }).then(function (res) {
      if (res.ok) toast('Tersimpan.'); else toast(res.error || 'Gagal menyimpan.', true);
    });
  }

  /* ====================================================================== *
   *  TEST CHATBOT (uses public chat endpoint with live settings)
   * ====================================================================== */
  var testHist = [];
  function initTest() {
    $('#testSend').onclick = testSend;
    $('#testClear').onclick = function () { testHist = []; $('#test-body').innerHTML = ''; };
    $('#testInput').addEventListener('keydown', function (e) { if (e.key === 'Enter') testSend(); });
  }
  function testAdd(role, text) {
    var d = document.createElement('div'); d.className = 'tm ' + role;
    var b = document.createElement('div'); b.className = 'tm-b'; b.textContent = text;
    d.appendChild(b); $('#test-body').appendChild(d); $('#test-body').scrollTop = $('#test-body').scrollHeight; return d;
  }
  function testSend() {
    var v = $('#testInput').value.trim(); if (!v) return;
    $('#testInput').value = '';
    testAdd('user', v); testHist.push({ role: 'user', content: v });
    var t = testAdd('bot', '…');
    // v1.2.4: X-Auth-Token supaya backend detect admin test (bypass chatbot_enabled check)
    fetch(API + '?action=chat', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Auth-Token': localStorage.getItem('dei_token') || '' }, body: JSON.stringify({ message: v, history: testHist.slice(-8), utm: { utm_source: 'dashboard', utm_medium: 'test', page: '/dashboard/test' } }) })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.ok) { t.querySelector('.tm-b').textContent = res.answer; testHist.push({ role: 'assistant', content: res.answer }); }
        else t.querySelector('.tm-b').textContent = res.error || 'Gangguan.';
      })
      .catch(function () { t.querySelector('.tm-b').textContent = 'Koneksi bermasalah.'; });
  }

  /* ====================================================================== *
   *  WIDGET & API (admin only)
   * ====================================================================== */
  // v1.2.36: tampilkan hanya kolom milik penyedia terpilih, supaya tidak ada
  // yang bingung mengisi kolom yang tidak terpakai.
  function waTampilkanBlokPenyedia(prov) {
    var meta = (prov !== 'fonnte');
    $$('.wa-meta-only').forEach(function (el)   { el.style.display = meta ? '' : 'none'; });
    $$('.wa-fonnte-only').forEach(function (el) { el.style.display = meta ? 'none' : ''; });
  }
  function loadWidget() {
    api('get_settings').then(function (res) {
      if (!res.ok) return;
      var s = res.settings, w = s.widget || {}, a = s.api || {};
      $('#w_chatbot').checked = w.chatbot_enabled !== false;
      $('#w_whatsapp').checked = w.whatsapp_enabled !== false;
      $('#w_wa_number').value = w.whatsapp_number || '';
      $('#w_wa_msg').value = w.whatsapp_message || '';
      $('#a_key').value = a.claude_api_key || '';       // masked from server
      $('#a_key').placeholder = a.key_is_set ? '•••• (terisi — kosongkan untuk tidak mengubah)' : 'sk-ant-...';
      $('#a_model').value = a.model || 'claude-haiku-4-5-20251001';
      $('#a_maxtok').value = a.max_tokens || 400;
      $('#a_rate').value = a.rate_limit || 20;
      $('#a_kbmax').value = a.kb_max_results || 5;
      $('#a_loglimit').value = a.log_limit || 500;

      var wa = s.whatsapp_api || {};
      $('#wa_enabled').checked = wa.enabled === true;
      $('#wa_token').value = wa.access_token || '';   // masked from server
      $('#wa_token').placeholder = wa.token_is_set ? '•••• (terisi — kosongkan untuk tidak mengubah)' : 'EAAG...';
      $('#wa_pnid').value = wa.phone_number_id || '';
      $('#wa_verify').value = wa.verify_token || '';
      $('#wa_secret').value = wa.app_secret || '';     // masked from server
      $('#wa_rate').value = wa.rate_limit_per_number || 20;
      $('#wa_ctx').checked = wa.keep_context !== false;
      $('#wa_webhook_url').value = API + '?action=wa_webhook';
      // v1.2.36: penyedia + kolom Fonnte
      var _prov = wa.provider || 'meta';
      $('#wa_provider').value = _prov;
      $('#fon_token').value = wa.fonnte_token || '';   // disamarkan server
      $('#fon_token').placeholder = wa.fonnte_token_is_set
        ? '•••• (terisi — kosongkan untuk tidak mengubah)' : 'token dari panel Fonnte';
      $('#fon_device').value = wa.fonnte_device || '';
      $('#fon_webhook_url').value = wa.fonnte_webhook_key
        ? (API + '?action=wa_webhook_fonnte&key=' + encodeURIComponent(wa.fonnte_webhook_key))
        : '(kunci dibuat otomatis setelah disimpan dengan penyedia Fonnte)';
      waTampilkanBlokPenyedia(_prov);
      $('#wa_provider').onchange = function () { waTampilkanBlokPenyedia(this.value); };
      $('#btnCopyFonWebhook').onclick = function () {
        var f = $('#fon_webhook_url'); f.select();
        copyText(f.value, 'Webhook Fonnte disalin.');
      };

      var tg = s.telegram || {};
      $('#tg_enabled').checked = tg.enabled === true;
      $('#tg_token').value = '';
      $('#tg_token').placeholder = tg.token_is_set ? '•••• (terisi — kosongkan untuk tidak mengubah)' : '123456:ABC-DEF...';
      $('#tg_chatid').value = tg.chat_id || '';
      $('#tg_wa').checked = tg.notify_whatsapp !== false;
      $('#tg_web').checked = tg.notify_web !== false;

      var ho = s.handoff || {};
      $('#ho_enabled').checked = ho.enabled !== false;
      $('#ho_keywords').value = (ho.keywords || []).join('\n');
    });
    $('#btnSaveWidget').onclick = saveWidget;
    $('#btnCopyWebhook').onclick = function () {
      var f = $('#wa_webhook_url'); f.select();
      try { document.execCommand('copy'); toast('URL webhook disalin.'); }
      catch (e) { toast('Salin manual: ' + f.value); }
    };
  }
  function saveWidget() {
    var keyField = $('#a_key').value.trim();
    var apiBlock = {
      model: $('#a_model').value,
      max_tokens: +$('#a_maxtok').value || 400,
      rate_limit: +$('#a_rate').value || 20,
      kb_max_results: +$('#a_kbmax').value || 5,
      log_limit: +$('#a_loglimit').value || 500
    };
    // Only send key if user typed a fresh one (not the masked bullet value)
    if (keyField && keyField.indexOf('•') === -1) apiBlock.claude_api_key = keyField;

    var waBlock = {
      enabled: $('#wa_enabled').checked,
      phone_number_id: $('#wa_pnid').value.trim(),
      verify_token: $('#wa_verify').value.trim(),
      keep_context: $('#wa_ctx').checked,
      rate_limit_per_number: +$('#wa_rate').value || 20,
      provider: $('#wa_provider').value,                                          // v1.2.36
      fonnte_device: $('#fon_device').value.trim(),
      // tersamar atau kosong -> kirim kosong; backend mempertahankan nilai lama
      fonnte_token: ($('#fon_token').value.indexOf('•') !== -1) ? '' : $('#fon_token').value.trim()
    };
    var waToken = $('#wa_token').value.trim();
    if (waToken && waToken.indexOf('•') === -1) waBlock.access_token = waToken;
    var waSecret = $('#wa_secret').value.trim();
    if (waSecret && waSecret.indexOf('•') === -1) waBlock.app_secret = waSecret;

    var tgBlock = {
      enabled: $('#tg_enabled').checked,
      chat_id: $('#tg_chatid').value.trim(),
      notify_whatsapp: $('#tg_wa').checked,
      notify_web: $('#tg_web').checked
    };
    var tgToken = $('#tg_token').value.trim();
    if (tgToken && tgToken.indexOf('•') === -1) tgBlock.bot_token = tgToken;

    var hoBlock = {
      enabled: $('#ho_enabled').checked,
      keywords: $('#ho_keywords').value.split('\n').map(function (k) { return k.trim(); }).filter(function (k) { return k !== ''; })
    };

    var body = { settings: {
      widget: {
        chatbot_enabled: $('#w_chatbot').checked,
        whatsapp_enabled: $('#w_whatsapp').checked,
        whatsapp_number: $('#w_wa_number').value.trim(),
        whatsapp_message: $('#w_wa_msg').value
      },
      api: apiBlock,
      whatsapp_api: waBlock,
      telegram: tgBlock,
      handoff: hoBlock
    } };
    api('save_settings', { method: 'POST', body: body }).then(function (res) {
      if (res.ok) { toast('Konfigurasi tersimpan.'); loaded.widget = false; loadWidget(); }
      else toast(res.error || 'Gagal menyimpan.', true);
    });
  }

  /* ====================================================================== *
   *  USERS (admin only)
   * ====================================================================== */
  // v1.2.2: Profil Saya — self-service password change
  function loadProfile() {
    var user = JSON.parse(localStorage.getItem('dei_user') || '{}');
    if ($('#profileUsername')) $('#profileUsername').textContent = user.username || '-';
    if ($('#profileName'))     $('#profileName').textContent     = user.name || user.username || '-';
    var roleMap = {'super_admin':'Super Admin', 'admin':'Admin', 'wa_agent':'WA Agent'};
    if ($('#profileRole'))     $('#profileRole').textContent     = roleMap[user.role] || user.role || '-';
    if ($('#profileCurrentPw')) $('#profileCurrentPw').value = '';
    if ($('#profileNewPw'))     $('#profileNewPw').value = '';
    if ($('#profileConfirmPw')) $('#profileConfirmPw').value = '';
    // Wire button (idempotent)
    var btn = $('#btnChangePassword');
    if (btn && !btn.dataset.wired) {
      btn.onclick = changeOwnPassword;
      btn.dataset.wired = 'true';
    }
  }
  function changeOwnPassword() {
    var cur = $('#profileCurrentPw').value;
    var newPw = $('#profileNewPw').value;
    var conf = $('#profileConfirmPw').value;
    if (!cur || !newPw || !conf) { toast('Semua field wajib diisi.', true); return; }
    if (newPw !== conf) { toast('Konfirmasi password tidak cocok.', true); return; }
    if (newPw.length < 8) { toast('Password baru minimal 8 karakter.', true); return; }
    if (newPw === cur) { toast('Password baru tidak boleh sama dengan yang lama.', true); return; }
    var btn = $('#btnChangePassword');
    btn.disabled = true;
    btn.textContent = 'Menyimpan...';
    api('update_own_password', {
      method: 'POST',
      body: { current_password: cur, new_password: newPw }
    }).then(function(res) {
      if (!res.ok) {
        toast(res.error || 'Gagal ganti password.', true);
        btn.disabled = false;
        btn.textContent = 'Simpan Password';
        return;
      }
      toast('Password berhasil diganti. Anda akan logout otomatis...');
      setTimeout(function() {
        localStorage.removeItem('dei_token');
        localStorage.removeItem('dei_user');
        location.href = 'login.html';
      }, 2000);
    });
  }

  function loadUsers() {
    ensureCategories(function () { renderUserCategories([]); renderUsers(); });  // v1.2.13
    applyRoleDropdownRestriction();
    $('#btnSaveUser').onclick = saveUser;
    $('#btnResetUser').onclick = resetUserForm;
  }
  // v1.2.6: role-aware user management
  window.ROLE_LABELS_V126 = { super_admin: 'Super Admin', admin: 'Admin', wa_agent: 'WA Agent' };
  function applyRoleDropdownRestriction() {
    var sel = document.getElementById('u_role');
    if (!sel) return;
    if (user.role === 'admin') {
      sel.innerHTML = '<option value="wa_agent">WA Agent — hanya balas chat WhatsApp</option>';
      sel.value = 'wa_agent';
      sel.disabled = true;
    }
  }
  function renderUsers() {
    api('get_users').then(function (res) {
      if (!res.ok) return;
      $('#tblUsers').innerHTML = res.users.map(function (u) {
        return '<tr>' +
          '<td class="mono">' + esc(u.username) + '</td>' +
          '<td>' + esc(u.name) + '</td>' +
          '<td><span class="tag">' + (window.ROLE_LABELS_V126[u.role] || u.role) + '</span></td>' +
          '<td style="text-align:right;white-space:nowrap">' +
            ((user.role === 'super_admin' || (user.role === 'admin' && u.role === 'wa_agent'))
              ? ('<button class="btn ghost sm u-edit" data-u="' + esc(u.username) + '" data-n="' + esc(u.name) + '" data-r="' + esc(u.role) + '" data-cats="' + esc(JSON.stringify(u.categories || [])) + '">Edit</button> ' +
                 (u.username === user.username ? '' : '<button class="btn danger sm u-del" data-u="' + esc(u.username) + '">Hapus</button>'))
              : '<span class="help" style="font-size:11px">read-only</span>') +
          '</td></tr>';
      }).join('');
      $$('.u-edit').forEach(function (b) { b.onclick = function () {
        $('#userFormTitle').textContent = 'Edit Pengguna';
        $('#u_username').value = b.dataset.u; $('#u_username').readOnly = true;
        $('#u_name').value = b.dataset.n; $('#u_role').value = b.dataset.r; $('#u_password').value = '';
        // v1.2.12: populate kategori checkbox
        var editCats = [];
        try { editCats = JSON.parse(b.dataset.cats || '[]'); } catch (e) { editCats = []; }
        renderUserCategories(editCats);   // v1.2.13: rebuild dari daftar dinamis
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }; });
      $$('.u-del').forEach(function (b) { b.onclick = function () {
        if (!confirm('Hapus pengguna "' + b.dataset.u + '"?')) return;
        api('delete_user', { method: 'POST', body: { username: b.dataset.u } }).then(function (r) {
          if (r.ok) { toast('Pengguna dihapus.'); renderUsers(); } else toast(r.error || 'Gagal.', true);
        });
      }; });
    });
  }
  function resetUserForm() {
    $('#userFormTitle').textContent = 'Tambah Pengguna';
    $('#u_username').value = ''; $('#u_username').readOnly = false;
    $('#u_name').value = ''; $('#u_password').value = '';
    $('#u_role').value = (user.role === 'admin') ? 'wa_agent' : 'admin';
    renderUserCategories([]);  // v1.2.13: rebuild kosong
    applyRoleDropdownRestriction();
  }
  function saveUser() {
    var body = {
      username: $('#u_username').value.trim(),
      name: $('#u_name').value.trim(),
      password: $('#u_password').value,
      role: $('#u_role').value,
      categories: Array.prototype.slice.call(document.querySelectorAll('.u_cat:checked')).map(function(c){return c.value;})  // v1.2.12: categories
    };
    if (!body.username) { toast('Username wajib diisi.', true); return; }
    api('save_user', { method: 'POST', body: body }).then(function (res) {
      if (res.ok) { toast('Pengguna disimpan.'); resetUserForm(); renderUsers(); }
      else toast(res.error || 'Gagal menyimpan.', true);
    });
  }

  /* ====================================================================== *
   *  INSTALL (GTM snippet)
   * ====================================================================== */
  function loadInstall() {
    var gtm =
'<!-- DEI AI Chatbot -->\n' +
'<script>\n' +
'  window.DEI_CHATBOT_BASE = "' + SITE_BASE + '";\n' +
'  (function(){var s=document.createElement("script");\n' +
'    s.src=window.DEI_CHATBOT_BASE+"/assets/js/chat-widget.js";\n' +
'    s.defer=true;document.body.appendChild(s);})();\n' +
'<\/script>';
    var direct =
'<script>window.DEI_CHATBOT_BASE="' + SITE_BASE + '";<\/script>\n' +
'<script src="' + SITE_BASE + '/assets/js/chat-widget.js" defer><\/script>';
    $('#gtmCode').textContent = gtm;
    $('#directCode').textContent = direct;
    $('#btnCopyGtm').onclick = function () { copy(gtm, 'Kode GTM disalin.'); };
    $('#btnCopyDirect').onclick = function () { copy(direct, 'Kode disalin.'); };
  }
  function copy(text, msg) {
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(function () { toast(msg); }, fallback);
    else fallback();
    function fallback() {
      var ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta);
      ta.select(); try { document.execCommand('copy'); toast(msg); } catch (e) { toast('Salin manual.', true); }
      ta.remove();
    }
  }

  /* ====================================================================== *
   *  WHATSAPP CONVERSATIONS (handoff inbox)
   * ====================================================================== */
  var waState = { current: null, timer: null, lastAwaiting: -1, convs: [] };

/* ============================================================================
 *  v1.2.0 WA Claim System — Frontend UI
 *  REPLACES: loadWachat, fetchWaConvs, renderWaConvs, renderWaThread
 *  ADDS: filter bar, claim/release/takeover UI, audit log viewer
 * ============================================================================ */

  // Extend waState (existing) — safe to add properties, existing code still works
  // (waState declared elsewhere; if not, this becomes: var waState = window.waState || {...})
  window.waState = window.waState || {};
  waState.filter = waState.filter || 'all';
  waState.counts = waState.counts || { all: 0, mine: 0, unclaimed: 0, others: 0, takeover_requests: 0, today: 0, attention: 0 };
  waState.me = waState.me || '';
  waState.isAdmin = waState.isAdmin || false;
  waState.claimDetails = waState.claimDetails || {}; // number → claim object cache
  waState.currentThreadClaim = null;

  /* ============================================================
   * v1.2.8: web push + PWA subscribe
   * ============================================================ */
  var DEI_VAPID_PUBLIC = 'BCLUf1Mk_6nts_qsCK2Gxw88b2cXTLKZztuo-fZohcrl0oqTh2YIfwd1qVWpb3rXFbC0vropFPzmHtXhzNk6sbg';
  var deiSwReg = null;

  function urlBase64ToUint8Array(base64String) {
    var padding = '='.repeat((4 - base64String.length % 4) % 4);
    var base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    var raw = window.atob(base64);
    var arr = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
    return arr;
  }

  function initPushNotif() {
    var btn = document.getElementById('btnNotif');
    if (!btn) return;

    // Cek support
    if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) {
      btn.style.display = 'none';
      return;
    }

    // Register service worker
    navigator.serviceWorker.register('./sw.js').then(function (reg) {
      deiSwReg = reg;
      updateNotifButton();
    }).catch(function (err) {
      console.warn('SW register gagal:', err);
    });

    btn.onclick = function () {
      if (Notification.permission === 'denied') {
        toast('Notifikasi diblokir. Aktifkan lewat setting browser.', true);
        return;
      }
      if (!deiSwReg) { toast('Service worker belum siap, coba lagi.', true); return; }

      // Cek sudah subscribe atau belum
      deiSwReg.pushManager.getSubscription().then(function (sub) {
        if (sub) {
          // Sudah aktif → unsubscribe (matikan)
          var endpoint = sub.endpoint;
          sub.unsubscribe().then(function () {
            api('delete_push_subscription', { method: 'POST', body: { endpoint: endpoint } });
            toast('Notifikasi dimatikan.');
            updateNotifButton();
          });
        } else {
          // Belum → minta permission + subscribe
          Notification.requestPermission().then(function (perm) {
            if (perm !== 'granted') { toast('Izin notifikasi ditolak.', true); return; }
            deiSwReg.pushManager.subscribe({
              userVisibleOnly: true,
              applicationServerKey: urlBase64ToUint8Array(DEI_VAPID_PUBLIC)
            }).then(function (sub) {
              api('save_push_subscription', {
                method: 'POST',
                body: { subscription: sub.toJSON(), ua: navigator.userAgent }
              }).then(function (res) {
                if (res.ok) { toast('Notifikasi aktif!'); updateNotifButton(); }
                else toast(res.error || 'Gagal simpan subscription.', true);
              });
            }).catch(function (err) {
              console.error('Subscribe gagal:', err);
              toast('Gagal aktifkan notifikasi.', true);
            });
          });
        }
      });
    };
  }

  function updateNotifButton() {
    var btn = document.getElementById('btnNotif');
    if (!btn || !deiSwReg) return;
    deiSwReg.pushManager.getSubscription().then(function (sub) {
      if (sub && Notification.permission === 'granted') {
        btn.innerHTML = ico('bell',15) + ' Notif Aktif';
        btn.style.opacity = '1';
      } else {
        btn.innerHTML = ico('bell-off',15) + ' Notifikasi';
        btn.style.opacity = '0.7';
      }
    });
  }

  /* ---- Web Conversations (v1.2.45) ---- */
  var webState = { convs: [], current: null, timer: null };

  function loadWebchat() {
    var wrap = document.querySelector('#panel-webchat .wachat-wrap');
    if (wrap) wrap.classList.remove('showing-thread');
    if (window.scrollTo) window.scrollTo(0, 0);
    fetchWebConvs();
    if ($('#webBackBtn')) $('#webBackBtn').onclick = function () {
      var w = document.querySelector('#panel-webchat .wachat-wrap');
      if (w) w.classList.remove('showing-thread');
    };
    if (webState.timer) clearInterval(webState.timer);
    webState.timer = setInterval(function () {
      if (!$('#panel-webchat').classList.contains('active')) return;
      fetchWebConvs(true).then(function () {
        if (webState.current) fetchWebThread(webState.current, true);
      });
    }, 8000);
  }

  function fetchWebConvs(silent) {
    var list = $('#webConvList');
    if (!silent && list) list.innerHTML = '<div style="padding:16px;color:var(--muted)">Memuat…</div>';
    return api('web_conversations_admin')
      .then(function (res) {
        if (!res.ok) return;
        webState.convs = res.conversations || [];
        renderWebConvs(webState.convs);
      })
      .catch(function () {
        if (!silent && list) list.innerHTML = '<div style="padding:16px;color:var(--err)">Gagal memuat.</div>';
      });
  }

  function renderWebConvs(convs) {
    var list = $('#webConvList');
    if (!list) return;
    if (!convs.length) {
      list.innerHTML = '<div style="padding:24px;color:var(--muted);text-align:center">Belum ada percakapan web.</div>';
      return;
    }
    list.innerHTML = '';
    convs.forEach(function (c) {
      var preview = c.last_message
        ? '<b style="color:var(--txt)">Pengunjung:</b> ' + esc(c.last_message)
        : (c.last_answer ? '<b style="color:var(--txt)">Bot:</b> ' + esc(c.last_answer) : '');
      var msgCount = c.message_count || 0;
      var row = document.createElement('div');
      row.className = 'wa-conv-row' + (webState.current === c.id ? ' active' : '');
      row.innerHTML =
        '<div class="wa-conv-left">' +
          '<div class="wa-conv-av">' + ico('monitor-smartphone', 18) + '</div>' +
        '</div>' +
        '<div class="wa-conv-mid">' +
          '<div class="wa-conv-name">' + esc(c.title || 'Percakapan') + '</div>' +
          '<div class="wa-conv-preview">' + (preview || '<i style="color:var(--muted)">Belum ada pesan</i>') + '</div>' +
        '</div>' +
        '<div class="wa-conv-right">' +
          '<div class="wa-conv-ts">' + waConvTimeInfo(c.last_ts || c.created_at).label + '</div>' +
          '<div style="font-size:11px;color:var(--muted)">' + msgCount + ' pesan</div>' +
        '</div>';
      row.onclick = function () { selectWebConv(c.id); };
      list.appendChild(row);
    });
  }

  function selectWebConv(convId) {
    webState.current = convId;
    var wrap = document.querySelector('#panel-webchat .wachat-wrap');
    if (wrap) wrap.classList.add('showing-thread');
    fetchWebThread(convId);
  }

  function fetchWebThread(convId, silent) {
    var head = $('#webThreadHead');
    var body = $('#webThreadBody');
    if (!silent && head) head.innerHTML = '<span style="color:var(--muted)">Memuat…</span>';
    if (!silent && body) body.innerHTML = '';
    return api('web_thread_admin', { query: '&conversation_id=' + encodeURIComponent(convId) })
      .then(function (res) {
        if (!res.ok) return;
        var conv = res.conversation || {};
        var msgs = res.messages || [];
        if (head) {
          head.innerHTML =
            '<div style="display:flex;align-items:center;gap:10px;padding:12px 14px;border-bottom:1px solid var(--border)">' +
              '<div>' + ico('monitor-smartphone', 20) + '</div>' +
              '<div style="flex:1;min-width:0">' +
                '<div style="font-weight:600;font-size:15px">' + esc(conv.title || 'Percakapan') + '</div>' +
                '<div style="font-size:12px;color:var(--muted)">Visitor: ' + esc(conv.visitor_id || '-') + ' &middot; Dibuat: ' + esc(conv.created_at || '') + '</div>' +
              '</div>' +
            '</div>';
        }
        if (body) {
          body.innerHTML = '';
          msgs.forEach(function (m) {
            var bubble = document.createElement('div');
            bubble.className = 'wa-msg ' + (m.role === 'user' ? 'wa-msg-in' : 'wa-msg-out');
            bubble.innerHTML =
              '<div class="wa-msg-bubble">' +
                '<div class="wa-msg-text">' + esc(m.content || '') + '</div>' +
                '<div class="wa-msg-ts">' + esc(m.ts || '') + '</div>' +
              '</div>';
            body.appendChild(bubble);
          });
          body.scrollTop = body.scrollHeight;
        }
        // refresh list to highlight active
        renderWebConvs(webState.convs);
      })
      .catch(function () {
        if (head) head.innerHTML = '<span style="color:var(--err)">Gagal memuat.</span>';
      });
  }

  function loadWachat() {
    // v1.2.39 fase7: membuka menu "Percakapan WA" harus diperlakukan sama
    // dengan menekan tombol Back di mobile -- balik ke DAFTAR percakapan,
    // bukan nyangkut di thread terakhir yang dibuka (lengkap dengan posisi
    // scroll-nya). Tombol Back sudah menghapus kelas ini; loadWachat()
    // sebelumnya tidak, jadi tampilan tetap menempel di thread.
    var _wrapReset = document.querySelector('.wachat-wrap');
    if (_wrapReset) _wrapReset.classList.remove('showing-thread');
    if (window.scrollTo) window.scrollTo(0, 0);
    // Filter bar (kalau belum di-render)
    ensureFilterBar();
    fetchWaConvs();
    $('#waReplySend').onclick = function () { if (waState.current) sendWaManual(waState.current); };
    initPushNotif();  // v1.2.8: init push notif saat buka menu WA
    // v1.2.7: back button — mobile balik ke list
    if ($('#waBackBtn')) $('#waBackBtn').onclick = function () {
      var wrap = document.querySelector('.wachat-wrap');
      if (wrap) wrap.classList.remove('showing-thread');
    };
    $('#waReplyInput').addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && waState.current && !$('#waReplySend').disabled) sendWaManual(waState.current);
    });
    if (waState.timer) clearInterval(waState.timer);
    waState.timer = setInterval(function () {
      if (!$('#panel-wachat').classList.contains('active')) return;
      // v1.2.39 fase2d: tunggu fetchWaConvs selesai dulu (waState.convs
      // terisi data baru) baru gambar ulang thread -- kalau paralel,
      // thread bisa baca data lama dan tag/dropdown kelihatan balik ke
      // nilai sebelumnya beberapa detik setelah diubah, tanpa ada yang
      // menyentuh dropdown-nya lagi.
      fetchWaConvs(true).then(function () {
        if (waState.current) fetchWaThread(waState.current, true);
      });
    }, 6000);
  }

  function ensureFilterBar() {
    if ($('#waFilterBar')) return; // sudah render
    var bar = document.createElement('div');
    bar.id = 'waFilterBar';
    bar.className = 'wa-filter-bar';
    bar.innerHTML =
      '<button class="wa-filter-btn active" data-filter="all">All <span class="wa-filter-count" data-count="all">0</span></button>' +
      '<button class="wa-filter-btn" data-filter="today">Hari Ini <span class="wa-filter-count" data-count="today">0</span></button>' +
      '<button class="wa-filter-btn" data-filter="attention">Perlu Perhatian <span class="wa-filter-count" data-count="attention">0</span></button>' +
      '<button class="wa-filter-btn" data-filter="mine">Punya Saya <span class="wa-filter-count" data-count="mine">0</span></button>' +
      '<button class="wa-filter-btn" data-filter="unclaimed">Unclaimed <span class="wa-filter-count" data-count="unclaimed">0</span></button>' +
      '<button class="wa-filter-btn" data-filter="others">Punya Agent Lain <span class="wa-filter-count" data-count="others">0</span></button>' +
      '<button class="wa-filter-btn" data-filter="takeover_requests">Take-over Requests <span class="wa-filter-count" data-count="takeover_requests">0</span></button>' +
      (waState.isAdmin === false ? '' : '<button class="wa-filter-btn wa-export-contacts" title="Unduh semua kontak WA (.vcf)">' + ico('download',14) + ' Ekspor Kontak</button>') +
      (waState.isAdmin === false ? '' : '<button class="wa-filter-btn wa-audit-toggle" style="margin-left:auto" title="Lihat audit log">' + ico('clipboard-list',14) + ' Audit</button>');
    // Insert BEFORE .wachat-wrap
    var wrap = $('#panel-wachat .wachat-wrap');
    wrap.parentNode.insertBefore(bar, wrap);
    // Audit log container
    var auditBox = document.createElement('div');
    auditBox.id = 'waAuditBox';
    auditBox.className = 'wa-audit-box';
    auditBox.style.display = 'none';
    wrap.parentNode.insertBefore(auditBox, wrap);
    // Event listeners
    $$('#waFilterBar .wa-filter-btn').forEach(function (btn) {
      if (btn.classList.contains('wa-audit-toggle')) {
        btn.onclick = toggleAuditLog;
      } else if (btn.classList.contains('wa-export-contacts')) {   // v1.2.19
        btn.onclick = exportWaContacts;
      } else {
        btn.onclick = function () {
          waState.filter = btn.dataset.filter;
          $$('#waFilterBar .wa-filter-btn').forEach(function (b) { b.classList.remove('active'); });
          btn.classList.add('active');
          fetchWaConvs();
        };
      }
    });
  }

  function fetchWaConvs(silent) {
    var query = '&filter=' + encodeURIComponent(waState.filter || 'all');
    // v1.2.39: return promise-nya supaya pemanggil bisa .then() menunggu
    // waState.convs benar-benar terisi data terbaru sebelum lanjut.
    return api('wa_conversations_v2', { query: query }).then(function (res) {
      if (!res || !res.ok) {
        // Fallback to old endpoint jika v2 error (backward compat)
        fetchWaConvsLegacy(silent);
        return;
      }
      waState.convs = res.conversations || [];
      waState.counts = res.counts || waState.counts;
      waState.me = res.me || '';
      waState.isAdmin = !!res.is_admin;
      // Rebuild filter bar setelah tahu role user (hide Audit btn untuk non-admin)
      var oldBar = document.getElementById('waFilterBar');
      if (oldBar) oldBar.remove();
      var oldAuditBox = document.getElementById('waAuditBox');
      if (oldAuditBox) oldAuditBox.remove();
      ensureFilterBar();
      // Cache claim per number
      waState.claimDetails = {};
      waState.convs.forEach(function (c) {
        if (c.claim) waState.claimDetails[c.number] = c.claim;
      });
      updateFilterCounts();
      renderWaConvs();
      // Beep detection
      var awaiting = waState.convs.filter(function (c) { return c.awaiting || c.status === 'takeover_requested'; }).length;
      if (silent && waState.lastAwaiting >= 0 && awaiting > waState.lastAwaiting) playBeep();
      waState.lastAwaiting = awaiting;
      // Update sidebar badge
      updateSidebarBadge(res.counts);
      // Refresh audit log kalau sedang open
      if ($('#waAuditBox') && $('#waAuditBox').style.display !== 'none') {
        refreshAuditLog();
      }
    });
  }

  function fetchWaConvsLegacy(silent) {
    api('wa_conversations').then(function (res) {
      if (!res || !res.ok) {
        $('#waConvList').innerHTML = '<div style="padding:16px;color:#b91c1c;font-size:13px">Gagal memuat: ' + esc((res && res.error) || 'tidak diketahui') + '</div>';
        return;
      }
      waState.convs = res.conversations || [];
      renderWaConvs();
      var awaiting = waState.convs.filter(function (c) { return c.awaiting; }).length;
      if (silent && waState.lastAwaiting >= 0 && awaiting > waState.lastAwaiting) playBeep();
      waState.lastAwaiting = awaiting;
    });
  }

  function updateFilterCounts() {
    var c = waState.counts || {};
    ['all', 'mine', 'unclaimed', 'others', 'takeover_requests', 'today', 'attention'].forEach(function (f) {
      var el = $('#waFilterBar .wa-filter-count[data-count="' + f + '"]');
      if (el) {
        el.textContent = c[f] || 0;
        el.style.display = (c[f] > 0 || f === 'all') ? 'inline-block' : 'none';
      }
    });
  }

  function updateSidebarBadge(counts) {
    var tabBtn = document.querySelector('[data-tab="wachat"]');
    if (!tabBtn) return;
    var badge = tabBtn.querySelector('.wa-sidebar-badge');
    var pending = (counts.unclaimed || 0) + (counts.takeover_requests || 0);
    if (pending > 0) {
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'wa-sidebar-badge';
        tabBtn.appendChild(badge);
      }
      badge.textContent = pending;
    } else if (badge) {
      badge.remove();
    }
  }

  /* ---- v1.2.16: label waktu untuk daftar percakapan ------------------- */
  // Kembalikan { label, today } untuk ditampilkan di sidebar.
  //   hari ini -> "14:23" (today=true)  |  kemarin -> "Kemarin"  |  lama -> "16 Jul"
  function waConvTimeInfo(ts) {
    var key = waDateKey(ts);
    if (!key) return { label: '', today: false };
    var p = key.split('-');
    if (p.length !== 3) return { label: '', today: false };

    var d = new Date(+p[0], +p[1] - 1, +p[2]);
    if (isNaN(d.getTime())) return { label: '', today: false };
    var today = new Date();
    today.setHours(0, 0, 0, 0);
    var diffHari = Math.round((today.getTime() - d.getTime()) / 86400000);

    if (diffHari === 0) {
      var jam = String(ts).split(' ')[1] || '';
      return { label: jam.slice(0, 5), today: true };   // "14:23"
    }
    if (diffHari === 1) return { label: 'Kemarin', today: false };

    var bulanPendek = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];
    var lbl = d.getDate() + ' ' + bulanPendek[d.getMonth()];
    if (d.getFullYear() !== new Date().getFullYear()) lbl += ' ' + d.getFullYear();
    return { label: lbl, today: false };
  }
  /* ---- v1.2.19: kontak WA — ekspor & koreksi nama --------------------- */
  // Unduhan dibangun di browser dari respons JSON, supaya token tidak pernah
  // muncul di URL (kalau pakai tautan langsung, token ikut tercatat di riwayat).
  function exportWaContacts() {
    api('export_contacts').then(function (res) {
      if (!res || !res.ok) { toast((res && res.error) || 'Gagal mengekspor.', true); return; }
      if (!res.count) { toast('Belum ada kontak untuk diekspor.', true); return; }
      try {
        var blob = new Blob([res.vcf], { type: 'text/vcard;charset=utf-8' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        var d = new Date();
        var stamp = d.getFullYear() + String(d.getMonth() + 1).padStart(2, '0') + String(d.getDate()).padStart(2, '0');
        a.href = url;
        a.download = 'kontak-wa-' + stamp + '.vcf';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
        toast(res.count + ' kontak diunduh. Buka file .vcf di HP untuk mengimpor.');
      } catch (e) {
        toast('Gagal membuat file unduhan.', true);
      }
    });
  }
  // Koreksi nama: kosongkan untuk kembali memakai nama profil WhatsApp.
  function editWaContactName(num) {
    var conv = (waState.convs || []).filter(function (c) { return c.number === num; })[0];
    var sekarang = (conv && conv.name) || '';
    var baru = prompt('Nama untuk +' + num + '\n(kosongkan untuk memakai nama profil WhatsApp)', sekarang);
    if (baru === null) return;
    api('save_contact', { method: 'POST', body: { number: num, name: baru.trim() } }).then(function (r) {
      if (r && r.ok) { toast('Nama disimpan.'); fetchWaConvs(); if (waState.current === num) fetchWaThread(num); }
      else toast((r && r.error) || 'Gagal menyimpan.', true);
    });
  }
  var waFilterLabelExtra = { today: 'Hari Ini', attention: 'Perlu Perhatian' };  // v1.2.17
  function renderWaConvs() {
    if (!waState.convs.length) {
      var msg = 'Belum ada percakapan';
      if (waState.filter && waState.filter !== 'all') {
        var labels = { mine: 'Punya Saya', unclaimed: 'Unclaimed', others: 'Punya Agent Lain', takeover_requests: 'Take-over Requests' };
        msg = 'Tidak ada di filter "' + (labels[waState.filter] || waFilterLabelExtra[waState.filter] || waState.filter) + '"';
      }
      $('#waConvList').innerHTML = '<div style="padding:16px;color:var(--muted)">' + msg + '</div>';
      return;
    }
    $('#waConvList').innerHTML = waState.convs.map(function (c) {
      var badge = statusBadgeHtml(c);
      var awa = c.awaiting ? ' <span class="tag" style="background:#fecaca;color:#991b1b">menunggu</span>' : '';
      // v1.2.17: tanda kalau butuh manusia (bot gagal / menggantung) & belum dibalas manual
      var attn = c.needs_attention ? ' <span class="tag" style="background:#fee2e2;color:#b91c1c">' + ico('triangle-alert',12) + ' perlu perhatian</span>' : '';
      var bg = (c.number === waState.current) ? 'background:var(--brand-soft);' : '';
      // v1.2.16: waktu aktivitas terakhir + pembeda visual hari ini vs lama
      var t = waConvTimeInfo(c.last_ts);
      var accent = t.today ? 'border-left:3px solid var(--brand);' : 'border-left:3px solid transparent;';
      var timeStyle = t.today
        ? 'font-size:12px;font-weight:600;color:var(--brand);white-space:nowrap'
        : 'font-size:12px;color:var(--muted);white-space:nowrap';
      var timeHtml = t.label
        ? '<span style="' + timeStyle + '">' + esc(t.label) + '</span>'
        : '';
      // v1.2.19: tampilkan nama kalau ada; nomor jadi baris kecil di bawahnya
      var judul = c.name ? esc(c.name) : ('+' + esc(c.number));
      var subNomor = c.name ? '<div style="font-size:11px;color:var(--muted)">+' + esc(c.number) + '</div>' : '';
      // v1.2.39: badge tag kontak (stage + VIP kalau ada)
      var stageBadge = ' ' + contactStageBadgeHtml(c.stage, c.vip, ';margin-left:2px');
      return '<div class="wa-conv" data-num="' + esc(c.number) + '" style="' + bg + accent + '">' +
        '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px">' +
          '<span style="font-weight:600">' + judul + '</span>' + timeHtml +
        '</div>' + subNomor +
        '<div style="font-size:13px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + esc(c.last_q || c.last_text || '') + '</div>' +
        '<div style="margin-top:5px">' + badge + awa + attn + stageBadge + '</div></div>';
    }).join('');
    $$('#waConvList .wa-conv').forEach(function (el) {
      el.onclick = function () { selectWaConv(el.dataset.num); };
    });
  }

  function statusBadgeHtml(c) {
    var s = c.status || (c.mode === 'human' ? 'human_unclaimed' : 'bot');
    var isMine = c.claim && c.claim.agent_username === waState.me;
    switch (s) {
      case 'bot':
        return '<span class="tag" style="background:#dbeafe;color:#1e40af">' + ico('bot',13) + ' Bot</span>';
      case 'claimed':
        return isMine
          ? '<span class="tag" style="background:#d1fae5;color:#065f46">' + ico('user-round',13) + ' Saya</span>'
          : '<span class="tag" style="background:#fde68a;color:#92400e">' + ico('user-round',13) + ' ' + esc(c.claim.agent_username) + '</span>';
      case 'takeover_requested':
        var req = c.claim && c.claim.takeover_request ? c.claim.takeover_request.requester : '?';
        return '<span class="tag" style="background:#fed7aa;color:#9a3412">' + ico('clock-3',12) + ' Take-over req dari ' + esc(req) + '</span>';
      case 'human_unclaimed':
        return '<span class="tag" style="background:#e5e7eb;color:#374151">' + ico('user-round',13) + ' Mode manual</span>';
      default:
        return '<span class="tag">' + esc(s) + '</span>';
    }
  }

  function selectWaConv(num) {
    waState.current = num; renderWaConvs(); fetchWaThread(num);
    // v1.2.7: mobile show thread (hide list)
    var wrap = document.querySelector('.wachat-wrap');
    if (wrap) wrap.classList.add('showing-thread');
  }

  function fetchWaThread(num, silent) {
    api('wa_thread', { query: '&number=' + encodeURIComponent(num) }).then(function (res) {
      if (!res || !res.ok) return;
      if (waState.current !== num) return;
      renderWaThread(res);
    });
  }

  function waBubble(text, kind, ts) {
    var st = kind === 'in' ? 'align-self:flex-start;background:#fff;border:1px solid var(--line);color:var(--ink)'
      : kind === 'manual' ? 'align-self:flex-end;background:#dcfce7;color:#14532d'
      : 'align-self:flex-end;background:var(--brand);color:#fff';
    var who = kind === 'manual' ? ' · admin' : kind === 'bot' ? ' · bot' : '';
    return '<div style="max-width:78%;' + st + ';padding:8px 12px;border-radius:12px;margin:4px 0;white-space:pre-wrap;font-size:14px;line-height:1.45">' +
      esc(text) + '<div style="font-size:10px;opacity:.65;margin-top:4px">' + esc((ts || '').slice(11, 16)) + who + '</div></div>';
  }

  /* ---- v1.2.15: pemisah tanggal di thread WA ------------------------- */
  // Ambil bagian tanggal dari ts 'Y-m-d H:i:s' -> 'Y-m-d' (kunci pembanding)
  function waDateKey(ts) {
    return String(ts || '').split(' ')[0] || '';
  }
  // Label ramah: Hari ini / Kemarin / 16 Juli 2026
  function waDateLabel(key) {
    if (!key) return '';
    var p = key.split('-');
    if (p.length !== 3) return key;
    var d = new Date(+p[0], +p[1] - 1, +p[2]);
    if (isNaN(d.getTime())) return key;
    var today = new Date();
    today.setHours(0, 0, 0, 0);
    var diffHari = Math.round((today.getTime() - d.getTime()) / 86400000);
    if (diffHari === 0) return 'Hari ini';
    if (diffHari === 1) return 'Kemarin';
    var bulan = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'];
    return d.getDate() + ' ' + bulan[d.getMonth()] + ' ' + d.getFullYear();
  }
  function waDateSepHtml(label) {
    return '<div style="display:flex;justify-content:center;margin:14px 0 10px">' +
           '<span style="background:#e5e7eb;color:#374151;font-size:12px;padding:4px 12px;border-radius:12px">' +
           esc(label) + '</span></div>';
  }
  function renderWaThread(res) {
    var num = res.number;
    var claim = waState.claimDetails[num] || null;
    waState.currentThreadClaim = claim;
    var isMine = claim && claim.agent_username === waState.me;
    var hasTakeoverReq = claim && claim.takeover_request;

    // Build action buttons based on claim state + user role
    var actionBtns = '';
    if (!claim) {
      // Unclaimed → Claim button
      actionBtns = '<button class="btn" id="waClaimBtn" style="padding:7px 14px;font-size:13px">' + ico('hand',14) + ' Claim</button>';
    } else if (isMine) {
      // Mine → Release + (kalau ada takeover req dari orang lain) Approve/Deny
      if (hasTakeoverReq) {
        actionBtns =
          '<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">' +
          '<span class="tag" style="background:#fed7aa;color:#9a3412;padding:5px 9px">' + ico('clock-3',12) + ' ' + esc(claim.takeover_request.requester) + ' minta take-over' +
          (claim.takeover_request.reason ? ': "' + esc(claim.takeover_request.reason) + '"' : '') + '</span>' +
          '<button class="btn ghost" id="waTakeoverDenyBtn" style="padding:6px 12px;font-size:12px">Tolak</button>' +
          '<button class="btn" id="waTakeoverApproveBtn" style="padding:6px 12px;font-size:12px">Setujui</button>' +
          '<button class="btn ghost" id="waReleaseBtn" style="padding:6px 12px;font-size:12px">' + ico('corner-up-left',14) + ' Release</button>' +
          '</div>';
      } else {
        actionBtns = '<button class="btn ghost" id="waReleaseBtn" style="padding:7px 14px;font-size:13px">' + ico('corner-up-left',14) + ' Release (kembali ke bot)</button>';
      }
    } else {
      // Owned by someone else
      var ownerLabel = '<span style="color:var(--muted);font-size:13px">Dikelola oleh <strong>' + esc(claim.agent_username) + '</strong></span>';
      if (waState.isAdmin) {
        actionBtns = ownerLabel +
          ' <button class="btn ghost" id="waAdminTakeoverBtn" style="padding:6px 12px;font-size:12px;margin-left:8px">' + ico('wrench',13) + ' Admin Take-over</button>' +
          ' <button class="btn ghost" id="waReleaseBtn" style="padding:6px 12px;font-size:12px">' + ico('corner-up-left',14) + ' Release</button>';
      } else {
        // wa_agent role → Request Take-over
        if (hasTakeoverReq && claim.takeover_request.requester === waState.me) {
          var secondsLeft = Math.max(0, 300 - Math.floor((Date.now() / 1000) - claim.takeover_request.requested_at));
          actionBtns = ownerLabel +
            ' <span class="tag" style="background:#fed7aa;color:#9a3412;margin-left:8px">' + ico('clock-3',12) + ' Request Anda pending (' + secondsLeft + 's tersisa)</span>';
        } else if (hasTakeoverReq) {
          actionBtns = ownerLabel + ' <span class="tag" style="background:#e5e7eb;color:#374151;margin-left:8px">Ada request take-over pending dari ' + esc(claim.takeover_request.requester) + '</span>';
        } else {
          actionBtns = ownerLabel +
            ' <button class="btn ghost" id="waRequestTakeoverBtn" style="padding:6px 12px;font-size:12px;margin-left:8px">' + ico('hand',13) + ' Minta Take-over</button>';
        }
      }
    }

    // v1.2.19: nama kontak (dari daftar percakapan) + tombol koreksi
    // v1.2.39 fase2e: bandingkan sebagai String -- wa_conversations_v2
    // mengembalikan "number" sebagai JSON Number (tanpa kutip), sementara
    // res.number di sini bisa jadi String. === akan SELALU false kalau
    // tipenya beda walau nilainya sama, bikin _konv selalu undefined dan
    // stage selalu fallback ke 'new'. Ini akar masalah dropdown "balik ke
    // New" -- bukan soal urutan fetch seperti dugaan sebelumnya.
    var _konv = (waState.convs || []).filter(function (c) { return String(c.number) === String(res.number); })[0];
    var _nama = (_konv && _konv.name) || '';
    var _judulThread = _nama
      ? '<strong>' + esc(_nama) + '</strong> <span style="color:var(--muted);font-size:12px">+' + esc(res.number) + '</span>'
      : '<strong>+' + esc(res.number) + '</strong>';
    // v1.2.21: jalan masuk ke Leads dari thread — supaya percakapan lama pun
    // bisa ditarik jadi lead (kartu otomatis hanya terbentuk saat ada pesan baru).
    var _leadLink = '';
    if (_konv && _konv.has_lead) {
      // v1.2.29: agent boleh membuka kartu yang sudah ada
      _leadLink = ' <a href="#" id="waOpenLead" style="font-size:12px">' + ico('clipboard-list',13) + ' Lihat lead</a>';
    } else if (waState.isAdmin !== false) {
      // membuat kartu baru memakai kuota klien -> admin saja
      _leadLink = ' <a href="#" id="waMakeLead" style="font-size:12px">' + ico('clipboard-list',13) + ' Analisa jadi lead</a>';
    }
    // v1.2.39 fase2f: baris kedua kepala thread -- status chat (pakai ulang
    // statusBadgeHtml yang sama dengan daftar percakapan) + kategori kontak
    // (dropdown, diberi label supaya beda jelas dari status chat) + VIP
    // (tombol toggle icon-only, bukan checkbox+emoji lagi).
    var _stageNow = (_konv && _konv.stage) || 'new';
    var _vipNow = !!(_konv && _konv.vip);
    var _stageOpts = contactStageOptionsHtml(_stageNow);
    var _statusBadge = _konv ? statusBadgeHtml(_konv) : '';
    var _awaBadge = (_konv && _konv.awaiting) ? ' <span class="tag" style="background:#fecaca;color:#991b1b">menunggu</span>' : '';
    var _attnBadge = (_konv && _konv.needs_attention) ? ' <span class="tag" style="background:#fee2e2;color:#b91c1c">' + ico('triangle-alert',12) + ' perlu perhatian</span>' : '';
    var _vipBtnStyle = _vipNow
      ? 'background:#fef9c3;color:#92400e;border:1px solid #fbbf24'
      : 'background:transparent;color:var(--muted);border:1px solid var(--line)';
    var _metaRow =
      '<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:6px;font-size:12px">' +
        _statusBadge + _awaBadge + _attnBadge +
        '<span style="color:var(--muted);margin:0 2px">&middot;</span>' +
        '<span style="color:var(--muted)">Lead Rating:</span>' +
        '<select id="waStageSelect" style="border-radius:6px;padding:2px 4px;font-size:11px;border:1px solid var(--line);width:118px">' + _stageOpts + '</select>' +
        '<button type="button" id="waVipToggle" data-vip="' + (_vipNow ? '1' : '0') + '" title="' + (_vipNow ? 'VIP \u2014 klik untuk hapus tanda' : 'Tandai sebagai kontak VIP') + '" style="' + _vipBtnStyle + ';border-radius:6px;padding:3px 7px;display:' + (_stageNow === 'active_customer' ? 'inline-flex' : 'none') + ';align-items:center;gap:3px;cursor:pointer">' + ico('star',13) + ' VIP</button>' +
      '</div>';
    $('#waThreadHead').innerHTML =
      '<div>' +
      '<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">' +
      '<span>' + _judulThread + ' <a href="#" id="waEditName" title="Ubah nama" style="text-decoration:none;font-size:12px">' + ico('pen-tool',12) + '</a>' + _leadLink + '</span>' +
      '<div>' + actionBtns + '</div>' +
      '</div>' +
      _metaRow +
      '</div>';

    // Attach event handlers
    if ($('#waEditName')) $('#waEditName').onclick = function (ev) { ev.preventDefault(); editWaContactName(num); };  // v1.2.19
    // v1.2.39 fase2f: dropdown kategori + tombol toggle VIP
    if ($('#waStageSelect')) {
      $('#waStageSelect').onchange = function () {
        var stage = this.value;
        var vipBtn = $('#waVipToggle');
        var vip = (stage === 'active_customer') ? !!(vipBtn && vipBtn.dataset.vip === '1') : false;
        if (vipBtn) vipBtn.style.display = (stage === 'active_customer') ? 'inline-flex' : 'none';
        saveContactStage(num, stage, vip);
      };
    }
    if ($('#waVipToggle')) {
      $('#waVipToggle').onclick = function () {
        var stage = $('#waStageSelect') ? $('#waStageSelect').value : 'active_customer';
        var newVip = this.dataset.vip !== '1';
        this.dataset.vip = newVip ? '1' : '0';
        this.style.background = newVip ? '#fef9c3' : 'transparent';
        this.style.color = newVip ? '#92400e' : 'var(--muted)';
        this.style.border = newVip ? '1px solid #fbbf24' : '1px solid var(--line)';
        saveContactStage(num, stage, newVip);
      };
    }
    // v1.2.21
    if ($('#waOpenLead')) $('#waOpenLead').onclick = function (ev) { ev.preventDefault(); showTab('leads'); };
    if ($('#waMakeLead')) $('#waMakeLead').onclick = function (ev) {
      ev.preventDefault();
      if (!confirm('Analisa percakapan ini jadi lead?\n\nMemakai 1 jatah kuota chat.')) return;
      toast('Menganalisa...');
      api('analyze_lead', { method: 'POST', body: { number: num } }).then(function (r) {
        if (r && r.ok) {
          toast('Lead dibuat.');
          fetchWaConvs();          // perbarui has_lead
          showTab('leads');
          if (typeof fetchLeads === 'function') fetchLeads();
        } else {
          toast((r && r.error) || 'Analisa gagal.', true);
        }
      });
    };
    if ($('#waClaimBtn')) $('#waClaimBtn').onclick = function () { claimNumber(num); };
    if ($('#waReleaseBtn')) $('#waReleaseBtn').onclick = function () { releaseNumber(num); };
    if ($('#waRequestTakeoverBtn')) $('#waRequestTakeoverBtn').onclick = function () { openRequestTakeoverModal(num); };
    if ($('#waTakeoverApproveBtn')) $('#waTakeoverApproveBtn').onclick = function () { respondTakeover(num, 'approve'); };
    if ($('#waTakeoverDenyBtn')) $('#waTakeoverDenyBtn').onclick = function () { respondTakeover(num, 'deny'); };
    if ($('#waAdminTakeoverBtn')) $('#waAdminTakeoverBtn').onclick = function () { openAdminTakeoverModal(num); };

    // wa-scroll-preserve: cek posisi scroll SEBELUM re-render
    var _waBody = $('#waThreadBody');
    var _waWasBottom = _waBody ? (_waBody.scrollHeight - _waBody.scrollTop - _waBody.clientHeight < 60) : true;
    var _waPrevTop = _waBody ? _waBody.scrollTop : 0;
    var _waPrevHeight = _waBody ? _waBody.scrollHeight : 0;

    var _waLastDate = '';   // v1.2.15: reset tiap render -> aman untuk polling
    $('#waThreadBody').innerHTML = (res.messages || []).map(function (m) {
      var h = '';
      var _dk = waDateKey(m.ts);
      if (_dk && _dk !== _waLastDate) {   // v1.2.15: tanggal berganti -> sisip pemisah
        h += waDateSepHtml(waDateLabel(_dk));
        _waLastDate = _dk;
      }
      if (m.q) h += waBubble(m.q, 'in', m.ts);
      if (m.a) h += waBubble(m.a, m.dir === 'manual' ? 'manual' : 'bot', m.ts);
      return h;
    }).join('') || '<div style="color:var(--muted);margin:auto">Belum ada pesan.</div>';
    // wa-scroll-preserve: scroll ke bawah HANYA kalau user tadi di bawah (ngikutin chat).
    // Kalau user scroll ke atas baca history, pertahankan posisi (jangan ketarik ke bawah).
    if (_waBody) {
      if (_waWasBottom) {
        _waBody.scrollTop = _waBody.scrollHeight;
      } else {
        // pertahankan posisi relatif: kompensasi kalau ada pesan baru di bawah (tinggi bertambah)
        _waBody.scrollTop = _waPrevTop + (_waBody.scrollHeight - _waPrevHeight);
      }
    }

    $('#waReplyBar').style.display = 'block';
    var open = res.window_open;
    // Reply hanya enable kalau isMine ATAU isAdmin (untuk emergency)
    var canReply = open && (isMine || waState.isAdmin);
    $('#waReplyInput').disabled = !canReply;
    $('#waReplySend').disabled = !canReply;
    $('#waWindowNote').innerHTML = open
      ? (isMine ? '<span style="color:#065f46">' + ico('check-circle-2',13) + ' Anda mengelola chat ini.</span>'
          : (claim ? '<span style="color:var(--muted)">Chat dikelola oleh <strong>' + esc(claim.agent_username) + '</strong>. Klik "Minta Take-over" untuk request handling.</span>'
              : '<span style="color:var(--muted)">Tip: klik <strong>Claim</strong> agar bot berhenti dan Anda handle sendiri.</span>'))
      : ico('triangle-alert',13) + ' Jendela 24 jam tertutup — WhatsApp tidak mengizinkan balasan teks bebas sampai pelanggan mengirim pesan lagi.';
  }

  // === Claim actions ========================================================

  function claimNumber(num) {
    api('wa_claim', { method: 'POST', body: { number: num } }).then(function (res) {
      if (res && res.ok) {
        toast('Anda claim chat ini.');
        fetchWaThread(num); fetchWaConvs();
      } else toast((res && res.error) || 'Gagal claim.', true);
    });
  }

  function releaseNumber(num) {
    if (!confirm('Release chat ini? Bot akan resume balas otomatis.')) return;
    api('wa_release', { method: 'POST', body: { number: num } }).then(function (res) {
      if (res && res.ok) {
        toast('Chat direlease. Bot resume.');
        fetchWaThread(num); fetchWaConvs();
      } else toast((res && res.error) || 'Gagal release.', true);
    });
  }

  function openRequestTakeoverModal(num) {
    var reason = prompt('Alasan request take-over (opsional):', '');
    if (reason === null) return; // cancel
    api('wa_takeover_request', { method: 'POST', body: { number: num, reason: reason } }).then(function (res) {
      if (res && res.ok) {
        toast('Request take-over dikirim. Auto-approve dalam 5 menit kalau tidak ada respond.');
        fetchWaThread(num); fetchWaConvs();
      } else toast((res && res.error) || 'Gagal request.', true);
    });
  }

  function respondTakeover(num, decision) {
    var confirmMsg = decision === 'approve'
      ? 'Setujui take-over? Chat akan pindah ke requester.'
      : 'Tolak take-over?';
    if (!confirm(confirmMsg)) return;
    api('wa_takeover_respond', { method: 'POST', body: { number: num, decision: decision } }).then(function (res) {
      if (res && res.ok) {
        toast(decision === 'approve' ? 'Take-over disetujui.' : 'Take-over ditolak.');
        fetchWaThread(num); fetchWaConvs();
      } else toast((res && res.error) || 'Gagal respond.', true);
    });
  }

  function openAdminTakeoverModal(num) {
    var reason = prompt('Alasan admin take-over (untuk audit log):', 'escalation');
    if (reason === null) return;
    api('wa_admin_takeover', { method: 'POST', body: { number: num, reason: reason } }).then(function (res) {
      if (res && res.ok) {
        toast('Admin take-over sukses. Chat sekarang milik Anda.');
        fetchWaThread(num); fetchWaConvs();
      } else toast((res && res.error) || 'Gagal takeover.', true);
    });
  }

  function sendWaManual(num) {
    var inp = $('#waReplyInput'); var t = inp.value.trim();
    if (!t) return;
    $('#waReplySend').disabled = true;
    // Auto-claim kalau belum di-claim (backwards compat behavior)
    var claim = waState.claimDetails[num];
    var chainSend = function () {
      api('wa_send_manual', { method: 'POST', body: { number: num, text: t } }).then(function (res) {
        if (res && res.ok) { inp.value = ''; fetchWaThread(num); fetchWaConvs(); }
        else { toast((res && res.error) || 'Gagal mengirim.', true); $('#waReplySend').disabled = false; }
      });
    };
    if (!claim) {
      // Auto-claim dulu supaya konsisten dengan sistem
      api('wa_claim', { method: 'POST', body: { number: num } }).then(function (r) {
        chainSend();
      });
    } else {
      chainSend();
    }
  }

  // === Audit log viewer =====================================================

  function toggleAuditLog() {
    var box = $('#waAuditBox');
    if (box.style.display === 'none') {
      box.style.display = 'block';
      refreshAuditLog();
    } else {
      box.style.display = 'none';
    }
  }

  function refreshAuditLog() {
    api('wa_audit_log').then(function (res) {
      if (!res || !res.ok) {
        $('#waAuditBox').innerHTML = '<div style="padding:12px;color:#b91c1c;font-size:13px">Gagal memuat audit log</div>';
        return;
      }
      var entries = res.entries || [];
      if (!entries.length) {
        $('#waAuditBox').innerHTML = '<div style="padding:12px;color:var(--muted);font-size:13px">Belum ada audit entry.</div>';
        return;
      }
      var html = '<div class="wa-audit-header"><strong>' + ico('clipboard-list',14) + ' Audit Log</strong> <span style="color:var(--muted);font-size:12px">(' + res.shown + ' dari ' + res.total + ')</span></div>';
      html += '<div class="wa-audit-list">';
      entries.forEach(function (e) {
        var actionColor = {
          'claim': '#065f46', 'release': '#374151', 'auto_release': '#6b7280',
          'takeover_request': '#9a3412', 'takeover_approve': '#065f46', 'takeover_deny': '#991b1b',
          'takeover_auto_approve': '#a16207', 'admin_takeover': '#7c2d12', 'admin_release': '#374151'
        }[e.action] || '#374151';
        html += '<div class="wa-audit-row">' +
          '<span class="wa-audit-ts">' + esc(e.ts) + '</span>' +
          '<span class="wa-audit-action" style="color:' + actionColor + '">' + esc(e.action) + '</span>' +
          '<span class="wa-audit-agent">' + esc(e.agent) + '</span>' +
          '<span class="wa-audit-num">+' + esc(e.number) + '</span>' +
          (e.extra ? '<span class="wa-audit-extra" title="' + esc(JSON.stringify(e.extra)) + '">' + ico('paperclip',12) + '</span>' : '') +
          '</div>';
      });
      html += '</div>';
      $('#waAuditBox').innerHTML = html;
    });
  }

/* === End v1.2.0 WA Claim Frontend =========================================== */
  function playBeep() {
    try {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      var a = new Ctx(), o = a.createOscillator(), g = a.createGain();
      o.connect(g); g.connect(a.destination);
      o.frequency.value = 880; g.gain.value = 0.05; o.start();
      setTimeout(function () { o.stop(); a.close(); }, 180);
    } catch (e) {}
  }

  /* ---- loader registry + first tab ------------------------------------ */
  /* ====================================================================== *
   *  CENTRAL SERVER — auto-update + report-back (super_admin only)
   * ====================================================================== */
  function loadCentral() {
    if (role !== 'super_admin') return;
    var card = document.querySelector('[data-role-card="super_admin"] #cs_url');
    if (!card) return;   // card not rendered (role hidden)
    api('update_status').then(function (res) {
      if (!res.ok) return;
      var c = res.central || {};
      $('#cs_url').value     = c.url || '';
      $('#cs_tenant').value  = c.tenant_id || '';
      $('#cs_license').value = c.license_set ? c.license_key : '';
      $('#cs_auto').checked  = !!c.auto_update;
      $('#csVersion').textContent    = res.installed_version || 'v1.1.0';
      $('#csLastCheck').textContent  = c.last_check  || '–';
      $('#csLastResult').textContent = c.last_result || '–';
    });
  }

  function saveCentral() {
    var body = {
      url:         $('#cs_url').value.trim(),
      tenant_id:   $('#cs_tenant').value.trim(),
      license_key: $('#cs_license').value.trim(),
      auto_update: $('#cs_auto').checked
    };
    if (!body.url || !body.tenant_id) { toast('URL & Tenant ID wajib.', true); return; }
    api('save_central', { method: 'POST', body: body }).then(function (res) {
      if (res.ok) { toast('Setting pusat tersimpan.'); loadCentral(); }
      else toast(res.error || 'Gagal simpan.', true);
    });
  }

  function checkUpdate(silent) {
    return api('update_check', { method: 'POST' }).then(function (res) {
      if (!res.ok) {
        if (!silent) toast(res.error || 'Gagal cek update.', true);
        loadCentral();
        return res;
      }
      if (res.update_available) {
        if (!silent) toast('Update tersedia: ' + res.latest + '. Memasang…');
        return applyUpdate(res, silent);
      }
      if (!silent) toast('Sudah versi terkini (' + res.current + ').');
      loadCentral();
      return res;
    });
  }

  function applyUpdate(info, silent) {
    return api('update_apply', { method: 'POST', body: {
      zip_url: info.zip_url, manifest_url: info.manifest_url, target: info.latest
    }}).then(function (res) {
      if (!res.ok) {
        toast(res.error || 'Gagal pasang update.', true);
        return res;
      }
      toast('Versi baru dipasang: ' + res.version + ' ✓');
      // v1.1.2: trigger one more check so central immediately learns the new version
      // (the in-page report_back fired BEFORE replacement still has the old version).
      api('update_check', { method: 'POST' }).catch(function(){});
      // Brief reload so the new code is loaded
      // v1.2.2: cache-buster reload — bypass browser cache after update
      setTimeout(function () {
        var url = new URL(location.href);
        url.searchParams.set('_cb', Date.now());
        location.href = url.toString();
      }, 1500);
      return res;
    });
  }

  // Wire buttons (only attach once when DOM has the card)
  function wireCentralButtons() {
    if ($('#btnSaveCentral') && !$('#btnSaveCentral').dataset.wired) {
      $('#btnSaveCentral').onclick = saveCentral;
      $('#btnSaveCentral').dataset.wired = '1';
    }
    if ($('#btnCheckUpdate') && !$('#btnCheckUpdate').dataset.wired) {
      $('#btnCheckUpdate').onclick = function () { checkUpdate(false); };
      $('#btnCheckUpdate').dataset.wired = '1';
    }
  }

  // Auto-check on dashboard bootstrap (silent — only acts if auto_update is enabled)
  function maybeAutoCheck() {
    if (role !== 'super_admin' && role !== 'admin') return;
    // small delay so it doesn't block initial UI
    setTimeout(function () {
      api('update_status').then(function (res) {
        if (!res.ok || !res.central) return;
        if (!res.central.auto_update) return;
        if (!res.central.url || !res.central.tenant_id || !res.central.license_set) return;
        // super_admin runs the check directly. Admins also check, but the call requires super_admin role —
        // so we only fire if role allows.
        if (role !== 'super_admin') return;
        checkUpdate(true);
      });
    }, 1200);
  }

  /* ====================================================================== *
   *  LICENSE BANNER (v1.1.3) — super_admin/admin only
   * ====================================================================== */
  function renderLicenseBanner() {
    if (role !== 'super_admin' && role !== 'admin') return;
    var el = document.getElementById('licenseBanner');
    if (!el) return;
    api('license_status').then(function (res) {
      if (!res.ok || !res.license) { el.style.display = 'none'; return; }
      var lic = res.license;
      if (lic.status === 'active') {
        // Show banner only if expires_at is within 14 days
        if (lic.days_left !== null && lic.days_left >= 0 && lic.days_left <= 14) {
          el.style.display = 'block';
          el.style.background = '#fef3c7';
          el.style.borderColor = '#fde68a';
          el.style.color = '#854d0e';
          el.innerHTML = '<div style="display:flex;gap:10px;align-items:flex-start">'
                       + '<span style="flex-shrink:0;margin-top:1px">' + ico('clock-3', 18) + '</span>'
                       + '<div><b>Lisensi akan berakhir dalam ' + lic.days_left + ' hari.</b> Silakan hubungi vendor untuk perpanjangan.</div>'
                       + '</div>';
        } else {
          el.style.display = 'none';
        }
      } else if (lic.status === 'expired') {
        el.style.display = 'block';
        el.style.background = '#fef3c7';
        el.style.borderColor = '#d97706';
        el.style.color = '#854d0e';
        var msg = '<b>Lisensi sudah expired</b> (sejak ' + (lic.expires_at || '?') + ').';
        if (lic.days_left !== null && lic.days_left < 0) {
          var daysOver = Math.abs(lic.days_left);
          var daysLeftBeforeSuspend = 7 - daysOver;
          if (daysLeftBeforeSuspend > 0) {
            msg += ' Layanan akan otomatis di-suspend dalam <b>' + daysLeftBeforeSuspend + ' hari</b> jika tidak diperpanjang.';
          } else {
            msg += ' Suspend otomatis akan segera dilakukan.';
          }
        }
        msg += ' Hubungi vendor untuk perpanjangan.';
        el.innerHTML = '<div style="display:flex;gap:10px;align-items:flex-start">'
                     + '<span style="flex-shrink:0;margin-top:1px">' + ico('triangle-alert', 18) + '</span>'
                     + '<div>' + msg + '</div></div>';
      } else if (lic.status === 'suspended') {
        el.style.display = 'block';
        el.style.background = '#fee2e2';
        el.style.borderColor = '#c4302b';
        el.style.color = '#991b1b';
        el.innerHTML = '<div style="display:flex;gap:10px;align-items:flex-start">'
                     + '<span style="flex-shrink:0;margin-top:1px">' + ico('ban', 18) + '</span>'
                     + '<div><b>Layanan SUSPENDED.</b> Chatbot tidak melayani pengunjung. Token API Anda telah dikosongkan. Setelah perpanjangan, isi ulang token Claude/WhatsApp/Telegram di menu Widget &amp; API.</div>'
                     + '</div>';
      } else {
        el.style.display = 'none';
      }
    }).catch(function(){ el.style.display = 'none'; });
  }

  /* ====================================================================== *
   *  CAP BANNER (v1.1.4) — all roles see this
   * ====================================================================== */
  function renderCapBanner() {
    var el = document.getElementById('capBanner');
    if (!el) return;
    api('cap_status').then(function (res) {
      if (!res.ok || !res.cap) { el.style.display = 'none'; return; }
      var c = res.cap;
      if (c.reached) {
        // 100%+
        el.style.display = 'block';
        el.style.background = '#fee2e2';
        el.style.borderColor = '#c4302b';
        el.style.color = '#991b1b';
        el.innerHTML = '<div style="display:flex;gap:10px;align-items:flex-start">'
                     + '<span style="flex-shrink:0;margin-top:1px">' + ico('octagon-alert', 18) + '</span>'
                     + '<div><b>Layanan mencapai batas kuota bulan ini.</b> Chatbot tidak memanggil AI sampai reset tanggal 1 atau kuota dinaikkan. Pengunjung dapat pesan pengganti.</div>'
                     + '</div>';
      } else if (c.warning) {
        // 90-99%
        el.style.display = 'block';
        el.style.background = '#fef3c7';
        el.style.borderColor = '#d97706';
        el.style.color = '#854d0e';
        el.innerHTML = '<div style="display:flex;gap:10px;align-items:flex-start">'
                     + '<span style="flex-shrink:0;margin-top:1px">' + ico('triangle-alert', 18) + '</span>'
                     + '<div><b>Layanan mendekati batas kuota bulan ini.</b> Chatbot sudah berhenti memanggil AI untuk menghemat kuota. Pengunjung dapat pesan pengganti.</div>'
                     + '</div>';
      } else {
        el.style.display = 'none';
      }
    }).catch(function(){ el.style.display = 'none'; });
  }

  /* ====================================================================== *
   *  USAGE CARD (v1.1.5) — renders in Reports tab, all roles
   * ====================================================================== */
  function loadUsageCard() {
    var card = document.getElementById('usageCard');
    if (!card) return;
    api('usage_dashboard').then(function (res) {
      if (!res.ok) { card.style.display = 'none'; return; }
      card.style.display = '';

      // v1.1.9: inject Lucide icon ke header
      var headIcon = document.getElementById('ucHeadIcon');
      if (headIcon && !headIcon.firstChild) headIcon.innerHTML = ico('activity', 20);

      // Tier badge — pill dengan label kecil + dot + nama tier
      var tierLabels  = { starter:'Starter', business:'Business', pro:'Pro', custom:'Custom' };
      // Gradient backgrounds for tiers — give a premium feel
      var tierStyles  = {
        starter:  'linear-gradient(135deg,#64748b,#475569)',
        business: 'linear-gradient(135deg,#140383,#3730a3)',
        pro:      'linear-gradient(135deg,#16a34a,#15803d)',
        custom:   'linear-gradient(135deg,#d97706,#b45309)',
      };
      var tier  = (res.tier || 'starter').toLowerCase();
      var tBadge = document.getElementById('ucTier');
      tBadge.innerHTML = '<span class="uc-dot"></span>'
                       + '<span class="uc-label">Paket</span>'
                       + (tierLabels[tier] || tier);
      tBadge.style.background = tierStyles[tier] || tierStyles.starter;
      tBadge.className = 'uc-pill uc-tier-' + tier;

      // License status badge — pill dengan ikon emoji + label + status
      var statusLabels = { active:'Aktif', expired:'Expired', suspended:'Suspended' };
      var statusIcons  = { active: ico('check-circle-2',13), expired: ico('clock-3',13), suspended: ico('ban',13) };
      var statusStyles = {
        active:    'linear-gradient(135deg,#16a34a,#15803d)',
        expired:   'linear-gradient(135deg,#d97706,#b45309)',
        suspended: 'linear-gradient(135deg,#c4302b,#991b1b)',
      };
      var st = res.license_status || 'active';
      var sBadge = document.getElementById('ucStatus');
      sBadge.innerHTML = '<span class="uc-dot"></span>'
                       + '<span class="uc-label">Lisensi</span>'
                       + (statusLabels[st] || st);
      sBadge.style.background = statusStyles[st] || statusStyles.active;
      sBadge.className = 'uc-pill uc-status-' + st;

      // Chat used / cap
      var used = res.chats_used || 0;
      var cap = res.chat_cap || 0;
      var pct = res.usage_pct || 0;
      // v1.2.9: chat-based — bar & display pakai chat count, bukan usage_pct (cost)
      var chatPct = (typeof res.chat_pct === 'number') ? res.chat_pct : (res.chat_cap > 0 ? Math.round((res.chats_used||0) / res.chat_cap * 100) : 0);
      document.getElementById('ucUsedRaw').textContent = cap > 0 ? used + ' / ' + cap : used + ' (unlimited)';
      var bar = document.getElementById('ucBar');
      bar.style.width = Math.min(chatPct, 100) + '%';
      bar.style.background = chatPct >= 100 ? '#c4302b' : (chatPct >= 90 ? '#d97706' : '#16a34a');
      var pctEl = document.getElementById('ucPct');
      pctEl.textContent = res.chat_cap > 0 ? (res.chats_used||0) + ' / ' + res.chat_cap + ' chat' : (res.chats_used||0) + ' chat'; // v1.2.9: chat-based
      pctEl.style.color = res.cap_reached ? '#c4302b' : (res.cap_warning ? '#d97706' : 'var(--muted)');

      // Days left
      document.getElementById('ucDaysLeft').textContent = (res.days_left_month || 0) + ' hari';

      // Chart 30 hari — inline SVG bar chart
      drawDailyChart(res.daily_30d || [], res.today_wib);
    }).catch(function () { card.style.display = 'none'; });
  }

  function drawDailyChart(daily, todayWib) {
    var container = document.getElementById('ucChart');
    if (!container) return;

    // Build full 30-day array (fill missing days with 0)
    var days = [];
    var todayMs = Date.parse((todayWib || new Date().toISOString().slice(0,10)) + 'T00:00:00Z');
    for (var i = 29; i >= 0; i--) {
      var d = new Date(todayMs - i * 86400000);
      var ds = d.toISOString().slice(0,10);
      var hit = daily.find(function(x){ return x.date === ds; });
      days.push({ date: ds, calls: hit ? hit.calls : 0 });
    }
    var max = Math.max.apply(null, days.map(function(d){return d.calls;}).concat([1]));
    var w = container.clientWidth - 24 || 400;
    var h = 130;
    var pad = { top: 8, right: 8, bottom: 22, left: 28 };
    var chartW = w - pad.left - pad.right;
    var chartH = h - pad.top - pad.bottom;
    var barW = chartW / days.length;

    // Y axis ticks: 0, 50%, 100% of max
    var yMax = Math.max(max, 1);
    var ticks = [0, Math.ceil(yMax/2), yMax];

    var bars = days.map(function (d, i) {
      var bh = d.calls > 0 ? Math.max(2, (d.calls / yMax) * chartH) : 0;
      var x = pad.left + i * barW + 1;
      var y = pad.top + chartH - bh;
      var color = d.calls > 0 ? '#140383' : '#e2e5ee';
      return '<rect x="'+x.toFixed(1)+'" y="'+y.toFixed(1)+'" width="'+(barW-2).toFixed(1)+'" height="'+bh.toFixed(1)+'" fill="'+color+'" rx="1"><title>'+d.date+': '+d.calls+' chat</title></rect>';
    }).join('');

    var yAxis = ticks.map(function (t) {
      var y = pad.top + chartH - (t / yMax) * chartH;
      return '<text x="'+(pad.left-4)+'" y="'+(y+3)+'" text-anchor="end" font-size="9" fill="#5d6479">'+t+'</text>'
           + '<line x1="'+pad.left+'" x2="'+(w-pad.right)+'" y1="'+y+'" y2="'+y+'" stroke="#eef0fb" stroke-width="1"/>';
    }).join('');

    // X axis: label every ~5th day
    var xLabels = days.map(function (d, i) {
      if (i % 5 !== 0 && i !== days.length-1) return '';
      var x = pad.left + i * barW + barW/2;
      var label = d.date.slice(5);   // MM-DD
      return '<text x="'+x.toFixed(1)+'" y="'+(h-6)+'" text-anchor="middle" font-size="9" fill="#5d6479">'+label+'</text>';
    }).join('');

    container.innerHTML = '<svg viewBox="0 0 '+w+' '+h+'" width="100%" height="'+h+'" xmlns="http://www.w3.org/2000/svg">'+yAxis+bars+xLabels+'</svg>';
  }

  /* ====================================================================== *
   *  LEADS (v1.2.20) — AI menyiapkan bahan, agent yang memutuskan
   * ====================================================================== */
  var leadData = [];
  var leadFilter = 'all';
  // v1.2.27: mengingat kartu mana yang terbuka. Tanpa ini, mengubah status akan
  // memuat ulang daftar dan menutup semuanya — Anda kehilangan tempat.
  var leadOpenState = {};
  var LEAD_STATUS = {
    baru:      { label: 'Baru',      bg: '#e5e7eb', fg: '#374151' },
    qualified: { label: 'Qualified', bg: '#d1fae5', fg: '#065f46' },
    follow_up: { label: 'Follow-up', bg: '#fed7aa', fg: '#9a3412' },
    closed:    { label: 'Closed',    bg: '#e0e7ff', fg: '#3730a3' }
  };
  // v1.2.39: tag pipeline kontak (stage) — terpisah dari status lead di atas.
  var CONTACT_STAGE = {
    new:             { label: 'Unrated',         bg: '#e5e7eb', fg: '#374151' },
    cold:            { label: 'Cold',            bg: '#dbeafe', fg: '#1e40af' },
    warm:            { label: 'Warm',            bg: '#fef3c7', fg: '#92400e' },
    hot_prospect:    { label: 'Hot Prospect',    bg: '#fee2e2', fg: '#991b1b' },
    lost:            { label: 'Unqualified',     bg: '#f3f4f6', fg: '#6b7280' },
    active_customer: { label: 'Active Customer', bg: '#d1fae5', fg: '#065f46' },
    churned:         { label: 'Churned',         bg: '#fde68a', fg: '#78350f' }
  };
  // v1.2.39 fase2g: urutan tampil di dropdown, dikelompokkan dengan garis
  // pemisah -- '__sep__' bukan value asli, cuma penanda render pemisah.
  var CONTACT_STAGE_ORDER = ['new', '__sep__', 'cold', 'warm', 'hot_prospect', '__sep__', 'lost', '__sep__', 'active_customer', 'churned'];
  function contactStageOptionsHtml(selected) {
    return CONTACT_STAGE_ORDER.map(function (k) {
      if (k === '__sep__') return '<option disabled>\u2500\u2500\u2500\u2500\u2500</option>';
      return '<option value="' + k + '"' + (selected === k ? ' selected' : '') + '>' + CONTACT_STAGE[k].label + '</option>';
    }).join('');
  }
  var CONTACT_VIP_STYLE = 'background:#fef9c3;color:#92400e';
  function contactStageBadgeHtml(stage, vip, extraStyle) {
    var cs = CONTACT_STAGE[stage || 'new'] || CONTACT_STAGE.new;
    var html = '<span class="tag" style="background:' + cs.bg + ';color:' + cs.fg + (extraStyle || '') + '">' + esc(cs.label) + '</span>';
    if (vip) html += ' <span class="tag" style="' + CONTACT_VIP_STYLE + '">' + ico('star', 12) + ' VIP</span>';
    return html;
  }
  // Simpan stage/vip lalu segarkan daftar percakapan. Dipakai dari daftar
  // percakapan maupun kepala thread.
  function saveContactStage(num, stage, vip) {
    api('save_contact_stage', { method: 'POST', body: { number: num, stage: stage, vip: vip } }).then(function (r) {
      // v1.2.39 fase2b: refresh thread yang SEDANG DIBUKA juga (bukan cuma
      // daftar percakapan) — kalau tidak, dropdown kelihatan balik ke nilai
      // lama karena kepala thread tidak ikut digambar ulang dengan data baru.
      if (r && r.ok) {
        toast('Tag disimpan.');
        // v1.2.39 fase2c: tunggu fetchWaConvs SELESAI (waState.convs terisi
        // data baru) baru gambar ulang thread -- kalau paralel, thread bisa
        // selesai duluan dan baca data lama (dropdown keliatan balik lagi).
        fetchWaConvs().then(function () { if (waState.current === num) fetchWaThread(num); });
      } else toast((r && r.error) || 'Gagal menyimpan tag.', true);
    });
  }
  // v1.2.39 fase4: simpan nama/tanggal lahir pelanggan (partial update --
  // cuma kirim field yang diisi). Update data lokal supaya tidak perlu
  // refetch penuh, cukup renderContacts() ulang.
  function saveContactInfo(num, fields) {
    var body = { number: num };
    if (fields.cust_name !== undefined) body.cust_name = fields.cust_name;
    if (fields.cust_dob !== undefined) body.cust_dob = fields.cust_dob;
    api('save_contact_info', { method: 'POST', body: body }).then(function (r) {
      if (r && r.ok) {
        toast('Data pelanggan disimpan.');
        var idx = -1;
        for (var i = 0; i < contactData.length; i++) { if (contactData[i].number === num) { idx = i; break; } }
        if (idx > -1) {
          if (fields.cust_name !== undefined) contactData[idx].cust_name = r.cust_name;
          if (fields.cust_dob !== undefined) contactData[idx].cust_dob = r.cust_dob;
        }
      } else toast((r && r.error) || 'Gagal menyimpan data pelanggan.', true);
    });
  }

  function loadLeads() {
    fetchLeads();
    $('#btnReloadLeads').onclick = fetchLeads;
    $$('.lead-filter').forEach(function (b) {
      b.onclick = function () {
        leadFilter = b.dataset.leadStatus;
        $$('.lead-filter').forEach(function (x) { x.classList.remove('active'); });
        b.classList.add('active');
        renderLeads();
      };
    });
  }

  function fetchLeads() {
    api('get_leads').then(function (res) {
      if (!res || !res.ok) { toast((res && res.error) || 'Gagal memuat leads.', true); return; }
      leadData = res.leads || [];
      renderLeads();
    });
  }

  // Kolom kosong ditampilkan sebagai "—": customer tidak menyebutkannya,
  // dan itu sendiri informasi berguna bagi agent.
  function leadField(label, val) {
    var isi = (val && String(val).trim()) ? esc(val) : '<span style="color:var(--muted)">&mdash;</span>';
    return '<div style="margin-bottom:6px"><span style="color:var(--muted);font-size:12px">' + label + '</span><br>' + isi + '</div>';
  }

  function renderLeads() {
    var list = leadData.filter(function (l) {
      return leadFilter === 'all' || (l.status || 'baru') === leadFilter;
    });
    if (!list.length) {
      $('#leadList').innerHTML = '<div class="card" style="text-align:center;color:var(--muted)">' +
        (leadData.length ? 'Tidak ada lead pada filter ini.' : 'Belum ada lead. Kartu dibuat otomatis saat percakapan WhatsApp mencapai 8 pesan.') +
        '</div>';
      return;
    }
    $('#leadList').innerHTML = list.map(function (l) {
      var ex = l.extracted || {};
      var st = LEAD_STATUS[l.status || 'baru'] || LEAD_STATUS.baru;
      var judul = l.name ? esc(l.name) : ('+' + esc(l.number));
      var opsi = Object.keys(LEAD_STATUS).map(function (k) {
        return '<option value="' + k + '"' + ((l.status || 'baru') === k ? ' selected' : '') + '>' + LEAD_STATUS[k].label + '</option>';
      }).join('');

      // v1.2.27: kepala selalu tampil, rincian menyusul saat diklik
      var terbuka = !!leadOpenState[l.number];
      var putar = terbuka ? 'transform:rotate(180deg);' : '';
      return '<div class="card" data-lead="' + esc(l.number) + '">' +
        '<div class="lead-head" style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;cursor:pointer;user-select:none">' +
          '<div style="display:flex;align-items:center;gap:8px">' +
            '<span class="lead-chev" style="display:inline-flex;color:var(--muted);transition:transform .15s;' + putar + '">' +
              ico('chevron-down', 16) + '</span>' +
            '<div><strong style="font-size:15px">' + judul + '</strong>' +
              (l.name ? ' <span style="color:var(--muted);font-size:12px">+' + esc(l.number) + '</span>' : '') +
              '<div style="color:var(--muted);font-size:12px">Dianalisa ' + esc((l.analyzed_at || '').slice(0, 16)) + '</div>' +
            '</div>' +
          '</div>' +
          '<span class="tag" style="background:' + st.bg + ';color:' + st.fg + '">' + st.label + '</span>' +
          ' ' + contactStageBadgeHtml(l.contact_stage, l.contact_vip, ';margin-left:2px') +
        '</div>' +
        '<div class="lead-body" style="margin-top:12px;' + (terbuka ? '' : 'display:none') + '">' +
        '<div style="background:var(--brand-soft);padding:10px 12px;border-radius:8px;margin-bottom:10px;font-size:14px">' +
          (ex.ringkasan ? esc(ex.ringkasan) : '<span style="color:var(--muted)">Tidak ada ringkasan.</span>') +
        '</div>' +
        '<div class="grid2">' +
          leadField('Nama disebut', ex.nama) +
          leadField('Kebutuhan', ex.kebutuhan) +
          leadField('Waktu', ex.waktu) +
          leadField('Anggaran', ex.anggaran) +
        '</div>' +
        '<div class="row" style="margin-top:8px"><label class="fl">Status</label>' +
          '<select class="lead-status">' + opsi + '</select></div>' +
        '<div class="row"><label class="fl">Catatan</label>' +
          '<textarea class="lead-note" rows="2" placeholder="Catatan agent...">' + esc(l.note || '') + '</textarea></div>' +
        '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">' +
          '<button class="btn ghost sm lead-open">Lihat percakapan</button>' +
          // v1.2.29: analisa memakai kuota klien -> hanya admin
          (user.role === 'wa_agent' ? '' : '<button class="btn ghost sm lead-reanalyze">Analisa ulang</button>') +
        '</div>' +
        '</div>' +   /* v1.2.27: tutup lead-body */
      '</div>';
    }).join('');

    $$('#leadList .card[data-lead]').forEach(function (card) {
      var num = card.dataset.lead;
      // v1.2.27: buka/tutup. Klik hanya ditangkap di kepala, jadi menekan
      // dropdown/catatan/tombol di dalam rincian tidak menutup kartunya.
      var kepala = card.querySelector('.lead-head');
      var badan  = card.querySelector('.lead-body');
      var chev   = card.querySelector('.lead-chev');
      if (kepala) kepala.onclick = function () {
        var kini = badan.style.display !== 'none';
        badan.style.display = kini ? 'none' : '';
        leadOpenState[num] = !kini;
        if (chev) chev.style.transform = kini ? '' : 'rotate(180deg)';
      };
      card.querySelector('.lead-status').onchange = function (e) {
        saveLead(num, { status: e.target.value });
      };
      // simpan saat kursor meninggalkan kotak catatan
      card.querySelector('.lead-note').onblur = function (e) {
        var lama = (leadData.filter(function (x) { return x.number === num; })[0] || {}).note || '';
        if (e.target.value === lama) return;
        saveLead(num, { note: e.target.value });
      };
      card.querySelector('.lead-open').onclick = function () { openLeadConv(num); };
      var btnUlang = card.querySelector('.lead-reanalyze');
      if (btnUlang) btnUlang.onclick = function () {
        if (!confirm('Analisa ulang percakapan ini? Memakai 1 jatah kuota chat.')) return;
        api('analyze_lead', { method: 'POST', body: { number: num } }).then(function (r) {
          if (r && r.ok) { toast('Analisa diperbarui.'); fetchLeads(); }
          else toast((r && r.error) || 'Analisa gagal.', true);
        });
      };
    });
  }

  function saveLead(num, body) {
    body.number = num;
    api('save_lead', { method: 'POST', body: body }).then(function (r) {
      if (r && r.ok) { toast('Tersimpan.'); fetchLeads(); }
      else toast((r && r.error) || 'Gagal menyimpan.', true);
    });
  }

  function openLeadConv(num) {
    showTab('wachat');
    // beri jeda supaya daftar percakapan sempat dimuat sebelum dipilih
    setTimeout(function () {
      try { selectWaConv(num); } catch (e) {}
    }, 700);
  }

  /* ====================================================================== *
   *  KONTAK (v1.2.39) — semua kontak WA + tag pipeline
   * ====================================================================== */
  // v1.2.39 fase6: VIP yang ulang tahun (bulan+hari) hari ini -- dipakai
  // filter Fase 5 maupun tombol "Kirim Ucapan" di kartu.
  function contactBirthdayToday(c) {
    if (!c || !c.vip || !c.cust_dob) return false;
    var d = new Date();
    var mmdd = String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    return c.cust_dob.slice(5) === mmdd;
  }
  // Ambil template dari pengaturan (fallback teks default kalau kosong),
  // ganti {nama}, lalu ISI OTOMATIS kotak balas WA -- TIDAK langsung
  // kirim, admin yang review & kirim manual (sesuai jendela 24 jam WA).
  // v1.2.39 fase8: template diambil dari contactWaConfig (hasil action
  // get_birthday_config), BUKAN get_settings -- get_settings dibatasi
  // super_admin/admin sehingga wa_agent dulu gagal tanpa penjelasan.
  function sendBirthdayGreeting(num, custName) {
    var tmpl = (contactWaConfig && contactWaConfig.birthday_greeting) || '';
    if (!tmpl.trim()) {
      tmpl = 'Selamat ulang tahun, {nama}! \uD83C\uDF89 Semoga sehat selalu dan sukses terus. Terima kasih sudah menjadi pelanggan setia kami.';
    }
    var teks = tmpl.split('{nama}').join(custName || '');
    showTab('wachat');
    setTimeout(function () {
      try {
        selectWaConv(num);
        setTimeout(function () {
          var input = $('#waReplyInput');
          if (input) { input.value = teks; input.focus(); }
        }, 700);
      } catch (e) {}
    }, 300);
  }
  // v1.2.39 fase8: status WA Bot + template ucapan (diisi loadKontak)
  var contactWaConfig = { wa_enabled: false, birthday_greeting: '' };
  var contactData = [];
  var contactFilter = 'all';
  var contactOpenState = {};
  function loadKontak() {
    // v1.2.39 fase8: status WhatsApp Bot + template ucapan. Semua elemen
    // fitur ulang tahun bergantung pada ini.
    api('get_birthday_config').then(function (r) {
      if (r && r.ok) {
        contactWaConfig.wa_enabled = !!r.wa_enabled && r.provider === 'fonnte';   // v1.2.39 fase8b
        contactWaConfig.birthday_greeting = r.birthday_greeting || '';
      }
      var fb = document.querySelector('.contact-filter[data-contact-stage="vip_birthday_today"]');
      if (fb) fb.style.display = contactWaConfig.wa_enabled ? '' : 'none';
      renderContacts();
    });
    fetchContacts();
    $('#btnReloadKontak').onclick = fetchContacts;
    $$('.contact-filter').forEach(function (b) {
      b.onclick = function () {
        contactFilter = b.dataset.contactStage;
        $$('.contact-filter').forEach(function (x) { x.classList.remove('active'); });
        b.classList.add('active');
        renderContacts();
      };
    });
  }
  function fetchContacts() {
    api('get_contacts').then(function (res) {
      if (res && res.ok) { contactData = res.contacts || []; renderContacts(); }
    });
  }
  function renderContacts() {
    var list = contactData.filter(function (c) {
      // v1.2.39 fase5: filter khusus -- VIP yang tanggal lahirnya (bulan+hari)
      // sama dengan hari ini (tanggal perangkat yang membuka dashboard).
      if (contactFilter === 'vip_birthday_today') {
        if (!c.vip || !c.cust_dob) return false;
        var _d = new Date();
        var _mmdd = String(_d.getMonth() + 1).padStart(2, '0') + '-' + String(_d.getDate()).padStart(2, '0');
        return c.cust_dob.slice(5) === _mmdd;   // cust_dob format YYYY-MM-DD
      }
      return contactFilter === 'all' || (c.stage || 'new') === contactFilter;
    });
    if (!list.length) {
      $('#contactList').innerHTML = '<div class="card" style="text-align:center;color:var(--muted)">' +
        (contactData.length ? 'Tidak ada kontak pada filter ini.' : 'Belum ada kontak.') +
        '</div>';
      return;
    }
    $('#contactList').innerHTML = list.map(function (c) {
      var judul = c.name ? esc(c.name) : ('+' + esc(c.number));
      var opsi = contactStageOptionsHtml(c.stage || 'new');
      var terbuka = !!contactOpenState[c.number];
      var putar = terbuka ? 'transform:rotate(180deg);' : '';
      return '<div class="card" data-contact="' + esc(c.number) + '">' +
        '<div class="contact-head" style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;cursor:pointer;user-select:none">' +
          '<div style="display:flex;align-items:center;gap:8px">' +
            '<span class="contact-chev" style="display:inline-flex;color:var(--muted);transition:transform .15s;' + putar + '">' +
              ico('chevron-down', 16) + '</span>' +
            '<div><strong style="font-size:15px">' + judul + '</strong>' +
              (c.name ? ' <span style="color:var(--muted);font-size:12px">+' + esc(c.number) + '</span>' : '') +
              '<div style="color:var(--muted);font-size:12px">Terakhir aktif ' + esc((c.last_seen || '').slice(0, 16)) + '</div>' +
            '</div>' +
          '</div>' +
          contactStageBadgeHtml(c.stage, c.vip, '') +
        '</div>' +
        '<div class="contact-body" style="margin-top:12px;' + (terbuka ? '' : 'display:none') + '">' +
        '<div class="row" style="margin-top:8px"><label class="fl">Lead Rating</label>' +
          '<select class="contact-stage-select">' + opsi + '</select></div>' +
        '<div class="row contact-vip-row" style="align-items:center;gap:8px;display:' + ((c.stage || 'new') === 'active_customer' ? 'flex' : 'none') + '">' +
          '<label class="fl">VIP</label><input type="checkbox" class="contact-vip-check" style="margin-left:4px"' + (c.vip ? ' checked' : '') + '></div>' +
        // v1.2.39 fase4: data pelanggan, cuma tampil saat Active Customer
        '<div class="contact-customer-fields" style="display:' + ((c.stage || 'new') === 'active_customer' ? 'block' : 'none') + '">' +
          '<div class="row" style="margin-top:8px"><label class="fl">Nama</label>' +
            '<input type="text" class="contact-cust-name" placeholder="Nama pelanggan" value="' + esc(c.cust_name || '') + '"></div>' +
          (contactWaConfig.wa_enabled
            ? '<div class="row" style="margin-top:8px"><label class="fl">Tanggal Lahir</label>' +
                '<input type="date" class="contact-cust-dob" value="' + esc(c.cust_dob || '') + '"></div>'
            : '') +
        '</div>' +
        '<div class="grid2" style="margin-top:8px">' +
          leadField('Pertama dilihat', (c.first_seen || '').slice(0, 16)) +
          leadField('Terakhir aktif', (c.last_seen || '').slice(0, 16)) +
        '</div>' +
        '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">' +
          '<button class="btn ghost sm contact-open-thread">Lihat percakapan</button>' +
          ((contactWaConfig.wa_enabled && contactBirthdayToday(c)) ? '<button class="btn sm contact-birthday-btn" style="background:#fef3c7;color:#92400e;border:1px solid #fbbf24">' + ico('cake', 14) + ' Kirim Ucapan</button>' : '') +
        '</div>' +
        '</div>' +
      '</div>';
    }).join('');

    $$('#contactList .card[data-contact]').forEach(function (card) {
      var num = card.dataset.contact;
      var kepala = card.querySelector('.contact-head');
      var badan  = card.querySelector('.contact-body');
      var chev   = card.querySelector('.contact-chev');
      kepala.onclick = function () {
        var buka = badan.style.display === 'none';
        badan.style.display = buka ? '' : 'none';
        chev.style.transform = buka ? 'rotate(180deg)' : '';
        contactOpenState[num] = buka;
      };
      var sel    = card.querySelector('.contact-stage-select');
      var vipRow = card.querySelector('.contact-vip-row');
      var vipChk = card.querySelector('.contact-vip-check');
      function _syncLocal(stage, vip) {
        var idx = -1;
        for (var i = 0; i < contactData.length; i++) { if (contactData[i].number === num) { idx = i; break; } }
        if (idx > -1) { contactData[idx].stage = stage; contactData[idx].vip = vip; }
      }
      if (sel) {
        sel.onclick = function (ev) { ev.stopPropagation(); };
        sel.onchange = function (ev) {
          ev.stopPropagation();
          var stage = this.value;
          var vip = (stage === 'active_customer') ? (vipChk ? vipChk.checked : false) : false;
          _syncLocal(stage, vip);
          saveContactStage(num, stage, vip);
          renderContacts();   // optimistic: badge & filter langsung ikut berubah
        };
      }
      if (vipChk) {
        vipChk.onclick = function (ev) { ev.stopPropagation(); };
        vipChk.onchange = function (ev) {
          var stage = sel ? sel.value : 'active_customer';
          _syncLocal(stage, this.checked);
          saveContactStage(num, stage, this.checked);
          renderContacts();
        };
      }
      // v1.2.39 fase4: field Nama (simpan saat kursor pindah) & Tanggal
      // Lahir (simpan saat dipilih) -- sama pola dengan catatan di Leads.
      var custNameInput = card.querySelector('.contact-cust-name');
      var custDobInput  = card.querySelector('.contact-cust-dob');
      if (custNameInput) {
        custNameInput.onclick = function (ev) { ev.stopPropagation(); };
        custNameInput.onblur = function (e) {
          var lama = (contactData.filter(function (x) { return x.number === num; })[0] || {}).cust_name || '';
          if (e.target.value === lama) return;
          saveContactInfo(num, { cust_name: e.target.value });
        };
      }
      if (custDobInput) {
        custDobInput.onclick = function (ev) { ev.stopPropagation(); };
        custDobInput.onchange = function (e) {
          saveContactInfo(num, { cust_dob: e.target.value });
        };
      }
      var btnOpen = card.querySelector('.contact-open-thread');
      if (btnOpen) {
        btnOpen.onclick = function (ev) {
          ev.stopPropagation();
          showTab('wachat');
          setTimeout(function () { try { selectWaConv(num); } catch (e) {} }, 700);
        };
      }
      // v1.2.39 fase6: tombol Kirim Ucapan (kalau tampil di kartu ini)
      var btnBday = card.querySelector('.contact-birthday-btn');
      if (btnBday) {
        btnBday.onclick = function (ev) {
          ev.stopPropagation();
          var cd = contactData.filter(function (x) { return x.number === num; })[0] || {};
          sendBirthdayGreeting(num, cd.cust_name || cd.name || '');
        };
      }
    });
  }
  var loaders = {
    reports: function () { initReportsControls(); loadUsageCard(); loadReports(); },
    wachat: loadWachat,
    webchat: loadWebchat,
    leads: loadLeads,
    kontak: loadKontak,
    kb: loadKb,
    content: loadContent,
    test: initTest,
    widget: function () { loadWidget(); loadCentral(); wireCentralButtons(); },
    users: loadUsers,
    install: loadInstall,
    profile: loadProfile
  };

  // first tab per role
  var firstTab = role === 'wa_agent' ? 'wachat'
               : role === 'admin'    ? 'reports'
               :                       'reports';   // super_admin
  showTab(firstTab);
  maybeAutoCheck();
  renderLicenseBanner();
  renderCapBanner();
})();
