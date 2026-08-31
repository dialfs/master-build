<?php
/**
 * DEI AI Chat Widget — Unified API
 * Single endpoint: api/index.php?action=<action>
 * Flat-file JSON storage. No database required. PHP 7.4+.
 */

date_default_timezone_set('Asia/Jakarta');
// v1.2.43: versi yang TERTANAM di berkas ini. Nilainya disuntik otomatis
// oleh skrip build saat mengemas master ZIP. Berbeda dari version.json yang
// ditulis updater, konstanta ini tidak bisa berbohong: ia bagian dari berkas
// yang diganti. Kalau update gagal dan berkas tidak terganti, nilainya tetap
// lama -- itulah cara kita mendeteksi update gagal senyap.
// Nilai 'dev' berarti berkas ini sumber yang dipatch manual (deintegra),
// bukan hasil pemasangan dari rilis -- itu jujur, bukan tanda masalah.
define('DEI_VERSION', 'v1.2.44');
error_reporting(E_ALL & ~E_NOTICE & ~E_WARNING & ~E_DEPRECATED);

define('DATA_DIR', __DIR__ . '/../data');
define('SETTINGS_FILE', DATA_DIR . '/settings.json');
define('USERS_FILE', DATA_DIR . '/users.json');
define('KB_FILE', DATA_DIR . '/knowledge-base.json');
define('LOG_FILE', DATA_DIR . '/chatbot-log.json');
define('PUSH_CATEGORIES_FILE', DATA_DIR . '/push-categories.json');  // v1.2.13: kategori custom (file sendiri, bukan settings)
define('CONTACTS_FILE', DATA_DIR . '/wa-contacts.json');  // v1.2.19: nama kontak WA (file sendiri — log dipangkas log_limit)
define('LEADS_FILE', DATA_DIR . '/leads.json');           // v1.2.20: kartu lead hasil analisa AI
define('PRICELIST_FILE', DATA_DIR . '/pricelist.json');   // v1.2.22: daftar harga resmi (terpisah dari KB)
define('GAPS_DISMISSED_FILE', DATA_DIR . '/kb-gaps-dismissed.json');  // v1.2.25: pertanyaan yang disembunyikan
define('LEAD_TRIGGER_MSGS', 8);                            // v1.2.20: analisa saat percakapan mencapai N pesan
define('RATELIMIT_FILE', DATA_DIR . '/ratelimit.json');
define('SECRET_FILE', DATA_DIR . '/.secret.php');
define('WA_SESSIONS_DIR', DATA_DIR . '/wa-sessions');
define('WA_MODES_FILE', DATA_DIR . '/wa-modes.json');

/* ----------------------------------------------------------------------------
 *  CORS — the widget runs on the client's site (loaded via GTM) so public
 *  endpoints must allow cross-origin requests.
 * ------------------------------------------------------------------------- */
$PUBLIC_ACTIONS = ['bootstrap', 'chat'];
$action = isset($_GET['action']) ? $_GET['action'] : '';

if (in_array($action, $PUBLIC_ACTIONS, true)) {
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, X-Auth-Token');
    header('Access-Control-Expose-Headers: X-Auth-Refresh');  // fix auto sign out: biar JS bisa baca token refresh
}
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

/* ----------------------------------------------------------------------------
 *  Helpers
 * ------------------------------------------------------------------------- */
function jsonOut($arr, $code = 200) {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($arr, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function readJson($file, $fallback) {
    if (!file_exists($file)) return $fallback;
    $raw = file_get_contents($file);
    $data = json_decode($raw, true);
    return ($data === null) ? $fallback : $data;
}

function writeJson($file, $data) {
    $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
    // v1.2.40 LUBANG 1: json_encode() bisa gagal dan mengembalikan false --
    // paling sering karena ada byte UTF-8 tidak valid (pesan WhatsApp, nama
    // kontak, emoji terpotong). Versi lama melewatkan false itu ke
    // file_put_contents, yang menuliskannya sebagai STRING KOSONG: isi file
    // hilang total, tapi fungsinya tetap melaporkan sukses. Sekarang: jangan
    // tulis apa pun, catat sebabnya, biarkan berkas lama utuh.
    if ($json === false) {
        error_log('writeJson: json_encode GAGAL untuk ' . $file . ' -- ' . json_last_error_msg() . ' (berkas lama dibiarkan utuh)');
        return false;
    }
    // v1.2.40 LUBANG 2: file_put_contents memotong berkas dulu baru menulis,
    // jadi kalau proses mati di tengah jalan (timeout/fatal/memory limit)
    // yang tersisa berkas separuh. Tulis ke berkas sementara di direktori
    // yang SAMA lalu rename() -- rename dalam satu filesystem bersifat
    // atomic: pembaca tidak pernah melihat berkas setengah tertulis, dan
    // kalau gagal sebelum rename, berkas asli tidak tersentuh sama sekali.
    $tmp = $file . '.tmp.' . getmypid() . '.' . mt_rand(1000, 9999);
    if (file_put_contents($tmp, $json, LOCK_EX) === false) {
        @unlink($tmp);
        error_log('writeJson: gagal menulis berkas sementara untuk ' . $file);
        return false;
    }
    // pertahankan hak akses seperti berkas aslinya
    if (file_exists($file)) {
        $perm = @fileperms($file);
        if ($perm !== false) @chmod($tmp, $perm & 0777);
    }
    if (!@rename($tmp, $file)) {
        @unlink($tmp);
        error_log('writeJson: rename gagal untuk ' . $file);
        return false;
    }
    return true;
}

// v1.2.41: cari folder di dalam hasil ekstrak ZIP yang benar-benar berisi
// api/index.php. Tidak lagi hardcode nama folder -- 'dei-chatbot-ai' dan
// 'dei-update' cuma tebakan pertama supaya cepat. Kalau kemasan ZIP berubah
// lagi di masa depan, ini tetap menemukannya asal strukturnya tidak lebih
// dalam dari satu tingkat.
function deiCariRootPayload($tmpDir) {
    $penanda = '/api/index.php';
    if (file_exists($tmpDir . $penanda)) return $tmpDir;
    foreach (['dei-chatbot-ai', 'dei-update'] as $tebak) {
        if (file_exists($tmpDir . '/' . $tebak . $penanda)) return $tmpDir . '/' . $tebak;
    }
    $anak = @scandir($tmpDir);
    if (is_array($anak)) {
        foreach ($anak as $c) {
            if ($c === '.' || $c === '..') continue;
            $p = $tmpDir . '/' . $c;
            if (is_dir($p) && file_exists($p . $penanda)) return $p;
        }
    }
    return null;
}

function bodyInput() {
    $raw = file_get_contents('php://input');
    $data = json_decode($raw, true);
    return is_array($data) ? $data : [];
}

function clientIp() {
    foreach (['HTTP_CF_CONNECTING_IP', 'HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR'] as $k) {
        if (!empty($_SERVER[$k])) {
            $ip = trim(explode(',', $_SERVER[$k])[0]);
            if (filter_var($ip, FILTER_VALIDATE_IP)) return $ip;
        }
    }
    return '0.0.0.0';
}

/* ----------------------------------------------------------------------------
 *  Secret key (auto-generated, stored as PHP so it is never served as text)
 * ------------------------------------------------------------------------- */
function getSecret() {
    if (file_exists(SECRET_FILE)) {
        $s = @include SECRET_FILE;
        if (is_string($s) && strlen($s) >= 32) return $s;
    }
    $s = bin2hex(random_bytes(32));
    @file_put_contents(SECRET_FILE, "<?php return '" . $s . "';\n", LOCK_EX);
    return $s;
}

/* ----------------------------------------------------------------------------
 *  Auth — stateless token with idle + absolute expiry
 *  Format: base64url(username) . hex(issued_at) . hex(last_seen) . hmac
 * ------------------------------------------------------------------------- */
define('TOKEN_IDLE_SEC', 28800);         // 8 jam tanpa aktivitas (fix auto sign out)
define('TOKEN_MAX_SEC',  7 * 86400);     // 7 hari maksimum sejak login

function makeToken($username) {
    $secret = getSecret();
    $u = rtrim(strtr(base64_encode($username), '+/', '-_'), '=');
    $now = time();
    $iss = dechex($now);
    $seen = dechex($now);
    $sig = hash_hmac('sha256', "$u|$iss|$seen", $secret);
    return "$u.$iss.$seen.$sig";
}

/**
 * Returns the username for a still-valid token, or null.
 * Updates last_seen by issuing a fresh token via setTokenRefreshHeader().
 */
function tokenUsername($token) {
    if (!$token || substr_count($token, '.') !== 3) return null;
    list($u, $iss, $seen, $sig) = explode('.', $token, 4);
    $secret = getSecret();
    $expected = hash_hmac('sha256', "$u|$iss|$seen", $secret);
    if (!hash_equals($expected, $sig)) return null;
    $issued = @hexdec($iss);
    $lastSeen = @hexdec($seen);
    $now = time();
    if ($issued <= 0 || $lastSeen <= 0) return null;
    if (($now - $lastSeen) > TOKEN_IDLE_SEC) return null;          // idle expired
    if (($now - $issued)   > TOKEN_MAX_SEC)  return null;          // absolute expired
    $username = base64_decode(strtr($u, '-_', '+/'));
    if (!$username) return null;
    // Hand a refreshed token back via response header so the client can rotate.
    if (!headers_sent()) {
        $newSeen = dechex($now);
        $newSig = hash_hmac('sha256', "$u|$iss|$newSeen", $secret);
        header('X-Auth-Refresh: ' . "$u.$iss.$newSeen.$newSig");
    }
    return $username;
}

function requestToken() {
    if (!empty($_SERVER['HTTP_X_AUTH_TOKEN'])) return $_SERVER['HTTP_X_AUTH_TOKEN'];
    if (!empty($_SERVER['HTTP_AUTHORIZATION'])) {
        return trim(str_ireplace('Bearer', '', $_SERVER['HTTP_AUTHORIZATION']));
    }
    if (!empty($_GET['token'])) return $_GET['token'];
    $b = bodyInput();
    if (!empty($b['token'])) return $b['token'];
    return null;
}

define('LOCKOUT_FILE', DATA_DIR . '/lockout.json');
define('LOCKOUT_MAX_TRIES', 5);
define('LOCKOUT_WINDOW_SEC', 15 * 60);

/** Read lockout map; expire entries past window automatically. */
function lockoutRead() {
    $m = readJson(LOCKOUT_FILE, []);
    $now = time();
    $changed = false;
    foreach ($m as $k => $row) {
        $until = $row['locked_until'] ?? 0;
        $last = $row['last_try'] ?? 0;
        if ($until <= $now && ($now - $last) > LOCKOUT_WINDOW_SEC) {
            unset($m[$k]); $changed = true;
        }
    }
    if ($changed) writeJson(LOCKOUT_FILE, $m);
    return $m;
}
function lockoutKey($username) { return strtolower(trim($username)); }
function lockoutCheck($username) {
    $m = lockoutRead();
    $k = lockoutKey($username);
    if (!isset($m[$k])) return 0;
    $until = (int)($m[$k]['locked_until'] ?? 0);
    return ($until > time()) ? $until - time() : 0;
}
function lockoutRecordFail($username) {
    $m = lockoutRead();
    $k = lockoutKey($username);
    $now = time();
    $tries = (int)($m[$k]['tries'] ?? 0);
    // reset counter if no failure within window
    if (!empty($m[$k]['last_try']) && ($now - (int)$m[$k]['last_try']) > LOCKOUT_WINDOW_SEC) {
        $tries = 0;
    }
    $tries++;
    $row = ['tries' => $tries, 'last_try' => $now];
    if ($tries >= LOCKOUT_MAX_TRIES) {
        $row['locked_until'] = $now + LOCKOUT_WINDOW_SEC;
        $row['tries'] = 0;   // reset counter after locking
    }
    $m[$k] = $row;
    writeJson(LOCKOUT_FILE, $m);
}
function lockoutClear($username) {
    $m = lockoutRead();
    $k = lockoutKey($username);
    if (isset($m[$k])) { unset($m[$k]); writeJson(LOCKOUT_FILE, $m); }
}

/** Returns null if OK, or an error string explaining why password is too weak. */
function checkPasswordStrength($pw) {
    $pw = (string)$pw;
    if (strlen($pw) < 8) return 'Password minimal 8 karakter.';
    if (!preg_match('/[a-z]/', $pw)) return 'Password harus mengandung huruf kecil.';
    if (!preg_match('/[A-Z]/', $pw)) return 'Password harus mengandung huruf besar.';
    if (!preg_match('/[0-9]/', $pw)) return 'Password harus mengandung angka.';
    return null;
}

/** Returns the authenticated user array or sends 401. */
/* v1.2.4: silent auth for admin test chatbot bypass — mirror requireAuth tapi return null (no exit) */
function getAuthenticatedUserSilent() {
    $username = tokenUsername(requestToken());
    if (!$username) return null;
    $users = readJson(USERS_FILE, []);
    foreach ($users as $u) {
        if (isset($u['username']) && $u['username'] === $username) {
            $role = $u['role'] ?? 'admin';
            // Apply same role migration as requireAuth (in-memory only, no write)
            if ($role === 'admin' && empty($u['migrated_3role'])) $role = 'super_admin';
            elseif ($role === 'editor' && empty($u['migrated_3role'])) $role = 'admin';
            $u['role'] = $role;
            return $u;
        }
    }
    return null;
}
// === /v1.2.4 silent auth ===

function requireAuth($roles = null) {
    $username = tokenUsername(requestToken());
    if (!$username) jsonOut(['ok' => false, 'error' => 'Tidak terautentikasi. Silakan login kembali.'], 401);
    $users = readJson(USERS_FILE, []);
    $changed = false;
    foreach ($users as $idx => $u) {
        if (isset($u['username']) && $u['username'] === $username) {
            // Migrate legacy roles: 'admin' (akses penuh lama) -> 'super_admin'; 'editor' -> 'admin'
            $role = $u['role'] ?? 'admin';
            if ($role === 'admin' && empty($u['migrated_3role'])) {
                $users[$idx]['role'] = 'super_admin';
                $users[$idx]['migrated_3role'] = true;
                $role = 'super_admin';
                $changed = true;
            } elseif ($role === 'editor' && empty($u['migrated_3role'])) {
                $users[$idx]['role'] = 'admin';
                $users[$idx]['migrated_3role'] = true;
                $role = 'admin';
                $changed = true;
            }
            if ($changed) writeJson(USERS_FILE, $users);
            $u['role'] = $role;
            if ($roles !== null && !in_array($role, (array)$roles, true)) {
                jsonOut(['ok' => false, 'error' => 'Akses ditolak untuk peran Anda.'], 403);
            }
            return $u;
        }
    }
    jsonOut(['ok' => false, 'error' => 'Pengguna tidak ditemukan.'], 401);
}

/** Allowed roles for masking-aware settings save (mirrors get_settings). */
function roleCanEditSecrets($role)   { return $role === 'super_admin'; }
function roleCanEditApiBlock($role)  { return $role === 'super_admin'; }   // Claude API block
function roleCanEditWaBlock($role)   { return $role === 'super_admin'; }   // WhatsApp API + config
function roleCanEditTelegram($role)  { return $role === 'super_admin'; }
function roleCanEditBotPersona($role){ return in_array($role, ['super_admin', 'admin'], true); }
function roleCanEditWidget($role)    { return in_array($role, ['super_admin', 'admin'], true); }   // toggles, branding (non-secret)
function roleCanEditHandoff($role)   { return in_array($role, ['super_admin', 'admin'], true); }

/* ----------------------------------------------------------------------------
 *  Settings — never leak the raw API key to clients
 * ------------------------------------------------------------------------- */
function getSettings() {
    return readJson(SETTINGS_FILE, []);
}

function maskKey($key) {
    if (!$key) return '';
    $len = strlen($key);
    if ($len <= 8) return str_repeat('•', $len);
    return substr($key, 0, 6) . str_repeat('•', 8) . substr($key, -4);
}

/* ----------------------------------------------------------------------------
 *  Knowledge-base relevance search (keyword scoring)
 * ------------------------------------------------------------------------- */
function searchKB($query, $max) {
    $kb = readJson(KB_FILE, []);
    if (!$kb) return [];
    $words = preg_split('/\s+/', mb_strtolower(trim($query)));
    $words = array_filter($words, function ($w) { return mb_strlen($w) >= 3; });
    $scored = [];
    foreach ($kb as $entry) {
        $hay = mb_strtolower(($entry['title'] ?? '') . ' ' . ($entry['category'] ?? '') . ' ' . ($entry['content'] ?? ''));
        $score = 0;
        foreach ($words as $w) {
            $score += substr_count($hay, $w);
        }
        if ($score > 0) $scored[] = ['s' => $score, 'e' => $entry];
    }
    usort($scored, function ($a, $b) { return $b['s'] - $a['s']; });
    $top = array_slice($scored, 0, max(1, (int)$max));
    return array_map(function ($r) { return $r['e']; }, $top);
}

/* ----------------------------------------------------------------------------
 *  Rate limiting — per IP per hour
 * ------------------------------------------------------------------------- */
function checkRateLimit($ip, $limit) {
    $store = readJson(RATELIMIT_FILE, []);
    $now = time();
    // prune entries older than 1 hour
    foreach ($store as $k => $v) {
        if (!is_array($v)) { unset($store[$k]); continue; }
        $store[$k] = array_values(array_filter($v, function ($t) use ($now) { return $t > $now - 3600; }));
        if (empty($store[$k])) unset($store[$k]);
    }
    $count = isset($store[$ip]) ? count($store[$ip]) : 0;
    if ($count >= $limit) {
        writeJson(RATELIMIT_FILE, $store);
        return false;
    }
    $store[$ip][] = $now;
    writeJson(RATELIMIT_FILE, $store);
    return true;
}

/* ----------------------------------------------------------------------------
 *  Call Anthropic API
 * ------------------------------------------------------------------------- */
/* ============================================================
 *  License enforcement (v1.1.3)
 *  Tenant caches license_status from central in license-cache.json
 *  Refreshes lazily: if cache empty or >24h old, fetch from central.
 *  When status changes to 'suspended', backs up + clears tokens.
 *  When status changes back to 'active', requires manual token re-entry.
 * ============================================================ */
define('LIC_CACHE_FILE', DATA_DIR . '/license-cache.json');
define('LIC_CACHE_TTL', 24 * 3600);
define('LIC_DEFAULT_SUSPEND_MSG', 'Maaf, layanan chat sementara tidak tersedia. Silakan hubungi kami melalui kontak yang tersedia.');

/* v1.1.4: WIB helpers — Indonesia UTC+7 */
function wibNow() { return time() + 7 * 3600; }
function wibDate($fmt, $ts = null) { return gmdate($fmt, ($ts ?? time()) + 7 * 3600); }
function wibMonthKey($ts = null) { return wibDate('Y-m', $ts); }
function wibToday($ts = null) { return wibDate('Y-m-d', $ts); }

/* v1.1.4: cap cache + getCapStatus
 * Cap status comes from central via update_check response.
 * Cached 24h. When stale, refreshed lazily on next chat.
 */
define('CAP_CACHE_FILE', DATA_DIR . '/cap-cache.json');
define('CAP_DEFAULT_MSG', 'Maaf, layanan chat sedang sibuk. Silakan hubungi kami melalui kontak yang tersedia.');

function getCapStatus($settings, $forceRefresh = false) {
    $cs = $settings['central_server'] ?? [];
    // No central configured → no cap enforcement
    if (empty($cs['url']) || empty($cs['tenant_id']) || empty($cs['license_key'])) {
        return ['reached' => false, 'warning' => false, 'pct' => 0, 'message' => '', 'source' => 'no-central'];
    }
    $cache = readJson(CAP_CACHE_FILE, []);
    $now = time();
    $age = $now - (int)($cache['cached_at'] ?? 0);
    if (!$forceRefresh && !empty($cache['cached_at']) && $age < 24 * 3600) {
        return [
            'reached' => !empty($cache['reached']),
            'warning' => !empty($cache['warning']),
            'pct'     => (float)($cache['pct'] ?? 0),
            'message' => $cache['message'] ?? '',
            'tier'    => $cache['tier']    ?? '',
            'cap'     => $cache['cap']     ?? 0,
            'used'    => $cache['used']    ?? 0,
            'source'  => 'cache-' . $age . 's',
        ];
    }
    // Stale or missing → refresh by calling update_check (lightweight; same path license uses)
    $stats = computeMonthStats();
    $url = rtrim($cs['url'], '/') . '/backend/index.php?action=check_update';
    $payload = json_encode([
        'tenant_id'   => $cs['tenant_id'],
        'license_key' => $cs['license_key'],
        'current'     => readJson(DATA_DIR . '/version.json', [])['version'] ?? 'v1.1.4',
        'stats'       => $stats,
    ]);
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $payload,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_TIMEOUT => 10,
    ]);
    $resp = curl_exec($ch);
    curl_close($ch);
    if (!$resp) {
        // fail-open with stale cache or default
        if (!empty($cache['cached_at'])) {
            $cache['source'] = 'stale-fallback';
            return $cache;
        }
        return ['reached' => false, 'warning' => false, 'pct' => 0, 'message' => '', 'source' => 'fail-open'];
    }
    $data = json_decode($resp, true) ?: [];
    $cap = $data['cap_info'] ?? null;
    if (!$cap) {
        return ['reached' => false, 'warning' => false, 'pct' => 0, 'message' => '', 'source' => 'no-cap-info'];
    }
    $msg = trim($cap['cap_message'] ?? '');
    if ($msg === '') $msg = CAP_DEFAULT_MSG;
    $newCache = [
        'reached'   => !empty($cap['cap_reached']),
        'warning'   => !empty($cap['cap_warning']),
        'pct'       => (float)($cap['usage_pct'] ?? 0),
        'tier'      => $cap['tier'] ?? '',
        'cap'       => (int)($cap['monthly_chat_cap'] ?? 0),
        'used'      => (int)($cap['chats_this_month'] ?? 0),
        'message'   => $msg,
        'cached_at' => $now,
    ];
    writeJson(CAP_CACHE_FILE, $newCache);
    $newCache['source'] = 'refreshed';
    return $newCache;
}

/* Compute chat count + cost for current WIB month from data/usage.json */
function computeMonthStats() {
    $usage = readJson(DATA_DIR . '/usage.json', []);
    $monthKey = wibDate('Y-m');
    $chats = 0; $cost = 0.0;
    foreach ($usage as $day => $d) {
        if (strpos($day, $monthKey) !== 0) continue;
        $chats += (int)($d['calls'] ?? 0);
        $cost  += ($d['input']      / 1e6 * 1.00)
                + ($d['output']     / 1e6 * 5.00)
                + ($d['cache_write']/ 1e6 * 1.25)
                + ($d['cache_read'] / 1e6 * 0.10);
    }
    return ['chats_this_month' => $chats, 'cost_this_month_usd' => round($cost, 6)];
}

/**
 * Aggregate Claude usage per day into data/usage.json — used for:

/**
 * Returns ['status' => 'active'|'expired'|'suspended', 'message' => string, 'expires_at' => string, 'days_left' => int|null]
 *
 * If central is unreachable AND cache exists, returns stale cache (fail-open behavior — we don't punish tenant for our pusat being down).
 * If central is unreachable AND no cache, returns 'active' (fail-open default).
 */
function getLicenseStatus($settings, $forceRefresh = false) {
    $cs = $settings['central_server'] ?? [];
    // No central configured → no enforcement (e.g. legacy installs)
    if (empty($cs['url']) || empty($cs['tenant_id']) || empty($cs['license_key'])) {
        return ['status' => 'active', 'message' => '', 'expires_at' => '', 'days_left' => null, 'source' => 'no-central'];
    }

    $cache = readJson(LIC_CACHE_FILE, []);
    $now = time();
    $age = $now - (int)($cache['cached_at'] ?? 0);

    if (!$forceRefresh && !empty($cache['status']) && $age < LIC_CACHE_TTL) {
        return [
            'status'     => $cache['status'],
            'message'    => $cache['message']    ?? '',
            'expires_at' => $cache['expires_at'] ?? '',
            'days_left'  => $cache['days_left']  ?? null,
            'source'     => 'cache-' . $age . 's',
        ];
    }

    // Refresh from central
    $url = rtrim($cs['url'], '/') . '/backend/index.php?action=check_update';
    $payload = json_encode([
        'tenant_id'   => $cs['tenant_id'],
        'license_key' => $cs['license_key'],
        'current'     => readJson(DATA_DIR . '/version.json', [])['version'] ?? 'v1.1.3',
    ]);
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
        CURLOPT_TIMEOUT        => 10,
    ]);
    $resp = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($resp === false || $code !== 200) {
        // FAIL-OPEN: use stale cache if any, else default active
        if (!empty($cache['status'])) {
            return [
                'status'     => $cache['status'],
                'message'    => $cache['message']    ?? '',
                'expires_at' => $cache['expires_at'] ?? '',
                'days_left'  => $cache['days_left']  ?? null,
                'source'     => 'stale-fallback',
            ];
        }
        return ['status' => 'active', 'message' => '', 'expires_at' => '', 'days_left' => null, 'source' => 'fail-open'];
    }
    $data = json_decode($resp, true) ?: [];
    if (empty($data['ok'])) {
        // Central explicitly rejected (e.g. tenant tidak terdaftar lagi → treat as suspended)
        $newCache = [
            'status'     => 'suspended',
            'message'    => LIC_DEFAULT_SUSPEND_MSG,
            'expires_at' => '',
            'days_left'  => null,
            'cached_at'  => $now,
            'reason'     => $data['error'] ?? 'rejected',
        ];
        writeJson(LIC_CACHE_FILE, $newCache);
        applyStatusSideEffects('suspended', $settings);
        return $newCache + ['source' => 'rejected'];
    }

    $newStatus = $data['license_status'] ?? 'active';
    $msg = trim($data['suspend_message'] ?? '');
    if ($msg === '') $msg = LIC_DEFAULT_SUSPEND_MSG;

    $newCache = [
        'status'     => $newStatus,
        'message'    => $msg,
        'expires_at' => $data['expires_at'] ?? '',
        'days_left'  => $data['days_left']  ?? null,
        'cached_at'  => $now,
    ];
    // Detect transition (was-active, now-suspended) → backup & clear tokens
    $oldStatus = $cache['status'] ?? null;
    if ($oldStatus !== 'suspended' && $newStatus === 'suspended') {
        applyStatusSideEffects('suspended', $settings);
    }
    writeJson(LIC_CACHE_FILE, $newCache);
    return $newCache + ['source' => 'refreshed'];
}

/**
 * Side-effects of status transitions.
 * Currently only 'suspended' has a side-effect: backup + clear tokens
 * (Claude API key, WA access_token + app_secret, Telegram bot_token).
 *
 * Backup saved to data/settings.json.suspended-backup.<timestamp> for SSH recovery.
 * To unsuspend → super_admin/admin must manually re-enter tokens in dashboard.
 */
function applyStatusSideEffects($newStatus, $settings) {
    if ($newStatus !== 'suspended') return;
    $path = SETTINGS_FILE;
    if (!file_exists($path)) return;
    $current = readJson($path, []);
    // Already cleared? skip.
    $hasToken =
        !empty($current['api']['claude_api_key']) ||
        !empty($current['whatsapp_api']['access_token']) ||
        !empty($current['telegram']['bot_token']);
    if (!$hasToken) return;

    // Backup current settings (with tokens) for SSH recovery
    $stamp = date('Ymd-His');
    @copy($path, $path . '.suspended-backup.' . $stamp);

    // Clear tokens
    if (isset($current['api']['claude_api_key']))        $current['api']['claude_api_key'] = '';
    if (isset($current['api']['key_is_set']))            $current['api']['key_is_set'] = false;
    if (isset($current['whatsapp_api']['access_token'])) $current['whatsapp_api']['access_token'] = '';
    if (isset($current['whatsapp_api']['app_secret']))   $current['whatsapp_api']['app_secret'] = '';
    if (isset($current['telegram']['bot_token']))        $current['telegram']['bot_token'] = '';
    writeJson($path, $current);
}

/**
 * Aggregate Claude usage per day into data/usage.json — used for:
 *  - report-back to central (estimated cost per tenant)
 *  - super_admin dashboard transparency
 *
 * Schema: { "YYYY-MM-DD": { calls, input, output, cache_write, cache_read } }
 * Keeps last 90 days; trims older entries.
 */
function recordUsage($usage) {
    if (!is_array($usage) || !$usage) return;
    $path = DATA_DIR . '/usage.json';
    $all  = readJson($path, []);
    $day  = date('Y-m-d');
    if (!isset($all[$day])) {
        $all[$day] = ['calls' => 0, 'input' => 0, 'output' => 0, 'cache_write' => 0, 'cache_read' => 0];
    }
    $all[$day]['calls']++;
    $all[$day]['input']       += (int)($usage['input_tokens']                ?? 0);
    $all[$day]['output']      += (int)($usage['output_tokens']               ?? 0);
    $all[$day]['cache_write'] += (int)($usage['cache_creation_input_tokens'] ?? 0);
    $all[$day]['cache_read']  += (int)($usage['cache_read_input_tokens']     ?? 0);

    // Keep last 90 days
    if (count($all) > 95) {
        ksort($all);
        $all = array_slice($all, -90, null, true);
    }
    writeJson($path, $all);
}

function callClaude($settings, $systemBlocks, $messages) {
    $key = $settings['api']['claude_api_key'] ?? '';
    if (!$key) return [false, 'API key belum dikonfigurasi di dashboard.', []];

    // $systemBlocks can be a plain string (legacy) or an array of blocks
    // (with optional cache_control on individual blocks for prompt caching).
    $systemParam = is_array($systemBlocks) ? $systemBlocks : (string)$systemBlocks;

    $payload = [
        'model'      => $settings['api']['model'] ?? 'claude-haiku-4-5-20251001',
        'max_tokens' => (int)($settings['api']['max_tokens'] ?? 400),
        'system'     => $systemParam,
        'messages'   => $messages,
    ];

    $ch = curl_init('https://api.anthropic.com/v1/messages');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_TIMEOUT        => 30,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            'x-api-key: ' . $key,
            'anthropic-version: 2023-06-01',
        ],
        CURLOPT_POSTFIELDS     => json_encode($payload, JSON_UNESCAPED_UNICODE),
    ]);
    $res  = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err  = curl_error($ch);
    curl_close($ch);

    if ($res === false) return [false, 'Gagal terhubung ke server AI: ' . $err, []];
    $data = json_decode($res, true);
    if ($code !== 200) {
        $msg = $data['error']['message'] ?? ('HTTP ' . $code);
        return [false, 'AI error: ' . $msg, []];
    }
    $answer = '';
    if (!empty($data['content']) && is_array($data['content'])) {
        foreach ($data['content'] as $block) {
            if (($block['type'] ?? '') === 'text') $answer .= $block['text'];
        }
    }
    // Capture cache usage from response for monitoring/cost transparency
    $usage = [
        'input_tokens'                => (int)($data['usage']['input_tokens']                ?? 0),
        'output_tokens'               => (int)($data['usage']['output_tokens']               ?? 0),
        'cache_creation_input_tokens' => (int)($data['usage']['cache_creation_input_tokens'] ?? 0),
        'cache_read_input_tokens'     => (int)($data['usage']['cache_read_input_tokens']     ?? 0),
    ];
    return [true, trim($answer), $usage];
}

/* ============================================================
 * v1.2.3: Structured prompt builder — merge form fields to prompt prefix.
 * Return empty string if all structured fields are empty (backward compat).
 * ============================================================ */
function buildStructuredPromptPrefix($bot) {
    $parts = [];

    // Identity — skip, already in existing system_prompt (v1.2.3 fix)

    // Languages
    $langs = $bot['languages'] ?? [];
    if (is_array($langs) && count($langs) > 0) {
        $langMap = ['id'=>'Bahasa Indonesia', 'en'=>'English', 'zh'=>'Mandarin', 'ar'=>'Arabic', 'ja'=>'Japanese'];
        $langNames = [];
        foreach ($langs as $l) $langNames[] = $langMap[$l] ?? $l;
        if (count($langNames) > 1) {
            $parts[] = "BAHASA: Anda mendukung " . implode(', ', $langNames) . ".";
            $behavior = $bot['language_prompt_behavior'] ?? 'ask_user';
            if ($behavior === 'ask_user') {
                $parts[] = "Setelah greeting, tanyakan user ingin melanjutkan dalam bahasa apa.";
            } elseif ($behavior === 'auto_detect') {
                $parts[] = "Deteksi bahasa dari pesan user, respond dalam bahasa yang sama.";
            }
        }
    }

    // User address
    $address = trim((string)($bot['user_address'] ?? ''));
    if ($address !== '') {
        $parts[] = "Sapa user dengan \"" . $address . "\".";
    }

    // Style
    $style = trim((string)($bot['language_style'] ?? ''));
    $styleMap = [
        'formal' => 'Gunakan bahasa formal profesional.',
        'semi_formal' => 'Gunakan bahasa semi-formal, ramah namun tetap profesional.',
        'casual' => 'Gunakan bahasa casual friendly, seperti teman.',
        'enthusiastic' => 'Gunakan bahasa antusias dengan energy tinggi.',
    ];
    if (isset($styleMap[$style])) $parts[] = $styleMap[$style];

    // Response rules
    $rules = $bot['response_rules'] ?? [];
    if (is_array($rules)) {
        if (!empty($rules['no_asterisk'])) $parts[] = "JANGAN pakai tanda * atau ** di jawaban (no markdown formatting).";
        if (!empty($rules['one_question_at_a_time'])) $parts[] = "Tanya hanya 1 pertanyaan per turn, jangan langsung banyak.";
        if (!empty($rules['summary_before_confirm'])) $parts[] = "Buat summary sebelum minta konfirmasi user.";
        if (!empty($rules['use_emoji'])) $parts[] = "Gunakan emoji ramah secukupnya.";
        if (!empty($rules['concise_response'])) $parts[] = "Jawaban maksimal 3 kalimat.";
    }

    // Fallback behavior
    $fallback = trim((string)($bot['fallback_behavior'] ?? ''));
    $fallbackMap = [
        'say_dont_know' => "Kalau tidak tahu jawaban dari knowledge base, katakan dengan sopan bahwa Anda belum memiliki info.",
        'ask_contact' => "PENTING: Kalau tidak tahu jawaban dari knowledge base, JANGAN bilang \"tidak tahu\" atau \"tidak memiliki info detail\". Langsung tanyakan nama dan no HP user untuk dihubungi kembali oleh tim kami.",
        'redirect_wa' => "Kalau tidak tahu jawaban, arahkan user untuk chat langsung dengan admin via WhatsApp.",
    ];
    if (isset($fallbackMap[$fallback])) $parts[] = $fallbackMap[$fallback];

    return implode("\n", $parts);
}
// === /v1.2.3 Structured prompt builder ===

/* ============================================================
 * v1.2.5: Strip markdown formatting auto — post-process AI response
 * kalau rule no_asterisk aktif di structured config.
 * ============================================================ */
function stripMarkdownIfEnabled($answer, $settings) {
    if (empty($settings['bot']['response_rules']['no_asterisk'])) return $answer;
    if (!is_string($answer) || $answer === '') return $answer;

    // Strip **bold** dan __bold__ (double)
    $answer = preg_replace('/\*\*([^*\n]+?)\*\*/', '$1', $answer);
    $answer = preg_replace('/__([^_\n]+?)__/', '$1', $answer);

    // Strip *italic* dan _italic_ (single, dengan word boundary supaya tidak break code/var)
    $answer = preg_replace('/(?<![a-zA-Z0-9])\*([^*\n]+?)\*(?![a-zA-Z0-9])/', '$1', $answer);
    $answer = preg_replace('/(?<![a-zA-Z0-9])_([^_\n]+?)_(?![a-zA-Z0-9])/', '$1', $answer);

    // Strip headers (# H1, ## H2, ### H3, dst)
    $answer = preg_replace('/^\s*#{1,6}\s+/m', '', $answer);

    return $answer;
}
// === /v1.2.5 ===

/* ----------------------------------------------------------------------------
 *  Shared answer engine — used by BOTH the web chat widget and WhatsApp.
 *  Returns [bool ok, string answer, int kbUsed].
 * ------------------------------------------------------------------------- */
/* ============================================================
 * v1.2.8: deiDashboardUrl — auto-detect dashboard URL per tenant
 * ============================================================ */
function deiDashboardUrl() {
    $host   = $_SERVER['HTTP_HOST'] ?? 'localhost';
    $scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
    $uri    = $_SERVER['REQUEST_URI'] ?? '';
    $basePath = '';
    if (($pos = strpos($uri, '/api/')) !== false) {
        $basePath = substr($uri, 0, $pos);
    }
    return $scheme . '://' . $host . $basePath . '/dashboard/chatbot-ai/';
}

/* ============================================================
/* ============================================================
 * v1.2.35: konteks waktu — dipakai SEMUA jalur pembangunan prompt
 * ============================================================ */
// Sebelumnya blok ini hanya ada di jalur KB besar, sehingga tenant ber-KB kecil
// tidak tahu hari ini tanggal berapa dan menanyakan bulan/tahun kepada tamu.
function deiKonteksWaktu() {
    $hari_id  = ['Sunday'=>'Minggu','Monday'=>'Senin','Tuesday'=>'Selasa','Wednesday'=>'Rabu',
                 'Thursday'=>'Kamis','Friday'=>'Jumat','Saturday'=>'Sabtu'];
    $bulan_id = ['January'=>'Januari','February'=>'Februari','March'=>'Maret','April'=>'April',
                 'May'=>'Mei','June'=>'Juni','July'=>'Juli','August'=>'Agustus',
                 'September'=>'September','October'=>'Oktober','November'=>'November','December'=>'Desember'];
    $now = new DateTime('now', new DateTimeZone('Asia/Jakarta'));
    $tanggalIndo = $hari_id[$now->format('l')] . ', ' . $now->format('j') . ' '
                 . $bulan_id[$now->format('F')] . ' ' . $now->format('Y');
    $th = $now->format('Y');
    return "KONTEKS WAKTU (WAJIB DIINGAT):\n"
        . "Hari ini adalah {$tanggalIndo} (Waktu Indonesia Barat / WIB).\n"
        . "Tahun sekarang adalah {$th}.\n"
        . "Jika user menyebut tanggal tanpa bulan/tahun (misal: '21-22' atau '5 Agustus'), "
        . "JANGAN bertanya bulan atau tahunnya. Asumsikan bulan berjalan dan tahun {$th}. "
        . "Kalau tanggal itu sudah lewat di bulan berjalan, asumsikan bulan berikutnya.\n"
        . "WAJIB konfirmasi tanggal lengkap ke user setelah dia sebut tanggal, misal: "
        . "'Baik, jadi check-in 21 " . $bulan_id[$now->format('F')] . " {$th} ya, Bapak/Ibu?' sebelum lanjut proses.\n"
        . "JANGAN PERNAH pakai tahun sebelum {$th} dalam booking/reservasi.";
}

/* ============================================================
 * v1.2.22: Daftar harga resmi — sumber tunggal untuk pertanyaan harga
 * ============================================================ */
function pricelistGet() {
    $p = readJson(PRICELIST_FILE, []);
    if (!is_array($p)) return ['items' => [], 'updated_at' => '', 'updated_by' => ''];
    return [
        'items'      => is_array($p['items'] ?? null) ? $p['items'] : [],
        'updated_at' => (string)($p['updated_at'] ?? ''),
        'updated_by' => (string)($p['updated_by'] ?? ''),
    ];
}

// Susun blok instruksi + daftar harga untuk dikirim ke model.
// Return '' kalau daftar kosong — jangan kirim blok kosong.
function pricelistPromptBlock() {
    $pl = pricelistGet();
    $rows = '';
    foreach ($pl['items'] as $it) {
        if (!is_array($it)) continue;
        $nama  = trim((string)($it['item'] ?? ''));
        $harga = trim((string)($it['price'] ?? ''));
        if ($nama === '' || $harga === '') continue;
        $note  = trim((string)($it['note'] ?? ''));
        $rows .= '- ' . $nama . ' : ' . $harga . ($note !== '' ? ' (' . $note . ')' : '') . "\n";
    }
    if ($rows === '') return '';

    $blk  = "=== DAFTAR HARGA RESMI ===\n";
    $blk .= "Ini sumber harga SATU-SATUNYA. Aturan yang WAJIB dipatuhi:\n";
    $blk .= "1. Untuk pertanyaan harga/tarif/biaya, pakai HANYA angka dari daftar ini.\n";
    $blk .= "2. Kalau ada angka berbeda di Knowledge Base, daftar ini yang benar.\n";
    $blk .= "3. JANGAN menghitung apa pun — tidak boleh mengalikan jumlah malam/unit,\n";
    $blk .= "   menjumlahkan beberapa item, menghitung diskon, pajak, atau total.\n";
    $blk .= "   Sebutkan harga satuan apa adanya, lalu arahkan customer untuk konfirmasi\n";
    $blk .= "   perhitungan total ke admin/tim kami.\n";
    $blk .= "4. Kalau item yang ditanya TIDAK ada di daftar, katakan terus terang belum\n";
    $blk .= "   tersedia informasinya dan arahkan ke kontak resmi. JANGAN menebak.\n\n";
    $blk .= $rows;
    if ($pl['updated_at'] !== '') {
        $blk .= "\n(Daftar diperbarui " . substr($pl['updated_at'], 0, 10) . ")";
    }
    return $blk;
}

/* ============================================================
 * v1.2.20: Leads — AI mengekstrak fakta, agent yang memutuskan qualified
 * ============================================================ */
function leadsGetAll() {
    $l = readJson(LEADS_FILE, []);
    return is_array($l) ? $l : [];
}
function leadStatusValid($s) {
    return in_array($s, ['baru', 'qualified', 'follow_up', 'closed'], true);
}

// Minta Claude MENGEKSTRAK fakta dari transkrip — bukan menilai keseriusan.
// Return array hasil ekstraksi, atau null kalau gagal.
function leadExtract($settings, $transcript) {
    $transcript = trim((string)$transcript);
    if ($transcript === '') return null;

    $sys = "Anda menganalisa transkrip percakapan customer service.\n"
         . "Kembalikan HANYA JSON valid, tanpa penjelasan, tanpa tanda kutip markdown.\n"
         . "Struktur persis:\n"
         . '{"nama":"","kebutuhan":"","waktu":"","anggaran":"","ringkasan":""}' . "\n\n"
         . "Aturan:\n"
         . "- nama: nama customer kalau disebut di percakapan\n"
         . "- kebutuhan: apa yang dicari/ditanyakan customer\n"
         . "- waktu: tanggal atau jangka waktu yang disebut customer\n"
         . "- anggaran: angka/kisaran biaya yang disebut customer\n"
         . "- ringkasan: satu kalimat singkat isi percakapan\n"
         . "- Kosongkan string kalau TIDAK disebut. JANGAN menebak atau mengarang.";

    $msgs = [['role' => 'user', 'content' => "Transkrip percakapan:\n\n" . $transcript]];
    list($ok, $answer, $usage) = callClaude($settings, $sys, $msgs);
    if (!$ok) return null;

    // v1.2.20: biaya analisa MASUK KUOTA (kuota dihitung dari 'calls' di usage.json)
    recordUsage($usage);

    // Bersihkan pagar markdown kalau model tetap menambahkannya
    $raw = trim((string)$answer);
    $raw = preg_replace('/^```[a-zA-Z]*\s*/', '', $raw);
    $raw = preg_replace('/```\s*$/', '', $raw);
    $raw = trim($raw);

    $data = json_decode($raw, true);
    if (!is_array($data)) {
        error_log('leadExtract: respons bukan JSON valid: ' . mb_substr($raw, 0, 200));
        return null;
    }
    return [
        'nama'      => mb_substr(trim((string)($data['nama']      ?? '')), 0, 100),
        'kebutuhan' => mb_substr(trim((string)($data['kebutuhan'] ?? '')), 0, 300),
        'waktu'     => mb_substr(trim((string)($data['waktu']     ?? '')), 0, 200),
        'anggaran'  => mb_substr(trim((string)($data['anggaran']  ?? '')), 0, 250),
        'ringkasan' => mb_substr(trim((string)($data['ringkasan'] ?? '')), 0, 300),
    ];
}

// Bangun transkrip percakapan satu nomor dari log (urut lama -> baru).
function leadBuildTranscript($number, $logs = null, $max = 40) {
    $number = preg_replace('/\D/', '', (string)$number);
    if ($logs === null) $logs = readJson(LOG_FILE, []);
    $rows = [];
    foreach ($logs as $e) {
        if (($e['channel'] ?? '') !== 'whatsapp') continue;
        if (preg_replace('/\D/', '', (string)($e['ip'] ?? '')) !== $number) continue;
        $rows[] = $e;
        if (count($rows) >= $max) break;
    }
    $rows = array_reverse($rows);   // log disimpan terbaru-dulu
    $out = '';
    foreach ($rows as $e) {
        $q = trim((string)($e['q'] ?? ''));
        $a = trim((string)($e['a'] ?? ''));
        if ($q !== '') $out .= "Customer: " . $q . "\n";
        if ($a !== '') $out .= "CS: " . $a . "\n";
    }
    return trim($out);
}

// Jalankan analisa untuk satu nomor lalu simpan kartunya.
// $force = true untuk analisa ulang manual (lewat action analyze_lead).
function leadAnalyzeNumber($settings, $number, $logs = null, $force = false) {
    $number = preg_replace('/\D/', '', (string)$number);
    if ($number === '') return false;
    $all = leadsGetAll();
    if (!$force && isset($all[$number])) return false;   // sudah punya kartu -> sekali saja

    $transcript = leadBuildTranscript($number, $logs);
    if ($transcript === '') return false;

    $ex = leadExtract($settings, $transcript);
    if ($ex === null) return false;

    $now = date('Y-m-d H:i:s');
    $lama = $all[$number] ?? [];
    $all[$number] = [
        'number'      => $number,
        'name'        => waContactName($number),
        'status'      => $lama['status'] ?? 'baru',
        'note'        => $lama['note'] ?? '',
        'extracted'   => $ex,
        'analyzed_at' => $now,
        'created_at'  => $lama['created_at'] ?? $now,
        'updated_at'  => $now,
    ];
    writeJson(LEADS_FILE, $all);
    return true;
}

/* ============================================================
 * v1.2.19: kontak WA — nama pengirim dari profil WhatsApp
 * ============================================================ */
function waGetContacts() {
    $c = readJson(CONTACTS_FILE, []);
    return is_array($c) ? $c : [];
}
// Simpan/perbarui nama dari profil WhatsApp. TIDAK menimpa koreksi manual agent.
function waSaveContact($number, $nameWa) {
    $number = preg_replace('/\D/', '', (string)$number);
    if ($number === '') return;
    $nameWa = trim((string)$nameWa);
    $all = waGetContacts();
    $now = date('Y-m-d H:i:s');
    if (!isset($all[$number]) || !is_array($all[$number])) {
        $all[$number] = ['name_wa' => '', 'name_manual' => '', 'first_seen' => $now, 'last_seen' => $now];
    }
    if ($nameWa !== '') $all[$number]['name_wa'] = mb_substr($nameWa, 0, 100);
    $all[$number]['last_seen'] = $now;
    writeJson(CONTACTS_FILE, $all);
}
// Nama tampil: koreksi manual menang atas nama profil WhatsApp.
function waContactName($number, $contacts = null) {
    $number = preg_replace('/\D/', '', (string)$number);
    $all = ($contacts === null) ? waGetContacts() : $contacts;
    $c = $all[$number] ?? null;
    if (!is_array($c)) return '';
    $manual = trim((string)($c['name_manual'] ?? ''));
    if ($manual !== '') return $manual;
    return trim((string)($c['name_wa'] ?? ''));
}

// v1.2.39: tag pipeline kontak (stage) + modifier VIP
function contactStageValid($s) {
    return in_array($s, ['new', 'warm', 'hot_prospect', 'cold', 'lost', 'active_customer', 'churned'], true);
}
function waContactStage($number, $contacts = null) {
    $number = preg_replace('/\D/', '', (string)$number);
    $all = ($contacts === null) ? waGetContacts() : $contacts;
    $c = $all[$number] ?? null;
    if (!is_array($c)) return 'new';
    $st = (string)($c['stage'] ?? 'new');
    return contactStageValid($st) ? $st : 'new';
}
function waContactVip($number, $contacts = null) {
    $number = preg_replace('/\D/', '', (string)$number);
    $all = ($contacts === null) ? waGetContacts() : $contacts;
    $c = $all[$number] ?? null;
    if (!is_array($c)) return false;
    // VIP hanya sah nempel di stage active_customer, walau data lama entah
    // bagaimana punya vip=true di stage lain (jaga-jaga, bukan cuma pas simpan).
    return !empty($c['vip']) && waContactStage($number, $all) === 'active_customer';
}
// Simpan stage + vip. VIP dipaksa false kalau stage bukan active_customer,
// supaya tidak ada kombinasi ganjil tersimpan (mis. "Baru" + VIP).
function waSetContactStage($number, $stage, $vip) {
    $number = preg_replace('/\D/', '', (string)$number);
    if ($number === '' || !contactStageValid($stage)) return false;
    $all = waGetContacts();
    $now = date('Y-m-d H:i:s');
    if (!isset($all[$number]) || !is_array($all[$number])) {
        $all[$number] = ['name_wa' => '', 'name_manual' => '', 'first_seen' => $now, 'last_seen' => $now];
    }
    $all[$number]['stage']            = $stage;
    $all[$number]['vip']              = ($stage === 'active_customer') ? (bool)$vip : false;
    $all[$number]['stage_updated_at'] = $now;
    writeJson(CONTACTS_FILE, $all);
    return true;
}
// v1.2.39 fase4: data pelanggan (nama + tanggal lahir), diisi manual saat
// kontak sudah jadi Active Customer. $custName / $custDob null = tidak
// diubah (partial update, sama pola dengan save_lead).
function waSetContactInfo($number, $custName, $custDob) {
    $number = preg_replace('/\D/', '', (string)$number);
    if ($number === '') return false;
    $all = waGetContacts();
    $now = date('Y-m-d H:i:s');
    if (!isset($all[$number]) || !is_array($all[$number])) {
        $all[$number] = ['name_wa' => '', 'name_manual' => '', 'first_seen' => $now, 'last_seen' => $now];
    }
    if ($custName !== null) $all[$number]['cust_name'] = mb_substr(trim((string)$custName), 0, 100);
    if ($custDob  !== null) $all[$number]['cust_dob']  = $custDob;
    writeJson(CONTACTS_FILE, $all);
    return true;
}

/* ============================================================
 * v1.2.13: daftar kategori notif (6 fixed permanen + custom dari file)
 * ============================================================ */
function deiFixedCategories() {
    return ['Sales', 'Operation', 'Marketing', 'Engineering', 'Owner', 'IT'];
}
function deiCustomCategories() {
    $c = readJson(PUSH_CATEGORIES_FILE, []);
    if (!is_array($c)) return [];
    $out = [];
    foreach ($c as $x) {
        $x = trim((string)$x);
        if ($x !== '') $out[] = $x;
    }
    return array_values(array_unique($out));
}
function deiAllCategories() {
    return array_values(array_merge(deiFixedCategories(), deiCustomCategories()));
}
// Hitung pemakaian kategori di KB (topic) + users (categories) — untuk blokir hapus.
function deiCategoryUsage($cat) {
    $cat = trim((string)$cat);
    $kbCount = 0; $userCount = 0;
    foreach (readJson(KB_FILE, []) as $e) {
        if (trim((string)($e['topic'] ?? '')) === $cat) $kbCount++;
    }
    foreach (readJson(USERS_FILE, []) as $u) {
        $cats = $u['categories'] ?? [];
        if (is_array($cats) && in_array($cat, $cats, true)) $userCount++;
    }
    return ['kb' => $kbCount, 'users' => $userCount];
}

/* ============================================================
 * v1.2.12: auto-assign by topic — deteksi topik via KB retrieval + routing
 * ============================================================ */
// Deteksi topik dari pesan (hybrid: window + score threshold). Gratis (no AI call).
// Scoring sama persis dengan searchKB, tapi sekalian bawa score supaya bisa
// apply threshold — searchKB sendiri tidak diubah (dipakai tempat lain).
define('TOPIC_SCAN_MAX', 5);      // berapa kandidat teratas yang dicek topic-nya
define('TOPIC_MIN_RATIO', 0.5);   // kandidat diabaikan kalau score < ratio x score tertinggi
function detectTopicFromMessage($message) {
    $message = trim((string)$message);
    if ($message === '') return '';
    $kb = readJson(KB_FILE, []);
    if (!$kb) return '';

    $words = preg_split('/\s+/', mb_strtolower($message));
    $words = array_filter($words, function ($w) { return mb_strlen($w) >= 3; });
    if (empty($words)) return '';

    $scored = [];
    foreach ($kb as $entry) {
        $hay = mb_strtolower(($entry['title'] ?? '') . ' ' . ($entry['category'] ?? '') . ' ' . ($entry['content'] ?? ''));
        $score = 0;
        foreach ($words as $w) { $score += substr_count($hay, $w); }
        if ($score > 0) $scored[] = ['s' => $score, 'e' => $entry];
    }
    if (empty($scored)) return '';
    usort($scored, function ($a, $b) { return $b['s'] - $a['s']; });

    $topScore  = (int)$scored[0]['s'];
    $minScore  = $topScore * TOPIC_MIN_RATIO;
    $candidates = array_slice($scored, 0, TOPIC_SCAN_MAX);
    foreach ($candidates as $r) {
        if ($r['s'] < $minScore) break;   // sisanya pasti lebih kecil (sudah terurut)
        $topic = trim((string)($r['e']['topic'] ?? ''));
        if ($topic !== '') return $topic;
    }
    return '';
}

// Filter subscriber by topik: agent yang punya kategori match + SEMUA super_admin/admin.
// Kalau topic kosong -> return semua subscriber (broadcast fallback).
// $subscribers = array_keys(push-subs.json) = daftar username yang subscribe.
function getPushTargetsByTopic($topic, $subscribers) {
    $topic = trim((string)$topic);
    if ($topic === '' || empty($subscribers)) return $subscribers;   // fallback broadcast

    $users = readJson(USERS_FILE, []);
    $byName = [];
    foreach ($users as $u) {
        if (isset($u['username'])) $byName[$u['username']] = $u;
    }

    $targets = [];
    foreach ($subscribers as $sub) {
        $u = $byName[$sub] ?? null;
        if (!$u) { continue; }   // subscriber tidak ada di users -> skip (safety)
        $role = $u['role'] ?? '';
        // super_admin + admin selalu dapat semua notif
        if ($role === 'super_admin' || $role === 'admin') {
            $targets[] = $sub;
            continue;
        }
        // agent lain: cek kategori match
        $cats = $u['categories'] ?? [];
        if (is_array($cats) && in_array($topic, $cats, true)) {
            $targets[] = $sub;
        }
    }
    // Safety: kalau hasil kosong (tidak ada agent match + tidak ada admin subscribe),
    // fallback broadcast supaya notif tidak hilang total.
    return empty($targets) ? $subscribers : $targets;
}

/*
 * v1.2.8: sendPushToUsers — kirim Web Push ke subscriber (generic, future-proof)
 * ============================================================ */
function sendPushToUsers($targetUsers, $title, $body, $url) {
    $vendorAutoload = __DIR__ . '/../vendor/autoload.php';
    $vapidFile = DATA_DIR . '/vapid-keys.json';
    $subsFile  = DATA_DIR . '/push-subs.json';
    if (!file_exists($vendorAutoload) || !file_exists($vapidFile) || !file_exists($subsFile)) return;

    require_once $vendorAutoload;
    $vapid = json_decode(file_get_contents($vapidFile), true);
    $allSubs = json_decode(file_get_contents($subsFile), true);
    if (!is_array($allSubs) || empty($allSubs)) return;
    if (empty($vapid['publicKey']) || empty($vapid['privateKey'])) return;

    try {
        $auth = ['VAPID' => [
            'subject'    => 'mailto:admin@deintegra.com',
            'publicKey'  => $vapid['publicKey'],
            'privateKey' => $vapid['privateKey'],
        ]];
        $webPush = new \Minishlink\WebPush\WebPush($auth);
        $payload = json_encode([
            'title' => $title,
            'body'  => $body,
            'url'   => $url,
            'icon'  => './icon-192.png',
            'tag'   => 'dei-wa',
        ], JSON_UNESCAPED_UNICODE);

        foreach ($targetUsers as $username) {
            $subs = $allSubs[$username] ?? [];
            foreach ($subs as $sub) {
                if (empty($sub['endpoint']) || empty($sub['keys'])) continue;
                $webPush->queueNotification(
                    \Minishlink\WebPush\Subscription::create([
                        'endpoint' => $sub['endpoint'],
                        'keys'     => $sub['keys'],
                    ]),
                    $payload
                );
            }
        }

        // Flush + cleanup expired (410 Gone / 404)
        $expired = [];
        foreach ($webPush->flush() as $report) {
            if (!$report->isSuccess() && $report->isSubscriptionExpired()) {
                $ep = method_exists($report, 'getEndpoint') ? $report->getEndpoint() : '';
                if ($ep !== '') $expired[$ep] = true;
            }
        }
        if (!empty($expired)) {
            $changed = false;
            foreach ($allSubs as $u => $subs) {
                $filtered = array_values(array_filter($subs, function ($s) use ($expired) {
                    return empty($expired[$s['endpoint'] ?? '']);
                }));
                if (count($filtered) !== count($subs)) { $allSubs[$u] = $filtered; $changed = true; }
            }
            if ($changed) @file_put_contents($subsFile, json_encode($allSubs, JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE), LOCK_EX);
        }
    } catch (\Throwable $e) {
        error_log('sendPushToUsers error: ' . $e->getMessage());
    }
}
// === /v1.2.8 sendPushToUsers ===

function generateAnswer($s, $message, $history = []) {
    $persona     = trim((string)($s['bot']['system_prompt'] ?? ''));
    // v1.2.3: prepend structured prompt prefix (form-generated). Empty string if all fields blank.
    $structuredPrefix = buildStructuredPromptPrefix($s['bot'] ?? []);
    if ($structuredPrefix !== '') {
        $persona = $structuredPrefix . "\n\n=== INSTRUKSI TAMBAHAN ===\n" . $persona;
    }
    $kbAll       = readJson(KB_FILE, []);
    $kbHitsUsed  = count($kbAll);
    $deiPriceBlk = pricelistPromptBlock();   // v1.2.22: '' kalau daftar harga kosong
    $deiWaktuBlk = deiKonteksWaktu();        // v1.2.35: dipasang di SEMUA jalur di bawah
    $minCacheTok = 1024;   // Anthropic ignores cache on blocks below ~1024 tokens

    // Build the full-KB block (Strategy B: send everything, let Claude pick what's relevant).
    $kbText = '';
    foreach ($kbAll as $e) {
        $cat = trim((string)($e['category'] ?? ''));
        $tit = trim((string)($e['title']    ?? ''));
        $con = trim((string)($e['content']  ?? ''));
        // v1.2.24: entri tanpa ISI dilewati. Entri "judul saja" (mis. hasil
        // fitur Pertanyaan Belum Terjawab yang menunggu diisi) kalau dikirim
        // akan terbaca model sebagai pertanyaan tanpa jawaban.
        if ($con === '') continue;
        if ($tit === '' && $con === '') continue;
        $kbText .= '[' . $cat . '] ' . $tit . "\n" . $con . "\n\n";
    }
    $kbText = trim($kbText);

    // Heuristic: 4 chars ≈ 1 token. Anthropic caches only blocks >=1024 tokens.
    $kbTokensEst = (int)(strlen($kbText) / 4);

    if ($kbText === '') {
        // No KB at all — single-string system (no caching needed).
        $sys = $deiWaktuBlk . "\n\n" . $persona . "\n\n(Tidak ada entri Knowledge Base. Arahkan pengunjung untuk menghubungi tim resmi.)";   // v1.2.35
        if ($deiPriceBlk !== '') $sys .= "\n\n" . $deiPriceBlk;   // v1.2.22
        $messages = buildMessages($message, $history);
        list($ok, $answer, $usage) = callClaude($s, $sys, $messages);
        return [$ok, $answer, 0, $usage];
    }

    if ($kbTokensEst < $minCacheTok) {
        // KB too small to benefit from cache — fall back to inline string system (saves a request roundtrip on cache write).
        $sys = $deiWaktuBlk . "\n\n" . $persona . "\n\n=== KNOWLEDGE BASE ===\n" . $kbText;   // v1.2.35
        if ($deiPriceBlk !== '') $sys .= "\n\n" . $deiPriceBlk;   // v1.2.22
        $messages = buildMessages($message, $history);
        list($ok, $answer, $usage) = callClaude($s, $sys, $messages);
        return [$ok, $answer, $kbHitsUsed, $usage];
    }

    // KB big enough to cache. System = array of blocks:
    //   [persona block, KB block with cache_control]
    // The KB block is identical across requests for the same tenant, so cache hit rate should be high.
    // v1.1.10 fix: inject KONTEKS WAKTU (dynamic date) di depan supaya AI tahu tahun sekarang
    // Bukan di-cache karena isinya berubah tiap hari. Persona + KB tetap di-cache.
    $konteksWaktu = $deiWaktuBlk;   // v1.2.35: memakai helper bersama


    $systemBlocks = [
        ['type' => 'text', 'text' => $konteksWaktu],
        ['type' => 'text', 'text' => $persona . "\n\n=== KNOWLEDGE BASE (gunakan HANYA informasi di bawah; jika tidak ada, arahkan ke kontak resmi) ==="],
        ['type' => 'text', 'text' => $kbText, 'cache_control' => ['type' => 'ephemeral']],
    ];
    // v1.2.22: blok harga ditaruh SETELAH titik cache — mengubah harga tidak
    // menghanguskan cache KB, jadi update sesering apa pun tetap murah.
    if ($deiPriceBlk !== '') {
        $systemBlocks[] = ['type' => 'text', 'text' => $deiPriceBlk];
    }
    $messages = buildMessages($message, $history);
    list($ok, $answer, $usage) = callClaude($s, $systemBlocks, $messages);
    return [$ok, $answer, $kbHitsUsed, $usage];
}

function buildMessages($message, $history) {
    $messages = [];
    foreach (array_slice($history, -8) as $h) {
        $role = ($h['role'] ?? '') === 'assistant' ? 'assistant' : 'user';
        $content = trim($h['content'] ?? '');
        if ($content !== '') $messages[] = ['role' => $role, 'content' => $content];
    }
    $messages[] = ['role' => 'user', 'content' => $message];
    return $messages;
}

/* ----------------------------------------------------------------------------
 *  WhatsApp Cloud API helpers
 * ------------------------------------------------------------------------- */
function waConf($s) {
    return is_array($s['whatsapp_api'] ?? null) ? $s['whatsapp_api'] : [];
}

// v1.2.36: batas 24 jam adalah aturan Meta, bukan WhatsApp secara umum.
// Untuk penyedia lain jendela selalu terbuka. Hasilnya disimpan sementara
// karena dipakai berulang di dalam perulangan daftar percakapan.
function waWindowSelaluTerbuka() {
    static $cache = null;
    if ($cache === null) {
        $wa = waConf(getSettings());
        $cache = (($wa['provider'] ?? 'meta') !== 'meta');
    }
    return $cache;
}

// Validate Meta's X-Hub-Signature-256 (skipped only if app_secret not set).
function waVerifySignature($rawBody, $appSecret) {
    if ($appSecret === '' || $appSecret === null) return true;
    $hdr = $_SERVER['HTTP_X_HUB_SIGNATURE_256'] ?? '';
    if (strpos($hdr, 'sha256=') !== 0) return false;
    $expected = 'sha256=' . hash_hmac('sha256', $rawBody, $appSecret);
    return hash_equals($expected, $hdr);
}

// Send a plain-text WhatsApp message via the Cloud API. Returns true on 2xx.
// v1.2.36: kirim lewat Fonnte (gateway tidak resmi, memakai nomor yang sudah ada).
// Fonnte membalas HTTP 200 walau gagal, jadi status di badan balasan ikut diperiksa.
function waSendFonnte($wa, $to, $text) {
    $token = $wa['fonnte_token'] ?? '';
    if ($token === '') return false;
    $ch = curl_init('https://api.fonnte.com/send');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_TIMEOUT        => 20,
        CURLOPT_HTTPHEADER     => ['Authorization: ' . $token],
        CURLOPT_POSTFIELDS     => http_build_query([
            'target'      => $to,
            'message'     => $text,
            'countryCode' => '62',
        ]),
    ]);
    $resp = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($code < 200 || $code >= 300) {
        error_log('waSendFonnte HTTP ' . $code);
        return false;
    }
    $d = json_decode((string)$resp, true);
    if (is_array($d) && array_key_exists('status', $d) && $d['status'] === false) {
        error_log('waSendFonnte ditolak: ' . mb_substr((string)$resp, 0, 200));
        return false;
    }
    return true;
}

function waSend($wa, $to, $text) {
    // v1.2.36: pilih penyedia. Bawaan 'meta' supaya tenant lama tidak berubah.
    if (($wa['provider'] ?? 'meta') === 'fonnte') return waSendFonnte($wa, $to, $text);
    $token = $wa['access_token'] ?? '';
    $pnid  = $wa['phone_number_id'] ?? '';
    if ($token === '' || $pnid === '') return false;
    $url = 'https://graph.facebook.com/v21.0/' . rawurlencode($pnid) . '/messages';
    $payload = [
        'messaging_product' => 'whatsapp',
        'recipient_type'    => 'individual',
        'to'                => $to,
        'type'              => 'text',
        'text'              => ['preview_url' => false, 'body' => $text],
    ];
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_TIMEOUT        => 20,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json', 'Authorization: Bearer ' . $token],
        CURLOPT_POSTFIELDS     => json_encode($payload, JSON_UNESCAPED_UNICODE),
    ]);
    curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return $code >= 200 && $code < 300;
}

/* ============================================================
 * v1.2.36: alur pemrosesan pesan WA masuk — dipakai SEMUA penyedia
 * ============================================================ */
// Dipisahkan supaya penyedia kedua (Fonnte) tidak perlu menyalin alur ini.
// Yang khas per-penyedia tinggal di webhook masing-masing: cara memverifikasi
// kiriman, membaca strukturnya, dan mengirim balasan. Begitu nomor dan teks
// didapat, penanganannya identik.
//
// $metaInfo  : value.metadata dari Meta (untuk tracker WA-to-Ads). Kosongkan
//              untuk penyedia lain — tracker otomatis tidak aktif.
// $senderName: nama profil pengirim kalau tersedia.
function waProcessIncoming($s, $wa, $from, $text, $senderName = '', $metaInfo = []) {
    $logLimit = (int)($s['api']['log_limit'] ?? 500);
    $keepCtx  = ($wa['keep_context'] ?? true);

    // v1.2.8 Fase 3: push notif ke semua subscriber saat WA text masuk
    $deiPushSubsFile = DATA_DIR . '/push-subs.json';
    if (file_exists($deiPushSubsFile)) {
        $deiPushSubs = json_decode(file_get_contents($deiPushSubsFile), true);
        if (is_array($deiPushSubs) && !empty($deiPushSubs)) {
            $deiPushPreview = mb_substr($text, 0, 80);
            $deiWaTopic = detectTopicFromMessage($text);  // v1.2.12: auto-assign by topic
            $deiWaTargets = getPushTargetsByTopic($deiWaTopic, array_keys($deiPushSubs));
            sendPushToUsers($deiWaTargets, 'Pesan WA: +' . $from, $deiPushPreview, deiDashboardUrl());
        }
    }

    // === WA-to-Ads tracker (deintegra lead) — fire & forget ===
    $wtMeta = $metaInfo;
    $wtPn  = preg_replace('/\D/','', $wtMeta['display_phone_number'] ?? '');
    $wtPid = (string)($wtMeta['phone_number_id'] ?? '');
    if ($wtPid === '1247385528447121' || $wtPn === '6285111230487') {
        $wtPayload = json_encode(['phone'=>$from, 'message'=>$text, 'name'=>$senderName, 'token'=>'a72243cc6cec300146cbaef6a0b14490']);  // v1.2.19: nama kini terisi
        if (function_exists('curl_init')) {
            $wtCh = curl_init('https://deintegra.com/wa-tracker/fn-hook.php');
            curl_setopt_array($wtCh, [CURLOPT_POST=>true, CURLOPT_HTTPHEADER=>['Content-Type: application/json'], CURLOPT_POSTFIELDS=>$wtPayload, CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>3, CURLOPT_SSL_VERIFYPEER=>false]);
            @curl_exec($wtCh); @curl_close($wtCh);
        }
    }
    if (mb_strlen($text) > 2000) $text = mb_substr($text, 0, 2000);

    $limit = (int)($wa['rate_limit_per_number'] ?? ($s['api']['rate_limit'] ?? 20));
    if (!checkRateLimit('wa:' . $from, $limit)) {
        waSend($wa, $from, 'Anda mengirim terlalu banyak pesan. Mohon tunggu sebentar ya.');
        return;
    }

    // v1.2.37: bereskan claim & mode kedaluwarsa SEBELUM memutuskan siapa yang
    // menjawab. Sebelumnya keduanya hanya diproses saat dashboard dibuka —
    // agent yang pulang tanpa melepas percakapan membuat bot diam semalaman.
    try {
        waClaimAutoProcess();
        waModeSweepIdle();
    } catch (\Throwable $e) { error_log('sapu mode/claim: ' . $e->getMessage()); }

    // --- Handoff logic ---
    $ho = is_array($s['handoff'] ?? null) ? $s['handoff'] : [];
    $mode = waGetMode($from);
    // Auto-handoff: a keyword flips this number to human mode.
    if ($mode === 'bot' && !empty($ho['enabled']) && waMatchHandoff($text, $ho['keywords'] ?? [])) {
        waSetMode($from, 'human');
        $mode = 'human';
    }

    $logBase = [
        'ts'           => date('Y-m-d H:i:s'),
        'q'            => $text,
        'ip'           => $from,
        'channel'      => 'whatsapp',
        'utm_source'   => 'whatsapp',
        'utm_medium'   => 'chat',
        'utm_campaign' => '',
        'page'         => '',
        'referrer'     => '',
    ];

    if ($mode === 'human') {
        // Admin is handling this number — record, notify, do NOT auto-reply.
        if ($keepCtx) {
            $history = waLoadHistory($from);
            $history[] = ['role' => 'user', 'content' => $text];
            waSaveHistory($from, $history);
        }
        $logs = readJson(LOG_FILE, []);
        array_unshift($logs, array_merge($logBase, ['a' => '', 'awaiting' => true]));
        writeJson(LOG_FILE, array_slice($logs, 0, $logLimit));
        tgNotify($s, "\xF0\x9F\x93\xA9 [WhatsApp] " . $from . ":\n\"" . $text . "\"\n\xF0\x9F\x99\x8B menunggu admin");
        return;
    }

    // Bot mode — generate and send an automatic answer.
    // v1.1.3: license enforcement
    $lic = getLicenseStatus($s);
    if ($lic['status'] === 'suspended') {
        $answer = $lic['message'] ?: LIC_DEFAULT_SUSPEND_MSG;
        waSend($wa, $from, $answer);
        $logs = readJson(LOG_FILE, []);
        array_unshift($logs, array_merge($logBase, ['a' => $answer, 'suspended' => true]));
        writeJson(LOG_FILE, array_slice($logs, 0, $logLimit));
        return;
    }
    // v1.1.4: cap enforcement (graceful at 90%+, no Claude call)
    $cap = getCapStatus($s);
    if ($cap['reached'] || $cap['warning']) {
        $answer = $cap['message'] ?: CAP_DEFAULT_MSG;
        waSend($wa, $from, $answer);
        $logs = readJson(LOG_FILE, []);
        array_unshift($logs, array_merge($logBase, ['a' => $answer, 'cap_reached' => true]));
        writeJson(LOG_FILE, array_slice($logs, 0, $logLimit));
        return;
    }
    $history = $keepCtx ? waLoadHistory($from) : [];
    list($ok, $answer, $_kbUsed, $usage) = generateAnswer($s, $text, $history);
    // v1.2.5: strip markdown kalau rule no_asterisk aktif (WA channel)
    $answer = stripMarkdownIfEnabled($answer, $s);
    $deiAiError = false;   // v1.2.17
    if (!$ok || trim($answer) === '') {
        $answer = 'Maaf, saya sedang mengalami gangguan. Silakan coba lagi sebentar lagi.';
        $deiAiError = true;
    } else {
        recordUsage($usage);
    }
    waSend($wa, $from, $answer);

    if ($keepCtx) {
        $history[] = ['role' => 'user', 'content' => $text];
        $history[] = ['role' => 'assistant', 'content' => $answer];
        waSaveHistory($from, $history);
    }

    $logs = readJson(LOG_FILE, []);
    array_unshift($logs, array_merge($logBase, ['a' => $answer], $deiAiError ? ['ai_error' => true] : []));  // v1.2.17
    writeJson(LOG_FILE, array_slice($logs, 0, $logLimit));

    // v1.2.20: kalau percakapan sudah mencapai ambang pesan dan belum
    // punya kartu lead, jalankan analisa SEKALI. Non-blocking —
    // kegagalan analisa tidak boleh mengganggu balasan ke customer.
    if (!$deiAiError) {
        try {
            $deiLeadNum = preg_replace('/\D/', '', (string)$from);
            $deiLeadCount = 0;
            foreach ($logs as $deiLogRow) {
                if (($deiLogRow['channel'] ?? '') !== 'whatsapp') continue;
                if (preg_replace('/\D/', '', (string)($deiLogRow['ip'] ?? '')) === $deiLeadNum) $deiLeadCount++;
            }
            if ($deiLeadCount >= LEAD_TRIGGER_MSGS) {
                leadAnalyzeNumber($s, $from, $logs, false);
            }
        } catch (\Throwable $e) { error_log('lead analyze: ' . $e->getMessage()); }
    }
    tgNotify($s, "\xF0\x9F\x93\xA9 [WhatsApp] " . $from . ":\n\"" . $text . "\"\n\xE2\x9C\x85 dijawab bot");
}

// Per-number short conversation memory (flat-file, expires after 6h idle).
function waSessionFile($from) {
    return WA_SESSIONS_DIR . '/' . preg_replace('/[^0-9]/', '', (string)$from) . '.json';
}
function waLoadHistory($from) {
    $f = waSessionFile($from);
    if (!is_file($f)) return [];
    $d = json_decode(@file_get_contents($f), true);
    if (!is_array($d) || empty($d['turns'])) return [];
    if (($d['ts'] ?? 0) < time() - 6 * 3600) return [];
    return $d['turns'];
}
function waSaveHistory($from, $turns) {
    if (!is_dir(WA_SESSIONS_DIR)) @mkdir(WA_SESSIONS_DIR, 0755, true);
    @file_put_contents(waSessionFile($from), json_encode(['ts' => time(), 'turns' => array_slice($turns, -16)], JSON_UNESCAPED_UNICODE), LOCK_EX);
}

// Send a 200 to Meta immediately and detach, so the webhook never times out
// while we call the AI. Only used when fastcgi_finish_request() is available
// (PHP-FPM). Otherwise the caller processes synchronously and replies at the end.
function respondAndContinue($body = 'EVENT_RECEIVED') {
    @ignore_user_abort(true);
    http_response_code(200);
    header('Content-Type: text/plain; charset=utf-8');
    header('Content-Length: ' . strlen($body));
    header('Connection: close');
    echo $body;
    fastcgi_finish_request();
}

/* ----------------------------------------------------------------------------
 *  Handoff (per-number bot/human mode) + Telegram notifications
 * ------------------------------------------------------------------------- */
function waNormNum($n) { return preg_replace('/[^0-9]/', '', (string)$n); }

function waGetMode($from) {
    $modes = readJson(WA_MODES_FILE, []);
    $k = waNormNum($from);
    return (isset($modes[$k]['mode']) && $modes[$k]['mode'] === 'human') ? 'human' : 'bot';
}
function waSetMode($from, $mode) {
    $modes = readJson(WA_MODES_FILE, []);
    $k = waNormNum($from);
    if ($mode === 'human') {
        $modes[$k] = ['mode' => 'human', 'ts' => time()];
    } else {
        unset($modes[$k]); // bot is the default → remove entry
    }
    writeJson(WA_MODES_FILE, $modes);
}

// v1.2.37: berapa lama mode manusia bertahan tanpa aktivitas agent.
// Dihitung dari waktu waSetMode('human') terakhir — yaitu saat handoff terjadi
// atau saat agent membalas manual. Pesan dari tamu TIDAK memperpanjangnya:
// kalau tamu terus mengirim pesan tapi tidak ada yang menjawab, justru itulah
// saat bot paling perlu mengambil alih.
define('WA_MODE_IDLE_SEC', 3600);   // 1 jam

// Kembalikan ke mode bot untuk nomor yang sudah lama diam di mode manusia.
// Nomor yang masih dipegang agent (ada claim) DILEWATI — percakapan itu punya
// aturannya sendiri lewat waClaimAutoProcess (lepas otomatis 30 menit), dan bot
// tidak boleh menyela pekerjaan yang sedang berjalan.
function waModeSweepIdle() {
    $modes = readJson(WA_MODES_FILE, []);
    if (empty($modes) || !is_array($modes)) return 0;
    $claims = readJson(waClaimFile(), []);
    if (!is_array($claims)) $claims = [];
    $now = time();
    $n = 0;
    foreach ($modes as $k => $m) {
        if (!is_array($m) || ($m['mode'] ?? '') !== 'human') continue;
        if (!empty($claims[$k])) continue;                     // masih dipegang agent
        $ts = (int)($m['ts'] ?? 0);
        if ($ts > 0 && ($now - $ts) < WA_MODE_IDLE_SEC) continue;
        unset($modes[$k]);                                     // bot = bawaan
        $n++;
    }
    if ($n > 0) {
        writeJson(WA_MODES_FILE, $modes);
        error_log('wa: ' . $n . ' nomor kembali ke mode bot (manual idle > '
                  . (int)(WA_MODE_IDLE_SEC / 60) . ' menit)');
    }
    return $n;
}

// ============================================================================
// === v1.2.0 WA Claim System — Helper Functions ==============================
// ============================================================================

/** Path ke file audit log WA claim. */
function waAuditLogFile() {
    return DATA_DIR . '/wa-audit-log.json';
}

/** Path ke file claim state (per nomor). Reuse pattern WA_MODES_FILE style. */
function waClaimFile() {
    return DATA_DIR . '/wa-claims.json';
}

/** Get claim state untuk 1 nomor. Return null kalau tidak claimed. */
function waClaimGet($number) {
    $number = waNormNum($number);
    if ($number === '') return null;
    $claims = readJson(waClaimFile(), []);
    return $claims[$number] ?? null;
}

/** Get semua claim state. Return array [number => claim_data]. */
function waClaimGetAll() {
    return readJson(waClaimFile(), []);
}

/** Set claim state untuk 1 nomor. Pass null untuk release (hapus entry). */
function waClaimSet($number, $claim) {
    $number = waNormNum($number);
    if ($number === '') return false;
    $claims = readJson(waClaimFile(), []);
    if ($claim === null) {
        unset($claims[$number]);
        // Sinkronkan mode ke bot supaya konsisten
        waSetMode($number, 'bot');
    } else {
        $claims[$number] = $claim;
        // Sinkronkan mode ke human supaya bot tidak balas
        waSetMode($number, 'human');
    }
    writeJson(waClaimFile(), $claims);
    return true;
}

/** Update last_agent_activity untuk 1 nomor (dipanggil saat agent kirim manual reply). */
function waClaimTouchActivity($number, $agent) {
    $number = waNormNum($number);
    if ($number === '') return;
    $claims = readJson(waClaimFile(), []);
    if (!isset($claims[$number])) return;
    if (($claims[$number]['agent_username'] ?? '') !== $agent) return;
    $claims[$number]['last_agent_activity'] = time();
    writeJson(waClaimFile(), $claims);
}

/** Write audit log entry. Keep last 500 entries. */
function waAuditLog($action, $agent, $number, $extra = []) {
    $entries = readJson(waAuditLogFile(), []);
    $entry = [
        'ts' => date('Y-m-d H:i:s'),
        'action' => $action,
        'agent' => $agent,
        'number' => waNormNum($number),
    ];
    if (!empty($extra)) $entry['extra'] = $extra;
    array_unshift($entries, $entry);
    $entries = array_slice($entries, 0, 500);
    writeJson(waAuditLogFile(), $entries);
}

/**
 * Auto-process expired claims + takeover requests.
 * - mode=human AND last_agent_activity > 30 menit → auto release
 * - takeover_request pending > 5 menit → auto approve
 * Return: [released_count, approved_count]
 */
function waClaimAutoProcess() {
    $claims = readJson(waClaimFile(), []);
    if (empty($claims)) return [0, 0];

    $now = time();
    $INACTIVITY_TIMEOUT = 30 * 60;  // 30 menit
    $TAKEOVER_TIMEOUT = 5 * 60;     // 5 menit
    $released = 0;
    $approved = 0;
    $changed = false;

    foreach ($claims as $num => $claim) {
        // 1. Auto-approve takeover request
        if (!empty($claim['takeover_request'])) {
            $req = $claim['takeover_request'];
            if ($now - ($req['requested_at'] ?? 0) > $TAKEOVER_TIMEOUT) {
                $oldAgent = $claim['agent_username'] ?? 'unknown';
                $claim['agent_username'] = $req['requester'];
                $claim['claimed_at'] = $now;
                $claim['last_agent_activity'] = $now;
                unset($claim['takeover_request']);
                waAuditLog('takeover_auto_approve', $req['requester'], $num, [
                    'from_agent' => $oldAgent,
                    'reason' => $req['reason'] ?? '',
                ]);
                $claims[$num] = $claim;
                $changed = true;
                $approved++;
            }
        }

        // 2. Auto-release kalau inactivity
        $lastActivity = $claim['last_agent_activity'] ?? $claim['claimed_at'] ?? 0;
        if ($now - $lastActivity > $INACTIVITY_TIMEOUT) {
            waAuditLog('auto_release', $claim['agent_username'] ?? 'unknown', $num, [
                'inactivity_seconds' => $now - $lastActivity,
            ]);
            unset($claims[$num]);
            waSetMode($num, 'bot');
            $changed = true;
            $released++;
        }
    }

    if ($changed) writeJson(waClaimFile(), $claims);
    return [$released, $approved];
}

// === /v1.2.0 WA Claim System Helpers ========================================

// Does the message contain a handoff keyword? Single words match on word
// boundaries; multi-word phrases match as substring.
function waMatchHandoff($text, $keywords) {
    $t = ' ' . mb_strtolower(trim($text)) . ' ';
    $t = preg_replace('/[^\p{L}\p{N}]+/u', ' ', $t);
    foreach ($keywords as $kw) {
        $kw = mb_strtolower(trim($kw));
        if ($kw === '') continue;
        if (strpos($kw, ' ') !== false) {
            if (mb_strpos($t, $kw) !== false) return true;       // phrase
        } else {
            if (mb_strpos($t, ' ' . $kw . ' ') !== false) return true; // whole word
        }
    }
    return false;
}

// Send a Telegram notification (best-effort, never blocks the flow).
function tgNotify($s, $text) {
    $tg = is_array($s['telegram'] ?? null) ? $s['telegram'] : [];
    if (empty($tg['enabled']) || empty($tg['bot_token']) || empty($tg['chat_id'])) return false;
    $url = 'https://api.telegram.org/bot' . $tg['bot_token'] . '/sendMessage';
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_TIMEOUT        => 8,
        CURLOPT_POSTFIELDS     => http_build_query([
            'chat_id' => $tg['chat_id'],
            'text'    => $text,
            'disable_web_page_preview' => 'true',
        ]),
    ]);
    curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return $code >= 200 && $code < 300;
}

/* ============================================================================
 *  ROUTER
 * ========================================================================= */
switch ($action) {

    /* ---------- PUBLIC: widget bootstrap (no secrets) ---------- */
    case 'bootstrap': {
        $s = getSettings();
        jsonOut([
            'ok' => true,
            'config' => [
                'chatbot_enabled'  => (bool)($s['widget']['chatbot_enabled'] ?? true),
                'whatsapp_enabled' => (bool)($s['widget']['whatsapp_enabled'] ?? true),
                'whatsapp_number'  => $s['widget']['whatsapp_number'] ?? '',
                'whatsapp_message' => $s['widget']['whatsapp_message'] ?? '',
                'bot' => [
                    'bot_name'      => $s['bot']['bot_name'] ?? 'Assistant',
                    'greeting'      => $s['bot']['greeting'] ?? 'Halo!',
                    'quick_replies' => $s['bot']['quick_replies'] ?? [],
                ],
                'appearance' => [
                    'primary_color' => $s['appearance']['primary_color'] ?? '#140383',
                    'avatar_type'      => $s['appearance']['avatar_type']      ?? ($s['appearance']['avatar_image'] ?? '' ? 'image' : 'emoji'),
                    'avatar_emoji'     => $s['appearance']['avatar_emoji']     ?? '🤖',
                    'avatar_icon_name' => $s['appearance']['avatar_icon_name'] ?? 'bot',
                    'avatar_image'     => $s['appearance']['avatar_image']     ?? '',
                    'position'      => $s['appearance']['position'] ?? 'right',
                    'offset_bottom' => (int)($s['appearance']['offset_bottom'] ?? 24),
                    'offset_right'  => (int)($s['appearance']['offset_right'] ?? 24),
                ],
            ],
        ]);
        break;
    }

    /* ---------- PUBLIC: chat ---------- */
    case 'chat': {
        if ($_SERVER['REQUEST_METHOD'] !== 'POST') jsonOut(['ok' => false, 'error' => 'Method not allowed'], 405);
        $s = getSettings();
        // v1.2.4: silent auth check — kalau admin dashboard test (via X-Auth-Token), skip chatbot_enabled check
        $adminTestUser = getAuthenticatedUserSilent();
        $isAdminTest = $adminTestUser && in_array(($adminTestUser['role'] ?? ''), ['super_admin', 'admin', 'wa_agent'], true);
        if (!$isAdminTest && !($s['widget']['chatbot_enabled'] ?? true)) {
            jsonOut(['ok' => false, 'error' => 'Chatbot sedang dinonaktifkan.'], 403);
        }

        // v1.1.3: license enforcement (cache 24h, lazy refresh)
        $lic = getLicenseStatus($s);
        if ($lic['status'] === 'suspended') {
            jsonOut(['ok' => true, 'answer' => $lic['message'] ?: LIC_DEFAULT_SUSPEND_MSG, 'kb_used' => 0, 'suspended' => true]);
        }
        // v1.1.4: cap enforcement (cache 24h, tiered: 90%=graceful, 100%=halt total)
        $cap = getCapStatus($s);
        if ($cap['reached'] || $cap['warning']) {
            // Both 90%+ and 100%+ get the cap message (no Claude call → no token cost)
            // The difference: 100% also halts (already true since we return here), 90-99% returns same message
            jsonOut(['ok' => true, 'answer' => $cap['message'] ?: CAP_DEFAULT_MSG, 'kb_used' => 0, 'cap_reached' => true]);
        }
        // 'expired' = still serves chat normally (banner shown in dashboard, not to visitors)
        // 'active' = normal flow

        $ip = clientIp();
        $limit = (int)($s['api']['rate_limit'] ?? 20);
        if (!checkRateLimit($ip, $limit)) {
            jsonOut(['ok' => false, 'error' => 'Terlalu banyak permintaan. Coba lagi nanti.'], 429);
        }

        $in = bodyInput();
        $message = trim($in['message'] ?? '');
        if ($message === '') jsonOut(['ok' => false, 'error' => 'Pesan kosong.'], 400);
        if (mb_strlen($message) > 2000) $message = mb_substr($message, 0, 2000);

        $history = is_array($in['history'] ?? null) ? $in['history'] : [];
        $utm = is_array($in['utm'] ?? null) ? $in['utm'] : [];

        list($ok, $answer, $kbUsed, $usage) = generateAnswer($s, $message, $history);
        // v1.2.5: strip markdown kalau rule no_asterisk aktif
        $answer = stripMarkdownIfEnabled($answer, $s);
        if (!$ok) {
            // v1.2.17: sebelumnya kegagalan AI di chat web LANGSUNG jsonOut tanpa
            // menulis log — kejadiannya hilang tanpa jejak. Sekarang dicatat.
            try {
                $failLogs = readJson(LOG_FILE, []);
                array_unshift($failLogs, [
                    'ts'       => date('Y-m-d H:i:s'),
                    'q'        => $message,
                    'a'        => $answer,
                    'ip'       => $ip ?? '',
                    'channel'  => 'web',
                    'ai_error' => true,
                ]);
                $failLimit = (int)($s['api']['log_limit'] ?? 500);
                writeJson(LOG_FILE, array_slice($failLogs, 0, $failLimit));
            } catch (\Throwable $e) { error_log('log ai_error web: ' . $e->getMessage()); }
            jsonOut(['ok' => false, 'error' => 'Maaf, terjadi gangguan. ' . $answer], 502);
        }
        recordUsage($usage);

        // Log the conversation with UTM
        $logs = readJson(LOG_FILE, []);
        array_unshift($logs, [
            'ts'           => date('Y-m-d H:i:s'),
            'q'            => $message,
            'a'            => $answer,
            'ip'           => $ip,
            'channel'      => 'web',
            'utm_source'   => substr((string)($utm['utm_source'] ?? ''), 0, 120),
            'utm_medium'   => substr((string)($utm['utm_medium'] ?? ''), 0, 120),
            'utm_campaign' => substr((string)($utm['utm_campaign'] ?? ''), 0, 120),
            'page'         => substr((string)($utm['page'] ?? ''), 0, 300),
            'referrer'     => substr((string)($utm['referrer'] ?? ''), 0, 300),
        ]);
        $logLimit = (int)($s['api']['log_limit'] ?? 500);
        $logs = array_slice($logs, 0, $logLimit);
        writeJson(LOG_FILE, $logs);

        // v1.2.11: push notif chat web masuk (tiap pesan) — tiru pola WA (Fase 3)
        try {
            $deiWebPushFile = DATA_DIR . '/push-subs.json';
            if (file_exists($deiWebPushFile)) {
                $deiWebSubs = json_decode(file_get_contents($deiWebPushFile), true);
                if (is_array($deiWebSubs) && !empty($deiWebSubs)) {
                    $deiWebPreview = mb_substr(trim($message), 0, 80);
                    $deiWebTopic = detectTopicFromMessage($message);  // v1.2.12: auto-assign by topic
                    $deiWebTargets = getPushTargetsByTopic($deiWebTopic, array_keys($deiWebSubs));
                    sendPushToUsers($deiWebTargets, 'Chat web baru', $deiWebPreview, deiDashboardUrl());
                }
            }
        } catch (\Throwable $e) { error_log('web push hook: ' . $e->getMessage()); }

        $tg = is_array($s['telegram'] ?? null) ? $s['telegram'] : [];
        if (!empty($tg['notify_web'])) {
            tgNotify($s, "\xF0\x9F\x93\xA9 [Web] " . $ip . ":\n\"" . $message . "\"\n\xE2\x9C\x85 dijawab bot");
        }

        jsonOut(['ok' => true, 'answer' => $answer, 'kb_used' => $kbUsed]);
        break;
    }

    /* ---------- PUBLIC: WhatsApp Cloud API webhook ---------- */
    case 'wa_webhook': {
        $s  = getSettings();
        $wa = waConf($s);

        // GET — Meta verification handshake (hub.* arrive as hub_* in PHP).
        if ($_SERVER['REQUEST_METHOD'] === 'GET') {
            $mode      = $_GET['hub_mode'] ?? '';
            $token     = $_GET['hub_verify_token'] ?? '';
            $challenge = $_GET['hub_challenge'] ?? '';
            $expected  = (string)($wa['verify_token'] ?? '');
            if ($mode === 'subscribe' && $expected !== '' && hash_equals($expected, (string)$token)) {
                header('Content-Type: text/plain');
                echo $challenge;
                exit;
            }
            http_response_code(403);
            echo 'Forbidden';
            exit;
        }

        if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); exit; }

        $raw = file_get_contents('php://input');
        if (!waVerifySignature($raw, $wa['app_secret'] ?? '')) {
            http_response_code(403);
            echo 'bad signature';
            exit;
        }

        // Acknowledge Meta right away on PHP-FPM, then keep working in the
        // background. On other SAPIs, process synchronously and reply at the end
        // (fast enough for Meta's window since Haiku replies in a few seconds).
        $earlyAck = function_exists('fastcgi_finish_request');
        if ($earlyAck) respondAndContinue('EVENT_RECEIVED');
        @set_time_limit(60);

        if (!($wa['enabled'] ?? false)) { if (!$earlyAck) { echo 'EVENT_RECEIVED'; } exit; }
        // v1.2.36: tenant ini memakai penyedia lain — abaikan kiriman Meta,
        // supaya pesan tidak masuk lewat satu nomor lalu dibalas dari nomor lain.
        if (($wa['provider'] ?? 'meta') !== 'meta') { if (!$earlyAck) { echo 'EVENT_RECEIVED'; } exit; }

        $payload  = json_decode($raw, true);
        $logLimit = (int)($s['api']['log_limit'] ?? 500);
        $keepCtx  = ($wa['keep_context'] ?? true);

        foreach (($payload['entry'] ?? []) as $entry) {
            foreach (($entry['changes'] ?? []) as $change) {
                $messages = $change['value']['messages'] ?? [];
                // v1.2.19: nama profil WhatsApp ada di value.contacts (sejajar messages),
                // bukan di dalam tiap pesan. Petakan wa_id -> nama dulu.
                $waProfileNames = [];
                foreach (($change['value']['contacts'] ?? []) as $wc) {
                    $wcId = preg_replace('/\D/', '', (string)($wc['wa_id'] ?? ''));
                    $wcNm = trim((string)($wc['profile']['name'] ?? ''));
                    if ($wcId !== '' && $wcNm !== '') $waProfileNames[$wcId] = $wcNm;
                }
                foreach ($messages as $msg) {
                    $from = $msg['from'] ?? '';
                    if ($from === '') continue;
                    // v1.2.19: simpan nama kontak (tidak menimpa koreksi manual)
                    $deiFromKey = preg_replace('/\D/', '', (string)$from);
                    $deiWaName  = $waProfileNames[$deiFromKey] ?? '';
                    try { waSaveContact($from, $deiWaName); }
                    catch (\Throwable $e) { error_log('waSaveContact: ' . $e->getMessage()); }

                    if (($msg['type'] ?? '') !== 'text') {
                        waSend($wa, $from, 'Maaf, untuk saat ini saya hanya bisa membalas pesan teks.');
                        continue;
                    }
                    $text = trim($msg['text']['body'] ?? '');
                    if ($text === '') continue;
                    // v1.2.36: alur pemrosesan dipindah ke fungsi bersama
                    waProcessIncoming($s, $wa, $from, $text, $deiWaName, $change['value']['metadata'] ?? []);
                }
            }
        }
        if (!$earlyAck) { echo 'EVENT_RECEIVED'; }
        exit;
    }

    /* ---------- PUBLIC: webhook Fonnte (penyedia alternatif) ---------- */
    // Jalur TERPISAH dari webhook Meta. Kalau bagian ini bermasalah, tenant
    // yang memakai Meta tidak ikut terganggu.
    case 'wa_webhook_fonnte': {
        $s  = getSettings();
        $wa = waConf($s);

        if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo 'method not allowed'; exit; }

        // LAPIS 1 — kunci rahasia di URL.
        // Fonnte tidak menandatangani kirimannya seperti Meta, jadi alamat ini
        // harus dijaga sendiri. Tanpa penjagaan, siapa pun yang tahu alamatnya
        // bisa menyuntikkan percakapan palsu: memakan kuota klien dan mengotori
        // data leads.
        $kunci = (string)($wa['fonnte_webhook_key'] ?? '');
        if ($kunci === '' || !hash_equals($kunci, (string)($_GET['key'] ?? ''))) {
            http_response_code(403); echo 'forbidden'; exit;
        }

        $raw = file_get_contents('php://input');

        $earlyAck = function_exists('fastcgi_finish_request');
        if ($earlyAck) respondAndContinue('OK');
        @set_time_limit(60);

        if (($wa['provider'] ?? 'meta') !== 'fonnte') { if (!$earlyAck) { echo 'OK'; } exit; }
        if (!($wa['enabled'] ?? false))               { if (!$earlyAck) { echo 'OK'; } exit; }

        // Fonnte dapat mengirim JSON maupun form biasa — terima keduanya.
        $d = json_decode($raw, true);
        if (!is_array($d)) $d = is_array($_POST) ? $_POST : [];

        // Bentuk medan belum diverifikasi langsung, jadi dibaca longgar.
        // Nyalakan fonnte_debug di pengaturan untuk melihat kiriman mentahnya.
        if (!empty($wa['fonnte_debug'])) {
            error_log('fonnte mentah: ' . mb_substr($raw !== '' ? $raw : json_encode($_POST), 0, 500));
        }

        // Pesan GRUP diabaikan. Nomor bot yang dimasukkan ke grup akan menjawab
        // setiap pesan di sana — berisik, memakan kuota klien, dan pola semacam
        // itu justru yang meningkatkan risiko pemblokiran nomor.
        if (!empty($d['isgroup'])) {
            if (!$earlyAck) { echo 'OK'; }
            exit;
        }

        // Medan sesuai format Fonnte yang sudah diverifikasi.
        // CATATAN: medan 'text' SENGAJA TIDAK dipakai — isinya keterangan jenis
        // pesan ("non-button message"), bukan isi pesan tamu.
        $from = '';
        foreach (['sender', 'pengirim'] as $k) {
            if (!empty($d[$k])) { $from = preg_replace('/\D/', '', (string)$d[$k]); break; }
        }
        $text = '';
        foreach (['message', 'pesan'] as $k) {
            if (isset($d[$k]) && trim((string)$d[$k]) !== '') { $text = trim((string)$d[$k]); break; }
        }
        $nama = '';
        foreach (['name', 'pushname'] as $k) {
            if (!empty($d[$k])) { $nama = trim((string)$d[$k]); break; }
        }

        // Fonnte memakai mode "lid" (pengenal privasi WhatsApp). Kalau suatu saat
        // 'sender' berisi LID alih-alih nomor, tolak daripada memasukkan data
        // sampah ke log percakapan.
        if ($from === '' || !preg_match('/^\d{8,15}$/', $from)) {
            error_log('fonnte: nomor pengirim tidak wajar - ' . mb_substr($raw !== '' ? $raw : json_encode($_POST), 0, 300));
            if (!$earlyAck) { echo 'OK'; }
            exit;
        }

        // Pesan non-teks dibalas sama seperti jalur Meta.
        $jenis = trim((string)($d['type'] ?? ''));
        if (($jenis !== '' && $jenis !== 'text') || $text === '') {
            waSend($wa, $from, 'Maaf, untuk saat ini saya hanya bisa membalas pesan teks.');
            if (!$earlyAck) { echo 'OK'; }
            exit;
        }

        // LAPIS 2 — cocokkan nomor perangkat kalau tersimpan.
        $devTersimpan = preg_replace('/\D/', '', (string)($wa['fonnte_device'] ?? ''));
        if ($devTersimpan !== '') {
            $devKiriman = preg_replace('/\D/', '', (string)($d['device'] ?? ''));
            if ($devKiriman !== '' && $devKiriman !== $devTersimpan) {
                error_log('fonnte: perangkat tidak cocok (' . $devKiriman . ')');
                if (!$earlyAck) { echo 'OK'; }
                exit;
            }
        }

        // Alur pemrosesan sama persis dengan Meta (Fase 1).
        // $metaInfo dikosongkan sehingga tracker WA-to-Ads tidak aktif di sini.
        waProcessIncoming($s, $wa, $from, $text, $nama, []);

        if (!$earlyAck) { echo 'OK'; }
        exit;
    }

    /* ---------- ADMIN: WhatsApp conversations (handoff inbox) ---------- */
    case 'wa_conversations': {
        requireAuth(['super_admin','admin','wa_agent']);
        $logs = readJson(LOG_FILE, []);
        $byNum = [];
        foreach ($logs as $e) {                       // logs are newest-first
            if (($e['channel'] ?? '') !== 'whatsapp') continue;
            $num = waNormNum($e['ip'] ?? '');
            if ($num === '') continue;
            if (!isset($byNum[$num])) {
                $byNum[$num] = [
                    'number'          => $num,
                    'last_ts'         => $e['ts'] ?? '',
                    'last_text'       => ($e['q'] ?? '') !== '' ? $e['q'] : ($e['a'] ?? ''),
                    'awaiting'        => !empty($e['awaiting']),
                    'last_inbound_ts' => null,
                ];
            }
            if ($byNum[$num]['last_inbound_ts'] === null && ($e['q'] ?? '') !== '') {
                $byNum[$num]['last_inbound_ts'] = $e['ts'] ?? '';
            }
        }
        $out = [];
        foreach ($byNum as $num => $c) {
            $c['mode'] = waGetMode($num);
            $inTs = $c['last_inbound_ts'] ? strtotime($c['last_inbound_ts']) : 0;
            $c['window_open'] = waWindowSelaluTerbuka() || ($inTs > 0 && (time() - $inTs) <= 24 * 3600);   // v1.2.36
            unset($c['last_inbound_ts']);
            $out[] = $c;
        }
        usort($out, function ($a, $b) { return strcmp($b['last_ts'], $a['last_ts']); });
        jsonOut(['ok' => true, 'conversations' => array_slice($out, 0, 50)]);
        break;
    }

    /* ---------- ADMIN: one WhatsApp thread ---------- */
    /* ---------- v1.2.22: daftar harga ---------- */
    case 'get_pricelist': {
        requireAuth(['super_admin', 'admin']);
        $pl = pricelistGet();
        jsonOut(['ok' => true, 'items' => $pl['items'], 'updated_at' => $pl['updated_at'], 'updated_by' => $pl['updated_by']]);
        break;
    }

    case 'save_pricelist': {
        $me = requireAuth(['super_admin', 'admin']);
        $in = bodyInput();
        $items = is_array($in['items'] ?? null) ? $in['items'] : [];
        $clean = [];
        foreach ($items as $it) {
            if (!is_array($it)) continue;
            $nama = trim((string)($it['item'] ?? ''));
            if ($nama === '') continue;   // baris tanpa nama dibuang
            $clean[] = [
                'id'    => (string)($it['id'] ?? ('pr_' . substr(md5(uniqid('', true)), 0, 8))),
                'item'  => mb_substr($nama, 0, 150),
                'price' => mb_substr(trim((string)($it['price'] ?? '')), 0, 100),
                'note'  => mb_substr(trim((string)($it['note'] ?? '')), 0, 200),
            ];
        }
        writeJson(PRICELIST_FILE, [
            'items'      => $clean,
            'updated_at' => date('Y-m-d H:i:s'),
            'updated_by' => (string)($me['username'] ?? ''),
        ]);
        jsonOut(['ok' => true, 'count' => count($clean)]);
        break;
    }

    /* ---------- v1.2.20: leads ---------- */
    case 'get_leads': {
        // v1.2.29: agent boleh melihat — merekalah yang menindaklanjuti
        requireAuth(['super_admin', 'admin', 'wa_agent']);
        $all = leadsGetAll();
        $contacts = waGetContacts();
        $out = [];
        foreach ($all as $num => $l) {
            if (!is_array($l)) continue;
            $nm = waContactName($num, $contacts);
            if ($nm === '') $nm = trim((string)($l['extracted']['nama'] ?? ''));
            $out[] = [
                'number'        => (string)$num,
                'name'          => $nm,
                'status'        => (string)($l['status'] ?? 'baru'),
                'note'          => (string)($l['note'] ?? ''),
                'extracted'     => is_array($l['extracted'] ?? null) ? $l['extracted'] : [],
                'analyzed_at'   => (string)($l['analyzed_at'] ?? ''),
                'updated_at'    => (string)($l['updated_at'] ?? ''),
                'contact_stage' => waContactStage($num, $contacts),   // v1.2.39
                'contact_vip'   => waContactVip($num, $contacts),     // v1.2.39
            ];
        }
        usort($out, function ($a, $b) { return strcmp($b['updated_at'], $a['updated_at']); });
        jsonOut(['ok' => true, 'leads' => $out, 'count' => count($out)]);
        break;
    }

    case 'save_lead': {
        // v1.2.29: agent boleh mengubah status & menulis catatan
        requireAuth(['super_admin', 'admin', 'wa_agent']);
        $in  = bodyInput();
        $num = preg_replace('/\D/', '', (string)($in['number'] ?? ''));
        if ($num === '') jsonOut(['ok' => false, 'error' => 'Nomor tidak valid.'], 400);
        $all = leadsGetAll();
        if (!isset($all[$num]) || !is_array($all[$num])) {
            jsonOut(['ok' => false, 'error' => 'Lead tidak ditemukan.'], 404);
        }
        if (isset($in['status'])) {
            $st = (string)$in['status'];
            if (!leadStatusValid($st)) jsonOut(['ok' => false, 'error' => 'Status tidak dikenal.'], 400);
            $all[$num]['status'] = $st;
        }
        if (isset($in['note'])) {
            $all[$num]['note'] = mb_substr(trim((string)$in['note']), 0, 1000);
        }
        $all[$num]['updated_at'] = date('Y-m-d H:i:s');
        writeJson(LEADS_FILE, $all);
        jsonOut(['ok' => true]);
        break;
    }

    case 'analyze_lead': {
        // Analisa manual (mis. percakapan lama sebelum fitur ini ada, atau
        // percakapan yang sudah berkembang jauh sejak analisa pertama).
        requireAuth(['super_admin', 'admin']);
        $in  = bodyInput();
        $num = preg_replace('/\D/', '', (string)($in['number'] ?? ''));
        if ($num === '') jsonOut(['ok' => false, 'error' => 'Nomor tidak valid.'], 400);
        $s = getSettings();
        if (empty($s['api']['claude_api_key'])) {
            jsonOut(['ok' => false, 'error' => 'API key Claude belum dikonfigurasi.'], 400);
        }
        $done = leadAnalyzeNumber($s, $num, null, true);
        if (!$done) jsonOut(['ok' => false, 'error' => 'Analisa gagal atau percakapan kosong.'], 500);
        jsonOut(['ok' => true]);
        break;
    }

    /* ---------- v1.2.31: pemeriksaan sesi ---------- */
    case 'auth_check': {
        // Sengaja seringan mungkin: tidak membaca berkas data apa pun selain
        // yang sudah dibaca requireAuth. Dipakai login.html untuk memastikan
        // token masih sah SEBELUM mengalihkan ke dashboard — tanpa ini, token
        // kedaluwarsa membuat halaman berputar antara login dan dashboard.
        // Tanpa daftar peran = berlaku untuk semua peran yang sudah login.
        $u = requireAuth();
        jsonOut(['ok' => true, 'username' => $u['username'] ?? '', 'role' => $u['role'] ?? '']);
        break;
    }

    /* ---------- v1.2.19: kontak WA ---------- */
    case 'get_contacts': {
        requireAuth(['super_admin', 'admin', 'wa_agent']);
        $all = waGetContacts();
        $out = [];
        foreach ($all as $num => $c) {
            if (!is_array($c)) continue;
            $out[] = [
                'number'      => (string)$num,
                'name'        => waContactName($num, $all),
                'name_wa'     => (string)($c['name_wa'] ?? ''),
                'name_manual' => (string)($c['name_manual'] ?? ''),
                'first_seen'  => (string)($c['first_seen'] ?? ''),
                'last_seen'   => (string)($c['last_seen'] ?? ''),
                'stage'       => waContactStage($num, $all),   // v1.2.39
                'vip'         => waContactVip($num, $all),     // v1.2.39
                'cust_name'   => (string)($c['cust_name'] ?? ''),   // v1.2.39 fase4
                'cust_dob'    => (string)($c['cust_dob'] ?? ''),    // v1.2.39 fase4
            ];
        }
        // terbaru dulu
        usort($out, function ($a, $b) { return strcmp($b['last_seen'], $a['last_seen']); });
        jsonOut(['ok' => true, 'contacts' => $out, 'count' => count($out)]);
        break;
    }

    case 'export_contacts': {
        // Ekspor menarik data pribadi customer keluar sistem -> dibatasi ke
        // super_admin/admin saja, dan dicatat jejaknya.
        $me = requireAuth(['super_admin', 'admin']);

        // Kumpulkan SEMUA nomor WA yang pernah muncul di log (bukan hanya yang
        // sudah punya nama), lalu gabungkan dengan nama dari wa-contacts.json.
        $seen = [];
        foreach (readJson(LOG_FILE, []) as $e) {
            if (($e['channel'] ?? '') !== 'whatsapp') continue;
            $n = preg_replace('/\D/', '', (string)($e['ip'] ?? ''));
            if ($n !== '' && !isset($seen[$n])) $seen[$n] = ($e['ts'] ?? '');
        }
        $contacts = waGetContacts();
        foreach ($contacts as $n => $c) {
            $n = preg_replace('/\D/', '', (string)$n);
            if ($n !== '' && !isset($seen[$n])) $seen[$n] = (string)($c['last_seen'] ?? '');
        }

        // Escape sesuai spesifikasi vCard: backslash, koma, titik-koma.
        $vEsc = function ($str) {
            $str = str_replace('\\', '\\\\', (string)$str);
            $str = str_replace(';', '\\;', $str);
            $str = str_replace(',', '\\,', $str);
            return str_replace(["\r", "\n"], ' ', $str);
        };

        $vcf = '';
        $n = 0;
        foreach ($seen as $num => $lastTs) {
            $nama = waContactName($num, $contacts);
            if ($nama === '') $nama = '+' . $num;   // tanpa nama -> pakai nomor
            $note = 'Kontak WhatsApp chatbot';
            if ($lastTs !== '') $note .= ' - terakhir aktif ' . substr($lastTs, 0, 10);
            // CRLF wajib per spesifikasi vCard
            $vcf .= "BEGIN:VCARD\r\n";
            $vcf .= "VERSION:3.0\r\n";
            $vcf .= 'FN:' . $vEsc($nama) . "\r\n";
            $vcf .= 'N:' . $vEsc($nama) . ";;;\r\n";
            $vcf .= 'TEL;TYPE=CELL:+' . $num . "\r\n";
            $vcf .= 'NOTE:' . $vEsc($note) . "\r\n";
            $vcf .= "END:VCARD\r\n";
            $n++;
        }

        error_log('export_contacts: ' . ($me['username'] ?? '?') . ' mengekspor ' . $n . ' kontak');
        jsonOut(['ok' => true, 'vcf' => $vcf, 'count' => $n]);
        break;
    }

    case 'save_contact': {
        requireAuth(['super_admin', 'admin', 'wa_agent']);
        $in  = bodyInput();
        $num = preg_replace('/\D/', '', (string)($in['number'] ?? ''));
        if ($num === '') jsonOut(['ok' => false, 'error' => 'Nomor tidak valid.'], 400);
        $nm  = trim((string)($in['name'] ?? ''));
        if (mb_strlen($nm) > 100) $nm = mb_substr($nm, 0, 100);
        $all = waGetContacts();
        $now = date('Y-m-d H:i:s');
        if (!isset($all[$num]) || !is_array($all[$num])) {
            $all[$num] = ['name_wa' => '', 'name_manual' => '', 'first_seen' => $now, 'last_seen' => $now];
        }
        $all[$num]['name_manual'] = $nm;   // kosong = kembali pakai nama profil WA
        writeJson(CONTACTS_FILE, $all);
        jsonOut(['ok' => true, 'number' => $num, 'name' => waContactName($num, $all)]);
        break;
    }

    case 'save_contact_stage': {
        requireAuth(['super_admin', 'admin', 'wa_agent']);
        $in  = bodyInput();
        $num = preg_replace('/\D/', '', (string)($in['number'] ?? ''));
        if ($num === '') jsonOut(['ok' => false, 'error' => 'Nomor tidak valid.'], 400);
        $stage = (string)($in['stage'] ?? '');
        if (!contactStageValid($stage)) jsonOut(['ok' => false, 'error' => 'Tag tidak dikenal.'], 400);
        $vip = !empty($in['vip']);
        waSetContactStage($num, $stage, $vip);
        $all = waGetContacts();
        jsonOut([
            'ok'     => true,
            'number' => $num,
            'stage'  => waContactStage($num, $all),
            'vip'    => waContactVip($num, $all),
        ]);
        break;
    }

    case 'save_contact_info': {
        requireAuth(['super_admin', 'admin', 'wa_agent']);
        $in  = bodyInput();
        $num = preg_replace('/\D/', '', (string)($in['number'] ?? ''));
        if ($num === '') jsonOut(['ok' => false, 'error' => 'Nomor tidak valid.'], 400);
        $custName = null; $custDob = null;
        if (isset($in['cust_name'])) $custName = (string)$in['cust_name'];
        if (isset($in['cust_dob'])) {
            $d = trim((string)$in['cust_dob']);
            if ($d !== '' && !preg_match('/^\d{4}-\d{2}-\d{2}$/', $d)) {
                jsonOut(['ok' => false, 'error' => 'Format tanggal lahir tidak valid (YYYY-MM-DD).'], 400);
            }
            $custDob = $d;
        }
        waSetContactInfo($num, $custName, $custDob);
        $all = waGetContacts();
        $c = $all[$num] ?? [];
        jsonOut([
            'ok'        => true,
            'number'    => $num,
            'cust_name' => (string)($c['cust_name'] ?? ''),
            'cust_dob'  => (string)($c['cust_dob'] ?? ''),
        ]);
        break;
    }

    case 'get_birthday_config': {
        // v1.2.39 fase8: dipakai halaman Kontak untuk tahu apakah fitur
        // ulang tahun boleh tampil, sekaligus mengambil template ucapan.
        // Dibuat terpisah dari get_settings karena get_settings dibatasi
        // super_admin/admin, sementara halaman Kontak juga dibuka wa_agent.
        // Tidak mengandung rahasia apa pun (cuma status aktif + teks ucapan).
        requireAuth(['super_admin', 'admin', 'wa_agent']);
        $s = getSettings();
        jsonOut([
            'ok'                => true,
            'wa_enabled'        => !empty($s['whatsapp_api']['enabled']),
            // v1.2.39 fase8b: fitur ulang tahun hanya untuk Fonnte -- Meta
            // menolak teks bebas di luar jendela 24 jam, jadi ucapan hampir
            // selalu gagal kirim kalau providernya Meta.
            'provider'          => (string)($s['whatsapp_api']['provider'] ?? 'meta'),
            'birthday_greeting' => (string)($s['bot']['birthday_greeting'] ?? ''),
        ]);
        break;
    }

    case 'wa_thread': {
        requireAuth(['super_admin','admin','wa_agent']);
        $num = waNormNum($_GET['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        $logs = readJson(LOG_FILE, []);
        $msgs = [];
        $lastInbound = 0;
        foreach ($logs as $e) {
            if (($e['channel'] ?? '') !== 'whatsapp') continue;
            if (waNormNum($e['ip'] ?? '') !== $num) continue;
            if ($lastInbound === 0 && ($e['q'] ?? '') !== '') $lastInbound = strtotime($e['ts']);
            $msgs[] = ['ts' => $e['ts'] ?? '', 'q' => $e['q'] ?? '', 'a' => $e['a'] ?? '', 'dir' => $e['dir'] ?? '', 'awaiting' => !empty($e['awaiting'])];
        }
        $msgs = array_reverse(array_slice($msgs, 0, 60)); // oldest → newest
        jsonOut([
            'ok' => true,
            'number' => $num,
            'mode' => waGetMode($num),
            'window_open' => waWindowSelaluTerbuka() || ($lastInbound > 0 && (time() - $lastInbound) <= 24 * 3600),   // v1.2.36
            'messages' => $msgs,
        ]);
        break;
    }

    /* ---------- ADMIN: take over / return to bot ---------- */
    case 'wa_set_mode': {
        requireAuth(['super_admin','admin','wa_agent']);
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        $mode = (($in['mode'] ?? '') === 'human') ? 'human' : 'bot';
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        waSetMode($num, $mode);
        jsonOut(['ok' => true, 'number' => $num, 'mode' => $mode]);
        break;
    }

    /* ---------- ADMIN: send a manual WhatsApp reply ---------- */
    case 'wa_send_manual': {
        requireAuth(['super_admin','admin','wa_agent']);
        $s = getSettings();
        $wa = waConf($s);
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        $text = trim($in['text'] ?? '');
        if ($num === '' || $text === '') jsonOut(['ok' => false, 'error' => 'number & text wajib'], 400);
        if (mb_strlen($text) > 4000) $text = mb_substr($text, 0, 4000);

        $logs = readJson(LOG_FILE, []);
        $lastInbound = 0;
        foreach ($logs as $e) {
            if (($e['channel'] ?? '') === 'whatsapp' && waNormNum($e['ip'] ?? '') === $num && ($e['q'] ?? '') !== '') {
                $lastInbound = strtotime($e['ts']); break;
            }
        }
        if ($lastInbound <= 0 || (time() - $lastInbound) > 24 * 3600) {
            if (!waWindowSelaluTerbuka()) jsonOut(['ok' => false, 'error' => 'Jendela 24 jam tertutup — WhatsApp tidak mengizinkan balasan teks bebas. Pelanggan harus mengirim pesan lagi terlebih dulu.'], 409);
        }

        if (!waSend($wa, $num, $text)) {
            jsonOut(['ok' => false, 'error' => 'Gagal mengirim via WhatsApp. Cek Access Token / Phone Number ID.'], 502);
        }
        waSetMode($num, 'human'); // replying manually = taking over
        if ($wa['keep_context'] ?? true) {
            $h = waLoadHistory($num);
            $h[] = ['role' => 'assistant', 'content' => $text];
            waSaveHistory($num, $h);
        }
        array_unshift($logs, [
            'ts' => date('Y-m-d H:i:s'), 'q' => '', 'a' => $text, 'ip' => $num,
            'channel' => 'whatsapp', 'dir' => 'manual',
            'utm_source' => 'whatsapp', 'utm_medium' => 'manual', 'utm_campaign' => '', 'page' => '', 'referrer' => '',
        ]);
        writeJson(LOG_FILE, array_slice($logs, 0, (int)($s['api']['log_limit'] ?? 500)));
        jsonOut(['ok' => true]);
        break;
    }

    /* ---------- AUTH: login ---------- */
    case 'login': {
        $in = bodyInput();
        $username = trim($in['username'] ?? '');
        $password = (string)($in['password'] ?? '');
        if ($username === '' || $password === '') {
            jsonOut(['ok' => false, 'error' => 'Username dan password wajib diisi.'], 400);
        }
        $remaining = lockoutCheck($username);
        if ($remaining > 0) {
            $mins = (int)ceil($remaining / 60);
            jsonOut(['ok' => false, 'error' => "Terlalu banyak percobaan. Coba lagi dalam $mins menit."], 429);
        }
        $users = readJson(USERS_FILE, []);
        foreach ($users as $idx => $u) {
            if (($u['username'] ?? '') !== $username) continue;
            $stored = (string)($u['password'] ?? '');
            $valid = false;
            if (strpos($stored, '$2y$') === 0 || strpos($stored, '$argon') === 0) {
                $valid = password_verify($password, $stored);
            } else {
                // Legacy plaintext — verify then upgrade to bcrypt
                $valid = hash_equals($stored, $password);
                if ($valid) {
                    $users[$idx]['password'] = password_hash($password, PASSWORD_DEFAULT);
                    writeJson(USERS_FILE, $users);
                }
            }
            if ($valid) {
                lockoutClear($username);
                // role migration on login too (so token carries new role)
                $role = $u['role'] ?? 'admin';
                if ($role === 'admin' && empty($u['migrated_3role'])) {
                    $users[$idx]['role'] = 'super_admin';
                    $users[$idx]['migrated_3role'] = true;
                    writeJson(USERS_FILE, $users);
                    $role = 'super_admin';
                } elseif ($role === 'editor' && empty($u['migrated_3role'])) {
                    $users[$idx]['role'] = 'admin';
                    $users[$idx]['migrated_3role'] = true;
                    writeJson(USERS_FILE, $users);
                    $role = 'admin';
                }
                jsonOut([
                    'ok' => true,
                    'token' => makeToken($username),
                    'user' => [
                        'username' => $username,
                        'name'     => $u['name'] ?? $username,
                        'role'     => $role,
                    ],
                ]);
            }
            break;
        }
        lockoutRecordFail($username);
        jsonOut(['ok' => false, 'error' => 'Username atau password salah.'], 401);
        break;
    }

    /* ---------- AUTH: validate session ---------- */
    case 'me': {
        $u = requireAuth();
        jsonOut(['ok' => true, 'user' => [
            'username' => $u['username'],
            'name'     => $u['name'] ?? $u['username'],
            'role'     => $u['role'] ?? 'editor',
        ]]);
        break;
    }

    /* ---------- get settings (super_admin + admin) ---------- */
    case 'get_settings': {
        $u = requireAuth(['super_admin', 'admin']);
        $role = $u['role'];
        $raw = getSettings();
        $s = $raw;
        // mask the API key
        $s['api']['claude_api_key'] = maskKey($raw['api']['claude_api_key'] ?? '');
        $s['api']['key_is_set'] = !empty($raw['api']['claude_api_key']);
        // mask WhatsApp secrets
        if (isset($s['whatsapp_api']) && is_array($s['whatsapp_api'])) {
            $s['whatsapp_api']['access_token'] = maskKey($raw['whatsapp_api']['access_token'] ?? '');
            $s['whatsapp_api']['app_secret']   = maskKey($raw['whatsapp_api']['app_secret'] ?? '');
            $s['whatsapp_api']['token_is_set'] = !empty($raw['whatsapp_api']['access_token']);
            // v1.2.36: token Fonnte diperlakukan sama seperti token Meta
            $s['whatsapp_api']['fonnte_token']        = maskKey($raw['whatsapp_api']['fonnte_token'] ?? '');
            $s['whatsapp_api']['fonnte_token_is_set'] = !empty($raw['whatsapp_api']['fonnte_token']);
        }
        if (isset($s['telegram']) && is_array($s['telegram'])) {
            $s['telegram']['bot_token'] = maskKey($raw['telegram']['bot_token'] ?? '');
            $s['telegram']['token_is_set'] = !empty($raw['telegram']['bot_token']);
        }
        // For admin (non super), also strip verify_token + phone_number_id values to placeholders
        // so the field can't be inspected even though Admin can't edit it.
        if ($role !== 'super_admin' && isset($s['whatsapp_api'])) {
            $s['whatsapp_api']['verify_token']    = $s['whatsapp_api']['verify_token']    ? '••••' : '';
            // phone_number_id is not a secret per se, but Admin can't edit; keep visibility off too.
            $s['whatsapp_api']['phone_number_id'] = $s['whatsapp_api']['phone_number_id'] ? '••••' : '';
            // v1.2.36: kunci webhook Fonnte juga rahasia — hanya super_admin yang perlu melihatnya
            $s['whatsapp_api']['fonnte_webhook_key'] = !empty($s['whatsapp_api']['fonnte_webhook_key']) ? '••••' : '';
        }
        jsonOut(['ok' => true, 'settings' => $s, 'role' => $role]);
        break;
    }

    /* ---------- save settings (3-role policy) ---------- */
    case 'save_settings': {
        $u = requireAuth(['super_admin', 'admin']);
        $role = $u['role'];
        $in = bodyInput();
        $incoming = is_array($in['settings'] ?? null) ? $in['settings'] : [];
        $current = getSettings();
        $merged  = $current;

        // Super Admin: full edit, preserve masked secrets.
        if ($role === 'super_admin') {
            // Preserve Claude API key if masked/empty submitted.
            if (isset($incoming['api']['claude_api_key'])) {
                $v = $incoming['api']['claude_api_key'];
                if (strpos($v, '•') !== false || $v === '') {
                    $incoming['api']['claude_api_key'] = $current['api']['claude_api_key'] ?? '';
                }
            }
            // Preserve WhatsApp secrets when masked/empty.
            foreach (['access_token', 'app_secret', 'fonnte_token'] as $secf) {   // v1.2.36
                if (isset($incoming['whatsapp_api'][$secf])) {
                    $v = $incoming['whatsapp_api'][$secf];
                    if (strpos($v, '•') !== false || $v === '') {
                        $incoming['whatsapp_api'][$secf] = $current['whatsapp_api'][$secf] ?? '';
                    }
                }
            }
            // v1.2.36: kunci webhook Fonnte dibuat otomatis saat penyedia ini
            // dipilih pertama kali, supaya tidak perlu dibuat manual di server.
            if (($incoming['whatsapp_api']['provider'] ?? '') === 'fonnte'
                && empty($incoming['whatsapp_api']['fonnte_webhook_key'])
                && empty($current['whatsapp_api']['fonnte_webhook_key'])) {
                $incoming['whatsapp_api']['fonnte_webhook_key'] = bin2hex(random_bytes(16));
            }

            // Preserve verify_token / phone_number_id when masked.
            foreach (['verify_token', 'phone_number_id', 'fonnte_webhook_key'] as $f) {   // v1.2.36
                if (isset($incoming['whatsapp_api'][$f])) {
                    $v = (string)$incoming['whatsapp_api'][$f];
                    if (strpos($v, '•') !== false) {
                        $incoming['whatsapp_api'][$f] = $current['whatsapp_api'][$f] ?? '';
                    }
                }
            }
            // Preserve Telegram bot token when masked/empty.
            if (isset($incoming['telegram']['bot_token'])) {
                $v = $incoming['telegram']['bot_token'];
                if (strpos($v, '•') !== false || $v === '') {
                    $incoming['telegram']['bot_token'] = $current['telegram']['bot_token'] ?? '';
                }
            }
            $merged = array_replace_recursive($current, $incoming);
        } else {
            // Admin: bot persona, appearance, widget toggles (non-secret), handoff. NO secrets / NO WA / NO Telegram.
            // v1.2.3: extend with structured form fields (additive, backward-compat)
            $allowedBot = ['bot_name', 'greeting', 'quick_replies', 'system_prompt', 'persona_company',
                           'user_address', 'language_style', 'languages', 'language_prompt_behavior',
                           'response_rules', 'fallback_behavior', 'birthday_greeting'];
            foreach ($allowedBot as $f) {
                if (isset($incoming['bot'][$f])) $merged['bot'][$f] = $incoming['bot'][$f];
            }
            if (isset($incoming['appearance']) && is_array($incoming['appearance'])) {
                $merged['appearance'] = array_replace($current['appearance'] ?? [], $incoming['appearance']);
            }
            // Widget toggles + WhatsApp floating button (non-secret). NOT whatsapp_api (Cloud API).
            $allowedWidget = ['chatbot_enabled', 'whatsapp_enabled', 'whatsapp_number', 'whatsapp_message'];
            foreach ($allowedWidget as $f) {
                if (isset($incoming['widget'][$f])) $merged['widget'][$f] = $incoming['widget'][$f];
            }
            // Handoff keywords + on/off.
            if (isset($incoming['handoff']) && is_array($incoming['handoff'])) {
                foreach (['enabled', 'keywords'] as $f) {
                    if (isset($incoming['handoff'][$f])) $merged['handoff'][$f] = $incoming['handoff'][$f];
                }
            }
            // Admin MAY tweak some api block items that aren't secrets (model, rate_limit, log_limit, max_tokens, kb_max_results).
            $allowedApi = ['model', 'max_tokens', 'rate_limit', 'kb_max_results', 'log_limit'];
            foreach ($allowedApi as $f) {
                if (isset($incoming['api'][$f])) $merged['api'][$f] = $incoming['api'][$f];
            }
            // EXPLICITLY ignore: api.claude_api_key, whatsapp_api.*, telegram.*
        }
        writeJson(SETTINGS_FILE, $merged);
        jsonOut(['ok' => true]);
        break;
    }

    /* ---------- knowledge base (admin only) ---------- */
    case 'get_kb': {
        requireAuth(['super_admin','admin']);
        jsonOut(['ok' => true, 'kb' => readJson(KB_FILE, [])]);
        break;
    }

    /* ---------- v1.2.13: kelola kategori notif ---------- */
    case 'get_categories': {
        requireAuth(['super_admin', 'admin']);
        jsonOut([
            'ok'         => true,
            'fixed'      => deiFixedCategories(),
            'custom'     => deiCustomCategories(),
            'categories' => deiAllCategories(),
        ]);
        break;
    }

    case 'add_category': {
        requireAuth(['super_admin']);
        $in  = bodyInput();
        $cat = trim((string)($in['category'] ?? ''));
        if ($cat === '') jsonOut(['ok' => false, 'error' => 'Nama kategori wajib diisi.'], 400);
        if (mb_strlen($cat) > 30) jsonOut(['ok' => false, 'error' => 'Nama kategori maksimal 30 karakter.'], 400);
        foreach (deiAllCategories() as $exist) {
            if (mb_strtolower($exist) === mb_strtolower($cat)) {
                jsonOut(['ok' => false, 'error' => 'Kategori "' . $exist . '" sudah ada.'], 400);
            }
        }
        $custom   = deiCustomCategories();
        $custom[] = $cat;
        writeJson(PUSH_CATEGORIES_FILE, array_values($custom));
        jsonOut(['ok' => true, 'categories' => deiAllCategories()]);
        break;
    }

    case 'delete_category': {
        requireAuth(['super_admin']);
        $in  = bodyInput();
        $cat = trim((string)($in['category'] ?? ''));
        if ($cat === '') jsonOut(['ok' => false, 'error' => 'Kategori tidak valid.'], 400);
        if (in_array($cat, deiFixedCategories(), true)) {
            jsonOut(['ok' => false, 'error' => 'Kategori bawaan tidak dapat dihapus.'], 400);
        }
        $custom = deiCustomCategories();
        if (!in_array($cat, $custom, true)) {
            jsonOut(['ok' => false, 'error' => 'Kategori tidak ditemukan.'], 404);
        }
        // Blokir kalau masih dipakai — hindari routing "mati diam-diam".
        $use = deiCategoryUsage($cat);
        if ($use['kb'] > 0 || $use['users'] > 0) {
            jsonOut(['ok' => false, 'error' => 'Tidak dapat dihapus: masih dipakai ' . $use['kb'] . ' entri KB dan ' . $use['users'] . ' pengguna. Lepaskan dulu pemakaiannya.'], 409);
        }
        $custom = array_values(array_filter($custom, function ($x) use ($cat) { return $x !== $cat; }));
        writeJson(PUSH_CATEGORIES_FILE, $custom);
        jsonOut(['ok' => true, 'categories' => deiAllCategories()]);
        break;
    }

    /* ---------- v1.2.24: pertanyaan yang belum terjawab ---------- */
    case 'kb_find_gaps': {
        requireAuth(['super_admin', 'admin']);

        // Frasa "menyerah" yang dipakai bot saat tidak punya informasi.
        $frasa = [
            'belum tersedia', 'tidak tersedia', 'belum ada informasi',
            'tidak ada informasi', 'tidak memiliki informasi',
            'hubungi tim', 'menghubungi tim', 'hubungi admin', 'kontak resmi',
            'tim kami akan', 'silakan hubungi', 'tidak dapat menemukan',
            'belum memiliki data', 'informasi lebih lanjut',
        ];
        // Kata umum yang dibuang saat menyusun kunci kelompok.
        $stop = ['yang','untuk','dengan','pada','dari','apakah','bagaimana','berapa',
                 'tolong','mohon','saya','ingin','tahu','bisa','bisakah','boleh',
                 'ada','adalah','itu','ini','dan','atau','di','ke','nya','kah',
                 'informasi','tentang','mengenai','jelaskan','ceritakan','berikan'];

        // Judul KB yang sudah ada — supaya tidak menyarankan yang sudah dipunyai.
        $kbAda = [];
        foreach (readJson(KB_FILE, []) as $e) {
            $t = mb_strtolower(trim((string)($e['title'] ?? '')));
            $t = preg_replace('/[^a-z0-9\s]/u', ' ', $t);
            $t = preg_replace('/\s+/', ' ', trim($t));
            if ($t !== '') $kbAda[$t] = true;
        }

        $grup = [];
        $dipindai = 0;
        foreach (readJson(LOG_FILE, []) as $e) {
            // kegagalan SISTEM bukan lubang pengetahuan — jangan ikut dihitung
            if (!empty($e['cap_reached']) || !empty($e['suspended']) || !empty($e['ai_error'])) continue;
            if (($e['dir'] ?? '') === 'manual') continue;   // balasan agent, bukan bot

            $q = trim((string)($e['q'] ?? ''));
            $a = mb_strtolower(trim((string)($e['a'] ?? '')));
            if ($q === '' || $a === '') continue;
            $dipindai++;

            $gagal = false;
            foreach ($frasa as $f) {
                if (mb_strpos($a, $f) !== false) { $gagal = true; break; }
            }
            if (!$gagal) continue;

            // kunci kelompok: kata penting, diurutkan -> tahan beda urutan kata
            $norm = mb_strtolower($q);
            $norm = preg_replace('/[^a-z0-9\s]/u', ' ', $norm);
            $kata = preg_split('/\s+/', trim($norm));
            $penting = [];
            foreach ($kata as $w) {
                if (mb_strlen($w) < 3) continue;
                if (in_array($w, $stop, true)) continue;
                $penting[] = $w;
            }
            if (!$penting) continue;
            sort($penting);
            $kunci = implode(' ', $penting);

            // lewati kalau judul serupa sudah ada di KB
            $cekKb = implode(' ', $penting);
            if (isset($kbAda[$cekKb])) continue;

            if (!isset($grup[$kunci])) {
                // v1.2.25: key dipakai untuk menyembunyikan; sample_a untuk penyaringan AI
                $grup[$kunci] = ['key' => $kunci, 'count' => 0, 'question' => $q,
                                 'sample_a' => mb_substr(trim((string)($e['a'] ?? '')), 0, 200),
                                 'last_ts' => '', 'channels' => []];
            }
            $grup[$kunci]['count']++;
            // wakil kelompok: pertanyaan TERPENDEK (paling ringkas)
            if (mb_strlen($q) < mb_strlen($grup[$kunci]['question'])) $grup[$kunci]['question'] = $q;
            $ts = (string)($e['ts'] ?? '');
            if ($ts > $grup[$kunci]['last_ts']) $grup[$kunci]['last_ts'] = $ts;
            $ch = (string)($e['channel'] ?? '');
            if ($ch !== '' && !in_array($ch, $grup[$kunci]['channels'], true)) $grup[$kunci]['channels'][] = $ch;
        }

        // v1.2.25: buang yang sudah disembunyikan (kecuali diminta ditampilkan)
        $sembunyi = readJson(GAPS_DISMISSED_FILE, []);
        if (!is_array($sembunyi)) $sembunyi = [];
        $tampilkanSembunyi = !empty($_GET['show_hidden']);
        $jmlSembunyi = 0;
        if (!$tampilkanSembunyi) {
            foreach ($grup as $k => $v) {
                if (in_array($k, $sembunyi, true)) { unset($grup[$k]); $jmlSembunyi++; }
            }
        }

        $hasil = array_values($grup);
        usort($hasil, function ($a, $b) {
            if ($b['count'] !== $a['count']) return $b['count'] - $a['count'];
            return strcmp($b['last_ts'], $a['last_ts']);
        });
        jsonOut([
            'ok'        => true,
            'scanned'   => $dipindai,
            'found'     => count($hasil),
            'hidden'    => $jmlSembunyi,           // v1.2.25
            'gaps'      => array_slice($hasil, 0, 40),
        ]);
        break;
    }

    case 'kb_verify_gaps': {
        // AI MEMILAH saja — tidak menulis jawaban, tidak menghapus apa pun.
        // Satu panggilan untuk seluruh daftar (bukan per baris).
        requireAuth(['super_admin', 'admin']);
        $s = getSettings();
        if (empty($s['api']['claude_api_key'])) {
            jsonOut(['ok' => false, 'error' => 'API key Claude belum dikonfigurasi.'], 400);
        }
        $in = bodyInput();
        $items = is_array($in['items'] ?? null) ? $in['items'] : [];
        if (!$items) jsonOut(['ok' => false, 'error' => 'Tidak ada yang disaring.'], 400);
        $items = array_slice($items, 0, 40);

        $daftar = '';
        foreach ($items as $i => $it) {
            $q = trim((string)($it['question'] ?? ''));
            $a = trim((string)($it['sample_a'] ?? ''));
            $daftar .= $i . '. TANYA: ' . mb_substr($q, 0, 200) . "\n";
            $daftar .= '   JAWAB BOT: ' . mb_substr($a, 0, 200) . "\n\n";
        }

        $sys = "Anda memeriksa mutu jawaban chatbot customer service.\n"
             . "Untuk tiap nomor, tentukan apakah bot BENAR-BENAR GAGAL menjawab pertanyaannya.\n\n"
             . "GAGAL = bot tidak memberi informasi yang diminta (menyatakan tidak tahu,\n"
             . "belum tersedia, atau hanya melempar ke tim/admin tanpa isi).\n"
             . "TIDAK GAGAL = bot sudah memberi informasi yang diminta, walaupun di akhir\n"
             . "menambahkan ajakan menghubungi tim. Ajakan sopan di akhir BUKAN kegagalan.\n\n"
             . "Kembalikan HANYA JSON: {\"gagal\":[nomor, nomor, ...]}\n"
             . "Berisi nomor yang BENAR-BENAR gagal saja. Tanpa penjelasan apa pun.";

        list($okAi, $answer, $usage) = callClaude($s, $sys, [['role' => 'user', 'content' => $daftar]]);
        if (!$okAi) jsonOut(['ok' => false, 'error' => 'Analisa AI gagal.'], 502);
        recordUsage($usage);   // masuk kuota, sepola dengan analisa lead

        $raw = trim((string)$answer);
        $raw = preg_replace('/^```[a-zA-Z]*\s*/', '', $raw);
        $raw = preg_replace('/```\s*$/', '', $raw);
        $data = json_decode(trim($raw), true);
        if (!is_array($data) || !isset($data['gagal']) || !is_array($data['gagal'])) {
            error_log('kb_verify_gaps: respons bukan JSON: ' . mb_substr($raw, 0, 200));
            jsonOut(['ok' => false, 'error' => 'Jawaban AI tidak terbaca.'], 502);
        }
        $gagal = [];
        foreach ($data['gagal'] as $n) { $gagal[] = (int)$n; }
        jsonOut(['ok' => true, 'failed' => $gagal, 'total' => count($items)]);
        break;
    }

    case 'kb_dismiss_gap': {
        requireAuth(['super_admin', 'admin']);
        $in  = bodyInput();
        $keys = is_array($in['keys'] ?? null) ? $in['keys'] : [];
        if (isset($in['key'])) $keys[] = (string)$in['key'];
        $keys = array_filter(array_map('trim', $keys));
        if (!$keys) jsonOut(['ok' => false, 'error' => 'Tidak ada yang disembunyikan.'], 400);

        $sembunyi = readJson(GAPS_DISMISSED_FILE, []);
        if (!is_array($sembunyi)) $sembunyi = [];
        foreach ($keys as $k) {
            if (!in_array($k, $sembunyi, true)) $sembunyi[] = $k;
        }
        writeJson(GAPS_DISMISSED_FILE, array_values($sembunyi));
        jsonOut(['ok' => true, 'hidden_total' => count($sembunyi)]);
        break;
    }

    case 'kb_restore_gaps': {
        // kosongkan daftar sembunyi — untuk meninjau ulang kalau ada salah klik
        requireAuth(['super_admin', 'admin']);
        writeJson(GAPS_DISMISSED_FILE, []);
        jsonOut(['ok' => true]);
        break;
    }

    case 'kb_add_gap': {
        requireAuth(['super_admin', 'admin']);
        $in = bodyInput();
        $q  = trim((string)($in['question'] ?? ''));
        if ($q === '') jsonOut(['ok' => false, 'error' => 'Pertanyaan kosong.'], 400);
        $kb = readJson(KB_FILE, []);
        // isi sengaja DIKOSONGKAN — jawabannya harus ditulis manusia.
        // Entri tanpa isi tidak dikirim ke bot (lihat perbaikan di generateAnswer).
        array_unshift($kb, [
            'id'       => 'kb_' . substr(md5(uniqid('', true)), 0, 8),
            'category' => 'Perlu Diisi',
            'title'    => mb_substr($q, 0, 300),
            'content'  => '',
            'topic'    => '',
        ]);
        writeJson(KB_FILE, $kb);
        jsonOut(['ok' => true, 'count' => count($kb)]);
        break;
    }

    /* ---------- v1.2.23: analisa & gabung duplikat KB ---------- */
    case 'kb_find_duplicates': {
        requireAuth(['super_admin', 'admin']);
        $kb = readJson(KB_FILE, []);
        $grup = [];
        $tanpaIsi = 0;
        foreach ($kb as $e) {
            $isi = trim((string)($e['content'] ?? ''));
            if ($isi === '') { $tanpaIsi++; continue; }
            $k = md5($isi);
            if (!isset($grup[$k])) $grup[$k] = [];
            $grup[$k][] = $e;
        }
        $kelompok = [];
        $bentrok = [];
        foreach ($grup as $anggota) {
            if (count($anggota) < 2) continue;
            // judul terpendek = biasanya bentuk dasar pertanyaan
            $judul = '';
            foreach ($anggota as $a) {
                $t = (string)($a['title'] ?? '');
                if ($judul === '' || mb_strlen($t) < mb_strlen($judul)) $judul = $t;
            }
            $topik = [];
            foreach ($anggota as $a) {
                $tp = trim((string)($a['topic'] ?? ''));
                if ($tp !== '' && !in_array($tp, $topik, true)) $topik[] = $tp;
            }
            if (count($topik) > 1) $bentrok[] = ['title' => $judul, 'topics' => $topik];
            $kelompok[] = ['count' => count($anggota), 'title' => mb_substr($judul, 0, 80)];
        }
        usort($kelompok, function ($a, $b) { return $b['count'] - $a['count']; });
        $unik = count($grup) + $tanpaIsi;
        jsonOut([
            'ok'        => true,
            'total'     => count($kb),
            'unique'    => $unik,
            'removed'   => max(0, count($kb) - $unik),
            'no_content'=> $tanpaIsi,
            'groups'    => array_slice($kelompok, 0, 15),
            'group_count'=> count($kelompok),
            'conflicts' => $bentrok,
        ]);
        break;
    }

    case 'kb_merge_duplicates': {
        requireAuth(['super_admin', 'admin']);
        $kb = readJson(KB_FILE, []);
        if (!is_array($kb) || !$kb) jsonOut(['ok' => false, 'error' => 'Knowledge Base kosong.'], 400);

        // cadangan dulu — penggabungan menghapus entri, harus bisa dipulihkan
        $bak = KB_FILE . '.bak-dedup-' . date('Ymd-His');
        @copy(KB_FILE, $bak);

        $grup = [];
        $tanpaIsi = [];
        foreach ($kb as $e) {
            $isi = trim((string)($e['content'] ?? ''));
            if ($isi === '') { $tanpaIsi[] = $e; continue; }
            $k = md5($isi);
            if (!isset($grup[$k])) $grup[$k] = [];
            $grup[$k][] = $e;
        }

        $hasil = [];
        foreach ($grup as $anggota) {
            $terpilih = $anggota[0];
            foreach ($anggota as $a) {
                if (mb_strlen((string)($a['title'] ?? '')) < mb_strlen((string)($terpilih['title'] ?? ''))) {
                    $terpilih = $a;
                }
            }
            // pertahankan tag topik dari duplikat mana pun yang punya
            $topik = '';
            foreach ($anggota as $a) {
                $tp = trim((string)($a['topic'] ?? ''));
                if ($tp !== '') { $topik = $tp; break; }
            }
            // kategori: dari terpilih, kalau kosong ambil dari duplikat yang terisi
            $kat = trim((string)($terpilih['category'] ?? ''));
            if ($kat === '') {
                foreach ($anggota as $a) {
                    $c = trim((string)($a['category'] ?? ''));
                    if ($c !== '') { $kat = $c; break; }
                }
            }
            $hasil[] = [
                'id'       => (string)($terpilih['id'] ?? ('kb_' . substr(md5(uniqid('', true)), 0, 8))),
                'category' => $kat,
                'title'    => (string)($terpilih['title'] ?? ''),
                'content'  => trim((string)($terpilih['content'] ?? '')),
                'topic'    => $topik,
            ];
        }
        foreach ($tanpaIsi as $e) $hasil[] = $e;

        if (count($hasil) === 0) {
            jsonOut(['ok' => false, 'error' => 'Hasil kosong — dibatalkan demi keamanan.'], 500);
        }
        writeJson(KB_FILE, $hasil);
        error_log('kb_merge_duplicates: ' . count($kb) . ' -> ' . count($hasil) . ', cadangan: ' . $bak);
        jsonOut(['ok' => true, 'before' => count($kb), 'after' => count($hasil), 'backup' => basename($bak)]);
        break;
    }

    case 'save_kb': {
        requireAuth(['super_admin','admin']);
        $in = bodyInput();
        $kb = is_array($in['kb'] ?? null) ? $in['kb'] : [];
        // sanitize entries
        $clean = [];
        foreach ($kb as $e) {
            $clean[] = [
                'id'       => $e['id'] ?? ('kb_' . substr(md5(uniqid('', true)), 0, 8)),
                'category' => trim((string)($e['category'] ?? '')),
                'title'    => trim((string)($e['title'] ?? '')),
                'content'  => trim((string)($e['content'] ?? '')),
                'topic'    => trim((string)($e['topic'] ?? '')),  // v1.2.12 Fase 3: topic tag untuk routing
            ];
        }
        writeJson(KB_FILE, $clean);
        jsonOut(['ok' => true, 'count' => count($clean)]);
        break;
    }

    /* ---------- logs (admin only) ---------- */
    case 'get_logs': {
        requireAuth(['super_admin','admin']);
        $logs = readJson(LOG_FILE, []);
        $limit = (int)($_GET['limit'] ?? 200);
        if ($limit > 0) $logs = array_slice($logs, 0, $limit);
        jsonOut(['ok' => true, 'logs' => $logs]);
        break;
    }

    /* ---------- report / stats with UTM aggregation (admin only) ---------- */
    case 'report': {
        requireAuth(['super_admin','admin']);
        $logs = readJson(LOG_FILE, []);
        $kb = readJson(KB_FILE, []);
        $today = date('Y-m-d');

        $from = isset($_GET['from']) ? substr((string)$_GET['from'], 0, 10) : '';
        $to   = isset($_GET['to'])   ? substr((string)$_GET['to'], 0, 10)   : '';
        $chFilter = $_GET['channel'] ?? 'all';   // all | web | whatsapp

        $todayCount = 0; $ips = []; $total = 0;
        $bySource = []; $byMedium = []; $bySrcMed = []; $byCampaign = []; $byChannel = [];
        $srcU = []; $medU = []; $smU = []; $cmpU = [];
        $daily = [];

        foreach ($logs as $l) {
            if (($l['dir'] ?? '') === 'manual') continue;          // skip admin manual replies
            $ts = (string)($l['ts'] ?? '');
            $d  = substr($ts, 0, 10);
            if ($from !== '' && $d !== '' && $d < $from) continue;  // date range
            if ($to   !== '' && $d !== '' && $d > $to)   continue;

            $ch = ($l['channel'] ?? '') !== '' ? $l['channel'] : 'web';
            $byChannel[$ch] = ($byChannel[$ch] ?? 0) + 1;           // channel breakdown (pre channel-filter)
            if ($chFilter !== 'all' && $ch !== $chFilter) continue; // channel filter for the rest

            $total++;
            if ($d === $today) $todayCount++;
            $ip = $l['ip'] ?? '';
            if ($ip !== '') $ips[$ip] = true;

            $src = ($l['utm_source'] ?? '') !== '' ? $l['utm_source'] : '(direct)';
            $med = ($l['utm_medium'] ?? '') !== '' ? $l['utm_medium'] : '(none)';
            $cmp = ($l['utm_campaign'] ?? '') !== '' ? $l['utm_campaign'] : '(none)';
            $sm  = $src . ' / ' . $med;

            $bySource[$src]   = ($bySource[$src] ?? 0) + 1;
            $byMedium[$med]   = ($byMedium[$med] ?? 0) + 1;
            $bySrcMed[$sm]    = ($bySrcMed[$sm] ?? 0) + 1;
            $byCampaign[$cmp] = ($byCampaign[$cmp] ?? 0) + 1;
            if ($ip !== '') { $srcU[$src][$ip] = 1; $medU[$med][$ip] = 1; $smU[$sm][$ip] = 1; $cmpU[$cmp][$ip] = 1; }

            if (!isset($daily[$d])) $daily[$d] = ['count' => 0, 'users' => []];
            $daily[$d]['count']++;
            if ($ip !== '') $daily[$d]['users'][$ip] = 1;
        }

        arsort($bySource); arsort($byMedium); arsort($bySrcMed); arsort($byCampaign); arsort($byChannel);

        $fmt = function ($assoc, $users = null) {
            $out = [];
            foreach ($assoc as $k => $v) {
                $row = ['label' => $k, 'count' => $v];
                if ($users !== null) $row['users'] = isset($users[$k]) ? count($users[$k]) : 0;
                $out[] = $row;
            }
            return $out;
        };

        ksort($daily);
        $trend = [];
        foreach ($daily as $d => $o) $trend[] = ['date' => $d, 'count' => $o['count'], 'users' => count($o['users'])];

        jsonOut([
            'ok' => true,
            'range' => ['from' => $from, 'to' => $to, 'channel' => $chFilter],
            'stats' => [
                'total'      => $total,
                'today'      => $todayCount,
                'kb_entries' => count($kb),
                'unique_ips' => count($ips),
            ],
            'by_channel'       => $fmt($byChannel),
            'by_source'        => $fmt($bySource, $srcU),
            'by_medium'        => $fmt($byMedium, $medU),
            'by_source_medium' => $fmt($bySrcMed, $smU),
            'by_campaign'      => $fmt($byCampaign, $cmpU),
            'trend'            => $trend,
        ]);
        break;
    }

    /* ---------- export logs to CSV with date range (admin only) ---------- */
    case 'export_logs': {
        requireAuth(['super_admin','admin']);
        $from = isset($_GET['from']) ? substr($_GET['from'], 0, 10) : '';
        $to   = isset($_GET['to'])   ? substr($_GET['to'], 0, 10)   : '';
        $logs = readJson(LOG_FILE, []);

        $rows = [];
        foreach ($logs as $l) {
            $d = substr((string)($l['ts'] ?? ''), 0, 10);
            if ($from && $d < $from) continue;
            if ($to && $d > $to) continue;
            $rows[] = $l;
        }

        $fname = 'chatbot-log';
        if ($from || $to) $fname .= '_' . ($from ?: 'awal') . '_to_' . ($to ?: 'akhir');
        $fname .= '.csv';

        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: attachment; filename="' . $fname . '"');
        $out = fopen('php://output', 'w');
        // UTF-8 BOM so Excel reads Indonesian characters correctly
        fwrite($out, "\xEF\xBB\xBF");
        fputcsv($out, ['Waktu', 'Channel', 'Pertanyaan', 'Jawaban AI', 'Pengirim/IP', 'UTM Source', 'UTM Medium', 'UTM Campaign', 'Halaman', 'Referrer']);
        foreach ($rows as $l) {
            fputcsv($out, [
                $l['ts'] ?? '',
                $l['channel'] ?? 'web',
                $l['q'] ?? '',
                $l['a'] ?? '',
                $l['ip'] ?? '',
                $l['utm_source'] ?? '',
                $l['utm_medium'] ?? '',
                $l['utm_campaign'] ?? '',
                $l['page'] ?? '',
                $l['referrer'] ?? '',
            ]);
        }
        fclose($out);
        exit;
    }

    /* ---------- user management (admin only) ---------- */
    /* ============================================================
     * v1.2.8: push subscription endpoints (Web Push + PWA)
     * ============================================================ */
    case 'get_push_config': {
        // Semua user authenticated boleh ambil VAPID public key
        requireAuth(['super_admin', 'admin', 'wa_agent']);
        $vapidFile = DATA_DIR . '/vapid-keys.json';
        if (!file_exists($vapidFile)) {
            jsonOut(['ok' => false, 'error' => 'VAPID keys belum di-setup.'], 500);
        }
        $vapid = json_decode(file_get_contents($vapidFile), true);
        jsonOut(['ok' => true, 'publicKey' => $vapid['publicKey'] ?? '']);
        break;
    }

    case 'save_push_subscription': {
        $me = requireAuth(['super_admin', 'admin', 'wa_agent']);
        $in = bodyInput();
        $sub = $in['subscription'] ?? null;
        if (!$sub || empty($sub['endpoint'])) {
            jsonOut(['ok' => false, 'error' => 'Subscription tidak valid.'], 400);
        }
        $ua = substr((string)($in['ua'] ?? ''), 0, 120);
        $subsFile = DATA_DIR . '/push-subs.json';
        $all = file_exists($subsFile) ? (json_decode(file_get_contents($subsFile), true) ?: []) : [];
        $username = $me['username'];
        if (!isset($all[$username]) || !is_array($all[$username])) $all[$username] = [];
        // Dedup: hapus subscription lama dengan endpoint sama
        $all[$username] = array_values(array_filter($all[$username], function ($s) use ($sub) {
            return ($s['endpoint'] ?? '') !== $sub['endpoint'];
        }));
        $all[$username][] = [
            'endpoint' => $sub['endpoint'],
            'keys'     => $sub['keys'] ?? [],
            'added'    => date('Y-m-d H:i:s'),
            'ua'       => $ua,
        ];
        writeJson($subsFile, $all);
        jsonOut(['ok' => true]);
        break;
    }

    case 'delete_push_subscription': {
        $me = requireAuth(['super_admin', 'admin', 'wa_agent']);
        $in = bodyInput();
        $endpoint = (string)($in['endpoint'] ?? '');
        $subsFile = DATA_DIR . '/push-subs.json';
        $all = file_exists($subsFile) ? (json_decode(file_get_contents($subsFile), true) ?: []) : [];
        $username = $me['username'];
        if (isset($all[$username]) && is_array($all[$username])) {
            if ($endpoint !== '') {
                $all[$username] = array_values(array_filter($all[$username], function ($s) use ($endpoint) {
                    return ($s['endpoint'] ?? '') !== $endpoint;
                }));
            } else {
                $all[$username] = [];  // hapus semua kalau endpoint kosong
            }
            writeJson($subsFile, $all);
        }
        jsonOut(['ok' => true]);
        break;
    }
    // === /v1.2.8 push subscription ===

    case 'get_users': {
        // v1.2.14: admin ikut boleh (kelola wa_agent). Data aman: tanpa password/hash.
        // Pembatasan tetap di save_user/delete_user (admin cuma boleh target wa_agent).
        requireAuth(['super_admin', 'admin']);
        $users = readJson(USERS_FILE, []);
        $safe = array_map(function ($u) {
            return [
                'username'   => $u['username'] ?? '',
                'name'       => $u['name'] ?? '',
                'role'       => $u['role'] ?? 'editor',
                'categories' => $u['categories'] ?? [],  // v1.2.12 Fase 2: categories
            ];
        }, $users);
        jsonOut(['ok' => true, 'users' => $safe]);
        break;
    }

    case 'save_user': {
        $me = requireAuth(['super_admin', 'admin']);
        $in = bodyInput();
        $username = trim($in['username'] ?? '');
        $name     = trim($in['name'] ?? $username);
        $roleIn   = (string)($in['role'] ?? 'admin');
        $role     = in_array($roleIn, ['super_admin', 'admin', 'wa_agent'], true) ? $roleIn : 'admin';
        $password = (string)($in['password'] ?? '');
        // v1.2.12 Fase 2: categories (multi-select untuk routing push by topic)
        $categories = [];
        if (isset($in['categories']) && is_array($in['categories'])) {
            foreach ($in['categories'] as $c) {
                $c = trim((string)$c);
                if ($c !== '') $categories[] = $c;
            }
            $categories = array_values(array_unique($categories));
        }
        if ($username === '') jsonOut(['ok' => false, 'error' => 'Username wajib diisi.'], 400);

        // === v1.2.6: admin restriction — cuma boleh manage wa_agent ===
        if ($me['role'] === 'admin') {
            if ($role !== 'wa_agent') {
                jsonOut(['ok' => false, 'error' => 'Admin hanya dapat mengelola user dengan peran WA Agent.'], 403);
            }
            $chkUsers = readJson(USERS_FILE, []);
            foreach ($chkUsers as $chkU) {
                if (($chkU['username'] ?? '') === $username && ($chkU['role'] ?? '') !== 'wa_agent') {
                    jsonOut(['ok' => false, 'error' => 'Admin tidak dapat mengubah user dengan peran lebih tinggi.'], 403);
                }
            }
        }
        // === /v1.2.6 ===
        // Enforce password strength only when a new password is being set.
        if ($password !== '') {
            $weak = checkPasswordStrength($password);
            if ($weak) jsonOut(['ok' => false, 'error' => $weak], 400);
        }

        $users = readJson(USERS_FILE, []);
        $found = false;
        foreach ($users as $i => $u) {
            if (($u['username'] ?? '') === $username) {
                $users[$i]['name'] = $name;
                $users[$i]['role'] = $role;
                $users[$i]['categories'] = $categories;  // v1.2.12 Fase 2
                if ($password !== '') $users[$i]['password'] = password_hash($password, PASSWORD_DEFAULT);
                $found = true;
                break;
            }
        }
        if (!$found) {
            if ($password === '') jsonOut(['ok' => false, 'error' => 'Password wajib diisi untuk user baru.'], 400);
            $users[] = [
                'username' => $username,
                'password' => password_hash($password, PASSWORD_DEFAULT),
                'role'     => $role,
                'name'     => $name,
                'categories' => $categories,
                'migrated_3role' => true,
            ];
        }
        writeJson(USERS_FILE, $users);
        jsonOut(['ok' => true]);
        break;
    }

    case 'delete_user': {
        $me = requireAuth(['super_admin', 'admin']);
        $in = bodyInput();
        $username = trim($in['username'] ?? '');
        if ($username === $me['username']) jsonOut(['ok' => false, 'error' => 'Tidak dapat menghapus akun Anda sendiri.'], 400);
        // === v1.2.6: admin restriction — cuma boleh delete wa_agent ===
        if ($me['role'] === 'admin') {
            $delUsers = readJson(USERS_FILE, []);
            $delTargetRole = '';
            foreach ($delUsers as $du) {
                if (($du['username'] ?? '') === $username) { $delTargetRole = $du['role'] ?? ''; break; }
            }
            if ($delTargetRole !== 'wa_agent') {
                jsonOut(['ok' => false, 'error' => 'Admin hanya dapat menghapus user dengan peran WA Agent.'], 403);
            }
        }
        // === /v1.2.6 ===
        $users = readJson(USERS_FILE, []);
        $remaining = array_values(array_filter($users, function ($u) use ($username) {
            return ($u['username'] ?? '') !== $username;
        }));
        $admins = array_filter($remaining, function ($u) { return ($u['role'] ?? '') === 'super_admin'; });
        if (count($admins) === 0) jsonOut(['ok' => false, 'error' => 'Minimal harus ada satu Super Admin.'], 400);
        writeJson(USERS_FILE, $remaining);
        jsonOut(['ok' => true]);
        break;
    }

    case 'update_own_password': {
        // v1.2.2: user self-service password change (semua role)
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        $in = bodyInput();
        $currentPw = (string)($in['current_password'] ?? '');
        $newPw     = (string)($in['new_password']     ?? '');

        if ($currentPw === '' || $newPw === '') {
            jsonOut(['ok' => false, 'error' => 'Password lama & baru wajib diisi.'], 400);
        }
        if ($currentPw === $newPw) {
            jsonOut(['ok' => false, 'error' => 'Password baru tidak boleh sama dengan yang lama.'], 400);
        }

        $weak = checkPasswordStrength($newPw);
        if ($weak) jsonOut(['ok' => false, 'error' => $weak], 400);

        $users = readJson(USERS_FILE, []);
        $found = false;
        foreach ($users as $i => $usr) {
            if (($usr['username'] ?? '') === $u['username']) {
                if (!password_verify($currentPw, $usr['password'] ?? '')) {
                    jsonOut(['ok' => false, 'error' => 'Password lama salah.'], 400);
                }
                // Update password ONLY — jangan touch role/name/username (prevent privilege escalation)
                $users[$i]['password'] = password_hash($newPw, PASSWORD_DEFAULT);
                $found = true;
                break;
            }
        }
        if (!$found) jsonOut(['ok' => false, 'error' => 'User tidak ditemukan.'], 404);

        writeJson(USERS_FILE, $users);
        jsonOut(['ok' => true, 'message' => 'Password berhasil diganti. Silakan login ulang.']);
        break;
    }

    /* ============================================================
     * Central Server — auto-update (super_admin only)
     * ============================================================ */

    case 'usage_summary': {
        requireAuth(['super_admin', 'admin']);
        $all = readJson(DATA_DIR . '/usage.json', []);
        ksort($all);
        // last 30 days
        $cut = date('Y-m-d', strtotime('-29 days'));
        $rows = [];
        $sum = ['calls' => 0, 'input' => 0, 'output' => 0, 'cache_write' => 0, 'cache_read' => 0];
        foreach ($all as $day => $d) {
            if ($day < $cut) continue;
            $rows[] = ['date' => $day] + $d;
            foreach (['calls','input','output','cache_write','cache_read'] as $k) $sum[$k] += $d[$k] ?? 0;
        }
        $cost30 = round(
            ($sum['input']/1e6 * 1.00) +
            ($sum['output']/1e6 * 5.00) +
            ($sum['cache_write']/1e6 * 1.25) +
            ($sum['cache_read']/1e6 * 0.10),
        4);
        // Estimated cost WITHOUT caching (counter-factual: all cache_read + cache_write would be normal input)
        $cost30_no_cache = round(
            (($sum['input'] + $sum['cache_write'] + $sum['cache_read'])/1e6 * 1.00) +
            ($sum['output']/1e6 * 5.00),
        4);
        $saved = round($cost30_no_cache - $cost30, 4);
        $saved_pct = $cost30_no_cache > 0 ? round($saved / $cost30_no_cache * 100, 1) : 0;
        jsonOut([
            'ok' => true,
            'daily' => $rows,
            'summary_30d' => [
                'calls'           => $sum['calls'],
                'tokens_input'    => $sum['input'],
                'tokens_output'   => $sum['output'],
                'cache_write'     => $sum['cache_write'],
                'cache_read'      => $sum['cache_read'],
                'cost_usd'        => $cost30,
                'cost_no_cache'   => $cost30_no_cache,
                'saved_by_cache'  => $saved,
                'saved_pct'       => $saved_pct,
            ],
        ]);
        break;
    }

    case 'upload_avatar': {
        // v1.1.6: server-side avatar validate + save.
        // Client already resized to 96×96 PNG via Canvas, but we re-validate
        // (1) MIME type from magic bytes (2) max raw size 1 MB after client resize
        // (3) re-encode with GD as 96×96 PNG to strip any payload (4) save to data/uploads/
        requireAuth(['super_admin', 'admin']);
        if (empty($_FILES['avatar']['tmp_name'])) {
            jsonOut(['ok' => false, 'error' => 'Tidak ada file diupload.'], 400);
        }
        $tmp = $_FILES['avatar']['tmp_name'];
        $size = (int)$_FILES['avatar']['size'];
        if ($size <= 0 || $size > 1024 * 1024) {  // 1 MB cap after client resize (much smaller than 2 MB raw)
            jsonOut(['ok' => false, 'error' => 'Ukuran file tidak valid (maks 1 MB setelah resize).'], 400);
        }

        // Detect MIME from magic bytes
        $finfo = function_exists('finfo_open') ? finfo_open(FILEINFO_MIME_TYPE) : null;
        $mime = $finfo ? finfo_file($finfo, $tmp) : mime_content_type($tmp);
        if ($finfo) finfo_close($finfo);
        if (!in_array($mime, ['image/png', 'image/jpeg', 'image/webp'], true)) {
            jsonOut(['ok' => false, 'error' => 'Format harus PNG, JPG, atau WEBP. Terdeteksi: ' . $mime], 400);
        }

        if (!function_exists('imagecreatetruecolor')) {
            jsonOut(['ok' => false, 'error' => 'GD library tidak tersedia di server.'], 500);
        }

        // Load source image
        $src = null;
        switch ($mime) {
            case 'image/png':  $src = @imagecreatefrompng($tmp); break;
            case 'image/jpeg': $src = @imagecreatefromjpeg($tmp); break;
            case 'image/webp': $src = function_exists('imagecreatefromwebp') ? @imagecreatefromwebp($tmp) : null; break;
        }
        if (!$src) jsonOut(['ok' => false, 'error' => 'Gagal membaca gambar.'], 400);

        $sw = imagesx($src); $sh = imagesy($src);
        if ($sw <= 0 || $sh <= 0 || $sw > 4096 || $sh > 4096) {
            imagedestroy($src);
            jsonOut(['ok' => false, 'error' => 'Dimensi gambar tidak valid.'], 400);
        }

        // Resize/crop to 96×96 (center crop)
        $cropSize = min($sw, $sh);
        $cropX = (int)(($sw - $cropSize) / 2);
        $cropY = (int)(($sh - $cropSize) / 2);
        $dst = imagecreatetruecolor(96, 96);
        imagesavealpha($dst, true);
        $transparent = imagecolorallocatealpha($dst, 0, 0, 0, 127);
        imagefill($dst, 0, 0, $transparent);
        imagecopyresampled($dst, $src, 0, 0, $cropX, $cropY, 96, 96, $cropSize, $cropSize);
        imagedestroy($src);

        // Ensure uploads dir exists
        $uploadsDir = DATA_DIR . '/uploads';
        if (!is_dir($uploadsDir)) @mkdir($uploadsDir, 0755, true);
        if (!is_dir($uploadsDir) || !is_writable($uploadsDir)) {
            imagedestroy($dst);
            jsonOut(['ok' => false, 'error' => 'Folder uploads tidak bisa ditulis (' . $uploadsDir . ').'], 500);
        }

        // Filename: avatar-<timestamp>.png (collision-safe + cache-busting)
        $fname = 'avatar-' . time() . '.png';
        $fpath = $uploadsDir . '/' . $fname;
        $ok = imagepng($dst, $fpath, 6);
        imagedestroy($dst);
        if (!$ok || !file_exists($fpath)) {
            jsonOut(['ok' => false, 'error' => 'Gagal menulis file.'], 500);
        }
        @chmod($fpath, 0644);

        // Delete previous avatar files (keep only latest)
        foreach (glob($uploadsDir . '/avatar-*.png') as $old) {
            if ($old !== $fpath) @unlink($old);
        }

        // Public URL (relative from dashboard's parent dir)
        $url = 'data/uploads/' . $fname;
        jsonOut(['ok' => true, 'url' => $url, 'size' => filesize($fpath)]);
        break;
    }

    case 'license_status': {
        requireAuth(['super_admin', 'admin']);
        $s = getSettings();
        $lic = getLicenseStatus($s);
        jsonOut(['ok' => true, 'license' => $lic]);
        break;
    }

    case 'cap_status': {
        // Available to all roles (super_admin, admin, wa_agent) for banner
        requireAuth(['super_admin', 'admin', 'wa_agent']);
        $s = getSettings();
        $cap = getCapStatus($s);
        jsonOut(['ok' => true, 'cap' => $cap]);
        break;
    }

    case 'usage_dashboard': {
        // v1.1.5: combined endpoint for the Usage card in Reports tab
        // Returns: tier/status/cap + this-month stats + 30-day daily breakdown
        requireAuth(['super_admin', 'admin', 'wa_agent']);
        $s = getSettings();
        $cap = getCapStatus($s);
        $lic = getLicenseStatus($s);

        // 30-day daily breakdown from usage.json
        $usage = readJson(DATA_DIR . '/usage.json', []);
        ksort($usage);
        $daily = [];
        $cutoff = wibDate('Y-m-d', time() - 29 * 86400);
        foreach ($usage as $day => $d) {
            if ($day < $cutoff) continue;
            $daily[] = ['date' => $day, 'calls' => (int)($d['calls'] ?? 0)];
        }

        // Days remaining until next reset (1st of next month, WIB)
        $todayW = wibToday();
        list($curY, $curM) = explode('-', $todayW);
        $nextResetTs = mktime(0, 0, 0, (int)$curM + 1, 1, (int)$curY) - 7 * 3600;   // 1st of next month 00:00 WIB
        $daysLeftMonth = (int)ceil(($nextResetTs - time()) / 86400);

        // Month stats (same calc as in computeMonthStats but expose more fields)
        $monthKey = wibDate('Y-m');
        $mIn = 0; $mOut = 0; $mCW = 0; $mCR = 0; $mCalls = 0;
        foreach ($usage as $day => $d) {
            if (strpos($day, $monthKey) !== 0) continue;
            $mCalls += (int)($d['calls'] ?? 0);
            $mIn    += (int)($d['input'] ?? 0);
            $mOut   += (int)($d['output'] ?? 0);
            $mCW    += (int)($d['cache_write'] ?? 0);
            $mCR    += (int)($d['cache_read'] ?? 0);
        }
        $costUsd = round(($mIn/1e6 * 1.0) + ($mOut/1e6 * 5.0) + ($mCW/1e6 * 1.25) + ($mCR/1e6 * 0.10), 5);

        jsonOut([
            'ok' => true,
            'tier'           => $cap['tier'] ?? 'starter',
            'license_status' => $lic['status'] ?? 'active',
            'expires_at'     => $lic['expires_at'] ?? '',
            'chats_used'     => $cap['used'] ?? $mCalls,
            'chat_cap'       => $cap['cap'] ?? 0,
            'usage_pct'      => $cap['pct'] ?? 0,
            'cap_reached'    => !empty($cap['reached']),
            'cap_warning'    => !empty($cap['warning']),
            'days_left_month'=> $daysLeftMonth,
            'cost_this_month_usd' => $costUsd,
            'daily_30d'      => $daily,
            'month_key'      => $monthKey,
            'today_wib'      => $todayW,
        ]);
        break;
    }

    case 'update_status': {
        requireAuth(['super_admin']);
        $s = getSettings();
        $cs = $s['central_server'] ?? [];
        $vp = DATA_DIR . '/version.json';
        $ver = file_exists($vp) ? readJson($vp, []) : [];
        jsonOut([
            'ok' => true,
            'central' => [
                'url'         => $cs['url'] ?? '',
                'tenant_id'   => $cs['tenant_id'] ?? '',
                'license_set' => !empty($cs['license_key']),
                'license_key' => !empty($cs['license_key']) ? maskKey($cs['license_key']) : '',
                'auto_update' => !empty($cs['auto_update']),
                'last_check'  => $cs['last_check'] ?? '',
                'last_result' => $cs['last_result'] ?? '',
            ],
            'installed_version' => $ver['version'] ?? 'v1.1.0',
            'installed_at'      => $ver['installed_at'] ?? '',
        ]);
        break;
    }

    case 'save_central': {
        requireAuth(['super_admin']);
        $in = bodyInput();
        $url   = trim($in['url']         ?? '');
        $tid   = strtolower(trim($in['tenant_id'] ?? ''));   // v1.1.2: always lowercase
        $lic   = trim($in['license_key'] ?? '');
        $auto  = !empty($in['auto_update']);

        $s = getSettings();
        $cur = $s['central_server'] ?? [];

        // Preserve license_key when masked/empty sent in
        if ($lic === '' || strpos($lic, '•') !== false) $lic = $cur['license_key'] ?? '';

        $s['central_server'] = [
            'url'         => rtrim($url, '/'),
            'tenant_id'   => $tid,
            'license_key' => $lic,
            'auto_update' => $auto,
            'last_check'  => $cur['last_check'] ?? '',
            'last_result' => $cur['last_result'] ?? '',
        ];
        writeJson(SETTINGS_FILE, $s);
        jsonOut(['ok' => true]);
        break;
    }

    case 'update_check': {
        requireAuth(['super_admin']);
        $s = getSettings();
        $cs = $s['central_server'] ?? [];
        if (empty($cs['url']) || empty($cs['tenant_id']) || empty($cs['license_key'])) {
            jsonOut(['ok' => false, 'error' => 'Server pusat belum dikonfigurasi.'], 400);
        }
        $vp = DATA_DIR . '/version.json';
        $ver = file_exists($vp) ? readJson($vp, []) : [];
        $current = $ver['version'] ?? 'v1.1.0';

        // Gather aggregate stats for report-back
        $logs = readJson(LOG_FILE, []);
        $kb = readJson(KB_FILE, []);
        $today = wibToday();    // v1.1.4: use WIB date for "today"
        $chats_today = 0; $chats_total = 0; $wa_chats_today = 0; $visitors_today = [];
        foreach ($logs as $l) {
            if (($l['dir'] ?? '') === 'manual') continue;
            $chats_total++;
            if (strpos((string)($l['ts'] ?? ''), $today) === 0) {
                $chats_today++;
                if (($l['channel'] ?? '') === 'whatsapp') $wa_chats_today++;
                if (!empty($l['ip'])) $visitors_today[$l['ip']] = 1;
            }
        }

        // Load today's token usage for cost transparency
        $usage = readJson(DATA_DIR . '/usage.json', []);
        $u = $usage[$today] ?? ['calls' => 0, 'input' => 0, 'output' => 0, 'cache_write' => 0, 'cache_read' => 0];
        // Estimated USD cost for Haiku 4.5: input $1/M, output $5/M, cache write 1.25x, cache read 0.10x
        $cost_today = round(
            ($u['input']/1e6 * 1.00) +
            ($u['output']/1e6 * 5.00) +
            ($u['cache_write']/1e6 * 1.25) +
            ($u['cache_read']/1e6 * 0.10),
        5);

        // v1.1.4: monthly stats (WIB) for cap enforcement
        $monthStats = computeMonthStats();

        $body = [
            'tenant_id'   => $cs['tenant_id'],
            'license_key' => $cs['license_key'],
            'current'     => $current,
            'version'     => $current,
            // v1.2.43: versi dari konstanta di berkas ini (tidak bisa
            // berbohong), berdampingan dengan 'current' dari version.json.
            // Pusat membandingkan keduanya: kalau beda -> update gagal senyap.
            'code_version' => defined('DEI_VERSION') ? DEI_VERSION : '',
            'stats' => [
                'chats_today'           => $chats_today,
                'chats_total'           => $chats_total,
                'wa_chats_today'        => $wa_chats_today,
                'kb_entries'            => count($kb),
                'unique_visitors_today' => count($visitors_today),
                'tokens_in_today'       => $u['input'],
                'tokens_out_today'      => $u['output'],
                'cache_write_today'     => $u['cache_write'],
                'cache_read_today'      => $u['cache_read'],
                'cost_today_usd'        => $cost_today,
                // v1.1.4: monthly (WIB calendar)
                'chats_this_month'      => $monthStats['chats_this_month'],
                'cost_this_month_usd'   => $monthStats['cost_this_month_usd'],
            ],
            'health' => [
                'claude_key_set' => !empty($s['api']['claude_api_key'] ?? ''),
                'wa_enabled'     => !empty($s['whatsapp_api']['enabled'] ?? false),
                'wa_responding'  => !empty($s['whatsapp_api']['access_token'] ?? '') && !empty($s['whatsapp_api']['phone_number_id'] ?? ''),
            ],
        ];

        // Two parallel calls collapsed into two sequential ones (simpler) — report_back first, then check_update.
        $headers = ['Content-Type: application/json'];
        $reportUrl = $cs['url'] . '/backend/index.php?action=report_back';
        $checkUrl  = $cs['url'] . '/backend/index.php?action=check_update';

        $payload = json_encode($body);

        // report_back
        $ch = curl_init($reportUrl);
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 15,
            CURLOPT_POST => true, CURLOPT_POSTFIELDS => $payload, CURLOPT_HTTPHEADER => $headers]);
        @curl_exec($ch);
        curl_close($ch);

        // check_update
        $ch = curl_init($checkUrl);
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 15,
            CURLOPT_POST => true, CURLOPT_POSTFIELDS => $payload, CURLOPT_HTTPHEADER => $headers]);
        $resp = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $err  = curl_error($ch);
        curl_close($ch);

        $now = wibDate('Y-m-d H:i:s');   // v1.2.42: WIB, bukan UTC
        if ($resp === false || $code !== 200) {
            $s['central_server']['last_check']  = $now;
            $s['central_server']['last_result'] = "Gagal terhubung ($code) " . ($err ?: '');
            writeJson(SETTINGS_FILE, $s);
            jsonOut(['ok' => false, 'error' => 'Gagal hubungi pusat: HTTP ' . $code . ' ' . $err], 502);
        }
        $data = json_decode($resp, true) ?: [];
        $s['central_server']['last_check']  = $now;
        $s['central_server']['last_result'] = !empty($data['ok']) ? 'OK' : ('Gagal: ' . ($data['error'] ?? 'unknown'));
        writeJson(SETTINGS_FILE, $s);

        if (!($data['ok'] ?? false)) {
            jsonOut(['ok' => false, 'error' => $data['error'] ?? 'Respon pusat tidak ok'], 400);
        }

        // v1.1.3: refresh license cache from central response (no need for separate refresh call)
        $newStatus = $data['license_status'] ?? 'active';
        $msg = trim($data['suspend_message'] ?? '');
        if ($msg === '') $msg = LIC_DEFAULT_SUSPEND_MSG;
        $cacheBefore = readJson(LIC_CACHE_FILE, []);
        $oldStatus = $cacheBefore['status'] ?? null;
        $newCache = [
            'status'     => $newStatus,
            'message'    => $msg,
            'expires_at' => $data['expires_at'] ?? '',
            'days_left'  => $data['days_left']  ?? null,
            'cached_at'  => time(),
        ];
        writeJson(LIC_CACHE_FILE, $newCache);
        if ($oldStatus !== 'suspended' && $newStatus === 'suspended') {
            applyStatusSideEffects('suspended', $s);
        }

        // v1.1.4: also cache cap_info if present in response
        if (!empty($data['cap_info'])) {
            $cap = $data['cap_info'];
            $capMsg = trim($cap['cap_message'] ?? '');
            if ($capMsg === '') $capMsg = CAP_DEFAULT_MSG;
            $capCache = [
                'reached'   => !empty($cap['cap_reached']),
                'warning'   => !empty($cap['cap_warning']),
                'pct'       => (float)($cap['usage_pct'] ?? 0),
                'tier'      => $cap['tier'] ?? '',
                'cap'       => (int)($cap['monthly_chat_cap'] ?? 0),
                'used'      => (int)($cap['chats_this_month'] ?? 0),
                'message'   => $capMsg,
                'cached_at' => time(),
            ];
            writeJson(CAP_CACHE_FILE, $capCache);
        }

        jsonOut([
            'ok'               => true,
            'current'          => $current,
            'latest'           => $data['latest'] ?? null,
            'update_available' => !empty($data['update_available']),
            'zip_url'          => $data['zip_url']     ?? '',
            'manifest_url'     => $data['manifest_url']?? '',
            'changelog'        => $data['changelog']   ?? '',
            'released_at'      => $data['released_at'] ?? '',
            'license_status'   => $newStatus,
            'expires_at'       => $data['expires_at']  ?? '',
            'days_left'        => $data['days_left']   ?? null,
        ]);
        break;
    }

    case 'update_apply': {
        requireAuth(['super_admin']);
        $in = bodyInput();
        $zipUrl      = (string)($in['zip_url']      ?? '');
        $manifestUrl = (string)($in['manifest_url'] ?? '');
        $target      = (string)($in['target']       ?? '');     // expected version, mis. "v1.1.1"
        if ($zipUrl === '' || $target === '') jsonOut(['ok' => false, 'error' => 'zip_url & target wajib'], 400);

        // === v1.2.1 fix: Downgrade prevention =====================
        $s = getSettings();
        $currentVer = $s['central_server']['target_last_ver'] ?? '';
        if ($target !== '' && $currentVer !== '' &&
            version_compare(ltrim($target,'v'), ltrim($currentVer,'v'), '<')) {
            jsonOut([
                'ok' => false,
                'error' => 'Downgrade dicegah: target ' . $target . ' lebih rendah dari current ' . $currentVer . '. Manual intervention diperlukan.',
                'current' => $currentVer,
                'target' => $target,
            ], 400);
        }
        // === /v1.2.1 fix ==========================================


        $s = getSettings();
        $csUrl = $s['central_server']['url'] ?? '';
        // Safety: zip_url must be on the configured central server URL
        if ($csUrl === '' || strpos($zipUrl, rtrim($csUrl, '/')) !== 0) {
            jsonOut(['ok' => false, 'error' => 'zip_url tidak cocok dengan server pusat.'], 400);
        }

        // Download manifest (optional but recommended for md5 verification)
        $manifest = null;
        if ($manifestUrl !== '') {
            $ch = curl_init($manifestUrl);
            curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 20]);
            $mResp = curl_exec($ch); curl_close($ch);
            if ($mResp) $manifest = json_decode($mResp, true);
        }

        // Download ZIP to temp
        $tmpZip = sys_get_temp_dir() . '/dei-update-' . bin2hex(random_bytes(6)) . '.zip';
        $fh = @fopen($tmpZip, 'w');
        if (!$fh) jsonOut(['ok' => false, 'error' => 'Tidak bisa membuat file sementara.'], 500);
        $ch = curl_init($zipUrl);
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => false, CURLOPT_TIMEOUT => 60,
            CURLOPT_FILE => $fh, CURLOPT_FOLLOWLOCATION => true]);
        $ok = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch); fclose($fh);
        if (!$ok || $code !== 200 || filesize($tmpZip) < 100) {
            @unlink($tmpZip);
            jsonOut(['ok' => false, 'error' => "Gagal unduh ZIP (HTTP $code, size " . filesize($tmpZip) . ")."], 502);
        }

        // Extract to temp dir
        $tmpDir = sys_get_temp_dir() . '/dei-update-' . bin2hex(random_bytes(6));
        @mkdir($tmpDir, 0755, true);
        $extracted = false;
        if (class_exists('ZipArchive')) {
            $zip = new ZipArchive();
            if ($zip->open($tmpZip) === true) {
                $zip->extractTo($tmpDir);
                $zip->close();
                $extracted = true;
            }
        }
        if (!$extracted && function_exists('exec')) {
            $cmd = 'unzip -o ' . escapeshellarg($tmpZip) . ' -d ' . escapeshellarg($tmpDir) . ' 2>&1';
            @exec($cmd, $exo, $rc);
            $extracted = ($rc === 0) && is_dir($tmpDir) && count(scandir($tmpDir)) > 2;
        }
        if (!$extracted) {
            @unlink($tmpZip);
            jsonOut(['ok' => false, 'error' => 'Tidak bisa ekstrak ZIP (ZipArchive & unzip tidak tersedia).'], 500);
        }
        @unlink($tmpZip);

        // Find the payload root: prefer 'dei-update/' folder, else use tmpDir directly.
        // v1.2.41 BUG 1: dulu hanya mengenali akar ZIP atau folder
        // 'dei-update/'. Master ZIP sekarang membungkus di 'dei-chatbot-ai/',
        // jadi $root salah dan SEMUA berkas gagal ditemukan -> update no-op
        // senyap sejak v1.2.1. Sekarang root dicari otomatis berdasarkan
        // keberadaan api/index.php, jadi tahan kalau kemasan ZIP berubah lagi.
        $root = deiCariRootPayload($tmpDir);
        if ($root === null) {
            $isi = @scandir($tmpDir);
            $isi = is_array($isi) ? array_values(array_diff($isi, ['.', '..'])) : [];
            $rmrfEarly = function ($p) use (&$rmrfEarly) {
                if (is_dir($p)) {
                    foreach (scandir($p) as $c) {
                        if ($c === '.' || $c === '..') continue;
                        $rmrfEarly($p . '/' . $c);
                    }
                    @rmdir($p);
                } else { @unlink($p); }
            };
            $rmrfEarly($tmpDir);
            jsonOut([
                'ok'    => false,
                'error' => 'Struktur ZIP update tidak dikenali: api/index.php tidak ditemukan. Isi ZIP: ' . implode(', ', array_slice($isi, 0, 10)),
            ], 500);
        }

        // Whitelist of paths we will replace. NEVER touch data/.
        $allowed = [
            'api/index.php',
            'dashboard/chatbot-ai/app.js',
            'dashboard/chatbot-ai/index.html',
            'dashboard/chatbot-ai/login.html',
            'assets/js/chat-widget.js',
        ];

        // Verify md5 against manifest where possible
        $verified = [];
        // === v1.2.2 fix: track whether manifest has per-file MD5 (for skip guard below) ===
        $hasFilesManifest = is_array($manifest) && !empty($manifest['files']);
        // === /v1.2.2 fix ===
        if ($hasFilesManifest) {
            foreach ($manifest['files'] as $f) {
                $p = $f['path'] ?? ''; $md5 = $f['md5'] ?? '';
                if (!in_array($p, $allowed, true)) continue;
                $local = $root . '/' . $p;
                if (file_exists($local) && $md5 && md5_file($local) === $md5) $verified[$p] = true;
            }
            // If we have a manifest, require every file we plan to replace to be verified.
        }

        // Backup before replace
        $backupDir = dirname(__DIR__) . '/backup-pre-update/' . wibDate('Ymd-His') . '-to-' . preg_replace('/[^a-z0-9.]/i', '', $target);
        @mkdir($backupDir, 0755, true);
        $replaced = []; $skipped = [];
        foreach ($allowed as $rel) {
            $src = $root . '/' . $rel;
            if (!file_exists($src)) { $skipped[] = $rel; continue; }
            // === v1.2.2 fix: only require MD5 verification if manifest has 'files' array ===
            // Backward compat: manifests without 'files' array → skip MD5 check → replace all
            if ($hasFilesManifest && !isset($verified[$rel])) { $skipped[] = $rel . ' (md5-mismatch)'; continue; }
            // === /v1.2.2 fix ===
            $dst = dirname(__DIR__) . '/' . $rel;
            if (file_exists($dst)) {
                $bdst = $backupDir . '/' . $rel;
                @mkdir(dirname($bdst), 0755, true);
                @copy($dst, $bdst);
            }
            @mkdir(dirname($dst), 0755, true);
            if (@copy($src, $dst)) $replaced[] = $rel; else $skipped[] = $rel . ' (copy-failed)';
        }

        // Cleanup temp
        $rmrf = function ($p) use (&$rmrf) {
            if (is_dir($p)) {
                foreach (scandir($p) as $c) {
                    if ($c === '.' || $c === '..') continue;
                    $rmrf($p . '/' . $c);
                }
                @rmdir($p);
            } else { @unlink($p); }
        };
        $rmrf($tmpDir);

        // v1.2.41 BUG 2 & 3: dulu version.json ditulis dengan $target dan
        // respons selalu ok=true WALAU tidak satu berkas pun tergantikan.
        // Akibatnya dashboard memajang versi baru padahal nol berkas berubah,
        // dan masalahnya tidak terdeteksi hampir sebulan. Sekarang: kalau
        // $replaced kosong -> ERROR, dan version.json TIDAK ditulis, supaya
        // versi terpasang selalu mencerminkan kode yang benar-benar ada.
        if (empty($replaced)) {
            @rmdir($backupDir);   // backup kosong, tidak perlu disimpan
            jsonOut([
                'ok'      => false,
                'error'   => 'Update GAGAL: tidak satu berkas pun tergantikan. Versi terpasang tidak diubah.',
                'skipped' => $skipped,
            ], 500);
        }
        // Update version.json
        writeJson(DATA_DIR . '/version.json', [
            'version'      => $target,
            'installed_at' => wibDate('Y-m-d H:i:s'),   // v1.2.42: WIB
            'replaced'     => $replaced,
            'skipped'      => $skipped,
            'backup'       => basename($backupDir),
        ]);

        jsonOut([
            'ok' => true,
            'version'  => $target,
            'replaced' => $replaced,
            'skipped'  => $skipped,
            'backup'   => basename($backupDir),
        ]);
        break;
    }



    /* ============================================================
     *  v1.2.0 WA CLAIM — Endpoints: claim, release, list v2
     * ============================================================ */

    case 'wa_claim': {
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);

        // Run auto-process dulu supaya state fresh
        waClaimAutoProcess();

        // Cek current claim (mungkin sudah expired dan baru saja di-auto-release)
        $current = waClaimGet($num);
        if ($current) {
            $owner = $current['agent_username'] ?? '';
            if ($owner !== '' && $owner !== $u['username']) {
                jsonOut([
                    'ok' => false,
                    'error' => 'Chat sudah di-claim oleh ' . $owner . '. Gunakan take-over kalau butuh.',
                    'current_owner' => $owner,
                    'claimed_at' => $current['claimed_at'] ?? null,
                ], 409);
            }
        }

        $claim = [
            'agent_username' => $u['username'],
            'claimed_at' => time(),
            'last_agent_activity' => time(),
        ];
        if (!waClaimSet($num, $claim)) {
            jsonOut(['ok' => false, 'error' => 'Gagal menyimpan claim state'], 500);
        }
        waAuditLog('claim', $u['username'], $num);
        jsonOut([
            'ok' => true,
            'number' => $num,
            'claim' => $claim,
            'mode' => 'human',
        ]);
        break;
    }

    case 'wa_release': {
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);

        $current = waClaimGet($num);
        if (!$current) {
            jsonOut([
                'ok' => true,
                'number' => $num,
                'note' => 'Sudah tidak claimed (bot mode)',
                'mode' => 'bot',
            ]);
            break;
        }

        // Admin bisa release siapa saja, wa_agent hanya release milik sendiri
        $isAdmin = in_array($u['role'], ['super_admin','admin']);
        $owner = $current['agent_username'] ?? '';
        if (!$isAdmin && $owner !== $u['username']) {
            jsonOut([
                'ok' => false,
                'error' => 'Chat bukan milik Anda. Hanya admin yang bisa release chat agent lain.',
                'current_owner' => $owner,
            ], 403);
        }

        if (!waClaimSet($num, null)) {
            jsonOut(['ok' => false, 'error' => 'Gagal release'], 500);
        }
        $action = ($owner === $u['username']) ? 'release' : 'admin_release';
        waAuditLog($action, $u['username'], $num, ['from_agent' => $owner]);
        jsonOut([
            'ok' => true,
            'number' => $num,
            'released_by' => $u['username'],
            'mode' => 'bot',
        ]);
        break;
    }

    case 'wa_conversations_v2': {
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $me = $u['username'];
        $isAdmin = in_array($u['role'], ['super_admin','admin']);

        // Auto-process expired claims + takeover requests
        list($autoReleased, $autoApproved) = waClaimAutoProcess();
        waModeSweepIdle();   // v1.2.37: supaya lencana status tidak basi

        $filter = $_GET['filter'] ?? 'all';  // all|mine|unclaimed|others|takeover_requests

        // Read chat log untuk dapatkan list nomor + last message
        $logs = readJson(LOG_FILE, []);
        $numbers = [];  // num => {last_ts, last_q, last_a, count, awaiting}
        foreach ($logs as $e) {
            if (($e['channel'] ?? '') !== 'whatsapp') continue;
            $num = waNormNum($e['ip'] ?? '');
            if ($num === '') continue;
            if (!isset($numbers[$num])) {
                $numbers[$num] = [
                    'last_ts' => $e['ts'] ?? '',
                    'last_q' => $e['q'] ?? '',
                    'last_a' => $e['a'] ?? '',
                    'count' => 0,
                    'awaiting' => !empty($e['awaiting']),
                    // v1.2.17: dipakai filter "Perlu Perhatian". Entri pertama yang
                    // ditemui = entri TERAKHIR (log disimpan terbaru-dulu).
                    'last_dir' => $e['dir'] ?? '',
                    'bot_failed' => (!empty($e['cap_reached']) || !empty($e['suspended']) || !empty($e['ai_error'])),
                ];
            }
            $numbers[$num]['count']++;
        }

        // Get semua claim state sekaligus (1 file read)
        $allClaims = waClaimGetAll();
        $allContacts = waGetContacts();   // v1.2.19: 1 file read untuk semua nomor
        $allLeads = leadsGetAll();        // v1.2.21: tandai nomor yang sudah punya kartu lead

        // Build result with claim state
        $result = [];
        $cntToday = 0; $cntAttention = 0;   // v1.2.17
        $todayStr = date('Y-m-d');          // sejam dengan penulisan log (date(), bukan WIB helper)
        foreach ($numbers as $num => $meta) {
            $claim = $allClaims[$num] ?? null;
            $mode = $claim ? 'human' : waGetMode($num);  // fallback ke waGetMode kalau tidak claimed
            $status = 'bot';
            if ($claim) {
                $status = 'claimed';
                if (!empty($claim['takeover_request'])) $status = 'takeover_requested';
            } elseif ($mode === 'human') {
                // human mode tapi tidak ada claim (auto-handoff via keyword, atau legacy)
                $status = 'human_unclaimed';
            }

            // v1.2.17: perlu perhatian = belum dibalas manual DAN (bot gagal ATAU menggantung ke manusia)
            $isToday = (substr((string)$meta['last_ts'], 0, 10) === $todayStr);
            $needsAttention = false;
            if (($meta['last_dir'] ?? '') !== 'manual') {
                if (!empty($meta['bot_failed'])) {
                    $needsAttention = true;
                } elseif ($status === 'human_unclaimed' || !empty($meta['awaiting'])) {
                    $needsAttention = true;
                }
            }
            if ($isToday) $cntToday++;
            if ($needsAttention) $cntAttention++;

            $item = [
                'number' => $num,
                'name' => waContactName($num, $allContacts),   // v1.2.19
                'has_lead' => isset($allLeads[$num]),          // v1.2.21
                'stage' => waContactStage($num, $allContacts), // v1.2.39
                'vip' => waContactVip($num, $allContacts),     // v1.2.39
                'last_ts' => $meta['last_ts'],
                'needs_attention' => $needsAttention,
                'last_q' => mb_substr($meta['last_q'] ?? '', 0, 200),
                'last_a' => mb_substr($meta['last_a'] ?? '', 0, 100),
                'count' => $meta['count'],
                'awaiting' => $meta['awaiting'],
                'mode' => $mode,
                'status' => $status,
                'claim' => $claim,
            ];

            // Apply filter
            $show = false;
            switch ($filter) {
                case 'mine':
                    $show = $claim && ($claim['agent_username'] ?? '') === $me;
                    break;
                case 'unclaimed':
                    // Termasuk bot mode DAN human tanpa claim (menunggu di-pick up)
                    $show = !$claim;
                    break;
                case 'others':
                    $show = $claim && ($claim['agent_username'] ?? '') !== $me;
                    break;
                case 'takeover_requests':
                    // Filter untuk Phase 3 — sekarang belum ada takeover, return kosong
                    if ($claim && !empty($claim['takeover_request'])) {
                        $req = $claim['takeover_request'];
                        $isTarget = ($claim['agent_username'] ?? '') === $me;
                        $isRequester = ($req['requester'] ?? '') === $me;
                        $show = $isAdmin || $isTarget || $isRequester;
                    }
                    break;
                case 'today':               // v1.2.17
                    $show = $isToday;
                    break;
                case 'attention':           // v1.2.17
                    $show = $needsAttention;
                    break;
                case 'all':
                default:
                    $show = true;
            }
            if ($show) $result[] = $item;
        }

        // Sort by last_ts desc
        usort($result, function ($a, $b) {
            return strcmp($b['last_ts'] ?? '', $a['last_ts'] ?? '');
        });

        // Counts per filter (untuk badge)
        $counts = ['all' => count($numbers), 'mine' => 0, 'unclaimed' => 0, 'others' => 0, 'takeover_requests' => 0, 'today' => $cntToday, 'attention' => $cntAttention];  // v1.2.17
        foreach ($numbers as $num => $meta) {
            $claim = $allClaims[$num] ?? null;
            if (!$claim) {
                $counts['unclaimed']++;
            } elseif (($claim['agent_username'] ?? '') === $me) {
                $counts['mine']++;
            } else {
                $counts['others']++;
            }
            if ($claim && !empty($claim['takeover_request'])) {
                $req = $claim['takeover_request'];
                if ($isAdmin || ($claim['agent_username'] ?? '') === $me || ($req['requester'] ?? '') === $me) {
                    $counts['takeover_requests']++;
                }
            }
        }

        jsonOut([
            'ok' => true,
            'conversations' => $result,
            'counts' => $counts,
            'auto_processed' => ['released' => $autoReleased, 'approved' => $autoApproved],
            'me' => $me,
            'is_admin' => $isAdmin,
            'filter' => $filter,
        ]);
        break;
    }

    /* ============================================================
     *  v1.2.0 WA CLAIM — Endpoint: audit log viewer
     * ============================================================ */

    /* ============================================================
     *  v1.2.0 WA CLAIM — Endpoints: take-over workflow (Phase 3)
     * ============================================================ */

    case 'wa_takeover_request': {
        // Hanya wa_agent yang request; admin pakai wa_admin_takeover
        $u = requireAuth(['wa_agent']);
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        $reason = trim((string)($in['reason'] ?? ''));
        if (mb_strlen($reason) > 500) $reason = mb_substr($reason, 0, 500);
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);

        waClaimAutoProcess();

        $current = waClaimGet($num);
        if (!$current) {
            jsonOut(['ok' => false, 'error' => 'Chat tidak claimed. Silakan claim langsung dengan wa_claim.'], 400);
        }
        if (($current['agent_username'] ?? '') === $u['username']) {
            jsonOut(['ok' => false, 'error' => 'Chat sudah milik Anda.'], 400);
        }
        if (!empty($current['takeover_request'])) {
            $existing = $current['takeover_request'];
            if (($existing['requester'] ?? '') === $u['username']) {
                jsonOut([
                    'ok' => true,
                    'note' => 'Request Anda masih pending',
                    'requested_at' => $existing['requested_at'] ?? null,
                    'auto_approve_in_seconds' => max(0, 300 - (time() - ($existing['requested_at'] ?? time()))),
                ]);
                break;
            } else {
                jsonOut([
                    'ok' => false,
                    'error' => 'Sudah ada request take-over pending dari ' . ($existing['requester'] ?? 'agent lain'),
                ], 409);
            }
        }

        // Set request
        $current['takeover_request'] = [
            'requester' => $u['username'],
            'requested_at' => time(),
            'reason' => $reason,
        ];
        if (!waClaimSet($num, $current)) {
            jsonOut(['ok' => false, 'error' => 'Gagal simpan request'], 500);
        }
        waAuditLog('takeover_request', $u['username'], $num, [
            'target_agent' => $current['agent_username'] ?? '',
            'reason' => $reason,
        ]);
        jsonOut([
            'ok' => true,
            'number' => $num,
            'target_agent' => $current['agent_username'] ?? '',
            'auto_approve_in_seconds' => 300,
            'note' => 'Request pending. Kalau owner tidak respond dalam 5 menit, request auto-approved.',
        ]);
        break;
    }

    case 'wa_takeover_respond': {
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        $decisionRaw = strtolower(trim((string)($in['decision'] ?? '')));
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        if (!in_array($decisionRaw, ['approve', 'deny'])) {
            jsonOut(['ok' => false, 'error' => 'decision harus "approve" atau "deny"'], 400);
        }

        $current = waClaimGet($num);
        if (!$current || empty($current['takeover_request'])) {
            jsonOut(['ok' => false, 'error' => 'Tidak ada take-over request untuk nomor ini'], 404);
        }
        $req = $current['takeover_request'];
        $owner = $current['agent_username'] ?? '';
        $isAdmin = in_array($u['role'], ['super_admin','admin']);

        // Only owner atau admin yang boleh respond
        if (!$isAdmin && $owner !== $u['username']) {
            jsonOut(['ok' => false, 'error' => 'Hanya owner chat atau admin yang bisa respond request'], 403);
        }

        if ($decisionRaw === 'approve') {
            $current['agent_username'] = $req['requester'];
            $current['claimed_at'] = time();
            $current['last_agent_activity'] = time();
            unset($current['takeover_request']);
            waClaimSet($num, $current);
            waAuditLog('takeover_approve', $u['username'], $num, [
                'from_agent' => $owner,
                'to_agent' => $req['requester'],
                'requester_reason' => $req['reason'] ?? '',
            ]);
            jsonOut([
                'ok' => true,
                'number' => $num,
                'decision' => 'approve',
                'new_owner' => $req['requester'],
                'from_agent' => $owner,
            ]);
        } else {
            unset($current['takeover_request']);
            waClaimSet($num, $current);
            waAuditLog('takeover_deny', $u['username'], $num, [
                'requester' => $req['requester'],
                'kept_owner' => $owner,
            ]);
            jsonOut([
                'ok' => true,
                'number' => $num,
                'decision' => 'deny',
                'requester' => $req['requester'],
                'kept_owner' => $owner,
            ]);
        }
        break;
    }

    case 'wa_admin_takeover': {
        $u = requireAuth(['super_admin','admin']);
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        $reason = trim((string)($in['reason'] ?? 'admin_action'));
        if (mb_strlen($reason) > 500) $reason = mb_substr($reason, 0, 500);
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);

        $current = waClaimGet($num);
        $oldAgent = $current['agent_username'] ?? '(none)';

        // Force claim untuk admin ini
        $claim = [
            'agent_username' => $u['username'],
            'claimed_at' => time(),
            'last_agent_activity' => time(),
        ];
        if (!waClaimSet($num, $claim)) {
            jsonOut(['ok' => false, 'error' => 'Gagal admin_takeover'], 500);
        }
        waAuditLog('admin_takeover', $u['username'], $num, [
            'from_agent' => $oldAgent,
            'reason' => $reason,
        ]);
        jsonOut([
            'ok' => true,
            'number' => $num,
            'from_agent' => $oldAgent,
            'new_owner' => $u['username'],
            'reason' => $reason,
        ]);
        break;
    }

    case 'wa_audit_log': {
        requireAuth(['super_admin', 'admin']);
        $limit = min(200, max(10, (int)($_GET['limit'] ?? 50)));
        $all = readJson(waAuditLogFile(), []);
        $entries = array_slice($all, 0, $limit);
        jsonOut([
            'ok' => true,
            'entries' => $entries,
            'total' => count($all),
            'shown' => count($entries),
        ]);
        break;
    }

    default:
        jsonOut(['ok' => false, 'error' => 'Unknown action: ' . $action], 404);
}
