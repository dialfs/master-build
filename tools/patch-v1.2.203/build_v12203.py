#!/usr/bin/env python3
"""Build paket v1.2.203 (sales-tag):
releases/v1.2.203 (update.zip: api/index.php + app.js MINIFIED + index.html), master penuh, salinan di master-build.
Sumber dei-tenant tetap utuh (tidak di-minify)."""
import zipfile, hashlib, json, os, time, shutil, sys
H=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd'); T=H+'/dei-tenant'; P=H+'/dei-pusat'; MB=H+'/master-build'
sys.path.insert(0, MB+'/tools/minify'); from minify import minify_js
V='v1.2.203'; TAG='v1.2.203: sales-tag'; now=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()+7*3600))
TD=MB+'/tools/patch-v1.2.203'; OUT=TD+'/out'
md5=lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()
for f in ('/api/index.php','/dashboard/chatbot-ai/app.js','/dashboard/chatbot-ai/index.html'):
    assert TAG in open(T+f, encoding='utf-8').read(), f+' belum dipatch'
assert os.path.isdir(P+'/releases/v1.2.202'), 'rilis v1.2.202 belum dibuat'
os.makedirs(OUT, exist_ok=True)
pkg={'api/index.php': T+'/api/index.php',
     'dashboard/chatbot-ai/app.js': minify_js(T+'/dashboard/chatbot-ai/app.js', OUT+'/app.js', V),
     'dashboard/chatbot-ai/index.html': T+'/dashboard/chatbot-ai/index.html'}
os.makedirs(P+'/releases/'+V, exist_ok=True); up=P+'/releases/'+V+'/update.zip'
with zipfile.ZipFile(up,'w',zipfile.ZIP_DEFLATED) as z:
    for f,src in pkg.items(): z.write(src, 'dei-chatbot-ai/'+f)
man={"version":V,"released_at":now,"zip":"update.zip","size":os.path.getsize(up),"md5":md5(up),
 "title":"Tag Sales per chat, catat PO & laporan per Sales","type":"fitur",
 "changelog":"Setiap chat WhatsApp kini bisa ditandai dengan nama Sales yang menanganinya. Dari chat yang sama, Agent dan Supervisor bisa mencatat PO dan menjadikan lead Close Deal atas nama sales itu. Menu Tim & Agent punya daftar Sales dan Laporan per Sales (chat di-tag, PO, Close Deal, Close Lose, konversi) yang bisa diunduh CSV. Menu Leads menampilkan sales tiap lead dan bisa difilter per sales. Tersedia mulai paket Growth.",
 "highlights":["Pilih Sales di kepala chat WhatsApp","Catat PO & jadikan lead Close Deal dari chat","Laporan per Sales + unduh CSV","Filter Leads per sales"],
 "guide":[
  {"key":"sales-daftar","menu":"tim","title":"Menambah daftar Sales",
   "content":"Buka Tim & Agent, kartu Sales. Isi nama sales (no. HP opsional) lalu klik Tambah. Sales tidak perlu akun login. Matikan Aktif untuk sales yang sudah tidak dipakai: namanya hilang dari pilihan di chat, tetapi data lamanya tetap tercatat di laporan. Hanya Supervisor, Admin, dan Super Admin yang bisa mengelola daftar ini. Tersedia mulai paket Growth.","min_tier":"growth","since":V},
  {"key":"sales-tag-po","menu":"wachat","title":"Menandai Sales, mencatat PO, dan Close Deal dari chat",
   "content":"Di kepala chat WhatsApp (di HP: tombol titik tiga, Alat chat), pilih nama di dropdown Sales. Lalu klik PO untuk mencatat PO: isi tanggal, no. PO, dan catatan bila perlu, lalu Simpan PO. Satu chat bisa punya beberapa PO. Klik Jadikan Lead Close Deal untuk menutup lead chat itu atas nama sales yang dipilih; bila chat belum punya lead, lead baru dibuat otomatis. PO hanya bisa dicatat setelah Sales dipilih. Agent dan Supervisor bisa memilih sales, mencatat PO, dan Close Deal; menghapus PO hanya Supervisor ke atas.","min_tier":"growth","since":V},
  {"key":"sales-laporan","menu":"tim","title":"Laporan per Sales",
   "content":"Buka Tim & Agent, kartu Laporan per Sales, pilih rentang tanggal lalu Tampilkan. Kolom: Chat di-tag (menurut tanggal chat ditandai ke sales itu), PO (menurut tanggal PO), Close Deal dan Close Lose (menurut tanggal status lead berubah), dan Konversi = Close Deal dibagi Chat di-tag. Klik satu baris untuk melihat rincian chatnya, atau Unduh CSV. Close Deal yang terjadi sebelum v1.2.203 tidak masuk laporan karena tanggalnya belum tercatat. Laporan hanya untuk Supervisor, Admin, dan Super Admin.","min_tier":"growth","since":V}]}
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
