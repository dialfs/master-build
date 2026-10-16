#!/usr/bin/env python3
"""v1.2.88 — tabel RUTE redBus (pasangan kota), bukan sekadar daftar kota.
  CLI: php api/index.php action=redbus_scan [only=Jakarta] [delay=700] [dry=1]
       Memeriksa tiap pasangan kota di tabel ke halaman rute redBus; pasangan yang punya link
       pemesanan dengan opId operator disimpan di data/redbus-routes.json.
  Runtime: bila berkas itu ada, link hanya dibuat untuk pasangan yang tercatat (dua arah);
           pasangan lain -> "rute X – Y belum tersedia", plus contoh tujuan dari kota asal.
  Tanpa berkas = perilaku v1.2.87.
Idempoten. Pakai: patch_v1288_redbus_routes.py <api/index.php>"""
import re, sys, pathlib
P = pathlib.Path(sys.argv[1]); A = P.read_text(encoding='utf-8')
if 'function deiRedbusRoutes(' in A: print('sudah terpasang'); sys.exit(0)
def rep(old, new, n=1):
    global A
    c = A.count(old)
    if c != n: raise SystemExit(f'ANCHOR {c}x: {old[:80]!r}')
    A = A.replace(old, new)
A = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.88');", A, count=1)

rep("""'db_init', 'db_import', 'update_cli'], true)) { fwrite(STDERR, "CLI: action=cron_tick|wa_worker|wa_queue_status|db_init|db_import|update_cli\\n"); exit(1); }""",
    """'db_init', 'db_import', 'update_cli', 'redbus_scan'], true)) { fwrite(STDERR, "CLI: action=cron_tick|wa_worker|wa_queue_status|db_init|db_import|update_cli|redbus_scan\\n"); exit(1); }""")

rep("""function deiRedbusSlug($s) {""", r"""// v1.2.88: tabel rute (pasangan id kota) dari action=redbus_scan. null = belum ada -> semua pasangan boleh.
function deiRedbusRoutesFile() { return DATA_DIR . '/redbus-routes.json'; }
function deiRedbusRoutes() {
    static $r = false;
    if ($r !== false) return $r;
    $j = is_file(deiRedbusRoutesFile()) ? json_decode((string)@file_get_contents(deiRedbusRoutesFile()), true) : null;   // cek-storage: boleh (berkas konfigurasi hasil CLI, hanya dibaca)
    $r = (is_array($j) && !empty($j['pairs']) && is_array($j['pairs'])) ? array_fill_keys($j['pairs'], true) : null;
    return $r;
}
function deiRedbusPairKey($idA, $idB) { $a = (int)$idA; $b = (int)$idB; return min($a, $b) . '-' . max($a, $b); }
function deiRedbusRouteOk($from, $to) {
    $R = deiRedbusRoutes(); if ($R === null) return true;
    $f = deiRedbusCity($from); $t = deiRedbusCity($to);
    return $f && $t && isset($R[deiRedbusPairKey($f[1], $t[1])]);
}
// Tujuan yang tersedia dari satu kota (nama tampilan), maks $max.
function deiRedbusDestsFrom($from, $max = 8) {
    $R = deiRedbusRoutes(); $c = deiRedbusConf(); $f = deiRedbusCity($from);
    if ($R === null || !$c || !$f) return [];
    $out = [];
    foreach ($c['cities'] as $k => $v) {
        if (!(is_int($v) || ctype_digit((string)$v)) || (string)$v === $f[1]) continue;
        if (isset($R[deiRedbusPairKey($f[1], $v)])) $out[] = trim(preg_replace('/\s*\(.*?\)/', '', $k));
        if (count($out) >= $max) break;
    }
    return $out;
}
function deiRedbusSlug($s) {""")

rep("""    if (!$c || !$f || !$t || $f[1] === $t[1]) return '';""",
    """    if (!$c || !$f || !$t || $f[1] === $t[1]) return '';
    if (!deiRedbusRouteOk($from, $to)) return '';   // v1.2.88: pasangan tidak ada di tabel rute""")

rep("""    return 'Mohon maaf, rute' . $r . ' belum tersedia' . ($op !== '' ? ' di ' . $op : '') . '.';
}""", """    $msg = 'Mohon maaf, rute' . $r . ' belum tersedia' . ($op !== '' ? ' di ' . $op : '') . '.';
    $d = $from !== '' ? deiRedbusDestsFrom($from) : [];   // v1.2.88
    if ($d) $msg .= ' Dari ' . $nm(deiRedbusCity($from)[0]) . ' tersedia ke ' . implode(', ', $d) . '.';
    return $msg;
}""")

# pasangan dua kota dikenal tapi tidak ada di tabel rute -> kabar tidak tersedia
rep("""        if ($g && $g['to'] !== null && $g['from'] === null) return 'Berangkat dari kota mana? Nanti saya kirimkan link cek harga & pesan tiket ke ' . $nm($g['to']) . '.';
        return deiRedbusRouteNA() . ' Silakan sebutkan kota tujuan lain.';""",
    """        if ($g && $g['to'] !== null && $g['from'] === null) return 'Berangkat dari kota mana? Nanti saya kirimkan link cek harga & pesan tiket ke ' . $nm($g['to']) . '.';
        if ($g && $g['to'] !== null && $g['from'] !== null) return deiRedbusRouteNA($g['from'], $g['to']);   // v1.2.88
        return deiRedbusRouteNA() . ' Silakan sebutkan kota tujuan lain.';""")
rep("""        $u = deiRedbusUrl($g['from'], $g['to'], $g['date']);
        if ($u === '') return $answer;""", """        $u = deiRedbusUrl($g['from'], $g['to'], $g['date']);
        if ($u === '' && !deiRedbusRouteOk($g['from'], $g['to'])) return deiRedbusRouteNA($g['from'], $g['to']);   // v1.2.88
        if ($u === '') return $answer;""")
rep("""            error_log('redbus: kota tidak dikenal (' . $m[1] . ' -> ' . $m[2] . ')');""", """            error_log('redbus: rute/kota tidak tersedia (' . $m[1] . ' -> ' . $m[2] . ')');""")
rep("""            return deiRedbusRouteNA(trim($m[1]), trim($m[2])) . ' Silakan sebutkan kota tujuan lain.';""",
    """            return deiRedbusRouteNA(trim($m[1]), trim($m[2])) . (deiRedbusCity(trim($m[1])) && deiRedbusRoutes() !== null ? '' : ' Silakan sebutkan kota tujuan lain.');""")

# CLI scan
rep("""    /* ---------- CLI (v1.2.71): buat tabel MySQL ---------- */""", r"""    /* ---------- CLI (v1.2.88): periksa pasangan kota redBus -> data/redbus-routes.json ---------- */
    case 'redbus_scan': {
        if (PHP_SAPI !== 'cli') jsonOut(['ok' => false, 'error' => 'Hanya lewat CLI.'], 403);
        $c = deiRedbusConf();
        if (!$c || empty($c['op_id'])) { fwrite(STDERR, "redbus_scan: 'redbus' (cities + op_id) belum diisi di data/server.php\n"); exit(1); }
        $ops = array_filter(array_map('trim', explode(',', (string)$c['op_id'])));
        $cities = [];
        foreach ($c['cities'] as $k => $v) if (is_int($v) || ctype_digit((string)$v)) $cities[(string)$v] = $k;
        $only = trim((string)($_GET['only'] ?? ''));
        $onlyId = '';
        if ($only !== '') { $oc = deiRedbusCity($only); if (!$oc) { fwrite(STDERR, "redbus_scan: kota '$only' tidak ada di tabel\n"); exit(1); } $onlyId = $oc[1]; }
        $delay = max(200, (int)($_GET['delay'] ?? 700)) * 1000;
        $dry = !empty($_GET['dry']);
        $fetch = function ($a, $b) {
            $u = 'https://www.redbus.id/tiket-bus/' . deiRedbusSlug($a) . '-ke-' . deiRedbusSlug($b);
            $ch = curl_init($u);
            curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_FOLLOWLOCATION => true, CURLOPT_TIMEOUT => 25,
                CURLOPT_USERAGENT => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
                CURLOPT_HTTPHEADER => ['Accept: text/html', 'Accept-Language: id-ID,id;q=0.9']]);
            $html = (string)curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
            return [$code, $html];
        };
        $hasOp = function ($html) use ($ops) {
            if (!preg_match_all('/opId=((?:[0-9]|,|%2C)+)/i', $html, $m)) return false;
            foreach ($m[1] as $v) { $ids = explode(',', str_ireplace('%2C', ',', $v)); if (array_intersect($ops, $ids)) return true; }
            return false;
        };
        $old = is_file(deiRedbusRoutesFile()) ? (json_decode((string)file_get_contents(deiRedbusRoutesFile()), true) ?: []) : [];   // cek-storage: boleh
        $pairs = array_fill_keys(is_array($old['pairs'] ?? null) ? $old['pairs'] : [], true);
        $ids = array_keys($cities); $n = 0; $hit = 0; $okPages = 0;
        for ($i = 0; $i < count($ids); $i++) for ($j = $i + 1; $j < count($ids); $j++) {
            $a = (string)$ids[$i]; $b = (string)$ids[$j];
            if ($onlyId !== '' && $a !== $onlyId && $b !== $onlyId) continue;
            $key = deiRedbusPairKey($a, $b); $found = false; $n++;
            foreach ([[$cities[$a], $cities[$b]], [$cities[$b], $cities[$a]]] as $dir) {
                list($code, $html) = $fetch($dir[0], $dir[1]); usleep($delay);
                if ($code === 200 && strlen($html) > 5000) $okPages++;
                if ($code === 200 && $hasOp($html)) { $found = true; break; }
            }
            if ($found) { $pairs[$key] = true; $hit++; } else unset($pairs[$key]);
            echo ($found ? '  ADA   ' : '  -     ') . $cities[$a] . ' – ' . $cities[$b] . "\n";
        }
        if ($okPages === 0) { fwrite(STDERR, "redbus_scan: tidak ada halaman redBus yang terbaca (diblokir/jaringan?) — berkas tidak diubah\n"); exit(1); }
        echo "\nDiperiksa $n pasangan, ada rute: $hit. Total pasangan tersimpan: " . count($pairs) . "\n";
        if ($dry) { echo "(dry=1: berkas tidak ditulis)\n"; exit(0); }
        $names = [];
        foreach (array_keys($pairs) as $k) { list($x, $y) = explode('-', $k); if (isset($cities[$x], $cities[$y])) $names[] = $cities[$x] . ' – ' . $cities[$y]; }
        sort($names);
        file_put_contents(deiRedbusRoutesFile(), json_encode(['updated_at' => wibDate('Y-m-d H:i:s'), 'op_id' => (string)$c['op_id'],
            'pairs' => array_keys($pairs), 'routes' => $names], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));   // cek-storage: boleh
        echo "Tersimpan: " . deiRedbusRoutesFile() . "\n";
        exit(0);
    }

    /* ---------- CLI (v1.2.71): buat tabel MySQL ---------- */""")
P.write_text(A, encoding='utf-8'); print('OK v1.2.88 terpasang')
