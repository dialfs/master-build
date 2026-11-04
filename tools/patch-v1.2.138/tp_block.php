/* ======================================================================
 * v1.2.138: filter-topik — klasifikasi topik & divisi percakapan WA oleh AI
 *  - Taksonomi per tenant (data/topics-conf.json): divisi + topik (tiap topik -> 1 divisi), preset per industri.
 *  - AI (Claude Haiku 5.5 lewat server pusat, key pusat DEI) membaca 20 bubble terakhir -> topik (multi-label) + topik utama.
 *  - Pemicu (cron_tick): chat diam 3 menit | tiap 5 pesan pelanggan baru | ditandai Selesai. Backfill 7 hari saat diaktifkan.
 *  - Label disimpan di kontak: tp {m, t[], d, at, by, lk, cf} + tp_h (riwayat "pernah tanya"). Koreksi manual = dikunci dari AI.
 *  - Paket: mulai Growth (bukan trial). Kuota klasifikasi/bulan dari pusat (Growth 5.000, Business 15.000, Pro 30.000).
 * ==================================================================== */
define('TP_CONF_FILE', DATA_DIR . '/topics-conf.json');
define('TP_USAGE_FILE', DATA_DIR . '/classify-usage.json');
define('TP_BACKFILL_FILE', DATA_DIR . '/tp-backfill.json');
if (!defined('TP_TIERS')) define('TP_TIERS', 'growth,business,pro,custom,enterprise');
if (!defined('TP_IDLE_SEC')) define('TP_IDLE_SEC', 180);        // chat diam 3 menit
if (!defined('TP_EVERY_N')) define('TP_EVERY_N', 5);            // tiap 5 pesan pelanggan baru
if (!defined('TP_PER_TICK')) define('TP_PER_TICK', 10);         // maks klasifikasi per cron tick
if (!defined('TP_BUBBLES')) define('TP_BUBBLES', 20);
if (!defined('TP_MODEL')) define('TP_MODEL', 'anthropic/claude-haiku-5.5');
if (!defined('TP_MAX_TOPICS')) define('TP_MAX_TOPICS', 40);
if (!defined('TP_MAX_DIVS')) define('TP_MAX_DIVS', 12);

function tpSlug($s) {
    $s = strtolower(trim(preg_replace('/[^A-Za-z0-9]+/', '_', iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', (string)$s) ?: (string)$s), '_'));
    return substr($s !== '' ? $s : 'x', 0, 32);
}
function tpPresets() {
    $P = function ($name, $divs, $topics) {
        $d = []; foreach ($divs as $x) $d[] = ['id' => $x[0], 'name' => $x[1]];
        $t = []; foreach ($topics as $x) $t[] = ['id' => $x[0], 'name' => $x[1], 'desc' => $x[2], 'div' => $x[3]];
        return ['name' => $name, 'divisions' => $d, 'topics' => $t];
    };
    return [
        'hotel' => $P('Hotel',
            [['reservasi', 'Reservasi & Sales'], ['fo', 'Front Office'], ['hk', 'Housekeeping & Operasional'], ['fnb', 'F&B / Event'], ['cs', 'Customer Service']],
            [['harga_kamar', 'Tanya harga & ketersediaan kamar', 'tarif, tipe kamar, kamar kosong di tanggal tertentu', 'reservasi'],
             ['booking', 'Booking kamar', 'mau pesan/reservasi kamar, kirim data tamu, pembayaran booking', 'reservasi'],
             ['ubah_batal', 'Ubah / batal booking', 'reschedule, ganti tanggal, pembatalan, refund', 'reservasi'],
             ['checkin', 'Check-in / check-out', 'jam check-in/out, early check-in, late check-out, deposit', 'fo'],
             ['fasilitas', 'Fasilitas hotel', 'kolam, parkir, sarapan, wifi, gym, antar-jemput', 'fo'],
             ['permintaan', 'Permintaan selama menginap', 'handuk, bersih kamar, extra bed, AC/TV rusak', 'hk'],
             ['event', 'Meeting, event & wedding', 'paket meeting, ruang acara, pernikahan, gathering', 'fnb'],
             ['resto', 'Restoran & makanan', 'menu, room service, jam restoran', 'fnb'],
             ['lokasi', 'Lokasi & akses', 'alamat, rute, jarak ke tempat tertentu', 'cs'],
             ['komplain', 'Komplain', 'keluhan layanan, kamar, staf, tagihan', 'cs']]),
        'dealer' => $P('Dealer Otomotif',
            [['sales', 'Sales'], ['finance', 'Finance & Leasing'], ['service', 'Service / Bengkel'], ['part', 'Sparepart'], ['admin', 'Admin STNK/BPKB'], ['cs', 'Customer Service']],
            [['harga', 'Tanya harga & promo', 'harga OTR, diskon, promo, cashback', 'sales'],
             ['cicilan', 'Tanya cicilan / kredit', 'DP, angsuran, tenor, simulasi kredit, leasing, syarat kredit', 'finance'],
             ['stok', 'Stok, tipe & warna', 'ketersediaan unit, varian, warna, inden', 'sales'],
             ['test_drive', 'Test drive & kunjungan', 'jadwal test drive, datang ke dealer, alamat showroom', 'sales'],
             ['tukar_tambah', 'Tukar tambah', 'trade-in kendaraan lama, taksiran harga', 'sales'],
             ['stnk', 'STNK, BPKB & plat', 'pengurusan surat, STNK/BPKB jadi kapan, plat nomor, balik nama', 'admin'],
             ['servis', 'Booking servis', 'jadwal servis berkala, perbaikan, biaya servis', 'service'],
             ['sparepart', 'Sparepart & aksesoris', 'harga/stok suku cadang, aksesoris, oli', 'part'],
             ['garansi', 'Garansi & klaim', 'masa garansi, klaim garansi, recall', 'service'],
             ['komplain', 'Komplain', 'keluhan unit, pelayanan, keterlambatan', 'cs']]),
        'pobus' => $P('PO Bus',
            [['tiket', 'Tiket & Reservasi'], ['ops', 'Operasional'], ['pariwisata', 'Sewa / Pariwisata'], ['cargo', 'Paket / Cargo'], ['cs', 'Customer Service']],
            [['jadwal', 'Jadwal & rute', 'jam berangkat, rute, agen/titik naik, trayek', 'tiket'],
             ['harga_tiket', 'Harga tiket', 'tarif per kelas/rute, promo tiket', 'tiket'],
             ['pesan_tiket', 'Pesan tiket', 'booking kursi, cara bayar, kirim e-tiket', 'tiket'],
             ['ubah_batal', 'Ubah / batal / refund', 'reschedule, pembatalan, refund tiket', 'tiket'],
             ['posisi_bus', 'Posisi bus & keberangkatan', 'bus sudah sampai mana, terlambat, nomor bus/kru', 'ops'],
             ['fasilitas', 'Fasilitas armada', 'kelas, toilet, makan, bagasi, colokan', 'ops'],
             ['sewa', 'Sewa bus pariwisata', 'carter bus, harga sewa, kapasitas', 'pariwisata'],
             ['paket', 'Kirim paket', 'ongkos kirim paket/barang, cara kirim, lacak paket', 'cargo'],
             ['tertinggal', 'Barang tertinggal', 'barang ketinggalan di bus', 'cs'],
             ['komplain', 'Komplain', 'keluhan kru, sopir, armada, keterlambatan', 'cs']]),
        'travel' => $P('Travel',
            [['sales', 'Sales'], ['tour', 'Operasional Tour'], ['ticketing', 'Ticketing'], ['dokumen', 'Visa & Dokumen'], ['cs', 'Customer Service']],
            [['paket_tour', 'Paket tour & harga', 'paket wisata, itinerary, harga per orang', 'sales'],
             ['umrah', 'Umrah & haji', 'paket umrah/haji, jadwal keberangkatan, manasik', 'sales'],
             ['tiket_pesawat', 'Tiket pesawat', 'harga & pemesanan tiket pesawat/kereta', 'ticketing'],
             ['hotel', 'Pesan hotel', 'booking hotel/akomodasi', 'ticketing'],
             ['visa', 'Visa & paspor', 'syarat visa, pengurusan paspor, dokumen', 'dokumen'],
             ['jadwal', 'Jadwal keberangkatan', 'tanggal berangkat, kuota seat, kumpul', 'tour'],
             ['bayar', 'Pembayaran & cicilan', 'DP, pelunasan, cicilan, transfer', 'sales'],
             ['ubah_batal', 'Ubah / batal / refund', 'reschedule, pembatalan, refund', 'cs'],
             ['komplain', 'Komplain', 'keluhan perjalanan, pemandu, hotel', 'cs']]),
        'klinik' => $P('Klinik',
            [['admin', 'Pendaftaran / Admin'], ['medis', 'Layanan Medis'], ['farmasi', 'Farmasi'], ['kasir', 'Kasir & Asuransi'], ['cs', 'Customer Service']],
            [['jadwal_dokter', 'Jadwal dokter', 'dokter praktik kapan, dokter spesialis', 'admin'],
             ['daftar', 'Daftar / booking janji', 'reservasi antrean, daftar pasien baru', 'admin'],
             ['biaya', 'Biaya & tarif', 'harga konsultasi/tindakan/paket', 'kasir'],
             ['asuransi', 'BPJS & asuransi', 'terima BPJS/asuransi, klaim, rujukan', 'kasir'],
             ['layanan', 'Layanan & tindakan', 'jenis layanan, vaksin, cek kesehatan, perawatan', 'medis'],
             ['hasil_lab', 'Hasil lab & pemeriksaan', 'hasil lab, surat keterangan, rekam medis', 'medis'],
             ['obat', 'Obat & resep', 'ketersediaan obat, tebus resep', 'farmasi'],
             ['lokasi', 'Lokasi & jam buka', 'alamat, jam operasional, parkir', 'cs'],
             ['komplain', 'Komplain', 'keluhan pelayanan, antrean, tagihan', 'cs']]),
        'restoran' => $P('Restoran',
            [['reservasi', 'Reservasi'], ['order', 'Order & Delivery'], ['event', 'Event & Catering'], ['cs', 'Customer Service']],
            [['reservasi_meja', 'Reservasi meja', 'booking tempat, jumlah orang, private room', 'reservasi'],
             ['menu', 'Menu & harga', 'daftar menu, harga, menu halal/vegetarian', 'order'],
             ['delivery', 'Pesan antar / takeaway', 'order delivery, ojol, ongkir, takeaway', 'order'],
             ['catering', 'Catering & event', 'paket catering, ulang tahun, acara kantor', 'event'],
             ['promo', 'Promo', 'diskon, paket hemat, voucher', 'order'],
             ['lokasi', 'Jam buka & lokasi', 'alamat, jam operasional, parkir', 'cs'],
             ['bayar', 'Pembayaran', 'metode bayar, QRIS, split bill, invoice', 'order'],
             ['komplain', 'Komplain', 'keluhan makanan, pelayanan, pesanan', 'cs']]),
        'properti' => $P('Sales Properti',
            [['marketing', 'Marketing / Sales'], ['kpr', 'KPR & Keuangan'], ['legal', 'Legal & Dokumen'], ['estate', 'Serah Terima / Estate'], ['cs', 'Customer Service']],
            [['harga_unit', 'Harga & tipe unit', 'harga, tipe, luas, denah, ketersediaan unit', 'marketing'],
             ['lokasi', 'Lokasi & akses', 'alamat proyek, akses tol/stasiun, fasilitas sekitar', 'marketing'],
             ['kpr', 'Cicilan, KPR & DP', 'simulasi KPR, DP, cicilan, syarat bank', 'kpr'],
             ['promo', 'Promo', 'diskon, subsidi, free biaya', 'marketing'],
             ['survei', 'Jadwal survei / kunjungan', 'datang ke lokasi, show unit, marketing gallery', 'marketing'],
             ['legal', 'Legalitas & sertifikat', 'SHM/HGB, IMB/PBG, AJB, PPJB', 'legal'],
             ['progres', 'Progres pembangunan', 'kapan jadi, progres proyek', 'estate'],
             ['serah_terima', 'Serah terima & komplain bangunan', 'kunci, retensi, kerusakan bangunan', 'estate'],
             ['komplain', 'Komplain', 'keluhan pelayanan atau pembayaran', 'cs']]),
        'rental' => $P('Rental Mobil',
            [['reservasi', 'Reservasi & Sales'], ['armada', 'Operasional Armada'], ['keuangan', 'Keuangan'], ['cs', 'Customer Service']],
            [['harga_sewa', 'Harga sewa', 'tarif harian/mingguan/bulanan per unit', 'reservasi'],
             ['unit', 'Ketersediaan unit', 'unit kosong di tanggal tertentu, jenis mobil', 'reservasi'],
             ['sopir', 'Dengan sopir / lepas kunci', 'pilihan sopir, biaya sopir, BBM, tol', 'reservasi'],
             ['syarat', 'Syarat & dokumen', 'KTP, SIM, jaminan, survei', 'reservasi'],
             ['booking', 'Booking', 'pesan unit, konfirmasi, kontrak', 'reservasi'],
             ['antar_jemput', 'Antar-jemput unit', 'unit diantar ke lokasi/bandara', 'armada'],
             ['perpanjang', 'Perpanjang / batal', 'tambah hari, pembatalan', 'reservasi'],
             ['deposit', 'Deposit & pembayaran', 'DP, deposit, pengembalian deposit, transfer', 'keuangan'],
             ['kendala', 'Kerusakan / kendala unit', 'mogok, ban, kecelakaan, servis darurat', 'armada'],
             ['komplain', 'Komplain', 'keluhan unit atau pelayanan', 'cs']]),
        'saas' => $P('Software House / SaaS',
            [['sales', 'Sales'], ['support', 'Support Teknis'], ['billing', 'Billing'], ['implementasi', 'Onboarding / Implementasi'], ['cs', 'Customer Service']],
            [['harga', 'Harga & paket', 'harga langganan, paket, perbandingan paket', 'sales'],
             ['demo', 'Demo & trial', 'minta demo, coba gratis, presentasi', 'sales'],
             ['fitur', 'Fitur & integrasi', 'bisa apa saja, integrasi API/aplikasi lain', 'sales'],
             ['custom', 'Custom development', 'buat aplikasi/website custom, estimasi biaya proyek', 'sales'],
             ['bug', 'Bug / error', 'aplikasi error, tidak bisa dipakai, lambat', 'support'],
             ['akun', 'Akun & login', 'lupa password, tidak bisa login, tambah user', 'support'],
             ['onboarding', 'Onboarding & pelatihan', 'cara pakai, setup awal, training', 'implementasi'],
             ['tagihan', 'Tagihan & pembayaran', 'invoice, faktur pajak, metode bayar', 'billing'],
             ['upgrade', 'Perpanjangan / upgrade', 'perpanjang langganan, naik paket, berhenti', 'billing'],
             ['komplain', 'Komplain', 'keluhan layanan atau respons support', 'cs']]),
        'marketplace' => $P('Seller Marketplace',
            [['sales', 'Sales'], ['logistik', 'Pengiriman'], ['cs', 'CS & Retur'], ['admin', 'Admin']],
            [['stok', 'Stok & varian', 'ready stok, ukuran, warna, varian', 'sales'],
             ['harga', 'Harga & promo', 'harga, nego, voucher, flash sale', 'sales'],
             ['cara_order', 'Cara order', 'cara beli, checkout di marketplace, custom order', 'sales'],
             ['resi', 'Status pengiriman & resi', 'kapan dikirim, nomor resi, paket belum sampai', 'logistik'],
             ['retur', 'Retur & tukar', 'barang salah/rusak, tukar ukuran, refund', 'cs'],
             ['garansi', 'Garansi', 'klaim garansi, servis produk', 'cs'],
             ['grosir', 'Reseller & grosir', 'harga grosir, jadi reseller/dropship', 'sales'],
             ['komplain', 'Komplain produk', 'kualitas produk, tidak sesuai foto', 'cs']]),
        'tokoonline' => $P('Toko Online',
            [['sales', 'Sales'], ['gudang', 'Gudang & Pengiriman'], ['keuangan', 'Keuangan'], ['cs', 'Customer Service']],
            [['stok', 'Stok, ukuran & varian', 'ready stok, size chart, warna', 'sales'],
             ['harga', 'Harga & diskon', 'harga, promo, kode voucher', 'sales'],
             ['cara_pesan', 'Cara pesan & checkout', 'cara order, format order, checkout website', 'sales'],
             ['bayar', 'Pembayaran & konfirmasi', 'rekening, transfer, konfirmasi bayar, COD', 'keuangan'],
             ['ongkir', 'Ongkir & pengiriman', 'biaya kirim, kurir, estimasi sampai', 'gudang'],
             ['lacak', 'Lacak pesanan', 'status pesanan, resi, belum diterima', 'gudang'],
             ['retur', 'Retur, tukar & refund', 'barang rusak/salah, tukar ukuran, uang kembali', 'cs'],
             ['reseller', 'Reseller & dropship', 'daftar reseller, harga agen, dropship', 'sales'],
             ['komplain', 'Komplain', 'keluhan produk atau pelayanan', 'cs']]),
    ];
}
function tpConfClean($in) {
    $in = is_array($in) ? $in : [];
    $divs = []; $seenD = [];
    foreach ((array)($in['divisions'] ?? []) as $d) {
        if (!is_array($d)) continue;
        $name = mb_substr(trim(preg_replace('/\s+/u', ' ', (string)($d['name'] ?? ''))), 0, 40);
        if ($name === '') continue;
        $id = tpSlug(($d['id'] ?? '') !== '' ? $d['id'] : $name);
        $b = $id; $i = 2; while (isset($seenD[$id])) $id = substr($b, 0, 29) . '_' . $i++;
        $seenD[$id] = true; $divs[] = ['id' => $id, 'name' => $name];
        if (count($divs) >= TP_MAX_DIVS) break;
    }
    $tops = []; $seenT = [];
    foreach ((array)($in['topics'] ?? []) as $t) {
        if (!is_array($t)) continue;
        $name = mb_substr(trim(preg_replace('/\s+/u', ' ', (string)($t['name'] ?? ''))), 0, 50);
        if ($name === '') continue;
        $id = tpSlug(($t['id'] ?? '') !== '' ? $t['id'] : $name);
        $b = $id; $i = 2; while (isset($seenT[$id])) $id = substr($b, 0, 29) . '_' . $i++;
        $seenT[$id] = true;
        $div = tpSlug((string)($t['div'] ?? ''));
        if (!isset($seenD[$div])) $div = '';
        $tops[] = ['id' => $id, 'name' => $name, 'desc' => mb_substr(trim(preg_replace('/\s+/u', ' ', (string)($t['desc'] ?? ''))), 0, 160), 'div' => $div];
        if (count($tops) >= TP_MAX_TOPICS) break;
    }
    $preset = (string)($in['preset'] ?? '');
    return ['enabled' => !empty($in['enabled']), 'preset' => isset(tpPresets()[$preset]) ? $preset : '',
            'divisions' => $divs, 'topics' => $tops,
            'updated_at' => (string)($in['updated_at'] ?? ''), 'by' => (string)($in['by'] ?? '')];
}
function tpConf() {
    if (isset($GLOBALS['dei_tp_conf'])) return $GLOBALS['dei_tp_conf'];
    return $GLOBALS['dei_tp_conf'] = tpConfClean(readJson(TP_CONF_FILE, []));
}
// Paket: tanpa server pusat (instalasi sendiri) = boleh. Trial & Starter = belum.
function tpPlan() {
    if (isset($GLOBALS['dei_tp_plan'])) return $GLOBALS['dei_tp_plan'];
    $s = getSettings();
    $cs = $s['central_server'] ?? [];
    if (empty($cs['url']) || empty($cs['tenant_id']) || empty($cs['license_key'])) return $GLOBALS['dei_tp_plan'] = ['ok' => true, 'tier' => '', 'trial' => false, 'central' => false];
    $cap = [];
    try { $cap = getCapStatus($s); } catch (\Throwable $e) { error_log('tpPlan: ' . $e->getMessage()); }
    $tier = strtolower(trim((string)($cap['tier'] ?? '')));
    $trial = !empty($cap['trial']) || $tier === 'trial';
    $ok = !$trial && in_array($tier, explode(',', TP_TIERS), true);
    return $GLOBALS['dei_tp_plan'] = ['ok' => $ok, 'tier' => $trial ? 'trial' : $tier, 'trial' => $trial, 'central' => true];
}
function tpLockedMsg() { return 'Filter Topik & Divisi tersedia mulai paket Growth. Hubungi ' . deiBrandVendor() . ' untuk upgrade paket.'; }
function tpActive() {
    if (isset($GLOBALS['dei_tp_active'])) return $GLOBALS['dei_tp_active'];
    $c = tpConf();
    return $GLOBALS['dei_tp_active'] = (!empty($c['enabled']) && count($c['topics']) > 0 && tpPlan()['ok']);
}
function tpTopicMap() {
    $m = [];
    foreach (tpConf()['topics'] as $t) $m[$t['id']] = $t;
    return $m;
}
// Pesan yang layak memicu klasifikasi (bukan basa-basi / stiker / ucapan penutup)
function tpCountable($text, $bye) {
    if ($bye) return false;
    $t = trim(preg_replace('/\s+/u', ' ', (string)$text));
    if (mb_strlen($t) < 4) return false;
    if (preg_match('/^(ok(e|ey|ay)?|oke+h?|sip+|siap|baik|iya+|ya+|y|tidak|gak|nggak|ga|thanks?|thx|makasih|terima ?kasih|mksh|tq|halo+|hai|hi|p|ping|test|tes)( (kak|ka|kk|min|mas|mbak|pak|bu|ya|yah|deh|dong))*[.!]*$/iu', $t)) return false;
    return (bool)preg_match('/[\p{L}\p{N}]/u', $t);
}
// Kuota: dari pusat (features.classify_quota) + catatan lokal bulan berjalan
function tpQuota() {
    $f = (array)(readJson(CAP_CACHE_FILE, [])['features'] ?? []);
    $month = wibDate('Y-m');
    $u = readJson(TP_USAGE_FILE, []);
    $row = is_array($u[$month] ?? null) ? $u[$month] : [];
    $central = tpPlan()['central'];
    // pusat: kuota dari fitur paket (didorong pusat), kalau belum ada dari jawaban pusat terakhir; -1 = belum diketahui.
    // Tanpa pusat: 0 = tanpa batas.
    $fq = (int)($f['classify_quota'] ?? -1);   // didorong pusat tiap menit (cron) -> paling baru
    $limit = $central ? ($fq >= 0 ? $fq : (int)($row['limit'] ?? -1)) : 0;
    $used = (int)($row['used'] ?? ($row['n'] ?? 0));
    $out = $central && $limit >= 0 && $used >= $limit;   // limit 0 di pusat = tidak dapat jatah
    $y = (int)substr($month, 0, 4); $m = (int)substr($month, 5, 2) + 1; if ($m > 12) { $m = 1; $y++; }
    return ['limit' => $limit, 'used' => $used, 'left' => ($limit > 0 ? max(0, $limit - $used) : null), 'out' => $out,
            'month' => $month, 'reset' => sprintf('%04d-%02d-01', $y, $m), 'central' => $central,
            'pct' => $limit > 0 ? round($used / $limit * 100, 1) : 0];
}
function tpUsageAdd($n, $quotaFromPusat = null) {
    deiWithLock('tp-usage', function () use ($n, $quotaFromPusat) {
        $month = wibDate('Y-m');
        $u = readJson(TP_USAGE_FILE, []); if (!is_array($u)) $u = [];
        $row = is_array($u[$month] ?? null) ? $u[$month] : ['n' => 0];
        $row['n'] = (int)($row['n'] ?? 0) + (int)$n;
        if (is_array($quotaFromPusat)) { $row['used'] = (int)($quotaFromPusat['used'] ?? $row['n']); $row['limit'] = (int)($quotaFromPusat['limit'] ?? -1); }
        else $row['used'] = (int)($row['used'] ?? 0) + (int)$n;
        $row['at'] = time();
        $u[$month] = $row; ksort($u); $u = array_slice($u, -12, null, true);
        writeJson(TP_USAGE_FILE, $u);
    });
}
// 20 bubble terakhir satu nomor (lama -> baru): [['r' => 'p'|'k', 't' => teks]]
function tpBubbles($num) {
    $out = [];
    foreach (logReadByNumber($num, TP_BUBBLES) as $e) {   // terbaru dulu
        $a = trim((string)($e['a'] ?? ''));
        $q = trim((string)($e['q'] ?? ''));
        if ($q === '' && is_array($e['media'] ?? null)) $q = '[' . (string)($e['media']['type'] ?? 'media') . ']' . (isset($e['media']['caption']) ? ' ' . (string)$e['media']['caption'] : '');
        if ($a !== '' && ($e['dir'] ?? '') !== 'call') $out[] = ['r' => 'k', 't' => mb_substr($a, 0, 300)];
        if ($q !== '') $out[] = ['r' => 'p', 't' => mb_substr($q, 0, 300)];
        if (count($out) >= TP_BUBBLES) break;
    }
    return array_reverse(array_slice($out, 0, TP_BUBBLES));
}
// Prompt klasifikasi — SAMA dengan versi di server pusat (backend/classify-lib.php)
function tpPrompt($business, $topics, $msgs) {
    $list = '';
    foreach ($topics as $t) $list .= '- ' . $t['id'] . ': ' . $t['name'] . (($t['desc'] ?? '') !== '' ? ' (' . $t['desc'] . ')' : '') . "\n";
    $sys = "Anda mengklasifikasi percakapan WhatsApp pelanggan" . ($business !== '' ? " dengan bisnis \"" . $business . "\"" : '') . ".\n"
         . "Tentukan topik yang sedang ditanyakan/dibahas PELANGGAN, HANYA dari daftar ini (pakai id-nya):\n" . $list
         . "\nATURAN:\n- t: semua id topik yang dibahas pelanggan (boleh lebih dari satu, maks 4). Abaikan sapaan/basa-basi.\n"
         . "- m: satu id topik utama = yang paling relevan dengan pesan pelanggan TERAKHIR.\n"
         . "- Kalau tidak ada yang cocok atau hanya basa-basi: t = [] dan m = \"\".\n"
         . "- c: keyakinan 0-1.\nBalas HANYA JSON: {\"t\":[\"id\"],\"m\":\"id\",\"c\":0.9}";
    $conv = '';
    foreach ($msgs as $b) $conv .= (($b['r'] ?? '') === 'p' ? 'Pelanggan: ' : 'Kami: ') . str_replace(["\r", "\n"], ' ', (string)($b['t'] ?? '')) . "\n";
    return [$sys, "Percakapan (lama ke baru):\n" . $conv];
}
function tpParse($raw, $ids) {
    $raw = (string)$raw; $a = strpos($raw, '{'); $b = strrpos($raw, '}');
    $j = ($a !== false && $b !== false) ? json_decode(substr($raw, $a, $b - $a + 1), true) : null;
    if (!is_array($j)) return null;
    $ok = array_flip($ids); $t = [];
    foreach ((array)($j['t'] ?? []) as $x) { $x = (string)$x; if (isset($ok[$x]) && !in_array($x, $t, true)) $t[] = $x; }
    $t = array_slice($t, 0, 4);
    $m = (string)($j['m'] ?? '');
    if (!isset($ok[$m])) $m = $t[0] ?? '';
    if ($m !== '' && !in_array($m, $t, true)) array_unshift($t, $m);
    return ['t' => $t, 'm' => $m, 'c' => max(0, min(1, (float)($j['c'] ?? 0)))];
}
/* Klasifikasi beberapa percakapan. $items = [key => msgs]. Hasil [key => ['t','m','c'] | ['err' => '...']]
 * Dengan server pusat: lewat pusat (key DEI, kuota dihitung pusat). Tanpa pusat: OpenRouter tenant sendiri. */
function tpClassify($items, $s = null) {
    if (!$items) return [[], null];
    if ($s === null) $s = getSettings();
    $topics = array_values(tpConf()['topics']);
    $ids = array_column($topics, 'id');
    $biz = trim((string)($s['bot']['persona_company'] ?? '')) ?: trim((string)($s['bot']['bot_name'] ?? ''));
    $cs = $s['central_server'] ?? [];
    $out = [];
    if (!empty($cs['url']) && !empty($cs['tenant_id']) && !empty($cs['license_key'])) {
        $send = []; $keys = array_keys($items);
        foreach ($keys as $i => $k) $send[] = ['id' => $i, 'msgs' => $items[$k]];
        $ch = curl_init(rtrim($cs['url'], '/') . '/backend/index.php?action=classify');
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true, CURLOPT_TIMEOUT => 40, CURLOPT_CONNECTTIMEOUT => 8,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode(['tenant_id' => $cs['tenant_id'], 'license_key' => $cs['license_key'], 'current' => DEI_VERSION,
                'business' => mb_substr($biz, 0, 80), 'topics' => array_map(function ($t) { return ['id' => $t['id'], 'name' => $t['name'], 'desc' => $t['desc']]; }, $topics),
                'items' => $send], JSON_UNESCAPED_UNICODE)]);
        $res = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $err = curl_error($ch); curl_close($ch);
        $j = json_decode((string)$res, true);
        $quota = is_array($j['quota'] ?? null) ? $j['quota'] : null;
        if (!is_array($j) || empty($j['ok'])) {
            $msg = is_array($j) ? (string)($j['error'] ?? ('HTTP ' . $code)) : ('pusat: ' . ($err !== '' ? $err : 'HTTP ' . $code));
            foreach ($keys as $k) $out[$k] = ['err' => $msg, 'quota_out' => !empty($j['quota_out'])];
            if ($quota) tpUsageAdd(0, $quota);
            return [$out, $quota];
        }
        $n = 0;
        foreach ((array)($j['results'] ?? []) as $r) {
            $k = $keys[(int)($r['id'] ?? -1)] ?? null;
            if ($k === null) continue;
            if (!empty($r['ok'])) { $n++; $p = tpParse(json_encode(['t' => $r['t'] ?? [], 'm' => $r['m'] ?? '', 'c' => $r['c'] ?? 0]), $ids); $out[$k] = $p ?: ['err' => 'jawaban tak terbaca']; }
            else { if (!empty($r['used'])) $n++; $out[$k] = ['err' => (string)($r['error'] ?? 'gagal')]; }
        }
        foreach ($keys as $k) if (!isset($out[$k])) $out[$k] = ['err' => 'tidak ada hasil'];
        tpUsageAdd($n, $quota);
        return [$out, $quota];
    }
    // tanpa server pusat: key OpenRouter / Anthropic tenant sendiri, model Haiku
    $s2 = $s; $s2['api']['max_tokens'] = 150; $s2['api']['_timeout'] = 25; $s2['api']['fallback'] = 'none';
    if (($s['api']['provider'] ?? 'anthropic') === 'openrouter') $s2['api']['openrouter_model'] = TP_MODEL; else $s2['api']['model'] = 'claude-haiku-5-5';
    $n = 0;
    foreach ($items as $k => $msgs) {
        list($sys, $user) = tpPrompt($biz, $topics, $msgs);
        list($ok, $ans, $usage) = callClaudeOnce($s2, $sys, [['role' => 'user', 'content' => $user]]);
        if (!$ok) { $out[$k] = ['err' => mb_substr((string)$ans, 0, 160)]; continue; }
        $n++;
        $p = tpParse($ans, $ids);
        $out[$k] = $p ?: ['err' => 'jawaban tak terbaca'];
    }
    if ($n) tpUsageAdd($n, null);
    return [$out, null];
}
function tpPublic($c) {
    if (!is_array($c) || !is_array($c['tp'] ?? null)) return null;
    $tp = $c['tp'];
    return ['m' => (string)($tp['m'] ?? ''), 't' => array_values((array)($tp['t'] ?? [])), 'd' => (string)($tp['d'] ?? ''),
            'lk' => !empty($tp['lk']), 'by' => (string)($tp['by'] ?? ''), 'at' => (int)($tp['at'] ?? 0), 'cf' => (float)($tp['cf'] ?? 0),
            'h' => array_values((array)($c['tp_h'] ?? []))];
}
function tpDivOf($topicId, $map = null) {
    $map = $map ?? tpTopicMap();
    return (string)($map[$topicId]['div'] ?? '');
}
// Tulis label ke kontak. $by = 'ai' | username. $lock: kunci dari AI (koreksi manual)
function tpStore($num, $t, $m, $by, $lock, $cf = 0) {
    $map = tpTopicMap();
    $t = array_values(array_filter(array_map('strval', (array)$t), function ($x) use ($map) { return isset($map[$x]); }));
    if ($m !== '' && !isset($map[$m])) $m = '';
    if ($m === '' && $t) $m = $t[0];
    if ($m !== '' && !in_array($m, $t, true)) array_unshift($t, $m);
    return waContactUpdate($num, function (&$c) use ($t, $m, $by, $lock, $cf, $map) {
        if ($by === 'ai' && !empty($c['tp']['lk'])) return false;   // dikunci agent -> AI tidak menimpa
        $c['tp'] = ['m' => $m, 't' => $t, 'd' => $m !== '' ? (string)($map[$m]['div'] ?? '') : '', 'at' => time(), 'by' => $by, 'lk' => $lock ? 1 : 0, 'cf' => round((float)$cf, 2)];
        $h = array_values((array)($c['tp_h'] ?? []));
        foreach ($t as $x) { $h = array_values(array_diff($h, [$x])); $h[] = $x; }
        $c['tp_h'] = array_slice($h, -30);
    });
}
function tpBackfillState() {
    $b = readJson(TP_BACKFILL_FILE, []);
    if (!is_array($b) || empty($b['started_at'])) return null;
    return ['started_at' => (int)$b['started_at'], 'by' => (string)($b['by'] ?? ''), 'total' => (int)($b['total'] ?? 0),
            'left' => count((array)($b['queue'] ?? [])), 'done' => (int)($b['done'] ?? 0), 'fail' => (int)($b['fail'] ?? 0),
            'finished_at' => (int)($b['finished_at'] ?? 0)];
}
// Antrekan semua nomor WA yang aktif 7 hari terakhir & belum berlabel (atau semua bila $all)
function tpBackfillStart($by, $days = 7, $all = false) {
    $cut = date('Y-m-d H:i:s', time() - $days * 86400);
    $nums = [];
    foreach (logReadAll() as $e) {
        if (($e['channel'] ?? '') !== 'whatsapp') continue;
        if ((string)($e['ts'] ?? '') < $cut) continue;
        $n = waNormNum($e['ip'] ?? '');
        if ($n !== '') $nums[$n] = true;
    }
    $ct = waGetContacts();
    $q = [];
    foreach (array_keys($nums) as $n) {
        $n = (string)$n;
        if (!empty($ct[$n]['tp']['lk'])) continue;
        if (!$all && is_array($ct[$n]['tp'] ?? null)) continue;
        $q[] = $n;
    }
    $st = ['started_at' => time(), 'by' => (string)$by, 'days' => $days, 'total' => count($q), 'queue' => $q, 'done' => 0, 'fail' => 0, 'finished_at' => count($q) ? 0 : time()];
    deiWithLock('tp-backfill', function () use ($st) { writeJson(TP_BACKFILL_FILE, $st); });
    return tpBackfillState();
}
/* cron_tick: klasifikasikan chat yang memenuhi pemicu + antrean backfill. Maks TP_PER_TICK per tick. */
function tpSweep($s) {
    if (!empty($GLOBALS['dei_dry']) || !tpActive()) return null;
    $q = tpQuota();
    $u = readJson(TP_USAGE_FILE, []);
    $lastOut = (int)($u[$q['month']]['out_at'] ?? 0);
    if ($q['out'] && (time() - $lastOut) < 600) return ['quota_out' => true];   // cek ulang ke pusat maks 1x / 10 menit
    $now = time();
    $cand = [];
    foreach (convStateReadAll() as $num => $st) {
        if (!is_array($st)) continue;
        $n = (int)($st['tp_n'] ?? 0); $due = !empty($st['tp_due']);
        if (!$n && !$due) continue;
        if ((int)($st['tp_err_at'] ?? 0) > $now - 600) continue;   // gagal < 10 menit lalu -> tunda
        $idle = $now - (int)($st['last_at'] ?? 0);
        if ($due || $n >= TP_EVERY_N || $idle >= TP_IDLE_SEC) $cand[(string)$num] = ['n' => $n, 'due' => $due, 'pr' => $due ? 0 : ($n >= TP_EVERY_N ? 1 : 2), 'last' => (int)($st['last_at'] ?? 0)];
    }
    uasort($cand, function ($a, $b) { return $a['pr'] <=> $b['pr'] ?: $b['last'] <=> $a['last']; });
    $pick = array_slice($cand, 0, TP_PER_TICK, true);
    $fromBf = [];
    if (count($pick) < TP_PER_TICK) {
        $bf = readJson(TP_BACKFILL_FILE, []);
        foreach (array_slice((array)($bf['queue'] ?? []), 0, TP_PER_TICK - count($pick)) as $n) {
            $n = (string)$n;
            if (!isset($pick[$n])) { $fromBf[$n] = true; $pick[$n] = ['n' => 0, 'due' => false, 'pr' => 3]; }
        }
    }
    if (!$pick) return null;
    $ct = waGetContacts();
    $items = []; $skip = [];
    foreach ($pick as $num => $p) {
        if (!empty($ct[$num]['tp']['lk'])) { $skip[$num] = 'lk'; continue; }
        $b = tpBubbles($num);
        $hasGuest = false; foreach ($b as $x) if ($x['r'] === 'p') { $hasGuest = true; break; }
        if (!$hasGuest) { $skip[$num] = 'kosong'; continue; }
        $items[$num] = $b;
    }
    list($res, $quota) = $items ? tpClassify($items, $s) : [[], null];
    $done = 0; $fail = 0; $qOut = false;
    foreach ($pick as $num => $p) {
        $r = $res[$num] ?? null;
        $ok = isset($skip[$num]) || (is_array($r) && !isset($r['err']));
        if (is_array($r) && !isset($r['err'])) { tpStore($num, $r['t'], $r['m'], 'ai', false, $r['c']); $done++; }
        elseif (is_array($r)) { $fail++; if (!empty($r['quota_out'])) $qOut = true; }
        if (!empty($fromBf[$num])) continue;
        try { convStateMutate(function (&$a) use ($num, $p, $ok) {
            if (!is_array($a[$num] ?? null)) return;
            if ($ok) { $a[$num]['tp_n'] = max(0, (int)($a[$num]['tp_n'] ?? 0) - (int)$p['n']); $a[$num]['tp_due'] = 0; $a[$num]['tp_err_at'] = 0; }
            else $a[$num]['tp_err_at'] = time();
        }, $num); } catch (\Throwable $e) { error_log('tpSweep conv-state: ' . $e->getMessage()); }
    }
    if ($fromBf) {
        deiWithLock('tp-backfill', function () use ($fromBf, $res, $skip, $qOut) {
            $bf = readJson(TP_BACKFILL_FILE, []);
            if (!is_array($bf) || empty($bf['started_at'])) return;
            $keep = [];
            foreach ((array)($bf['queue'] ?? []) as $n) {
                $n = (string)$n;
                if (!isset($fromBf[$n])) { $keep[] = $n; continue; }
                $r = $res[$n] ?? null;
                if (isset($skip[$n]) || (is_array($r) && !isset($r['err']))) { $bf['done'] = (int)($bf['done'] ?? 0) + 1; continue; }
                if ($qOut) { $keep[] = $n; continue; }   // kuota habis: tetap di antrean
                $bf['fail'] = (int)($bf['fail'] ?? 0) + 1;   // gagal lain: dilewati
            }
            $bf['queue'] = $keep;
            if (!$keep && empty($bf['finished_at'])) $bf['finished_at'] = time();
            writeJson(TP_BACKFILL_FILE, $bf);
        });
    }
    if ($qOut) {
        deiWithLock('tp-usage', function () {
            $m = wibDate('Y-m'); $u = readJson(TP_USAGE_FILE, []); if (!is_array($u)) $u = [];
            $u[$m] = (is_array($u[$m] ?? null) ? $u[$m] : []); $u[$m]['out_at'] = time(); writeJson(TP_USAGE_FILE, $u);
        });
    }
    return ['done' => $done, 'fail' => $fail, 'skip' => count($skip), 'quota_out' => $qOut];
}
// Filter daftar Percakapan WA: topik ('' | id | __none), divisi ('' | id | __none), $ever = cari di riwayat "pernah tanya"
function tpMatchTopic($tp, $f, $ever) {
    if ($f === '') return true;
    if ($f === '__none') return !$tp || !$tp['t'];
    if (!$tp) return false;
    return in_array($f, $ever ? array_unique(array_merge($tp['t'], $tp['h'])) : $tp['t'], true);
}
function tpMatchDiv($tp, $f) {
    if ($f === '') return true;
    if ($f === '__none') return !$tp || $tp['d'] === '';
    return $tp && $tp['d'] === $f;
}
function tpClientConf($withQuota = false) {
    $c = tpConf();
    $o = ['on' => tpActive(), 'divisions' => $c['divisions'],
          'topics' => array_map(function ($t) { return ['id' => $t['id'], 'name' => $t['name'], 'div' => $t['div']]; }, $c['topics'])];
    if ($withQuota) $o['quota'] = tpQuota();
    return $o;
}
/* ====== /v1.2.138: filter-topik ====== */

