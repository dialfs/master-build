<?php
/**
 * v1.2.185: master-grup — Dashboard Grup (satu login klien grup untuk beberapa tenant).
 *
 * Data  : data/groups.json
 *   [{ id, name, tenant_ids[], created,
 *      users: [{ id, email, name, role: manager|viewer, tenants[] (kosong = semua tenant grup),
 *                map: {tenant_id: username di tenant}, password, pw_changed_at, disabled, last_login }] }]
 * Login : /grup/ — token sendiri (HMAC secret pusat + '|grp'), terpisah dari admin pusat.
 * Data tenant ditarik server-ke-server (X-Tenant-Id + X-License-Key) — action tenant grp_report / grp_users (v1.2.185+).
 * Pindah tenant: token SSO sekali pakai (suSsoToken + penanda grup) -> tenant sso_login.
 */

define('GROUPS_FILE',    DATA_DIR . '/groups.json');
define('GRP_RESET_FILE', DATA_DIR . '/group-resets.json');
define('GRP_RL_FILE',    DATA_DIR . '/group-login-rl.json');
define('GRP_MAX_TENANTS', 10);
define('GRP_TOKEN_IDLE', 12 * 3600);
define('GRP_TOKEN_MAX',  14 * 86400);
define('GRP_MIN_VER',    'v1.2.185');

function grpAll(): array { $g = readJson(GROUPS_FILE, []); return is_array($g) ? array_values($g) : []; }
function grpSaveAll(array $g): void { writeJson(GROUPS_FILE, array_values($g)); }
function grpId(string $p): string { return $p . bin2hex(random_bytes(5)); }
function grpEmail($e): string {
    $e = strtolower(trim((string)$e));
    return ($e !== '' && strlen($e) <= 190 && !preg_match('/[\r\n,;\s]/', $e) && filter_var($e, FILTER_VALIDATE_EMAIL)) ? $e : '';
}
function grpTenantsById(): array {
    $o = [];
    foreach (readJson(TENANTS_FILE, []) as $t) if (is_array($t) && !empty($t['tenant_id'])) $o[tidNorm((string)$t['tenant_id'])] = $t;
    return $o;
}
/** Cari user grup berdasarkan email: [indexGrup, indexUser] atau null. */
function grpFindUser(array $groups, string $email): ?array {
    foreach ($groups as $gi => $g) foreach ((array)($g['users'] ?? []) as $ui => $u) {
        if (strtolower((string)($u['email'] ?? '')) === $email) return [$gi, $ui];
    }
    return null;
}
function grpPwOk(string $pw): string {
    if (strlen($pw) < 8) return 'Password minimal 8 karakter.';
    if (!preg_match('/[A-Za-z]/', $pw) || !preg_match('/[0-9]/', $pw)) return 'Password harus berisi huruf dan angka.';
    return '';
}
/** Tenant yang boleh dilihat user (irisan tenant grup & batasan user). */
function grpUserTenantIds(array $g, array $u): array {
    $all = array_values(array_map('tidNorm', array_map('strval', (array)($g['tenant_ids'] ?? []))));
    $lim = array_values(array_filter(array_map('tidNorm', array_map('strval', (array)($u['tenants'] ?? [])))));
    return $lim ? array_values(array_intersect($all, $lim)) : $all;
}
function grpUserPublic(array $u): array {
    return ['id' => (string)($u['id'] ?? ''), 'email' => (string)($u['email'] ?? ''), 'name' => (string)($u['name'] ?? ''),
            'role' => (string)($u['role'] ?? 'manager'), 'tenants' => array_values((array)($u['tenants'] ?? [])),
            'map' => (object)((array)($u['map'] ?? [])), 'disabled' => !empty($u['disabled']),
            'has_password' => !empty($u['password']), 'last_login' => (string)($u['last_login'] ?? '')];
}

/* ---------- token login grup ---------- */
function grpSecret(): string { return getSecret() . '|grp'; }
function grpMakeToken(string $email, ?int $iss = null): string {
    $u = rtrim(strtr(base64_encode($email), '+/', '-_'), '=');
    $now = time(); $i = dechex($iss ?? $now); $s = dechex($now);
    return "g.$u.$i.$s." . hash_hmac('sha256', "g|$u|$i|$s", grpSecret());
}
/** Mengembalikan [gi, ui, group, user] atau kirim 401. */
function grpRequire(): array {
    $tok = (string)($_SERVER['HTTP_X_GRP_TOKEN'] ?? '');
    $p = explode('.', $tok);
    $bad = function () { jsonOut(['ok' => false, 'error' => 'Sesi berakhir. Silakan login kembali.'], 401); };
    if (count($p) !== 5 || $p[0] !== 'g') $bad();
    [, $u, $i, $s, $sig] = $p;
    if (!hash_equals(hash_hmac('sha256', "g|$u|$i|$s", grpSecret()), $sig)) $bad();
    $iss = (int)@hexdec($i); $seen = (int)@hexdec($s); $now = time();
    if ($iss <= 0 || $seen <= 0 || $now - $seen > GRP_TOKEN_IDLE || $now - $iss > GRP_TOKEN_MAX) $bad();
    $email = strtolower((string)base64_decode(strtr($u, '-_', '+/')));
    $groups = grpAll();
    $f = $email !== '' ? grpFindUser($groups, $email) : null;
    if (!$f) $bad();
    [$gi, $ui] = $f; $g = $groups[$gi]; $usr = $g['users'][$ui];
    if (!empty($usr['disabled'])) jsonOut(['ok' => false, 'error' => 'Akun Anda dinonaktifkan. Hubungi DEI.'], 401);
    if ((int)($usr['pw_changed_at'] ?? 0) > $iss) $bad();   // password diganti -> sesi lama gugur
    if (!headers_sent()) header('X-Grp-Refresh: ' . grpMakeToken($email, $iss));
    return [$gi, $ui, $g, $usr];
}

/* ---------- batas percobaan login ---------- */
function grpRlKey(string $email): string { return md5(strtolower($email) . '|' . (string)($_SERVER['REMOTE_ADDR'] ?? '')); }
function grpRlBlocked(string $email): bool {
    $rows = readJson(GRP_RL_FILE, []); $k = grpRlKey($email); $now = time();
    $n = 0; foreach ((array)($rows[$k] ?? []) as $t) if ((int)$t > $now - 900) $n++;
    return $n >= 8;
}
function grpRlFail(string $email): void {
    $rows = readJson(GRP_RL_FILE, []); if (!is_array($rows)) $rows = [];
    $now = time(); $k = grpRlKey($email);
    foreach ($rows as $kk => $ts) { $rows[$kk] = array_values(array_filter((array)$ts, function ($t) use ($now) { return (int)$t > $now - 900; })); if (!$rows[$kk]) unset($rows[$kk]); }
    $rows[$k][] = $now;
    writeJson(GRP_RL_FILE, $rows);
}
function grpRlClear(string $email): void { $rows = readJson(GRP_RL_FILE, []); unset($rows[grpRlKey($email)]); writeJson(GRP_RL_FILE, $rows); }

/* ---------- email ---------- */
function grpMail(string $to, string $subject, string $text, string $html = ''): bool {
    if (!function_exists('mail')) return false;
    $from = 'noreply@deintegra.com'; $b = 'dei-' . bin2hex(random_bytes(8));
    $hdr = 'From: =?UTF-8?B?' . base64_encode('DEI Chatbot') . '?= <' . $from . ">\r\n"
         . "MIME-Version: 1.0\r\n"
         . 'Message-ID: <' . bin2hex(random_bytes(12)) . "@deintegra.com>\r\n"
         . "Auto-Submitted: auto-generated\r\n"
         . 'Content-Type: multipart/alternative; boundary="' . $b . '"';
    $mb = "--$b\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($text))
        . ($html !== '' ? "--$b\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($html)) : '')
        . "--$b--\r\n";
    $subj = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $ok = @mail($to, $subj, $mb, $hdr, '-f' . $from);
    if (!$ok) $ok = @mail($to, $subj, $mb, $hdr);
    $lf = DATA_DIR . '/mail-log.json'; $log = readJson($lf, []); if (!is_array($log)) $log = [];
    $at = strpos($to, '@'); $mask = substr($to, 0, min(2, (int)$at)) . str_repeat('*', max(1, (int)$at - 2)) . substr($to, (int)$at);
    array_unshift($log, ['ts' => wibDate('Y-m-d H:i:s'), 'tid' => 'grup', 'kind' => 'grp', 'to' => $mask, 'ok' => $ok, 'via' => 'grup']);
    writeJson($lf, array_slice($log, 0, 500));
    return $ok;
}
function grpBaseUrl(): string { return publicUrlBase() . '/grup/'; }
/** Buat tautan atur/reset password (30 menit, sekali pakai; undangan: 3 hari). */
function grpResetLink(string $email, int $ttl = 1800): string {
    $tok = bin2hex(random_bytes(24)); $now = time();
    $rows = array_filter((array)readJson(GRP_RESET_FILE, []), function ($r) use ($now) { return is_array($r) && (int)($r['exp'] ?? 0) > $now; });
    $rows[hash('sha256', $tok)] = ['email' => $email, 'exp' => $now + $ttl];
    writeJson(GRP_RESET_FILE, $rows);
    return grpBaseUrl() . '#reset=' . $tok;
}
function grpResetLookup(string $tok, bool $consume): ?string {
    $tok = preg_replace('/[^a-f0-9]/', '', $tok);
    if (strlen($tok) !== 48) return null;
    $rows = (array)readJson(GRP_RESET_FILE, []); $k = hash('sha256', $tok);
    $r = $rows[$k] ?? null;
    if (!is_array($r) || (int)($r['exp'] ?? 0) < time()) return null;
    if ($consume) { unset($rows[$k]); writeJson(GRP_RESET_FILE, $rows); }
    return (string)$r['email'];
}
function grpSendLink(array $g, array $u, bool $invite): bool {
    $email = (string)$u['email'];
    $link = grpResetLink($email, $invite ? 3 * 86400 : 1800);
    $nm = (string)($u['name'] ?? '') ?: $email; $gn = (string)($g['name'] ?? 'Grup');
    if ($invite) {
        $subj = 'Undangan Dashboard Grup ' . $gn . ' — DEI Chatbot';
        $txt = "Halo $nm,\n\nAnda diundang ke Dashboard Grup \"$gn\" (DEI Chatbot): satu login untuk melihat laporan gabungan dan membuka dashboard semua tenant grup.\n\nBuat password Anda (tautan berlaku 3 hari, sekali pakai):\n$link\n\nSetelah itu, login di " . grpBaseUrl() . " dengan email $email.\n\n— DEI Chatbot";
    } else {
        $subj = 'Reset password Dashboard Grup — DEI Chatbot';
        $txt = "Halo $nm,\n\nKami menerima permintaan reset password Dashboard Grup \"$gn\".\n\nBuat password baru (berlaku 30 menit, sekali pakai):\n$link\n\nAbaikan email ini bila Anda tidak memintanya.\n\n— DEI Chatbot";
    }
    $e = function ($x) { return htmlspecialchars((string)$x, ENT_QUOTES, 'UTF-8'); };
    $btn = '<p><a href="' . $e($link) . '" style="display:inline-block;background:#140383;color:#fff;padding:10px 16px;border-radius:7px;text-decoration:none">' . ($invite ? 'Buat password' : 'Buat password baru') . '</a></p>';
    $html = '<div style="font-family:Arial,sans-serif;font-size:14px;color:#1a1a2e;max-width:520px"><p>Halo ' . $e($nm) . ',</p>'
          . ($invite
              ? '<p>Anda diundang ke <b>Dashboard Grup &quot;' . $e($gn) . '&quot;</b> (DEI Chatbot): satu login untuk melihat laporan gabungan dan membuka dashboard semua tenant grup.</p>' . $btn
                . '<p style="color:#5d6479;font-size:12px">Tautan berlaku 3 hari, sekali pakai. Setelah itu login di <a href="' . $e(grpBaseUrl()) . '">' . $e(grpBaseUrl()) . '</a> dengan email ' . $e($email) . '.</p>'
              : '<p>Kami menerima permintaan reset password Dashboard Grup &quot;' . $e($gn) . '&quot;.</p>' . $btn
                . '<p style="color:#5d6479;font-size:12px">Tautan berlaku 30 menit, sekali pakai. Abaikan email ini bila Anda tidak memintanya.</p>')
          . '<p>— DEI Chatbot</p></div>';
    return grpMail($email, $subj, $txt, $html);
}

/* ---------- panggilan ke tenant ---------- */
function grpTenantApi(array $t): string { return trim((string)($t['api_url'] ?? '')); }
/** GET paralel ke beberapa tenant. $jobs: [key => [tenant, action, query[]]]. Hasil: [key => json|error]. */
function grpFetchMulti(array $jobs, int $timeout = 25): array {
    $mh = curl_multi_init(); $hs = []; $out = [];
    foreach ($jobs as $k => [$t, $action, $q]) {
        $api = grpTenantApi($t);
        if ($api === '') { $out[$k] = ['ok' => false, 'error' => 'URL API tenant belum diisi di Admin Pusat.']; continue; }
        $url = puUrl($api, $action) . ($q ? '&' . http_build_query($q) : '');
        $ch = curl_init($url);
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => $timeout, CURLOPT_CONNECTTIMEOUT => 8,
            CURLOPT_FOLLOWLOCATION => true, CURLOPT_MAXREDIRS => 2,
            CURLOPT_HTTPHEADER => ['X-Tenant-Id: ' . strtolower((string)$t['tenant_id']), 'X-License-Key: ' . (string)($t['license_key'] ?? ''),
                                   'User-Agent: DEI-Pusat-Grup/1.2.185']]);
        curl_multi_add_handle($mh, $ch); $hs[$k] = $ch;
    }
    do { $st = curl_multi_exec($mh, $run); if ($run) curl_multi_select($mh, 1.0); } while ($run && $st === CURLM_OK);
    foreach ($hs as $k => $ch) {
        $raw = curl_multi_getcontent($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $err = curl_error($ch);
        $j = json_decode((string)$raw, true);
        if (!is_array($j)) $j = ['ok' => false, 'error' => $err !== '' ? $err : ('HTTP ' . $code)];
        elseif (empty($j['ok']) && empty($j['error'])) $j['error'] = 'HTTP ' . $code;
        $j['_http'] = $code;
        $out[$k] = $j;
        curl_multi_remove_handle($mh, $ch); curl_close($ch);
    }
    curl_multi_close($mh);
    return $out;
}
/** Pesan ramah bila tenant belum mendukung action grup. */
function grpVerNote(array $t, array $r): string {
    $e = (string)($r['error'] ?? '');
    $ver = (string)($t['current_version'] ?? '');
    $old = $ver !== '' && function_exists('puVerCmp') && puVerCmp($ver, GRP_MIN_VER) < 0;
    if ($old || stripos($e, 'tidak dikenal') !== false || stripos($e, 'unknown') !== false || (int)($r['_http'] ?? 0) === 404)
        return 'Tenant perlu update ke ' . GRP_MIN_VER . ' atau lebih baru' . ($ver !== '' ? ' (sekarang ' . $ver . ')' : '') . '.';
    return $e !== '' ? $e : 'Gagal mengambil data tenant.';
}
