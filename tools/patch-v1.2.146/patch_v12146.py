# v1.2.146: label-nomor-utama — dropdown nomor: nomor tanpa label tampil "Nomor utama" (bukan nomor WA)
import sys, os, shutil, time
T = os.path.expanduser(sys.argv[1])
J = os.path.join(T, 'dashboard/chatbot-ai/app.js'); H = os.path.join(T, 'dashboard/chatbot-ai/index.html'); A = os.path.join(T, 'api/index.php')
ts = time.strftime('%Y%m%d-%H%M%S')
for f in (H, J, A): shutil.copy2(f, f + '.bak-v12146-' + ts)
def rep(path, old, new):
    s = open(path, encoding='utf-8').read()
    if new in s and old not in s: print('skip'); return
    assert s.count(old) == 1, (path, old[:60]); open(path, 'w', encoding='utf-8').write(s.replace(old, new))
rep(J, """      var _curCh144 = _chs116.filter(function (c) { return c.id === _cur116; })[0];""",
       """      var _curCh144 = _chs116.filter(function (c) { return c.id === _cur116; })[0];
      var _lbl146 = function (c) {   // v1.2.146: label-nomor-utama — nomor tanpa label: tampilkan nama, bukan nomor WA
        var l = String(c.label || ''), n = String(c.number || '');
        if (!l || l === '+' + n || l.replace(/\\D/g, '') === n) return c.primary || c.id === 'utama' ? 'Nomor utama' : (n ? '+' + n : c.id);
        return l;
      };""")
rep(J, """'<select id="waChMoveSel"><option value="">' + esc(_curCh144 ? _curCh144.label : 'Nomor bisnis') + '</option>' +""",
       """'<select id="waChMoveSel"><option value="">' + esc(_curCh144 ? _lbl146(_curCh144) : 'Nomor bisnis') + '</option>' +""")
rep(J, """return '<option value="' + esc(c.id) + '"' + (c.number ? ' title="+' + esc(c.number) + '"' : '') + '>' + esc(c.label) + '</option>';""",
       """return '<option value="' + esc(c.id) + '"' + (c.number ? ' title="+' + esc(c.number) + '"' : '') + '>' + esc(_lbl146(c)) + '</option>';""")
rep(H, '<script src="app.js?v=1.2.145"></script><!-- v1.2.145: transfer-ke-agent -->',
       '<script src="app.js?v=1.2.146"></script><!-- v1.2.146: label-nomor-utama -->')
rep(A, "define('DEI_VERSION', 'v1.2.145');   // v1.2.145: transfer-ke-agent",
       "define('DEI_VERSION', 'v1.2.146');   // v1.2.146: label-nomor-utama")
print('OK')
