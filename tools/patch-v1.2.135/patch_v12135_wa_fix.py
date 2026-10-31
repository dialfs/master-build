#!/usr/bin/env python3
"""v1.2.135 wa-fix: pulihkan avatar + .wa-conv-b di daftar WA (terpotong komentar // di v1.2.134). Idempoten."""
import os, sys
T=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd/dei-tenant')
def rep(p,a,b):
    p=T+'/'+p; s=open(p,encoding='utf-8').read()
    if b in s: return
    assert s.count(a)==1,(p,a[:60]); open(p,'w',encoding='utf-8').write(s.replace(a,b))
rep('dashboard/chatbot-ai/app.js',"""' + bg + accent + '">' +   // v1.2.134: chat-aktif waAvatarHtml(c.name, c.number, 38) + '<div class="wa-conv-b">' +""","""' + bg + accent + '">' + waAvatarHtml(c.name, c.number, 38) + '<div class="wa-conv-b">' +   // v1.2.134: chat-aktif; v1.2.135: wa-fix""")
rep('dashboard/chatbot-ai/index.html','<script src="app.js?v=1.2.134"></script><!-- v1.2.134: chat-aktif -->','<script src="app.js?v=1.2.135"></script><!-- v1.2.135: wa-fix -->')
rep('api/index.php',"define('DEI_VERSION', 'v1.2.134');   // v1.2.134: chat-aktif","define('DEI_VERSION', 'v1.2.135');   // v1.2.135: wa-fix")
print('ok')
