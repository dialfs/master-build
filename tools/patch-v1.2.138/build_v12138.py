#!/usr/bin/env python3
"""Build paket v1.2.138 (filter-topik): releases/v1.2.138 (update.zip + manifest), master penuh, salinan di master-build."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
V='v1.2.138'; TAG='v1.2.138: filter-topik'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
files=['api/index.php','dashboard/chatbot-ai/app.js','dashboard/chatbot-ai/index.html']
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in files: assert TAG in open(T+'/'+f, encoding='utf-8').read(), 'belum dipatch: ' + f
assert TAG in open(P+'/backend/index.php', encoding='utf-8').read(), 'pusat belum dipatch'
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files: z.write(T+'/'+f, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Filter Topik & Divisi Chat WA","type":"fitur",
 "only_tenants":["dev-lokal"],
 "changelog":"Menu baru Topik & Divisi (paket Growth ke atas): AI membaca 20 pesan terakhir tiap chat WhatsApp lalu memberi label topik (mis. tanya harga, cicilan, STNK, sparepart) dan divisi. Percakapan WA kini bisa disaring per divisi dan per topik (topik saat ini atau pernah ditanyakan), lengkap dengan jumlah. Preset untuk 11 jenis bisnis. Label bisa dikoreksi agent dari kepala chat. Klasifikasi berjalan otomatis saat chat diam 3 menit, tiap 5 pesan baru, dan saat ditandai Selesai; chat 7 hari terakhir ikut diklasifikasi saat pertama diaktifkan. Kuota termasuk paket (Growth 5.000, Business 15.000, Pro 30.000 per bulan). Scan Topik memakai daftar topik yang sama. Customer Feedback kini tersedia mulai paket Growth.",
 "highlights":["Filter chat per topik & divisi","Customer Feedback mulai Growth"]}
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
