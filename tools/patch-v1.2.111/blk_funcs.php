/* ======================================================================
 * v1.2.111: blokir-total — status lisensi 'blocked' (di atas suspended).
 * Seluruh URL tenant (dashboard, login, widget, aset, API) menjawab 403:
 *  - root .htaccess diberi blok RewriteRule ^ - [F] (otomatis, bertanda);
 *  - API menolak semua action kecuali panggilan pusat yang lolos
 *    X-Tenant-Id + X-License-Key (license_push / cron_tick / stats_pull),
 *    supaya pusat tetap bisa MEMBUKA blokir.
 * Efek samping suspended (backup + kosongkan token) ikut berlaku.
 * ==================================================================== */
define('LIC_BLOCK_FLAG', DATA_DIR . '/.dei-blocked');
define('LIC_BLOCK_MARK_A', '# DEI-BLOCKED-START v1.2.111 (otomatis dari lisensi pusat - jangan diedit)');
define('LIC_BLOCK_MARK_B', '# DEI-BLOCKED-END');
function deiLicOff($st) { return $st === 'suspended' || $st === 'blocked'; }
function deiHtaccessBlock($on) {
    $p = dirname(__DIR__) . '/.htaccess';
    $s = is_file($p) ? (string)@file_get_contents($p) : '';
    $has = strpos($s, LIC_BLOCK_MARK_A) !== false;
    if ($on === $has) return true;
    $re = '/' . preg_quote(LIC_BLOCK_MARK_A, '/') . '.*?' . preg_quote(LIC_BLOCK_MARK_B, '/') . '\R?/s';
    $clean = (string)preg_replace($re, '', $s);
    if ($on) $clean = LIC_BLOCK_MARK_A . "\n<IfModule mod_rewrite.c>\nRewriteEngine On\nRewriteRule ^ - [F,L]\n</IfModule>\n" . LIC_BLOCK_MARK_B . "\n" . $clean;
    $perm = is_file($p) ? (@fileperms($p) & 0777) : 0;
    if ($perm && !is_writable($p)) @chmod($p, 0644);   // .htaccess 0444 di sebagian hosting
    $ok = @file_put_contents($p, $clean, LOCK_EX) !== false;
    if ($perm && !($perm & 0200)) @chmod($p, $perm);
    return $ok;
}
function deiSyncBlock($st) {
    $on = ($st === 'blocked');
    if ($on) { if (!is_file(LIC_BLOCK_FLAG)) @file_put_contents(LIC_BLOCK_FLAG, gmdate('c')); }
    elseif (is_file(LIC_BLOCK_FLAG)) @unlink(LIC_BLOCK_FLAG);
    return deiHtaccessBlock($on);
}
function deiBlockedOut() {
    while (ob_get_level()) @ob_end_clean();
    if (!headers_sent()) {
        header_remove();
        http_response_code(403);
        header('Content-Type: text/html; charset=iso-8859-1');
        header('Cache-Control: no-store');
    }
    echo "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\">\n<html><head>\n<title>403 Forbidden</title>\n</head><body>\n<h1>Forbidden</h1>\n<p>You don't have permission to access this resource.</p>\n</body></html>\n";
    exit;
}
function deiCentralAuthOk() {
    $cs = getSettings()['central_server'] ?? [];
    $tidWant = (string)($cs['tenant_id'] ?? ''); $licWant = (string)($cs['license_key'] ?? '');
    if ($tidWant === '' || $licWant === '') return false;
    $tidGot = (string)($_SERVER['HTTP_X_TENANT_ID']   ?? ($_GET['tenant_id']   ?? ''));
    $licGot = (string)($_SERVER['HTTP_X_LICENSE_KEY'] ?? ($_GET['license_key'] ?? ''));
    return hash_equals($tidWant, strtolower(trim($tidGot))) && hash_equals($licWant, trim($licGot));
}
/* Pusat mendorong status lisensi (header X-Dei-License di cron_tick / action license_push).
 * Mengembalikan status yang diterapkan, atau null bila data tidak valid. */
function deiApplyLicensePush($raw, $settings) {
    $j = is_array($raw) ? $raw : json_decode((string)$raw, true);
    if (!is_array($j)) return null;
    $st = strtolower(trim((string)($j['status'] ?? $j['license_status'] ?? '')));
    if (!in_array($st, ['active', 'expired', 'suspended', 'blocked'], true)) return null;
    $msg = trim((string)($j['message'] ?? $j['suspend_message'] ?? ''));
    if ($msg === '') $msg = LIC_DEFAULT_SUSPEND_MSG;
    $old = readJson(LIC_CACHE_FILE, []);
    $exp = (string)($j['expires_at'] ?? ($old['expires_at'] ?? ''));
    $changed = ($old['status'] ?? null) !== $st || ($old['message'] ?? '') !== $msg || ($old['expires_at'] ?? '') !== $exp;
    if ($changed || (time() - (int)($old['cached_at'] ?? 0)) > 3600) {
        writeJson(LIC_CACHE_FILE, ['status' => $st, 'message' => $msg, 'expires_at' => $exp,
            'days_left' => $j['days_left'] ?? ($old['days_left'] ?? null), 'cached_at' => time(), 'source' => 'push']);
    }
    if (!deiLicOff($old['status'] ?? null) && deiLicOff($st)) applyStatusSideEffects($st, $settings);
    $GLOBALS['dei_block_ht'] = deiSyncBlock($st);
    return $st;
}

/* Penjaga: tenant diblokir -> semua request ditolak 403 (kecuali pusat yang sah). */
if (PHP_SAPI !== 'cli' && is_file(LIC_BLOCK_FLAG)) {
    if (!(in_array($action, ['license_push', 'cron_tick', 'stats_pull'], true) && deiCentralAuthOk())) {
        // cek ulang ke pusat maks. tiap 10 menit -> blokir terbuka sendiri bila pusat sudah mengaktifkan lagi
        if (time() - (int)@filemtime(LIC_BLOCK_FLAG) > 600) {
            @touch(LIC_BLOCK_FLAG);
            try { getLicenseStatus(getSettings(), true); } catch (\Throwable $e) {}
        }
        if (is_file(LIC_BLOCK_FLAG)) { deiHtaccessBlock(true); deiBlockedOut(); }
    }
}

