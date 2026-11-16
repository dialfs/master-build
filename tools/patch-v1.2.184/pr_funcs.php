/* ============================================================
 * v1.2.184: lupa-password — reset password lewat email dari halaman login.
 * Token acak 32 byte (yang disimpan hanya sha256-nya) di data/pw-reset.json,
 * berlaku 30 menit & sekali pakai. Email dikirim lewat pusat (action mail_relay,
 * pengirim noreply@deintegra.com); tanpa pusat -> mail() lokal.
 * Alamat email: users[].email, atau username bila berbentuk email.
 * ============================================================ */
define('PWRESET_FILE', DATA_DIR . '/pw-reset.json');
define('PWRESET_TTL', 30 * 60);
function deiValidEmail($e) {
    $e = strtolower(trim((string)$e));
    return ($e !== '' && strlen($e) <= 190 && !preg_match('/[\r\n,;\s]/', $e) && filter_var($e, FILTER_VALIDATE_EMAIL)) ? $e : '';
}
function deiUserEmail($u) {
    $e = deiValidEmail($u['email'] ?? '');
    return $e !== '' ? $e : deiValidEmail($u['username'] ?? '');
}
function deiMaskEmail($e) {
    $p = explode('@', (string)$e, 2);
    if (count($p) < 2) return '';
    $n = mb_strlen($p[0]);
    return mb_substr($p[0], 0, min(2, $n)) . str_repeat('*', max(1, $n - 2)) . '@' . $p[1];
}
function deiEmailTaken($email, $exceptUsername, $users = null) {
    if ($email === '') return false;
    foreach (($users ?? readJson(USERS_FILE, [])) as $x) {
        if (($x['username'] ?? '') === $exceptUsername) continue;
        if (deiUserEmail($x) === $email) return true;
    }
    return false;
}
// Buka data/pw-reset.json di bawah kunci; $fn(&$all, $now) mengubah isi, nilai baliknya diteruskan.
function deiPwResetStore($fn) {
    return deiWithLock('pw-reset', function () use ($fn) {
        $all = readJson(PWRESET_FILE, []);
        if (!is_array($all)) $all = [];
        $now = time();
        foreach ($all as $k => $r) if ((int)($r['at'] ?? 0) < $now - 86400) unset($all[$k]);
        $ret = $fn($all, $now);
        writeJson(PWRESET_FILE, $all);
        return $ret;
    });
}
function deiMailMime($fromName, $fromAddr, $subject, $text, $html) {
    $fromName = trim(preg_replace('/[\r\n"<>\\\\]+/', ' ', (string)$fromName));
    if ($fromName === '') $fromName = 'DEI Chatbot';
    $b = 'dei-' . bin2hex(random_bytes(8));
    $dom = substr((string)strrchr($fromAddr, '@'), 1) ?: 'localhost';
    $hdr = 'From: =?UTF-8?B?' . base64_encode($fromName) . '?= <' . $fromAddr . ">\r\n"
         . "MIME-Version: 1.0\r\n"
         . 'Message-ID: <' . bin2hex(random_bytes(12)) . '@' . $dom . ">\r\n"
         . "Auto-Submitted: auto-generated\r\n"
         . 'Content-Type: multipart/alternative; boundary="' . $b . '"';
    $body = "--$b\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode((string)$text))
          . ((string)$html !== '' ? "--$b\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode((string)$html)) : '')
          . "--$b--\r\n";
    $subj = '=?UTF-8?B?' . base64_encode(trim(preg_replace('/[\r\n]+/', ' ', (string)$subject))) . '?=';
    return [$subj, $body, $hdr];
}
// Kirim email transaksional. Balikan ['ok'=>bool, 'via'=>'pusat'|'mail', 'error'=>...]
function deiSendMail($to, $subject, $text, $html, $kind) {
    $to = deiValidEmail($to);
    if ($to === '') return ['ok' => false, 'error' => 'alamat email tidak valid'];
    if (!empty($GLOBALS['dei_dry'])) return ['ok' => true, 'via' => 'dry'];
    $fromName = deiBrandProduct();
    $cs = getSettings()['central_server'] ?? [];
    if (!empty($cs['url']) && !empty($cs['tenant_id']) && !empty($cs['license_key'])) {
        $ch = curl_init(rtrim($cs['url'], '/') . '/backend/index.php?action=mail_relay');
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 20, CURLOPT_CONNECTTIMEOUT => 6,
            CURLOPT_POST => true, CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode(['tenant_id' => $cs['tenant_id'], 'license_key' => $cs['license_key'],
                'kind' => $kind, 'to' => $to, 'subject' => $subject, 'text' => $text, 'html' => $html, 'from_name' => $fromName])]);
        $resp = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $cerr = curl_error($ch); curl_close($ch);
        $j = json_decode((string)$resp, true);
        if ($code === 200 && !empty($j['ok']) && !empty($j['sent'])) return ['ok' => true, 'via' => 'pusat'];
        error_log('[mail] pusat HTTP ' . $code . ' ' . mb_substr((string)$resp, 0, 200) . ' ' . $cerr);
        if ($code !== 0) return ['ok' => false, 'via' => 'pusat', 'error' => (string)($j['error'] ?? ('HTTP ' . $code))];
        // pusat tak terjangkau -> coba mail() lokal
    }
    $host = strtolower(preg_replace('/:\d+$/', '', (string)($_SERVER['HTTP_HOST'] ?? '')));
    $host = preg_replace('/^www\./', '', preg_replace('/[^a-z0-9.\-]/', '', $host));
    if ($host === '' || strpos($host, '.') === false) $host = 'deintegra.com';
    list($subj, $body, $hdr) = deiMailMime($fromName, 'noreply@' . $host, $subject, $text, $html);
    $ok = function_exists('mail') && @mail($to, $subj, $body, $hdr);
    return ['ok' => (bool)$ok, 'via' => 'mail', 'error' => $ok ? '' : 'mail() gagal'];
}
function deiMailHtml($title, $paras, $btnText = '', $btnUrl = '', $foot = '') {
    $e = function ($x) { return htmlspecialchars((string)$x, ENT_QUOTES, 'UTF-8'); };
    $h = '<!DOCTYPE html><html><body style="margin:0;padding:24px;background:#f4f5fb;font-family:Arial,Helvetica,sans-serif;color:#15152b">'
       . '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">'
       . '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background:#ffffff;border:1px solid #e6e6ef;border-radius:14px">'
       . '<tr><td style="padding:28px 28px 8px"><div style="font-size:18px;font-weight:bold;margin-bottom:14px">' . $e($title) . '</div>';
    foreach ($paras as $p) $h .= '<p style="font-size:14px;line-height:1.6;margin:0 0 14px">' . $e($p) . '</p>';
    if ($btnUrl !== '') {
        $h .= '<p style="margin:20px 0 22px"><a href="' . $e($btnUrl) . '" style="display:inline-block;background:#140383;color:#ffffff;text-decoration:none;font-weight:bold;font-size:14px;padding:12px 22px;border-radius:9px">' . $e($btnText) . '</a></p>'
            . '<p style="font-size:12px;color:#6b6b82;line-height:1.5;margin:0 0 14px">Tombol tidak bisa diklik? Salin tautan ini ke browser:<br><span style="word-break:break-all">' . $e($btnUrl) . '</span></p>';
    }
    if ($foot !== '') $h .= '<p style="font-size:12px;color:#6b6b82;line-height:1.5;margin:18px 0 14px;border-top:1px solid #e6e6ef;padding-top:14px">' . $e($foot) . '</p>';
    return $h . '</td></tr></table></td></tr></table></body></html>';
}
function deiWibNow() {
    $bln = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
    $w = time() + 7 * 3600;
    return gmdate('j', $w) . ' ' . $bln[(int)gmdate('n', $w)] . ' ' . gmdate('Y H:i', $w) . ' WIB';
}
function deiPwResetMail($u, $to, $link, $ip) {
    $brand = deiBrandProduct(); $biz = deiTenantName(getSettings());
    $nm = trim((string)($u['name'] ?? '')) ?: (string)$u['username'];
    $subject = 'Reset password ' . $brand . ($biz !== $brand ? ' — ' . $biz : '');
    $p = ['Halo ' . $nm . ',',
          'Kami menerima permintaan untuk mengatur ulang password akun "' . $u['username'] . '" di dashboard ' . $brand . ($biz !== $brand ? ' (' . $biz . ')' : '') . '.',
          'Klik tombol di bawah untuk membuat password baru. Tautan berlaku 30 menit dan hanya bisa dipakai sekali.'];
    $foot = 'Tidak merasa meminta reset password? Abaikan email ini — password Anda tidak berubah. Permintaan dari IP ' . $ip . ' · ' . deiWibNow() . '.';
    $text = implode("\n\n", $p) . "\n\n" . $link . "\n\n" . $foot . "\n\n— " . $brand . "\n";
    return deiSendMail($to, $subject, $text, deiMailHtml('Reset password', $p, 'Buat password baru', $link, $foot), 'pw_reset');
}
function deiPwChangedMail($u, $to, $ip) {
    $brand = deiBrandProduct(); $biz = deiTenantName(getSettings());
    $nm = trim((string)($u['name'] ?? '')) ?: (string)$u['username'];
    $p = ['Halo ' . $nm . ',',
          'Password akun "' . $u['username'] . '" di dashboard ' . $brand . ($biz !== $brand ? ' (' . $biz . ')' : '') . ' baru saja diganti lewat tautan reset password (' . deiWibNow() . ', IP ' . $ip . '). Semua sesi login lama sudah dikeluarkan.',
          'Jika bukan Anda yang melakukannya, segera hubungi Admin atau Super Admin akun Anda.'];
    $text = implode("\n\n", $p) . "\n\n— " . $brand . "\n";
    return deiSendMail($to, 'Password Anda telah diganti — ' . $brand, $text, deiMailHtml('Password telah diganti', $p), 'pw_changed');
}
// Token sesi yang terbit sebelum password diganti tidak berlaku lagi.
function deiTokenBeforePwChange($u) {
    $at = (int)($u['pw_changed_at'] ?? 0);
    if ($at <= 0) return false;
    $parts = explode('.', (string)requestToken());
    if (count($parts) !== 4) return false;
    return (int)@hexdec($parts[1]) < $at;
}

