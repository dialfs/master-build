#!/usr/bin/env python3
"""v1.2.169 tema-warna (TENANT): pemilih tema warna dashboard (8 pilihan, disimpan per browser di localStorage 'dei_theme').
Hanya dashboard; widget chat pengunjung tetap pakai primary_color. Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HTML = T + '/dashboard/chatbot-ai/index.html'
TAG = 'v1.2.169: tema-warna'; stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label):
    n = s.count(old); assert n == 1, '%s: anchor %d kali' % (label, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    shutil.copy2(p, p + '.bak-v12169-' + stamp); wr(p, fn(s)); print('OK', p)

def api(s):
    return rep(s, "define('DEI_VERSION', 'v1.2.168');   // v1.2.168:",
                  "define('DEI_VERSION', 'v1.2.169');   // " + TAG + " — pilih tema warna dashboard (8 pilihan, per browser); v1.2.168:", 'versi')

HEAD_JS = r"""<script>/* """ + TAG + r""" — tema warna dashboard, per browser (localStorage dei_theme). Kosong = bawaan/brand instalasi. */
(function(){
  // c: [brand, brand-2, brand-mid, brand-hero(aksen), soft, line, tint, tint-2, bg]   p: palet grafik
  var T = {
    samudra: {n:'Samudra', d:'Biru laut + toska', c:['#0b4f8a','#1d7fc4','#12639f','#22b8cf','#e5f0fa','#bcd8ee','#f3f8fd','#eaf3fb','#f2f6fa'], p:['#0b4f8a','#1d7fc4','#22b8cf','#5fd0c5','#3b82f6','#93c5fd','#0e7490','#94a3b8']},
    hutan:   {n:'Hutan',   d:'Hijau zamrud + daun', c:['#0b5d45','#12936a','#0d7556','#4cc38a','#e2f4ec','#b5e0cb','#f2faf6','#e8f6ef','#f2f7f4'], p:['#0b5d45','#12936a','#4cc38a','#a3d977','#0e7490','#6ee7b7','#65a30d','#94a3b8']},
    toska:   {n:'Toska Koral', d:'Teal + koral', c:['#0f766e','#14a39a','#0d8c83','#fb7185','#e1f4f2','#b2e1dc','#f1faf9','#e7f6f4','#f2f7f7'], p:['#0f766e','#14a39a','#fb7185','#5eead4','#f59e0b','#0891b2','#fda4af','#94a3b8']},
    senja:   {n:'Senja',   d:'Merah mawar + jingga', c:['#a3213f','#df4f45','#c2353f','#f59e0b','#fde8eb','#f4c0c8','#fef5f6','#fdecee','#faf5f4'], p:['#a3213f','#df4f45','#f59e0b','#f97316','#e879a6','#fbbf24','#7c2d12','#94a3b8']},
    anggur:  {n:'Anggur',  d:'Ungu plum + magenta', c:['#5e1a73','#9b36b0','#7a2490','#e05fa8','#f4e7f7','#e0c2e8','#fbf5fc','#f5ebf8','#f8f4f9'], p:['#5e1a73','#9b36b0','#e05fa8','#c084fc','#f472b6','#7c3aed','#fda4af','#94a3b8']},
    kopi:    {n:'Kopi Susu', d:'Cokelat mocha + karamel', c:['#5a3825','#8c5a3a','#714630','#d9a066','#f3ebe4','#e2cdbb','#faf6f2','#f5ede6','#f7f4f0'], p:['#5a3825','#8c5a3a','#d9a066','#b07d4f','#e6c9a8','#7c5c45','#a8a29e','#94a3b8']},
    grafit:  {n:'Grafit',  d:'Abu gelap + kuning amber', c:['#1e293b','#475569','#334155','#f59e0b','#e9edf2','#cbd3dd','#f6f7f9','#eef1f4','#f3f4f6'], p:['#1e293b','#475569','#f59e0b','#64748b','#0ea5e9','#fbbf24','#94a3b8','#cbd5e1']}
  };
  var cur = '';
  function rgb(h){ h = h.replace('#',''); return parseInt(h.substr(0,2),16)+','+parseInt(h.substr(2,2),16)+','+parseInt(h.substr(4,2),16); }
  function css(t){ var c = t.c; return ':root{--brand:'+c[0]+';--brand-2:'+c[1]+';--brand-mid:'+c[2]+';--brand-hero:'+c[3]+';--brand-soft:'+c[4]+';--brand-line:'+c[5]+
    ';--brand-tint:'+c[6]+';--brand-tint-2:'+c[7]+';--bg:'+c[8]+';--brand-rgb:'+rgb(c[0])+';--brand-2-rgb:'+rgb(c[1])+';--brand-hero-rgb:'+rgb(c[3])+'}'; }
  function apply(id){
    var t = T[id] || null; cur = t ? id : '';
    var el = document.getElementById('dei-theme-css');
    if (!el) { el = document.createElement('style'); el.id = 'dei-theme-css'; document.head.appendChild(el); }
    el.textContent = t ? css(t) : '';
    var m = document.querySelector('meta[name="theme-color"]');
    if (m) m.setAttribute('content', t ? t.c[0] : ((window.DEI_BRAND && window.DEI_BRAND.theme) || '#140383'));
    window.DEI_THEME = t ? {id: id, c1: t.c[0], c2: t.c[3], palette: t.p} : null;
    return window.DEI_THEME;
  }
  window.DEI_THEMES = T; window.deiThemeApply = apply;
  try { cur = localStorage.getItem('dei_theme') || ''; } catch (e) {}
  apply(cur);
  // brand_js menimpa meta theme-color saat DOMContentLoaded; terapkan ulang sesudahnya
  document.addEventListener('DOMContentLoaded', function(){ apply(cur); });
})();
</script>
"""

CSS = """  /* """ + TAG + """ */
  .thm-ov{position:fixed;inset:0;background:rgba(15,15,35,.45);z-index:9000;display:flex;align-items:center;justify-content:center;padding:16px}
  .thm-box{background:#fff;border-radius:16px;width:100%;max-width:640px;max-height:90vh;overflow:auto;box-shadow:0 20px 60px rgba(0,0,0,.25);padding:20px 20px 18px}
  .thm-hd{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:4px}
  .thm-hd h3{font-size:17px;letter-spacing:-.01em;flex:1;margin:0}
  .thm-x{background:none;border:0;cursor:pointer;color:var(--muted);padding:4px;border-radius:8px;display:inline-flex}
  .thm-x:hover{background:var(--bg);color:var(--ink)}
  .thm-sub{color:var(--muted);font-size:12.5px;margin-bottom:14px;line-height:1.5}
  .thm-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px}
  .thm-card{position:relative;border:2px solid var(--line);border-radius:12px;overflow:hidden;cursor:pointer;background:#fff;text-align:left;font-family:inherit;padding:0;transition:transform .12s,border-color .12s,box-shadow .12s}
  .thm-card:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(0,0,0,.08)}
  .thm-card.on{border-color:var(--brand);box-shadow:0 0 0 3px rgba(var(--brand-rgb),.15)}
  .thm-pv{height:64px;position:relative;display:flex}
  .thm-pv .sb{width:30%;background:rgba(255,255,255,.88);display:flex;flex-direction:column;gap:5px;padding:9px 7px}
  .thm-pv .sb i{display:block;height:5px;border-radius:3px;background:#e5e7ef}
  .thm-pv .sb i:first-child{width:70%}
  .thm-pv .mn{flex:1;padding:9px 8px;display:flex;flex-direction:column;gap:6px}
  .thm-pv .mn i{display:block;height:14px;border-radius:5px}
  .thm-pv .mn i+i{height:9px;width:60%;background:rgba(255,255,255,.85)}
  .thm-dots{display:flex;gap:4px;padding:9px 11px 0}
  .thm-dots span{width:14px;height:14px;border-radius:50%;border:1px solid rgba(0,0,0,.06)}
  .thm-nm{padding:6px 11px 10px;font-size:13px;font-weight:600;color:var(--ink)}
  .thm-nm small{display:block;font-weight:400;color:var(--muted);font-size:11.5px;margin-top:1px}
  .thm-ok{position:absolute;top:7px;right:7px;width:22px;height:22px;border-radius:50%;background:#fff;color:var(--brand);font-size:13px;font-weight:700;display:none;align-items:center;justify-content:center;box-shadow:0 1px 4px rgba(0,0,0,.2)}
  .thm-card.on .thm-ok{display:flex}
  @media(max-width:480px){.thm-grid{grid-template-columns:1fr 1fr;gap:9px}.thm-box{padding:16px 14px}}
"""

def html(s):
    s = rep(s, '</script>\n</head>', '</script>\n' + HEAD_JS + '</head>', 'head-js')
    s = rep(s, '  @media(max-width:760px){.lk-col{flex-basis:78vw}}\n</style>',
               '  @media(max-width:760px){.lk-col{flex-basis:78vw}}\n' + CSS + '</style>', 'css')
    s = rep(s, '<button id="btnTour" type="button"',
               '<button id="btnTheme" type="button" title="Ganti tema warna dashboard"><span data-ico="palette"></span> Tema</button><!-- ' + TAG + ' --><button id="btnTour" type="button"', 'btn')
    return rep(s, '<script src="app.js?v=1.2.168"></script><!-- v1.2.168: kuota-unit -->',
                  '<script src="app.js?v=1.2.169"></script><!-- ' + TAG + ' --><!-- v1.2.168: kuota-unit -->', 'appjs')

MOD = r"""  /* ---- """ + TAG + r""": pemilih tema warna dashboard (per browser) ---- */
  var THM_PIE0 = PIE_COLORS.slice(), THM_TP0 = TP_COL.slice();
  function thmSync() {
    var t = window.DEI_THEME;
    BRAND_C1 = (t && t.c1) || (BRAND && BRAND.c1) || '#140383';
    BRAND_C2 = (t && t.c2) || (BRAND && BRAND.c2) || '#a855f7';
    var p = (t && t.palette && t.palette.length) ? t.palette : null;
    PIE_COLORS.splice.apply(PIE_COLORS, [0, PIE_COLORS.length].concat(p || THM_PIE0));
    TP_COL.splice.apply(TP_COL, [0, TP_COL.length].concat(p || THM_TP0));
    LG_ST.ai[1] = BRAND_C1;
  }
  function thmCur() { try { return localStorage.getItem('dei_theme') || ''; } catch (e) { return ''; } }
  function thmCard(id, name, desc, c, dots) {
    var on = thmCur() === id;
    return '<button type="button" class="thm-card' + (on ? ' on' : '') + '" data-thm="' + id + '">' +
      '<div class="thm-pv" style="background:radial-gradient(120% 140% at 100% 0%,' + c[2] + ' 0%,transparent 55%),linear-gradient(135deg,' + c[0] + ' 0%,' + c[1] + ' 100%)">' +
        '<div class="sb"><i></i><i style="background:' + c[0] + ';opacity:.35"></i><i></i><i></i></div>' +
        '<div class="mn"><i style="background:' + c[2] + '"></i><i></i></div></div>' +
      '<div class="thm-dots">' + dots.slice(0, 6).map(function (d) { return '<span style="background:' + d + '"></span>'; }).join('') + '</div>' +
      '<div class="thm-nm">' + esc(name) + '<small>' + esc(desc) + '</small></div><span class="thm-ok">&#10003;</span></button>';
  }
  function thmOpen() {
    var T = window.DEI_THEMES || {};
    var d1 = (BRAND && BRAND.c1) || '#140383', d2 = (BRAND && BRAND.c2) || '#a855f7';
    var dPal = THM_PIE0.length ? THM_PIE0 : [d1, d2];
    var h = thmCard('', 'Bawaan ' + BRAND_VENDOR, BRAND ? 'Warna brand ' + BRAND_VENDOR : 'Indigo khas DEI', [d1, BRAND ? d2 : '#3b2fb8', BRAND ? d2 : '#5b4fe0'], dPal);
    Object.keys(T).forEach(function (id) { var t = T[id]; h += thmCard(id, t.n, t.d, [t.c[0], t.c[1], t.c[3]], t.p); });
    var ov = document.createElement('div');
    ov.className = 'thm-ov';
    ov.innerHTML = '<div class="thm-box" role="dialog" aria-label="Tema warna"><div class="thm-hd"><h3>Tema warna</h3><button type="button" class="thm-x" aria-label="Tutup">' + ico('x', 18) + '</button></div>' +
      '<div class="thm-sub">Ganti suasana dashboard. Tersimpan di browser/perangkat ini saja. Warna widget chat untuk pengunjung tetap diatur di <b>Balasan &amp; Tampilan</b>.</div>' +
      '<div class="thm-grid">' + h + '</div></div>';
    function close() { ov.remove(); document.removeEventListener('keydown', onKey); }
    function onKey(e) { if (e.key === 'Escape') close(); }
    ov.addEventListener('click', function (e) {
      if (e.target === ov || e.target.closest('.thm-x')) { close(); return; }
      var c = e.target.closest('[data-thm]'); if (!c) return;
      var id = c.dataset.thm;
      try { if (id) localStorage.setItem('dei_theme', id); else localStorage.removeItem('dei_theme'); } catch (er) {}
      if (window.deiThemeApply) window.deiThemeApply(id);
      thmSync();
      Array.prototype.forEach.call(ov.querySelectorAll('.thm-card'), function (x) { x.classList.toggle('on', x === c); });
      toast('Tema "' + (id && T[id] ? T[id].n : 'Bawaan') + '" diterapkan. Grafik ikut berubah saat dimuat ulang.');
    });
    document.addEventListener('keydown', onKey);
    document.body.appendChild(ov);
  }
  thmSync();
  if ($('#btnTheme')) $('#btnTheme').onclick = function (e) { e.stopPropagation(); thmOpen(); };

"""

def js(s):
    s = rep(s, "  var ICONS_EXTRA = {\n",
               "  var ICONS_EXTRA = {\n    'palette': '<circle cx=\"13.5\" cy=\"6.5\" r=\".5\" fill=\"currentColor\"/><circle cx=\"17.5\" cy=\"10.5\" r=\".5\" fill=\"currentColor\"/><circle cx=\"8.5\" cy=\"7.5\" r=\".5\" fill=\"currentColor\"/><circle cx=\"6.5\" cy=\"12.5\" r=\".5\" fill=\"currentColor\"/><path d=\"M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 11.994 2z\"/>',   // " + TAG + "\n", 'ikon')
    s = rep(s, "var color = d.calls > 0 ? '#140383' : '#e2e5ee';", "var color = d.calls > 0 ? BRAND_C1 : '#e2e5ee';   // " + TAG, 'bar')
    return rep(s, "  // first tab per role\n", MOD + "  // first tab per role\n", 'modul')

patch(API, api); patch(HTML, html); patch(JS, js)
