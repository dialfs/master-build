<?php
// v1.2.184: tes kirim email reset password lewat mail_relay pusat LIVE (dijalankan di server pusat via SSH).
// Pakai: php tes_email_live.php <root pusat> <email tujuan>
$root = $argv[1]; $to = $argv[2];
$ts = json_decode((string)@file_get_contents($root . '/data/tenants.json'), true) ?: [];
$t = null;
foreach ($ts as $x) if (!empty($x['license_key']) && stripos((string)$x['tenant_id'], 'dei') !== false) { $t = $x; break; }
if (!$t) foreach ($ts as $x) if (!empty($x['license_key'])) { $t = $x; break; }
if (!$t) { echo "Tidak ada tenant berlisensi.\n"; exit(1); }
$w = gmdate('d-m-Y H:i', time() + 7 * 3600) . ' WIB';
$text = "Ini email UJI fitur Lupa password (v1.2.184), dikirim lewat mail_relay pusat atas nama tenant {$t['tenant_id']} pada {$w}.\n\nKalau email ini masuk Inbox (bukan Spam), pengiriman email reset password sudah berjalan.\n\n— DEI Chatbot\n";
$html = '<p style="font-family:Arial,sans-serif;font-size:14px">' . nl2br(htmlspecialchars($text)) . '</p>';
$ch = curl_init('https://chat.deintegra.com/backend/index.php?action=mail_relay');
curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 30, CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_POSTFIELDS => json_encode(['tenant_id' => $t['tenant_id'], 'license_key' => $t['license_key'], 'kind' => 'pw_reset',
        'to' => $to, 'subject' => '[Tes] Email reset password DEI Chatbot', 'text' => $text, 'html' => $html, 'from_name' => 'DEI Chatbot'])]);
$r = curl_exec($ch); $c = curl_getinfo($ch, CURLINFO_HTTP_CODE); $e = curl_error($ch);
echo "tenant {$t['tenant_id']} -> HTTP {$c} {$r} {$e}\n";
$log = json_decode((string)@file_get_contents($root . '/data/mail-log.json'), true) ?: [];
echo 'mail-log terakhir: ' . json_encode($log[0] ?? null) . "\n";
echo 'sendmail_path: ' . ini_get('sendmail_path') . "\n";
