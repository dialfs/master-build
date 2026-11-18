#!/usr/bin/env python3
"""Build paket v1.2.201 (edit-hapus-pesan):
releases/v1.2.201 (update.zip: api/index.php + app.js MINIFIED + index.html), master penuh, salinan di master-build.
Sumber dei-tenant tetap utuh (tidak di-minify)."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
sys.path.insert(0, MB+'/tools/minify'); from minify import minify_js
V='v1.2.201'; TAG='v1.2.201: transfer-nomor'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
TD=MB+'/tools/patch-v1.2.201'; OUT=TD+'/out'
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in ('/api/index.php','/dashboard/chatbot-ai/app.js','/dashboard/chatbot-ai/index.html'):
    assert TAG in open(T+f, encoding='utf-8').read(), f+' belum dipatch'
assert os.path.isdir(P+'/releases/v1.2.200'), 'rilis v1.2.200 belum dibuat'
pkg={'api/index.php': T+'/api/index.php',
     'dashboard/chatbot-ai/app.js': minify_js(T+'/dashboard/chatbot-ai/app.js', OUT+'/app.js', V),
     'dashboard/chatbot-ai/index.html': T+'/dashboard/chatbot-ai/index.html'}
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f,src in pkg.items(): z.write(src, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Transfer chat ke agent atau nomor WhatsApp lain","type":"peningkatan",
 "changelog":"Menu Transfer ke… di Percakapan WA kini berisi dua kelompok: Agent dan Nomor WhatsApp bisnis. Supervisor dan Admin bisa langsung memindahkan chat ke nomor WhatsApp bisnis lain milik akun dari menu yang sama.",
 "highlights":["Transfer ke… = Agent + Nomor WhatsApp bisnis","Supervisor bisa pindahkan chat ke nomor bisnis lain"],
 "guide":[{"key":"transfer-chat-nomor","menu":"wachat","title":"Transfer chat ke agent atau nomor WhatsApp lain",
   "content":"Supervisor, Admin, dan Super Admin: buka chat di Percakapan WA, lalu di panel kanan pilih menu Transfer ke…. Kelompok Agent menyerahkan chat ke agent lain. Kelompok Nomor WhatsApp bisnis memindahkan chat ke nomor bisnis lain milik akun (label kelompok menyebut nomor yang sedang dipakai); balasan berikutnya dari agent dan bot dikirim dari nomor itu, dan bila pelanggan masih membalas ke nomor lama chat otomatis kembali ke nomor lama. Kelompok nomor hanya muncul bila akun punya lebih dari satu nomor WhatsApp aktif sesuai paket. Untuk nomor WhatsApp API resmi (Meta), nomor baru belum punya jendela 24 jam dengan pelanggan, jadi kirim template lewat Blast dulu.",
   "since":V}]}
json.dump(man, open(P+'/releases/'+V+'/manifest.json','w'), ensure_ascii=False, indent=2)
src=P+'/master/dei-master.zip'; tmp=src+'.tmp'
with zipfile.ZipFile(src) as zi, zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zo:
    repl={'dei-chatbot-ai/'+f:p for f,p in pkg.items()}; done=set()
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
    for f,p in pkg.items(): assert hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest()==md5(p), 'master: '+f
    bad=[n for n in z.namelist() if '.bak' in n or n.endswith(('.zip','.tar.gz'))]; assert not bad, 'master memuat cadangan: %s' % bad[:5]
print(man['released_at'], man['size'], man['md5'], 'master', os.path.getsize(src), md5(src))
