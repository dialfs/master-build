#!/usr/bin/env python3
"""Build paket v1.2.204 (jam-ai):
releases/v1.2.204 (update.zip: api/index.php + app.js MINIFIED + index.html), master penuh, salinan di master-build.
Sumber dei-tenant tetap utuh (tidak di-minify)."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
sys.path.insert(0, MB+'/tools/minify'); from minify import minify_js
V='v1.2.204'; TAG='v1.2.204: jam-ai'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
TD=MB+'/tools/patch-v1.2.204'; OUT=TD+'/out'
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in ('/api/index.php','/dashboard/chatbot-ai/app.js','/dashboard/chatbot-ai/index.html'):
    assert TAG in open(T+f, encoding='utf-8').read(), f+' belum dipatch'
assert os.path.isdir(P+'/releases/v1.2.203'), 'rilis v1.2.203 belum dibuat'
os.makedirs(OUT, exist_ok=True)
pkg={'api/index.php': T+'/api/index.php',
     'dashboard/chatbot-ai/app.js': minify_js(T+'/dashboard/chatbot-ai/app.js', OUT+'/app.js', V),
     'dashboard/chatbot-ai/index.html': T+'/dashboard/chatbot-ai/index.html'}
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f,src in pkg.items(): z.write(src, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Jam Aktif AI: AI membalas di jam tertentu, sisanya agent","type":"fitur",
 "changelog":"Kini bisa diatur kapan AI membalas WhatsApp, misalnya hanya pukul 21:00 sampai 09:00. Di luar jam itu AI diam dan semua chat masuk ke agent seperti Mode Manual (antrean, routing, notifikasi, dan eskalasi tetap berjalan). Bisa juga memilih hari tertentu di mana AI aktif 24 jam, misalnya Minggu. Kotak status di Percakapan WA menunjukkan siapa yang sedang membalas.",
 "highlights":["Atur jam aktif AI (boleh lewat tengah malam)","Di luar jam AI, chat ditangani agent","Pilih hari AI aktif 24 jam"],
 "guide":[
  {"key":"jam-ai","menu":"eskalasi","title":"Mengatur Jam Aktif AI",
   "content":"Buka Respon & Eskalasi, kartu Jam Aktif AI (WhatsApp). Nyalakan Aktifkan jadwal AI, lalu isi AI aktif mulai dan sampai dalam WIB, misalnya 21:00 sampai 09:00. Di luar jam itu AI tidak membalas dan semua chat WhatsApp ditangani agent seperti Mode Manual: masuk antrean, notifikasi dan eskalasi tetap berjalan. Centang hari di AI aktif 24 jam bila di hari itu tidak ada agent, misalnya Minggu. Saat jam AI dimulai, chat yang sedang di-claim agent tetap di agent sampai dilepas atau Selesai; chat lain dijawab AI pada pesan berikutnya. Jadwal ini hanya untuk WhatsApp, tidak untuk widget website.","since":V}]}
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
