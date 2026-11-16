#!/usr/bin/env python3
"""Build paket v1.2.185 (master-grup): releases/v1.2.185 (update.zip + manifest), master penuh, salinan di master-build."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
V='v1.2.185'; TAG='v1.2.185: master-grup'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
files=['api/index.php','dashboard/chatbot-ai/index.html','dashboard/chatbot-ai/app.js']
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in files: assert TAG in open(T+'/'+f, encoding='utf-8').read(), 'belum dipatch: '+f
assert "case 'grp_report':" in open(P+'/backend/index.php', encoding='utf-8').read() and os.path.exists(P+'/backend/group-lib.php') and os.path.exists(P+'/grup/index.html'), 'pusat belum dipatch'
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files: z.write(T+'/'+f, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Siap untuk Dashboard Grup","type":"fitur",
 "changelog":"Tenant kini bisa digabung ke Dashboard Grup DEI: pemilik grup usaha dengan beberapa chatbot melihat laporan gabungan (percakapan, penyelesaian bot, respon pertama, leads, kinerja agent) dan membuka dashboard tiap tenant tanpa login ulang. Pusat hanya menarik angka ringkas, bukan isi chat. Masuk dari Dashboard Grup memakai akun yang sudah ada di tenant dan tercatat di Log Masuk sebagai \"Dashboard Grup\".",
 "highlights":["Laporan gabungan untuk Dashboard Grup","Buka dashboard tenant dari Dashboard Grup tanpa login ulang","Log Masuk mencatat masuk dari Dashboard Grup"]}
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
    for f in files: assert TAG.encode() in z.read('dei-chatbot-ai/'+f), 'master: '+f
print(man['released_at'], man['size'], man['md5'], 'master', os.path.getsize(src), md5(src))
