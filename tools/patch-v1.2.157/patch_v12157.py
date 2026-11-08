#!/usr/bin/env python3
"""v1.2.157 or-penalaran — balasan chatbot terpotong karena Haiku 5.5 (OpenRouter) menghabiskan max_tokens untuk penalaran.
 1. callOpenRouter: penalaran dimatikan secara bawaan (reasoning.enabled=false); kalau model menolak parameter itu (HTTP 400) -> ulang sekali tanpa parameter.
 2. Jaring pengaman diperluas: ulang sekali juga saat finish=length DAN jawaban sangat pendek (< 60 karakter), bukan hanya saat kosong.
 3. Jawaban panjang yang tetap terpotong (finish=length) dipangkas ke akhir kalimat utuh terakhir (bukan JSON).
 Idempoten. Pakai: patch_v12157.py <dei-tenant>"""
import sys, shutil, time
T = sys.argv[1]; TAG = 'v1.2.157: or-penalaran'
A = T + '/api/index.php'
api = open(A, encoding='utf-8').read()
if TAG in api:
    print('sudah dipatch'); sys.exit(0)
shutil.copy2(A, A + '.bak-v12157-' + time.strftime('%Y%m%d-%H%M%S'))
def rep(s, old, new, cnt=1):
    n = s.count(old); assert n == cnt, f'anchor {n}x (harus {cnt}): {old[:90]!r}'
    return s.replace(old, new)

api = rep(api, "define('DEI_VERSION', 'v1.2.156');   // v1.2.156: cls-hemat",
               "define('DEI_VERSION', 'v1.2.157');   // " + TAG)

# 1. reasoning bawaan mati
api = rep(api,
"    if (!empty($settings['api']['_or_reasoning'])) $payload['reasoning'] = $settings['api']['_or_reasoning'];   // v1.2.102: or-kosong\n",
"    if (!empty($settings['api']['_or_reasoning'])) $payload['reasoning'] = $settings['api']['_or_reasoning'];   // v1.2.102: or-kosong\n"
"    elseif (empty($settings['api']['_or_no_reason_param'])) $payload['reasoning'] = ['enabled' => false];   // " + TAG + ": penalaran memakan max_tokens -> balasan terpotong\n")

# 1b. model menolak parameter reasoning -> ulang tanpa parameter
api = rep(api,
"""    if ($code !== 200) {
        $msg = $data['error']['message'] ?? ('HTTP ' . $code);
        return [false, 'AI error: ' . $msg, []];
    }
    if (isset($data['error']) && empty($data['choices'])) return [false, 'AI error: ' . (string)($data['error']['message'] ?? 'tanpa pesan'), []];   // v1.2.102: or-kosong""",
"""    if ($code !== 200) {
        $msg = $data['error']['message'] ?? ('HTTP ' . $code);
        if ($code === 400 && isset($payload['reasoning']) && empty($settings['api']['_or_reasoning']) && empty($settings['api']['_or_no_reason_param'])) {   // """ + TAG + """
            error_log('openrouter: parameter reasoning ditolak (' . $msg . ') -> ulang tanpa parameter');
            $s2 = $settings; $s2['api']['_or_no_reason_param'] = 1;
            return callOpenRouter($s2, $systemBlocks, $messages);
        }
        return [false, 'AI error: ' . $msg, []];
    }
    if (isset($data['error']) && empty($data['choices'])) return [false, 'AI error: ' . (string)($data['error']['message'] ?? 'tanpa pesan'), []];   // v1.2.102: or-kosong""")

# 2. jaring pengaman: kosong ATAU (length & sangat pendek)
api = rep(api,
"""    if (trim((string)$answer) === '' && empty($settings['api']['_or_retry'])) {
        $fin = (string)($data['choices'][0]['finish_reason'] ?? '');
        error_log('openrouter: jawaban kosong (finish=' . $fin . ', out=' . (int)($data['usage']['completion_tokens'] ?? 0) . ') -> coba ulang');""",
"""    $fin = (string)($data['choices'][0]['finish_reason'] ?? '');
    $short = $fin === 'length' && mb_strlen(trim((string)$answer)) < 60;   // """ + TAG + """: sisa penalaran -> potongan kata
    if ((trim((string)$answer) === '' || $short) && empty($settings['api']['_or_retry'])) {
        error_log('openrouter: jawaban ' . ($short ? 'terpotong pendek' : 'kosong') . ' (finish=' . $fin . ', out=' . (int)($data['usage']['completion_tokens'] ?? 0) . ') -> coba ulang');""")

# 3. pangkas ke kalimat utuh
api = rep(api,
"""        $usage['cost_usd'] = (float)$data['usage']['cost'];   // v1.2.69: biaya asli dari OpenRouter
    }
    return [true, trim($answer), $usage];
}
""",
"""        $usage['cost_usd'] = (float)$data['usage']['cost'];   // v1.2.69: biaya asli dari OpenRouter
    }
    $answer = trim($answer);
    if ($fin === 'length') $answer = deiCutToSentence($answer);   // """ + TAG + """
    return [true, $answer, $usage];
}
/* """ + TAG + """ — balasan terpotong batas token: pangkas ke akhir kalimat utuh terakhir.
 * JSON / teks berstruktur tidak disentuh. Kalau tak ada batas kalimat yang wajar (sisa < 40%), tambahkan "…". */
function deiCutToSentence($s) {
    $s = rtrim((string)$s);
    if ($s === '' || preg_match('/^\\s*[\\[{]/', $s)) return $s;
    $len = mb_strlen($s);
    $best = -1;
    if (preg_match_all('/[.!?…](?:["\\')\\]*_~]*)(?=\\s|$)|\\n/u', $s, $m, PREG_OFFSET_CAPTURE)) {
        foreach ($m[0] as $hit) $best = max($best, mb_strlen(substr($s, 0, $hit[1] + strlen($hit[0]))));
    }
    if ($best >= (int)ceil($len * 0.4)) return rtrim(mb_substr($s, 0, $best));
    return rtrim(preg_replace('/\\s+\\S*$/u', '', $s), " ,;:-") . '…';
}
""")
open(A, 'w', encoding='utf-8').write(api)
print('tenant OK')
