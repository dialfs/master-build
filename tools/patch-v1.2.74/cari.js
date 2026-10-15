  /* ====================================================================== *
   *  v1.2.74: PUSAT BANTUAN — cari panduan ("cara lihat kontak leads")
   *  Artikel singkat per tugas, disaring per peran. "Tunjukkan di layar"
   *  menjalankan tur mini (mesin tur yang sama) lalu tetap di halaman tujuan.
   * ====================================================================== */
  var R_ALL = 'super_admin,admin,supervisor,wa_agent', R_SPV = 'super_admin,admin,supervisor', R_ADM = 'super_admin,admin', R_SA = 'super_admin';
  function hClick(sel) { return function () { var b = document.querySelector(sel); if (b) b.click(); }; }
  var HELP = [
    { id: 'leads', roles: R_ALL, t: 'Melihat leads (calon pelanggan)', k: 'leads lead prospek calon pelanggan qualified follow up closed ringkasan kartu',
      s: ['Buka menu <b>Leads</b>.', 'Kartu dibuat otomatis oleh AI saat percakapan WhatsApp mencapai 8 pesan.', 'Pakai filter <b>Baru</b>, <b>Qualified</b>, <b>Follow-up</b>, <b>Closed</b>, lalu ubah status di kartu.'],
      show: [{ tab: 'leads', el: '#panel-leads .card', title: 'Filter leads', body: '<p>Pilih status untuk menyaring kartu leads. Kartunya tampil di bawah.</p>' }] },
    { id: 'kontak', roles: R_ALL, t: 'Melihat kontak & mengubah tag pipeline', k: 'kontak contact nomor pelanggan customer tag pipeline cold warm hot prospect unrated unqualified active churned daftar',
      s: ['Buka menu <b>Kontak</b>.', 'Saring dengan tag: Cold, Warm, Hot Prospect, Active Customer, dst.', 'Klik satu kontak untuk mengubah tag atau melihat detailnya.'],
      show: [{ tab: 'kontak', el: '#panel-kontak .card', title: 'Saring kontak', body: '<p>Klik tag untuk menyaring. Daftar kontak ada di bawah — klik satu kontak untuk mengubah tag.</p>' }] },
    { id: 'kontak-lead', roles: R_ALL, t: 'Melihat kontak yang jadi leads / hot prospect', k: 'kontak leads lead hot prospect warm calon pembeli nomor prospek',
      s: ['Ringkasan percakapannya ada di menu <b>Leads</b> (filter <b>Qualified</b> / <b>Follow-up</b>).', 'Nomor & tag pipeline-nya ada di menu <b>Kontak</b> → filter <b>Hot Prospect</b> atau <b>Warm</b>.', 'Dari kartu kontak, klik <b>Simpan ke HP</b> untuk menyimpan nomornya.'],
      show: [{ tab: 'leads', el: '#panel-leads .card', title: '1. Leads', body: '<p>Ringkasan tiap calon pelanggan. Saring <b>Qualified</b> / <b>Follow-up</b>.</p>' },
             { tab: 'kontak', el: '.contact-filter[data-contact-stage="hot_prospect"]', title: '2. Kontak Hot Prospect', body: '<p>Klik <b>Hot Prospect</b> untuk melihat nomor-nomor yang paling siap membeli.</p>' }] },
    { id: 'simpan-hp', roles: R_ALL, t: 'Menyimpan nomor kontak ke HP', k: 'simpan save nomor hp handphone vcf vcard kontak',
      s: ['Buka menu <b>Kontak</b>.', 'Klik kontak yang diinginkan.', 'Klik <b>Simpan ke HP</b> — file .vcf terunduh dan bisa dibuka di HP.'],
      show: [{ tab: 'kontak', el: '#contactList', title: 'Pilih kontak', body: '<p>Klik satu kontak, lalu tombol <b>Simpan ke HP</b> di kartunya.</p>' }] },
    { id: 'ekspor-kontak', roles: R_SPV, t: 'Ekspor / unduh daftar kontak (CSV)', k: 'ekspor export unduh download csv excel kontak daftar nomor',
      s: ['Buka menu <b>Kontak</b>.', 'Pilih filter bila perlu (mis. Hot Prospect).', 'Klik <b>Ekspor CSV</b> — hanya kontak sesuai filter yang diunduh.'],
      show: [{ tab: 'kontak', el: '#btnExportKontakCsv', title: 'Ekspor CSV', body: '<p>Mengunduh kontak sesuai filter aktif. Bisa dibuka di Excel / Google Sheets.</p>' }] },
    { id: 'vip', roles: R_ALL, t: 'Melihat pelanggan VIP yang ulang tahun hari ini', k: 'ulang tahun birthday vip ultah pelanggan',
      s: ['Buka menu <b>Kontak</b>.', 'Klik filter <b>Ulang Tahun VIP Hari Ini</b>.'],
      show: [{ tab: 'kontak', el: '.contact-filter[data-contact-stage="vip_birthday_today"]', title: 'Ulang Tahun VIP', body: '<p>Menampilkan kontak VIP yang berulang tahun hari ini.</p>' }] },
    { id: 'balas', roles: R_ALL, t: 'Membalas chat WhatsApp pelanggan', k: 'balas reply jawab chat pesan whatsapp wa claim ambil alih manual kirim pelanggan',
      s: ['Buka menu <b>Percakapan WA</b> dan klik chat pelanggan.', 'Klik <b>Claim</b> — bot berhenti menjawab nomor itu.', 'Tulis balasan di kolom bawah, lalu <b>Kirim</b>.'],
      show: [{ tab: 'wachat', el: '#waConvList', title: 'Pilih chat', body: '<p>Klik chat pelanggan yang ingin dibalas.</p>' },
             { tab: 'wachat', el: '#panel-wachat .wachat-thread', title: 'Claim lalu balas', body: '<p>Klik <b>Claim</b>, tulis balasan di kolom bawah, lalu <b>Kirim</b>.</p>' }] },
    { id: 'release', roles: R_ALL, t: 'Mengembalikan chat ke bot / antrean', k: 'release lepas kembalikan bot antrean selesai claim',
      s: ['Buka chat yang sedang Anda pegang di <b>Percakapan WA</b>.', 'Klik <b>Release</b> (kembali ke bot) atau <b>Lepas ke antrean</b> bila mode Manual.'],
      show: [{ tab: 'wachat', el: '#panel-wachat .wachat-thread', title: 'Release', body: '<p>Tombol <b>Release</b> / <b>Lepas ke antrean</b> ada di kepala chat yang sedang Anda pegang.</p>' }] },
    { id: 'serahkan', roles: R_SPV, t: 'Menyerahkan / memindahkan chat ke agent lain', k: 'serahkan pindahkan transfer assign bagi chat agent lain',
      s: ['Buka chat di <b>Percakapan WA</b>.', 'Di kepala chat, pilih agent pada menu <b>Serahkan ke…</b> / <b>Pindahkan ke…</b>.'],
      show: [{ tab: 'wachat', el: '#panel-wachat .wachat-thread', title: 'Serahkan ke agent', body: '<p>Menu <b>Serahkan ke…</b> ada di kepala chat setelah chat dibuka.</p>' }] },
    { id: '24jam', roles: R_ALL, t: 'Kenapa tidak bisa membalas chat? (jendela 24 jam)', k: 'tidak bisa balas gagal kirim 24 jam jendela tertutup template error',
      s: ['WhatsApp hanya mengizinkan balasan teks bebas dalam <b>24 jam</b> sejak pesan terakhir pelanggan.', 'Lewat dari itu, tunggu pelanggan mengirim pesan lagi, atau kirim template resmi lewat <b>Blast WA</b> (Supervisor/Admin).'],
      show: [{ tab: 'wachat', el: '#panel-wachat .wachat-thread', title: 'Catatan jendela 24 jam', body: '<p>Status jendela 24 jam tampil di atas kolom balasan saat chat dibuka.</p>' }] },
    { id: 'webchat', roles: R_ALL, t: 'Melihat chat dari website (widget)', k: 'web website widget pengunjung percakapan web chat situs',
      s: ['Buka menu <b>Percakapan Web</b>.', 'Klik percakapan untuk melihat tanya-jawab pengunjung dengan bot.'],
      show: [{ tab: 'webchat', el: '#webConvList', title: 'Percakapan Web', body: '<p>Daftar percakapan dari widget website.</p>' }] },
    { id: 'notif', roles: R_ALL, t: 'Mengaktifkan notifikasi pesan baru', k: 'notifikasi notif pemberitahuan bunyi alert pesan baru hp push',
      s: ['Klik tombol <b>Notifikasi</b> di bawah menu.', 'Pilih <b>Izinkan</b> pada pertanyaan browser.', 'Di HP, pasang dashboard ke layar utama (Add to Home Screen) agar lebih andal.'],
      show: [{ el: '#btnNotif', side: true, title: 'Notifikasi', body: '<p>Klik di sini lalu izinkan notifikasi.</p>' }] },
    { id: 'password', roles: R_ALL, t: 'Mengganti password', k: 'password sandi kata sandi ganti ubah akun login lupa',
      s: ['Buka menu <b>Profil Saya</b>.', 'Isi password lama, password baru (min. 8 karakter), dan konfirmasinya.', 'Klik <b>Simpan Password</b> — Anda akan diminta login ulang.', 'Lupa password? Minta Admin / Supervisor mengaturnya di menu <b>Pengguna</b>.'],
      show: [{ tab: 'profile', el: tourCard('profile', 'Ganti Password'), title: 'Ganti Password', body: '<p>Isi ketiga kolom lalu klik <b>Simpan Password</b>.</p>' }] },
    { id: 'laporan', roles: R_SPV, t: 'Melihat laporan & statistik percakapan', k: 'laporan statistik report jumlah chat traffic utm sumber tren grafik data',
      s: ['Buka menu <b>Laporan &amp; Log</b> → <b>Ringkasan</b>.', 'Atur tanggal & channel, lalu <b>Terapkan Filter</b>.', '<b>Unduh CSV</b> untuk data mentahnya.'],
      show: [{ tab: 'reports', pre: hClick('#repSeg [data-v="summary"]'), el: '#btnExport', title: 'Filter & unduh', body: '<p>Atur tanggal dan channel, lalu <b>Terapkan Filter</b> atau <b>Unduh CSV</b>.</p>' }] },
    { id: 'log', roles: R_SPV, t: 'Melihat log / riwayat semua percakapan', k: 'log riwayat history percakapan status dijawab ai menunggu balasan error',
      s: ['Buka menu <b>Laporan &amp; Log</b> → <b>Log Percakapan</b>.', 'Lihat status tiap chat: dijawab AI, menunggu balasan, dibalas agent.', 'Klik baris untuk detail, atau <b>Unduh CSV</b>.'],
      show: [{ tab: 'reports', pre: hClick('#repSeg [data-v="logs"]'), el: '#repLogs', title: 'Log Percakapan', body: '<p>Klik satu baris untuk melihat detail percakapannya.</p>' }] },
    { id: 'topik', roles: R_SPV, t: 'Melihat topik yang paling sering ditanyakan', k: 'topik pertanyaan sering ditanyakan faq tren analisa',
      s: ['Buka menu <b>Laporan &amp; Log</b> → <b>Topik</b>.', 'Jalankan pemindaian untuk mengelompokkan pertanyaan pelanggan.'],
      show: [{ tab: 'reports', pre: hClick('#repSeg [data-v="topics"]'), el: '#repTopics', title: 'Topik', body: '<p>Ringkasan topik pertanyaan pelanggan.</p>' }] },
    { id: 'kuota', roles: R_SPV, t: 'Melihat sisa kuota / penggunaan bulan ini', k: 'kuota sisa paket limit batas penggunaan usage habis bulan',
      s: ['Buka menu <b>Laporan &amp; Log</b> → <b>Ringkasan</b>.', 'Kartu <b>Penggunaan Bulan Ini</b> menunjukkan chat terpakai, reset, dan pesan WA keluar.'],
      show: [{ tab: 'reports', pre: hClick('#repSeg [data-v="summary"]'), el: '#usageCard', title: 'Penggunaan Bulan Ini', body: '<p>Kuota paket dan grafik 30 hari.</p>' }] },
    { id: 'blast', roles: R_SPV, t: 'Mengirim pesan massal (Blast WA)', k: 'blast broadcast massal kirim banyak template promo pengumuman',
      s: ['Buka menu <b>Blast WA</b>.', 'Pilih template yang sudah disetujui Meta dan isi variabelnya.', 'Pilih penerima (hanya kontak opt-in), lalu kirim. Hasilnya ada di <b>Riwayat Blast</b>.'],
      show: [{ tab: 'blast', el: '#panel-blast .card', title: 'Buat Blast Baru', body: '<p>Pilih template, isi variabel, pilih penerima, lalu kirim.</p>' }] },
    { id: 'kinerja', roles: R_ALL, t: 'Melihat kinerja agent & waktu respon', k: 'kinerja performa agent waktu respon response time ditangani belum dibalas tim laporan agent',
      s: ['Buka menu <b>Tim &amp; Agent</b>.', 'Di <b>Laporan per Agent</b>, pilih tanggal lalu <b>Tampilkan</b>.'],
      show: [{ tab: 'tim', el: tourCard('tim', 'Laporan per Agent'), title: 'Laporan per Agent', body: '<p>Chat ditangani, balasan, respon pertama, dan belum dibalas per agent.</p>' }] },
    { id: 'akun', roles: R_SPV, t: 'Menambah akun agent / supervisor', k: 'tambah akun user pengguna agent supervisor admin buat baru staf tim kursi hapus edit reset password',
      s: ['Buka menu <b>Pengguna</b>.', 'Isi username, nama, password, dan pilih peran.', 'Klik simpan. Jumlah akun dibatasi kursi paket.', 'Edit / hapus akun lewat tombol di tabel bawah.'],
      show: [{ tab: 'users', el: tourCard('users', 'Pengguna'), title: 'Tambah Pengguna', body: '<p>Isi formulir lalu simpan.</p>' }] },
    { id: 'kb-tambah', roles: R_ADM, t: 'Menambah / mengubah jawaban bot (Knowledge Base)', k: 'knowledge base kb jawaban bot ai tambah entri ubah edit pertanyaan info produk',
      s: ['Buka menu <b>Knowledge Base</b>.', 'Klik <b>+ Tambah Entri</b> atau edit entri yang ada.', 'Klik <b>Simpan Perubahan</b>, lalu cek di <b>Tes Chatbot</b>.'],
      show: [{ tab: 'kb', pre: hClick('.kb-tab[data-kbtab="entri"]'), el: '#btnAddKb', title: '+ Tambah Entri', body: '<p>Tambahkan tanya-jawab baru. Jangan lupa <b>Simpan Perubahan</b>.</p>' }] },
    { id: 'kb-impor', roles: R_ADM, t: 'Impor Knowledge Base dari CSV / PDF', k: 'impor import csv pdf upload unggah dokumen brosur kb massal',
      s: ['Buka menu <b>Knowledge Base</b>.', 'Klik <b>Impor CSV</b> (format: category, question, answer) atau <b>Impor PDF</b>.', 'Periksa hasilnya lalu klik <b>Simpan Perubahan</b>.'],
      show: [{ tab: 'kb', pre: hClick('.kb-tab[data-kbtab="entri"]'), el: '#btnImportCsv', title: 'Impor', body: '<p><b>Impor CSV</b> atau <b>Impor PDF</b> ada di sini.</p>' }] },
    { id: 'harga', roles: R_ADM, t: 'Mengatur daftar harga', k: 'harga price pricelist daftar harga tarif biaya produk paket',
      s: ['Buka menu <b>Knowledge Base</b> → tab <b>Daftar Harga</b>.', 'Tambah / ubah item harga lalu simpan. Bot memakai daftar ini saat ditanya harga.'],
      show: [{ tab: 'kb', pre: hClick('.kb-tab[data-kbtab="harga"]'), el: '#kbTabHarga', title: 'Daftar Harga', body: '<p>Kelola harga produk / layanan di sini.</p>' }] },
    { id: 'gaps', roles: R_ADM, t: 'Melihat pertanyaan yang belum bisa dijawab bot', k: 'belum terjawab tidak tahu gagal jawab gap pertanyaan kosong',
      s: ['Buka menu <b>Knowledge Base</b>.', 'Klik <b>Belum Terjawab</b>.', 'Tambahkan jawabannya ke KB.'],
      show: [{ tab: 'kb', pre: hClick('.kb-tab[data-kbtab="entri"]'), el: '#btnFindGaps', title: 'Belum Terjawab', body: '<p>Daftar pertanyaan pelanggan yang belum ada jawabannya di KB.</p>' }] },
    { id: 'tes', roles: R_ADM, t: 'Mencoba / menguji jawaban bot', k: 'tes test uji coba bot jawaban simulasi',
      s: ['Buka menu <b>Tes Chatbot</b>.', 'Ketik pertanyaan seperti pelanggan, lalu <b>Kirim</b>.'],
      show: [{ tab: 'test', el: '#panel-test .card', title: 'Tes Chatbot', body: '<p>Ketik pertanyaan di kolom bawah.</p>' }] },
    { id: 'sapaan', roles: R_ADM, t: 'Mengubah sapaan, gaya bahasa & teks balasan bot', k: 'sapaan salam greeting gaya bahasa persona teks balasan pesan pembuka bahasa',
      s: ['Buka menu <b>Balasan &amp; Tampilan</b>.', '<b>Konfigurasi Terstruktur</b>: sapaan, bahasa, aturan respon.', '<b>Teks Balasan</b>: pesan pembuka & balasan bawaan. Simpan setelah mengubah.'],
      show: [{ tab: 'content', el: tourCard('content', 'Teks Balasan'), title: 'Teks Balasan', body: '<p>Pesan pembuka dan balasan bawaan bot.</p>' }] },
    { id: 'tampilan', roles: R_ADM, t: 'Mengubah warna & tampilan widget', k: 'warna tampilan widget desain posisi logo bubble look',
      s: ['Buka menu <b>Balasan &amp; Tampilan</b>.', 'Ubah di kartu <b>Tampilan Widget</b>, lalu simpan.'],
      show: [{ tab: 'content', el: tourCard('content', 'Tampilan Widget'), title: 'Tampilan Widget', body: '<p>Warna, posisi, dan tampilan widget di website.</p>' }] },
    { id: 'widget-onoff', roles: R_ADM, t: 'Menyalakan / mematikan widget & tombol WhatsApp', k: 'nyalakan matikan aktifkan nonaktif widget bubble tombol whatsapp website',
      s: ['Buka menu <b>Widget &amp; API</b>.', 'Di <b>Status Widget</b>, geser saklar <b>AI Chatbot Bubble</b> atau <b>WhatsApp Floating Button</b>.'],
      show: [{ tab: 'widget', el: tourCard('widget', 'Status Widget'), title: 'Status Widget', body: '<p>Saklar untuk bubble AI dan tombol WhatsApp.</p>' }] },
    { id: 'form', roles: R_ADM, t: 'Meminta nama & nomor pengunjung sebelum chat', k: 'form data pengunjung nama nomor hp lead form isian sebelum chat',
      s: ['Buka menu <b>Widget &amp; API</b>.', 'Aktifkan <b>Form Data Pengunjung</b>. Datanya masuk ke menu Kontak.'],
      show: [{ tab: 'widget', el: tourCard('widget', 'Form Data Pengunjung'), title: 'Form Data Pengunjung', body: '<p>Aktifkan form dan atur labelnya.</p>' }] },
    { id: 'pasang', roles: R_ADM, t: 'Memasang widget di website', k: 'pasang install embed website gtm google tag manager kode script html',
      s: ['Buka menu <b>Pemasangan (GTM)</b>.', 'Salin kode Custom HTML ke Google Tag Manager, atau pakai kode pasang langsung.'],
      show: [{ tab: 'install', el: tourCard('install', 'Langkah Pemasangan'), title: 'Pemasangan', body: '<p>Ikuti langkahnya, lalu salin kode di bawah.</p>' }] },
    { id: 'eskalasi', roles: R_ADM, t: 'Mengatur pesan penutup otomatis & alarm darurat', k: 'auto closing penutup eskalasi darurat alarm emergency pushover tamu menunggu lama',
      s: ['Buka menu <b>Respon &amp; Eskalasi</b>.', '<b>Auto-Closing</b>: pesan penutup ke tamu yang diam.', '<b>Eskalasi Darurat</b>: alarm ke Supervisor/Manager bila tamu menunggu tanpa balasan.'],
      show: [{ tab: 'eskalasi', el: tourCard('eskalasi', 'Auto-Closing'), title: 'Auto-Closing', body: '<p>Pesan penutup otomatis.</p>' },
             { tab: 'eskalasi', el: tourCard('eskalasi', 'Eskalasi Darurat'), title: 'Eskalasi Darurat', body: '<p>Alarm saat tamu menunggu terlalu lama.</p>' }] },
    { id: 'mode', roles: R_SA, t: 'Mengubah mode balasan WhatsApp (AI / Manual)', k: 'mode manual ai otomatis matikan bot agent saja balasan whatsapp',
      s: ['Buka menu <b>Tim &amp; Agent</b>.', 'Pilih <b>AI + Agent</b> atau <b>Manual</b>, lalu <b>Simpan</b>.'],
      show: [{ tab: 'tim', el: '#timModeCard', title: 'Mode Balasan WhatsApp', body: '<p>Pilih mode lalu Simpan.</p>' }] },
    { id: 'api', roles: R_SA, t: 'Mengganti API key / model AI', k: 'api key model ai claude openrouter gemini gpt provider konfigurasi',
      s: ['Buka menu <b>Widget &amp; API</b>.', 'Ubah di kartu <b>Konfigurasi API AI</b>, lalu simpan.'],
      show: [{ tab: 'widget', el: tourCard('widget', 'Konfigurasi API AI'), title: 'Konfigurasi API AI', body: '<p>Provider, API key, dan model.</p>' }] },
    { id: 'wa-connect', roles: R_SA, t: 'Menghubungkan nomor WhatsApp ke bot', k: 'hubungkan connect whatsapp nomor meta cloud api bot token webhook',
      s: ['Buka menu <b>Widget &amp; API</b>.', 'Isi kartu <b>WhatsApp Bot</b> (Meta Cloud API), lalu simpan.'],
      show: [{ tab: 'widget', el: tourCard('widget', 'WhatsApp Bot'), title: 'WhatsApp Bot', body: '<p>Pengaturan koneksi WhatsApp.</p>' }] },
    { id: 'update', roles: R_ADM, t: 'Memasang pembaruan / melihat fitur baru', k: 'pembaruan update versi rilis fitur baru upgrade',
      s: ['Buka menu <b>Pembaruan</b>.', 'Bila ada versi baru, klik <b>Pasang pembaruan</b>.'],
      show: [{ tab: 'pembaruan', el: '#panel-pembaruan .rel-hero', title: 'Pembaruan', body: '<p>Versi Anda dan rilis terbaru.</p>' }] },
    { id: 'tur', roles: R_ALL, t: 'Mengulang tur panduan lengkap', k: 'tur panduan tutorial ulang awal pengenalan belajar',
      s: ['Klik <b>Mulai tur lengkap</b> di bagian bawah jendela ini.'], show: null }
  ];
  var HELP_STOP = ' cara gimana bagaimana gmn gimna untuk utk buat bisa mau ingin saya aku kita yang yg di ke dari dan atau ini itu nya dong deh ya apa mana kok kenapa tolong mohon how to the a ';
  var HELP_SYN = { chat: 'percakapan pesan', pesan: 'chat', wa: 'whatsapp', whatsapp: 'wa', customer: 'pelanggan', pelanggan: 'customer kontak', tamu: 'pelanggan',
    lead: 'leads', prospek: 'leads prospect', contact: 'kontak', nomor: 'kontak', export: 'ekspor', download: 'unduh', unduh: 'ekspor', sandi: 'password',
    notif: 'notifikasi', kb: 'knowledge', jawaban: 'knowledge', harga: 'price', lihat: 'melihat', liat: 'melihat', cek: 'melihat', user: 'akun pengguna',
    akun: 'pengguna', staf: 'agent', cs: 'agent', admin: 'pengguna', report: 'laporan', statistik: 'laporan', broadcast: 'blast', reply: 'balas', jawab: 'balas', ga: 'tidak', gak: 'tidak', nggak: 'tidak', gk: 'tidak', engga: 'tidak', gagal: 'tidak' };
  function helpNorm(s) { return String(s || '').toLowerCase().replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/[^a-z0-9À-ɏ]+/g, ' ').trim(); }
  function helpTokens(q) {
    var out = [];
    helpNorm(q).split(' ').forEach(function (w) {
      if (!w || HELP_STOP.indexOf(' ' + w + ' ') !== -1) return;
      w = w.replace(/(nya|kah|lah)$/, '') || w;
      out.push([w]);
      if (HELP_SYN[w]) out[out.length - 1] = out[out.length - 1].concat(HELP_SYN[w].split(' '));
    });
    return out;   // tiap token = daftar alternatif (sinonim)
  }
  function helpScore(a, toks) {
    if (!a._t) { a._t = ' ' + helpNorm(a.t) + ' '; a._k = ' ' + helpNorm(a.k) + ' '; a._s = ' ' + helpNorm(a.s.join(' ')) + ' '; }
    var score = 0, hit = 0;
    toks.forEach(function (alts) {
      var best = 0;
      alts.forEach(function (w) {
        var whole = ' ' + w + ' ', part = w.length >= 4 ? w : null;
        if (a._t.indexOf(whole) !== -1) best = Math.max(best, 6); else if (part && a._t.indexOf(part) !== -1) best = Math.max(best, 4);
        if (a._k.indexOf(whole) !== -1) best = Math.max(best, 4); else if (part && a._k.indexOf(part) !== -1) best = Math.max(best, 3);
        if (a._s.indexOf(whole) !== -1) best = Math.max(best, 1.5); else if (part && a._s.indexOf(part) !== -1) best = Math.max(best, 1);
      });
      if (best) { hit++; score += best; }
    });
    return hit ? score * (hit / toks.length) : 0;   // utamakan artikel yang cocok dengan lebih banyak kata
  }
  function helpList() {
    return HELP.filter(function (a) {
      if (!can(a.roles)) return false;
      return !a.show || a.show.every(function (s) { return !s.tab || tourTabAllowed(s.tab); });
    });
  }
  var HELP_POPULAR = { wa_agent: ['balas', 'kontak-lead', 'leads', 'kontak', '24jam', 'password'],
    supervisor: ['serahkan', 'kinerja', 'kontak-lead', 'akun', 'laporan', 'blast'],
    admin: ['kb-tambah', 'kontak-lead', 'laporan', 'akun', 'pasang', 'sapaan'],
    super_admin: ['kb-tambah', 'kontak-lead', 'laporan', 'akun', 'mode', 'api'] };

  function helpEls() {
    var r = document.getElementById('helpRoot');
    if (r) return r;
    r = document.createElement('div');
    r.id = 'helpRoot';
    r.innerHTML = '<div class="help-back" data-h="close"></div>' +
      '<div class="help-box" role="dialog" aria-modal="true" aria-labelledby="helpTitle">' +
        '<div class="help-head"><div><b id="helpTitle">Pusat Bantuan</b><small>Ketik pertanyaan Anda, mis. "cara lihat kontak leads"</small></div>' +
          '<button type="button" class="help-x" data-h="close" title="Tutup (Esc)">' + ico('x', 18) + '</button></div>' +
        '<div class="help-search">' + ico('search', 17) + '<input type="search" id="helpQ" placeholder="Cari panduan… (kontak, balas chat, password)" autocomplete="off" enterkeyhint="search"></div>' +
        '<div class="help-res" id="helpRes"></div>' +
        '<div class="help-foot"><span>Baru memakai dashboard?</span><button type="button" class="btn sm" data-h="tour">' + ico('circle-help', 15) + ' Mulai tur lengkap</button></div>' +
      '</div>';
    document.body.appendChild(r);
    r.addEventListener('click', function (e) {
      e.stopPropagation();
      var b = e.target.closest('[data-h]'); if (!b) return;
      var h = b.dataset.h;
      if (h === 'close') helpClose();
      else if (h === 'tour') { helpClose(); tourStart(role, false); }
      else if (h === 'open') { var it = b.closest('.help-item'); var was = it.classList.contains('open'); $$('#helpRes .help-item').forEach(function (x) { x.classList.remove('open'); }); if (!was) it.classList.add('open'); }
      else if (h === 'show') helpShow(b.dataset.id);
      else if (h === 'q') { $('#helpQ').value = b.dataset.q; helpRender(); }
    });
    var deb;
    $('#helpQ').addEventListener('input', function () { clearTimeout(deb); deb = setTimeout(helpRender, 120); });
    $('#helpQ').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); var first = document.querySelector('#helpRes .help-item [data-h="show"]'); if (first) first.click(); }
    });
    return r;
  }
  function helpItem(a, open) {
    return '<div class="help-item' + (open ? ' open' : '') + '">' +
      '<button type="button" class="help-q" data-h="open"><span>' + a.t + '</span>' + ico('chevron-down', 16) + '</button>' +
      '<div class="help-a"><ol>' + a.s.map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ol>' +
      (a.show ? '<button type="button" class="btn sm" data-h="show" data-id="' + a.id + '">' + ico('sparkles', 14) + ' Tunjukkan di layar</button>'
              : '<button type="button" class="btn sm" data-h="tour">' + ico('circle-help', 14) + ' Mulai tur lengkap</button>') +
      '</div></div>';
  }
  function helpRender() {
    var q = $('#helpQ').value.trim(), list = helpList(), box = $('#helpRes');
    if (!q) {
      var pop = (HELP_POPULAR[role] || []).map(function (id) { return list.filter(function (a) { return a.id === id; })[0]; }).filter(Boolean);
      box.innerHTML = '<div class="help-lbl">Sering dicari</div>' + pop.map(function (a) { return helpItem(a, false); }).join('') +
        '<div class="help-lbl">Semua topik (' + list.length + ')</div>' +
        '<div class="help-chips">' + list.filter(function (a) { return pop.indexOf(a) === -1; }).map(function (a) {
          return '<button type="button" data-h="q" data-q="' + esc(helpNorm(a.t)) + '">' + a.t + '</button>'; }).join('') + '</div>';
      return;
    }
    var toks = helpTokens(q);
    var res = toks.length ? list.map(function (a) { return { a: a, s: helpScore(a, toks) }; })
      .filter(function (x) { return x.s > 0; }).sort(function (x, y) { return y.s - x.s; }).slice(0, 6) : [];
    if (res.length) res = res.filter(function (x) { return x.s >= res[0].s * 0.35; });   // buang hasil yang terlalu lemah
    box.innerHTML = res.length
      ? '<div class="help-lbl">' + res.length + ' hasil</div>' + res.map(function (x, i) { return helpItem(x.a, i === 0); }).join('')
      : '<div class="help-empty">Belum ketemu panduan untuk "<b>' + esc(q) + '</b>".<br>Coba kata lain, misalnya <a href="#" data-h="q" data-q="kontak">kontak</a>, <a href="#" data-h="q" data-q="balas chat">balas chat</a>, atau <a href="#" data-h="q" data-q="password">password</a>.</div>';
  }
  function helpOpen(q) {
    if (tour) tourEnd(true, true);
    var r = helpEls();
    r.classList.add('on');
    document.body.classList.add('help-on');
    if (tourIsMobile()) toggleSide(false);
    $('#helpQ').value = q || '';
    helpRender();
    setTimeout(function () { try { $('#helpQ').focus(); } catch (e) {} }, 30);
  }
  function helpClose() {
    var r = document.getElementById('helpRoot');
    if (r) r.classList.remove('on');
    document.body.classList.remove('help-on');
  }
  function helpShow(id) {
    var a = HELP.filter(function (x) { return x.id === id; })[0];
    if (!a || !a.show) return;
    helpClose();
    tourStartCustom(a.show, a.t);
  }
  document.addEventListener('keydown', function (e) {
    var on = document.body.classList.contains('help-on');
    if (on && e.key === 'Escape') { e.preventDefault(); helpClose(); return; }
    // "/" membuka pencarian panduan (kecuali sedang mengetik)
    if (!on && !tour && e.key === '/' && !/^(input|textarea|select)$/i.test((e.target.tagName || '')) && !e.target.isContentEditable) { e.preventDefault(); helpOpen(''); }
  });
  window.deiHelp = helpOpen;
