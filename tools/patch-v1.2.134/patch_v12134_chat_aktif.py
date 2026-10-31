#!/usr/bin/env python3
"""v1.2.134 chat-aktif: penanda chat yang sedang dibuka (garis kiri oranye). Idempoten."""
import os, sys
T=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd/dei-tenant'); TAG='v1.2.134: chat-aktif'
def rep(p, pairs):
    p=T+'/'+p; s=open(p,encoding='utf-8').read(); o=s
    for a,b in pairs:
        if b in s: continue
        assert s.count(a)==1, (p,a[:60]); s=s.replace(a,b)
    if s!=o: open(p,'w',encoding='utf-8').write(s)
rep('dashboard/chatbot-ai/app.js',[
 ("""      return '<div class="wa-conv" data-cid="' + esc(c.id) + '" style="' + active + accent + '">' +""",
  """      return '<div class="wa-conv' + (webState.current === c.id ? ' is-open' : '') + '" data-cid="' + esc(c.id) + '" style="' + active + accent + '">' +   // """+TAG),
 ("""      return '<div class="wa-conv" data-num="' + esc(c.number) + '" style="' + bg + accent + '">' +""",
  """      return '<div class="wa-conv' + (c.number === waState.current ? ' is-open' : '') + '" data-num="' + esc(c.number) + '" style="' + bg + accent + '">' +   // """+TAG),
 ("""    webState.current = convId;\n    var wrap""",
  """    webState.current = convId;\n    $$('#webConvList .wa-conv').forEach(function (el) { el.classList.toggle('is-open', el.dataset.cid === convId); });   // """+TAG+"""\n    var wrap"""),
])
rep('dashboard/chatbot-ai/index.html',[
 ("  .wa-conv:hover{background:var(--bg)}\n", "  .wa-conv:hover{background:var(--bg)}\n  /* "+TAG+" — penanda chat yang sedang dibuka */\n  .wa-conv.is-open,.wa-conv.is-open:hover{background:#eef0ff!important;border-left:4px solid #f97316!important;box-shadow:inset 0 0 0 1px rgba(79,70,229,.12)}\n"),
 ('<script src="app.js?v=1.2.133"></script><!-- v1.2.133: kb-cari -->','<script src="app.js?v=1.2.134"></script><!-- '+TAG+' -->'),
])
rep('api/index.php',[("define('DEI_VERSION', 'v1.2.133');   // v1.2.133: kb-cari","define('DEI_VERSION', 'v1.2.134');   // "+TAG)])
print('ok')
