<?php
/**
 * Reset harian tenant DEMO (chatbot.deintegra.com/demo).
 *   php demo-reset.php                 -> hanya jalan sekali per hari (WIB); aman dipanggil cron tiap jam
 *   php demo-reset.php force=1         -> jalan sekarang walau hari ini sudah
 *   php demo-reset.php today=2026-12-03 force=1   -> uji: anggap hari ini tanggal itu
 *   (opsional) dir=/path/ke/demo  data=/path/demo-data.zip
 *
 * 1. Data contoh asli (demo-data.zip) diekstrak ke folder sementara.
 * 2. Semua tanggal & timestamp digeser N hari = hari ini - tanggal acuan (data/demo-anchor.json),
 *    jadi "hari ini", "minggu ini", jatuh tempo follow-up, dsb. selalu terisi.
 *    Berkas bulanan (convs/, agent-events/, sales-events/ YYYY-MM.jsonl) dikelompokkan ulang per bulan.
 * 3. Rahasia & berkas sistem tenant yang sedang jalan dipertahankan (kunci AI, pusat, WAHA, .secret, VAPID, versi, cache lisensi).
 * 4. Folder data ditukar; data lama disimpan sebagai data.prev di folder skrip ini (di luar public_html, satu generasi).
 * Akibatnya perubahan pengunjung demo (password, lead dihapus, dll.) kembali ke awal setiap hari.
 */
if (PHP_SAPI !== 'cli') { http_response_code(403); exit('CLI only'); }
date_default_timezone_set('Asia/Jakarta');
$args = [];
parse_str(implode('&', array_slice($argv, 1)), $args);
$home = getenv('HOME') ?: dirname(__DIR__);
$dir  = rtrim((string)($args['dir'] ?? ($home . '/public_html/chatbot.deintegra.com/demo')), '/');
$zipF = (string)($args['data'] ?? (__DIR__ . '/demo-data.zip'));
$today = (string)($args['today'] ?? date('Y-m-d'));
$force = !empty($args['force']);
$state = __DIR__ . '/demo-reset-state.json';
$fail = function ($m) { fwrite(STDERR, date('Y-m-d H:i:s') . " GAGAL: $m\n"); exit(1); };

if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $today)) $fail('tanggal today tidak sah');
$st = is_file($state) ? (json_decode((string)file_get_contents($state), true) ?: []) : [];
if (!$force && ($st['last'] ?? '') === $today) exit(0);
if (!is_dir($dir . '/data') || !is_file($dir . '/api/index.php')) $fail("tenant demo tidak ditemukan di $dir");
if (!is_file($zipF) || !class_exists('ZipArchive')) $fail("demo-data.zip / ZipArchive tidak ada");

$lock = fopen(__DIR__ . '/demo-reset.lock', 'c');
if (!$lock || !flock($lock, LOCK_EX | LOCK_NB)) exit(0);

function drRm(string $p): void {
    if (is_link($p) || is_file($p)) { @unlink($p); return; }
    if (!is_dir($p)) return;
    foreach (scandir($p) as $f) if ($f !== '.' && $f !== '..') drRm($p . '/' . $f);
    @rmdir($p);
}
function drCopy(string $a, string $b): void {
    if (is_dir($a)) { @mkdir($b, 0755, true); foreach (scandir($a) as $f) if ($f !== '.' && $f !== '..') drCopy($a . '/' . $f, $b . '/' . $f); }
    elseif (is_file($a)) @copy($a, $b);
}

// 1) ekstrak data asli
$tmp = __DIR__ . '/.data-new-' . bin2hex(random_bytes(3));
@mkdir($tmp, 0755);
$z = new ZipArchive();
if ($z->open($zipF) !== true) { drRm($tmp); $fail('demo-data.zip rusak'); }
$names = [];
for ($i = 0; $i < $z->numFiles; $i++) {
    $n = (string)$z->getNameIndex($i);
    if (strpos($n, '..') !== false || strpos($n, 'data/') !== 0) { $z->close(); drRm($tmp); $fail("entri tidak aman: $n"); }
    $names[] = $n;
}
$z->extractTo($tmp, $names); $z->close();
$new = $tmp . '/data';
$anchor = json_decode((string)@file_get_contents($new . '/demo-anchor.json'), true)['date'] ?? '';
if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $anchor)) { drRm($tmp); $fail('demo-anchor.json tidak ada'); }

// 2) geser tanggal
$days = (int)round((strtotime($today . ' 12:00:00') - strtotime($anchor . ' 12:00:00')) / 86400);
$secs = $days * 86400;
$aTs = strtotime($anchor . ' 12:00:00');
$lo = $aTs - 400 * 86400; $hi = $aTs + 400 * 86400;
$skip = ['settings.json', 'users.json', 'knowledge-base.json', 'pricelist.json', 'demo-anchor.json', 'push-categories.json'];
$shiftText = function (string $s) use ($days, $secs, $lo, $hi): string {
    if ($days === 0) return $s;
    $s = preg_replace_callback('/(?<![0-9])(20\d\d)-(\d\d)-(\d\d)(?![0-9])/', function ($m) use ($days) {
        if (!checkdate((int)$m[2], (int)$m[3], (int)$m[1])) return $m[0];
        return date('Y-m-d', strtotime(sprintf('%s-%s-%s 12:00:00', $m[1], $m[2], $m[3])) + $days * 86400);
    }, $s);
    return preg_replace_callback('/([:\[,]\s*)(1[789]\d{8})(?=\s*[,\}\]])/', function ($m) use ($secs, $lo, $hi) {
        $v = (int)$m[2];
        return ($v >= $lo && $v <= $hi) ? $m[1] . ($v + $secs) : $m[0];
    }, $s);
};
$monthOf = function (string $line) {
    $j = json_decode($line, true);
    if (is_array($j)) foreach (['t', 'opened_at', 'ts', 'at', 'last_at'] as $k) {
        if (isset($j[$k]) && is_int($j[$k])) return date('Y-m', $j[$k]);
        if (isset($j[$k]) && is_string($j[$k]) && preg_match('/^(\d{4}-\d{2})-\d{2}/', $j[$k], $m)) return $m[1];
    }
    return null;
};
$it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($new, FilesystemIterator::SKIP_DOTS));
$monthDirs = [];
foreach ($it as $f) {
    $p = $f->getPathname(); $b = basename($p);
    if (in_array($b, $skip, true) || !preg_match('/\.(json|jsonl)$/', $b)) continue;
    $txt = (string)file_get_contents($p);
    file_put_contents($p, $shiftText($txt));
    if (preg_match('/^\d{4}-\d{2}\.jsonl$/', $b)) $monthDirs[dirname($p)] = true;
}
foreach (array_keys($monthDirs) as $md) {   // kelompokkan ulang berkas bulanan
    $files = glob($md . '/*.jsonl'); sort($files);
    $buckets = [];
    foreach ($files as $fp) {
        $fallback = substr(basename($fp), 0, 7);
        foreach (preg_split('/\r?\n/', (string)file_get_contents($fp)) as $ln) {
            if (trim($ln) === '') continue;
            $buckets[$monthOf($ln) ?? $fallback][] = $ln;
        }
        unlink($fp);
    }
    foreach ($buckets as $mon => $lines) file_put_contents($md . '/' . $mon . '.jsonl', implode("\n", $lines) . "\n");
}

// 3) pertahankan rahasia & berkas sistem dari data yang sedang jalan
$cur = $dir . '/data';
$curS = json_decode((string)@file_get_contents($cur . '/settings.json'), true) ?: [];
$newS = json_decode((string)@file_get_contents($new . '/settings.json'), true) ?: [];
foreach (['api', 'whatsapp_api', 'central_server', 'telegram', 'white_label'] as $k) if (isset($curS[$k])) $newS[$k] = $curS[$k];
if (empty($newS['api']['openrouter_api_key'])) { drRm($tmp); $fail('kunci AI tenant demo tidak ditemukan; dibatalkan'); }
file_put_contents($new . '/settings.json', json_encode($newS, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
foreach (['.secret.php', 'vapid-keys.json', 'version.json', 'self-url.txt', 'cap-cache.json', 'license-cache.json', 'sys-once.json',
          'release-notes-cache.json', 'release-notify.json', '.htaccess', '.ht-harden-v1', 'web-migrated.flag', 'server.php'] as $keep) {
    if (file_exists($cur . '/' . $keep)) drCopy($cur . '/' . $keep, $new . '/' . $keep);
}

// 4) tukar folder
$prev = __DIR__ . '/data.prev';   // di luar public_html
drRm($prev);
if (!@rename($cur, $prev)) { drRm($tmp); $fail('gagal memindahkan data lama'); }
if (!@rename($new, $cur)) { @rename($prev, $cur); drRm($tmp); $fail('gagal memasang data baru (data lama dikembalikan)'); }
drRm($tmp);
$ri = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($cur, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::SELF_FIRST);
@chmod($cur, 0755);
foreach ($ri as $f) @chmod($f->getPathname(), $f->isDir() ? 0755 : 0644);
file_put_contents($state, json_encode(['last' => $today, 'at' => date('Y-m-d H:i:s'), 'shift_days' => $days]));
echo date('Y-m-d H:i:s') . " demo direset: acuan $anchor -> $today (geser $days hari)\n";
