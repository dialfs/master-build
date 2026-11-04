# v1.2.143: kepala-chat-rapi — kepala thread Percakapan WA tidak berantakan saat kolom chat sempit
import sys, os, shutil, time
T = os.path.expanduser(sys.argv[1])
H = os.path.join(T, 'dashboard/chatbot-ai/index.html')
J = os.path.join(T, 'dashboard/chatbot-ai/app.js')
A = os.path.join(T, 'api/index.php')
ts = time.strftime('%Y%m%d-%H%M%S')
for f in (H, J, A): shutil.copy2(f, f + '.bak-v12143-' + ts)
def rep(path, old, new, cnt=1):
    s = open(path, encoding='utf-8').read()
    if new in s and old not in s: print('skip:', new[:50]); return
    n = s.count(old)
    if n != cnt: sys.exit('ANCHOR %d != %d di %s: %r' % (n, cnt, path, old[:80]))
    open(path, 'w', encoding='utf-8').write(s.replace(old, new))

# label Release dipendekkan (keterangan pindah ke tooltip)
rep(J, """actionBtns = '<button class="btn ghost" id="waReleaseBtn" style="padding:7px 14px;font-size:13px">' + ico('corner-up-left',14) + (waState.replyMode === 'manual' ? ' Lepas ke antrean' : ' Release (kembali ke bot)') + '</button>';""",
       """actionBtns = '<button class="btn ghost" id="waReleaseBtn" style="padding:7px 14px;font-size:13px" title="' + (waState.replyMode === 'manual' ? 'Lepas chat ke antrean' : 'Release — kembalikan chat ke bot') + '">' + ico('corner-up-left',14) + (waState.replyMode === 'manual' ? ' Lepas ke antrean' : ' Release') + '</button>';   // v1.2.143: kepala-chat-rapi""")
# Lead Rating + topik satu baris
rep(J, """            '<select id="waStageSelect">' + _stageOpts + '</select>' + ico('chevron-down',12) + '</label></div>' +
          tfThreadRowHtml(res) +   // v1.2.138: filter-topik""",
       """            '<select id="waStageSelect">' + _stageOpts + '</select>' + ico('chevron-down',12) + '</label>' +
          tfThreadRowHtml(res) + '</div>' +   // v1.2.138: filter-topik; v1.2.143: kepala-chat-rapi — sebaris dengan Lead Rating""")

CSS = '''
/* === v1.2.143: kepala-chat-rapi ========================================== */
#waThreadHead{container-type:inline-size;container-name:wath}
.wa-th-top{flex-wrap:wrap;align-items:flex-start;row-gap:8px}
.wa-th-id{flex:1 1 220px}
.wa-th-act{flex:0 0 auto;flex-wrap:nowrap;padding-top:4px}
.wa-th-act .btn{white-space:nowrap}
.wa-th-name{display:flex;align-items:center;gap:6px}
.wa-th-name a{flex:none}
.wa-rate-row{gap:4px 10px}
.wa-rate-row .tf-th-row{margin-top:0;display:inline-flex;align-items:center;flex-wrap:wrap;gap:4px 6px;line-height:1.5;color:var(--muted)}
.wa-rate-row .tf-th-row > span,.wa-rate-row .tf-th-row > a{white-space:nowrap}
.wa-rate-row .tf-th-row > div{flex-basis:100%}
.wa-th-tools{gap:6px 10px}
.wa-th-tools .wa-assign select{height:30px;font-size:12.5px;max-width:200px}
.wa-th-tools > a{white-space:nowrap}
@media(max-width:860px){
  .wa-th-top{flex-wrap:nowrap;align-items:center}
  .wa-th-id{flex:1 1 0}
  .wa-th-act{padding-top:0}
}
@media(min-width:861px){
  @container wath (max-width:640px){
    .wa-th-act{flex-basis:100%;justify-content:flex-start;padding:0 0 0 56px}
  }
}
'''
rep(H, '</style>\n<script>/* v1.2.73: brand per instalasi', CSS + '</style>\n<script>/* v1.2.73: brand per instalasi')
rep(H, '<script src="app.js?v=1.2.142"></script><!-- v1.2.142: mobile-rapi -->',
       '<script src="app.js?v=1.2.143"></script><!-- v1.2.143: kepala-chat-rapi -->')
rep(A, "define('DEI_VERSION', 'v1.2.142');   // v1.2.142: mobile-rapi",
       "define('DEI_VERSION', 'v1.2.143');   // v1.2.143: kepala-chat-rapi")
print('OK')
