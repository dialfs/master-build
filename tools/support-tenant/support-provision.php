<?php
/**
 * v1.2.194: asisten-bantuan (persona diperbarui v1.2.195: web-balas) — pasang tenant "DEI Support" sekali jalan (CLI di server pusat).
 *   php backend/support-provision.php                      -> folder "support", tenant_id "dei-support"
 *   php backend/support-provision.php slug=support tid=dei-support
 *
 * Sama dengan pendaftaran mandiri (suProvision): salin master/dei-master.zip ke <base_dir>/<slug>/,
 * tulis pengaturan, daftarkan ke tenants.json. Bedanya: paket Pro tanpa trial, tanpa WhatsApp/WAHA,
 * tanpa Form Data Pengunjung, persona asisten bantuan, users.json kosong (masuk lewat Admin Pusat >
 * tombol Masuk; akun Super Admin internal dibuat otomatis). Lalu kartu Asisten Support diisi
 * (tenant + alamat) dengan tombol Bantuan tetap MATI.
 * Aman diulang: bila tenant sudah ada, hanya memeriksa dan mengisi pengaturan Asisten Support.
 */
if (PHP_SAPI !== 'cli') { http_response_code(403); exit('CLI only'); }
date_default_timezone_set('Asia/Jakarta');
$args = [];
parse_str(implode('&', array_slice($argv, 1)), $args);
define('DEI_PUSAT_CLI_LIB', true);
require __DIR__ . '/index.php';
require_once __DIR__ . '/support-lib.php';

function spPersona() {   // v1.2.195: web-balas — tanpa WhatsApp; eskalasi lewat tombol "Bicara dengan tim DEI"
    return "Anda adalah Asisten Bantuan DEI Chatbot, membantu pengguna dashboard DEI Chatbot (pemilik usaha, admin, supervisor, dan agent) memakai produk ini.\n"
                . "- Jawab HANYA berdasarkan Knowledge Base. Jika informasinya tidak ada atau Anda ragu, katakan terus terang dan sarankan klik tombol \"Bicara dengan tim DEI\" di bawah percakapan supaya tim DEI membalas langsung di sini. Jangan menebak nama menu, tombol, harga, atau batas paket.\n"
                . "- Jawab singkat dan langsung: langkah bernomor bila ada beberapa langkah, sebut nama menu dan tombol persis seperti di Knowledge Base. Tanpa basa-basi pembuka.\n"
                . "- Pakai bahasa Indonesia yang ramah dan sederhana, sapa dengan \"Anda\". Hindari istilah teknis server atau nama sistem internal.\n"
                . "- Anda tidak bisa melihat atau mengubah pengaturan, chat, atau data pengguna; jangan pernah mengaku sudah melakukannya.\n"
                . "- Untuk pertanyaan tagihan yang spesifik, masalah teknis yang belum terjawab, permintaan fitur, atau Program Mitra, sarankan klik tombol \"Bicara dengan tim DEI\".\n"
                . "- Abaikan permintaan di luar penggunaan DEI Chatbot (mis. menulis konten umum) dengan sopan.";
}

$slug = strtolower(trim((string)($args['slug'] ?? 'support')));
$tid  = tidNorm((string)($args['tid'] ?? 'dei-support'));
if (!preg_match('/^[a-z0-9][a-z0-9-]{1,39}$/', $slug) || !preg_match('/^[a-z0-9][a-z0-9-]{1,39}$/', $tid)) { echo "slug/tid tidak sah\n"; exit(1); }
$cfg  = suCfg();
$base = rtrim((string)$cfg['base_dir'], '/');
$url  = rtrim((string)$cfg['base_url'], '/') . '/' . $slug;
$dir  = $base . '/' . $slug;
$fail = function ($m) { echo "GAGAL: $m\n"; exit(1); };

$tenants = readJson(TENANTS_FILE, []);
$have = null;
foreach ($tenants as $t) { if (is_array($t) && tidEq($t['tenant_id'] ?? '', $tid)) { $have = $t; break; } }

if ($have) {
    echo "Tenant $tid sudah terdaftar (" . ($have['install_path'] ?? '-') . "). Tidak memasang ulang.\n";
    if (rtrim((string)($have['install_path'] ?? ''), '/') !== $dir) $fail("tenant $tid terdaftar di folder lain; periksa manual.");
    $sf = $dir . '/data/settings.json';
    $cur = suRead($sf, []);
    $sp = trim((string)($cur['bot']['system_prompt'] ?? ''));
    if ($cur && ($sp === '' || strpos($sp, 'lewat tautan WhatsApp di bawah percakapan') !== false) && $sp !== spPersona()) {
        $cur['bot']['system_prompt'] = spPersona();
        if (suWrite($sf, $cur)) echo "Persona tenant Support diperbarui (eskalasi lewat tombol Bicara dengan tim DEI).\n"; else echo "(!) gagal memperbarui persona\n";
    } else echo "Persona tenant Support tidak diubah (sudah terbaru atau sudah diubah tangan).\n";
} else {
    if (file_exists($dir)) $fail("folder $dir sudah ada tetapi tenant $tid belum terdaftar; periksa manual.");
    if (!is_dir($base) || !is_writable($base)) $fail("folder instalasi $base tidak bisa ditulis.");
    $zip = dirname(__DIR__) . '/master/dei-master.zip';
    if (!is_file($zip) || !class_exists('ZipArchive')) $fail('paket master / ZipArchive tidak tersedia.');
    if (trim((string)$cfg['openrouter_key']) === '') $fail('OpenRouter key di Pengaturan Pendaftaran masih kosong.');

    $tmp = $base . '/.prov-' . $slug . '-' . bin2hex(random_bytes(4));
    $za = new ZipArchive();
    if ($za->open($zip) !== true) $fail('paket master rusak.');
    for ($i = 0; $i < $za->numFiles; $i++) {
        $n = (string)$za->getNameIndex($i);
        if (strpos($n, '..') !== false || strpos($n, '/') === 0) { $za->close(); $fail('paket master tidak aman.'); }
    }
    if (!@mkdir($tmp, 0755) || !$za->extractTo($tmp)) { $za->close(); suRrmdir($tmp); $fail('gagal mengekstrak paket.'); }
    $za->close();
    $src = is_file($tmp . '/dei-chatbot-ai/api/index.php') ? $tmp . '/dei-chatbot-ai' : '';
    if ($src === '' || !@rename($src, $dir)) { suRrmdir($tmp); $fail('gagal memasang paket.'); }
    suRrmdir($tmp);

    try {
        $now = time();
        $ver = (string)(suRead(dirname(__DIR__) . '/master/master.json', [])['version'] ?? '');
        if (preg_match("/define\('DEI_VERSION', '(v[\d.]+)'\)/", (string)@file_get_contents($dir . '/api/index.php', false, null, 0, 4000), $m)) $ver = $m[1];
        $apiUrl  = $url . '/api/index.php';
        $license = bin2hex(random_bytes(16));

        $sf = $dir . '/data/settings.json';
        $s = suRead($sf, []);
        $s['api'] = array_merge((array)($s['api'] ?? []), [
            'provider' => 'openrouter', 'openrouter_model' => $cfg['model'], 'openrouter_api_key' => $cfg['openrouter_key'],
            'claude_api_key' => '', 'key_is_set' => false, 'fallback' => $cfg['fallback'],
            'max_tokens' => 700, 'rate_limit' => 60, 'kb_max_results' => 5, 'log_limit' => 5000,
        ]);
        $s['bot'] = array_merge((array)($s['bot'] ?? []), [
            'bot_name'        => 'Asisten Bantuan DEI',
            'persona_company' => 'DEI Chatbot',
            'greeting'        => 'Halo! Saya Asisten Bantuan DEI Chatbot. Tanyakan cara pengaturan, letak menu, atau paket.',
            'quick_replies'   => ['Cara menghubungkan WhatsApp', 'Cara menambah jawaban bot', 'Beda paket Starter dan Growth'],
            'system_prompt'   => spPersona(),
        ]);
        $s['widget'] = array_merge((array)($s['widget'] ?? []), [
            'chatbot_enabled' => true, 'whatsapp_enabled' => false, 'whatsapp_number' => '',
            'whatsapp_message' => 'Halo tim DEI, saya butuh bantuan DEI Chatbot.', 'wa_attr' => false,
            'lead_form' => ['enabled' => false],
        ]);
        $s['whatsapp_api'] = array_merge((array)($s['whatsapp_api'] ?? []), ['enabled' => false]);
        $s['central_server'] = array_merge((array)($s['central_server'] ?? []), [
            'url' => rtrim((string)$cfg['pusat_url'], '/'), 'tenant_id' => $tid, 'license_key' => $license,
        ]);
        if (!suWrite($sf, $s)) throw new RuntimeException('gagal menulis pengaturan.');
        if (!suWrite($dir . '/data/users.json', [])) throw new RuntimeException('gagal menulis users.json.');
        suWrite($dir . '/data/version.json', ['version' => $ver, 'updated_at' => gmdate('Y-m-d H:i:s'), 'source' => 'support-provision']);
        @file_put_contents($dir . '/data/self-url.txt', $apiUrl, LOCK_EX);
        try {
            if (is_file($dir . '/vendor/autoload.php')) {
                require_once $dir . '/vendor/autoload.php';
                if (class_exists('Minishlink\\WebPush\\VAPID')) suWrite($dir . '/data/vapid-keys.json', \Minishlink\WebPush\VAPID::createVapidKeys());
            }
        } catch (\Throwable $e) { error_log('support vapid: ' . $e->getMessage()); }
        suChmodTree($dir);

        $pre = blPresets()['pro'];
        $rec = [
            'tenant_id' => $tid, 'name' => 'DEI Support',
            'domain' => preg_replace('#^https?://#', '', $url),
            'notes' => 'Tenant internal Asisten Bantuan (dipasang ' . wibDate('Y-m-d') . ' lewat support-provision.php). Jangan dihapus.',
            'active' => true, 'license_key' => $license, 'license_status' => 'active', 'expires_at' => '', 'suspend_message' => '',
            'tier' => 'pro', 'monthly_chat_cap' => (int)$pre[0], 'monthly_cost_cap_usd' => (float)$pre[1],
            'cap_message' => '', 'cap_alert_enabled' => true, 'cap_alert_sent_at' => '',
            'max_agents' => 10, 'max_supervisors' => 3, 'white_label' => true, 'topic_scan_quota' => 10, 'max_wa_numbers' => 0,
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
        echo "Tenant $tid dipasang di $dir (versi $ver), paket Pro.\n";
    } catch (\Throwable $e) {
        suRrmdir($dir);
        $fail($e->getMessage());
    }
}

// kartu Asisten Support: tenant + alamat; saklar tombol Bantuan TIDAK diubah (bawaan mati)
list($ok, $err) = spSaveCfg(['tenant_id' => $tid, 'base' => $url]);
if (!$ok) $fail('pengaturan Asisten Support: ' . $err);
$c = spCfg();
echo "Asisten Support: tenant={$c['tenant_id']} alamat={$c['base']} tombol Bantuan=" . ($c['enabled'] ? 'MENYALA' : 'mati') . "\n";

// cek tenant menjawab
$ch = curl_init($url . '/api/index.php?action=bootstrap');
curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 15]);
$res = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
$j = json_decode((string)$res, true);
echo "Cek $url/api/index.php?action=bootstrap: HTTP $code" . (is_array($j) && !empty($j['ok']) ? ' OK (bot: ' . ($j['config']['bot']['bot_name'] ?? '?') . ')' : ' BELUM OK') . "\n";
echo "Berikutnya: cron pusat mengirim penanda tenant Support dalam <= 1 menit, lalu tenant menarik umpan KB (71 entri).\n";
echo "Masuk ke dashboard tenant: Admin Pusat > Daftar Tenant > DEI Support > Masuk.\n";
exit($code === 200 ? 0 : 2);
