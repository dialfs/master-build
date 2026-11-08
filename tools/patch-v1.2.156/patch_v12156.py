#!/usr/bin/env python3
"""v1.2.156 cls-hemat — Filter Topik boros token.
 Pusat (backend/classify-lib.php): reasoning dimatikan + max_tokens 300; jawaban kosong / HTTP 400 diulang SEKALI
   (effort low, 1500 token — kombinasi terbukti v1.2.102); token semua percobaan dicatat; header HTTP-Referer.
 Tenant (api/index.php): jalur tanpa pusat ikut matikan reasoning; tpSweep berhenti mencoba chat live yang gagal
   TP_MAX_FAIL (3) kali berturut-turut (sebelumnya diulang tiap 10 menit tanpa batas).
 Idempoten. Pakai: patch_v12156.py <dei-tenant> <dei-pusat>"""
import sys, shutil, time
T, P = sys.argv[1], sys.argv[2]; TAG = 'v1.2.156: cls-hemat'
A = T + '/api/index.php'; C = P + '/backend/classify-lib.php'
api, cls = (open(p, encoding='utf-8').read() for p in (A, C))
if TAG in api and TAG in cls:
    print('sudah dipatch'); sys.exit(0)
stamp = time.strftime('%Y%m%d-%H%M%S')
def rep(s, old, new, cnt=1):
    n = s.count(old); assert n == cnt, f'anchor {n}x (harus {cnt}): {old[:90]!r}'
    return s.replace(old, new)

# ---------------- TENANT ----------------
if TAG not in api:
    shutil.copy2(A, A + '.bak-v12156-' + stamp)
    api = rep(api, "define('DEI_VERSION', 'v1.2.155');   // v1.2.155: statistik-kontak",
                   "define('DEI_VERSION', 'v1.2.156');   // " + TAG)
    api = rep(api, "if (!defined('TP_MAX_DIVS')) define('TP_MAX_DIVS', 12);\n",
                   "if (!defined('TP_MAX_DIVS')) define('TP_MAX_DIVS', 12);\n"
                   "if (!defined('TP_MAX_FAIL')) define('TP_MAX_FAIL', 3);         // " + TAG + ": chat live gagal 3x berturut-turut -> berhenti sampai ada pesan baru\n")
    api = rep(api, "    $s2 = $s; $s2['api']['max_tokens'] = 150; $s2['api']['_timeout'] = 25; $s2['api']['fallback'] = 'none';\n",
                   "    $s2 = $s; $s2['api']['max_tokens'] = 300; $s2['api']['_timeout'] = 25; $s2['api']['fallback'] = 'none';\n"
                   "    $s2['api']['_or_reasoning'] = ['enabled' => false];   // " + TAG + ": Haiku 5.5 menghabiskan 150 token untuk penalaran -> jawaban kosong\n")
    api = rep(api,
"""        try { convStateMutate(function (&$a) use ($num, $p, $ok) {
            if (!is_array($a[$num] ?? null)) return;
            if ($ok) { $a[$num]['tp_n'] = max(0, (int)($a[$num]['tp_n'] ?? 0) - (int)$p['n']); $a[$num]['tp_due'] = 0; $a[$num]['tp_err_at'] = 0; }
            else $a[$num]['tp_err_at'] = time();
        }, $num); }""",
"""        $qo = is_array($r) && !empty($r['quota_out']);   // """ + TAG + r""": kuota habis tidak dihitung gagal
        try { convStateMutate(function (&$a) use ($num, $p, $ok, $qo) {
            if (!is_array($a[$num] ?? null)) return;
            if ($ok) { $a[$num]['tp_n'] = max(0, (int)($a[$num]['tp_n'] ?? 0) - (int)$p['n']); $a[$num]['tp_due'] = 0; $a[$num]['tp_err_at'] = 0; $a[$num]['tp_err_n'] = 0; }
            elseif ($qo) $a[$num]['tp_err_at'] = time();
            else {
                $en = (int)($a[$num]['tp_err_n'] ?? 0) + 1;
                if ($en >= TP_MAX_FAIL) { $a[$num]['tp_n'] = 0; $a[$num]['tp_due'] = 0; $a[$num]['tp_err_at'] = 0; $a[$num]['tp_err_n'] = 0; }   // menyerah sampai ada pesan baru
                else { $a[$num]['tp_err_at'] = time(); $a[$num]['tp_err_n'] = $en; }
            }
        }, $num); }""")
    open(A, 'w', encoding='utf-8').write(api)
    print('tenant OK')

# ---------------- PUSAT ----------------
if TAG not in cls:
    shutil.copy2(C, C + '.bak-v12156-' + stamp)
    cls = rep(cls, " * Prompt HARUS sama dengan tpPrompt() di tenant (api/index.php).\n",
                   " * Prompt HARUS sama dengan tpPrompt() di tenant (api/index.php).\n"
                   " * " + TAG + ": reasoning dimatikan (dulu 150 token habis untuk penalaran -> jawaban kosong tapi tetap ditagih);\n"
                   " *   jawaban kosong / HTTP 400 diulang sekali dengan jatah besar; token semua percobaan dicatat.\n")
    cls = rep(cls, "function clsClean($s, $max) {",
r"""function clsAnswer($j) {   // """ + TAG + r"""
    $ans = is_array($j) ? ($j['choices'][0]['message']['content'] ?? '') : '';
    if (is_array($ans)) { $tx = ''; foreach ($ans as $seg) $tx .= is_array($seg) ? ($seg['text'] ?? '') : (string)$seg; $ans = $tx; }
    return trim((string)$ans);
}
/** Kirim paralel. $retry=false: tanpa penalaran, 300 token. $retry=true: effort low, 1500 token. Hasil [[item, http, json, err], ...] */
function clsSend($cfg, $biz, $topics, $list, $retry) {
    $mh = curl_multi_init(); $hs = [];
    foreach ($list as $it) {
        list($sys, $user) = clsPrompt($biz, $topics, $it['msgs']);
        $ch = curl_init(getenv('DEI_CLS_OR_URL') ?: 'https://openrouter.ai/api/v1/chat/completions');   // env: uji dengan mock
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true, CURLOPT_TIMEOUT => $retry ? 40 : 30, CURLOPT_CONNECTTIMEOUT => 8,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'Authorization: Bearer ' . $cfg['key'], 'X-Title: DEI Filter Topik', 'HTTP-Referer: https://chat.deintegra.com/filter-topik'],
            CURLOPT_POSTFIELDS => json_encode(['model' => $cfg['model'], 'max_tokens' => $retry ? 1500 : 300, 'temperature' => 0, 'usage' => ['include' => true],
                'reasoning' => $retry ? ['effort' => 'low', 'exclude' => true] : ['enabled' => false],
                'messages' => [['role' => 'system', 'content' => $sys], ['role' => 'user', 'content' => $user]]], JSON_UNESCAPED_UNICODE)]);
        curl_multi_add_handle($mh, $ch);
        $hs[] = [$ch, $it];
    }
    do { $s = curl_multi_exec($mh, $run); if ($run) curl_multi_select($mh, 1.0); } while ($run && $s === CURLM_OK);
    $out = [];
    foreach ($hs as list($ch, $it)) {
        $res = curl_multi_getcontent($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $err = curl_error($ch);
        curl_multi_remove_handle($mh, $ch); curl_close($ch);
        $out[] = [$it, $code, json_decode((string)$res, true), $err];
    }
    curl_multi_close($mh);
    return $out;
}
function clsClean($s, $max) {""")
    a = cls.index("    // panggil OpenRouter paralel\n"); b = cls.index("    curl_multi_close($mh);\n", a) + len("    curl_multi_close($mh);\n")
    assert cls.count("    // panggil OpenRouter paralel\n") == 1
    cls = cls[:a] + r"""    // panggil OpenRouter paralel — """ + TAG + r"""
    $n = 0; $tin = 0; $tout = 0; $cost = 0.0;
    $idList = array_keys($ids);
    $tally = function ($j) use (&$tin, &$tout, &$cost) {   // token tiap percobaan tetap ditagih -> catat semua
        if (!is_array($j['usage'] ?? null)) return;
        $tin += (int)($j['usage']['prompt_tokens'] ?? 0); $tout += (int)($j['usage']['completion_tokens'] ?? 0);
        if (isset($j['usage']['cost']) && is_numeric($j['usage']['cost'])) $cost += (float)$j['usage']['cost'];
    };
    $rows = []; $again = [];
    foreach ($items ? clsSend($cfg, $biz, $topics, $items, false) : [] as $row) {
        $tally($row[2]);
        if ($row[1] === 400 || ($row[1] === 200 && clsAnswer($row[2]) === '')) $again[] = $row[0];
        else $rows[] = $row;
    }
    if ($again) foreach (clsSend($cfg, $biz, $topics, $again, true) as $row) { $tally($row[2]); $rows[] = $row; }
    foreach ($rows as list($it, $code, $j, $err)) {
        $iid = $it['id'];
        if ($code !== 200 || !is_array($j) || empty($j['choices'])) {
            $results[] = ['id' => $iid, 'ok' => false, 'error' => 'AI: ' . (is_array($j) ? (string)($j['error']['message'] ?? ('HTTP ' . $code)) : ($err !== '' ? $err : 'HTTP ' . $code))];
            continue;
        }
        $n++;
        $p = clsParse(clsAnswer($j), $idList);
        $results[] = $p ? (['id' => $iid, 'ok' => true] + $p) : ['id' => $iid, 'ok' => false, 'used' => true, 'error' => 'jawaban tak terbaca'];
    }
""" + cls[b:]
    open(C, 'w', encoding='utf-8').write(cls)
    print('pusat OK')
