<?php
/**
 * v1.2.188: mitra-portal — Portal Mitra (/mitra/): mitra login untuk melihat tenant dan komisinya sendiri.
 *
 * Login : email mitra + password. Token sendiri (HMAC secret pusat + '|mitra', header X-Mitra-Token),
 *         terpisah dari admin pusat dan Dashboard Grup. Password dibuat mitra lewat tautan sekali pakai
 *         (undangan 3 hari dari Admin Pusat, atau "Lupa password" 30 menit).
 * Akses : hanya baca. Mitra melihat tier, tautan pendaftaran, tenant miliknya (nama, paket, status) dan buku
 *         komisinya. Tidak ada akses ke dashboard atau isi chat tenant.
 *
 * v1.2.189: mitra-masuk — admin pusat bisa membuka portal mitra mana pun ("Masuk" di kartu Mitra): token jenis 'a',
 *         sesi pendek (idle 1 jam, maksimal 4 jam), tidak butuh password mitra, tidak bisa mengganti password.
 *
 * Hanya dimuat backend/index.php: memakai getSecret, readJson/writeJson, publicUrlBase, wibDate,
 * grpMail, grpRlBlocked, grpRlFail, grpRlClear, grpEmail, grpPwOk (group-lib.php) dan fungsi pt (partner-lib.php).
 * Fungsi di file ini berawalan ptp.
 */

define('PTP_RESET_FILE', DATA_DIR . '/partner-resets.json');
define('PTP_TOKEN_IDLE', 12 * 3600);
define('PTP_TOKEN_MAX',  14 * 86400);
define('PTP_ADMIN_IDLE', 3600);        // v1.2.189: mitra-masuk
define('PTP_ADMIN_MAX',  4 * 3600);

function ptpBaseUrl(): string { return publicUrlBase() . '/mitra/'; }
function ptpSecret(): string { return getSecret() . '|mitra'; }
function ptpFindByEmail(string $email, ?array $all = null): ?array {
    if ($email === '') return null;
    foreach (($all ?? ptAll()) as $p) if (strtolower((string)($p['email'] ?? '')) === $email) return $p;
    return null;
}

/* ---------- token ---------- */
/** $kind: 'm' = mitra login sendiri, 'a' = admin pusat melihat portal mitra (v1.2.189). */
function ptpMakeToken(string $pid, ?int $iss = null, string $kind = 'm'): string {
    $kind = $kind === 'a' ? 'a' : 'm';
    $now = time(); $i = dechex($iss ?? $now); $s = dechex($now);
    return "$kind.$pid.$i.$s." . hash_hmac('sha256', "$kind|$pid|$i|$s", ptpSecret());
}
/** Mengembalikan data mitra yang sedang login, atau mengirim 401. Sesi admin: kunci `_admin` = true. */
function ptpRequire(): array {
    $p = explode('.', (string)($_SERVER['HTTP_X_MITRA_TOKEN'] ?? ''));
    $bad = function () { jsonOut(['ok' => false, 'error' => 'Sesi berakhir. Silakan login kembali.'], 401); };
    if (count($p) !== 5 || !in_array($p[0], ['m', 'a'], true)) $bad();
    [$kind, $pid, $i, $s, $sig] = $p;
    if (!hash_equals(hash_hmac('sha256', "$kind|$pid|$i|$s", ptpSecret()), $sig)) $bad();
    $iss = (int)@hexdec($i); $seen = (int)@hexdec($s); $now = time();
    if ($kind === 'a') {   // v1.2.189: mitra-masuk — admin pusat, hanya lihat
        if ($iss <= 0 || $seen <= 0 || $now - $seen > PTP_ADMIN_IDLE || $now - $iss > PTP_ADMIN_MAX) $bad();
        $m = ptFind($pid);
        if (!$m) $bad();
        if (!headers_sent()) header('X-Mitra-Refresh: ' . ptpMakeToken($pid, $iss, 'a'));
        $m['_admin'] = true;
        return $m;
    }
    if ($iss <= 0 || $seen <= 0 || $now - $seen > PTP_TOKEN_IDLE || $now - $iss > PTP_TOKEN_MAX) $bad();
    $m = ptFind($pid);
    if (!$m || empty($m['password'])) $bad();
    if (empty($m['active'])) jsonOut(['ok' => false, 'error' => 'Akun mitra Anda dinonaktifkan. Hubungi DEI.'], 401);
    if ((int)($m['pw_changed_at'] ?? 0) > $iss) $bad();   // password diganti -> sesi lama gugur
    if (!headers_sent()) header('X-Mitra-Refresh: ' . ptpMakeToken($pid, $iss));
    return $m;
}

/* ---------- password ---------- */
function ptpUpdate(string $pid, array $set): bool {
    $lk = ptLock(); $all = ptAll(); $ok = false;
    foreach ($all as $i => $p) if (($p['id'] ?? '') === $pid) { $all[$i] = array_merge($p, $set); $ok = ptSaveAll($all); break; }
    ptUnlock($lk);
    return $ok;
}
/** Tautan atur/reset password (30 menit, sekali pakai; undangan: 3 hari). */
function ptpResetLink(string $pid, int $ttl = 1800): string {
    $tok = bin2hex(random_bytes(24)); $now = time();
    $rows = array_filter((array)readJson(PTP_RESET_FILE, []), function ($r) use ($now) { return is_array($r) && (int)($r['exp'] ?? 0) > $now; });
    $rows[hash('sha256', $tok)] = ['pid' => $pid, 'exp' => $now + $ttl];
    writeJson(PTP_RESET_FILE, $rows);
    return ptpBaseUrl() . '#reset=' . $tok;
}
function ptpResetLookup(string $tok, bool $consume): ?string {
    $tok = preg_replace('/[^a-f0-9]/', '', $tok);
    if (strlen($tok) !== 48) return null;
    $rows = (array)readJson(PTP_RESET_FILE, []); $k = hash('sha256', $tok);
    $r = $rows[$k] ?? null;
    if (!is_array($r) || (int)($r['exp'] ?? 0) < time()) return null;
    if ($consume) { unset($rows[$k]); writeJson(PTP_RESET_FILE, $rows); }
    return (string)$r['pid'];
}
function ptpSendLink(array $m, bool $invite): bool {
    $email = (string)($m['email'] ?? '');
    if ($email === '') return false;
    $link = ptpResetLink((string)$m['id'], $invite ? 3 * 86400 : 1800);
    $nm = (string)($m['contact'] ?? '') ?: (string)$m['name'];
    if ($invite) {
        $subj = 'Akses Portal Mitra DEI Chatbot';
        $txt = "Halo $nm,\n\nAkun mitra \"{$m['name']}\" (kode {$m['code']}) sudah aktif. Di Portal Mitra Anda bisa melihat tenant yang mendaftar lewat kode Anda dan komisinya.\n\nBuat password Anda (tautan berlaku 3 hari, sekali pakai):\n$link\n\nSetelah itu, login di " . ptpBaseUrl() . " dengan email $email.\n\n— DEI Chatbot";
        $lead = 'Akun mitra <b>&quot;%s&quot;</b> (kode %s) sudah aktif. Di Portal Mitra Anda bisa melihat tenant yang mendaftar lewat kode Anda dan komisinya.';
        $foot = 'Tautan berlaku 3 hari, sekali pakai. Setelah itu login di <a href="%1$s">%1$s</a> dengan email %2$s.';
    } else {
        $subj = 'Reset password Portal Mitra — DEI Chatbot';
        $txt = "Halo $nm,\n\nKami menerima permintaan reset password Portal Mitra untuk \"{$m['name']}\".\n\nBuat password baru (berlaku 30 menit, sekali pakai):\n$link\n\nAbaikan email ini bila Anda tidak memintanya.\n\n— DEI Chatbot";
        $lead = 'Kami menerima permintaan reset password Portal Mitra untuk &quot;%s&quot;.';
        $foot = 'Tautan berlaku 30 menit, sekali pakai. Abaikan email ini bila Anda tidak memintanya.';
    }
    $e = function ($x) { return htmlspecialchars((string)$x, ENT_QUOTES, 'UTF-8'); };
    $html = '<div style="font-family:Arial,sans-serif;font-size:14px;color:#1a1a2e;max-width:520px"><p>Halo ' . $e($nm) . ',</p>'
          . '<p>' . sprintf($lead, $e($m['name']), $e($m['code'])) . '</p>'
          . '<p><a href="' . $e($link) . '" style="display:inline-block;background:#140383;color:#fff;padding:10px 16px;border-radius:7px;text-decoration:none">' . ($invite ? 'Buat password' : 'Buat password baru') . '</a></p>'
          . '<p style="color:#5d6479;font-size:12px">' . sprintf($foot, $e(ptpBaseUrl()), $e($email)) . '</p><p>— DEI Chatbot</p></div>';
    return grpMail($email, $subj, $txt, $html);
}

/* ---------- data untuk portal (hanya milik mitra itu) ---------- */
function ptpView(array $m, array $tenants): array {
    $pid = (string)$m['id']; $cfg = ptCfg(); $r = ptRate($m, $tenants, $cfg); $now = time();
    $led = array_values(array_filter(ptLedger(), function ($e) use ($pid) { return ($e['partner_id'] ?? '') === $pid; }));
    usort($led, function ($a, $b) { return strcmp((string)($b['date'] ?? '') . ($b['created'] ?? ''), (string)($a['date'] ?? '') . ($a['created'] ?? '')); });
    $tn = [];
    foreach (ptTenantsOf($pid, $tenants) as $t) {
        $trial = isTrialTenant($t); $ends = (int)($t['trial']['ends'] ?? 0);
        $tn[] = ['name' => (string)($t['name'] ?? ''), 'tier' => $trial ? 'trial' : strtolower((string)($t['tier'] ?? '')),
                 'status' => ptIsPaying($t) ? 'paying' : ($trial && !empty($t['active']) && ($ends === 0 || $ends > $now) ? 'trial' : 'inactive'),
                 'trial_days' => $trial && $ends > $now ? (int)ceil(($ends - $now) / 86400) : 0,
                 'expires_at' => $trial ? '' : (string)($t['expires_at'] ?? ''), 'since' => substr((string)($t['partner_at'] ?? ($t['created'] ?? '')), 0, 10)];
    }
    usort($tn, function ($a, $b) { return strcmp($b['since'], $a['since']); });
    $rows = array_map(function ($e) {
        return ['date' => (string)($e['date'] ?? ''), 'month' => (string)($e['month'] ?? ''), 'tenant' => (string)($e['tenant_name'] ?? ''),
                'note' => preg_replace('/ · susulan$/', '', (string)($e['note'] ?? '')), 'base' => (int)($e['base'] ?? 0), 'pct' => (int)($e['pct'] ?? 0),
                'amount' => (int)($e['amount'] ?? 0), 'status' => !empty($e['void']) ? 'void' : (!empty($e['paid_out']) ? 'paid' : 'unpaid'),
                'paid_at' => substr((string)($e['paid_out']['at'] ?? ''), 0, 10), 'paid_note' => (string)($e['paid_out']['note'] ?? '')];
    }, $led);
    return ['partner' => array_merge(['name' => (string)$m['name'], 'code' => (string)$m['code'], 'type' => (string)($m['type'] ?? 'reseller'),
                'contact' => (string)($m['contact'] ?? ''), 'email' => (string)($m['email'] ?? ''), 'pct' => $r['pct'], 'paying' => $r['n'], 'next' => $r['next'], 'scheme' => $r['scheme'],   // v1.2.191: mitra-skema
                'link' => ptSignupBase() . '?ref=' . $m['code']], ptTotals($pid, $led)),
            'tiers' => $r['tiers'] ?: $cfg['tiers'], 'referral_pct' => $cfg['referral_pct'], 'referral_months' => $cfg['referral_months'], 'min_payout' => $cfg['min_payout'],
            'trial_days' => (int)(suCfg()['trial_days'] ?? 30), 'month' => ptMonth(), 'tenants' => $tn, 'ledger' => $rows];
}
