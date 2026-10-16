#!/usr/bin/env python3
"""v1.2.84 — redBus ketat: hanya link resmi buatan server (dengan opId operator).
  - Link redbus.id yang ditulis AI sendiri dibuang (bisa salah kota / tanpa opId).
  - Kota di luar tabel -> "rute belum tersedia", bukan link.
Idempoten. Pakai: patch_v1284_redbus_strict.py <api/index.php>"""
import re, sys, pathlib
P = pathlib.Path(sys.argv[1]); A = P.read_text(encoding='utf-8')
if 'function deiRedbusExpandCore(' in A: print('sudah terpasang'); sys.exit(0)
def rep(old, new, n=1):
    global A
    c = A.count(old)
    if c != n: raise SystemExit(f'ANCHOR {c}x: {old[:80]!r}')
    A = A.replace(old, new)
A = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.84');", A, count=1)
rep('''        . "- Jangan menulis link redBus sendiri; sistem mengganti tag dengan link resmi.\\n"''',
    '''        . "- JANGAN PERNAH menulis URL/link redbus.id sendiri; sistem mengganti tag dengan link resmi.\\n"''')
rep('''        . "- Bila kota asal/tujuan tidak ada di daftar, sampaikan rute itu belum bisa dicek lewat link dan tawarkan rute dari daftar kota di atas.";''',
    '''        . "- Hanya kota di daftar yang dilayani. Bila kota asal/tujuan tidak ada di daftar, jawab singkat bahwa rute itu tidak tersedia (tanpa tag, tanpa link) lalu tawarkan kota tujuan dari daftar.";''')
rep('''function deiRedbusExpand($answer, $message = '', $history = []) {
    if (strpos((string)$answer, '[[REDBUS') === false) {
        $c = deiRedbusConf();
        if (!$c || $message === '' || stripos((string)$answer, 'redbus.id') !== false) return $answer;''',
'''// v1.2.84: pembungkus — buang link redbus.id tulisan AI, lalu pastikan ada link resmi atau kabar "tidak tersedia".
function deiRedbusRouteNA($from = '', $to = '') {
    $c = deiRedbusConf() ?: []; $op = trim((string)($c['operator'] ?? ''));
    $nm = function ($x) { return trim(preg_replace('/\\s*\\(.*?\\)/', '', (string)$x)); };
    $r = ($from !== '' && $to !== '') ? ' ' . $nm($from) . ' – ' . $nm($to) : ' tersebut';
    return 'Mohon maaf, rute' . $r . ' belum tersedia' . ($op !== '' ? ' di ' . $op : '') . '.';
}
function deiRedbusExpand($answer, $message = '', $history = []) {
    if (!deiRedbusConf()) return $answer;
    $raw = false;
    if (preg_match('~redbus\\.id~i', (string)$answer)) {
        $raw = true;   // baris yang memuat link tulisan AI dibuang seluruhnya
        $answer = trim(preg_replace("/\\n{3,}/", "\\n\\n", preg_replace('~^.*(?:https?://)?(?:www\\.)?redbus\\.id\\S*.*$\\n?~imu', '', (string)$answer)));
    }
    // tag dengan kota di luar tabel -> seluruh jawaban jadi kabar "tidak tersedia" (tanpa kalimat "berikut linknya")
    if (preg_match_all('/\\[\\[REDBUS:([^|\\]]*)\\|([^|\\]]*)(?:\\|([^\\]]*))?\\]\\]/u', (string)$answer, $tm, PREG_SET_ORDER)) {
        foreach ($tm as $m) if (deiRedbusUrl(trim($m[1]), trim($m[2]), trim($m[3] ?? '')) === '') {
            error_log('redbus: kota tidak dikenal (' . $m[1] . ' -> ' . $m[2] . ')');
            return deiRedbusRouteNA(trim($m[1]), trim($m[2])) . ' Silakan sebutkan kota tujuan lain.';
        }
    }
    if ($raw && strpos((string)$answer, '[[REDBUS') === false) {
        // AI menulis link sendiri: ganti seluruhnya dengan link resmi, tanya kota asal, atau kabar tidak tersedia
        $g = $message !== '' ? deiRedbusGuess($message, $history) : null;
        $nm = function ($x) { return trim(preg_replace('/\\s*\\(.*?\\)/', '', (string)$x)); };
        if ($g && $g['to'] !== null && $g['from'] !== null && ($u = deiRedbusUrl($g['from'], $g['to'], $g['date'])) !== '') {
            $c = deiRedbusConf();
            return 'Harga & kursi terbaru rute ' . $nm($g['from']) . ' – ' . $nm($g['to']) . ' bisa dicek langsung di redBus.' . "\\n\\n" . trim((string)($c['label'] ?? 'Cek harga & pesan tiket:') . ' ' . $u);
        }
        if ($g && $g['to'] !== null && $g['from'] === null) return 'Berangkat dari kota mana? Nanti saya kirimkan link cek harga & pesan tiket ke ' . $nm($g['to']) . '.';
        return deiRedbusRouteNA() . ' Silakan sebutkan kota tujuan lain.';
    }
    return deiRedbusExpandCore($answer, $message, $history);
}
function deiRedbusExpandCore($answer, $message = '', $history = []) {
    if (strpos((string)$answer, '[[REDBUS') === false) {
        $c = deiRedbusConf();
        if (!$c || $message === '' || stripos((string)$answer, 'redbus.id') !== false) return $answer;''')
rep('''        if ($u === '') { error_log('redbus: kota tidak dikenal (' . $m[1] . ' -> ' . $m[2] . ')'); return ''; }''',
    '''        if ($u === '') { error_log('redbus: kota tidak dikenal (' . $m[1] . ' -> ' . $m[2] . ')'); return deiRedbusRouteNA(trim($m[1]), trim($m[2])); }   // v1.2.84''')
P.write_text(A, encoding='utf-8'); print('OK v1.2.84 terpasang')
