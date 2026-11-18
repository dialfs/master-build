#!/usr/bin/env python3
"""Build paket v1.2.197 (kode-terlindung):
releases/v1.2.197 (update.zip: api/index.php + app.js & chat-widget.js MINIFIED), master penuh (+ .htaccess bertanda), salinan di master-build.
Sumber dei-tenant tetap utuh (tidak di-minify). Mulai rilis ini, setiap build WAJIB lewat tools/minify/minify.py."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
sys.path.insert(0, MB+'/tools/minify'); from minify import minify_js
V='v1.2.197'; TAG='v1.2.197: kode-terlindung'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
OUT=MB+'/tools/patch-v1.2.197/out'
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
assert TAG in open(T+'/api/index.php', encoding='utf-8').read(), 'api belum dipatch'
assert '# DEI-HARDEN-START v1.2.197' in open(T+'/.htaccess', encoding='utf-8').read(), '.htaccess belum dipatch'
assert 'v1.2.196: tombol-bantuan' in open(T+'/dashboard/chatbot-ai/app.js', encoding='utf-8').read(), 'app.js belum v1.2.196'
assert "case 'pkg':" in open(P+'/backend/index.php', encoding='utf-8').read(), 'pusat belum paket-terkunci'
assert os.path.isfile(P+'/master/.htaccess') and os.path.isfile(P+'/releases/.htaccess'), 'pusat: .htaccess master/releases belum ada'
# file paket -> sumber siap kirim
pkg={'api/index.php': T+'/api/index.php',
     'dashboard/chatbot-ai/app.js': minify_js(T+'/dashboard/chatbot-ai/app.js', OUT+'/app.js', V),
     'assets/js/chat-widget.js': minify_js(T+'/assets/js/chat-widget.js', OUT+'/chat-widget.js', 'widget '+V)}
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f,src in pkg.items(): z.write(src, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Keamanan & dashboard lebih ringan","type":"peningkatan",
 "changelog":"Peningkatan keamanan: berkas cadangan dan arsip di folder chatbot Anda tidak lagi bisa dibuka dari internet. File aplikasi dashboard dan widget kini dikirim dalam bentuk ringkas sehingga sedikit lebih cepat dimuat.",
 "highlights":["Berkas cadangan/arsip di server tidak bisa diunduh dari luar","Dashboard & widget lebih ringan dimuat"]}
json.dump(man, open(P+'/releases/'+V+'/manifest.json','w'), ensure_ascii=False, indent=2)
src=P+'/master/dei-master.zip'; tmp=src+'.tmp'
mpkg=dict(pkg); mpkg['.htaccess']=T+'/.htaccess'
with zipfile.ZipFile(src) as zi, zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zo:
    repl={'dei-chatbot-ai/'+f:p for f,p in mpkg.items()}; done=set()
    for it in zi.infolist():
        if it.filename in repl: zo.write(repl[it.filename], it.filename); done.add(it.filename)
        else: zo.writestr(it, zi.read(it.filename))
    assert done==set(repl), 'berkas tidak ada di master: %s' % (set(repl)-done)
os.replace(tmp, src)
json.dump({"version":V,"released_at":now,"size":os.path.getsize(src),"md5":md5(src),"description":"paket penuh untuk instalasi baru ("+V+")"}, open(P+'/master/master.json','w'), ensure_ascii=False, indent=2)
if os.path.isdir(MB): shutil.copy2(src, MB+'/dei-master-'+V+'.zip'); shutil.copy2(src, MB+'/dei-master.zip'); shutil.copy2(up, MB+'/dei-update-'+V+'-slim.zip')
with zipfile.ZipFile(up) as z:
    for f,p in pkg.items(): assert hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest()==md5(p), f
with zipfile.ZipFile(src) as z:
    for f,p in mpkg.items(): assert hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest()==md5(p), 'master: '+f
    bad=[n for n in z.namelist() if '.bak' in n or n.endswith(('.zip','.tar.gz'))]; assert not bad, 'master memuat cadangan: %s' % bad[:5]
print(man['released_at'], man['size'], man['md5'], 'master', os.path.getsize(src), md5(src))
