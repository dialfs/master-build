# v1.2.144: label-alat-chat — "Assign ke agen" + dropdown nomor menampilkan label nomor aktif; tanpa teks terpotong
import sys, os, shutil, time
T = os.path.expanduser(sys.argv[1])
H = os.path.join(T, 'dashboard/chatbot-ai/index.html')
J = os.path.join(T, 'dashboard/chatbot-ai/app.js')
A = os.path.join(T, 'api/index.php')
ts = time.strftime('%Y%m%d-%H%M%S')
for f in (H, J, A): shutil.copy2(f, f + '.bak-v12144-' + ts)
def rep(path, old, new, cnt=1):
    s = open(path, encoding='utf-8').read()
    if new in s and old not in s: print('skip:', new[:50]); return
    n = s.count(old)
    if n != cnt: sys.exit('ANCHOR %d != %d di %s: %r' % (n, cnt, path, old[:80]))
    open(path, 'w', encoding='utf-8').write(s.replace(old, new))

rep(J, """var _opsi = '<option value="">' + (claim ? 'Pindahkan ke…' : 'Serahkan ke…') + '</option>' +""",
       """var _opsi = '<option value="">Assign ke agen</option>' +   // v1.2.144: label-alat-chat""")
rep(J, """      toolBtns += '<span class="wa-assign" title="Balasan berikutnya (agent & bot) dikirim dari nomor yang dipilih">' + ico('phone',13) +
        '<select id="waChMoveSel"><option value="">Pindah ke nomor…</option>' +
        _chs116.filter(function (c) { return c.id !== _cur116; }).map(function (c) {
          var t = c.label + ((c.number && c.label !== '+' + c.number) ? ' (+' + c.number + ')' : '');
          return '<option value="' + esc(c.id) + '">' + esc(t) + '</option>';
        }).join('') + '</select></span>';""",
       """      var _curCh144 = _chs116.filter(function (c) { return c.id === _cur116; })[0];   // v1.2.144: label-alat-chat — tampilkan label nomor yang sedang dipakai
      toolBtns += '<span class="wa-assign" title="Nomor bisnis yang dipakai membalas chat ini. Pilih nomor lain untuk memindah.">' + ico('phone',13) +
        '<select id="waChMoveSel"><option value="">' + esc(_curCh144 ? _curCh144.label : 'Nomor bisnis') + '</option>' +
        _chs116.filter(function (c) { return c.id !== _cur116; }).map(function (c) {
          return '<option value="' + esc(c.id) + '"' + (c.number ? ' title="+' + esc(c.number) + '"' : '') + '>' + esc(c.label) + '</option>';
        }).join('') + '</select></span>';""")

CSS = '''
/* === v1.2.144: label-alat-chat — dropdown alat tidak terpotong ============ */
#waThreadHead .wa-th-tools .wa-assign{margin:0;max-width:100%;min-width:0}
#waThreadHead .wa-th-tools .wa-assign select{width:auto;max-width:100%!important;height:32px;font-size:13px;padding:0 28px 0 10px;text-overflow:clip}
@media(max-width:860px){
  #waThreadHead .wa-th-tools .wa-assign{flex:1 1 100%}
  #waThreadHead .wa-th-tools .wa-assign select{flex:1;width:100%;font-size:16px;height:36px}
}
'''
rep(H, '</style>\n<script>/* v1.2.73: brand per instalasi', CSS + '</style>\n<script>/* v1.2.73: brand per instalasi')
rep(H, '<script src="app.js?v=1.2.143"></script><!-- v1.2.143: kepala-chat-rapi -->',
       '<script src="app.js?v=1.2.144"></script><!-- v1.2.144: label-alat-chat -->')
rep(A, "define('DEI_VERSION', 'v1.2.143');   // v1.2.143: kepala-chat-rapi",
       "define('DEI_VERSION', 'v1.2.144');   // v1.2.144: label-alat-chat")
print('OK')
