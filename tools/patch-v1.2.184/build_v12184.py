#!/usr/bin/env python3
"""Build paket v1.2.184 (lupa-password): releases/v1.2.184 (update.zip + manifest), master penuh, salinan di master-build."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
V='v1.2.184'; TAG='v1.2.184: lupa-password'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
files=['api/index.php','dashboard/chatbot-ai/index.html','dashboard/chatbot-ai/app.js','dashboard/chatbot-ai/login.html']
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in files: assert TAG in open(T+'/'+f, encoding='utf-8').read(), 'belum dipatch: '+f
assert "case 'mail_relay':" in open(P+'/backend/index.php', encoding='utf-8').read(), 'pusat belum dipatch'
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files: z.write(T+'/'+f, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Lupa password? Reset lewat email","type":"fitur",
 "changelog":"Halaman login kini punya tautan \"Lupa password?\". Masukkan username atau email, lalu buka tautan yang dikirim ke email akun (berlaku 30 menit, sekali pakai) untuk membuat password baru. Setelah diganti, semua sesi login lama otomatis keluar dan pemilik akun menerima email pemberitahuan. Isi email pemulihan di Profil Saya, atau Admin mengisinya di menu Pengguna. Akun yang username-nya berupa email langsung bisa dipakai.",
 "highlights":["Lupa password? Reset lewat email dari halaman login","Email pemulihan di Profil Saya & menu Pengguna","Sesi lama keluar otomatis setelah password diganti"]}
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
