#!/usr/bin/env python3
"""v1.2.77 — perbaikan WAHA (uji di nomor sungguhan):
  * Balasan dari HP (fromMe) tidak tercatat: NOWEB menaruh lawan bicara di `from`
    (dan _data.key.remoteJid), bukan di `to`. Lawan bicara kini diambil dari
    remoteJid / Info.Chat dulu, lalu from/to, dan nomor sendiri dilewati.
  * Sesi FAILED (login rusak) di-restart tiap 3 dtk tanpa henti -> QR tak pernah muncul.
    Kini: restart sekali; FAILED lagi dalam 2 menit -> logout (hapus login rusak) + start = QR baru.
Idempoten. Pakai: patch_v1277_waha_fix.py <api/index.php>"""
import re, sys, pathlib
P = pathlib.Path(sys.argv[1]); src = P.read_text(encoding='utf-8')
if 'function wahaChatCandidates(' in src: print('sudah terpasang'); sys.exit(0)
if 'function wahaToMetaPayload(' not in src: raise SystemExit('butuh v1.2.76 dulu')
def rep(old, new):
    global src
    n = src.count(old)
    if n != 1: raise SystemExit(f'ANCHOR {n}x: {old[:80]!r}')
    src = src.replace(old, new)
src = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.77');", src, count=1)

rep("""    $fromMe = !empty($p['fromMe']);
    $chat = (string)($fromMe ? ($p['to'] ?? '') : ($p['from'] ?? ''));
    if ($chat === '' || preg_match('/@(g\\.us|newsletter|broadcast)$/i', $chat)) return null;
    $num = wahaResolveNum($wa, $chat, $p);
    if ($num === '') { error_log('waha: lawan bicara tidak terbaca (' . $chat . ')'); return null; }
    $me = wahaJidNum(preg_replace('/:\\d+@/', '@', (string)($evt['me']['id'] ?? '')));
    if ($me !== '' && $me === $num) return null;
""", """    $fromMe = !empty($p['fromMe']);
    // v1.2.77: lawan bicara = chat-nya (remoteJid), bukan selalu `to` — NOWEB mengisi `from`
    // dengan chat lawan bicara juga untuk pesan fromMe. Nomor sendiri dilewati.
    $me = wahaJidNum(preg_replace('/:\\d+@/', '@', (string)($evt['me']['id'] ?? '')));
    $meLid = strtolower((string)($evt['me']['lid'] ?? ''));
    $num = ''; $chat = '';
    foreach (wahaChatCandidates($p, $fromMe) as $cj) {
        if (preg_match('/@(g\\.us|newsletter|broadcast)$/i', $cj)) return null;
        if ($meLid !== '' && strtolower(preg_replace('/:\\d+@/', '@', $cj)) === $meLid) continue;
        $n = wahaResolveNum($wa, $cj, $p);
        if ($n === '' || ($me !== '' && $n === $me)) { if ($chat === '') $chat = $cj; continue; }
        $num = $n; $chat = $cj; break;
    }
    if ($num === '') {
        if ($chat !== '') error_log('waha: lawan bicara tidak terbaca (' . $chat . ')');
        return null;
    }
""")

rep("function wahaToMetaPayload($wa, $evt) {", """// v1.2.77: kandidat JID chat lawan bicara, urut dari yang paling bisa dipercaya.
function wahaChatCandidates($p, $fromMe) {
    $d = is_array($p['_data'] ?? null) ? $p['_data'] : [];
    $c = [
        (string)($d['key']['remoteJid'] ?? ''),          // NOWEB
        (string)($d['Info']['Chat'] ?? ''),              // GOWS
        (string)($d['id']['remote'] ?? ''),              // WEBJS
    ];
    if ($fromMe) { $c[] = (string)($p['to'] ?? ''); $c[] = (string)($p['from'] ?? ''); }
    else         { $c[] = (string)($p['from'] ?? ''); $c[] = (string)($p['to'] ?? ''); }
    $out = [];
    foreach ($c as $j) { $j = trim($j); if ($j !== '' && strpos($j, '@') !== false && !in_array($j, $out, true)) $out[] = $j; }
    return $out;
}
function wahaToMetaPayload($wa, $evt) {""")

rep("""    elseif ($st === 'FAILED') { wahaApi($wa, 'POST', '/api/sessions/' . rawurlencode($n) . '/restart'); $d['status'] = 'STARTING'; }
    return [true, $d];""", """    elseif ($st === 'FAILED') {
        // v1.2.77: restart sekali. FAILED lagi dalam 2 menit = login tersimpan rusak/ditolak WhatsApp
        // -> logout (hapus login) lalu start, supaya QR baru muncul (dulu restart tiap 3 dtk tanpa henti).
        $f = DATA_DIR . '/waha-failed.json';
        $last = (int)(readJson($f, [])[$n] ?? 0);
        if ($last > 0 && time() - $last < 120) {
            wahaApi($wa, 'POST', '/api/sessions/' . rawurlencode($n) . '/logout');
            wahaApi($wa, 'POST', '/api/sessions/' . rawurlencode($n) . '/start');
            writeJson($f, [$n => 0]);
            error_log('waha: sesi ' . $n . ' gagal berulang -> logout + start (QR baru)');
        } else {
            wahaApi($wa, 'POST', '/api/sessions/' . rawurlencode($n) . '/restart');
            writeJson($f, [$n => time()]);
        }
        $d['status'] = 'STARTING';
    }
    return [true, $d];""")
P.write_text(src, encoding='utf-8'); print('OK v1.2.77 terpasang')
