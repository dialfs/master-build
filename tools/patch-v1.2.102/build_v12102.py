#!/usr/bin/env python3
"""Build paket v1.2.102: releases/v1.2.102 (update.zip + manifest), master penuh, salinan di master-build."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
V='v1.2.102'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
files=['api/index.php']
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files: z.write(T+'/'+f, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Closing WA tidak berulang + AI lebih andal","type":"perbaikan",
 "changelog":"Pesan penutup otomatis ('Apakah ada lagi yang bisa kami bantu?') kini dikirim paling banyak sekali per 12 jam per pelanggan dan tidak dikirim bila pelanggan sudah pamit/menjawab tidak ada ('trimakasih', 'blm kak', 'tidak ada'). AI tidak lagi menutup jawaban dengan pertanyaan 'ada lagi?' saat pelanggan pamit. Riwayat percakapan yang dikirim ke AI dirapikan supaya tidak memicu galat, galat sementara dicoba ulang sekali, jawaban kosong dari model OpenRouter (mis. Gemini 2.5 Flash) dicoba ulang otomatis, alasan kegagalan AI dicatat di log, dan balasan dari HP ke chat berformat LID lebih andal terbaca.",
 "highlights":["Closing otomatis maks 1x / 12 jam","Deteksi pamit lebih luas","AI gagal: coba ulang + alasan di log"]}
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
with zipfile.ZipFile(src) as z: assert b'v1.2.102: closing-sekali' in z.read('dei-chatbot-ai/api/index.php')
print(man['released_at'], man['size'], man['md5'], 'master', os.path.getsize(src), md5(src))
