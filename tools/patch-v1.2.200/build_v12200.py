#!/usr/bin/env python3
"""Build paket v1.2.200 (edit-hapus-pesan):
releases/v1.2.200 (update.zip: api/index.php + app.js MINIFIED + index.html), master penuh, salinan di master-build.
Sumber dei-tenant tetap utuh (tidak di-minify)."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
sys.path.insert(0, MB+'/tools/minify'); from minify import minify_js
V='v1.2.200'; TAG='v1.2.200: edit-hapus-pesan'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
TD=MB+'/tools/patch-v1.2.200'; OUT=TD+'/out'
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in ('/api/index.php','/dashboard/chatbot-ai/app.js','/dashboard/chatbot-ai/index.html'):
    assert TAG in open(T+f, encoding='utf-8').read(), f+' belum dipatch'
assert os.path.isdir(P+'/releases/v1.2.199'), 'rilis v1.2.199 belum dibuat'
pkg={'api/index.php': T+'/api/index.php',
     'dashboard/chatbot-ai/app.js': minify_js(T+'/dashboard/chatbot-ai/app.js', OUT+'/app.js', V),
     'dashboard/chatbot-ai/index.html': T+'/dashboard/chatbot-ai/index.html'}
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f,src in pkg.items(): z.write(src, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Edit & hapus pesan yang sudah terkirim","type":"peningkatan",
 "changelog":"Di Percakapan WA, pesan yang sudah terkirim kini bisa diedit (maks 15 menit, pesan teks) atau dihapus untuk semua orang (maks 48 jam) langsung dari bubble-nya. Pelanggan melihat label Diedit atau Pesan ini telah dihapus; di dashboard isi lama tetap terlihat dicoret untuk tim. Berlaku untuk nomor WhatsApp lewat WAHA; WhatsApp API resmi (Meta) tidak menyediakan fitur ini.",
 "highlights":["Edit pesan terkirim (maks 15 menit)","Hapus pesan untuk semua orang (maks 48 jam)","Riwayat tetap tercatat untuk tim & audit"],
 "guide":[{"key":"edit-hapus-pesan","menu":"wachat","title":"Mengedit atau menghapus pesan yang sudah terkirim",
   "content":"Di Percakapan WA, arahkan kursor ke bubble pesan yang sudah dikirim (di HP tautannya selalu tampil), lalu klik Edit atau Hapus di baris jam pesan. Edit: ubah isi lalu Simpan; pesan di WhatsApp pelanggan ikut berubah dengan label Diedit. Hanya pesan teks dan paling lama 15 menit setelah dikirim. Hapus: menarik pesan untuk semua orang, pelanggan melihat Pesan ini telah dihapus; paling lama 48 jam setelah dikirim. Di dashboard pesan terhapus tetap terlihat dicoret dengan nama yang menghapus, dan semua edit/hapus tercatat di Audit. Fitur ini hanya untuk nomor WhatsApp yang tersambung lewat WAHA; WhatsApp API resmi (Meta) tidak menyediakan edit atau hapus pesan terkirim, jadi tautannya tidak muncul. WA Agent hanya bisa mengubah pesan yang ia kirim sendiri dan saat chat tidak dipegang agent lain; Supervisor, Admin, dan Super Admin bisa mengubah semua pesan keluar termasuk jawaban bot.",
   "since":V}]}
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
