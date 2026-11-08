#!/usr/bin/env python3
"""Build paket v1.2.157 (or-penalaran): releases/v1.2.157 (update.zip + manifest), master penuh, salinan di master-build."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
if len(sys.argv)>3: T,P,MB=sys.argv[1],sys.argv[2],sys.argv[3]
V='v1.2.157'; TAG='v1.2.157: or-penalaran'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
files=['api/index.php']
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in files: assert TAG in open(T+'/'+f, encoding='utf-8').read(), 'belum dipatch: ' + f
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files: z.write(T+'/'+f, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Balasan chatbot tidak terpotong lagi","type":"perbaikan",
 "changelog":"Sebagian balasan chatbot sebelumnya terpotong atau hanya berisi beberapa kata karena jatah jawaban AI habis untuk proses berpikir. Kini proses berpikir dimatikan untuk balasan chat, balasan yang terlalu pendek akibat terpotong dicoba ulang otomatis, dan balasan panjang yang tetap kena batas dipangkas rapi di akhir kalimat terakhir.",
 "highlights":["Balasan tidak lagi terpotong di tengah kata","Coba ulang otomatis untuk balasan yang terlalu pendek","Hemat token: tidak ada proses berpikir yang memakan jatah jawaban"]}
json.dump(man, open(P+'/releases/'+V+'/manifest.json','w'), ensure_ascii=False, indent=2)
src=P+'/master/dei-master.zip'; tmp=src+'.tmp'
with zipfile.ZipFile(src) as zi, zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zo:
    repl={'dei-chatbot-ai/'+f:f for f in files}
    for it in zi.infolist():
        if it.filename in repl: zo.write(T+'/'+repl[it.filename], it.filename)
        else: zo.writestr(it, zi.read(it.filename))
os.replace(tmp, src)
json.dump({"version":V,"released_at":now,"size":os.path.getsize(src),"md5":md5(src),"description":"paket penuh untuk instalasi baru ("+V+")"}, open(P+'/master/master.json','w'), ensure_ascii=False, indent=2)
if os.path.isdir(MB): shutil.copy2(src, MB+'/dei-master-'+V+'.zip'); shutil.copy2(src, MB+'/dei-master.zip'); shutil.copy2(up, MB+'/dei-update-'+V+'-slim.zip')
with zipfile.ZipFile(up) as z:
    for f in files: assert hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest()==md5(T+'/'+f), f
with zipfile.ZipFile(src) as z:
    for f in files: assert TAG.encode() in z.read('dei-chatbot-ai/'+f), 'master: ' + f
print(man['released_at'], man['size'], man['md5'], 'master', os.path.getsize(src), md5(src))
