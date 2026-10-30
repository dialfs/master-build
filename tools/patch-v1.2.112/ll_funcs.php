/* ---------- v1.2.112: login-log ----------
 * Riwayat masuk dasbor: setiap percobaan login (password / tautan pusat), berhasil maupun gagal.
 * data/login-log.json, terbaru di depan, maks LOGIN_LOG_MAX entri & LOGIN_LOG_DAYS hari.
 * Field: t (unix), ts (WIB), u, ok, m (password|sso), r (alasan gagal), ip, dev, ua, name, role, in (akun internal DEI). */
define('LOGIN_LOG_FILE', DATA_DIR . '/login-log.json');
define('LOGIN_LOG_MAX', 3000);
define('LOGIN_LOG_DAYS', 180);

/** Label ringkas perangkat dari User-Agent: "Chrome · Android". */
function deiUaLabel($ua) {
    $ua = (string)$ua;
    if ($ua === '') return '';
    if (preg_match('/curl|python|wget|okhttp|Go-http|bot|spider|httpclient|postman/i', $ua)) return 'Skrip/Bot';
    $b = 'Browser';
    if (strpos($ua, 'Edg/') !== false || strpos($ua, 'EdgA/') !== false) $b = 'Edge';
    elseif (strpos($ua, 'OPR/') !== false || strpos($ua, 'Opera') !== false) $b = 'Opera';
    elseif (strpos($ua, 'SamsungBrowser') !== false) $b = 'Samsung Internet';
    elseif (strpos($ua, 'Firefox/') !== false || strpos($ua, 'FxiOS') !== false) $b = 'Firefox';
    elseif (strpos($ua, 'Chrome/') !== false || strpos($ua, 'CriOS') !== false) $b = 'Chrome';
    elseif (strpos($ua, 'Safari/') !== false) $b = 'Safari';
    $o = '';
    if (strpos($ua, 'Android') !== false) $o = 'Android';
    elseif (preg_match('/iPhone|iPad|iPod/', $ua)) $o = 'iOS';
    elseif (strpos($ua, 'Windows') !== false) $o = 'Windows';
    elseif (strpos($ua, 'CrOS') !== false) $o = 'ChromeOS';
    elseif (preg_match('/Mac OS X|Macintosh/', $ua)) $o = 'macOS';
    elseif (strpos($ua, 'Linux') !== false) $o = 'Linux';
    return $o !== '' ? ($b . ' · ' . $o) : $b;
}

/** Catat satu percobaan login. Tidak pernah menggagalkan proses login. */
function deiLoginLog($username, $ok, $method, $reason = '', $extra = []) {
    try {
        deiWithLock('login-log', function () use ($username, $ok, $method, $reason, $extra) {
            $all = readJson(LOGIN_LOG_FILE, []);
            if (!is_array($all)) $all = [];
            $now = time();
            $ua  = substr((string)($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 300);
            $e = [
                't'   => $now,
                'ts'  => wibDate('Y-m-d H:i:s', $now),
                'u'   => mb_substr(trim((string)$username), 0, 60),
                'ok'  => (bool)$ok,
                'm'   => (string)$method,
                'ip'  => clientIp(),
                'dev' => deiUaLabel($ua),
                'ua'  => $ua,
            ];
            if ($reason !== '') $e['r'] = (string)$reason;
            foreach ((array)$extra as $k => $v) $e[$k] = is_string($v) ? mb_substr($v, 0, 80) : $v;
            array_unshift($all, $e);
            $cut = $now - LOGIN_LOG_DAYS * 86400;
            $all = array_values(array_filter(array_slice($all, 0, LOGIN_LOG_MAX), function ($x) use ($cut) {
                return is_array($x) && (int)($x['t'] ?? 0) >= $cut;
            }));
            writeJson(LOGIN_LOG_FILE, $all);
        });
    } catch (\Throwable $ex) {
        error_log('login-log: ' . $ex->getMessage());
    }
}

/** username => entri login berhasil terakhir. */
function deiLoginLastMap() {
    $m = [];
    foreach ((array)readJson(LOGIN_LOG_FILE, []) as $e) {
        if (!is_array($e) || empty($e['ok'])) continue;
        $u = (string)($e['u'] ?? '');
        if ($u !== '' && !isset($m[$u])) $m[$u] = $e;
    }
    return $m;
}
