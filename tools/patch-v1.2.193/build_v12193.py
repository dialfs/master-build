#!/usr/bin/env python3
"""Build paket v1.2.193 (asisten-support): releases/v1.2.193 (update.zip + manifest), master penuh, salinan di master-build."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
V='v1.2.193'; TAG='v1.2.193: asisten-support'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
files=['api/index.php','assets/js/chat-widget.js']
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in files: assert TAG in open(T+'/'+f, encoding='utf-8').read(), 'belum dipatch: '+f
assert TAG in open(P+'/backend/cron-tick.php', encoding='utf-8').read(), 'pusat: cron-tick.php belum dipatch'
assert "case 'support_kb_feed':" in open(P+'/backend/index.php', encoding='utf-8').read() and os.path.isfile(P+'/backend/support-lib.php'), 'pusat belum v1.2.192'
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files: z.write(T+'/'+f, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Persiapan Asisten Bantuan","type":"peningkatan",
 "changelog":"Persiapan untuk Asisten Bantuan: tombol bantuan di dashboard tempat Anda bisa bertanya cara pengaturan, letak menu, dan paket. Rilis ini menyiapkan bagian dalamnya; belum ada perubahan tampilan. Tombolnya hadir di rilis berikutnya.",
 "highlights":["Persiapan Asisten Bantuan di dashboard","Belum ada perubahan tampilan di rilis ini"]}
json.dump(man, open(P+'/releases/'+V+'/manifest.json','w'), ensure_ascii=False, indent=2)
src=P+'/master/dei-master.zip'; tmp=src+'.tmp'
with zipfile.ZipFile(src) as zi, zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zo:
    repl={'dei-chatbot-ai/'+f:f for f in files}; done=set()
    for it in zi.infolist():
        if it.filename in repl: zo.write(T+'/'+repl[it.filename], it.filename); done.add(it.filename)
        else: zo.writestr(it, zi.read(it.filename))
    assert done==set(repl), 'berkas tidak ada di master: %s' % (set(repl)-done)
os.replace(tmp, src)
json.dump({"version":V,"released_at":now,"size":os.path.getsize(src),"md5":md5(src),"description":"paket penuh untuk instalasi baru ("+V+")"}, open(P+'/master/master.json','w'), ensure_ascii=False, indent=2)
if os.path.isdir(MB): shutil.copy2(src, MB+'/dei-master-'+V+'.zip'); shutil.copy2(src, MB+'/dei-master.zip'); shutil.copy2(up, MB+'/dei-update-'+V+'-slim.zip')
with zipfile.ZipFile(up) as z:
    for f in files: assert hashlib.md5(z.read('dei-chatbot-ai/'+f)).hexdigest()==md5(T+'/'+f), f
with zipfile.ZipFile(src) as z:
    for f in files: assert TAG.encode() in z.read('dei-chatbot-ai/'+f), 'master: '+f
print(man['released_at'], man['size'], man['md5'], 'master', os.path.getsize(src), md5(src))
