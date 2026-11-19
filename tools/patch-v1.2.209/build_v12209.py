#!/usr/bin/env python3
"""Build paket v1.2.209 (autoreply-hp):
releases/v1.2.209 (update.zip: api/index.php + app.js MINIFIED + index.html), master penuh, salinan di master-build.
Sumber dei-tenant tetap utuh (tidak di-minify)."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
sys.path.insert(0, MB+'/tools/minify'); from minify import minify_js
V='v1.2.209'; TAG='v1.2.209: autoreply-hp'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
TD=MB+'/tools/patch-v1.2.209'; OUT=TD+'/out'
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in ('/api/index.php','/dashboard/chatbot-ai/app.js','/dashboard/chatbot-ai/index.html'):
    assert TAG in open(T+f, encoding='utf-8').read(), f+' belum dipatch'
assert os.path.isdir(P+'/releases/v1.2.208'), 'rilis v1.2.208 belum dibuat'
os.makedirs(OUT, exist_ok=True)
pkg={'api/index.php': T+'/api/index.php',
     'dashboard/chatbot-ai/app.js': minify_js(T+'/dashboard/chatbot-ai/app.js', OUT+'/app.js', V),
     'dashboard/chatbot-ai/index.html': T+'/dashboard/chatbot-ai/index.html'}
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f,src in pkg.items(): z.write(src, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Auto reply WhatsApp Business di HP tidak lagi menghentikan bot","type":"perbaikan",
 "changelog":"Away message atau Greeting message otomatis dari aplikasi WhatsApp Business di HP sebelumnya dianggap balasan agent, sehingga bot berhenti membalas chat itu. Kini teks auto reply bisa didaftarkan di Widget & API (atau ditandai langsung dari bubble pesan di chat). Pesan dari HP dengan teks yang sama tetap tercatat, tetapi bot tetap aktif. Chat yang terlanjur berhenti karena auto reply bisa dikembalikan ke bot sekaligus.",
 "highlights":["Daftar teks auto reply WhatsApp Business","Tandai auto reply langsung dari chat","Pulihkan chat yang terlanjur berhenti dibalas bot"],
 "guide":[
  {"key":"autoreply-hp","menu":"widget","title":"Bot berhenti membalas karena auto reply WhatsApp Business di HP",
   "content":"Pesan yang dikirim dari HP dianggap balasan agent, jadi bot berhenti membalas chat itu. Ini juga terjadi pada Away message atau Greeting message otomatis dari aplikasi WhatsApp Business. Cara mengatasi: buka Widget & API, kartu Auto reply WhatsApp Business di HP, tempel teks auto reply persis seperti di HP, lalu Simpan Daftar Auto Reply (biarkan centang Kembalikan ke bot agar chat yang terlanjur berhenti ikut pulih). Bisa juga dari chat: pada pesan dari HP klik tandai sebagai auto reply (Supervisor ke atas). Bila Jam Aktif AI sudah menangani jam di luar kerja, lebih rapi matikan Away message di HP supaya pelanggan tidak menerima dua balasan. Teks yang diubah di HP harus diubah juga di daftar.","since":V}]}
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
