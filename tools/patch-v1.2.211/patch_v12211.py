#!/usr/bin/env python3
"""v1.2.211 (list-db): tenant mode MySQL tidak lagi bergantung pada "500 entri log terakhir seluruh tenant".
- Daftar chat WA: entri terakhir per nomor langsung dari dei_log (nomor terbaru, default 500, setelan api.wa_list_max
  100-3000) + chat yang dipegang agent / percakapan aktif, berapa pun umurnya.
- Laporan, statistik kontak, stats_pull, grp_report, statistik ke pusat, Log (logs_query) & ekspor CSV, KB gaps,
  Scan Topik, backfill topik: log ditelusuri per rentang tanggal bertahap (1.000 baris/putaran, hemat memori).
- Cari pesan di semua chat, riwayat telepon, ekspor kontak: query langsung ke dei_log.
- Edit/hapus pesan & echo HP: ubah log per nomor (bukan 500 entri terakhir).
Mode file: perilaku sama. Butuh v1.2.210. Idempoten. Pakai: patch_v12211.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.211: list-db'; NEED = 'v1.2.210: thread-db'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
API = T + '/api/index.php'

# ---------- dashboard: daftar chat per halaman + cari di server ----------
JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'
j = open(JS, encoding='utf-8').read()
if TAG not in j:
    j = rep(j, "    if (waState.lastQ140 !== query) { waState.lastQ140 = query; waState.scrollCur140 = true; }   // v1.2.141: filter-chat-terpilih\n",
               "    if (waState.lastQ140 !== query) { waState.lastQ140 = query; waState.scrollCur140 = true; waState.listLim211 = 500; }   // v1.2.141: filter-chat-terpilih\n"
               "    var _q211 = String(waState.q || '').trim();   // v1.2.211: list-db — daftar per halaman (500), cari nama/nomor di server\n"
               "    query += '&lim=' + (waState.listLim211 || 500) + (_q211 ? '&q=' + encodeURIComponent(_q211) : '');\n", what='js-query')
    j = rep(j, "      waState.convs = res.conversations || [];\n      waState.convCache = waState.convCache || {};",
               "      waState.convs = res.conversations || [];\n      waState.listTotal211 = (typeof res.total === 'number') ? res.total : waState.convs.length;   // v1.2.211: list-db\n      waState.convCache = waState.convCache || {};", what='js-total')
    j = rep(j, "    if (_q125) { $('#waConvList').insertAdjacentHTML('beforeend', waGlobHtml164()); waGlobBind164(); }   // v1.2.164: cari-simpan\n",
               "    var _shown211 = (waState.convs || []).length - (_pin140 ? 1 : 0);   // v1.2.211: list-db — tombol halaman berikutnya\n"
               "    if ((waState.listTotal211 || 0) > _shown211) {\n"
               "      $('#waConvList').insertAdjacentHTML('beforeend', '<div style=\"padding:10px 12px;text-align:center\"><button type=\"button\" class=\"btn ghost sm\" id=\"waMore211\">Tampilkan lebih banyak</button>'\n"
               "        + '<div style=\"font-size:11px;color:var(--muted);margin-top:4px\">Menampilkan ' + _shown211 + ' dari ' + waState.listTotal211 + ' percakapan</div></div>');\n"
               "      $('#waMore211').onclick = function () { this.disabled = true; this.textContent = 'Memuat\\u2026'; waState.listLim211 = (waState.listLim211 || 500) + 500; fetchWaConvs(); };\n"
               "    }\n"
               "    if (_q125) { $('#waConvList').insertAdjacentHTML('beforeend', waGlobHtml164()); waGlobBind164(); }   // v1.2.164: cari-simpan\n", what='js-more')
    j = rep(j, "    if ($('#waSearch')) $('#waSearch').oninput = function () { waState.q = this.value; waGlobFetch164(this.value); renderWaConvs(); };",
               "    if ($('#waSearch')) $('#waSearch').oninput = function () { waState.q = this.value; waGlobFetch164(this.value); renderWaConvs(); clearTimeout(waState.qT211); waState.qT211 = setTimeout(function () { waState.listLim211 = 500; fetchWaConvs(); }, 400); /* v1.2.211: list-db */ };", what='js-cari')
    j = j.replace("// v1.2.211: list-db — daftar per halaman", "// " + TAG + " — daftar per halaman", 1)
    if not NOBAK: shutil.copy2(JS, JS + '.bak-v12211-' + stamp)
    open(JS, 'w', encoding='utf-8').write(j); print('OK', JS)
h = open(HT, encoding='utf-8').read()
if TAG not in h:
    h = rep(h, '<script src="app.js?v=1.2.210"></script>' if 'app.js?v=1.2.210"' in h else '<script src="app.js?v=1.2.209"></script>',
               '<script src="app.js?v=1.2.211"></script><!-- ' + TAG + ' -->', what='html')
    if not NOBAK: shutil.copy2(HT, HT + '.bak-v12211-' + stamp)
    open(HT, 'w', encoding='utf-8').write(h); print('OK', HT)

s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API); sys.exit(0)
assert NEED in s, 'butuh v1.2.210 dulu'

s = rep(s, "define('DEI_VERSION', 'v1.2.210');   // v1.2.210:",
        "define('DEI_VERSION', 'v1.2.211');   // v1.2.211: list-db — daftar chat, laporan, Log & pencarian (mode MySQL) membaca dei_log langsung, tidak terpotong 500 entri terakhir tenant; v1.2.210:", what='versi')

# ---------- pustaka ----------
LIB = r'''
/* ---- v1.2.211: list-db — pembaca dei_log tanpa jendela 500 entri (mode mysql) ---- */
// Telusuri log per rentang tanggal (Y-m-d, '' = tanpa batas), terbaru dulu, bertahap 1.000 baris (hemat memori).
// Mode file: logReadAll() apa adanya — pemanggil tetap menyaring tanggal. $max > 0 = berhenti setelah sekian entri.
function logIter($fromDate = '', $toDate = '', $max = 0) {
    if (!deiStorageMysql()) {
        $n = 0;
        foreach (logReadAll() as $e) { yield $e; if ($max > 0 && ++$n >= $max) return; }
        return;
    }
    $db = deiDb(); $lo = 0;
    if ($fromDate !== '') {
        $st = $db->prepare('SELECT MIN(id) FROM dei_log WHERE ts >= ?'); $st->execute([$fromDate . ' 00:00:00']);
        $lo = (int)$st->fetchColumn(); if ($lo <= 0) return;
    }
    if ($toDate !== '') { $st = $db->prepare('SELECT MAX(id) FROM dei_log WHERE ts <= ?'); $st->execute([$toDate . ' 23:59:59']); $hi = (int)$st->fetchColumn(); }
    else $hi = (int)$db->query('SELECT MAX(id) FROM dei_log')->fetchColumn();
    if ($hi <= 0 || $hi < $lo) return;
    $st = $db->prepare('SELECT id, body FROM dei_log WHERE id <= ? AND id >= ? ORDER BY id DESC LIMIT 1000');
    $n = 0; $cur = $hi;
    while ($cur >= $lo) {
        $st->execute([$cur, $lo]); $rows = $st->fetchAll(PDO::FETCH_NUM);
        if (!$rows) return;
        foreach ($rows as $r) {
            $e = json_decode($r[1], true);
            if (!is_array($e)) continue;
            yield $e;
            if ($max > 0 && ++$n >= $max) return;
        }
        $cur = (int)$rows[count($rows) - 1][0] - 1;
    }
}
// Tanggal entri terlama & jumlah entri log (laporan pusat / Log).
function logStatsInfo() {
    if (!deiStorageMysql()) {
        $l = logReadAll(); $o = '';
        foreach ($l as $e) { $t = substr((string)($e['ts'] ?? ''), 0, 10); if ($t !== '' && ($o === '' || $t < $o)) $o = $t; }
        return ['oldest' => $o, 'entries' => count($l)];
    }
    $r = deiDb()->query('SELECT MIN(ts), COUNT(*) FROM dei_log')->fetch(PDO::FETCH_NUM);
    return ['oldest' => ($r && $r[0]) ? substr((string)$r[0], 0, 10) : '', 'entries' => (int)($r[1] ?? 0)];
}
// Bahan daftar chat WA (mysql): entri TERAKHIR tiap nomor — $max nomor paling baru aktif + nomor $extra
// (dipegang agent / percakapan aktif) berapa pun umurnya. Terbaru dulu.
function logLastPerNum($max, $extra = []) {
    $db = deiDb(); $mids = [];
    foreach ($db->query("SELECT num, MAX(id) AS mid FROM dei_log WHERE num <> '' GROUP BY num ORDER BY mid DESC LIMIT " . (int)$max)->fetchAll(PDO::FETCH_NUM) as $r) $mids[(string)$r[0]] = (int)$r[1];
    $ex = [];
    foreach ((array)$extra as $x) { $x = substr(preg_replace('/\D/', '', (string)$x), 0, 32); if ($x !== '' && !isset($mids[$x])) $ex[] = $x; }
    foreach (array_chunk(array_values(array_unique($ex)), 500) as $ch) {
        $st = $db->prepare('SELECT num, MAX(id) FROM dei_log WHERE num IN (' . implode(',', array_fill(0, count($ch), '?')) . ') GROUP BY num');
        $st->execute($ch);
        foreach ($st->fetchAll(PDO::FETCH_NUM) as $r) $mids[(string)$r[0]] = (int)$r[1];
    }
    $out = [];
    foreach (array_chunk(array_values($mids), 500) as $ch) {
        foreach ($db->query('SELECT id, body FROM dei_log WHERE id IN (' . implode(',', array_map('intval', $ch)) . ')')->fetchAll(PDO::FETCH_NUM) as $r) {
            $e = json_decode($r[1], true); if (is_array($e)) $out[(int)$r[0]] = $e;
        }
    }
    krsort($out);
    return array_values($out);
}
function deiListMax211() { return max(100, min(3000, (int)(getSettings()['api']['wa_list_max'] ?? 500))); }
// Entri WhatsApp yang body JSON-nya memuat potongan $raw (persis seperti tersimpan), terbaru dulu, + _dei_id.
function logLikeDb($raw, $max) {
    $st = deiDb()->prepare("SELECT id, body FROM dei_log WHERE num <> '' AND body LIKE ? ORDER BY id DESC LIMIT " . (int)$max);
    $st->execute(['%' . str_replace(['\\', '%', '_'], ['\\\\', '\\%', '\\_'], (string)$raw) . '%']);
    $out = [];
    foreach ($st->fetchAll(PDO::FETCH_NUM) as $r) { $e = json_decode($r[1], true); if (is_array($e)) { $e['_dei_id'] = (int)$r[0]; $out[] = $e; } }
    return $out;
}
// Posisi entri (id) di thread nomornya: 0 = paling baru (sama dengan urutan wa_thread).
function logPosDb($num, $id) {
    $st = deiDb()->prepare('SELECT COUNT(*) FROM dei_log WHERE num = ? AND id > ?');
    $st->execute([substr(preg_replace('/\D/', '', (string)$num), 0, 32), (int)$id]);
    return (int)$st->fetchColumn();
}
// Aktivitas terakhir per nomor WA (mysql), bentuk entri log ringkas.
function logNumLastTs211($cut = '') {
    $st = deiDb()->prepare("SELECT num, MAX(ts) FROM dei_log WHERE num <> ''" . ($cut !== '' ? ' AND ts >= ?' : '') . ' GROUP BY num');
    $st->execute($cut !== '' ? [$cut] : []);
    $out = [];
    foreach ($st->fetchAll(PDO::FETCH_NUM) as $r) if ($r[1] !== null) $out[] = ['channel' => 'whatsapp', 'ip' => (string)$r[0], 'ts' => (string)$r[1]];
    return $out;
}
function deiLogName211($e, $c) {
    if (!is_array($c) || !$c || ($e['channel'] ?? 'web') !== 'whatsapp') return $e;
    $k = (string)($e['ip'] ?? '');
    if ($k !== '' && isset($c[$k]) && is_array($c[$k])) {
        $n = trim((string)($c[$k]['name_manual'] ?? '')) ?: trim((string)($c[$k]['name_wa'] ?? ''));
        if ($n !== '') $e['_name'] = $n;
    }
    return $e;
}
function logDbMutate($fn, $num = '') {'''
s = rep(s, "\nfunction logDbMutate($fn) {", LIB, what='pustaka')
s = rep(s, "        foreach ($db->query('SELECT id, body FROM dei_log ORDER BY id DESC LIMIT ' . (int)logWindow())->fetchAll() as $r) {",
"""        if ($num !== '') { $stN = $db->prepare('SELECT id, body FROM dei_log WHERE num = ? ORDER BY id DESC LIMIT 2000'); $stN->execute([substr(preg_replace('/\\D/', '', (string)$num), 0, 32)]); $rows211 = $stN->fetchAll(); }   // v1.2.211: list-db — ubah log satu nomor
        else $rows211 = $db->query('SELECT id, body FROM dei_log ORDER BY id DESC LIMIT ' . (int)logWindow())->fetchAll();
        foreach ($rows211 as $r) {""", what='logDbMutate-num')
s = rep(s, "function logMutate($fn, $limit = null) {\n    if (deiStorageMysql()) return logDbMutate($fn);",
           "function logMutate($fn, $limit = null, $num = '') {   // v1.2.211: $num (mysql) = ubah log nomor itu saja\n    if (deiStorageMysql()) return logDbMutate($fn, $num);", what='logMutate')
s = rep(s, "            return false;\n        });\n        try {   // konteks AI ikut",
           "            return false;\n        }, null, $num);   // v1.2.211: list-db\n        try {   // konteks AI ikut", what='edit-hapus')
s = rep(s, "                    }, $logLimit);\n                    if ($dup && !empty($emedia['file']))",
           "                    }, $logLimit, $eto);   // v1.2.211: list-db\n                    if ($dup && !empty($emedia['file']))", what='echo')

# ---------- ringkasan entri terakhir per nomor (dei_num_last) ----------
NUMLAST = r'''
/* ---- v1.2.211: list-db — dei_num_last: entri TERAKHIR tiap nomor WA (ringkas), dipelihara saat log ditulis.
 * Dipakai daftar chat: hitungan "belum dibalas" dll. dari SEMUA percakapan tanpa memindai dei_log. ---- */
function numLastLite($e) {
    $l = ['ts' => (string)($e['ts'] ?? ''), 'q' => mb_substr((string)($e['q'] ?? ''), 0, 300), 'a' => mb_substr((string)($e['a'] ?? ''), 0, 150),
          'ip' => (string)($e['ip'] ?? ''), 'channel' => 'whatsapp', 'dir' => (string)($e['dir'] ?? '')];
    if (!empty($e['g_from'])) $l['g_from'] = (string)$e['g_from'];
    if (!empty($e['awaiting'])) $l['awaiting'] = true;
    if (!empty($e['cap_reached']) || !empty($e['suspended']) || !empty($e['ai_error'])) $l['ai_error'] = true;
    return $l;
}
function numLastTableOk() {
    static $ok = null;
    if ($ok !== null) return $ok;
    try {
        deiDb()->exec("CREATE TABLE IF NOT EXISTS dei_num_last (num VARCHAR(32) NOT NULL PRIMARY KEY, last_id BIGINT UNSIGNED NOT NULL, ts DATETIME NULL, lite TEXT NOT NULL, KEY last_id (last_id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
        $ok = true;
    } catch (\Throwable $e) { error_log('dei_num_last: ' . $e->getMessage()); $ok = false; }
    return $ok;
}
// Catat entri $id untuk nomor $num bila lebih baru dari yang tersimpan (urutan kolom UPDATE disengaja: ts & lite dibandingkan dulu).
function numLastPut($num, $id, $e) {
    if ($num === '' || $id <= 0 || !numLastTableOk()) return;
    $ts = (string)($e['ts'] ?? '');
    $st = deiDb()->prepare('INSERT INTO dei_num_last (num, last_id, ts, lite) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE '
        . 'ts = IF(VALUES(last_id) >= last_id, VALUES(ts), ts), lite = IF(VALUES(last_id) >= last_id, VALUES(lite), lite), last_id = GREATEST(last_id, VALUES(last_id))');
    $st->execute([$num, (int)$id, preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/', $ts) ? $ts : null,
                  json_encode(numLastLite($e), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_INVALID_UTF8_SUBSTITUTE)]);
}
// Hitung ulang dari dei_log (setelah entri diubah/dihapus).
function numLastRefresh($nums) {
    if (!$nums || !numLastTableOk()) return;
    $db = deiDb();
    $sel = $db->prepare('SELECT id, body FROM dei_log WHERE num = ? ORDER BY id DESC LIMIT 1');
    $del = $db->prepare('DELETE FROM dei_num_last WHERE num = ?');
    foreach (array_unique(array_map('strval', $nums)) as $n) {
        if ($n === '') continue;
        $sel->execute([$n]); $r = $sel->fetch(PDO::FETCH_NUM);
        $del->execute([$n]);
        if ($r) { $e = json_decode($r[1], true); if (is_array($e)) numLastPut($n, (int)$r[0], $e); }
    }
}
// Isi tabel dari dei_log sekali (lalu dipelihara numLastPut). false = belum siap (sedang dibangun proses lain / gagal).
function numLastEnsureBuilt() {
    if (!numLastTableOk()) return false;
    $f = DATA_DIR . '/num-last.json';
    $stt = readJson($f, []);
    if (!empty($stt['built'])) return true;
    $db = deiDb();
    if (!(int)$db->query("SELECT GET_LOCK('dei_num_last_build', 0)")->fetchColumn()) return false;
    try {
        $stt = readJson($f, []);
        if (!empty($stt['built'])) return true;
        @set_time_limit(300);
        $mids = $db->query("SELECT MAX(id) FROM dei_log WHERE num <> '' GROUP BY num")->fetchAll(PDO::FETCH_COLUMN);
        foreach (array_chunk($mids, 500) as $ch) {
            foreach ($db->query('SELECT id, num, body FROM dei_log WHERE id IN (' . implode(',', array_map('intval', $ch)) . ')')->fetchAll(PDO::FETCH_NUM) as $r) {
                $e = json_decode($r[2], true); if (is_array($e)) numLastPut((string)$r[1], (int)$r[0], $e);
            }
        }
        writeJson($f, ['built' => date('Y-m-d H:i:s'), 'nums' => count($mids)]);
        return true;
    } catch (\Throwable $e) { error_log('dei_num_last build: ' . $e->getMessage()); return false; }
    finally { $db->query("SELECT RELEASE_LOCK('dei_num_last_build')"); }
}
// Sumber daftar chat (mysql): entri terakhir SEMUA nomor; cadangan bila tabel belum siap: 3.000 nomor terbaru.
function listSrc211() {
    try {
        if (numLastEnsureBuilt()) {
            $out = [];
            foreach (deiDb()->query('SELECT lite FROM dei_num_last ORDER BY last_id DESC')->fetchAll(PDO::FETCH_COLUMN) as $b) { $e = json_decode($b, true); if (is_array($e)) $out[] = $e; }
            return $out;
        }
    } catch (\Throwable $e) { error_log('dei_num_last baca: ' . $e->getMessage()); }
    return logLastPerNum(3000, array_merge(array_keys((array)waClaimGetAll()), array_keys((array)convStateReadAll())));
}
// waGetMode tanpa membaca berkas per nomor (claim sudah dicek pemanggil).
function waGetModeFast211($num, $pre) {
    if (!empty($pre['manual']) || waIsGroup($num)) return 'human';
    $k = waNormNum($num);
    return (isset($pre['m'][$k]['mode']) && $pre['m'][$k]['mode'] === 'human') ? 'human' : 'bot';
}
function deiListMax211() {'''
s = rep(s, "\nfunction deiListMax211() {", NUMLAST, what='numlast-lib')
s = rep(s, "                  logRowNum($e), substr((string)($e['channel'] ?? ''), 0, 16), logEncode($e)]);\n}",
           "                  logRowNum($e), substr((string)($e['channel'] ?? ''), 0, 16), logEncode($e)]);\n"
           "    try { $n211 = logRowNum($e); if ($n211 !== '') numLastPut($n211, (int)deiDb()->lastInsertId(), $e); } catch (\\Throwable $x211) { error_log('dei_num_last: ' . $x211->getMessage()); }   // v1.2.211: list-db\n}", what='insert-hook')
s = rep(s, "            $keep = []; $new = [];\n            $upd = $db->prepare('UPDATE dei_log SET ts = ?, num = ?, channel = ?, body = ? WHERE id = ?');",
           "            $keep = []; $new = []; $chg211 = [];   // v1.2.211: list-db — nomor yang entrinya berubah\n            $upd = $db->prepare('UPDATE dei_log SET ts = ?, num = ?, channel = ?, body = ? WHERE id = ?');", what='mutate-1')
s = rep(s, "                                       logRowNum($e), substr((string)($e['channel'] ?? ''), 0, 16), $b, $id]);\n",
           "                                       logRowNum($e), substr((string)($e['channel'] ?? ''), 0, 16), $b, $id]);\n"
           "                        $chg211[] = logRowNum($e); $o211 = json_decode($orig[$id], true); if (is_array($o211)) $chg211[] = logRowNum($o211);\n", what='mutate-2')
s = rep(s, "            if ($gone) $db->exec('DELETE FROM dei_log WHERE id IN (' . implode(',', array_map('intval', array_keys($gone))) . ')');\n",
           "            if ($gone) $db->exec('DELETE FROM dei_log WHERE id IN (' . implode(',', array_map('intval', array_keys($gone))) . ')');\n"
           "            foreach ($gone as $gb211) { $ge211 = json_decode($gb211, true); if (is_array($ge211)) $chg211[] = logRowNum($ge211); }\n"
           "            try { numLastRefresh(array_values(array_filter($chg211))); } catch (\\Throwable $x211) { error_log('dei_num_last: ' . $x211->getMessage()); }   // v1.2.211\n", what='mutate-3')

# ---------- daftar chat ----------
s = rep(s, "        // Read chat log untuk dapatkan list nomor + last message\n        $logs = logReadAll();",
"""        // Read chat log untuk dapatkan list nomor + last message
        // v1.2.211: list-db — mysql: entri terakhir SEMUA nomor (dei_num_last); hitungan dari semua, daftar per halaman
        $logs = deiStorageMysql() ? listSrc211() : logReadAll();""", what='daftar-chat')
s = rep(s, "        $allContacts = waGetContacts();   // v1.2.19: 1 file read untuk semua nomor\n",
           "        $allContacts = waGetContacts();   // v1.2.19: 1 file read untuk semua nomor\n"
           "        $modes211 = ['manual' => $isManual, 'm' => (array)readJson(WA_MODES_FILE, [])];   // v1.2.211: list-db — tanpa baca berkas per nomor\n", what='modes-pre')
s = rep(s, "            $mode = $claim ? 'human' : waGetMode($num);  // fallback ke waGetMode kalau tidak claimed",
           "            $mode = $claim ? 'human' : waGetModeFast211($num, $modes211);  // fallback ke waGetMode kalau tidak claimed (v1.2.211: tanpa baca berkas per nomor)", what='mode-fast')
s = rep(s, """        // Sort by last_ts desc
        usort($result, function ($a, $b) {
            return strcmp($b['last_ts'] ?? '', $a['last_ts'] ?? '');
        });
""", """        // Sort by last_ts desc
        usort($result, function ($a, $b) {
            return strcmp($b['last_ts'] ?? '', $a['last_ts'] ?? '');
        });
        // v1.2.211: list-db — hitungan di atas dari SEMUA percakapan; daftar dikirim per halaman (lim) + cari di server (q)
        $q211 = mb_strtolower(trim((string)($_GET['q'] ?? '')));
        if ($q211 !== '') {
            $qn211 = preg_replace('/\\D/', '', $q211); if ($qn211 !== '' && $qn211[0] === '0') $qn211 = '62' . substr($qn211, 1);
            $result = array_values(array_filter($result, function ($c) use ($q211, $qn211) {
                $hay = mb_strtolower((string)($c['name'] ?? '') . ' ' . (string)($c['last_q'] ?? ''));
                return mb_strpos($hay, $q211) !== false || (strlen($qn211) >= 3 && strpos((string)$c['number'], $qn211) !== false);
            }));
        }
        $total211 = count($result);
        $lim211 = (int)($_GET['lim'] ?? 0); $lim211 = $lim211 > 0 ? max(50, min(10000, $lim211)) : 500;
        $result = array_slice($result, 0, $lim211);
""", what='halaman')
s = rep(s, "            'conversations' => $result,\n            'counts' => $counts,",
           "            'conversations' => $result,\n            'total' => $total211, 'lim' => $lim211,   // v1.2.211: list-db\n            'counts' => $counts,", what='respons')

# ---------- laporan ----------
s = rep(s, "        $logs = logReadAll();\n        $kb = readJson(KB_FILE, []);\n        $today = date('Y-m-d');",
           "        $logs = deiStorageMysql() ? null : logReadAll();   // v1.2.211: list-db — mysql: telusuri rentang tanggal\n        $kb = readJson(KB_FILE, []);\n        $today = date('Y-m-d');", what='report-1')
s = rep(s, "        $chFilter = $_GET['channel'] ?? 'all';   // all | web | whatsapp\n",
           "        $chFilter = $_GET['channel'] ?? 'all';   // all | web | whatsapp\n        if ($logs === null && $from === '') $from = wibDate('Y-m-d', time() - 364 * 86400);   // v1.2.211: tanpa tanggal = 1 tahun terakhir\n", what='report-2')
s = rep(s, "        foreach ($logs as $l) {\n            if (in_array(($l['dir'] ?? ''), ['manual', 'closing'], true)) continue;          // skip admin manual replies",
           "        foreach (($logs ?? logIter($from, $to)) as $l) {   // v1.2.211\n            if (in_array(($l['dir'] ?? ''), ['manual', 'closing'], true)) continue;          // skip admin manual replies", what='report-3')
s = rep(s, "    foreach ((array)$logs as $e) {\n        if (!is_array($e) || ($e['channel'] ?? '') !== 'whatsapp') continue;",
           "    foreach (($logs === null ? logIter(wibDate('Y-m-d', $minTs), '') : (array)$logs) as $e) {   // v1.2.211: null = telusuri sejak awal periode\n        if (!is_array($e) || ($e['channel'] ?? '') !== 'whatsapp') continue;", what='contact-stats')

# stats_pull
s = rep(s, "        $logs = logReadAll();\n        if (!is_array($logs)) $logs = [];\n\n        $daily = [];   // tanggal => pencacah",
           "        $logs = deiStorageMysql() ? null : logReadAll();   // v1.2.211: list-db\n        if ($logs !== null && !is_array($logs)) $logs = [];\n\n        $daily = [];   // tanggal => pencacah", what='stats_pull-1')
s = rep(s, "        foreach ($logs as $l) {\n            if (!is_array($l)) continue;\n            // balasan manual agent bukan percakapan bot, jangan dihitung",
           "        foreach (($logs ?? logIter($from, $to)) as $l) {   // v1.2.211\n            if (!is_array($l)) continue;\n            // balasan manual agent bukan percakapan bot, jangan dihitung", what='stats_pull-2')
s = rep(s, """        $oldest = '';
        foreach ($logs as $l) {
            if (!is_array($l)) continue;
            $t = substr((string)($l['ts'] ?? ''), 0, 10);
            if ($t === '') continue;
            if ($oldest === '' || $t < $oldest) $oldest = $t;
        }
""", "        $lsi211 = logStatsInfo(); $oldest = $lsi211['oldest'];   // v1.2.211: list-db\n", what='stats_pull-3')
s = rep(s, "                'entries'   => count($logs),", "                'entries'   => $lsi211['entries'],", what='stats_pull-4')

# statistik ke pusat
s = rep(s, "function deiCollectStats() {\n    $logs = logReadAll();\n    if (!is_array($logs)) $logs = [];",
           "function deiCollectStats() {\n    $my211 = deiStorageMysql();   // v1.2.211: list-db — mysql: telusuri hari ini saja; total = jumlah entri log\n    $logs = $my211 ? logIter(wibToday(), wibToday()) : logReadAll();\n    if (!$my211 && !is_array($logs)) $logs = [];", what='collect-1')
s = rep(s, "    $usage = readJson(DATA_DIR . '/usage.json', []);\n    $u = array_merge(['calls' => 0",
           "    if ($my211) { try { $chats_total = logStatsInfo()['entries']; } catch (\\Throwable $e) {} }   // v1.2.211\n    $usage = readJson(DATA_DIR . '/usage.json', []);\n    $u = array_merge(['calls' => 0", what='collect-2')

# grp_report
s = rep(s, "        foreach ((array)logReadAll() as $l) {\n            if (!is_array($l) || in_array(($l['dir'] ?? ''), ['manual', 'closing'], true)) continue;\n            $d = substr((string)($l['ts'] ?? ''), 0, 10);\n            if (!isset($daily[$d])) continue;",
           "        foreach (logIter($fromD, $toD) as $l) {   // v1.2.211: list-db\n            if (!is_array($l) || in_array(($l['dir'] ?? ''), ['manual', 'closing'], true)) continue;\n            $d = substr((string)($l['ts'] ?? ''), 0, 10);\n            if (!isset($daily[$d])) continue;", what='grp_report')

# logs_query (mysql: satu-dua putaran, simpan baris halaman saja)
LQ = r'''        $page = max(1, (int)($_GET['page'] ?? 1));
        if (deiStorageMysql()) {   // v1.2.211: list-db — telusuri bertahap (maks 200.000 entri), simpan baris halaman ini saja
            $cN = waGetContacts();
            $run = function ($page) use ($f, $per, $cN) {
                $fac = ['channel' => [], 'source' => [], 'medium' => [], 'campaign' => [], 'status' => []];
                $total = 0; $keep = []; $lo = ($page - 1) * $per;
                foreach (logIter($f['from'], $f['to'], 200000) as $e) {
                    $e = deiLogName211($e, $cN);
                    if (deiLogMatch($e, $f)) { if ($total >= $lo && $total < $lo + $per) $keep[] = $e; $total++; }
                    foreach ($fac as $dim => $_) {
                        if (!deiLogMatch($e, $f, $dim)) continue;
                        $v = $dim === 'channel' ? ($e['channel'] ?? 'web') : ($dim === 'status' ? deiLogStatus($e) : deiLogDim($e, $dim));
                        $fac[$dim][$v] = ($fac[$dim][$v] ?? 0) + 1;
                    }
                }
                return [$fac, $total, $keep];
            };
            list($fac, $total, $keep) = $run($page);
            $pages = max(1, (int)ceil($total / $per));
            if ($page > $pages) { $page = $pages; list($fac, $total, $keep) = $run($page); }
            $facets = [];
            foreach ($fac as $dim => $m) {
                arsort($m);
                $facets[$dim] = [];
                foreach (array_slice($m, 0, 200, true) as $v => $n) $facets[$dim][] = ['value' => (string)$v, 'count' => $n];
            }
            $out = [];
            foreach ($keep as $e) {
                $out[] = [
                    'ts' => (string)($e['ts'] ?? ''), 'channel' => (string)($e['channel'] ?? 'web'), 'status' => deiLogStatus($e),
                    'q' => mb_substr((string)($e['q'] ?? ''), 0, 4000), 'a' => mb_substr((string)($e['a'] ?? ''), 0, 6000),
                    'call_txt' => wcLabel($e), 'who' => (string)($e['ip'] ?? ''), 'name' => (string)($e['_name'] ?? ''),
                    'source' => deiLogDim($e, 'source'), 'medium' => deiLogDim($e, 'medium'), 'campaign' => deiLogDim($e, 'campaign'),
                    'page' => (string)($e['page'] ?? ''), 'referrer' => (string)($e['referrer'] ?? ''),
                ];
            }
            $lsi = logStatsInfo();
            jsonOut(['ok' => true, 'rows' => $out, 'total' => $total, 'page' => $page, 'pages' => $pages, 'per' => $per,
                     'facets' => $facets, 'filters' => $f, 'oldest' => $lsi['oldest'], 'all_total' => $lsi['entries']]);
        }
        $logs = deiLogWithNames(logReadAll());
        usort($logs, function ($a, $b) { return strcmp((string)($b['ts'] ?? ''), (string)($a['ts'] ?? '')); });
'''
s = rep(s, "        $page = max(1, (int)($_GET['page'] ?? 1));\n        $logs = deiLogWithNames(logReadAll());\n        usort($logs, function ($a, $b) { return strcmp((string)($b['ts'] ?? ''), (string)($a['ts'] ?? '')); });\n", LQ, what='logs_query')

# export_logs (mysql: dialirkan)
s = rep(s, """        $logs = deiLogWithNames(logReadAll());

        $rows = [];
        foreach ($logs as $l) {
            if (deiLogMatch($l, $f)) $rows[] = $l;
        }
""", """        if (deiStorageMysql()) {   // v1.2.211: list-db — baris dialirkan langsung ke CSV
            $cN211 = waGetContacts();
            $rows = (function () use ($from, $to, $f, $cN211) { foreach (logIter($from, $to) as $l) { $l = deiLogName211($l, $cN211); if (deiLogMatch($l, $f)) yield $l; } })();
        } else {
            $rows = [];
            foreach (deiLogWithNames(logReadAll()) as $l) {
                if (deiLogMatch($l, $f)) $rows[] = $l;
            }
        }
""", what='export_logs')

# KB gaps, topik
s = rep(s, "        $dipindai = 0;\n        foreach (logReadAll() as $e) {",
           "        $dipindai = 0;\n        foreach (logIter(deiStorageMysql() ? wibDate('Y-m-d', time() - 29 * 86400) : '', '', deiStorageMysql() ? 30000 : 0) as $e) {   // v1.2.211: mysql 30 hari terakhir", what='kb_gaps')
s = rep(s, "    $logs = logReadAll();\n    $oldest = '';\n    $units = [];\n    foreach ($logs as $e) {\n        $ts = (string)($e['ts'] ?? '');",
           "    $logs = logIter(deiStorageMysql() ? $from : '', '', deiStorageMysql() ? 150000 : 0);   // v1.2.211: list-db\n    $oldest = ''; $cnt211 = 0;\n    $units = [];\n    foreach ($logs as $e) {\n        $cnt211++;\n        $ts = (string)($e['ts'] ?? '');", what='topik-1')
s = rep(s, "    return [$out, ['from' => $from, 'to' => $to, 'oldest' => $oldest, 'log_entries' => count($logs)]];",
           "    if (deiStorageMysql()) { try { $oldest = logStatsInfo()['oldest']; } catch (\\Throwable $e) {} }   // v1.2.211\n    return [$out, ['from' => $from, 'to' => $to, 'oldest' => $oldest, 'log_entries' => $cnt211]];", what='topik-2')
s = rep(s, "    foreach (logReadAll() as $e) {\n        if (($e['channel'] ?? '') !== 'whatsapp') continue;\n        $n = waNormNum($e['ip'] ?? ''); $ts = (string)($e['ts'] ?? '');\n        if ($n !== '' && !waIsGroup($n)",
           "    foreach ((deiStorageMysql() ? logNumLastTs211($cut) : logReadAll()) as $e) {   // v1.2.211: list-db\n        if (($e['channel'] ?? '') !== 'whatsapp') continue;\n        $n = waNormNum($e['ip'] ?? ''); $ts = (string)($e['ts'] ?? '');\n        if ($n !== '' && !waIsGroup($n)", what='tp-backfill')

# cari pesan semua chat
s = rep(s, "    $logs = $num !== '' ? logReadForNum($num, 5000) : logReadAll();   // v1.2.210: thread-db",
           "    $logs = $num !== '' ? logReadForNum($num, 5000) : ((deiStorageMysql() && $q !== '') ? logLikeDb(substr(json_encode($q, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), 1, -1), 3000) : logReadAll());   // v1.2.210: thread-db; v1.2.211: list-db — semua chat: saring di database", what='cari-1')
s = rep(s, "            $h = ['num' => $n, 'pos' => $p, 'ts' => $ets,",
           "            $h = ['num' => $n, 'pos' => isset($e['_dei_id']) ? logPosDb($n, (int)$e['_dei_id']) : $p, 'ts' => $ets,   // v1.2.211", what='cari-2')

# telepon, ekspor kontak
s = rep(s, "        foreach (logReadAll() as $e) {\n            if ((string)($e['dir'] ?? '') !== 'call' || ($e['channel'] ?? '') !== 'whatsapp') continue;",
           "        foreach ((deiStorageMysql() ? logLikeDb('\"dir\":\"call\"', 300) : logReadAll()) as $e) {   // v1.2.211: list-db\n            if ((string)($e['dir'] ?? '') !== 'call' || ($e['channel'] ?? '') !== 'whatsapp') continue;", what='wa_calls')
s = rep(s, "        $seen = [];\n        foreach (logReadAll() as $e) {\n            if (($e['channel'] ?? '') !== 'whatsapp') continue;\n            $n = preg_replace('/\\D/', '', (string)($e['ip'] ?? ''));",
           "        $seen = [];\n        if (deiStorageMysql()) foreach (deiDb()->query(\"SELECT num, MAX(ts), MAX(id) AS mid FROM dei_log WHERE num <> '' GROUP BY num ORDER BY mid DESC\")->fetchAll(PDO::FETCH_NUM) as $r) $seen[(string)$r[0]] = (string)$r[1];   // v1.2.211: list-db\n        foreach ((deiStorageMysql() ? [] : logReadAll()) as $e) {\n            if (($e['channel'] ?? '') !== 'whatsapp') continue;\n            $n = preg_replace('/\\D/', '', (string)($e['ip'] ?? ''));", what='export_contacts')

if not NOBAK: shutil.copy2(API, API + '.bak-v12211-' + stamp)
open(API, 'w', encoding='utf-8').write(s); print('OK', API)
