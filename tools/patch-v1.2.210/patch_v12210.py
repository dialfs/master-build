#!/usr/bin/env python3
"""v1.2.210 (thread-db): di mode MySQL, thread chat WA dan fungsi per-nomor lain membaca log nomor itu langsung
(dei_log WHERE num=?), bukan 500 baris terakhir SELURUH tenant lalu disaring. Sebelumnya pesan lama satu chat
"hilang" dari thread dashboard begitu tenant ramai (kasus Omoway 19 Nov 2026: pesan 05:41 tidak tampil malamnya).
Kena: wa_thread, cari pesan di dalam chat, transkrip analisa lead, cek jendela 24 jam (kirim manual/media/terjadwal).
Mode file: perilaku sama persis (log memang dipangkas log_limit). Butuh v1.2.209. Idempoten.
Pakai: patch_v12210.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.210: thread-db'; NEED = 'v1.2.209: autoreply-hp'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
API = T + '/api/index.php'
s = open(API, encoding='utf-8').read()
if TAG in s: print('SUDAH', API); sys.exit(0)
assert NEED in s, 'butuh v1.2.209 dulu'

s = rep(s, "define('DEI_VERSION', 'v1.2.209');   // v1.2.209:",
        "define('DEI_VERSION', 'v1.2.210');   // v1.2.210: thread-db — thread chat WA (mode MySQL) memuat seluruh riwayat nomor itu, tidak terpotong 500 entri terakhir tenant; v1.2.209:", what='versi')

s = rep(s, "    return $out;\n}\nfunction logDbMutate($fn) {",
"""    return $out;
}
// v1.2.210: thread-db — entri satu nomor untuk tampilan/cek per chat. Mode mysql: langsung dei_log WHERE num=?
// (tidak terpotong jendela global logWindow). Mode file: logReadAll() apa adanya (pemanggil tetap menyaring nomor).
function logReadForNum($num, $max = 5000) {
    if (!deiStorageMysql()) return logReadAll();
    return logReadByNumber($num, $max);
}
function logDbMutate($fn) {""", what='helper')

s = rep(s, "        $logs = logReadAll();\n        $msgs = [];\n        $lastInbound = 0;",
           "        $logs = logReadForNum($num, 5000);   // v1.2.210: thread-db\n        $msgs = [];\n        $lastInbound = 0;", what='wa_thread')
s = rep(s, "    if ($logs === null) $logs = logReadAll();\n    $rows = [];",
           "    if ($logs === null) $logs = logReadForNum($number, 400);   // v1.2.210: thread-db\n    $rows = [];", what='leadBuildTranscript')
s = rep(s, "    foreach (($logs === null ? logReadAll() : $logs) as $e) {",
           "    foreach (($logs === null ? logReadForNum($num, 2000) : $logs) as $e) {   // v1.2.210: thread-db", what='schedLastInbound')
s = rep(s, "    if ($logs === null) $logs = logReadAll();\n    if (!empty($it['cancel_on_reply'])) {",
           "    if ($logs === null && !deiStorageMysql()) $logs = logReadAll();   // v1.2.210: thread-db — mysql: baca per nomor (cache lintas nomor salah)\n    if (!empty($it['cancel_on_reply'])) {", what='schedSendOne')
s = rep(s, "        foreach (logReadAll() as $e) {\n            if (($e['channel'] ?? '') === 'whatsapp' && waNormNum($e['ip'] ?? '') === $num && ($e['q'] ?? '') !== '' && waInboundOnCh($e, $winChM)) {",
           "        foreach (logReadForNum($num, 2000) as $e) {   // v1.2.210: thread-db\n            if (($e['channel'] ?? '') === 'whatsapp' && waNormNum($e['ip'] ?? '') === $num && ($e['q'] ?? '') !== '' && waInboundOnCh($e, $winChM)) {", what='wa_send_media')
s = rep(s, "        $logs = logReadAll();\n        $lastInbound = 0;\n        $winCh116 = waWinCh($num, $s);",
           "        $logs = logReadForNum($num, 2000);   // v1.2.210: thread-db\n        $lastInbound = 0;\n        $winCh116 = waWinCh($num, $s);", what='wa_send_manual')
s = rep(s, "function waMsgSearch164($u, $num, $q, $ts) {\n    $logs = logReadAll();",
           "function waMsgSearch164($u, $num, $q, $ts) {\n    $logs = $num !== '' ? logReadForNum($num, 5000) : logReadAll();   // v1.2.210: thread-db", what='cari-dalam-chat')

if not NOBAK: shutil.copy2(API, API + '.bak-v12210-' + stamp)
open(API, 'w', encoding='utf-8').write(s); print('OK', API)
