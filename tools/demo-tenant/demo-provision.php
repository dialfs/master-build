<?php
/**
 * Pasang tenant DEMO (chatbot.deintegra.com/demo) sekali jalan — CLI di server.
 *   php demo-provision.php pusat=/home/u1545168/public_html/chat.deintegra.com data=/path/demo-data.zip
 *
 * Sama dengan support-provision.php: salin master/dei-master.zip ke <base_dir>/demo, tulis pengaturan,
 * daftarkan ke tenants.json pusat. Bedanya: data/ diisi data contoh (demo-data.zip: percakapan WA,
 * kontak, leads + aktivitas CRM, task, KB, daftar harga, chat web) dengan akun admin/admin & sales/sales.
 * WhatsApp sengaja TIDAK tersambung (URL WAHA kosong): pengunjung demo tidak bisa scan QR nomornya sendiri.
 * Paket Pro dengan batas pemakaian kecil (kunci AI = kunci trial di Pengaturan Pendaftaran).
 * Tidak memasang ulang bila tenant/folder sudah ada.
 */
if (PHP_SAPI !== 'cli') { http_response_code(403); exit('CLI only'); }
date_default_timezone_set('Asia/Jakarta');
$args = [];
parse_str(implode('&', array_slice($argv, 1)), $args);
$pusat = rtrim((string)($args['pusat'] ?? (getenv('HOME') . '/public_html/chat.deintegra.com')), '/');
$dataZip = (string)($args['data'] ?? (__DIR__ . '/demo-data.zip'));
$slug = 'demo'; $tid = 'demo';
$fail = function ($m) { echo "GAGAL: $m\n"; exit(1); };
if (!is_file($pusat . '/backend/index.php')) $fail("pusat tidak ditemukan di $pusat");
if (!is_file($dataZip)) $fail("data contoh tidak ditemukan: $dataZip");

define('DEI_PUSAT_CLI_LIB', true);
require $pusat . '/backend/index.php';
foreach (['signup-lib.php', 'billing-lib.php'] as $lib) require_once $pusat . '/backend/' . $lib;

$cfg  = suCfg();
$base = rtrim((string)$cfg['base_dir'], '/');
$url  = rtrim((string)$cfg['base_url'], '/') . '/' . $slug;
$dir  = $base . '/' . $slug;

foreach (readJson(TENANTS_FILE, []) as $t) {
    if (is_array($t) && tidEq($t['tenant_id'] ?? '', $tid)) $fail("tenant id '$tid' sudah terdaftar (" . ($t['install_path'] ?? '-') . "). Tidak memasang ulang.");
}
if (file_exists($dir)) $fail("folder $dir sudah ada. Tidak memasang ulang.");
if (!is_dir($base) || !is_writable($base)) $fail("folder instalasi $base tidak bisa ditulis.");
$zip = $pusat . '/master/dei-master.zip';
if (!is_file($zip) || !class_exists('ZipArchive')) $fail('paket master / ZipArchive tidak tersedia.');
if (trim((string)$cfg['openrouter_key']) === '') $fail('OpenRouter key di Pengaturan Pendaftaran masih kosong.');

// 1) kode dari paket master
$tmp = $base . '/.prov-' . $slug . '-' . bin2hex(random_bytes(4));
$za = new ZipArchive();
if ($za->open($zip) !== true) $fail('paket master rusak.');
for ($i = 0; $i < $za->numFiles; $i++) { $n = (string)$za->getNameIndex($i); if (strpos($n, '..') !== false || strpos($n, '/') === 0) { $za->close(); $fail('paket master tidak aman.'); } }
if (!@mkdir($tmp, 0755) || !$za->extractTo($tmp)) { $za->close(); suRrmdir($tmp); $fail('gagal mengekstrak paket.'); }
$za->close();
$src = is_file($tmp . '/dei-chatbot-ai/api/index.php') ? $tmp . '/dei-chatbot-ai' : '';
if ($src === '' || !@rename($src, $dir)) { suRrmdir($tmp); $fail('gagal memasang paket.'); }
suRrmdir($tmp);

try {
    // 2) data contoh (hanya entri data/...)
    $zd = new ZipArchive();
    if ($zd->open($dataZip) !== true) throw new RuntimeException('demo-data.zip rusak.');
    $names = [];
    for ($i = 0; $i < $zd->numFiles; $i++) {
        $n = (string)$zd->getNameIndex($i);
        if (strpos($n, '..') !== false || strpos($n, 'data/') !== 0) { $zd->close(); throw new RuntimeException("entri tidak aman di demo-data.zip: $n"); }
        $names[] = $n;
    }
    if (!$zd->extractTo($dir, $names)) { $zd->close(); throw new RuntimeException('gagal mengekstrak data contoh.'); }
    $zd->close();

    $now = time();
    $ver = (string)(suRead($pusat . '/master/master.json', [])['version'] ?? '');
    if (preg_match("/define\('DEI_VERSION', '(v[\d.]+)'\)/", (string)@file_get_contents($dir . '/api/index.php', false, null, 0, 4000), $m)) $ver = $m[1];
    $apiUrl  = $url . '/api/index.php';
    $license = bin2hex(random_bytes(16));

    // 3) pengaturan: kunci AI trial, WA tidak tersambung, pusat
    $sf = $dir . '/data/settings.json';
    $s = suRead($sf, []);
    if (!$s) throw new RuntimeException('settings.json data contoh tidak terbaca.');
    $s['api'] = array_merge((array)($s['api'] ?? []), [
        'provider' => 'openrouter', 'openrouter_model' => $cfg['model'], 'openrouter_api_key' => $cfg['openrouter_key'],
        'claude_api_key' => '', 'key_is_set' => false, 'fallback' => $cfg['fallback'],
    ]);
    $s['whatsapp_api'] = array_merge((array)($s['whatsapp_api'] ?? []), [
        'enabled' => true, 'provider' => 'waha', 'waha_url' => '', 'waha_api_key' => '', 'waha_session' => 'dei-demo',
        'waha_webhook_key' => bin2hex(random_bytes(16)),
    ]);
    $s['central_server'] = array_merge((array)($s['central_server'] ?? []), [
        'url' => rtrim((string)$cfg['pusat_url'], '/'), 'tenant_id' => $tid, 'license_key' => $license, 'auto_update' => false,
    ]);
    if (!suWrite($sf, $s)) throw new RuntimeException('gagal menulis pengaturan.');
    suWrite($dir . '/data/version.json', ['version' => $ver, 'updated_at' => gmdate('Y-m-d H:i:s'), 'source' => 'demo-provision']);
    @file_put_contents($dir . '/data/self-url.txt', $apiUrl, LOCK_EX);
    try {
        if (is_file($dir . '/vendor/autoload.php')) {
            require_once $dir . '/vendor/autoload.php';
            if (class_exists('Minishlink\\WebPush\\VAPID')) suWrite($dir . '/data/vapid-keys.json', \Minishlink\WebPush\VAPID::createVapidKeys());
        }
    } catch (\Throwable $e) { error_log('demo vapid: ' . $e->getMessage()); }
    suChmodTree($dir);

    // 4) daftar di pusat: paket Pro (semua fitur), batas pemakaian kecil
    $rec = [
        'tenant_id' => $tid, 'name' => 'DEMO — Nusa EV (data contoh)',
        'domain' => preg_replace('#^https?://#', '', $url),
        'notes' => 'Tenant demo untuk presentasi (dipasang ' . wibDate('Y-m-d') . ' lewat demo-provision.php). Login admin/admin & sales/sales. WA sengaja tidak tersambung.',
        'active' => true, 'license_key' => $license, 'license_status' => 'active', 'expires_at' => '', 'suspend_message' => '',
        'tier' => 'pro', 'monthly_chat_cap' => 1000, 'monthly_cost_cap_usd' => 5.0,
        'cap_message' => 'Kuota demo bulan ini sudah habis. Hubungi tim DEI untuk mencoba lebih lanjut.', 'cap_alert_enabled' => true, 'cap_alert_sent_at' => '',
        'max_agents' => 10, 'max_supervisors' => 3, 'white_label' => false, 'topic_scan_quota' => 10, 'max_wa_numbers' => 0,
        'install_path' => $dir, 'api_url' => $apiUrl, 'api_url_manual' => false,
        'created' => gmdate('Y-m-d H:i:s', $now), 'last_seen' => '', 'current_version' => $ver, 'internal' => true,
    ];
    $tenants = readJson(TENANTS_FILE, []);
    foreach ($tenants as $t) { if (is_array($t) && tidEq($t['tenant_id'] ?? '', $tid)) throw new RuntimeException('tenant terdaftar bersamaan.'); }
    $tenants[] = $rec;
    writeJson(TENANTS_FILE, $tenants);
    $chk = false;
    foreach (readJson(TENANTS_FILE, []) as $t) { if (is_array($t) && tidEq($t['tenant_id'] ?? '', $tid)) { $chk = true; break; } }
    if (!$chk) throw new RuntimeException('gagal mendaftarkan tenant.');
    echo "Tenant $tid dipasang di $dir (versi $ver), paket Pro, batas 1.000 balasan AI / USD 5 per bulan.\n";
} catch (\Throwable $e) {
    suRrmdir($dir);
    $fail($e->getMessage());
}

// 5) cek dari luar: bootstrap + login admin & sales
$req = function ($action, $body = null) use ($url) {
    $ch = curl_init($url . '/api/index.php?action=' . $action);
    $o = [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 20];
    if ($body !== null) $o += [CURLOPT_POST => true, CURLOPT_POSTFIELDS => json_encode($body), CURLOPT_HTTPHEADER => ['Content-Type: application/json']];
    curl_setopt_array($ch, $o);
    $r = curl_exec($ch); $c = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    return [$c, json_decode((string)$r, true)];
};
[$c, $j] = $req('bootstrap');
echo "bootstrap: HTTP $c" . (!empty($j['ok']) ? ' OK (bot: ' . ($j['config']['bot']['bot_name'] ?? '?') . ')' : ' BELUM OK') . "\n";
$okAll = $c === 200;
foreach (['admin', 'sales'] as $u) {
    [$c, $j] = $req('login', ['username' => $u, 'password' => $u]);
    echo "login $u: HTTP $c " . (!empty($j['ok']) ? 'OK (peran ' . ($j['user']['role'] ?? '?') . ')' : 'GAGAL ' . ($j['error'] ?? '')) . "\n";
    $okAll = $okAll && !empty($j['ok']);
}
echo "Dashboard: $url/dashboard/chatbot-ai/login.html\n";
exit($okAll ? 0 : 2);
