#!/usr/bin/env python3
"""v1.2.82 — redBus lebih andal:
  1. Prompt redBus lebih tegas (mengalahkan aturan "hanya dari knowledge base" untuk harga/tiket,
     tanyakan kota asal bila belum disebut, jangan jawab "tidak memiliki informasi").
  2. Cadangan di server: bila AI tidak menulis tag tetapi pesan pelanggan jelas menanyakan
     harga/tiket dengan kota yang dikenal, link dibuat sendiri dari pesan (+2 pesan sebelumnya).
     Hanya kota tujuan yang dikenal -> tanya kota asal.
Idempoten. Pakai: patch_v1282_redbus_fallback.py <api/index.php>"""
import re, sys, pathlib
P = pathlib.Path(sys.argv[1]); A = P.read_text(encoding='utf-8')
if 'function deiRedbusGuess(' in A: print('sudah terpasang'); sys.exit(0)
def rep(old, new, n=1):
    global A
    c = A.count(old)
    if c != n: raise SystemExit(f'ANCHOR {c}x: {old[:80]!r}')
    A = A.replace(old, new)
A = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.82');", A, count=1)

rep('''        . "- Jangan menulis link redBus sendiri; sistem mengganti tag dengan link resmi. Bila kota asal/tujuan tidak ada di daftar atau belum jelas, jangan tulis tag dan tanyakan kotanya.";
}''', '''        . "- Jangan menulis link redBus sendiri; sistem mengganti tag dengan link resmi.\\n"
        . "- PENTING: aturan ini berlaku walaupun harga tidak ada di knowledge base. Untuk pertanyaan harga/tiket/kursi JANGAN menjawab 'tidak memiliki informasi' dan jangan menyuruh menghubungi tim; harga & kursi terbaru selalu ada di link redBus.\\n"
        . "- Bila kota asal belum disebut (mis. 'harga ke Purwokerto'), tanyakan singkat: berangkat dari kota mana. Setelah pelanggan menjawab, tulis tagnya.\\n"
        . "- Bila kota asal/tujuan tidak ada di daftar, sampaikan rute itu belum bisa dicek lewat link dan tawarkan rute dari daftar kota di atas.";
}''')

rep('''// Ganti tag di jawaban AI dengan link; tag yang tidak bisa dibuat linknya dibuang.
function deiRedbusExpand($answer) {
    if (strpos((string)$answer, '[[REDBUS') === false) return $answer;
    $c = deiRedbusConf();''', '''// v1.2.82: tebak rute dari pesan pelanggan (pesan sekarang + 2 pesan pelanggan sebelumnya).
// Hasil: ['from' => nama|null, 'to' => nama|null, 'date' => Y-m-d|'', 'intent' => bool]
function deiRedbusGuess($message, $history = []) {
    $c = deiRedbusConf(); if (!$c) return null;
    $texts = [mb_strtolower((string)$message)];
    for ($i = count($history) - 1; $i >= 0 && count($texts) < 3; $i--) {
        if (($history[$i]['role'] ?? '') !== 'assistant') $texts[] = mb_strtolower((string)($history[$i]['content'] ?? ''));
    }
    $names = array_keys($c['cities']);
    usort($names, function ($a, $b) { return mb_strlen($b) - mb_strlen($a); });
    $rx = '/(?<![\\p{L}])(' . implode('|', array_map(function ($n) { return preg_quote(mb_strtolower($n), '/'); }, $names)) . ')(?![\\p{L}])/u';
    $intent = false; $to = null; $from = null; $date = ''; $seen = [];
    $today = wibDate('Y-m-d');
    // salah ketik ringan (purwekerto -> purwokerto): kata >=5 huruf, jarak edit <=1 (<=2 bila >=8 huruf)
    $single = array_values(array_filter(array_map('mb_strtolower', $names), function ($n) { return strpos($n, ' ') === false && strlen($n) >= 5; }));
    foreach ($texts as $k => $t) {
        $texts[$k] = preg_replace_callback('/\\p{L}{5,}/u', function ($w) use ($single) {
            $x = $w[0]; if (in_array($x, $single, true)) return $x;
            foreach ($single as $n) { if (abs(strlen($n) - strlen($x)) <= 2 && levenshtein($x, $n) <= (strlen($n) >= 8 ? 2 : 1)) return $n; }
            return $x;
        }, $t);
    }
    foreach ($texts as $ti => $t) {
        if (preg_match('/\\b(harga|tiket|tarif|ongkos|biaya|berapa|pesan|booking|book|kursi|seat|jadwal|berangkat)\\b/u', $t)) $intent = true;
        if ($date === '') {
            if (preg_match('/\\b(\\d{4}-\\d{2}-\\d{2})\\b/', $t, $m)) $date = $m[1];
            elseif (preg_match('/\\blusa\\b/u', $t)) $date = date('Y-m-d', strtotime($today . ' +2 day'));
            elseif (preg_match('/\\bbesok\\b/u', $t)) $date = date('Y-m-d', strtotime($today . ' +1 day'));
            elseif (preg_match('/\\b(?:tanggal|tgl)\\.?\\s*(\\d{1,2})\\b/u', $t, $m) && (int)$m[1] >= 1 && (int)$m[1] <= 31) {
                $d = sprintf('%s-%02d', substr($today, 0, 7), (int)$m[1]);
                if ($d < $today) $d = date('Y-m', strtotime(substr($today, 0, 7) . '-01 +1 month')) . sprintf('-%02d', (int)$m[1]);
                if (checkdate((int)substr($d, 5, 2), (int)substr($d, 8, 2), (int)substr($d, 0, 4))) $date = $d;
            }
        }
        if (!preg_match_all($rx, $t, $mm, PREG_OFFSET_CAPTURE)) continue;
        foreach ($mm[1] as $hit) {
            $city = deiRedbusCity($hit[0]); if (!$city) continue;
            $before = substr($t, max(0, $hit[1] - 12), min(12, $hit[1]));
            if ($to === null && preg_match('/\\b(ke|tujuan|menuju|to)\\s*$/u', $before)) $to = $city[0];
            elseif ($from === null && preg_match('/\\b(dari|asal|from)\\s*$/u', $before)) $from = $city[0];
            else $seen[] = [$city[0], $ti];
        }
    }
    foreach ($seen as $s) {   // kota tanpa kata "dari/ke": pesan sekarang lebih dulu
        if ($s[0] === $to || $s[0] === $from) continue;
        if ($to === null && $from !== null) $to = $s[0];
        elseif ($from === null && ($to !== null || $s[1] === 0)) $from = $s[0];
        elseif ($to === null) $to = $s[0];
    }
    if ($from !== null && $to === null && count($seen) <= 1) { $to = $from; $from = null; }   // satu kota saja = tujuan
    return ['from' => $from, 'to' => $to, 'date' => $date, 'intent' => $intent];
}

// Ganti tag di jawaban AI dengan link; tag yang tidak bisa dibuat linknya dibuang.
// v1.2.82: tanpa tag -> cadangan dari pesan pelanggan.
function deiRedbusExpand($answer, $message = '', $history = []) {
    if (strpos((string)$answer, '[[REDBUS') === false) {
        $c = deiRedbusConf();
        if (!$c || $message === '' || stripos((string)$answer, 'redbus.id') !== false) return $answer;
        $g = deiRedbusGuess($message, $history);
        if (!$g || !$g['intent'] || $g['to'] === null) return $answer;
        $refuse = (bool)preg_match('/tidak (memiliki|punya|ada|tersedia)[^.\\n]{0,20}informasi|belum (memiliki|punya|ada) informasi|hubungi (tim|admin|cs|customer)/iu', (string)$answer);
        if ($g['from'] === null) {
            return $refuse ? 'Berangkat dari kota mana? Nanti saya kirimkan link cek harga & pesan tiket ke ' . trim(preg_replace('/\\s*\\(.*?\\)/', '', $g['to'])) . '.' : $answer;
        }
        $u = deiRedbusUrl($g['from'], $g['to'], $g['date']);
        if ($u === '') return $answer;
        $line = trim((string)($c['label'] ?? 'Cek harga & pesan tiket:') . ' ' . $u);
        $nm = function ($x) { return trim(preg_replace('/\\s*\\(.*?\\)/', '', $x)); };   // "Yogyakarta (jogja)" -> "Yogyakarta"
        if ($refuse) return 'Harga & kursi terbaru rute ' . $nm($g['from']) . ' – ' . $nm($g['to']) . ' bisa dicek langsung di redBus.' . "\\n\\n" . $line;
        return rtrim((string)$answer) . "\\n\\n" . $line;
    }
    $c = deiRedbusConf();''')

rep("return [$ok, $ok ? deiRedbusExpand($answer) : $answer,", "return [$ok, $ok ? deiRedbusExpand($answer, $message, $history) : $answer,", 3)
P.write_text(A, encoding='utf-8'); print('OK v1.2.82 terpasang')
