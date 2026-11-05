# v1.2.149: kepala-chat-mobile — di HP, Lead Rating + Topik turun ke baris sendiri (lebar penuh)
# supaya tidak menabrak tombol Claim/Selesai. CSS saja + versi.
import sys, os, shutil, time
T = os.path.expanduser(sys.argv[1])
H = os.path.join(T, 'dashboard/chatbot-ai/index.html'); A = os.path.join(T, 'api/index.php')
ts = time.strftime('%Y%m%d-%H%M%S')
for f in (H, A): shutil.copy2(f, f + '.bak-v12149-' + ts)
def rep(path, old, new):
    s = open(path, encoding='utf-8').read()
    if new in s: print('skip'); return
    assert s.count(old) == 1, (path, old[:70]); open(path, 'w', encoding='utf-8').write(s.replace(old, new))

CSS = """
/* === v1.2.149: kepala-chat-mobile — Lead Rating + Topik baris sendiri di HP === */
@media(max-width:860px){
  #waThreadHead .wa-th-top{display:grid;grid-template-columns:auto auto minmax(0,1fr) auto;column-gap:8px;row-gap:0;align-items:center}
  #waThreadHead .wa-th-top > .wa-th-back{grid-column:1;grid-row:1/3}
  #waThreadHead .wa-th-top > .wa-av{grid-column:2;grid-row:1/3}
  #waThreadHead .wa-th-id{display:contents}
  #waThreadHead .wa-th-name{grid-column:3;grid-row:1;min-width:0;overflow:hidden}
  #waThreadHead .wa-th-sub{grid-column:3;grid-row:2;min-width:0}
  #waThreadHead .wa-th-act{grid-column:4;grid-row:1/3;align-self:center}
  #waThreadHead .wa-rate-row{grid-column:1/-1;grid-row:3;min-width:0;margin-top:8px;padding-top:8px;border-top:1px dashed var(--line);flex-wrap:wrap;gap:6px 10px}
  #waThreadHead .wa-rate{max-width:100%;flex:none}
  #waThreadHead .wa-rate select{max-width:58vw;text-overflow:ellipsis;font-size:13px;field-sizing:content}
  #waThreadHead .wa-rate-row .tf-th-row{flex:1 1 auto;min-width:0}
}
"""
rep(H, "/* === v1.2.144: label-alat-chat", CSS.lstrip('\n') + "\n/* === v1.2.144: label-alat-chat")
rep(H, '<script src="app.js?v=1.2.148"></script><!-- v1.2.148: selesai-tanpa-flag -->',
       '<script src="app.js?v=1.2.149"></script><!-- v1.2.149: kepala-chat-mobile -->')
rep(A, "define('DEI_VERSION', 'v1.2.148');   // v1.2.148: selesai-tanpa-flag",
       "define('DEI_VERSION', 'v1.2.149');   // v1.2.149: kepala-chat-mobile")
print('patch v1.2.149 OK')
