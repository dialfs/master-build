#!/usr/bin/env python3
"""Build paket v1.2.223 (laporan-pdf):
releases/v1.2.223 (update.zip: api/index.php + app.js MINIFIED + index.html), master penuh, salinan di master-build.
Sumber dei-tenant tetap utuh (tidak di-minify). Mesin PDF (dompdf) TIDAK ikut paket: tenant mengunduhnya sekali dari <pusat>/lib/."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
sys.path.insert(0, MB+'/tools/minify'); from minify import minify_js
V='v1.2.223'; TAG='v1.2.223: laporan-pdf'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
TD=MB+'/tools/patch-v1.2.223'; OUT=TD+'/out'
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in ('/api/index.php','/dashboard/chatbot-ai/app.js','/dashboard/chatbot-ai/index.html'):
    assert TAG in open(T+f, encoding='utf-8').read(), f+' belum dipatch'
assert TAG in open(P+'/backend/index.php', encoding='utf-8').read(), 'pusat backend belum dipatch'
assert os.path.isfile(P+'/lib/dompdf-3.1.4-dei.zip'), 'pusat lib/dompdf-3.1.4-dei.zip belum ada'
assert os.path.isdir(P+'/releases/v1.2.222'), 'rilis v1.2.222 belum dibuat'
os.makedirs(OUT, exist_ok=True)
pkg={'api/index.php': T+'/api/index.php',
     'dashboard/chatbot-ai/app.js': minify_js(T+'/dashboard/chatbot-ai/app.js', OUT+'/app.js', V),
     'dashboard/chatbot-ai/index.html': T+'/dashboard/chatbot-ai/index.html'}
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f,src in pkg.items(): z.write(src, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Laporan Berkala PDF via email & WhatsApp","type":"fitur",
 "changelog":"Menu Laporan & Log punya tab baru Laporan Berkala (Super Admin/Admin, paket Growth ke atas). Laporan PDF dibuat dan dikirim otomatis setiap minggu (pilih hari & jam) dan/atau setiap bulan (pilih tanggal & jam) ke email sebagai lampiran PDF dan ke WhatsApp sebagai dokumen PDF, lengkap dengan perbandingan terhadap periode sebelumnya. Isi laporan bisa dipilih per jadwal: Ringkasan Chat & Sumber Lead, Kinerja Layanan, Kinerja per Agent, Performa Sales & Target, Pipeline/Forecast/Umur Lead, Rekap Task, Topik Chat, serta Penggunaan & Kuota. Admin menerima laporan lengkap, akun Sales hanya menerima performa, pipeline dan task miliknya; bisa ditambah email dan nomor WhatsApp lain (misalnya pemilik usaha). Ada tombol Buat & unduh PDF untuk periode apa pun, Kirim uji ke saya, arsip PDF 120 hari, dan tautan unduh aman 30 hari di setiap email/WhatsApp. WhatsApp dikirim dari nomor pengirim Notifikasi Tim. Mesin PDF dipasang otomatis dan berjalan di hosting cPanel maupun VPS; bila server punya Chromium, PDF dibuat dengan Chromium.",
 "highlights":["Laporan PDF mingguan & bulanan otomatis ke email dan WhatsApp","Pilih isi laporan: chat, layanan, agent, sales & target, pipeline, task, topik, kuota","Sales menerima laporannya sendiri; arsip & unduh PDF kapan saja"],
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
