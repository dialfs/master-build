#!/usr/bin/env python3
"""Build paket v1.2.96: releases/v1.2.96 (update.zip + manifest), master penuh, salinan di master-build."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
V='v1.2.96'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
files=['api/index.php','dashboard/chatbot-ai/app.js','dashboard/chatbot-ai/index.html','dashboard/chatbot-ai/login.html','assets/js/chat-widget.js']
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files: z.write(T+'/'+f, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Jeda balasan AI & status “sedang mengetik…” di WhatsApp","type":"fitur",
 "changelog":"Balasan bot WhatsApp kini bisa ditahan sesuai panjang teks supaya terasa seperti diketik manusia, dan pelanggan melihat status “sedang mengetik…” selama bot menyiapkan jawaban. Atur di Respon & Eskalasi › Jeda Balasan AI, misalnya 1–50 karakter 3 detik, 51–200 karakter 5 detik, lebih panjang 8 detik. Bisa dihitung dari panjang balasan AI atau panjang pesan pelanggan; waktu AI berpikir ikut dihitung.",
 "highlights":["Jeda balasan per jumlah karakter, pola bebas","Status “sedang mengetik…” (Meta & WAHA)","Waktu AI berpikir ikut dihitung, maks 20 detik"]}
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
with zipfile.ZipFile(src) as z: assert b'v1.2.96: mengetik' in z.read('dei-chatbot-ai/api/index.php')
print(man['released_at'], man['size'], man['md5'], 'master', os.path.getsize(src), md5(src))
