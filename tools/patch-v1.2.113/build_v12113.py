#!/usr/bin/env python3
"""Build paket v1.2.113 (import-kontak): releases/v1.2.113 (update.zip + manifest), master penuh, salinan di master-build."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
V='v1.2.113'; TAG='v1.2.113: import-kontak'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
files=['api/index.php','dashboard/chatbot-ai/index.html','dashboard/chatbot-ai/app.js']
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in files: assert TAG in open(T+'/'+f, encoding='utf-8').read(), 'belum dipatch: ' + f
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files: z.write(T+'/'+f, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Impor Kontak dari Excel/CSV — lengkap dengan Lead Rating","type":"fitur",
 "changelog":"Menu Kontak kini punya tombol Impor Kontak untuk Super Admin dan Admin. Unggah file Excel (.xls/.xlsx) atau CSV, misalnya data order atau data pelanggan, lalu pilih kolom nomor WA, nama, dan status. Setiap nilai status di file bisa dipetakan ke Lead Rating (Active Customer, Hot Prospect, Unqualified, dan lainnya) dengan saran otomatis, dan baris yang ada tanda refund/batal bisa langsung dijadikan Unqualified. Nomor dirapikan otomatis ke format WhatsApp (misalnya +62 0812… menjadi 62812…), nomor ganda digabung dengan Lead Rating tertinggi, dan pratinjau ditampilkan sebelum disimpan. Kontak yang diimpor sebelum WhatsApp terhubung akan otomatis menyatu begitu nomornya chat atau riwayatnya ditarik. Lead Rating dan nama yang sudah diatur tidak ditimpa, kecuali Anda memilih untuk menimpa.",
 "highlights":["Impor Kontak dari XLS/XLSX/CSV","Pemetaan status ke Lead Rating","Nomor dirapikan ke format WhatsApp","Pratinjau sebelum impor","Menyatu otomatis saat WA terhubung"]}
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
