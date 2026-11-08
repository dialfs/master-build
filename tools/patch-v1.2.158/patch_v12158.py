#!/usr/bin/env python3
"""v1.2.158 rl-wa — pesan WA pelanggan hilang saat kena batas per nomor (kasus deintegra 8 Nov 2026: 12 pesan terbuang).
 1. Chat yang dipegang agent (mode manusia / claim) tidak kena batas per nomor & tidak dapat balasan otomatis "terlalu banyak pesan".
 2. Mode bot: pesan yang lewat batas TETAP dicatat di log (hanya AI yang tidak membalas); peringatan ikut tercatat.
 3. Batas bawaan 20 -> 60 pesan/jam per nomor (nilai 20 tersimpan = bawaan lama, dianggap 60).
 Idempoten. Pakai: patch_v12158.py <dei-tenant>"""
import sys, shutil, time
T = sys.argv[1]; TAG = 'v1.2.158: rl-wa'
A = T + '/api/index.php'; J = T + '/dashboard/chatbot-ai/app.js'; Hh = T + '/dashboard/chatbot-ai/index.html'
api = open(A, encoding='utf-8').read()
if TAG in api:
    print('sudah dipatch'); sys.exit(0)
st = time.strftime('%Y%m%d-%H%M%S')
for f in (A, J, Hh): shutil.copy2(f, f + '.bak-v12158-' + st)
def rep(s, old, new, cnt=1):
    n = s.count(old); assert n == cnt, f'anchor {n}x (harus {cnt}): {old[:90]!r}'
    return s.replace(old, new)

api = rep(api, "define('DEI_VERSION', 'v1.2.157');   // v1.2.157: or-penalaran",
               "define('DEI_VERSION', 'v1.2.158');   // " + TAG)

api = rep(api,
"""    $limit = (int)($wa['rate_limit_per_number'] ?? ($s['api']['rate_limit'] ?? 20));
    // v1.2.58: mode Manual tidak memakai AI (tidak ada biaya), jangan buang pesan
    // pelanggan & jangan kirim balasan otomatis "terlalu banyak pesan".
    if (!deiIsManual($s) && !checkRateLimit('wa:' . $from, $limit)) {
        if (deiSysOnce($from, 'ratelimit', 600)) waSend($wa, $from, 'Anda mengirim terlalu banyak pesan. Mohon tunggu sebentar ya.');
        else waOutCount('saved');   // v1.2.89
        return;
    }
""",
"""    // """ + TAG + """: batas per nomor hanya menahan BALASAN AI — pesan pelanggan selalu dicatat.
    // Mode Manual & chat yang dipegang agent (mode manusia / claim) tidak dibatasi sama sekali.
    $limit = (int)($wa['rate_limit_per_number'] ?? 0);
    if ($limit <= 0 || $limit === 20) $limit = 60;   // 20 = bawaan lama
    if (!deiIsManual($s) && waGetMode($from) !== 'human' && !checkRateLimit('wa:' . $from, $limit)) {
        $metaInfo['_no_reply'] = true; $metaInfo['_rl'] = true; $metaInfo['_rl_a'] = '';
        $rlTxt = 'Anda mengirim terlalu banyak pesan. Mohon tunggu sebentar ya.';
        if (deiSysOnce($from, 'ratelimit', 600) && waSend($wa, $from, $rlTxt)) $metaInfo['_rl_a'] = $rlTxt;
    }
""")

api = rep(api,
"""    if ($mode === 'bot' && !deiIsManual($s)) {
        try { if (gcWaHandle($s, $wa, $from, $text, $senderName, $metaInfo)) return; }""",
"""    if ($mode === 'bot' && !deiIsManual($s) && empty($metaInfo['_rl'])) {   // """ + TAG + """
        try { if (gcWaHandle($s, $wa, $from, $text, $senderName, $metaInfo)) return; }""")

api = rep(api,
"""        logPrepend(array_merge($logBase, ['a' => '', 'hemat' => 'ack']), $logLimit);
        waOutCount('saved');
        return;
    }
    // v1.2.89: ucapan penutup""",
"""        if (!empty($metaInfo['_rl'])) {   // """ + TAG + """: lewat batas per nomor — dicatat, AI tidak membalas
            logPrepend(array_merge($logBase, ['a' => (string)($metaInfo['_rl_a'] ?? ''), 'hemat' => 'ratelimit']), $logLimit);
            if (($metaInfo['_rl_a'] ?? '') === '') waOutCount('saved');
            return;
        }
        logPrepend(array_merge($logBase, ['a' => '', 'hemat' => 'ack']), $logLimit);
        waOutCount('saved');
        return;
    }
    // v1.2.89: ucapan penutup""")

js = open(J, encoding='utf-8').read()
js = rep(js, "      $('#wa_rate').value = wa.rate_limit_per_number || 20;",
             "      $('#wa_rate').value = (+wa.rate_limit_per_number && +wa.rate_limit_per_number !== 20) ? wa.rate_limit_per_number : 60;   // " + TAG)
js = rep(js, "      rate_limit_per_number: +$('#wa_rate').value || 20,",
             "      rate_limit_per_number: +$('#wa_rate').value || 60,   // " + TAG)
ht = open(Hh, encoding='utf-8').read()
ht = rep(ht, '<label class="fl">Rate Limit (per nomor / jam)</label><input type="number" id="wa_rate" placeholder="20"></div>',
             '<label class="fl">Rate Limit balasan AI (per nomor / jam)</label><input type="number" id="wa_rate" placeholder="60"><!-- ' + TAG + ' --><div class="hint" style="font-size:12px;color:var(--muted);margin-top:4px">Lewat batas: pesan tetap tercatat, AI berhenti membalas sementara. Chat yang dipegang agent tidak dibatasi.</div></div>')
open(A, 'w', encoding='utf-8').write(api); open(J, 'w', encoding='utf-8').write(js); open(Hh, 'w', encoding='utf-8').write(ht)
print('OK dipatch', TAG)
