# v1.2.145: transfer-ke-agent — label dropdown "Transfer ke Agent"
import sys, os, shutil, time
T = os.path.expanduser(sys.argv[1])
J = os.path.join(T, 'dashboard/chatbot-ai/app.js'); H = os.path.join(T, 'dashboard/chatbot-ai/index.html'); A = os.path.join(T, 'api/index.php')
ts = time.strftime('%Y%m%d-%H%M%S')
for f in (H, J, A): shutil.copy2(f, f + '.bak-v12145-' + ts)
def rep(path, old, new):
    s = open(path, encoding='utf-8').read()
    if new in s and old not in s: print('skip'); return
    assert s.count(old) == 1, (path, old[:60]); open(path, 'w', encoding='utf-8').write(s.replace(old, new))
rep(J, """'<option value="">Assign ke agen</option>' +   // v1.2.144: label-alat-chat""",
       """'<option value="">Transfer ke Agent</option>' +   // v1.2.144: label-alat-chat; v1.2.145: transfer-ke-agent""")
rep(H, '<script src="app.js?v=1.2.144"></script><!-- v1.2.144: label-alat-chat -->',
       '<script src="app.js?v=1.2.145"></script><!-- v1.2.145: transfer-ke-agent -->')
rep(A, "define('DEI_VERSION', 'v1.2.144');   // v1.2.144: label-alat-chat",
       "define('DEI_VERSION', 'v1.2.145');   // v1.2.145: transfer-ke-agent")
print('OK')
