import json, os, datetime
from drv import *

D = datetime.timedelta
def ymd(days_from_now): return (NOW + D(days=days_from_now)).strftime('%Y-%m-%d')
def hm(t): return t.strftime('%Y-%m-%d %H:%M')
def lead_json(**k):
    open(os.path.expanduser('~/demo/seed/lead-next.json'), 'w').write(json.dumps(
        {'nama': k.get('nama', ''), 'kebutuhan': k.get('kebutuhan', ''), 'waktu': k.get('waktu', ''), 'anggaran': k.get('anggaran', ''), 'ringkasan': k.get('ringkasan', '')}, ensure_ascii=False))

seed = open(os.path.expanduser('~/demo/seed/token')).read().strip()

# ---------- 1. Pengguna (H-20) ----------
set_time(at(20, 9, 5))
call('save_user', 'POST', token=seed, body={'username': 'admin', 'name': 'Admin Nusa EV', 'role': 'admin', 'password': 'Sementara-Demo1'})
A = login('admin', 'Sementara-Demo1')
tick(3)
call('save_user', 'POST', token='@admin', body={'username': 'sales', 'name': 'Rina Sales', 'role': 'sales', 'password': 'Sementara-Demo2', 'sales_div': 'Showroom Jakarta', 'sales_scope': 'own'})
S = login('sales', 'Sementara-Demo2')
SID = [u for u in rj('users.json') if u['username'] == 'sales'][0]['sales_id']
print('sales_id', SID)

# ---------- 2. Knowledge Base & Daftar Harga ----------
tick(10)
KB = [
 ('Produk', 'Pilihan motor listrik Nusa EV', 'Nusa EV menjual 3 tipe motor listrik:\n1) Nusa Volt S — motor harian dalam kota, motor 1.500 W, jarak tempuh ± 80 km sekali cas, kecepatan maks 60 km/jam.\n2) Nusa Volt X — tipe paling laris, motor 2.000 W, jarak tempuh ± 110 km, kecepatan maks 75 km/jam, ada mode Sport dan fitur keyless.\n3) Nusa Cargo Pro — untuk usaha & kurir, motor 3.000 W, jarak tempuh ± 120 km, rak kargo belakang hingga 100 kg.\nWarna: Putih, Hitam Doff, Abu-abu, Merah (Merah khusus Volt X).'),
 ('Cicilan', 'Kredit / cicilan motor', 'Pembelian bisa kredit lewat leasing partner Nusa EV.\n- DP mulai 10% dari harga OTR.\n- Tenor 12, 24, atau 36 bulan.\n- Perkiraan angsuran Volt X (DP 10%): 12 bln ± Rp 2,1 jt/bln, 24 bln ± Rp 1,15 jt/bln, 36 bln ± Rp 830 rb/bln. Angka final mengikuti persetujuan leasing.\n- Syarat: KTP, KK, slip gaji / rekening koran 3 bulan terakhir. Tidak wajib kartu kredit.\n- Proses persetujuan 1–3 hari kerja.'),
 ('Test Ride', 'Jadwal test ride', 'Test ride gratis di showroom Nusa EV, semua tipe tersedia. Bisa datang langsung atau jadwalkan lewat WhatsApp agar unit dan sales disiapkan. Bawa SIM C. Durasi ± 20 menit.'),
 ('Showroom', 'Alamat & jam buka showroom', 'Showroom Nusa EV (alamat contoh untuk demo): Jl. Mawar Raya No. 12, Jakarta Timur.\nJam buka: Senin–Sabtu 09.00–18.00, Minggu & hari libur 10.00–16.00.'),
 ('Garansi', 'Garansi motor & baterai', 'Garansi rangka & dinamo 3 tahun. Garansi baterai 5 tahun atau 50.000 km (mana yang tercapai lebih dulu). Servis gratis 4 kali di tahun pertama (jasa).'),
 ('Charging', 'Cara mengecas & listrik rumah', 'Cas di stop kontak rumah biasa 220 V, daya charger 600 W — aman untuk listrik rumah 900 VA bila tidak bersamaan dengan alat berdaya besar (disarankan 1.300 VA ke atas). Waktu cas 0–100% ± 4–5 jam. Baterai bisa dilepas, jadi bisa dicas di dalam unit apartemen.'),
 ('Tukar Tambah', 'Tukar tambah motor bensin', 'Bisa tukar tambah motor bensin merek apa pun. Harga taksiran ditentukan setelah unit dicek di showroom (± 30 menit). Bawa STNK & BPKB asli. Nilai tukar tambah langsung memotong harga atau DP.'),
 ('Surat & Pengiriman', 'STNK, BPKB & pengiriman unit', 'Harga OTR sudah termasuk STNK & BPKB. Proses STNK 14–21 hari kerja, BPKB ± 2–3 bulan. Unit bisa dikirim gratis ke wilayah Jabodetabek, 2–4 hari kerja setelah pembayaran lunas / persetujuan leasing.'),
 ('Servis', 'Servis berkala & suku cadang', 'Servis berkala dianjurkan tiap 3.000 km atau 3 bulan. Booking servis lewat WhatsApp, pilih hari & jam. Biaya jasa servis berkala Rp 150.000 (gratis 4x di tahun pertama). Suku cadang tersedia di bengkel showroom.'),
 ('Pembelian Armada', 'Pembelian armada / perusahaan (fleet)', 'Untuk pembelian 5 unit ke atas (perusahaan, kurir, koperasi) tersedia harga khusus armada dan penawaran resmi. Bot tidak memberi harga armada — sambungkan ke tim sales.'),
]
call('save_kb', 'POST', token='@admin', body={'kb': [{'category': c, 'title': t, 'content': x, 'topic': ''} for c, t, x in KB]})
tick(5)
call('save_pricelist', 'POST', token='@admin', body={'items': [
 {'item': 'Nusa Volt S', 'price': 'Rp 18.900.000', 'note': 'OTR Jakarta, termasuk STNK, BPKB & charger. 1.500 W, ± 80 km.'},
 {'item': 'Nusa Volt X', 'price': 'Rp 24.500.000', 'note': 'OTR Jakarta, termasuk STNK, BPKB & charger. 2.000 W, ± 110 km. Warna Merah khusus tipe ini.'},
 {'item': 'Nusa Cargo Pro', 'price': 'Rp 32.900.000', 'note': 'OTR Jakarta. 3.000 W, ± 120 km, rak kargo 100 kg.'},
 {'item': 'Baterai cadangan 60V 30Ah', 'price': 'Rp 6.500.000', 'note': 'Untuk semua tipe.'},
 {'item': 'Servis berkala (jasa)', 'price': 'Rp 150.000', 'note': 'Gratis 4x di tahun pertama.'},
 {'item': 'Paket helm + jas hujan', 'price': 'Rp 450.000', 'note': ''},
]})
tick(2)
call('crm_remind_save', 'POST', token='@admin', body={'on': True, 'hour': 8})

# helpers ---------------------------------------------------------------
def convo(num, name, start, steps):
    set_time(start)
    for st in steps:
        kind = st[0]
        if kind == 'in':
            wa_in(num, name, st[1], st[2] if len(st) > 2 else None)
            tick(st[3] if len(st) > 3 else 2)
        elif kind == 'agent':
            tok = '@' + st[1]
            call('wa_send_manual', 'POST', token=tok, body={'number': num, 'text': st[2]})
            tick(st[3] if len(st) > 3 else 2)
        elif kind == 'human':
            call('wa_set_mode', 'POST', token='@admin', body={'number': num, 'mode': 'human'}); tick(1)
        elif kind == 'claim':
            call('wa_claim', 'POST', token='@admin', body={'number': num}); tick(1)
        elif kind == 'resolve':
            call('wa_resolve', 'POST', token='@admin', body={'number': num}); tick(1)
        elif kind == 'wait':
            tick(st[1])
        elif kind == 'at':
            set_time(st[1])

def tag(num, stage=None, vip=False, sales=False):
    if stage: call('save_contact_stage', 'POST', token='@admin', body={'number': num, 'stage': stage, 'vip': vip}); tick(0, 20)
    if sales: call('sales_tag', 'POST', token='@admin', body={'number': num, 'sales': SID}); tick(0, 20)

def analyze(num, **k):
    lead_json(**k); call('analyze_lead', 'POST', token='@admin', body={'number': num}); tick(0, 30)

def act(num, t, typ, text, nd='', ntm='', ntx='', tok=None):
    set_time(t)
    for a in (rj('lead_activity.json', {}) or {}).get(num, []):
        if a.get('next_due') and not a.get('next_done') and a['next_due'] <= t.strftime('%Y-%m-%d'):
            call('lead_act_update', 'POST', token=tok or '@sales', body={'number': num, 'id': a['id'], 'done': 1})
    call('lead_act_add', 'POST', token=tok or '@sales', body={'number': num, 'type': typ, 'at': hm(t), 'text': text, 'next_due': nd, 'next_time': ntm, 'next_text': ntx})

def status(num, st, t, tok=None, note=None):
    set_time(t)
    b = {'number': num, 'status': st}
    if note is not None: b['note'] = note
    call('save_lead', 'POST', token=tok or '@sales', body=b)

def deal(num, value, ce, t, tok=None):
    set_time(t); call('lead_deal_save', 'POST', token=tok or '@sales', body={'number': num, 'value': value, 'close_est': ce})

# ---------- 3. Percakapan WhatsApp ----------
# Bambang (H-15) -> akhirnya Close Lose
N_BAMBANG = '6281299900110'
convo(N_BAMBANG, 'Bambang S', at(15, 11, 20), [
 ('in', 'Siang, Volt S harganya berapa?', 'Siang Kak! Nusa Volt S harganya Rp 18.900.000 OTR Jakarta, sudah termasuk STNK, BPKB, dan charger. Jarak tempuhnya ± 80 km sekali cas. Mau sekalian dijadwalkan test ride?'),
 ('in', 'Garansi baterainya berapa lama?', 'Garansi baterai 5 tahun atau 50.000 km, Kak. Rangka & dinamo 3 tahun, plus servis gratis 4x di tahun pertama 😊'),
 ('in', 'Ok, masih mikir2 dulu ya kak', 'Siap Kak, silakan. Kalau ada pertanyaan lagi, kabari Nadia di sini ya 🙏', 3),
])
tag(N_BAMBANG, 'warm', sales=True)
analyze(N_BAMBANG, nama='Bambang', kebutuhan='Nusa Volt S, tanya harga & garansi baterai', ringkasan='Menanyakan harga Volt S dan garansi baterai, masih mempertimbangkan.')

# Dewi (H-13) -> Close Deal, sudah jadi pelanggan
N_DEWI = '6281299900104'
convo(N_DEWI, 'Dewi Lestari', at(13, 10, 2), [
 ('in', 'Halo kak, Volt S ada promo bulan ini?', 'Halo Kak! Bulan ini pembelian Nusa Volt S dapat bonus paket helm + jas hujan (senilai Rp 450.000). Harga Volt S Rp 18.900.000 OTR Jakarta. Kakak rencana beli cash atau kredit?'),
 ('in', 'Cash kak. Bisa dikirim ke Depok?', 'Bisa Kak, pengiriman gratis untuk Jabodetabek, 2–4 hari kerja setelah pembayaran lunas. Boleh saya sambungkan ke tim sales untuk proses pemesanannya?'),
 ('in', 'Boleh kak, warna putih ya', 'Baik Kak, saya teruskan ke tim sales ya. Mohon tunggu sebentar 🙏', 6),
 ('human',), ('claim',),
 ('agent', 'admin', 'Halo Kak Dewi, saya Admin Nusa EV 😊 Volt S warna Putih ready. Untuk pemesanan, boleh kirim nama lengkap sesuai KTP dan alamat pengiriman di Depok?', 9),
 ('in', 'Dewi Lestari, Jl. Kenanga No. 5 Beji, Depok', None, 4),
 ('agent', 'admin', 'Terima kasih Kak. Total Rp 18.900.000 (bonus helm + jas hujan). Invoice & nomor rekening kami kirim sebentar lagi ya.', 30),
 ('in', 'Sudah transfer ya kak 🙏', None, 5),
 ('agent', 'admin', 'Pembayaran sudah kami terima, terima kasih Kak Dewi! Unit dikirim Jumat ke Depok. Nanti kurir menghubungi sebelum berangkat 🛵⚡', 3),
 ('resolve',),
])
tag(N_DEWI, 'hot_prospect', sales=True)
analyze(N_DEWI, nama='Dewi Lestari', kebutuhan='Nusa Volt S warna Putih, pembelian cash, kirim ke Depok', waktu='bulan ini', anggaran='Rp 18.900.000', ringkasan='Membeli Volt S Putih secara cash dengan bonus helm & jas hujan, dikirim ke Depok.')
set_time(at(13, 11, 30))
call('lead_deal_save', 'POST', token='@admin', body={'number': N_DEWI, 'value': 18900000, 'close_est': ymd(-13)}); tick(1)
call('sales_po_add', 'POST', token='@admin', body={'number': N_DEWI, 'date': ymd(-13), 'no': 'PO-NEV-2611-001', 'note': 'Volt S Putih, cash, kirim Depok'})
tick(2); call('sales_deal', 'POST', token='@admin', body={'number': N_DEWI})
tick(2); tag(N_DEWI, 'active_customer')
act(N_DEWI, at(10, 14, 0), 'call', 'Konfirmasi unit sudah diterima dalam kondisi baik. Pelanggan puas, minta info servis pertama.')

# Andi (H-12) -> pipeline Negosiasi
N_ANDI = '6281299900101'
convo(N_ANDI, 'Andi', at(12, 10, 5), [
 ('in', 'Halo kak, mau tanya harga Nusa Volt X berapa ya?', 'Halo Kak! Nusa Volt X harganya Rp 24.500.000 OTR Jakarta, sudah termasuk STNK, BPKB, charger, dan garansi baterai 5 tahun. Jarak tempuhnya sampai ± 110 km sekali cas. Boleh tahu Kakak domisili di mana?'),
 ('in', 'Saya di Bekasi. Bisa dicicil ga?', 'Bisa Kak 😊 Cicilan lewat leasing partner kami dengan DP mulai 10% (± Rp 2.450.000). Perkiraan angsuran: 12 bln ± Rp 2,1 jt, 24 bln ± Rp 1,15 jt, 36 bln ± Rp 830 rb per bulan. Angka final mengikuti persetujuan leasing. Mau sekalian dijadwalkan test ride?'),
 ('in', 'Boleh, Sabtu ini bisa test ride jam 10?', 'Bisa Kak, showroom buka Sabtu 09.00–18.00. Boleh minta nama lengkap Kakak? Nanti tim sales kami konfirmasi jadwalnya.'),
 ('in', 'Andi Pratama', 'Terima kasih Kak Andi! Test ride Nusa Volt X: Sabtu jam 10.00 di showroom Nusa EV, Jl. Mawar Raya No. 12, Jakarta Timur. Jangan lupa bawa SIM C ya. Tim sales akan konfirmasi 🙏', 20),
 ('human',), ('claim',),
 ('agent', 'admin', 'Halo Kak Andi, jadwal test ride Sabtu 10.00 sudah kami kunci ya. Nanti ditemani Rina dari tim sales 😊', 4),
 ('in', 'Siap kak, terima kasih', None, 2),
 ('resolve',),
])
call('save_contact', 'POST', token='@admin', body={'number': N_ANDI, 'name': 'Andi Pratama'})
tag(N_ANDI, 'hot_prospect', sales=True)
analyze(N_ANDI, nama='Andi Pratama', kebutuhan='Nusa Volt X, kredit, test ride', waktu='Sabtu jam 10.00 (test ride)', anggaran='DP ± Rp 2.450.000, cicilan 24 bulan', ringkasan='Tertarik Volt X dengan kredit, domisili Bekasi, test ride dijadwalkan Sabtu 10.00.')
status(N_ANDI, 'qualified', at(12, 11, 0))
act(N_ANDI, at(11, 9, 30), 'wa', 'Konfirmasi ulang jadwal test ride Sabtu 10.00, pelanggan oke.', ymd(-9), '10:00', 'Test ride Volt X')
act(N_ANDI, at(9, 11, 0), 'presentasi', 'Test ride Volt X ± 25 menit. Suka akselerasi mode Sport & keyless. Tertarik warna Abu-abu, minta simulasi cicilan 24 bulan.')
status(N_ANDI, 'proposal', at(9, 11, 5))
deal(N_ANDI, 24500000, ymd(5), at(9, 11, 6))
act(N_ANDI, at(8, 15, 40), 'penawaran', 'Kirim simulasi cicilan 24 bulan (DP Rp 2.450.000, angsuran ± Rp 1,15 jt) + syarat dokumen leasing.', ymd(1), '10:00', 'Tanya keputusan & kelengkapan dokumen')
convo(N_ANDI, 'Andi', at(3, 19, 10), [
 ('in', 'Kak, kalau Volt X abu-abu ready stok? Kalau DP 3 juta bisa dapat potongan?', None, 15),
 ('claim',),
 ('agent', 'admin', 'Malam Kak Andi! Abu-abu ready 2 unit. Untuk DP Rp 3 juta, angsuran 24 bulan jadi ± Rp 1,12 jt/bln. Soal potongan, Rina dari tim sales akan menghubungi Kakak besok pagi ya 🙏', 3),
 ('in', 'Oke kak ditunggu', None, 3),
 ('agent', 'admin', 'Siap Kak Andi, terima kasih 🙏', 2),
 ('resolve',),
])
status(N_ANDI, 'negosiasi', at(2, 10, 15))
act(N_ANDI, at(2, 10, 10), 'call', 'Telepon: pelanggan minta potongan Rp 500 rb atau bonus baterai cadangan diskon. Sedang dicek ke SPV.', ymd(1), '13:00', 'Kabari hasil approval potongan')

# Siti (H-10) -> Follow-up, jatuh tempo hari ini
N_SITI = '6281299900102'
convo(N_SITI, 'Siti Rahmawati', at(10, 19, 40), [
 ('in', 'Malam kak, mau tanya motor listrik buat anak kuliah yang paling hemat yang mana ya?', 'Malam Kak! Untuk harian anak kuliah, Nusa Volt S paling pas: ringan, jarak tempuh ± 80 km sekali cas, harga Rp 18.900.000 OTR Jakarta. Biaya cas penuh hanya sekitar Rp 3.000-an 😊'),
 ('in', 'Kalau kredit DP nya berapa kak?', 'DP mulai 10% Kak, sekitar Rp 1.890.000 untuk Volt S. Tenor bisa 12, 24, atau 36 bulan. Syaratnya KTP, KK, dan slip gaji/rekening koran 3 bulan terakhir — tidak wajib kartu kredit.'),
 ('in', 'Oke kak nanti saya diskusi sama suami dulu', 'Siap Kak Siti, silakan didiskusikan. Kalau mau, tim sales kami bisa bantu hitung simulasi cicilannya ya 🙏', 3),
])
tag(N_SITI, 'warm', sales=True)
analyze(N_SITI, nama='Siti Rahmawati', kebutuhan='Motor listrik hemat untuk anak kuliah (Nusa Volt S), kredit', anggaran='DP ± Rp 1.890.000', ringkasan='Mencari motor hemat untuk anak kuliah, tertarik Volt S kredit, diskusi dulu dengan suami.')
status(N_SITI, 'follow_up', at(9, 10, 0))
deal(N_SITI, 18900000, ymd(7), at(9, 10, 1))
act(N_SITI, at(9, 10, 0), 'call', 'Telepon tidak diangkat. Kirim pesan WA berisi simulasi cicilan Volt S.', ymd(-4), '10:00', 'Telepon ulang')
act(N_SITI, at(4, 10, 20), 'call', 'Sudah diskusi dengan suami, cenderung ambil tenor 24 bulan. Minta waktu sampai gajian.', ymd(0), '15:00', 'Tanya keputusan setelah gajian')

# PT Kirim Cepat Logistik (H-9) -> pembelian armada, Negosiasi
N_HENDRA = '6281299900103'
convo(N_HENDRA, 'Hendra Gunawan', at(9, 13, 20), [
 ('in', 'Selamat siang, saya Hendra dari PT Kirim Cepat Logistik. Kami mau pengadaan 10 unit motor listrik untuk kurir. Ada harga khusus armada?', 'Selamat siang Pak Hendra! Untuk kurir, kami merekomendasikan Nusa Cargo Pro (3.000 W, ± 120 km, rak kargo hingga 100 kg). Untuk pembelian armada 5 unit ke atas ada harga khusus — saya sambungkan ke tim sales kami ya, Pak.', 8),
 ('human',), ('claim',),
 ('agent', 'admin', 'Siang Pak Hendra, terima kasih sudah menghubungi Nusa EV. Untuk 10 unit Cargo Pro kami bisa siapkan penawaran resmi harga armada. Boleh kami jadwalkan meeting di kantor Bapak minggu ini?', 12),
 ('in', 'Boleh, Kamis jam 10 di kantor kami daerah Cakung. Unit dibutuhkan awal Januari.', None, 5),
 ('agent', 'admin', 'Siap Pak, Kamis 10.00 di Cakung. Rina dari tim sales akan datang membawa unit demo Cargo Pro 👍', 3),
])
call('save_contact', 'POST', token='@admin', body={'number': N_HENDRA, 'name': 'Hendra — PT Kirim Cepat Logistik'})
tag(N_HENDRA, 'hot_prospect', sales=True)
analyze(N_HENDRA, nama='Hendra', kebutuhan='10 unit Nusa Cargo Pro untuk armada kurir PT Kirim Cepat Logistik', waktu='Unit dibutuhkan awal Januari', ringkasan='Perusahaan kurir minta harga armada 10 unit Cargo Pro, meeting Kamis 10.00 di Cakung.')
set_time(at(9, 14, 0))
call('lead_info_save', 'POST', token='@admin', body={'number': N_HENDRA, 'company': 'PT Kirim Cepat Logistik', 'source': 'manual'})
status(N_HENDRA, 'qualified', at(9, 14, 5))
act(N_HENDRA, at(6, 10, 0), 'meeting', 'Meeting di kantor Cakung bersama Pak Hendra & tim operasional. Kebutuhan 10 unit Cargo Pro, sistem tukar baterai, servis di lokasi. Unit demo dicoba 3 kurir.')
status(N_HENDRA, 'proposal', at(6, 12, 0))
act(N_HENDRA, at(5, 16, 0), 'penawaran', 'Kirim penawaran resmi 10 unit Cargo Pro Rp 310.000.000 (harga armada Rp 31 jt/unit), garansi baterai 5 th, servis on-site 1 th.', ymd(-2), '10:00', 'Follow-up penawaran')
deal(N_HENDRA, 310000000, ymd(14), at(5, 16, 2))
act(N_HENDRA, at(1, 10, 30), 'call', 'Pak Hendra minta tambah 2 baterai cadangan dengan harga khusus. Penawaran masuk tahap approval direksi.', ymd(2), '10:00', 'Follow-up approval direksi')
status(N_HENDRA, 'negosiasi', at(1, 10, 35))

# Yoga (H-7) -> tukar tambah, Qualified
N_YOGA = '6281299900106'
convo(N_YOGA, 'Yoga Saputra', at(7, 20, 15), [
 ('in', 'Bisa tukar tambah motor bensin ga kak? Saya ada Beat 2019', 'Bisa Kak! Tukar tambah berlaku untuk motor bensin merek apa pun. Harga taksiran Beat 2019 ditentukan setelah unit dicek di showroom (± 30 menit). Jangan lupa bawa STNK & BPKB asli ya.'),
 ('in', 'Mau ganti ke Volt X kak. Kira2 Beat saya dihargai berapa?', 'Taksiran pastinya menunggu pengecekan unit, Kak. Nilai tukar tambah langsung memotong harga Volt X (Rp 24.500.000) atau dipakai sebagai DP. Mau saya jadwalkan cek unit sekaligus test ride?'),
 ('in', 'Minggu depan aja kak saya kabari', 'Siap Kak Yoga, ditunggu kabarnya ya 🙏', 3),
])
tag(N_YOGA, 'warm', sales=True)
analyze(N_YOGA, nama='Yoga', kebutuhan='Tukar tambah Honda Beat 2019 ke Nusa Volt X', waktu='minggu depan', ringkasan='Ingin tukar tambah Beat 2019 ke Volt X, akan mengabari minggu depan.')
status(N_YOGA, 'qualified', at(6, 9, 30))
deal(N_YOGA, 24500000, ymd(12), at(6, 9, 31))
act(N_YOGA, at(6, 9, 30), 'wa', 'Kirim info syarat tukar tambah & promo Volt X. Pelanggan akan datang cek unit minggu depan.', ymd(2), '11:00', 'Ingatkan jadwal cek unit Beat')

# Maya (H-6) -> dijawab bot sampai selesai
N_MAYA = '6281299900107'
convo(N_MAYA, 'Maya Anggraini', at(6, 16, 5), [
 ('in', 'Kak aku tinggal di apartemen, bisa ngecas motornya gimana ya?', 'Bisa Kak 😊 Baterai Nusa EV bisa dilepas, jadi bisa dibawa dan dicas di dalam unit apartemen pakai stop kontak biasa 220 V. Waktu cas 0–100% ± 4–5 jam.'),
 ('in', 'Listrik unitku 1300 VA aman?', 'Aman Kak. Daya charger 600 W, jadi 1.300 VA cukup selama tidak bersamaan dengan alat berdaya besar seperti setrika atau microwave.'),
 ('in', 'Oke makasih infonya kak', 'Sama-sama Kak Maya! Kalau mau test ride, showroom buka setiap hari ya ⚡', 3),
])
tag(N_MAYA, 'new')

# Rudi (H-5) -> komplain, ditangani admin, selesai
N_RUDI = '6281299900105'
convo(N_RUDI, 'Rudi Hartono', at(5, 8, 15), [
 ('in', 'Kak saya mau komplain, baterai Volt S saya kok cepet habis ya, sekarang cuma dapat 50 km', None, 20),
 ('claim',),
 ('agent', 'admin', 'Selamat pagi Pak Rudi, mohon maaf atas ketidaknyamanannya 🙏 Boleh info motor dibeli bulan apa dan biasanya dicas sampai penuh atau dicabut di tengah?', 6),
 ('in', 'Beli bulan Juni kak. Biasanya dicas semalaman', None, 4),
 ('agent', 'admin', 'Baik Pak. Kemungkinan perlu kalibrasi BMS baterai. Masih dalam garansi, jadi gratis. Bisa dibawa ke bengkel showroom besok jam 09.00?', 5),
 ('in', 'Oke kak besok saya bawa', None, 2),
 ('at', at(4, 13, 30)),
 ('in', 'Kak sudah dicek tadi, katanya firmware BMS diupdate. Sekarang normal lagi 90an km. Makasih ya', None, 7),
 ('agent', 'admin', 'Syukurlah Pak Rudi, sama-sama! Kalau ada kendala lagi langsung kabari kami ya 🙏', 3),
 ('resolve',),
])
tag(N_RUDI, 'active_customer')

# Fajar (H-3) -> booking servis lewat bot
N_FAJAR = '6281299900108'
convo(N_FAJAR, 'Fajar Nugroho', at(3, 9, 0), [
 ('in', 'Pagi kak, mau booking servis berkala Volt X hari Sabtu bisa?', 'Pagi Kak Fajar! Bisa, bengkel showroom buka Sabtu 09.00–18.00. Servis berkala dianjurkan tiap 3.000 km. Kalau masih di tahun pertama, jasa servisnya gratis 😊 Mau jam berapa?'),
 ('in', 'Jam 1 siang kak', 'Siap, servis Volt X atas nama Kak Fajar: Sabtu jam 13.00 sudah dicatat. Mohon bawa buku servis ya 🙏', 3),
])
tag(N_FAJAR, 'active_customer')

# Dewi kembali bertanya (H-2)
convo(N_DEWI, 'Dewi Lestari', at(2, 9, 45), [
 ('in', 'Kak, STNK saya kira-kira jadi kapan ya?', 'Halo Kak Dewi! Proses STNK 14–21 hari kerja sejak pembelian, jadi perkiraan selesai awal bulan depan. Nanti tim kami kabari bila sudah bisa diambil atau dikirim 🙏', 3),
])

# Ratna (H-2) -> kredit, sedang ditangani admin
N_RATNA = '6281299900112'
convo(N_RATNA, 'Ratna Sari', at(2, 14, 20), [
 ('in', 'Siang kak, kalau kredit tanpa kartu kredit bisa? Saya ibu rumah tangga', 'Bisa Bu 😊 Kredit tidak wajib kartu kredit. Syaratnya KTP, KK, dan bukti penghasilan — untuk ibu rumah tangga bisa memakai slip gaji/rekening koran suami 3 bulan terakhir.'),
 ('in', 'Kalau gitu saya mau ajukan untuk Volt S ya kak', 'Baik Bu, saya sambungkan ke admin untuk proses pengajuan leasing ya 🙏', 6),
 ('human',), ('claim',),
 ('agent', 'admin', 'Siang Bu Ratna, saya Admin Nusa EV. Boleh kirim foto KTP Ibu, KK, dan rekening koran 3 bulan terakhir? Setelah lengkap kami ajukan ke leasing, prosesnya 1–3 hari kerja.', 10),
 ('in', 'Baik kak, nanti malam saya kirim ya', None, 2),
])
tag(N_RATNA, 'hot_prospect', sales=True)
analyze(N_RATNA, nama='Ratna', kebutuhan='Kredit Nusa Volt S tanpa kartu kredit', ringkasan='Ibu rumah tangga ingin mengajukan kredit Volt S; dokumen akan dikirim malam ini.')
status(N_RATNA, 'follow_up', at(2, 15, 0))
deal(N_RATNA, 18900000, ymd(6), at(2, 15, 1))
act(N_RATNA, at(2, 15, 0), 'wa', 'Menunggu foto KTP, KK, dan rekening koran suami untuk pengajuan leasing.', ymd(1), '10:00', 'Cek dokumen leasing Bu Ratna')

# Lina (hari ini) -> belum dibalas, menunggu admin
N_LINA = '6281299900109'
convo(N_LINA, 'Lina Marlina', at(0, 14, 10), [
 ('in', 'Kak Volt X warna merah ready? Saya mau ambil minggu ini, cash', 'Halo Kak Lina! Volt X warna Merah memang khusus tipe ini 😍 Untuk cek stok dan proses pembelian cash, saya sambungkan ke tim kami ya.', 4),
 ('human',),
 ('in', 'Ok ditunggu ya kak', None, 2),
])
tag(N_LINA, 'hot_prospect')

# Nanda (hari ini) -> bot sedang melayani
N_NANDA = '6281299900111'
convo(N_NANDA, 'Nanda Putri', at(0, 16, 45), [
 ('in', 'Kak hari Minggu showroom buka? Mau test ride Volt S', 'Buka Kak! Hari Minggu showroom buka 10.00–16.00. Test ride gratis, bawa SIM C ya. Mau saya catat jam berapa?'),
 ('in', 'Jam 11 kak, atas nama Nanda', 'Siap Kak Nanda, test ride Volt S hari Minggu jam 11.00 sudah dicatat. Sampai ketemu di showroom 😊', 2),
])
tag(N_NANDA, 'new')

# ---------- 4. Lead manual (CRM) ----------
set_time(at(4, 15, 10))
call('lead_create', 'POST', token='@sales', body={'number': '081299900201', 'name': 'Teguh Wibowo', 'source': 'walkin', 'status': 'qualified', 'value': '18900000', 'close_est': ymd(10), 'note': 'Datang ke showroom, tertarik Volt S warna Hitam Doff.'})
act('6281299900201', at(4, 15, 20), 'visit', 'Lihat-lihat Volt S & Volt X, minta brosur dan simulasi cash vs kredit.', ymd(1), '11:00', 'Kirim simulasi & tanya keputusan')
set_time(at(8, 11, 0))
call('lead_create', 'POST', token='@sales', body={'number': '081299900202', 'name': 'Irwan Setiadi', 'company': 'CV Sayur Segar Nusantara', 'source': 'event', 'status': 'proposal', 'value': '98700000', 'close_est': ymd(20), 'note': 'Kenalan di pameran otomotif. Butuh 3 Cargo Pro untuk antar sayur.'})
act('6281299900202', at(7, 14, 0), 'penawaran', 'Kirim penawaran 3 unit Cargo Pro Rp 98.700.000 via email.', ymd(3), '14:00', 'Follow-up penawaran CV Sayur Segar')
set_time(at(1, 19, 30))
call('lead_create', 'POST', token='@sales', body={'number': '081299900203', 'name': 'Dimas Arya', 'source': 'sosmed', 'status': 'baru', 'note': 'DM Instagram, tanya Volt X untuk ojek online.'})

# Bambang -> Close Lose
act(N_BAMBANG, at(13, 10, 0), 'call', 'Follow-up harga & promo. Pelanggan masih membandingkan dengan merek lain.', ymd(-8), '10:00', 'Follow-up kedua')
act(N_BAMBANG, at(8, 10, 15), 'call', 'Pelanggan sudah membeli merek lain karena dapat subsidi kantor.')
status(N_BAMBANG, 'closed_lost', at(8, 10, 20), note='Kalah dari kompetitor (ada subsidi kantor).')
set_time(at(8, 10, 22)); tag(N_BAMBANG, 'lost')

# ---------- 5. Task ----------
def task_from_bubble(num, title, status_, assignee, due, note, t, kind='in', idx_text=None):
    set_time(t)
    logs = [e for e in rj('chatbot-log.json') if e.get('ip') == num and e.get('channel') == 'whatsapp' and e.get('q')]
    e = [x for x in logs if idx_text in x['q']][0]
    src = {'number': num, 'k': 'q' + e['ts'] + e.get('wamid', ''), 'ts': e['ts'], 'kind': 'in', 'text': e['q'], 'mt': '', 'mn': ''}
    return call('task_save', 'POST', token='@admin', body={'title': title, 'status': status_, 'assignee': assignee, 'due': due, 'note': note, 'src': src})

r = task_from_bubble(N_LINA, 'Cek stok Volt X Merah & kabari Kak Lina (cash minggu ini)', 'new', 'admin', ymd(0), 'Prioritas — pembeli cash.', at(0, 14, 25), idx_text='merah')
r = task_from_bubble(N_HENDRA, 'Siapkan unit demo Cargo Pro untuk meeting Kamis di Cakung', 'done', 'sales', ymd(-6), '', at(9, 15, 0), idx_text='pengadaan')
set_time(at(1, 11, 0))
r = call('task_save', 'POST', token='@sales', body={'title': 'Revisi penawaran PT Kirim Cepat + 2 baterai cadangan', 'status': 'progress', 'assignee': 'sales', 'due': ymd(1), 'note': 'Minta approval harga baterai cadangan ke SPV dulu.', 'lead': N_HENDRA})
tid = r.get('task', {}).get('id')
set_time(at(0, 9, 15)); call('task_note', 'POST', token='@admin', body={'id': tid, 'text': 'SPV setuju baterai cadangan Rp 5,9 jt/unit. Silakan kirim revisi.'})
r = task_from_bubble(N_RATNA, 'Cek kelengkapan dokumen leasing Bu Ratna', 'pending', 'admin', ymd(1), 'Menunggu dokumen dikirim pelanggan.', at(2, 15, 10), idx_text='ajukan')

# ---------- 6. Chat web (widget) ----------
def web(start, msgs, lead=None):
    set_time(start)
    r = call('web_conv_new', 'POST', body={})
    cid, vid = r.get('conversation_id') or r.get('id'), r.get('visitor_id')
    if lead: call('web_lead_save', 'POST', body={'visitor_id': vid, 'name': lead[0], 'phone': lead[1]})
    hist = []
    for q, a in msgs:
        tick(1); ai_queue([a])
        call('chat', 'POST', body={'message': q, 'conversation_id': cid, 'visitor_id': vid, 'history': hist, 'utm': {'source': 'google', 'medium': 'organic'}})
        hist += [{'role': 'user', 'content': q}, {'role': 'assistant', 'content': a}]
        tick(2)
web(at(4, 21, 5), [('Berapa lama ngecas sampai penuh?', 'Waktu cas 0–100% sekitar 4–5 jam pakai stop kontak rumah biasa 220 V, Kak.'),
                   ('Bisa pakai listrik rumah 900 VA?', 'Bisa Kak, daya charger 600 W. Saat mengecas, hindari menyalakan alat berdaya besar bersamaan. Untuk lebih leluasa disarankan 1.300 VA ke atas.')])
web(at(0, 11, 30), [('Ada promo akhir tahun?', 'Ada Kak! Bulan ini pembelian Volt S dapat bonus helm + jas hujan, dan tukar tambah motor bensin bisa langsung jadi DP. Mau saya bantu jadwalkan test ride?')])

set_time(NOW)
print('selesai')
