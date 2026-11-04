#!/usr/bin/env python3
"""v1.2.139 topik-riwayat: Filter Topik membaca riwayat impor WAHA (wa-import) + log; scan chat lama
memakai daftar Percakapan WA (log + riwayat) dengan periode 7/30/90 hari/Semua, perkiraan biaya,
batas maks 3.000 chat & 50% kuota; 20 chat per menit; saat pertama diaktifkan scan 30 hari. Idempoten.
Pakai: patch_v12139_topik_riwayat.py [~/Herd/dei-tenant]"""
import os, sys, shutil, time, re
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.139: topik-riwayat'; STAMP = time.strftime('%Y%m%d-%H%M%S'); done = set()
def rd(fp): return open(fp, encoding='utf-8').read()
def wr(fp, s):
    if fp not in done: shutil.copy2(fp, fp + '.bak-v12139-' + STAMP); done.add(fp)
    open(fp, 'w', encoding='utf-8').write(s)
def rep(fp, a, b):
    s = rd(fp)
    if b in s: return
    assert s.count(a) == 1, (fp, s.count(a), a[:100])
    wr(fp, s.replace(a, b))
def rep_between(fp, start, end, new, marker):
    s = rd(fp)
    if marker in s: return
    i = s.index(start); j = s.index(end, i)
    assert s.count(start) == 1
    wr(fp, s[:i] + new + s[j:])
API = T + '/api/index.php'; A = T + '/dashboard/chatbot-ai/app.js'; H = T + '/dashboard/chatbot-ai/index.html'

rep(API, "define('DEI_VERSION', 'v1.2.138');   // v1.2.138: filter-topik", "define('DEI_VERSION', 'v1.2.139');   // " + TAG)
rep(API, "if (!defined('TP_PER_TICK')) define('TP_PER_TICK', 10);         // maks klasifikasi per cron tick\n",
         "if (!defined('TP_PER_TICK')) define('TP_PER_TICK', 20);         // maks klasifikasi per cron tick (" + TAG + ": 10 -> 20)\n"
         "if (!defined('TP_BACKFILL_MAX')) define('TP_BACKFILL_MAX', 3000);   // " + TAG + ": maks chat per scan chat lama (±Rp10rb)\n"
         "if (!defined('TP_COST_IDR')) define('TP_COST_IDR', 3.1);         // perkiraan biaya per klasifikasi (Haiku 5.5 + fee OpenRouter)\n")

rep_between(API, "// 20 bubble terakhir satu nomor (lama -> baru)", "// Prompt klasifikasi", r"""// 20 bubble terakhir satu nomor (lama -> baru): [['r' => 'p'|'k', 't' => teks]]
// """ + TAG + r""": gabungan log dashboard + riwayat impor WAHA (wa-import, selalu lebih lama dari pesan live pertama)
function tpBubbles($num) {
    $all = []; $li = 1000000;
    foreach (logReadByNumber($num, TP_BUBBLES) as $e) {   // terbaru dulu
        $ts = (string)($e['ts'] ?? ''); $li -= 2;
        $a = trim((string)($e['a'] ?? ''));
        $q = trim((string)($e['q'] ?? ''));
        if ($q === '' && is_array($e['media'] ?? null)) $q = '[' . (string)($e['media']['type'] ?? 'media') . ']' . (isset($e['media']['caption']) ? ' ' . (string)$e['media']['caption'] : '');
        if ($q !== '') $all[] = [$ts, $li, 'p', mb_substr($q, 0, 300)];
        if ($a !== '' && ($e['dir'] ?? '') !== 'call') $all[] = [$ts, $li + 1, 'k', mb_substr($a, 0, 300)];
    }
    if (count($all) < TP_BUBBLES && function_exists('wiLoad')) {
        $d = null; try { $d = wiLoad($num); } catch (\Throwable $e) {}
        $i = 0;
        if ($d) foreach (array_slice($d['msgs'], -(TP_BUBBLES * 2)) as $m) {
            $t = trim((string)($m['t'] ?? ''));
            if ($t === '') continue;
            $all[] = [(string)($m['ts'] ?? ''), $i++, (($m['d'] ?? '') === 'in') ? 'p' : 'k', mb_substr($t, 0, 300)];
        }
    }
    usort($all, function ($x, $y) { return strcmp($x[0], $y[0]) ?: ($x[1] <=> $y[1]); });
    $out = [];
    foreach (array_slice($all, -TP_BUBBLES) as $x) $out[] = ['r' => $x[2], 't' => $x[3]];
    return $out;
}
""", "// " + TAG + ": gabungan log dashboard + riwayat impor")

rep(API, "    if (!$items) return [[], null];\n    if ($s === null) $s = getSettings();\n",
         "    if (!$items) return [[], null];\n    if ($s === null) $s = getSettings();\n"
         "    // " + TAG + ": pusat menerima maks 10 per permintaan -> pecah\n"
         "    if (count($items) > 10 && !empty($s['central_server']['url'])) {\n"
         "        $out = []; $quota = null;\n"
         "        foreach (array_chunk($items, 10, true) as $part) { list($o, $q2) = tpClassify($part, $s); $out += $o; if ($q2) $quota = $q2; }\n"
         "        return [$out, $quota];\n    }\n")

rep_between(API, "function tpBackfillState() {", "/* cron_tick: klasifikasikan", r"""function tpBackfillState() {
    $b = readJson(TP_BACKFILL_FILE, []);
    if (!is_array($b) || empty($b['started_at'])) return null;
    return ['started_at' => (int)$b['started_at'], 'by' => (string)($b['by'] ?? ''), 'total' => (int)($b['total'] ?? 0),
            'left' => count((array)($b['queue'] ?? [])), 'done' => (int)($b['done'] ?? 0), 'fail' => (int)($b['fail'] ?? 0),
            'finished_at' => (int)($b['finished_at'] ?? 0), 'days' => (int)($b['days'] ?? 7),
            'found' => (int)($b['found'] ?? ($b['total'] ?? 0)), 'capped' => !empty($b['capped'])];
}
// """ + TAG + r""": kandidat = daftar Percakapan WA (log + riwayat impor WAHA), aktivitas terakhir dalam $days hari (0 = semua),
// terbaru dulu. Lewati label yang dikunci agent; yang sudah berlabel dilewati kecuali $all.
function tpBackfillCands($days, $all = false) {
    $cut = $days > 0 ? date('Y-m-d H:i:s', time() - $days * 86400) : '';
    $last = [];
    foreach (logReadAll() as $e) {
        if (($e['channel'] ?? '') !== 'whatsapp') continue;
        $n = waNormNum($e['ip'] ?? ''); $ts = (string)($e['ts'] ?? '');
        if ($n !== '' && (!isset($last[$n]) || strcmp($ts, $last[$n]) > 0)) $last[$n] = $ts;
    }
    if (function_exists('wiIndexAll')) { try { foreach (wiIndexAll() as $n => $r) {
        $n = waNormNum($n); $ts = (string)($r['last_ts'] ?? '');
        if ($n !== '' && is_array($r) && (!isset($last[$n]) || strcmp($ts, $last[$n]) > 0)) $last[$n] = $ts;
    } } catch (\Throwable $e) {} }
    $ct = waGetContacts();
    $q = [];
    foreach ($last as $n => $ts) {
        $n = (string)$n;
        if ($cut !== '' && strcmp($ts, $cut) < 0) continue;
        if (!empty($ct[$n]['tp']['lk'])) continue;
        if (!$all && is_array($ct[$n]['tp'] ?? null)) continue;
        $q[$n] = $ts;
    }
    arsort($q, SORT_STRING);
    return $q;
}
// Batas satu scan: maks TP_BACKFILL_MAX, maks 50% kuota bulanan, dan tidak melebihi sisa kuota.
function tpBackfillCap() {
    $q = tpQuota();
    $cap = TP_BACKFILL_MAX;
    if ($q['central'] && $q['limit'] > 0) $cap = min($cap, (int)floor($q['limit'] * 0.5), max(0, $q['limit'] - $q['used']));
    elseif ($q['central'] && $q['limit'] === 0) $cap = 0;
    return max(0, $cap);
}
// Antrekan scan chat lama. $dry = hanya perkiraan (tidak mengantre).
function tpBackfillStart($by, $days = 30, $all = false, $dry = false) {
    $c = tpBackfillCands($days, $all);
    $cap = tpBackfillCap();
    $take = array_map('strval', array_slice(array_keys($c), 0, $cap));
    $est = ['days' => $days, 'found' => count($c), 'take' => count($take), 'cap' => $cap, 'capped' => count($c) > count($take),
            'cost_idr' => (int)ceil(count($take) * TP_COST_IDR), 'minutes' => (int)ceil(count($take) / TP_PER_TICK)];
    if ($dry) return $est;
    $st = ['started_at' => time(), 'by' => (string)$by, 'days' => $days, 'total' => count($take), 'found' => count($c), 'capped' => $est['capped'],
           'queue' => $take, 'done' => 0, 'fail' => 0, 'finished_at' => $take ? 0 : time()];
    deiWithLock('tp-backfill', function () use ($st) { writeJson(TP_BACKFILL_FILE, $st); });
    return (tpBackfillState() ?: []) + $est;
}
""", "function tpBackfillCands(")

rep(API, "        if ($c['enabled'] && !$prev['enabled'] && !$bf) $started = tpBackfillStart($u['username']);   // pertama kali diaktifkan -> backfill 7 hari",
         "        if ($c['enabled'] && !$prev['enabled'] && !$bf) $started = tpBackfillStart($u['username'], 30);   // pertama kali diaktifkan -> scan 30 hari (" + TAG + ")")
rep(API, """        $days = (int)($in['days'] ?? 7); if (!in_array($days, [1, 3, 7, 14, 30], true)) $days = 7;
        jsonOut(['ok' => true, 'backfill' => tpBackfillStart($u['username'], $days, !empty($in['all'])), 'quota' => tpQuota()]);""",
"""        $days = (int)($in['days'] ?? 30); if (!in_array($days, [0, 7, 30, 90], true)) $days = 30;   // """ + TAG + """: 0 = semua
        if (!empty($in['estimate'])) jsonOut(['ok' => true, 'estimate' => tpBackfillStart($u['username'], $days, !empty($in['all']), true), 'quota' => tpQuota()]);
        $bfNow = tpBackfillState();
        if ($bfNow && !$bfNow['finished_at'] && $bfNow['left'] > 0 && empty($in['force'])) jsonOut(['ok' => false, 'running' => true, 'error' => 'Scan chat lama masih berjalan (' . $bfNow['left'] . ' chat tersisa).'], 409);
        $est = tpBackfillStart($u['username'], $days, !empty($in['all']), true);
        if (!$est['take']) jsonOut(['ok' => false, 'error' => $est['cap'] <= 0 ? 'Kuota klasifikasi bulan ini tidak cukup untuk scan chat lama.' : 'Tidak ada chat yang perlu di-scan di periode ini.'], 400);
        jsonOut(['ok' => true, 'backfill' => tpBackfillStart($u['username'], $days, !empty($in['all'])), 'quota' => tpQuota()]);""")

# ---------- app.js ----------
rep(A, """        (bf.finished_at ? 'selesai — ' + bf.done + ' chat' + (bf.fail ? ', ' + bf.fail + ' gagal' : '') : dn + ' / ' + tot + ' chat (berjalan di latar, ±10 chat per menit)') + '</div>';""",
       """        (bf.finished_at ? 'selesai — ' + bf.done + ' chat' + (bf.fail ? ', ' + bf.fail + ' gagal' : '') : dn + ' / ' + tot + ' chat (berjalan di latar, ±20 chat per menit)') +
        ' · ' + (bf.days ? bf.days + ' hari terakhir' : 'semua periode') + (bf.capped ? ' · dibatasi dari ' + Number(bf.found).toLocaleString('id-ID') + ' chat' : '') + '</div>';   // """ + TAG)
rep(A, """    qh += '<div style="margin-top:10px"><button type="button" class="btn ghost sm" id="tfBackfillBtn"' + (r.active ? '' : ' disabled') + '>' + ico('rotate-cw', 14) + ' Klasifikasi chat 7 hari terakhir</button></div>';""",
       """    qh += '<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center"><select id="tfBfDays" style="width:auto"' + (r.active ? '' : ' disabled') + '>' +   // """ + TAG + """
      '<option value="7">7 hari terakhir</option><option value="30" selected>30 hari terakhir</option><option value="90">90 hari terakhir</option><option value="0">Semua chat</option></select>' +
      '<button type="button" class="btn ghost sm" id="tfBackfillBtn"' + (r.active ? '' : ' disabled') + '>' + ico('rotate-cw', 14) + ' Scan chat lama</button>' +
      '<span style="font-size:12px;color:var(--muted)">Termasuk riwayat chat yang diimpor dari WhatsApp. Maks 3.000 chat / 50% kuota per scan.</span></div>';""")
rep(A, """    $('#tfBackfillBtn').onclick = function () {
      if (!confirm('Klasifikasikan semua chat WA 7 hari terakhir yang belum berlabel? Memakai kuota klasifikasi.')) return;
      api('tp_backfill', { method: 'POST', body: { days: 7 } }).then(function (x) { if (x && x.ok) { toast('Diantrekan ' + x.backfill.total + ' chat.'); loadTopik(); } else toast((x && x.error) || 'Gagal.', true); });
    };""", """    $('#tfBackfillBtn').onclick = function () {   // """ + TAG + """: perkiraan dulu, lalu konfirmasi
      var days = +$('#tfBfDays').value, fmt = function (n) { return Number(n).toLocaleString('id-ID'); };
      api('tp_backfill', { method: 'POST', body: { days: days, estimate: 1 } }).then(function (x) {
        if (!x || !x.ok) { toast((x && x.error) || 'Gagal menghitung.', true); return; }
        var e = x.estimate;
        if (!e.take) { toast(e.cap <= 0 ? 'Kuota klasifikasi bulan ini tidak cukup.' : 'Tidak ada chat belum berlabel di periode ini.', true); return; }
        var msg = 'Ditemukan ' + fmt(e.found) + ' chat belum berlabel (' + (days ? days + ' hari terakhir' : 'semua periode') + ').\\n' +
          (e.capped ? 'Yang di-scan: ' + fmt(e.take) + ' chat terbaru (batas ' + fmt(e.cap) + ' per scan).\\n' : '') +
          'Memakai ' + fmt(e.take) + ' kuota · perkiraan biaya ±Rp' + fmt(e.cost_idr) + ' · selesai ±' + fmt(e.minutes) + ' menit.\\n\\nLanjutkan?';
        if (!confirm(msg)) return;
        var go = function (force) {
          api('tp_backfill', { method: 'POST', body: { days: days, force: force ? 1 : 0 } }).then(function (y) {
            if (y && y.ok) { toast('Diantrekan ' + fmt(y.backfill.total) + ' chat.'); loadTopik(); }
            else if (y && y.running && confirm(y.error + ' Ganti dengan scan baru?')) go(true);
            else toast((y && y.error) || 'Gagal.', true);
          });
        };
        go(false);
      });
    };""")
rep(H, '<script src="app.js?v=1.2.138"></script><!-- v1.2.138: filter-topik -->', '<script src="app.js?v=1.2.139"></script><!-- ' + TAG + ' -->')
rep(H, "Saat pertama diaktifkan, chat 7 hari terakhir ikut diklasifikasi.", "Saat pertama diaktifkan, chat 30 hari terakhir (termasuk riwayat impor WhatsApp) ikut diklasifikasi.")
print('patch v1.2.139 OK; file diubah:', len(done))
