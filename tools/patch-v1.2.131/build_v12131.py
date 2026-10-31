#!/usr/bin/env python3
"""Build paket v1.2.131 (selesai-spv): releases/v1.2.131 (update.zip + manifest), master penuh, salinan di master-build."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
V='v1.2.131'; TAG='v1.2.131: selesai-spv'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
files=['api/index.php','dashboard/chatbot-ai/app.js','dashboard/chatbot-ai/index.html']
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in files: assert TAG in open(T+'/'+f, encoding='utf-8').read(), 'belum dipatch: ' + f
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files: z.write(T+'/'+f, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Selesai Khusus Supervisor + Log Selesai Manual","type":"perbaikan",
 "changelog":"Menandai percakapan WhatsApp sebagai Selesai kini hanya bisa dilakukan Supervisor, Admin, dan Super Admin; agent tidak lagi melihat tombol Selesai (agent tetap bisa Release). Setiap penandaan Selesai manual kini dicatat di Log Selesai (tombol Log Selesai di Percakapan WA): waktu, nomor, nama, siapa yang menandai, status sebelumnya dan lama menunggu, pemegang chat, nomor bisnis, dan pesan terakhir. Log bisa diunduh sebagai CSV. Perbaikan kecil: dropdown Lead Rating di percakapan kini terbuka saat ikon atau panahnya diklik, ikon VIP tampil kembali, dan menu Customer Feedback kini berikon.",
 "highlights":["Selesai hanya oleh Supervisor/Admin","Log Selesai manual + unduh CSV"]}
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
