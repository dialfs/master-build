#!/usr/bin/env python3
"""Build paket v1.2.199 (template-media):
releases/v1.2.199 (update.zip: api/index.php + app.js MINIFIED + index.html), master penuh, salinan di master-build.
Sumber dei-tenant tetap utuh (tidak di-minify)."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
sys.path.insert(0, MB+'/tools/minify'); from minify import minify_js
V='v1.2.199'; TAG='v1.2.199: template-media'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
TD=MB+'/tools/patch-v1.2.199'; OUT=TD+'/out'
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in ('/api/index.php','/dashboard/chatbot-ai/app.js','/dashboard/chatbot-ai/index.html'):
    assert TAG in open(T+f, encoding='utf-8').read(), f+' belum dipatch'
assert os.path.isdir(P+'/releases/v1.2.198'), 'rilis v1.2.198 belum dibuat — jalankan rilis-v1.2.198-auto.command dulu'
pkg={'api/index.php': T+'/api/index.php',
     'dashboard/chatbot-ai/app.js': minify_js(T+'/dashboard/chatbot-ai/app.js', OUT+'/app.js', V),
     'dashboard/chatbot-ai/index.html': T+'/dashboard/chatbot-ai/index.html'}
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f,src in pkg.items(): z.write(src, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Template balasan bisa membawa lampiran","type":"peningkatan",
 "changelog":"Template Balasan WA kini bisa menyertakan lampiran: gambar, video, PDF/dokumen, atau pesan suara. Saat agent memilih template (tombol Template atau ketik /pintasan), file langsung terpasang di kotak balas dan isi template menjadi keterangannya, tinggal Kirim atau Jadwalkan. Admin/Supervisor menambah lampiran lewat Kelola template.",
 "highlights":["Template balasan bisa membawa gambar, video, dokumen, atau audio","Pilih template: file + keterangan langsung siap kirim","Bisa langsung dijadwalkan"],
 "guide":[{"key":"template-balasan-lampiran","menu":"wachat","title":"Memakai template balasan (teks & lampiran)",
   "content":"Di kotak balas Percakapan WA klik tombol Template (ikon dokumen) atau ketik / lalu nama pintasan, misalnya /harga, pilih dengan panah lalu Enter. Template bisa membawa lampiran (brosur, foto, katalog PDF, video, pesan suara): saat dipilih, file langsung terpasang di atas kotak balas dan isi template menjadi keterangan; periksa lalu Kirim atau Jadwalkan. Menambah atau mengubah template hanya Super Admin, Admin, dan Supervisor: klik Kelola template, isi Judul, Pintasan, Isi, lalu Pilih file di bagian Lampiran (opsional), lalu Simpan template. Lampiran bisa diganti atau dihapus lewat Edit. Batas: JPG/PNG maks 5 MB, video, audio, PDF dan dokumen maks 16 MB; keterangan maks 1.024 karakter; pesan suara dikirim tanpa keterangan, jadi isi template audio dikosongkan. Total lampiran template per tenant maks 300 MB. Lampiran hanya bisa dikirim dari nomor WhatsApp API resmi (Meta) atau WAHA, tidak dari Fonnte; untuk WhatsApp API resmi juga harus di dalam jendela 24 jam.",
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
