#!/usr/bin/env python3
"""v1.2.101 — Percakapan: siklus hidup per percakapan WA + laporan Kinerja Layanan.

Record percakapan: dibuka saat pesan pelanggan masuk (agent kirim duluan -> origin outbound), lalu
bot / serah ke agent (alasan: keyword, ai_limit, ai_fail, manual_mode, takeover, agent_reply, assign, ...) /
assign / balasan agent, sampai selesai:
  - agent menekan "Selesai" di thread (resolved_by agent; chat dilepas)
  - pelanggan pamit ("ok makasih", 👍) setelah dibalas (guest_bye)
  - pesan terakhir dari kita & pelanggan diam >= 24 jam (timeout; resolved_at = balasan terakhir)
  Pesan pelanggan <= 30 menit setelah selesai -> dibuka lagi (reopen_n). Tanpa aktivitas 7 hari -> expired.
Penyimpanan dua mode: file = data/conv-open.json + data/convs/YYYY-MM.jsonl; mysql = dei_conversations
(dibuat otomatis bila belum ada; juga lewat db_init).
Laporan (Laporan & Log › Kinerja Layanan): Unassigned/Assigned/Resolved, FRT, FRT agent, waktu antre,
response time, resolution time (+ selisih vs periode sebelumnya), Bot vs Agent, tren harian, pola jam &
hari, per agent, per nomor bisnis, daftar percakapan + CSV. Endpoint: conv_report, conv_list, conv_export,
wa_resolve. cron_tick: convSweep.
Pemakaian: python3 patch_v12101_percakapan.py <root dei-tenant>   (idempoten; backup *.bak-v12101-*)  Butuh v1.2.100."""
import sys, os, time, shutil
TEN = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.101: percakapan'

def patch(root, rel, pairs):
    p = os.path.join(root, rel)
    s = open(p, encoding='utf-8').read()
    if MARK in s: print('sudah dipatch:', rel); return
    if 'v1.2.100: routing' not in s: sys.exit('GAGAL: v1.2.100 belum terpasang di ' + rel)
    for old, new in pairs:
        n = s.count(old)
        if n != 1: sys.exit(f'GAGAL {rel}: anchor {n}x:\n{old[:300]}')
        s = s.replace(old, new)
    shutil.copy2(p, p + '.bak-v12101-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

rd = lambda f: open(os.path.join(HERE, f), encoding='utf-8').read()
STORAGE = '\n/* v1.2.101: percakapan — lapisan penyimpanan */' + rd('conv_storage.php')
LOGIC = '/* v1.2.101: percakapan — mesin status & statistik */' + rd('conv_logic.php') + '\n'
ACTIONS = '    /* v1.2.101: percakapan — endpoint */' + rd('conv_actions.php') + '\n'

php = [
    ("define('DEI_VERSION', 'v1.2.100');", "define('DEI_VERSION', 'v1.2.101');"),
    # skema mysql
    ("""            KEY ts (ts)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
    ];
}""", """            KEY ts (ts)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci",
        convDbSchemaSql(),   // v1.2.101: percakapan
    ];
}"""),
    ("// Lepas kunci nomor milik slot worker yang mati", STORAGE.rstrip('\n') + "\n\n// Lepas kunci nomor milik slot worker yang mati"),
    ("/* ---------- escalations.json ---------- */", LOGIC + "/* ---------- escalations.json ---------- */"),
    # hook: pesan pelanggan
    ("function convGuestMsg($num, $text) {", "function convGuestMsg($num, $text, $ch = '') {   // v1.2.101: + nomor bisnis"),
    ("    } catch (\\Throwable $e) { error_log('convGuestMsg: ' . $e->getMessage()); }\n}",
     "    } catch (\\Throwable $e) { error_log('convGuestMsg: ' . $e->getMessage()); }\n"
     "    convTrack($num, 'guest', ['ch' => (string)$ch, 'bye' => $bye]);   // v1.2.101: percakapan\n}"),
    ("    convGuestMsg($from, $text);   // v1.2.56",
     "    convGuestMsg($from, $text, (string)($wa['_ch'] ?? ''));   // v1.2.56 + v1.2.101"),
    # hook: balasan bot / pesan sistem / agent
    ("    } catch (\\Throwable $e) { error_log('convReply: ' . $e->getMessage()); }\n}",
     "    } catch (\\Throwable $e) { error_log('convReply: ' . $e->getMessage()); }\n"
     "    if ($who === 'bot' || $who === 'system') convTrack($num, $who);   // v1.2.101: percakapan (agent lewat deiRecordAgentReply)\n}"),
    ("        agentEvent('reply', $agent, $num, $ex);\n",
     "        agentEvent('reply', $agent, $num, $ex);\n"
     "        convTrack($num, 'agent', ['agent' => (string)$agent]);   // v1.2.101: percakapan\n"),
    # hook: serah ke agent (mode manusia) + alasan
    ("function waSetMode($from, $mode) {\n    $r = deiWithLock('wa-modes', function () use ($from, $mode) { return waSetMode_nolock($from, $mode); });\n"
     "    if ($mode === 'human') convBotReset($from);   // v1.2.97: batas-ai — kembali ke bot nanti mulai dari nol\n",
     "function waSetMode($from, $mode, $reason = '') {   // v1.2.101: + alasan serah ke agent\n"
     "    $r = deiWithLock('wa-modes', function () use ($from, $mode) { return waSetMode_nolock($from, $mode); });\n"
     "    if ($mode === 'human') convBotReset($from);   // v1.2.97: batas-ai — kembali ke bot nanti mulai dari nol\n"
     "    if ($mode === 'human') convTrack($from, 'handover', ['reason' => $reason !== '' ? $reason : 'mode_human']);   // v1.2.101: percakapan\n"),
    ("    if ($mode === 'bot' && !empty($ho['enabled']) && waMatchHandoff($text, $ho['keywords'] ?? [])) {\n        waSetMode($from, 'human');",
     "    if ($mode === 'bot' && !empty($ho['enabled']) && waMatchHandoff($text, $ho['keywords'] ?? [])) {\n        waSetMode($from, 'human', 'keyword');"),
    ("convBotCount($from) >= $deiAiLim['max']) {\n        waSetMode($from, 'human');",
     "convBotCount($from) >= $deiAiLim['max']) {\n        waSetMode($from, 'human', 'ai_limit');"),
    ("try { waSetMode($from, 'human'); } catch (\\Throwable $e) { error_log('ai_fail_handoff: '",
     "try { waSetMode($from, 'human', 'ai_fail'); } catch (\\Throwable $e) { error_log('ai_fail_handoff: '"),
    ("waSetMode($eto, 'human'); // agent balas dari HP", "waSetMode($eto, 'human', 'agent_reply'); // agent balas dari HP"),
    ("waSetMode($num, 'human'); // replying manually = taking over", "waSetMode($num, 'human', 'agent_reply'); // replying manually = taking over"),
    ("        waSetMode($num, $mode);\n        jsonOut(['ok' => true, 'number' => $num, 'mode' => $mode]);",
     "        waSetMode($num, $mode, 'takeover');   // v1.2.101\n        jsonOut(['ok' => true, 'number' => $num, 'mode' => $mode]);"),
    ("try { waSetMode($num, 'human'); } catch (\\Throwable $e) {}", "try { waSetMode($num, 'human', 'escalation'); } catch (\\Throwable $e) {}"),
    ("        waSetMode($number, 'human');\n", "        waSetMode($number, 'human', 'assign');   // v1.2.101\n"),
    # hook: assign / lepas
    ("function waClaimSet($number, $claim) {\n    return deiWithLock('wa-claims', function () use ($number, $claim) { return waClaimSet_nolock($number, $claim); });\n}",
     "function waClaimSet($number, $claim) {\n"
     "    $prev = '';   // v1.2.101: percakapan — catat assign / lepas bila pemegang berubah\n"
     "    $r = deiWithLock('wa-claims', function () use ($number, $claim, &$prev) {\n"
     "        $cs = readJson(waClaimFile(), []);\n"
     "        $prev = (string)($cs[waNormNum($number)]['agent_username'] ?? '');\n"
     "        return waClaimSet_nolock($number, $claim);\n"
     "    });\n"
     "    $new = is_array($claim) ? (string)($claim['agent_username'] ?? '') : '';\n"
     "    if ($r && $new !== '' && $new !== $prev) convTrack($number, 'assign', ['agent' => $new]);\n"
     "    elseif ($r && $claim === null && $prev !== '') convTrack($number, 'release');\n"
     "    return $r;\n}"),
    # hook: auto-closing terkirim
    ("        $out[] = ['number' => $num, 'ok' => (bool)$ok];\n        if (!$ok) continue;\n",
     "        $out[] = ['number' => $num, 'ok' => (bool)$ok];\n        if (!$ok) continue;\n"
     "        convTrack($num, 'closing');   // v1.2.101: percakapan\n"),
    # cron
    ("try { $r['routed'] = deiRouteDrain(20, $s); }",
     "try { $r['conv'] = convSweep(); } catch (\\Throwable $e) { $r['err_conv'] = $e->getMessage(); }   // v1.2.101: percakapan\n"
     "        try { $r['routed'] = deiRouteDrain(20, $s); }"),
    # thread: status percakapan
    ("            'mode' => waGetMode($num),\n",
     "            'mode' => waGetMode($num),\n"
     "            'conv' => (function () use ($num) { try { return convPublic(convStoreGet($num)); } catch (\\Throwable $e) { return null; } })(),   // v1.2.101\n"),
    # flag "Selesai" saat ditandai agent
    ("    $hasAgent = isset($agentReplied[$num])",
     "    // v1.2.101: percakapan — ditandai selesai (tombol Selesai) dan belum ada pesan baru sesudahnya\n"
     "    if ($st && !empty($st['res_at']) && (int)$st['res_at'] >= (int)$at) {\n"
     "        $flag = 'done'; $note = 'Ditandai selesai' . (!empty($st['res_by']) ? ' oleh ' . $st['res_by'] : '');\n"
     "    }\n"
     "    $hasAgent = isset($agentReplied[$num])"),
    ("    case 'wa_conversations_v2': {", ACTIONS + "    case 'wa_conversations_v2': {"),
]

if __name__ == '__main__' and os.environ.get('HANYA_PHP') != '0':
    patch(TEN, 'api/index.php', php)
    if os.path.exists(os.path.join(HERE, 'patch_ui.py')):
        exec(open(os.path.join(HERE, 'patch_ui.py'), encoding='utf-8').read())
    print('selesai')
