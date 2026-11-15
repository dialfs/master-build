#!/usr/bin/env python3
"""v1.2.182 (foto-otomatis-pasti): foto entri KB bertanda "Kirim otomatis" ikut terkirim bila jawaban bot WA
jelas memakai isi entri itu, walau AI tidak menulis kode [[FOTO:id]] (mis. prompt tenant melarang menulis kode).
Pencocokan server: kata khas entri (bukan kata umum KB; df <= 30% entri) muncul di jawaban: >= 4 kata & >= 40%.
Tetap sekali per percakapan (kode terkirim tercatat di riwayat), maks 2 entri.
Idempoten.  Pakai: patch_v12182.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
T = H + '/dei-tenant'; API = T + '/api/index.php'
TAG = 'v1.2.182: foto-otomatis-pasti'; NEED = 'v1.2.181: kb-simpan-aman'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
C = '   // ' + TAG
FN = r'''/* v1.2.182: foto-otomatis-pasti — entri foto_auto ikut terkirim bila jawaban bot jelas memakai isinya,
 * walau AI tidak menulis kode [[FOTO:id]]. Cocok = kata khas entri (bukan kata umum KB) muncul di jawaban. */
function deiKbTok($s) {
    $s = mb_strtolower(preg_replace('~https?://\S+~u', ' ', (string)$s));
    $w = preg_split('/[^\p{L}\p{N}]+/u', $s, -1, PREG_SPLIT_NO_EMPTY);
    $o = [];
    foreach ((array)$w as $t) { if (mb_strlen($t) >= 4 || (ctype_digit($t) && strlen($t) >= 2)) $o[$t] = true; }
    return $o;
}
function deiKbFotoAutoMatch($kb, $answer) {
    $kb = array_values(array_filter((array)$kb, function ($e) { return is_array($e) && trim((string)($e['content'] ?? '')) !== ''; }));
    $n = count($kb); if (!$n || trim((string)$answer) === '') return [];
    $df = []; $toks = [];
    foreach ($kb as $i => $e) { $toks[$i] = deiKbTok($e['content']); foreach ($toks[$i] as $t => $_) $df[$t] = ($df[$t] ?? 0) + 1; }
    $lim = max(2, (int)ceil($n * 0.3));
    $ans = deiKbTok($answer); $hit = [];
    foreach ($kb as $i => $e) {
        if (empty($e['foto_auto']) || empty($e['id']) || !deiKbFotoClean($e['images'] ?? [])) continue;
        $khas = array_filter(array_keys($toks[$i]), function ($t) use ($df, $lim) { return $df[$t] <= $lim; });
        if (count($khas) < 3) continue;
        $m = 0; foreach ($khas as $t) if (isset($ans[$t])) $m++;
        $r = $m / count($khas);
        if ($m >= 4 && $r >= 0.4) $hit[(string)$e['id']] = $r;
    }
    arsort($hit);
    return array_slice(array_keys($hit), 0, 2);
}
'''
def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.181');   //", "define('DEI_VERSION', 'v1.2.182');   // " + TAG + " — foto entri Kirim otomatis terkirim walau AI tidak menulis kode; v1.2.181:", 'versi')
    s = rep(s, "function deiKbRev() {", FN + "function deiKbRev() {", 'fn')
    s = rep(s, "    if ($deiFotoIds) $deiFotoIds = deiKbFotoAutoDedupe($deiFotoIds, $history, $text);   // v1.2.178: foto-otomatis\n",
               "    if ($deiFotoIds) $deiFotoIds = deiKbFotoAutoDedupe($deiFotoIds, $history, $text);   // v1.2.178: foto-otomatis\n"
               "    if ($ok && count($deiFotoIds) < 2 && deiKbFotoAktif($s, 'whatsapp')) {" + C + "\n"
               "        try {\n"
               "            $deiKb182 = readJson(KB_FILE, []);\n"
               "            $deiU182 = deiUnitFor((string)($wa['_ch'] ?? 'utama')); if ($deiU182) $deiKb182 = deiUnitFilterKb($deiKb182, $deiU182);\n"
               "            $deiAuto182 = array_values(array_diff(deiKbFotoAutoMatch($deiKb182, $answer), $deiFotoIds));\n"
               "            if ($deiAuto182) $deiAuto182 = deiKbFotoAutoDedupe($deiAuto182, $history, '');   // sekali per percakapan, tanpa pengecualian kata minta-foto\n"
               "            $deiFotoIds = array_slice(array_values(array_unique(array_merge($deiFotoIds, $deiAuto182))), 0, 2);\n"
               "        } catch (\\Throwable $e) { error_log('kb-foto auto: ' . $e->getMessage()); }\n"
               "    }\n", 'hook')
    return s
s = rd(API)
if TAG in s: print('sudah:', API)
else:
    assert NEED in s, 'butuh v1.2.181'
    if not NOBAK: shutil.copy2(API, API + '.bak-v12182-' + stamp)
    wr(API, api(s)); print('OK', API)
