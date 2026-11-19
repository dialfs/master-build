#!/usr/bin/env python3
"""Build paket v1.2.210 (thread-db): releases/v1.2.210 (update.zip: api/index.php saja), master penuh, salinan di master-build."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
V='v1.2.210'; TAG='v1.2.210: thread-db'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
assert TAG in open(T+'/api/index.php', encoding='utf-8').read(), 'api/index.php belum dipatch'
assert os.path.isdir(P+'/releases/v1.2.209'), 'rilis v1.2.209 belum dibuat'
pkg={'api/index.php': T+'/api/index.php'}
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f,src in pkg.items(): z.write(src, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Riwayat chat WhatsApp tampil lengkap di tenant yang ramai","type":"perbaikan",
 "changelog":"Di tenant yang sudah memakai database, thread chat WhatsApp sebelumnya hanya membaca 500 pesan terakhir dari semua chat. Pada hari yang ramai, pesan lama di satu chat (misalnya pesan pagi) tidak tampil lagi di dashboard walau sudah tersimpan. Kini thread membaca seluruh riwayat nomor itu. Perbaikan yang sama berlaku untuk cari pesan di dalam chat, analisa lead, dan pengecekan jendela 24 jam saat membalas.",
 "highlights":["Thread chat memuat seluruh riwayat nomor","Cari pesan di dalam chat menemukan pesan lama","Analisa lead memakai percakapan lengkap"],
 "guide":[]}
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
