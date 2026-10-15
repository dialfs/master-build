  /* ====================================================================== *
   *  v1.2.74: PANDUAN — guided walkthrough per peran
   *  Muncul sekali saat pertama login (per akun: users.json → tour_seen),
   *  bisa dibuka lagi lewat tombol "Panduan" di bawah menu / Profil Saya.
   *  Naikkan TOUR_VER bila isi panduan berubah besar → semua akun melihat lagi.
   * ====================================================================== */
  var TOUR_VER = 1;
  var TOUR_ORDER = ['super_admin', 'admin', 'supervisor', 'wa_agent'];
  var tour = null;   // { role, steps, i, preview, home, t }

  // Kartu di sebuah panel berdasarkan judul <h3>-nya (tahan perubahan urutan kartu)
  function tourCard(panel, title) {
    return function () {
      var cards = document.querySelectorAll('#panel-' + panel + ' .card');
      for (var k = 0; k < cards.length; k++) {
        var h = cards[k].querySelector('h3');
        if (h && h.textContent.indexOf(title) !== -1) return cards[k];
      }
      return null;
    };
  }
  var TS = {
    nav: function (body) { return { el: '#nav', side: true, title: 'Menu Anda', body: body }; },
    waList: function (body) { return { tab: 'wachat', el: '#waConvList', title: 'Percakapan WhatsApp', body: body }; },
    waThread: function (title, body) { return { tab: 'wachat', el: '#panel-wachat .wachat-thread', title: title, body: body }; },
    webchat: { tab: 'webchat', el: '#webConvList', title: 'Percakapan Web',
      body: '<p>Chat dari widget di website Anda. Pantau apa yang ditanyakan pengunjung dan bagaimana bot menjawab.</p><p>Bila pengunjung mengisi <b>Form Data Pengunjung</b>, nama &amp; nomornya menjadi judul percakapan.</p>' },
    reports: { tab: 'reports', el: '#repSeg', title: 'Laporan &amp; Log',
      body: '<ul><li><b>Ringkasan</b> — statistik percakapan, sumber traffic (UTM), dan tren harian.</li><li><b>Log Percakapan</b> — status tiap chat: dijawab AI, menunggu balasan, dibalas agent.</li><li><b>Topik</b> — hal yang paling sering ditanyakan pelanggan.</li></ul>' },
    leads: function (extra) { return { tab: 'leads', el: '#panel-leads .card', title: 'Leads',
      body: '<p>Kartu ringkasan dibuat otomatis oleh AI saat percakapan mencapai 8 pesan. AI menyiapkan bahannya — Anda yang menentukan statusnya.</p><p>Pakai filter <b>Baru</b>, <b>Qualified</b>, <b>Follow-up</b>, <b>Closed</b> untuk menindaklanjuti.' + (extra || '') + '</p>' }; },
    kontak: function (extra) { return { tab: 'kontak', el: '#panel-kontak .card', title: 'Kontak',
      body: '<p>Semua kontak WhatsApp dengan tag pipeline: Cold, Warm, Hot Prospect, Active Customer, dan lainnya.</p><p>Klik satu kontak untuk mengubah tag atau <b>Simpan ke HP</b>.' + (extra || '') + '</p>' }; },
    blast: { tab: 'blast', el: '#panel-blast .card', title: 'Blast WA',
      body: '<p>Kirim pesan template resmi Meta ke banyak kontak sekaligus.</p><p>Hanya ke kontak yang sudah <b>opt-in</b> dan memakai template yang sudah <b>disetujui Meta</b>.</p>' },
    agentReport: function (title, body) { return { tab: 'tim', el: tourCard('tim', 'Laporan per Agent'), title: title, body: body }; },
    users: function (body) { return { tab: 'users', el: tourCard('users', 'Pengguna'), title: 'Kelola akun tim', body: body }; },
    usage: { tab: 'reports', el: '#usageCard', title: 'Penggunaan bulan ini',
      body: '<p>Kuota percakapan paket Anda dan grafik 30 hari terakhir.</p><p>Bila kuota hampir habis, peringatan muncul di bagian atas dashboard.</p>' },
    kb: { tab: 'kb', el: '#kbTabEntri .card', title: 'Knowledge Base — sumber jawaban AI',
      body: '<p>Isi tanya-jawab tentang bisnis Anda: <b>+ Tambah Entri</b>, atau <b>Impor CSV / PDF</b>. Jangan lupa klik <b>Simpan Perubahan</b>.</p><p><b>Belum Terjawab</b> menampilkan pertanyaan pelanggan yang belum ada jawabannya — tambahkan ke KB agar AI makin akurat. Tab <b>Daftar Harga</b> untuk harga produk/layanan.</p>' },
    content: { tab: 'content', el: '#panel-content .card', title: 'Balasan &amp; Tampilan',
      body: '<p>Mulai dari <b>Konfigurasi Terstruktur</b>: sapaan, bahasa, aturan respon, dan apa yang dilakukan AI saat tidak tahu jawabannya.</p><p>Di bawahnya: teks balasan bawaan dan tampilan widget (warna, posisi) di website.</p>' },
    test: { tab: 'test', el: '#panel-test .card', title: 'Tes Chatbot',
      body: '<p>Bertanya seperti pelanggan untuk memeriksa jawaban AI — lakukan setiap selesai mengubah Knowledge Base.</p>' },
    widget: { tab: 'widget', el: tourCard('widget', 'Status Widget'), title: 'Widget &amp; API',
      body: '<p>Nyalakan / matikan <b>bubble AI</b> dan <b>tombol WhatsApp</b> di website.</p><p>Di halaman ini juga: <b>Form Data Pengunjung</b> (minta nama &amp; nomor sebelum chat) dan pengaturan nomor WhatsApp.</p>' },
    eskalasi: { tab: 'eskalasi', el: tourCard('eskalasi', 'Auto-Closing'), title: 'Respon &amp; Eskalasi',
      body: '<p><b>Auto-Closing</b> mengirim pesan penutup ke tamu yang sudah diam.</p><p><b>Eskalasi Darurat</b> membunyikan alarm ke Supervisor/Manager bila tamu menunggu terlalu lama tanpa balasan.</p>' },
    install: { tab: 'install', el: tourCard('install', 'Langkah Pemasangan'), title: 'Pemasangan widget',
      body: '<p>Salin kode untuk <b>Google Tag Manager</b>, atau pasang langsung di HTML website. Cukup sekali — perubahan setelahnya otomatis ikut.</p>' },
    pembaruan: { tab: 'pembaruan', el: '#panel-pembaruan .rel-hero', title: 'Pembaruan',
      body: '<p>Catatan rilis fitur baru dan perbaikan. Saat ada versi baru, tanda muncul di menu ini dan Anda bisa memasangnya dari sini.</p>' },
    notif: { el: '#btnNotif', side: true, optional: true, title: 'Aktifkan notifikasi',
      body: '<p>Klik sekali dan izinkan notifikasi: browser / HP akan memberi tahu setiap ada pesan baru, walau dashboard tidak sedang dibuka.</p><p>Di HP, pasang dashboard ke layar utama (Add to Home Screen) agar notifikasi lebih andal.</p>' },
    profile: { tab: 'profile', el: tourCard('profile', 'Ganti Password'), title: 'Profil &amp; password',
      body: '<p>Ganti password Anda di sini. Setelah tersimpan, Anda diminta login ulang.</p>' },
    done: { el: '#btnTour', side: true, title: 'Selesai — siap bekerja!',
      body: '<p>Panduan ini bisa dibuka lagi kapan saja lewat tombol <b>Panduan</b> di bawah menu, atau dari <b>Profil Saya</b>.</p>' }
  };

  function tourSteps(r) {
    var W = { el: null, welcome: true };
    if (r === 'wa_agent') return [
      tourWelcome(W, '<p>Peran <b>WA Agent</b>: membalas chat pelanggan yang diteruskan dari bot, dan menindaklanjuti leads.</p><p>Panduan ini sekitar 1 menit.</p>'),
      TS.nav('<p>Menu hanya berisi halaman yang bisa Anda pakai.</p><p>Di HP, buka menu lewat tombol <b>&#9776;</b> di pojok kiri atas.</p>'),
      TS.waList('<p>Chat WhatsApp masuk tampil di sini secara real-time, yang terbaru di atas. Klik satu chat untuk membukanya.</p>'),
      TS.waThread('Claim, balas, lalu Release', '<ul><li>Klik <b>Claim</b> — bot berhenti menjawab nomor itu dan chat menjadi milik Anda.</li><li>Ketik balasan di kolom bawah, lalu <b>Kirim</b>.</li><li>Selesai? Klik <b>Release</b> / <b>Lepas ke antrean</b>.</li></ul><p>Aturan WhatsApp: balasan teks bebas hanya bisa dikirim dalam <b>24 jam</b> sejak pesan terakhir pelanggan.</p>'),
      TS.webchat,
      TS.leads(),
      TS.kontak(),
      TS.agentReport('Kinerja Anda', '<p>Jumlah chat yang Anda tangani dan rata-rata <b>waktu respon</b>. Waktu dihitung sejak pelanggan menunggu sampai Anda membalas — balas secepatnya.</p>'),
      TS.notif,
      TS.profile,
      TS.done
    ];
    if (r === 'supervisor') return [
      tourWelcome(W, '<p>Peran <b>Supervisor</b>: memantau tim agent, membagi chat, dan menjaga waktu respon.</p><p>Panduan ini sekitar 2 menit.</p>'),
      TS.nav('<p>Menu hanya berisi halaman yang bisa Anda pakai.</p><p>Di HP, buka menu lewat tombol <b>&#9776;</b> di pojok kiri atas.</p>'),
      TS.waList('<p>Anda melihat chat milik tim Anda secara real-time. Klik satu chat untuk membukanya.</p>'),
      TS.waThread('Bagi chat ke agent', '<ul><li><b>Serahkan ke…</b> / <b>Pindahkan ke…</b> di kepala chat — bagi chat ke agent yang tepat.</li><li>Atau <b>Claim</b> dan balas sendiri.</li></ul><p>Balasan teks bebas hanya bisa dikirim dalam <b>24 jam</b> sejak pesan terakhir pelanggan.</p>'),
      TS.webchat,
      TS.reports,
      TS.blast,
      TS.leads(),
      TS.kontak(' Tombol <b>Ekspor CSV</b> mengunduh kontak sesuai filter aktif.'),
      TS.agentReport('Pantau kinerja tim', '<p>Pilih rentang tanggal lalu <b>Tampilkan</b>: chat ditangani, balasan, respon pertama, dan chat yang <b>belum dibalas</b> per agent.</p><p>Kartu <b>Kursi Tim</b> di atasnya menunjukkan sisa akun sesuai paket.</p>'),
      TS.users('<p>Buat akun <b>WA Agent</b> untuk tim Anda: isi username, nama, password, lalu simpan.</p><p>Jumlah akun dibatasi kursi paket.</p>'),
      TS.notif,
      TS.done
    ];
    var sa = r === 'super_admin';
    var steps = [
      tourWelcome(W, sa
        ? '<p>Peran <b>Super Admin</b>: akses penuh — konfigurasi AI &amp; WhatsApp, isi jawaban bot, tim, dan semua pengguna.</p><p>Panduan ini sekitar 3 menit. Urutannya mengikuti langkah menyiapkan chatbot.</p>'
        : '<p>Peran <b>Admin</b>: mengatur isi jawaban bot, tampilan widget, tim, dan laporan.</p><p>Panduan ini sekitar 3 menit. Urutannya mengikuti langkah menyiapkan chatbot.</p>'),
      TS.nav('<p>Semua halaman yang bisa Anda kelola ada di sini. <b>Leads</b>, <b>Kontak</b>, dan <b>Blast WA</b> dipakai bersama tim untuk tindak lanjut pelanggan.</p><p>Di HP, buka menu lewat tombol <b>&#9776;</b> di pojok kiri atas.</p>'),
      TS.usage,
      TS.reports,
      TS.kb,
      TS.content,
      TS.test,
      TS.widget
    ];
    if (sa) steps.push(
      { tab: 'widget', el: tourCard('widget', 'Konfigurasi API AI'), title: 'Konfigurasi API AI',
        body: '<p>Pilih provider AI (Anthropic / OpenRouter), API key, dan model. Kartu rahasia seperti ini hanya terlihat oleh Super Admin.</p>' },
      { tab: 'widget', el: tourCard('widget', 'WhatsApp Bot'), title: 'WhatsApp Bot',
        body: '<p>Hubungkan nomor WhatsApp Business (Meta Cloud API) agar bot menjawab chat WhatsApp. Di bawahnya ada <b>Notifikasi Telegram</b> dan <b>Handoff Otomatis</b>.</p>' }
    );
    steps.push(TS.install, TS.eskalasi);
    steps.push(TS.waList('<p>Anda melihat <b>semua</b> chat. Buka chat untuk <b>Claim</b> dan membalas sendiri, atau <b>Serahkan ke</b> agent.</p>'));
    if (sa) steps.push({ tab: 'tim', el: '#timModeCard', title: 'Mode balasan WhatsApp',
      body: '<p><b>AI + Agent</b>: bot menjawab otomatis, agent mengambil alih lewat Claim.<br><b>Manual</b>: semua chat dibalas agent.</p><p>Di sini juga: agent hanya melihat chat miliknya atau tidak.</p>' });
    steps.push(
      TS.agentReport('Kinerja tim', '<p>Chat ditangani, balasan, respon pertama, dan chat yang belum dibalas — per agent, untuk rentang tanggal pilihan Anda.</p>'),
      TS.users(sa
        ? '<p>Buat akun untuk semua peran: <b>Admin</b>, <b>Supervisor</b>, dan <b>WA Agent</b>. Jumlah Supervisor &amp; Agent dibatasi kursi paket.</p>'
        : '<p>Buat akun <b>Supervisor</b> dan <b>WA Agent</b>. Akun Admin hanya bisa dibuat oleh Super Admin. Jumlah akun dibatasi kursi paket.</p>'),
      TS.pembaruan,
      TS.notif,
      TS.done
    );
    return steps;
  }
  function tourWelcome(base, body) {
    var s = {}; for (var k in base) s[k] = base[k];
    s.body = body;
    return s;
  }

  function tourTabAllowed(tab) {
    var b = document.querySelector('#nav button[data-tab="' + tab + '"]');
    return !!b && can(b.dataset.role);
  }
  function tourTarget(st) {
    if (!st.el) return null;
    var n = typeof st.el === 'function' ? st.el() : document.querySelector(st.el);
    if (!n || !n.getClientRects().length || n.closest('.hide')) return null;
    return n;
  }
  function tourIsMobile() { return window.innerWidth <= 860; }

  function tourEls() {
    var r = document.getElementById('tourRoot');
    if (r) return r;
    r = document.createElement('div');
    r.id = 'tourRoot';
    r.innerHTML = '<div class="tour-block"></div><div class="tour-hole"></div>' +
      '<div class="tour-pop" role="dialog" aria-modal="true" aria-labelledby="tourTitle">' +
        '<button type="button" class="tour-x" data-t="close" title="Tutup panduan (Esc)">' + ico('x', 16) + '</button>' +
        '<div class="tour-step" id="tourStepNo"></div><div id="tourPrev"></div>' +
        '<h4 id="tourTitle"></h4><div class="tour-body" id="tourBody"></div>' +
        '<div class="tour-prog"><i id="tourProg"></i></div>' +
        '<div class="tour-foot"><span class="tour-hint">&larr; &rarr; untuk berpindah</span><div class="tour-btns" id="tourBtnsBar"></div></div>' +
      '</div>';
    document.body.appendChild(r);
    // stopPropagation: handler "klik di luar sidebar" di document tidak boleh menutup menu saat tur
    r.addEventListener('click', function (e) {
      e.stopPropagation();
      var b = e.target.closest('[data-t]');
      if (!b || !tour) return;
      var t = b.dataset.t;
      if (t === 'next') tourGo(tour.i + 1);
      else if (t === 'back') tourGo(tour.i - 1);
      else if (t === 'finish') tourEnd(true);
      else tourEnd(false);
    });
    return r;
  }

  function tourGo(i) {
    if (!tour) return;
    var steps = tour.steps;
    // lewati langkah opsional yang targetnya tidak tampil (mis. tombol notifikasi di browser tanpa push)
    var dir = i < tour.i ? -1 : 1;
    i = Math.max(0, Math.min(steps.length - 1, i));
    while (steps[i] && steps[i].optional && i > 0 && i < steps.length - 1) {
      if (steps[i].tab) showTab(steps[i].tab);
      if (tourTarget(steps[i])) break;
      i += dir;
    }
    tour.i = i;
    var st = steps[i];
    if (st.tab) showTab(st.tab);
    if (tourIsMobile()) toggleSide(!!st.side);
    var node = tourTarget(st);
    if (node) {
      var tall = node.getBoundingClientRect().height > window.innerHeight * 0.6;
      try { node.scrollIntoView({ block: tall ? 'start' : 'center', behavior: 'auto' }); } catch (e) { node.scrollIntoView(); }
    } else if (st.tab) {
      window.scrollTo(0, 0);
    }
    tourText();
    tourPaint();
    clearTimeout(tour.t); clearTimeout(tour.t2);
    tour.t = setTimeout(tourPaint, 320);    // tunggu animasi panel (fade) / sidebar HP
    tour.t2 = setTimeout(tourPaint, 700);
  }

  function tourText() {
    var st = tour.steps[tour.i], n = tour.steps.length, last = tour.i === n - 1;
    var who = ROLE_LABEL[tour.role] || tour.role;
    $('#tourStepNo').textContent = st.welcome ? ('Panduan ' + who) : ('Langkah ' + tour.i + ' dari ' + (n - 1));
    $('#tourPrev').innerHTML = tour.preview ? '<span class="tour-prev">Pratinjau — tampilan untuk akun ' + esc(who) + '</span>' : '';
    $('#tourTitle').innerHTML = st.welcome
      ? (tour.preview ? 'Panduan untuk ' + esc(who) : 'Selamat datang, ' + esc(user.name || user.username) + '!')
      : st.title;
    $('#tourBody').innerHTML = st.body;
    $('#tourProg').style.width = Math.round(tour.i / (n - 1) * 100) + '%';
    $('#tourBtnsBar').innerHTML = st.welcome
      ? '<button type="button" class="btn ghost sm" data-t="close">Nanti saja</button><button type="button" class="btn sm" data-t="next">Mulai panduan</button>'
      : '<button type="button" class="btn ghost sm" data-t="back">Kembali</button>' +
        (last ? '<button type="button" class="btn sm" data-t="finish">Selesai</button>'
              : '<button type="button" class="btn sm" data-t="next">Lanjut</button>');
    var f = document.querySelector('#tourBtnsBar .btn:last-child');
    if (f) try { f.focus({ preventScroll: true }); } catch (e) {}
  }

  function tourPaint() {
    if (!tour) return;
    var root = tourEls(), st = tour.steps[tour.i];
    var hole = root.querySelector('.tour-hole'), pop = root.querySelector('.tour-pop');
    var vw = window.innerWidth, vh = window.innerHeight, pad = 6, gap = 12, m = 12;
    var node = tourTarget(st), x, y, x2, y2;
    if (node) {
      var r = node.getBoundingClientRect();
      x = Math.max(4, r.left - pad); y = Math.max(4, r.top - pad);
      x2 = Math.min(vw - 4, r.right + pad); y2 = Math.min(vh - 4, r.bottom + pad);
      if (x2 - x < 10 || y2 - y < 10) node = null;   // di luar layar
    }
    if (node) {
      root.classList.remove('center');
      hole.style.left = x + 'px'; hole.style.top = y + 'px';
      hole.style.width = (x2 - x) + 'px'; hole.style.height = (y2 - y) + 'px';
    } else {
      root.classList.add('center');
      hole.style.left = (vw / 2) + 'px'; hole.style.top = (vh / 2) + 'px';
      hole.style.width = '0px'; hole.style.height = '0px';
    }
    var pw = Math.min(380, vw - 2 * m);
    pop.style.width = pw + 'px';
    var ph = pop.offsetHeight, L, T;
    var clampL = function (v) { return Math.max(m, Math.min(vw - pw - m, v)); };
    var clampT = function (v) { return Math.max(m, Math.min(vh - ph - m, v)); };
    if (!node)                              { L = (vw - pw) / 2; T = clampT((vh - ph) / 2); }
    else if (vw - x2 >= pw + gap + m)       { L = x2 + gap; T = clampT(y); }          // kanan (menu samping)
    else if (vh - y2 >= ph + gap + m)       { L = clampL(x); T = y2 + gap; }          // bawah
    else if (y >= ph + gap + m)             { L = clampL(x); T = y - gap - ph; }      // atas
    else if (x >= pw + gap + m)             { L = x - gap - pw; T = clampT(y); }      // kiri
    else                                    { L = (vw - pw) / 2; T = vh - ph - m; }   // menimpa bawah layar
    pop.style.left = Math.round(L) + 'px';
    pop.style.top = Math.round(T) + 'px';
  }
  var tourRaf = 0;
  function tourRepaint() { if (!tour || tourRaf) return; tourRaf = requestAnimationFrame(function () { tourRaf = 0; tourPaint(); }); }
  window.addEventListener('resize', tourRepaint);
  window.addEventListener('scroll', tourRepaint, true);
  document.addEventListener('keydown', function (e) {
    if (!tour) return;
    if (e.key === 'Escape') { e.preventDefault(); tourEnd(false); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); if (tour.i < tour.steps.length - 1) tourGo(tour.i + 1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); if (tour.i > 0) tourGo(tour.i - 1); }
  });

  function tourStart(r, preview) {
    if (tour) tourEnd(true, true);
    var steps = tourSteps(r).filter(function (s) { return !s.tab || tourTabAllowed(s.tab); });
    var act = document.querySelector('#nav button.active');
    tour = { role: r, steps: steps, i: 0, preview: !!preview, home: act ? act.dataset.tab : firstTab, t: 0 };
    document.body.classList.add('tour-on');
    tourEls();
    tourGo(0);
  }
  function tourEnd(finished, silent) {
    if (!tour) return;
    var t = tour; tour = null;
    clearTimeout(t.t); clearTimeout(t.t2);
    var root = document.getElementById('tourRoot');
    if (root) root.parentNode.removeChild(root);
    document.body.classList.remove('tour-on');
    if (silent) return;
    if (tourIsMobile()) toggleSide(false);
    if (!t.preview) tourMarkSeen();
    showTab(t.home);
    window.scrollTo(0, 0);
    if (!finished) toast('Panduan bisa dibuka lagi lewat tombol "Panduan" di bawah menu.');
  }

  function tourLsKey() { return 'dei_tour_' + (user.username || ''); }
  function tourSeen() {
    if ((+user.tour_seen || 0) >= TOUR_VER) return true;
    try { return (+localStorage.getItem(tourLsKey()) || 0) >= TOUR_VER; } catch (e) { return false; }
  }
  function tourMarkSeen() {
    user.tour_seen = TOUR_VER;
    try { localStorage.setItem(tourLsKey(), String(TOUR_VER)); localStorage.setItem('dei_user', JSON.stringify(user)); } catch (e) {}
    api('tour_seen', { method: 'POST', body: { ver: TOUR_VER } }).catch(function () {});
  }

  function tourInit() {
    if ($('#btnTour')) $('#btnTour').onclick = function (e) { e.stopPropagation(); tourStart(role, false); };
    var box = $('#tourBtns');
    if (box) {
      var me = TOUR_ORDER.indexOf(role);
      var lower = me >= 0 ? TOUR_ORDER.slice(me + 1) : [];
      box.innerHTML = '<button type="button" class="btn sm" data-tour-role="' + role + '">' + ico('circle-help', 15) + ' Mulai panduan ' + esc(ROLE_LABEL[role] || role) + '</button>' +
        lower.map(function (r) { return '<button type="button" class="btn ghost sm" data-tour-role="' + r + '" data-tour-preview="1">Lihat panduan ' + esc(ROLE_LABEL[r]) + '</button>'; }).join('');
      if (lower.length && $('#tourCardNote')) $('#tourCardNote').innerHTML = 'Tur singkat menu &amp; fitur sesuai peran Anda. Untuk melatih tim, lihat juga pratinjau panduan yang ditampilkan ke peran lain saat pertama login.';
      $$('#tourBtns [data-tour-role]').forEach(function (b) {
        b.onclick = function () { tourStart(b.dataset.tourRole, !!b.dataset.tourPreview); };
      });
    }
    // otomatis sekali untuk akun yang belum pernah melihat versi panduan ini
    if (!tourSeen() && location.hash !== '#pembaruan') {
      setTimeout(function () { if (!tour) tourStart(role, false); }, 700);
    }
  }
