#!/usr/bin/env python3
"""v1.2.74 tahap 2 — Pusat Bantuan: cari panduan ("cara lihat kontak leads").
  * Tombol "Panduan" membuka Pusat Bantuan: kolom cari, "Sering dicari" per peran, semua topik
  * Tiap artikel: langkah singkat + "Tunjukkan di layar" (tur mini, tetap di halaman tujuan)
  * Tombol "/" membuka pencarian. Kartu Profil Saya ikut punya kolom cari.
Butuh patch_v1274.py dulu. Idempoten. Pakai: patch_v1274_cari.py <root>"""
import sys, pathlib

ROOT = pathlib.Path(sys.argv[1])
F_JS = ROOT / 'dashboard/chatbot-ai/app.js'
F_HTML = ROOT / 'dashboard/chatbot-ai/index.html'


def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count:
        raise SystemExit(f'ANCHOR {n}x (harus {count}): {old[:90]!r}')
    return src.replace(old, new)


html = F_HTML.read_text(encoding='utf-8')
if 'function tourStart(' not in F_JS.read_text(encoding='utf-8'):
    raise SystemExit('butuh patch_v1274.py dulu')

if '#helpRoot' not in html:
    css = r"""  #tourBtns .btn{display:inline-flex;align-items:center;gap:6px}
  /* v1.2.74: PUSAT BANTUAN (cari panduan) */
  #helpRoot{position:fixed;inset:0;z-index:9990;display:none}
  #helpRoot.on{display:block}
  #helpRoot .help-back{position:absolute;inset:0;background:rgba(12,12,32,.45)}
  #helpRoot .help-box{position:absolute;top:8vh;left:50%;transform:translateX(-50%);width:min(620px,calc(100vw - 32px));max-height:84vh;background:#fff;border-radius:16px;box-shadow:0 24px 60px rgba(10,10,40,.3);display:flex;flex-direction:column;overflow:hidden;animation:fade .18s ease}
  #helpRoot .help-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;padding:18px 20px 10px}
  #helpRoot .help-head b{font-size:17px;letter-spacing:-.01em;display:block}
  #helpRoot .help-head small{color:var(--muted);font-size:12.5px}
  #helpRoot .help-x{background:none;border:none;color:var(--muted);cursor:pointer;padding:4px;border-radius:6px;display:flex}
  #helpRoot .help-x:hover{background:var(--bg);color:var(--ink)}
  #helpRoot .help-search{margin:4px 20px 10px;display:flex;align-items:center;gap:10px;border:1.5px solid var(--brand-line);border-radius:12px;padding:0 14px;background:var(--brand-tint);color:var(--brand)}
  #helpRoot .help-search:focus-within{border-color:var(--brand);background:#fff}
  #helpRoot .help-search input{flex:1;border:none;outline:none;background:transparent;font:inherit;font-size:15px;padding:12px 0;color:var(--ink);min-width:0}
  #helpRoot .help-res{overflow-y:auto;padding:4px 20px 14px;flex:1}
  #helpRoot .help-lbl{font-size:11.5px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin:12px 0 6px}
  #helpRoot .help-item{border:1px solid var(--line);border-radius:11px;margin-bottom:8px;overflow:hidden}
  #helpRoot .help-item.open{border-color:var(--brand-line);box-shadow:0 2px 10px rgba(var(--brand-rgb),.06)}
  #helpRoot .help-q{width:100%;display:flex;justify-content:space-between;align-items:center;gap:10px;background:#fff;border:none;padding:12px 14px;font:inherit;font-size:14px;font-weight:600;color:var(--ink);text-align:left;cursor:pointer}
  #helpRoot .help-q:hover{background:var(--bg)}
  #helpRoot .help-q svg{flex-shrink:0;color:var(--muted);transition:transform .2s}
  #helpRoot .help-item.open .help-q svg{transform:rotate(180deg)}
  #helpRoot .help-a{display:none;padding:0 14px 14px}
  #helpRoot .help-item.open .help-a{display:block}
  #helpRoot .help-a ol{margin:0 0 12px 20px;font-size:13.5px;line-height:1.6;color:#3a3a52}
  #helpRoot .help-a li{margin:3px 0}
  #helpRoot .help-a .btn{display:inline-flex;align-items:center;gap:6px}
  #helpRoot .help-chips{display:flex;flex-wrap:wrap;gap:6px}
  #helpRoot .help-chips button{border:1px solid var(--line);background:#fff;border-radius:20px;padding:6px 11px;font:inherit;font-size:12.5px;color:var(--ink);cursor:pointer}
  #helpRoot .help-chips button:hover{border-color:var(--brand);color:var(--brand)}
  #helpRoot .help-empty{color:var(--muted);text-align:center;padding:28px 10px;line-height:1.7}
  #helpRoot .help-foot{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:12px 20px;border-top:1px solid var(--line);background:var(--bg);font-size:13px;color:var(--muted)}
  #helpRoot .help-foot .btn{display:inline-flex;align-items:center;gap:6px}
  .tour-cari{display:flex;gap:8px;margin-bottom:12px}
  .tour-cari input{flex:1}
  @media(max-width:860px){
    #helpRoot .help-box{top:0;left:0;transform:none;width:100vw;height:100%;max-height:none;border-radius:0}
    #helpRoot .help-head{padding-top:max(18px,env(safe-area-inset-top))}
    #helpRoot .help-search input{font-size:16px}
    #helpRoot .help-q{font-size:15px;padding:14px}
    #helpRoot .help-foot span{display:none}
  }"""
    html = rep(html, "  #tourBtns .btn{display:inline-flex;align-items:center;gap:6px}", css)
    html = rep(html, '<p class="hint" id="tourCardNote" style="font-size:13px;color:var(--muted);margin:0 0 12px">Tur singkat menu &amp; fitur sesuai peran Anda.</p>',
               '<div class="tour-cari"><input type="search" id="tourCariQ" placeholder="Cari panduan… mis. cara lihat kontak leads" autocomplete="off"><button type="button" class="btn ghost" id="tourCariBtn"><span data-ico="search"></span> Cari</button></div>\n'
               '        <p class="hint" id="tourCardNote" style="font-size:13px;color:var(--muted);margin:0 0 12px">Tur singkat menu &amp; fitur sesuai peran Anda.</p>')
    html = rep(html, 'title="Tur singkat menu sesuai peran Anda"', 'title="Cari panduan &amp; tur (tekan /)"')
    F_HTML.write_text(html, encoding='utf-8')
    print('html: ok')
else:
    print('html: sudah terpasang')

js = F_JS.read_text(encoding='utf-8')
if 'function helpOpen(' not in js:
    CARI = pathlib.Path(__file__).with_name('cari.js').read_text(encoding='utf-8')
    # 1. hook "pre" per langkah (mis. klik sub-tab) sebelum mencari target
    js = rep(js, """    if (st.tab) showTab(st.tab);
    if (tourIsMobile()) toggleSide(!!st.side);
    var node = tourTarget(st);""", """    if (st.tab) showTab(st.tab);
    if (st.pre) try { st.pre(); } catch (e) {}
    if (tourIsMobile()) toggleSide(!!st.side);
    var node = tourTarget(st);""")
    # 2. penomoran & tombol untuk tur mini (tanpa langkah sambutan)
    js = rep(js, """    var st = tour.steps[tour.i], n = tour.steps.length, last = tour.i === n - 1;
    var who = ROLE_LABEL[tour.role] || tour.role;
    $('#tourStepNo').textContent = st.welcome ? ('Panduan ' + who) : ('Langkah ' + tour.i + ' dari ' + (n - 1));""",
    """    var st = tour.steps[tour.i], n = tour.steps.length, last = tour.i === n - 1;
    var who = ROLE_LABEL[tour.role] || tour.role;
    if (tour.custom) {
      $('#tourStepNo').textContent = n > 1 ? (tour.custom + ' · ' + (tour.i + 1) + '/' + n) : tour.custom;
      $('#tourPrev').innerHTML = '';
      $('#tourTitle').innerHTML = st.title;
      $('#tourBody').innerHTML = st.body;
      $('#tourProg').style.width = Math.round((tour.i + 1) / n * 100) + '%';
      $('#tourBtnsBar').innerHTML = (tour.i === 0 ? '<button type="button" class="btn ghost sm" data-t="help">Cari lagi</button>' : '<button type="button" class="btn ghost sm" data-t="back">Kembali</button>') +
        (last ? '<button type="button" class="btn sm" data-t="finish">Mengerti</button>' : '<button type="button" class="btn sm" data-t="next">Lanjut</button>');
      var fc = document.querySelector('#tourBtnsBar .btn:last-child');
      if (fc) try { fc.focus({ preventScroll: true }); } catch (e) {}
      return;
    }
    $('#tourStepNo').textContent = st.welcome ? ('Panduan ' + who) : ('Langkah ' + tour.i + ' dari ' + (n - 1));""")
    js = rep(js, """      else if (t === 'finish') tourEnd(true);
      else tourEnd(false);""", """      else if (t === 'finish') tourEnd(true);
      else if (t === 'help') { tourEnd(true, true); helpOpen(tour_lastQ()); }
      else tourEnd(false);""")
    # 3. tur mini: tetap di halaman tujuan, tanpa tanda "sudah lihat"/toast
    js = rep(js, """    if (silent) return;
    if (tourIsMobile()) toggleSide(false);
    if (!t.preview) tourMarkSeen();""", """    if (silent) return;
    if (tourIsMobile()) toggleSide(false);
    if (t.custom) return;   // tur mini dari pencarian: biarkan user di halaman tujuan
    if (!t.preview) tourMarkSeen();""")
    js = rep(js, """  function tourEnd(finished, silent) {""", """  function tourStartCustom(steps, title) {
    if (tour) tourEnd(true, true);
    steps = steps.filter(function (s) { return !s.tab || tourTabAllowed(s.tab); });
    if (!steps.length) return;
    tour = { role: role, steps: steps, i: 0, preview: true, custom: title, home: null, t: 0 };
    document.body.classList.add('tour-on');
    tourEls();
    tourGo(0);
  }
  function tour_lastQ() { var q = document.getElementById('helpQ'); return q ? q.value : ''; }
  function tourEnd(finished, silent) {""")
    # 4. tombol Panduan → Pusat Bantuan; kolom cari di Profil Saya
    js = rep(js, """    if ($('#btnTour')) $('#btnTour').onclick = function (e) { e.stopPropagation(); tourStart(role, false); };""",
    """    if ($('#btnTour')) $('#btnTour').onclick = function (e) { e.stopPropagation(); helpOpen(''); };
    if ($('#tourCariBtn')) {
      $('#tourCariBtn').onclick = function () { helpOpen($('#tourCariQ').value); };
      $('#tourCariQ').onkeydown = function (e) { if (e.key === 'Enter') { e.preventDefault(); helpOpen($('#tourCariQ').value); } };
    }""")
    js = rep(js, """      body: '<p>Panduan ini bisa dibuka lagi kapan saja lewat tombol <b>Panduan</b> di bawah menu, atau dari <b>Profil Saya</b>.</p>' }""",
    """      body: '<p>Bingung di tengah jalan? Klik <b>Panduan</b> di bawah menu (atau tekan <b>/</b>) lalu ketik pertanyaan Anda, mis. <i>"cara lihat kontak leads"</i>.</p><p>Tur ini juga bisa diulang dari sana.</p>' }""")
    js = rep(js, "toast('Panduan bisa dibuka lagi lewat tombol \"Panduan\" di bawah menu.');",
             "toast('Cari panduan kapan saja lewat tombol \"Panduan\" di bawah menu.');")
    js = rep(js, "  function tourInit() {", CARI + "\n  function tourInit() {")
    F_JS.write_text(js, encoding='utf-8')
    print('js: ok')
else:
    print('js: sudah terpasang')
