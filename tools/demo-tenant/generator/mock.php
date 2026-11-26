<?php
// Mock: OpenRouter (/ai), WAHA (/api/*), pusat (/backend/index.php)
$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$raw = file_get_contents('php://input');
$in = json_decode($raw, true) ?: [];
header('Content-Type: application/json');
@file_put_contents(__DIR__ . '/mock.log', date('c') . " $uri " . substr($raw, 0, 300) . "\n", FILE_APPEND);
if ($uri === '/ai') {
    $msgs = $in['messages'] ?? [];
    $last = '';
    for ($i = count($msgs) - 1; $i >= 0; $i--) if (($msgs[$i]['role'] ?? '') === 'user') { $c = $msgs[$i]['content']; $last = is_array($c) ? json_encode($c) : (string)$c; break; }
    $sys = json_encode($msgs[0]['content'] ?? '');
    if (strpos($raw, 'Anda menganalisa transkrip') !== false) {
        $reply = @file_get_contents(__DIR__ . '/lead-next.json') ?: '{"nama":"","kebutuhan":"","waktu":"","anggaran":"","ringkasan":""}';
        echo json_encode(['id' => 'gen-x', 'choices' => [['message' => ['role' => 'assistant', 'content' => $reply], 'finish_reason' => 'stop']], 'usage' => ['prompt_tokens' => 900, 'completion_tokens' => 80, 'total_tokens' => 980, 'cost' => 0.0003]]);
        exit;
    }
    if (strpos($raw, 'Anda analis customer service') !== false) {
        $um = ''; foreach ($msgs as $m) if (($m['role'] ?? '') === 'user') $um = is_array($m['content']) ? json_encode($m['content']) : (string)$m['content'];
        preg_match_all('/^(\d+)\. \[(?:WA|Web)\] (.*)$/m', $um, $mm, PREG_SET_ORDER);
        $defs = [
          ['Harga & tipe motor', '/harga|tipe|promo|berapa|ready|warna|stok/i', 'Pelanggan paling sering menanyakan harga OTR, warna, dan stok Volt S / Volt X.', 'positif', 'Tampilkan harga OTR dan stok warna di Daftar Harga, dan siapkan template balasan untuk stok warna.'],
          ['Cicilan & syarat kredit', '/cicil|kredit|dp|leasing|ajukan|tenor/i', 'Menanyakan DP, tenor, dan syarat kredit tanpa kartu kredit.', 'netral', 'Buat simulasi cicilan per tipe di Knowledge Base dan dorong pengajuan dokumen lewat WA.'],
          ['Test ride & kunjungan showroom', '/test ride|showroom|buka|minggu|sabtu|jam/i', 'Ingin menjadwalkan test ride, terutama akhir pekan.', 'positif', 'Tambah slot test ride akhir pekan dan konfirmasi otomatis H-1.'],
          ['Charging & daya listrik', '/cas|charging|listrik|va\b|apartemen/i', 'Ragu soal lama cas dan kecukupan daya listrik rumah/apartemen.', 'netral', 'Tambahkan tabel daya listrik vs charger di KB dan materi iklan.'],
          ['Tukar tambah', '/tukar tambah|beat|bensin/i', 'Ingin menukar motor bensin lama sebagai DP.', 'positif', 'Buat promo tukar tambah dengan taksiran awal lewat foto.'],
          ['Pembelian armada', '/armada|unit|perusahaan|kurir|pengadaan/i', 'Perusahaan menanyakan harga khusus untuk banyak unit.', 'positif', 'Siapkan template penawaran armada dan arahkan langsung ke sales B2B.'],
          ['Servis, garansi & keluhan', '/servis|garansi|baterai|komplain|stnk|bpkb/i', 'Booking servis, garansi baterai, status STNK, dan keluhan jarak tempuh.', 'negatif', 'Kirim pengingat servis berkala dan update status STNK secara proaktif.'],
        ];
        $groups = []; foreach ($defs as $i => $d) $groups[$i] = [];
        $other = [];
        foreach ($mm as $row) { $hit = false; foreach ($defs as $i => $d) if (preg_match($d[1], $row[2])) { $groups[$i][] = (int)$row[1]; $hit = true; break; } if (!$hit) $other[] = (int)$row[1]; }
        $topics = [];
        foreach ($defs as $i => $d) if ($groups[$i]) $topics[] = ['name' => $d[0], 'summary' => $d[2], 'sentiment' => $d[3], 'action' => $d[4], 'ids' => $groups[$i], 'examples' => array_slice($groups[$i], 0, 2)];
        if ($other) $topics[] = ['name' => 'Sapaan & basa-basi', 'summary' => 'Ucapan terima kasih dan konfirmasi singkat.', 'sentiment' => 'positif', 'action' => 'Biarkan bot menutup percakapan dengan ajakan test ride.', 'ids' => $other, 'examples' => array_slice($other, 0, 2)];
        $reply = json_encode(['topics' => $topics, 'insight' => 'Mayoritas pelanggan datang untuk harga dan cicilan, lalu berlanjut ke test ride. Minat pembelian armada mulai muncul dan bernilai besar. Keluhan baterai sedikit tetapi perlu ditangani cepat agar tidak jadi ulasan negatif.'], JSON_UNESCAPED_UNICODE);
        echo json_encode(['id' => 'gen-t', 'choices' => [['message' => ['role' => 'assistant', 'content' => $reply], 'finish_reason' => 'stop']], 'usage' => ['prompt_tokens' => 3000, 'completion_tokens' => 600, 'total_tokens' => 3600, 'cost' => 0.002]]);
        exit;
    }
    if (strpos($raw, 'Anda adalah Nadia') === false) { file_put_contents(__DIR__ . '/mock-other.log', substr($raw, 0, 1500) . "\n---\n", FILE_APPEND); }
    $q = @json_decode(@file_get_contents(__DIR__ . '/ai-queue.json'), true) ?: [];
    $reply = null;
    if ($q) { $reply = array_shift($q); file_put_contents(__DIR__ . '/ai-queue.json', json_encode($q)); }
    if ($reply === null) $reply = 'Baik Kak, terima kasih. Ada lagi yang bisa kami bantu?';
    echo json_encode(['id' => 'gen-' . uniqid(), 'model' => 'google/gemini-2.5-flash', 'choices' => [['message' => ['role' => 'assistant', 'content' => $reply], 'finish_reason' => 'stop']],
        'usage' => ['prompt_tokens' => 1800 + rand(0, 600), 'completion_tokens' => 60 + rand(0, 90), 'total_tokens' => 2000, 'cost' => 0.0007]]);
    exit;
}
if (strpos($uri, '/backend/index.php') === 0) {
    echo json_encode(['ok' => true, 'license' => ['status' => 'active', 'message' => '', 'expires_at' => ''], 'license_status' => 'active', 'update_available' => false,
        'cap_info' => ['cap_reached' => false, 'cap_warning' => false, 'usage_pct' => 1, 'tier' => 'pro', 'monthly_chat_cap' => 0, 'chats_this_month' => 0,
            'max_agents' => 10, 'max_supervisors' => 3, 'white_label' => false, 'topic_scan_quota' => 10, 'max_wa_numbers' => 2, 'max_business_units' => 3, 'classify_quota' => 2000]]);
    exit;
}
if (strpos($uri, '/api/') === 0) {
    if (preg_match('#/api/sessions/[^/]+$#', $uri) || preg_match('#/api/sessions#', $uri)) { echo json_encode(['name' => 'dei-demo', 'status' => 'WORKING', 'me' => ['id' => '6281100000001@c.us', 'pushName' => 'Nusa EV']]); exit; }
    echo json_encode(['id' => 'true_' . ($in['chatId'] ?? 'x') . '_3EB0' . strtoupper(bin2hex(random_bytes(8))), 'ack' => 1, 'timestamp' => time()]);
    exit;
}
echo json_encode(['ok' => true]);
