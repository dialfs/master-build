#!/usr/bin/env python3
"""Build paket v1.2.109 (guest-comment): releases/v1.2.109 (update.zip + manifest), master penuh, salinan di master-build."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
V='v1.2.109'; TAG='v1.2.109: guest-comment'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
files=['api/index.php','dashboard/chatbot-ai/index.html','dashboard/chatbot-ai/app.js']
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in files: assert TAG in open(T+'/'+f, encoding='utf-8').read(), 'belum dipatch: ' + f
assert TAG in open(P+'/backend/cron-tick.php', encoding='utf-8').read(), 'pusat cron-tick belum dipatch'
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files: z.write(T+'/'+f, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Baru: Guest Comment — survei kepuasan tamu (paket Business)","type":"fitur",
 "changelog":"Menu baru Guest Comment (mulai paket Business). Tamu mengisi penilaian 1–5 per aspek (kamar, kebersihan, staf, dll. — bisa diatur) plus komentar, lewat dua jalur: chat WhatsApp (ketik kata kunci seperti \"GUEST COMMENT\" atau scan QR — bot memandu langkah demi langkah tanpa memakai kuota AI) dan form web untuk QR di kamar/front desk. Rating rendah langsung dikirim sebagai notifikasi ke Admin/Supervisor dan WhatsApp staf. Dashboard menampilkan rata-rata per aspek, daftar komentar dengan status tindak lanjut, ekspor CSV, serta tautan & QR siap cetak (bisa per nomor kamar). Setelah mengisi, tamu ditawari tautan ulasan Google.",
 "highlights":["Survei tamu lewat WhatsApp & form web (QR)","Notifikasi otomatis untuk rating rendah","Rata-rata per aspek, tindak lanjut, ekspor CSV","Tersedia mulai paket Business"]}
json.dump(man, open(P+'/releases/'+V+'/manifest.json','w'), ensure_ascii=False, indent=2)
src=P+'/master/dei-master.zip'; tmp=src+'.tmp'
with zipfile.ZipFile(src) as zi, zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zo:
    repl={'dei-chatbot-ai/'+f:f for f in files}
    for it in zi.infolist():
        if it.filename in repl: zo.write(T+'/'+repl[it.filename], it.filename)
        else: zo.writestr(it, zi.read(it.filename))
os.replace(tmp, src)
json.dump({"version":V,"released_at":now,"size":os.path.getsize(src),"md5":md5(src),"description":"paket penuh untuk instalasi baru ("+V+")"}, open(P+'/master/master.json','w'), ensure_ascii=False, indent=2)
shutil.copy2(src, MB+'/dei-master-'+V+'.zip'); shutil.copy2(src, MB+'/dei-master.zip'); shutil.copy2(up, MB+'/dei-update-'+V+'-slim.zip')
with zipfile.ZipFile(up) as z:
    for f in files: assert hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest()==md5(T+'/'+f), f
with zipfile.ZipFile(src) as z: assert TAG.encode() in z.read('dei-chatbot-ai/api/index.php')
print(man['released_at'], man['size'], man['md5'], 'master', os.path.getsize(src), md5(src))
