#!/usr/bin/env python3
"""v1.2.136 aktif-fix: penanda chat aktif WA (nomor angka vs teks) + kolom cari WA flat. Idempoten."""
import os, sys
T=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd/dei-tenant'); TAG='v1.2.136: aktif-fix'
def rep(p,a,b):
    p=T+'/'+p; s=open(p,encoding='utf-8').read()
    if b in s: return
    assert s.count(a)==1,(p,a[:70]); open(p,'w',encoding='utf-8').write(s.replace(a,b))
A='dashboard/chatbot-ai/app.js'; H='dashboard/chatbot-ai/index.html'
rep(A,"var bg = (c.number === waState.current) ? 'background:var(--brand-soft);' : '';",
      "var _open = String(c.number) === String(waState.current);   // "+TAG+": nomor bisa angka dari API\n      var bg = _open ? 'background:var(--brand-soft);' : '';")
rep(A,"""return '<div class="wa-conv' + (c.number === waState.current ? ' is-open' : '') + '\"""",
      """return '<div class="wa-conv' + (_open ? ' is-open' : '') + '\"""")
rep(A,"""(webState.current === c.id ? ' is-open' : '')""","""(String(webState.current) === String(c.id) ? ' is-open' : '')""")
rep(A,"var active = (webState.current === c.id) ? 'background:var(--brand-soft);' : '';","var active = (String(webState.current) === String(c.id)) ? 'background:var(--brand-soft);' : '';")
rep(A,"el.classList.toggle('is-open', el.dataset.cid === convId);","el.classList.toggle('is-open', el.dataset.cid === String(convId));")
rep(H,"#waSearch{width:100%;padding:8px 12px 8px 34px;border-radius:10px;background:var(--bg);font-size:13.5px}",
      "#waSearch{width:100%;padding:8px 12px 8px 34px;border-radius:10px;background:var(--bg);font-size:13.5px}\n#waSearch{border:1px solid var(--line)!important;box-shadow:none!important;outline:none!important;-webkit-appearance:none;appearance:none}   /* "+TAG+": flat */\n#waSearch:focus{border-color:var(--brand)!important;background:#fff}")
rep(H,'<script src="app.js?v=1.2.135"></script><!-- v1.2.135: wa-fix -->','<script src="app.js?v=1.2.136"></script><!-- '+TAG+' -->')
rep('api/index.php',"define('DEI_VERSION', 'v1.2.135');   // v1.2.135: wa-fix","define('DEI_VERSION', 'v1.2.136');   // "+TAG)
print('ok')
