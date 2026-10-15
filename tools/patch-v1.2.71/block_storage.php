
/* ============================================================================
 * v1.2.71: DRIVER PENYIMPANAN & ANTREAN (server self-hosted, mis. Halte Bus)
 *
 * Satu kode untuk dua mesin. Berkas OPSIONAL data/server.php (tidak pernah
 * ikut paket update, karena data/ tidak disentuh updater) mengembalikan:
 *
 *   <?php return [
 *     'storage' => 'mysql',            // 'file' (bawaan) | 'mysql'
 *     'queue'   => 'redis',            // 'sync' (bawaan) | 'redis'
 *     'db'      => ['host' => '127.0.0.1', 'port' => 3306, 'name' => 'sj_chat', 'user' => 'sj', 'pass' => '...'],
 *     'redis'   => ['host' => '127.0.0.1', 'port' => 6379, 'db' => 0, 'prefix' => 'sj:'],
 *   ];
 *
 * Tanpa berkas itu: 'file' + 'sync' = perilaku lama di shared hosting.
 * ATURAN PENGEMBANGAN: data yang ditulis tiap pesan (log, sesi WA, kontak)
 * HANYA lewat fungsi di blok ini — jangan readJson/writeJson berkasnya
 * langsung. tools/cek-storage.sh menolak rilis yang melanggar.
 * ========================================================================= */
function deiServerConf() {
    static $c = null;
    if ($c === null) {
        $c = [];
        $f = DATA_DIR . '/server.php';
        if (is_file($f)) { $r = include $f; if (is_array($r)) $c = $r; }
        $c['storage'] = (($c['storage'] ?? 'file') === 'mysql') ? 'mysql' : 'file';
        $c['queue']   = (($c['queue'] ?? 'sync') === 'redis') ? 'redis' : 'sync';
    }
    return $c;
}
function deiStorageMysql() { return deiServerConf()['storage'] === 'mysql'; }
// Mode antrean hanya aktif kalau Redis benar-benar bisa dihubungi. Kalau Redis mati,
// webhook jatuh ke pemrosesan langsung dan idempotensi/kunci memakai MySQL/berkas.
function deiQueueRedis() {
    static $ok = null;
    if ($ok === null) {
        $ok = false;
        if (deiServerConf()['queue'] === 'redis' && class_exists('Redis')) {
            try { $ok = (bool)deiRedis()->ping(); }
            catch (\Throwable $e) { error_log('Redis tidak bisa dihubungi: ' . $e->getMessage()); }
        }
    }
    return $ok;
}

function deiDb() {
    static $pdo = null;
    if ($pdo === null) {
        $d = deiServerConf()['db'] ?? [];
        $dsn = 'mysql:host=' . ($d['host'] ?? '127.0.0.1') . ';port=' . (int)($d['port'] ?? 3306)
             . ';dbname=' . ($d['name'] ?? '') . ';charset=utf8mb4';
        $pdo = new PDO($dsn, (string)($d['user'] ?? ''), (string)($d['pass'] ?? ''), [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]);
        $pdo->exec("SET time_zone = '+07:00'");
    }
    return $pdo;
}
function deiRedis() {
    static $r = null;
    if ($r === null) {
        $c = deiServerConf()['redis'] ?? [];
        $x = new Redis();
        $x->connect((string)($c['host'] ?? '127.0.0.1'), (int)($c['port'] ?? 6379), 2.0);
        if (!empty($c['pass'])) $x->auth((string)$c['pass']);
        if (!empty($c['db'])) $x->select((int)$c['db']);
        $x->setOption(Redis::OPT_PREFIX, (string)($c['prefix'] ?? 'dei:'));
        $x->setOption(Redis::OPT_READ_TIMEOUT, -1);
        $r = $x;
    }
    return $r;
}

// Skema MySQL — satu sumber; dijalankan lewat `php api/index.php action=db_init`.
function deiDbSchema() {
    return [
        "CREATE TABLE IF NOT EXISTS dei_log (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            ts DATETIME NULL,
            num VARCHAR(32) NOT NULL DEFAULT '',
            channel VARCHAR(16) NOT NULL DEFAULT '',
            body MEDIUMTEXT NOT NULL,
            KEY num_id (num, id),
            KEY ts (ts)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
        "CREATE TABLE IF NOT EXISTS dei_wa_sessions (
            num VARCHAR(32) NOT NULL PRIMARY KEY,
            ts INT UNSIGNED NOT NULL,
            turns MEDIUMTEXT NOT NULL,
            KEY ts (ts)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
        "CREATE TABLE IF NOT EXISTS dei_contacts (
            num VARCHAR(32) NOT NULL PRIMARY KEY,
            body TEXT NOT NULL,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
        "CREATE TABLE IF NOT EXISTS dei_conv_state (
            num VARCHAR(32) NOT NULL PRIMARY KEY,
            last_at INT UNSIGNED NOT NULL DEFAULT 0,
            body TEXT NOT NULL,
            KEY last_at (last_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
        "CREATE TABLE IF NOT EXISTS dei_wa_seen (
            wamid VARCHAR(191) NOT NULL PRIMARY KEY,
            ts INT UNSIGNED NOT NULL,
            KEY ts (ts)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
    ];
}

/* ---------- Kunci lintas proses (dua mode) ----------
 * flock di data/.locks/<nama>.lock. Reentrant per proses: fungsi yang sudah
 * memegang kunci boleh memanggil fungsi lain yang meminta kunci yang sama. */
function deiWithLock($name, $fn) {
    static $held = [];
    if (!empty($held[$name])) return $fn();
    $dir = DATA_DIR . '/.locks';
    if (!is_dir($dir)) @mkdir($dir, 0755, true);
    $fp = @fopen($dir . '/' . preg_replace('/[^a-z0-9_-]/i', '_', $name) . '.lock', 'c');
    if ($fp) @flock($fp, LOCK_EX);
    $held[$name] = true;
    try {
        return $fn();
    } finally {
        unset($held[$name]);
        if ($fp) { @flock($fp, LOCK_UN); @fclose($fp); }
    }
}

/* ---------- Log percakapan ---------- */
function logEncode($e) {
    return json_encode($e, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_INVALID_UTF8_SUBSTITUTE);
}
function logRowNum($e) {
    return (($e['channel'] ?? '') === 'whatsapp') ? substr(preg_replace('/\D/', '', (string)($e['ip'] ?? '')), 0, 32) : '';
}
// Jendela baca untuk dashboard/statistik: sama dengan log_limit di mode file.
function logWindow() {
    static $w = null;
    if ($w === null) {
        $s = readJson(SETTINGS_FILE, []);
        $w = max(500, (int)($s['api']['log_limit'] ?? 500));
    }
    return $w;
}
function logDbInsert($e) {
    $ts = (string)($e['ts'] ?? '');
    $st = deiDb()->prepare('INSERT INTO dei_log (ts, num, channel, body) VALUES (?, ?, ?, ?)');
    $st->execute([preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/', $ts) ? $ts : null,
                  logRowNum($e), substr((string)($e['channel'] ?? ''), 0, 16), logEncode($e)]);
}
// Semua entri log terbaru-dulu (bentuk persis isi chatbot-log.json).
function logReadAll() {
    if (!deiStorageMysql()) {
        $l = readJson(LOG_FILE, []);
        return is_array($l) ? $l : [];
    }
    $out = [];
    foreach (deiDb()->query('SELECT body FROM dei_log ORDER BY id DESC LIMIT ' . (int)logWindow(), PDO::FETCH_COLUMN, 0) as $b) {
        $e = json_decode($b, true);
        if (is_array($e)) $out[] = $e;
    }
    return $out;
}
// Entri WhatsApp satu nomor, terbaru-dulu.
function logReadByNumber($num, $max = 200) {
    $num = preg_replace('/\D/', '', (string)$num);
    if ($num === '') return [];
    if (!deiStorageMysql()) {
        $out = [];
        foreach (logReadAll() as $e) {
            if (($e['channel'] ?? '') !== 'whatsapp') continue;
            if (preg_replace('/\D/', '', (string)($e['ip'] ?? '')) !== $num) continue;
            $out[] = $e;
            if (count($out) >= $max) break;
        }
        return $out;
    }
    $st = deiDb()->prepare('SELECT body FROM dei_log WHERE num = ? ORDER BY id DESC LIMIT ' . (int)$max);
    $st->execute([$num]);
    $out = [];
    foreach ($st->fetchAll(PDO::FETCH_COLUMN, 0) as $b) { $e = json_decode($b, true); if (is_array($e)) $out[] = $e; }
    return $out;
}
function logDbMutate($fn) {
    $db = deiDb();
    $db->query("SELECT GET_LOCK('dei_log_mutate', 30)");
    try {
        $logs = []; $orig = [];
        foreach ($db->query('SELECT id, body FROM dei_log ORDER BY id DESC LIMIT ' . (int)logWindow())->fetchAll() as $r) {
            $e = json_decode($r['body'], true);
            if (!is_array($e)) $e = [];
            $e['_dei_id'] = (int)$r['id'];
            $orig[(int)$r['id']] = $r['body'];
            $logs[] = $e;
        }
        $res = $fn($logs);
        if (!is_array($logs)) $logs = [];
        if ($res !== false) {
            $keep = []; $new = [];
            $upd = $db->prepare('UPDATE dei_log SET ts = ?, num = ?, channel = ?, body = ? WHERE id = ?');
            foreach ($logs as $e) {
                if (!is_array($e)) continue;
                $id = (int)($e['_dei_id'] ?? 0);
                unset($e['_dei_id']);
                if ($id > 0 && isset($orig[$id]) && !isset($keep[$id])) {
                    $keep[$id] = true;
                    $b = logEncode($e);
                    if ($b !== $orig[$id]) {
                        $ts = (string)($e['ts'] ?? '');
                        $upd->execute([preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/', $ts) ? $ts : null,
                                       logRowNum($e), substr((string)($e['channel'] ?? ''), 0, 16), $b, $id]);
                    }
                } else {
                    $new[] = $e;
                }
            }
            // Elemen paling depan = paling baru -> disisipkan paling akhir (id terbesar).
            foreach (array_reverse($new) as $e) logDbInsert($e);
            $gone = array_diff_key($orig, $keep);
            if ($gone) $db->exec('DELETE FROM dei_log WHERE id IN (' . implode(',', array_map('intval', array_keys($gone))) . ')');
        }
        foreach ($logs as &$e) { if (is_array($e)) unset($e['_dei_id']); }
        unset($e);
        return $logs;
    } finally {
        $db->query("SELECT RELEASE_LOCK('dei_log_mutate')");
    }
}

/* ---------- Kontak WhatsApp ---------- */
function waContactDefaults() {
    $now = date('Y-m-d H:i:s');
    return ['name_wa' => '', 'name_manual' => '', 'first_seen' => $now, 'last_seen' => $now];
}
// Satu kontak (null kalau belum ada).
function waContactGet($number) {
    $number = preg_replace('/\D/', '', (string)$number);
    if ($number === '') return null;
    if (!deiStorageMysql()) {
        $all = waGetContacts();
        return (isset($all[$number]) && is_array($all[$number])) ? $all[$number] : null;
    }
    $st = deiDb()->prepare('SELECT body FROM dei_contacts WHERE num = ?');
    $st->execute([$number]);
    $b = $st->fetchColumn();
    $c = ($b === false) ? null : json_decode($b, true);
    return is_array($c) ? $c : null;
}
// Peta [nomor => kontak] yang cukup untuk membaca satu nomor.
function waContactsFor($number) {
    if (!deiStorageMysql()) return waGetContacts();
    $number = preg_replace('/\D/', '', (string)$number);
    $c = waContactGet($number);
    return $c === null ? [] : [$number => $c];
}
// Ubah satu kontak secara atomik. $fn(array &$row, bool $isNew); kembalikan false untuk batal.
function waContactUpdate($number, $fn) {
    $number = preg_replace('/\D/', '', (string)$number);
    if ($number === '') return null;
    if (!deiStorageMysql()) {
        return deiWithLock('wa-contacts', function () use ($number, $fn) {
            $all = waGetContacts();
            $isNew = !isset($all[$number]) || !is_array($all[$number]);
            $row = $isNew ? waContactDefaults() : $all[$number];
            if ($fn($row, $isNew) === false) return $isNew ? null : $all[$number];
            $all[$number] = $row;
            writeJson(CONTACTS_FILE, $all);
            return $row;
        });
    }
    // Baris dibuat dulu (INSERT IGNORE, autocommit) supaya FOR UPDATE mengunci baris,
    // bukan celah indeks — dua kontak baru bersamaan tidak saling deadlock.
    $db = deiDb();
    for ($attempt = 1; ; $attempt++) {
        try {
            $ins = $db->prepare('INSERT IGNORE INTO dei_contacts (num, body) VALUES (?, ?)');
            $ins->execute([$number, logEncode(waContactDefaults())]);
            $isNew = ($ins->rowCount() === 1);
            $db->beginTransaction();
            $st = $db->prepare('SELECT body FROM dei_contacts WHERE num = ? FOR UPDATE');
            $st->execute([$number]);
            $row = json_decode((string)$st->fetchColumn(), true);
            if (!is_array($row)) $row = waContactDefaults();
            $before = $row;
            if ($fn($row, $isNew) === false) {
                if ($isNew) $db->prepare('DELETE FROM dei_contacts WHERE num = ?')->execute([$number]);
                $db->commit();
                return $isNew ? null : $before;
            }
            $db->prepare('UPDATE dei_contacts SET body = ? WHERE num = ?')->execute([logEncode($row), $number]);
            $db->commit();
            return $row;
        } catch (\PDOException $e) {
            if ($db->inTransaction()) $db->rollBack();
            if ((int)($e->errorInfo[1] ?? 0) === 1213 && $attempt < 4) { usleep(50000 * $attempt); continue; }
            throw $e;
        }
    }
}

/* ---------- Pesan WA sudah diproses? (idempotensi wamid) ---------- */
function waMsgSeen($wamid) {
    $wamid = substr((string)$wamid, 0, 191);
    if ($wamid === '') return false;
    if (deiQueueRedis()) return (bool)deiRedis()->exists('seen:' . $wamid);
    if (deiStorageMysql()) {
        $st = deiDb()->prepare('SELECT 1 FROM dei_wa_seen WHERE wamid = ?');
        $st->execute([$wamid]);
        return (bool)$st->fetchColumn();
    }
    $all = readJson(DATA_DIR . '/wa-seen.json', []);
    return is_array($all) && isset($all[$wamid]);
}
function waMsgMarkSeen($wamid) {
    $wamid = substr((string)$wamid, 0, 191);
    if ($wamid === '') return;
    if (deiQueueRedis()) { deiRedis()->set('seen:' . $wamid, 1, ['ex' => 3 * 86400]); return; }
    if (deiStorageMysql()) {
        deiDb()->prepare('INSERT IGNORE INTO dei_wa_seen (wamid, ts) VALUES (?, ?)')->execute([$wamid, time()]);
        return;
    }
    deiWithLock('wa-seen', function () use ($wamid) {
        $f = DATA_DIR . '/wa-seen.json';
        $all = readJson($f, []);
        if (!is_array($all)) $all = [];
        $all[$wamid] = time();
        if (count($all) > 3000) { asort($all); $all = array_slice($all, -2000, null, true); }
        writeJson($f, $all);
    });
}

/* ---------- Kunci per nomor (hanya mode antrean) ----------
 * Pesan dari satu nomor diproses berurutan; nomor berbeda tetap paralel. */
function deiNumLock($num, $fn) {
    if (!deiQueueRedis()) return $fn();
    $r = deiRedis();
    $key = 'lock:wa:' . preg_replace('/\D/', '', (string)$num);
    // Nilai kunci = "<slot>:<token>" supaya slot yang hidup lagi bisa melepas kunci peninggalannya.
    $tok = ($GLOBALS['dei_worker_slot'] ?? 'web') . ':' . bin2hex(random_bytes(8));
    $deadline = microtime(true) + 130;
    while (!$r->set($key, $tok, ['nx', 'ex' => 120])) {
        if (microtime(true) > $deadline) break;   // jangan macet selamanya
        usleep(200000);
    }
    try {
        return $fn();
    } finally {
        if ($r->get($key) === $tok) $r->del($key);
    }
}

/* ---------- Bersih-bersih berkala (cron_tick) ----------
 * Sesi WA > 7 hari dihapus (bot sudah mengabaikannya setelah 6 jam) supaya
 * jumlah berkas/baris tidak tumbuh tanpa batas. */
function deiPurgeSessions() {
    if (deiStorageMysql()) {
        $db = deiDb();
        $n  = $db->exec('DELETE FROM dei_wa_sessions WHERE ts < ' . (time() - 7 * 86400));
        $db->exec('DELETE FROM dei_wa_seen WHERE ts < ' . (time() - 3 * 86400));
        $db->exec('DELETE FROM dei_conv_state WHERE last_at < ' . (time() - 3 * 86400));
        return (int)$n;
    }
    if (!is_dir(WA_SESSIONS_DIR)) return 0;
    $n = 0; $cut = time() - 7 * 86400;
    foreach ((array)glob(WA_SESSIONS_DIR . '/*.json') as $f) {
        if (@filemtime($f) < $cut && @unlink($f)) $n++;
        if ($n >= 500) break;   // sisanya di tick berikutnya
    }
    return $n;
}

/* ---------- Jejak percakapan (conv-state) untuk auto-closing & eskalasi ----------
 * Mode file: conv-state.json (dipangkas 3 hari). Mode mysql: tabel dei_conv_state. */
function convStateReadAll() {
    if (!deiStorageMysql()) {
        $f = CONV_STATE_FILE;   // lewat variabel: langkah 6c patch mengganti pola pembaca langsung
        $a = readJson($f, []);
        return is_array($a) ? $a : [];
    }
    $out = [];
    $st = deiDb()->prepare('SELECT num, body FROM dei_conv_state WHERE last_at >= ?');
    $st->execute([time() - 3 * 86400]);
    foreach ($st->fetchAll() as $r) { $b = json_decode($r['body'], true); if (is_array($b)) $out[(string)$r['num']] = $b; }
    return $out;
}
// Mode mysql: hanya baris $num yang dikunci & diberikan ke $fn sebagai [$num => state].
function convStateDbMutateOne($fn, $num) {
    $num = waNormNum($num);
    $db = deiDb();
    for ($attempt = 1; ; $attempt++) {
        try {
            $ins = $db->prepare("INSERT IGNORE INTO dei_conv_state (num, last_at, body) VALUES (?, 0, '{}')");
            $ins->execute([$num]);
            $isNew = ($ins->rowCount() === 1);
            $db->beginTransaction();
            $st = $db->prepare('SELECT body FROM dei_conv_state WHERE num = ? FOR UPDATE');
            $st->execute([$num]);
            $row = json_decode((string)$st->fetchColumn(), true);
            $all = (!$isNew && is_array($row) && $row) ? [$num => $row] : [];
            $res = $fn($all);
            if (isset($all[$num]) && is_array($all[$num])) {
                $db->prepare('UPDATE dei_conv_state SET last_at = ?, body = ? WHERE num = ?')
                   ->execute([(int)($all[$num]['last_at'] ?? 0), logEncode($all[$num]), $num]);
            } else {
                $db->prepare('DELETE FROM dei_conv_state WHERE num = ?')->execute([$num]);
            }
            $db->commit();
            return $res;
        } catch (\PDOException $e) {
            if ($db->inTransaction()) $db->rollBack();
            if ((int)($e->errorInfo[1] ?? 0) === 1213 && $attempt < 4) { usleep(50000 * $attempt); continue; }
            throw $e;
        }
    }
}

// Lepas kunci nomor milik slot worker yang mati (dipanggil saat slot itu start lagi).
function deiNumLockRelease($job, $slot) {
    $j = is_array($job) ? $job : json_decode((string)$job, true);
    $p = json_decode((string)($j['raw'] ?? ''), true);
    if (!is_array($p)) return;
    $r = deiRedis();
    foreach (($p['entry'] ?? []) as $en) foreach (($en['changes'] ?? []) as $ch) foreach (($ch['value']['messages'] ?? []) as $m) {
        $key = 'lock:wa:' . preg_replace('/\D/', '', (string)($m['from'] ?? ''));
        $v = (string)$r->get($key);
        if ($v !== '' && strpos($v, $slot . ':') === 0) $r->del($key);
    }
}
