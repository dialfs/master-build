
/* ---------- v1.2.101: percakapan — penyimpanan dua mode ----------
 * file : conv-open.json {nomor: record terakhir} = yang masih terbuka + yang selesai <= 24 jam
 *        (untuk buka-ulang & balasan susulan). Record selesai/kedaluwarsa di-append ke
 *        convs/YYYY-MM.jsonl (bulan percakapan dibuka); pembaca memakai baris TERAKHIR per id.
 * mysql: tabel dei_conversations (satu baris per percakapan). */
define('CONV_OPEN_FILE', DATA_DIR . '/conv-open.json');
define('CONV_DIR', DATA_DIR . '/convs');
if (!defined('CONV_ATTACH_SEC')) define('CONV_ATTACH_SEC', 86400);   // record selesai disimpan di "terbuka" selama ini
function convDbSchemaSql() {
    return "CREATE TABLE IF NOT EXISTS dei_conversations (
            id VARCHAR(48) NOT NULL PRIMARY KEY,
            num VARCHAR(32) NOT NULL,
            ch VARCHAR(48) NOT NULL DEFAULT '',
            status VARCHAR(12) NOT NULL DEFAULT 'open',
            opened_at INT UNSIGNED NOT NULL,
            last_at INT UNSIGNED NOT NULL DEFAULT 0,
            resolved_at INT UNSIGNED NOT NULL DEFAULT 0,
            agent VARCHAR(64) NOT NULL DEFAULT '',
            body TEXT NOT NULL,
            KEY num_opened (num, opened_at),
            KEY opened (opened_at),
            KEY status_last (status, last_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci";
}
function convIsFinal($c) { return is_array($c) && in_array((string)($c['status'] ?? ''), ['resolved', 'expired'], true); }
// Tabel belum dibuat (server sendiri yang belum menjalankan db_init setelah update) -> buat sekali, ulangi.
function convDbRun($fn) {
    try { return $fn(); }
    catch (\PDOException $e) {
        if ((string)$e->getCode() !== '42S02') throw $e;
        deiDb()->exec(convDbSchemaSql());
        return $fn();
    }
}
function convDbSave($c) {
    deiDb()->prepare('INSERT INTO dei_conversations (id, num, ch, status, opened_at, last_at, resolved_at, agent, body) VALUES (?,?,?,?,?,?,?,?,?)
        ON DUPLICATE KEY UPDATE ch = VALUES(ch), status = VALUES(status), last_at = VALUES(last_at),
        resolved_at = VALUES(resolved_at), agent = VALUES(agent), body = VALUES(body)')
        ->execute([(string)$c['id'], (string)$c['num'], substr((string)($c['ch'] ?? ''), 0, 48), (string)$c['status'],
                   (int)$c['opened_at'], (int)($c['last_at'] ?? 0), (int)($c['resolved_at'] ?? 0),
                   substr((string)($c['agent'] ?? ''), 0, 64), logEncode($c)]);
}
function convFileAppend($c) {
    if (!is_dir(CONV_DIR)) @mkdir(CONV_DIR, 0755, true);
    @file_put_contents(CONV_DIR . '/' . wibDate('Y-m', (int)$c['opened_at']) . '.jsonl', logEncode($c) . "\n", FILE_APPEND | LOCK_EX);
}
// Baca-ubah-tulis percakapan terakhir satu nomor di bawah kunci. $fn(&$c, &$flush):
// $c = record terakhir (null bila tidak ada / sudah lewat masa susulan); boleh diganti record baru.
// $flush = record lain (yang baru diselesaikan) untuk disimpan juga.
function convStoreMutate($num, $fn) {
    $num = waNormNum($num);
    if ($num === '') return null;
    if (deiStorageMysql()) {
        return deiWithLock('conv-' . $num, function () use ($num, $fn) {
            return convDbRun(function () use ($num, $fn) {
                $st = deiDb()->prepare('SELECT body FROM dei_conversations WHERE num = ? ORDER BY opened_at DESC, id DESC LIMIT 1');
                $st->execute([$num]);
                $c = json_decode((string)$st->fetchColumn(), true);
                if (!is_array($c) || (convIsFinal($c) && time() - (int)($c['ended_at'] ?? 0) > CONV_ATTACH_SEC)) $c = null;
                $before = ($c === null) ? '' : logEncode($c);
                $flush = [];
                $res = $fn($c, $flush);
                foreach ($flush as $x) if (is_array($x)) convDbSave($x);
                if (is_array($c) && logEncode($c) !== $before) convDbSave($c);
                return $res;
            });
        });
    }
    return deiWithLock('conv', function () use ($num, $fn) {
        $f = CONV_OPEN_FILE;
        $all = readJson($f, []);
        if (!is_array($all)) $all = [];
        $c = is_array($all[$num] ?? null) ? $all[$num] : null;
        if ($c !== null && convIsFinal($c) && time() - (int)($c['ended_at'] ?? 0) > CONV_ATTACH_SEC) $c = null;
        $before = ($c === null) ? '' : logEncode($c);
        $flush = [];
        $res = $fn($c, $flush);
        $dirty = false;
        foreach ($flush as $x) { if (is_array($x) && convIsFinal($x)) convFileAppend($x); $dirty = true; }
        if (is_array($c) && logEncode($c) !== $before) {
            $all[$num] = $c;
            if (convIsFinal($c)) convFileAppend($c);
            $dirty = true;
        } elseif ($c === null && isset($all[$num]) && $flush) {
            unset($all[$num]);
        }
        if ($dirty) writeJson($f, $all);
        return $res;
    });
}
// Record terakhir satu nomor (hanya baca).
function convStoreGet($num) {
    $num = waNormNum($num);
    if ($num === '') return null;
    if (deiStorageMysql()) {
        return convDbRun(function () use ($num) {
            $st = deiDb()->prepare('SELECT body FROM dei_conversations WHERE num = ? ORDER BY opened_at DESC, id DESC LIMIT 1');
            $st->execute([$num]);
            $c = json_decode((string)$st->fetchColumn(), true);
            return is_array($c) ? $c : null;
        });
    }
    $f = CONV_OPEN_FILE;
    $all = readJson($f, []);
    return is_array($all[$num] ?? null) ? $all[$num] : null;
}
// Semua record yang belum selesai (untuk sapu timeout).
function convStoreOpen() {
    if (deiStorageMysql()) {
        return convDbRun(function () {
            $out = [];
            foreach (deiDb()->query("SELECT body FROM dei_conversations WHERE status IN ('open','handover','assigned')")->fetchAll() as $r) {
                $c = json_decode((string)$r['body'], true);
                if (is_array($c)) $out[] = $c;
            }
            return $out;
        });
    }
    $f = CONV_OPEN_FILE;
    $all = readJson($f, []);
    $out = [];
    foreach ((is_array($all) ? $all : []) as $c) if (is_array($c) && !convIsFinal($c)) $out[] = $c;
    return $out;
}
// Mode file: buang record selesai yang sudah lewat masa susulan (sudah tersimpan di convs/*.jsonl).
function convStoreEvict($now = null) {
    if (deiStorageMysql()) return 0;
    $now = $now ?? time();
    return deiWithLock('conv', function () use ($now) {
        $f = CONV_OPEN_FILE;
        $all = readJson($f, []);
        if (!is_array($all)) return 0;
        $n = 0;
        foreach ($all as $k => $c) {
            if (!is_array($c) || (convIsFinal($c) && $now - (int)($c['ended_at'] ?? 0) > CONV_ATTACH_SEC)) { unset($all[$k]); $n++; }
        }
        if ($n) writeJson($f, $all);
        return $n;
    });
}
// Percakapan yang DIBUKA dalam rentang [from, to] (ts).
function convStoreRange($fromTs, $toTs) {
    if (deiStorageMysql()) {
        return convDbRun(function () use ($fromTs, $toTs) {
            $st = deiDb()->prepare('SELECT body FROM dei_conversations WHERE opened_at BETWEEN ? AND ? ORDER BY opened_at');
            $st->execute([(int)$fromTs, (int)$toTs]);
            $out = [];
            while (($r = $st->fetch()) !== false) { $c = json_decode((string)$r['body'], true); if (is_array($c)) $out[] = $c; }
            return $out;
        });
    }
    $out = [];
    $y = (int)wibDate('Y', $fromTs); $mo = (int)wibDate('n', $fromTs);
    $endKey = wibDate('Y-m', $toTs);
    for ($i = 0; $i < 40; $i++) {
        $key = sprintf('%04d-%02d', $y, $mo);
        if ($key > $endKey) break;
        $mo++; if ($mo > 12) { $mo = 1; $y++; }
        $fh = @fopen(CONV_DIR . '/' . $key . '.jsonl', 'r');
        if (!$fh) continue;
        while (($line = fgets($fh)) !== false) {
            $c = json_decode($line, true);
            if (!is_array($c) || empty($c['id'])) continue;
            $t = (int)($c['opened_at'] ?? 0);
            if ($t >= $fromTs && $t <= $toTs) $out[$c['id']] = $c;   // baris terakhir per id yang berlaku
        }
        fclose($fh);
    }
    $f = CONV_OPEN_FILE;
    foreach ((array)readJson($f, []) as $c) {
        if (!is_array($c) || empty($c['id'])) continue;
        $t = (int)($c['opened_at'] ?? 0);
        if ($t >= $fromTs && $t <= $toTs) $out[$c['id']] = $c;
    }
    $out = array_values($out);
    usort($out, function ($a, $b) { return (int)$a['opened_at'] <=> (int)$b['opened_at']; });
    return $out;
}
