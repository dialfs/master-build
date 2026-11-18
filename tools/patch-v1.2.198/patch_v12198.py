#!/usr/bin/env python3
"""v1.2.198 (pasang-di-hp): panduan memasang dashboard ke layar utama HP.
- app.js: artikel Pusat Bantuan `pasang-hp` (Android & iPhone) + tombol "Unduh panduan PDF bergambar",
  disorot "Sering ditanyakan" di urutan pertama daftar Sering dicari untuk semua peran.
  Di Android/Chrome yang mendukung, muncul tombol "Pasang sekarang" (prompt instal bawaan browser).
  Artikel notifikasi menautkan ke panduan ini.
- index.html: gaya sorotan + app.js?v=1.2.198.
- api/index.php: DEI_VERSION v1.2.198.
Butuh v1.2.197. Idempoten.  Pakai: patch_v12198.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.198: pasang-di-hp'; NEED = 'v1.2.197: kode-terlindung'
PDF = 'https://chat.deintegra.com/panduan/pasang-dashboard-di-hp.pdf'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12198-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)

API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

# ---------------------------------------------------------------- api/index.php
s = rd(API)
if TAG not in s:
    assert NEED in s, 'butuh v1.2.197 dulu'
    s = rep(s, "define('DEI_VERSION', 'v1.2.197');   // v1.2.197:",
            "define('DEI_VERSION', 'v1.2.198');   // " + TAG + " — panduan pasang dashboard di layar utama HP (Pusat Bantuan, PDF bergambar); v1.2.197:", what='DEI_VERSION')
    save(API, s)
else: print('sudah', API)

# ---------------------------------------------------------------- app.js
s = rd(JS)
if TAG not in s:
    # 1) artikel baru, disisipkan sesudah artikel notifikasi
    ART = ("    { id: 'pasang-hp', roles: R_ALL, hot: 1, pdf: '" + PDF + "', t: 'Memasang dashboard di HP (ikon di layar utama)', "
           "k: 'pasang install instal shortcut pintasan layar utama home screen homescreen ikon icon aplikasi app hp handphone android iphone ios safari chrome dock pwa tambah bagikan share',\n"
           "      s: ['Buka alamat dashboard tenant Anda di HP lalu login: <b>Android</b> pakai <b>Chrome</b>, <b>iPhone</b> pakai <b>Safari</b>.',\n"
           "          '<b>Android (Chrome):</b> ketuk menu <b>&#8942;</b> di kanan atas &rsaquo; <b>Tambahkan ke layar utama</b> atau <b>Instal aplikasi</b> &rsaquo; <b>Instal</b>.',\n"
           "          '<b>iPhone (Safari):</b> ketuk tombol <b>Bagikan</b> (kotak dengan panah ke atas; bila tidak terlihat, ketuk <b>&bull;&bull;&bull;</b> dulu) &rsaquo; <b>Tambah ke Layar Utama</b> &rsaquo; <b>Tambah</b>.',\n"
           "          'Ikon <b>DEI</b> muncul di layar utama. Selalu buka dashboard dari ikon itu, lalu aktifkan <b>Notifikasi</b> dan pilih <b>Izinkan</b>. Di iPhone notifikasi hanya jalan bila dibuka dari ikon (iOS 16.4 ke atas).',\n"
           "          'Satu ikon untuk satu tenant: bila memegang beberapa tenant, pasang dari alamat masing-masing.'] },   // " + TAG + "\n")
    s = rep(s, "    { id: 'password', roles: R_ALL, t: 'Mengganti password'", ART + "    { id: 'password', roles: R_ALL, t: 'Mengganti password'", what='artikel password')
    # 2) artikel notifikasi menunjuk ke panduan baru
    s = rep(s, "'Di HP, pasang dashboard ke layar utama (Add to Home Screen) agar lebih andal.'],",
            "'Di HP, pasang dashboard ke layar utama dulu agar lebih andal (lihat panduan <b>Memasang dashboard di HP</b>).'],   // " + TAG, what='notif HP')
    # 3) sorot di urutan pertama "Sering dicari" untuk semua peran
    for r in ("wa_agent: ['", "supervisor: ['", "admin: ['", "super_admin: ['"):
        s = rep(s, ("  var HELP_POPULAR = { " if r.startswith('wa_agent') else ("    " if r.startswith(('supervisor', 'admin', 'super_admin')) else '')) + r,
                ("  var HELP_POPULAR = { " if r.startswith('wa_agent') else "    ") + r + "pasang-hp', '", what='popular ' + r)
    # 4) tampilan artikel: lencana Sering ditanyakan, tombol PDF & Pasang sekarang
    old = ("  function helpItem(a, open) {\n"
           "    return '<div class=\"help-item' + (open ? ' open' : '') + '\">' +\n"
           "      '<button type=\"button\" class=\"help-q\" data-h=\"open\"><span>' + a.t + '</span>' + ico('chevron-down', 16) + '</button>' +\n"
           "      '<div class=\"help-a\"><ol>' + a.s.map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ol>' +\n"
           "      (a.show ?")
    new = ("  // " + TAG + ": prompt instal bawaan browser (Android/Chrome); iPhone tidak punya, cukup ikuti langkah\n"
           "  var pwaPrompt = null;\n"
           "  window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); pwaPrompt = e; });\n"
           "  window.addEventListener('appinstalled', function () { pwaPrompt = null; toast('Dashboard terpasang di layar utama.'); });\n"
           "  function pwaStandalone() { try { return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true; } catch (e) { return false; } }\n"
           "  function helpExtra(a) {\n"
           "    if (!a.pdf) return '';\n"
           "    var h = '';\n"
           "    if (a.id === 'pasang-hp' && pwaStandalone()) h += '<p class=\"help-ok\">' + ico('check-circle-2', 14) + ' Dashboard ini sudah terbuka dari ikon layar utama.</p>';\n"
           "    else if (a.id === 'pasang-hp' && pwaPrompt) h += '<button type=\"button\" class=\"btn sm primary\" data-h=\"install\">' + ico('monitor-smartphone', 14) + ' Pasang sekarang</button> ';\n"
           "    return h + '<a class=\"btn sm\" href=\"' + a.pdf + '\" target=\"_blank\" rel=\"noopener\">' + ico('file-text', 14) + ' Unduh panduan PDF bergambar</a> ';\n"
           "  }\n"
           "  function helpItem(a, open) {\n"
           "    return '<div class=\"help-item' + (open ? ' open' : '') + (a.hot ? ' hot' : '') + '\">' +\n"
           "      '<button type=\"button\" class=\"help-q\" data-h=\"open\"><span>' + a.t + (a.hot ? ' <em class=\"help-hot\">Sering ditanyakan</em>' : '') + '</span>' + ico('chevron-down', 16) + '</button>' +\n"
           "      '<div class=\"help-a\"><ol>' + a.s.map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ol>' + helpExtra(a) +\n"
           "      (a.pdf && !a.show ? '' : a.show ?")
    s = rep(s, old, new, what='helpItem')
    s = rep(s, "      else if (h === 'q') { $('#helpQ').value = b.dataset.q; helpRender(); }\n",
            "      else if (h === 'q') { $('#helpQ').value = b.dataset.q; helpRender(); }\n"
            "      else if (h === 'install' && pwaPrompt) { var pp = pwaPrompt; pwaPrompt = null; pp.prompt(); (pp.userChoice || Promise.resolve({})).then(function () { helpRender(); }); }   // " + TAG + "\n",
            what='klik help')
    save(JS, s)
else: print('sudah', JS)

# ---------------------------------------------------------------- index.html
s = rd(HT)
if TAG not in s:
    s = rep(s, '<script src="app.js?v=1.2.196"></script>', '<script src="app.js?v=1.2.198"></script><!-- ' + TAG + ' -->', what='app.js?v')
    css = ("  /* " + TAG + ": artikel yang sering ditanyakan disorot */\n"
           "  #helpRoot .help-item.hot{border-color:#f5c451;background:#fffaf0}\n"
           "  #helpRoot .help-item.hot .help-q{background:#fffaf0}\n"
           "  #helpRoot .help-hot{display:inline-block;margin-left:6px;padding:1px 8px;border-radius:20px;background:#f59e0b;color:#fff;font-size:10.5px;font-weight:700;font-style:normal;letter-spacing:.02em;vertical-align:2px;white-space:nowrap}\n"
           "  #helpRoot .help-a a.btn{display:inline-flex;align-items:center;gap:6px;text-decoration:none;margin:0 6px 6px 0}\n"
           "  #helpRoot .help-a .btn{margin-bottom:6px}\n"
           "  #helpRoot .help-ok{display:flex;align-items:center;gap:6px;margin:0 0 10px;font-size:13px;color:#15803d}\n")
    s = rep(s, "  #helpRoot .help-chips{display:flex;flex-wrap:wrap;gap:6px}\n", css + "  #helpRoot .help-chips{display:flex;flex-wrap:wrap;gap:6px}\n", what='css help-chips')
    save(HT, s)
else: print('sudah', HT)
print('patch v1.2.198 selesai')
