#!/usr/bin/env python3
"""Build paket v1.2.198 (pasang-di-hp):
releases/v1.2.198 (update.zip: api/index.php + app.js MINIFIED + index.html), master penuh, salinan di master-build.
Panduan PDF disalin ke dei-pusat/panduan/ (publik: https://chat.deintegra.com/panduan/pasang-dashboard-di-hp.pdf).
Sumber dei-tenant tetap utuh (tidak di-minify)."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
sys.path.insert(0, MB+'/tools/minify'); from minify import minify_js
V='v1.2.198'; TAG='v1.2.198: pasang-di-hp'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
TD=MB+'/tools/patch-v1.2.198'; OUT=TD+'/out'
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in ('/api/index.php','/dashboard/chatbot-ai/app.js','/dashboard/chatbot-ai/index.html'):
    assert TAG in open(T+f, encoding='utf-8').read(), f+' belum dipatch'
assert os.path.isdir(P+'/releases/v1.2.197'), 'rilis v1.2.197 belum dibuat — jalankan rilis-v1.2.197-auto.command dulu'
# panduan PDF (publik di pusat)
os.makedirs(P+'/panduan', exist_ok=True)
shutil.copy2(TD+'/manual/pasang-dashboard-di-hp.pdf', P+'/panduan/pasang-dashboard-di-hp.pdf')
os.chmod(P+'/panduan', 0o755); os.chmod(P+'/panduan/pasang-dashboard-di-hp.pdf', 0o644)
pkg={'api/index.php': T+'/api/index.php',
     'dashboard/chatbot-ai/app.js': minify_js(T+'/dashboard/chatbot-ai/app.js', OUT+'/app.js', V),
     'dashboard/chatbot-ai/index.html': T+'/dashboard/chatbot-ai/index.html'}
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f,src in pkg.items(): z.write(src, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Panduan memasang dashboard di HP","type":"peningkatan",
 "changelog":"Pusat Bantuan kini punya panduan memasang dashboard sebagai ikon di layar utama HP (Android dan iPhone), lengkap dengan PDF bergambar yang bisa diunduh dan dibagikan ke tim. Panduan ini ditandai Sering ditanyakan dan tampil paling atas. Di Android, tombol Pasang sekarang memasang dashboard langsung.",
 "highlights":["Panduan pasang di HP (Android & iPhone) di Pusat Bantuan, ditandai Sering ditanyakan","PDF panduan bergambar untuk dibagikan ke tim","Tombol Pasang sekarang di Android"],
 "guide":[{"key":"pasang-dashboard-hp","menu":"","title":"Memasang dashboard di HP (ikon di layar utama)",
   "content":"Pertanyaan yang sering ditanyakan. Buka alamat dashboard tenant di HP lalu login: Android pakai aplikasi Chrome, iPhone pakai Safari (jangan dari browser di dalam WhatsApp atau Instagram). Android: ketuk menu tiga titik di kanan atas, pilih Tambahkan ke layar utama atau Instal aplikasi, lalu Instal; di Pusat Bantuan juga ada tombol Pasang sekarang bila browser mendukung. iPhone: ketuk tombol Bagikan (kotak dengan panah ke atas; bila tidak terlihat ketuk tiga titik di bilah alamat dulu), pilih Tambah ke Layar Utama, lalu Tambah. Setelah ikon DEI muncul, selalu buka dashboard dari ikon itu, lalu klik Notifikasi dan pilih Izinkan; di iPhone notifikasi hanya jalan bila dibuka dari ikon (iOS 16.4 ke atas). Satu ikon untuk satu tenant. Panduan PDF bergambar: https://chat.deintegra.com/panduan/pasang-dashboard-di-hp.pdf (juga ada tombol Unduh panduan PDF bergambar di Pusat Bantuan, artikel Memasang dashboard di HP).",
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
