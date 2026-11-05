# v1.2.150: claim-patuh — chat yang di-claim agent tidak lagi dibalas bot otomatis:
#  1) waGetMode: claim aktif = 'human' walau wa-modes tidak berisi nomor itu
#  2) pesan non-teks (lokasi/kontak/polling/reaction/unsupported) tidak dibalas "hanya teks" saat dipegang agent; reaction tidak pernah dibalas
#  3) wa_set_mode -> bot ikut melepas claim (data konsisten)
import sys, os, shutil, time
T = os.path.expanduser(sys.argv[1])
H = os.path.join(T, 'dashboard/chatbot-ai/index.html'); A = os.path.join(T, 'api/index.php')
ts = time.strftime('%Y%m%d-%H%M%S')
for f in (H, A): shutil.copy2(f, f + '.bak-v12150-' + ts)
def rep(path, old, new):
    s = open(path, encoding='utf-8').read()
    if new in s: print('skip'); return
    assert s.count(old) == 1, (path, old[:70]); open(path, 'w', encoding='utf-8').write(s.replace(old, new))

# 1) waGetMode
rep(A, """    $k = waNormNum($from);
    return (isset($modes[$k]['mode']) && $modes[$k]['mode'] === 'human') ? 'human' : 'bot';
}""", """    $k = waNormNum($from);
    if (isset($modes[$k]['mode']) && $modes[$k]['mode'] === 'human') return 'human';
    // v1.2.150: claim-patuh — chat yang masih di-claim agent = manusia, apa pun isi wa-modes
    $cl = readJson(waClaimFile(), []);
    return (is_array($cl) && $k !== '' && !empty($cl[$k])) ? 'human' : 'bot';
}""")

# 2a) jalur Meta/WAHA non-teks
rep(A, """            if (deiIsManual($s)) {
                waProcessIncoming($s, $wa, $from, deiNonTextLabel($msg['type'] ?? ''), $deiWaName, $metadata);
                return;
            }
            if (deiSysOnce($from, 'nontext', 1800))""", """            if (deiIsManual($s)) {
                waProcessIncoming($s, $wa, $from, deiNonTextLabel($msg['type'] ?? ''), $deiWaName, $metadata);
                return;
            }
            // v1.2.150: claim-patuh — dipegang agent: catat saja (tanpa balasan otomatis)
            if (waGetMode($from) === 'human') {
                if (($msg['type'] ?? '') !== 'reaction')
                    waProcessIncoming($s, $wa, $from, deiNonTextLabel($msg['type'] ?? ''), $deiWaName, array_merge((array)$metadata, ['_no_reply' => true]));
                return;
            }
            if (($msg['type'] ?? '') === 'reaction') return;   // v1.2.150: reaksi emoji tidak perlu dibalas
            if (deiSysOnce($from, 'nontext', 1800))""")

# 2b) jalur Fonnte non-teks
rep(A, """        if (deiIsManual($s) && (($jenis !== '' && $jenis !== 'text') || $text === '')) {""",
       """        if ((deiIsManual($s) || waGetMode($from) === 'human') && (($jenis !== '' && $jenis !== 'text') || $text === '')) {   // v1.2.150: claim-patuh""")

# 3) wa_set_mode -> bot melepas claim
rep(A, """        deiGuardSpvScope($u, $num);   // v1.2.59
        waSetMode($num, $mode, 'takeover');   // v1.2.101""", """        deiGuardSpvScope($u, $num);   // v1.2.59
        if ($mode === 'bot' && ($cl150 = waClaimGet($num))) {   // v1.2.150: claim-patuh — kembali ke bot = claim dilepas
            waClaimSet($num, null);
            try { agentEvent('release', (string)($cl150['agent_username'] ?? ''), $num, ['by' => $u['username']]); } catch (\\Throwable $e) {}
        }
        waSetMode($num, $mode, 'takeover');   // v1.2.101""")

rep(H, '<script src="app.js?v=1.2.149"></script><!-- v1.2.149: kepala-chat-mobile -->',
       '<script src="app.js?v=1.2.150"></script><!-- v1.2.150: claim-patuh -->')
rep(A, "define('DEI_VERSION', 'v1.2.149');   // v1.2.149: kepala-chat-mobile",
       "define('DEI_VERSION', 'v1.2.150');   // v1.2.150: claim-patuh")
print('patch v1.2.150 OK')
