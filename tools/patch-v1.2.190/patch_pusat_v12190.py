#!/usr/bin/env python3
"""v1.2.190: admin-tampilan — tampilan baru Admin Pusat (sidebar, top bar, halaman per menu) + favicon. KHUSUS PUSAT.

  python3 patch_pusat_v12190.py <root dei-pusat>

- admin/favicon.svg (baru)
- admin/index.html: kerangka sidebar + top bar, kartu dikelompokkan per menu, ringkasan dashboard, favicon
- admin/login.html: favicon
Hanya tampilan: tidak ada action backend atau fungsi yang diubah. Idempoten (penanda "v1.2.190: admin-tampilan");
backup *.bak-v12190-<waktu>.
"""
import os, shutil, sys, time

MARK = 'v1.2.190: admin-tampilan'
NEED = 'v1.2.189: mitra-masuk'
STAMP = time.strftime('%Y%m%d-%H%M%S')
HERE = os.path.dirname(os.path.abspath(__file__))


def die(msg):
    print('GAGAL: ' + msg)
    sys.exit(1)


def rep(s, old, new, path):
    if s.count(old) != 1:
        die('jangkar tidak cocok di %s (%d): %r' % (path, s.count(old), old[:90]))
    return s.replace(old, new)


def cut(s, start, end, new, path):
    if s.count(start) != 1 or s.count(end) != 1:
        die('jangkar potong tidak cocok di %s: %r (%d) / %r (%d)' % (path, start[:50], s.count(start), end[:50], s.count(end)))
    a = s.index(start); b = s.index(end)
    if b <= a:
        die('urutan jangkar salah di ' + path)
    return s[:a] + new + s[b:]


def patch(root, rel, fn, need):
    path = os.path.join(root, rel)
    with open(path, encoding='utf-8') as f:
        s = f.read()
    if MARK in s:
        print('lewati (sudah dipatch): ' + rel)
        return
    if need and need not in s:
        die(rel + ' belum dipatch ' + need)
    out = fn(s, rel)
    shutil.copy2(path, path + '.bak-v12190-' + STAMP)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(out)
    print('dipatch: ' + rel)


HEAD = '''<link rel="icon" type="image/svg+xml" href="favicon.svg"><!-- v1.2.190: admin-tampilan -->
<meta name="theme-color" content="#140383">
'''

CSS = r'''  /* ---------- v1.2.190: admin-tampilan — sidebar, top bar, halaman per menu ---------- */
  :root{--side:#140383;--ink:#1a1a2e;--soft:#eef0fb}
  body{background:#f3f4f9}
  button{border-radius:8px;font-weight:600}
  .shell{display:flex;min-height:100vh}
  .side{width:218px;flex-shrink:0;background:var(--side);color:#fff;display:flex;flex-direction:column;position:sticky;top:0;height:100vh;overflow-y:auto;z-index:40}
  .side .brand{display:flex;align-items:center;gap:11px;padding:18px 18px 14px;font-weight:800;font-size:15px;line-height:1.15;letter-spacing:.4px}
  .side .brand img{width:34px;height:34px;border-radius:9px;box-shadow:0 0 0 1px rgba(255,255,255,.25)}
  .side .brand small{display:block;font-weight:500;font-size:11px;opacity:.7;letter-spacing:.5px;margin-top:2px}
  .side nav{padding:8px 10px;display:flex;flex-direction:column;gap:2px;flex:1}
  .side nav button{background:none;color:#dcdfff;display:flex;align-items:center;gap:11px;width:100%;text-align:left;padding:10px 12px;border-radius:8px;font-size:14px;font-weight:500}
  .side nav button:hover{background:rgba(255,255,255,.08);opacity:1}
  .side nav button.on{background:rgba(255,255,255,.17);color:#fff;font-weight:600}
  .side nav .nb{margin-left:auto;background:#ef4444;color:#fff;border-radius:9px;padding:1px 7px;font-size:11px;font-weight:700}
  .side .foot{padding:12px 18px 16px;font-size:11.5px;color:#c9ccf5;line-height:1.7}
  .side .foot a{color:#fff;text-decoration:none} .side .foot a:hover{text-decoration:underline}
  .mainwrap{flex:1;min-width:0;display:flex;flex-direction:column}
  header.top{position:sticky;top:0;z-index:30;padding:12px 24px;gap:12px;flex-wrap:nowrap}
  header.top h1{font-size:15.5px;color:var(--ink);text-transform:uppercase;letter-spacing:.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  header.top h1 span{color:var(--muted);font-weight:500}
  .burger{display:none;background:none;color:var(--ink);padding:6px}
  .srch{position:relative;flex-shrink:1;min-width:0} .srch svg{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:#8a90a6;pointer-events:none}
  .srch input{width:250px;max-width:100%;padding:9px 12px 9px 36px;border:1px solid transparent;background:#f1f2f7;border-radius:20px;font-size:13.5px;font-family:inherit;outline:none}
  .srch input:focus{border-color:var(--brand);background:#fff}
  .ibtn{background:none;color:#33384c;position:relative;padding:7px;border-radius:50%} .ibtn:hover{background:#f1f2f7;opacity:1}
  .ibtn .nb{position:absolute;top:0;right:0;background:#ef4444;color:#fff;border-radius:9px;min-width:17px;padding:1px 4px;font-size:10.5px;font-weight:700;line-height:15px;text-align:center}
  .usr{display:flex;align-items:center;gap:9px;padding-left:12px;border-left:1px solid var(--line);white-space:nowrap}
  .usr .ava{width:34px;height:34px;border-radius:50%;background:var(--brand);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px}
  .usr b{display:block;font-size:13.5px;line-height:1.2} .usr small{color:var(--muted);font-size:11.5px}
  main{max-width:none;margin:0;width:100%;padding:22px 24px}
  .view{display:none} .view.on{display:block}
  .vtitle{font-size:15px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;margin:0 0 14px;color:var(--ink)}
  .card{border-radius:14px;box-shadow:0 1px 2px rgba(20,3,131,.04)}
  .view .grid{gap:16px}
  .view .grid>.stat{border-radius:14px;padding:16px 18px;display:flex;justify-content:space-between;align-items:center;gap:10px;box-shadow:0 1px 2px rgba(20,3,131,.04)}
  .view .grid>.stat .l{margin:0 0 4px;font-size:12px;letter-spacing:.5px;color:#33384c;font-weight:600}
  .view .grid>.stat .v{font-size:27px;color:var(--ink);line-height:1.1}
  .view .grid>.stat .si{width:44px;height:44px;border-radius:12px;background:var(--soft);color:var(--brand);display:flex;align-items:center;justify-content:center;flex-shrink:0}
  .dash2{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:18px} .dash2>*{min-width:0}
  .rl{display:flex;flex-direction:column} .rl .ri{display:flex;gap:12px;padding:10px 0;border-bottom:1px solid var(--line);align-items:flex-start}
  .rl .ri:last-child{border-bottom:none} .rl .ic{width:34px;height:34px;border-radius:50%;background:var(--soft);color:var(--brand);display:flex;align-items:center;justify-content:center;flex-shrink:0}
  .rl .tx{flex:1;min-width:0;font-size:13px} .rl .tx b{display:block;font-size:13.5px} .rl .tx span{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;color:#33384c}
  .rl .dt{font-size:12px;color:var(--muted);white-space:nowrap}
  .tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
  .tile{border:1px solid var(--line);border-radius:12px;padding:13px 14px;cursor:pointer;background:#fff;transition:border-color .15s,box-shadow .15s}
  .tile:hover{border-color:var(--brand);box-shadow:0 2px 10px rgba(20,3,131,.08)}
  .tile .th{display:flex;align-items:center;gap:10px;font-weight:700;font-size:14px} .tile .th .ic{width:34px;height:34px;border-radius:9px;background:var(--soft);color:var(--brand);display:flex;align-items:center;justify-content:center;flex-shrink:0}
  .tile .th [data-mirror]{margin-left:auto} .tile .th .badge{white-space:nowrap}
  .tile p{margin:8px 0 8px;font-size:12.5px;color:#33384c;min-height:32px} .tile a{color:var(--brand);font-weight:600;font-size:13px;text-decoration:none}
  .shade{display:none}
  @media(max-width:1000px){ .dash2{grid-template-columns:minmax(0,1fr)} .srch input{width:170px} }
  @media(max-width:860px){
    .side{position:fixed;left:0;top:0;transform:translateX(-100%);transition:transform .2s;box-shadow:0 0 30px rgba(0,0,0,.3)} .shell.open .side{transform:none}
    .shell.open .shade{display:block;position:fixed;inset:0;background:rgba(10,10,40,.4);z-index:35}
    .burger{display:block} header.top{padding:10px 14px} header.top h1 span,.usr div,.srch{display:none} .usr{border-left:none;padding-left:0}
    main{padding:14px} .tiles{grid-template-columns:minmax(0,1fr)} .view .grid>.stat .v{font-size:22px} .view .grid>.stat .si{display:none}
  }
'''

SHELL_TOP = r'''<div class="shell" id="shell"><!-- v1.2.190: admin-tampilan -->
<aside class="side">
  <div class="brand"><img src="favicon.svg" alt=""><div>DEI CHATBOT<small>ADMIN PUSAT</small></div></div>
  <nav id="sideNav"></nav>
  <div class="foot"><a href="../mitra/" target="_blank" rel="noopener">Portal Mitra ↗</a><br><a href="../grup/" target="_blank" rel="noopener">Dashboard Grup ↗</a><br><a href="../daftar/" target="_blank" rel="noopener">Halaman pendaftaran ↗</a></div>
</aside>
<div class="shade" onclick="document.getElementById('shell').classList.remove('open')"></div>
<div class="mainwrap">
<header class="top">
  <button class="burger" id="btnBurger" aria-label="Menu"></button>
  <h1><b id="viewTitle">Dashboard</b> <span>| Admin Pusat</span></h1>
  <div class="grow"></div>
  <div class="srch"><span id="srchIco"></span><input id="gSearch" type="search" placeholder="Cari tenant…" autocomplete="off"></div>
  <button class="ibtn" id="btnBell" title="Permintaan WhatsApp API"></button>
  <div class="usr"><span class="ava" id="userAva">A</span><div><b id="userPill">…</b><small>Admin</small></div></div>
  <button class="ghost" id="btnLogout">Keluar</button>
</header>
<main>
 <section class="view on" data-view="dash">
  <div class="vtitle">Ringkasan tenant</div>
  <div class="grid">
    <div class="stat"><div><div class="l">Total Tenant</div><div class="v" id="kTenants">–</div></div><div class="si" data-ico="building"></div></div>
    <div class="stat"><div><div class="l">Aktif (24 jam)</div><div class="v" id="kActive">–</div></div><div class="si" data-ico="activity"></div></div>
    <div class="stat"><div><div class="l">Versi Terkini</div><div class="v" id="kVer">–</div></div><div class="si" data-ico="refresh"></div></div>
    <div class="stat"><div><div class="l">Chat Hari Ini (semua)</div><div class="v" id="kChats">–</div></div><div class="si" data-ico="message"></div></div>
  </div>

'''

DASH_EXTRA = r'''  <div class="dash2"><!-- v1.2.190: admin-tampilan — ringkasan dashboard -->
    <div class="card">
      <div class="row" style="justify-content:space-between;margin-bottom:6px"><h2 style="margin:0">Rilis &amp; pembaruan terbaru</h2><button onclick="goView('rilis')">Lihat semua</button></div>
      <div class="rl" id="dashRel"><div class="hint">memuat…</div></div>
    </div>
    <div class="card">
      <h2>Pusat Fitur</h2>
      <div class="tiles" id="dashTiles"></div>
    </div>
  </div>
 </section>

'''


def sec(v):
    return ' </section>\n\n <section class="view" data-view="%s">\n' % v


JS = r'''
// v1.2.190: admin-tampilan — navigasi sidebar, pencarian tenant, ringkasan dashboard
Object.assign(ICONS,{
  layout:'<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
  refresh:'<path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 4v5h-5"/>',
  message:'<path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
  users:'<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><circle cx="17.5" cy="9" r="2.5"/><path d="M17 14.5a5 5 0 0 1 4.5 5"/>',
  partner:'<circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.2 10.9l7.6-3.8M8.2 13.1l7.6 3.8"/>',
  userplus:'<circle cx="10" cy="8" r="3.5"/><path d="M3 20a7 7 0 0 1 14 0"/><path d="M19 8v6M16 11h6"/>',
  search:'<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
  menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
  building:'<path d="M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"/><path d="M16 9h2a2 2 0 0 1 2 2v10"/><path d="M2 21h20M8 7h4M8 11h4M8 15h4"/>',
  activity:'<path d="M3 12h4l3-8 4 16 3-8h4"/>',
  tag:'<path d="M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9z"/><circle cx="8" cy="8" r="1.5"/>'
});
const NAV=[['dash','Dashboard','layout'],['rilis','Rilis & Update','refresh'],['war','WhatsApp API','message'],['grp','Dashboard Grup','users'],
  ['mitra','Mitra / Reseller','partner'],['daftar','Pendaftaran & Trial','userplus'],['bayar','Pembayaran','wallet'],['cfg','Pengaturan','settings']];
const TILES=[['mitra','Mitra / Reseller','Kode mitra, tier komisi, dan buku komisi.','partner','ptBadge'],['grp','Dashboard Grup','Satu login untuk klien dengan beberapa tenant.','users',''],
  ['daftar','Pendaftaran & Trial','Pendaftaran mandiri, OTP, dan masa trial.','userplus',''],['bayar','Pembayaran Online','Harga paket, Duitku, dan daftar pesanan.','wallet','blBadge'],
  ['war','WhatsApp API','Permintaan WhatsApp API resmi dari tenant.','message','warBadge'],['cfg','Topik AI & Notifikasi','Klasifikasi topik dan alarm Telegram.','tag','']];
window.goView=function(v,keep){
  if(!NAV.some(n=>n[0]===v)) v='dash';
  $$('.view').forEach(s=>s.classList.toggle('on',s.dataset.view===v));
  $$('#sideNav button').forEach(b=>b.classList.toggle('on',b.dataset.v===v));
  $('#viewTitle').textContent=NAV.find(n=>n[0]===v)[1];
  $('#shell').classList.remove('open');
  try{ history.replaceState(null,'','#'+v); }catch(e){}
  if(!keep) window.scrollTo(0,0);
};
(function(){
  $('#sideNav').innerHTML=NAV.map(n=>`<button data-v="${n[0]}" onclick="goView('${n[0]}')">${ico(n[2],18)}<span>${esc(n[1])}</span><span class="nb" id="nb_${n[0]}" style="display:none"></span></button>`).join('');
  $('#dashTiles').innerHTML=TILES.map(t=>`<div class="tile" onclick="goView('${t[0]}')"><div class="th"><span class="ic">${ico(t[3],18)}</span>${esc(t[1])} <span data-mirror="${t[4]}"></span></div><p>${esc(t[2])}</p><a href="#${t[0]}" onclick="event.preventDefault()">Kelola</a></div>`).join('');
  $$('.si[data-ico]').forEach(e=>e.innerHTML=ico(e.dataset.ico,22));
  $('#srchIco').innerHTML=ico('search',16); $('#btnBurger').innerHTML=ico('menu',22); $('#btnBell').innerHTML=ico('bell',20)+'<span class="nb" id="bellN" style="display:none"></span>';
  $('#btnBurger').onclick=()=>$('#shell').classList.toggle('open');
  $('#btnBell').onclick=()=>goView('war');
  $('#userAva').textContent=(($('#userPill').textContent||'A').trim()[0]||'A').toUpperCase();
  // lencana: salin dari kartu aslinya (permintaan WA baru, komisi belum dibayar, pesanan bulan ini)
  const mirror=()=>{
    const n=parseInt((($('#warBadge')||{}).textContent||'').replace(/\D/g,''),10)||0;
    [['#nb_war',n],['#bellN',n]].forEach(([s,v])=>{ const e=$(s); if(e){ e.textContent=v; e.style.display=v?'':'none'; } });
    $$('[data-mirror]').forEach(e=>{ const src=e.dataset.mirror&&$('#'+e.dataset.mirror); const h=src?src.innerHTML:''; if(e.innerHTML!==h) e.innerHTML=h; });
  };
  ['warBadge','ptBadge','blBadge'].forEach(id=>{ const e=$('#'+id); if(e) new MutationObserver(mirror).observe(e,{childList:true,subtree:true,characterData:true}); });
  mirror();
  // pencarian tenant: menyaring baris Daftar Tenant, bertahan saat tabel dimuat ulang
  const filt=()=>{ const q=$('#gSearch').value.trim().toLowerCase(); $$('#tbl tbody tr').forEach(r=>{ r.style.display=(!q||r.textContent.toLowerCase().includes(q))?'':'none'; }); };
  $('#gSearch').addEventListener('input',()=>{ if(!$('.view[data-view="dash"]').classList.contains('on')) goView('dash',true); filt(); });
  new MutationObserver(filt).observe($('#tbl tbody'),{childList:true});
  window.addEventListener('hashchange',()=>goView(location.hash.slice(1),true));
  goView(location.hash.slice(1)||'dash',true);
})();
window.navRel=function(){
  const L=(window._rel||[]).slice(0,4);
  $('#dashRel').innerHTML=L.length?L.map(r=>`<div class="ri"><span class="ic">${ico('refresh',16)}</span><div class="tx"><b>${esc(r.version)}${r.has_zip?'':' <span class="badge off">ZIP hilang</span>'}</b><span>${esc(r.changelog||'Tanpa catatan.')}</span></div><div class="dt">${esc(String(r.released_at||'').slice(0,10))}</div></div>`).join('')
    :'<div class="hint">Belum ada rilis.</div>';
};
if(window._rel) navRel();
'''


def p_admin(s, rel):
    s = rep(s, '<title>Admin Pusat — DEI Chat-Bot</title>\n', '<title>Admin Pusat — DEI Chatbot</title>\n' + HEAD, rel)
    s = rep(s, '</style>\n</head>', CSS + '</style>\n</head>', rel)
    s = cut(s, '<header>\n  <h1>', '  <div class="card">\n    <div class="row" style="justify-content:space-between">\n      <h2>Daftar Tenant</h2>', SHELL_TOP, rel)
    a = '  <div class="card">\n    <h2>Versi Rilis</h2>'
    s = rep(s, a, DASH_EXTRA + ' <section class="view" data-view="rilis">\n' + a, rel)
    for v, a in (('war', '  <!-- v1.2.91: wa-api — permintaan WhatsApp API resmi -->'),
                 ('grp', '  <!-- v1.2.185: master-grup — Dashboard Grup -->'),
                 ('mitra', '  <!-- v1.2.187: mitra — Program Mitra (reseller / referral) -->'),
                 ('daftar', '  <!-- v1.2.90: Pendaftaran mandiri -->'),
                 ('bayar', '  <div class="card" id="blCard">'),
                 ('cfg', '  <div class="card"><!-- v1.2.138: filter-topik -->')):
        s = rep(s, a, sec(v) + a, rel)
    a = '</main>\n\n<div class="modal-bg" id="modalBg">'
    s = rep(s, a, ' </section>\n</main>\n</div>\n</div>\n\n<div class="modal-bg" id="modalBg">', rel)
    a = "    const list=res.releases||[];\n    $('#releases').innerHTML = list.length"
    s = rep(s, a, "    const list=res.releases||[];\n    window._rel=list; if(window.navRel) navRel();   // " + MARK + "\n    $('#releases').innerHTML = list.length", rel)
    s = rep(s, '</script>\n</body>', JS + '</script>\n</body>', rel)
    return s


def p_login(s, rel):
    return rep(s, '<title>Login — Admin Pusat</title>\n', '<title>Login — Admin Pusat</title>\n' + HEAD, rel)


def main():
    if len(sys.argv) != 2:
        die('pakai: python3 patch_pusat_v12190.py <root dei-pusat>')
    root = os.path.abspath(sys.argv[1])
    src = os.path.join(HERE, 'favicon.svg'); dst = os.path.join(root, 'admin', 'favicon.svg')
    if not os.path.isfile(src):
        die('favicon.svg tidak ada di samping skrip ini')
    if not os.path.isfile(dst) or open(src, 'rb').read() != open(dst, 'rb').read():
        shutil.copy2(src, dst); print('disalin: admin/favicon.svg')
    else:
        print('lewati (sama): admin/favicon.svg')
    patch(root, 'admin/index.html', p_admin, NEED)
    patch(root, 'admin/login.html', p_login, '')
    print('SELESAI v1.2.190 admin-tampilan')


if __name__ == '__main__':
    main()
