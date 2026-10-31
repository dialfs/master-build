#!/usr/bin/env python3
r"""v1.2.126 respon-median: Kinerja Layanan lebih jujur + chat handover tidak terlantar.
 1. Statistik: median & terlama untuk Respon Pertama; kartu dipisah Respon Pertama Bot / Agent
    (median sebagai angka utama, rata-rata & terlama di bawahnya). Satu chat 58 jam tidak lagi
    membuat bot 4 detik terlihat 20 menit.
 2. FRT agent: agent membalas tanpa serah terima & tanpa bot sebelumnya -> dihitung dari pesan
    pertama (sebelumnya 0 detik).
 3. Kembali ke Bot bila Agent Tidak Membalas (settings.handover_fallback): chat handover yang
    belum di-claim & belum dibalas N menit -> nomor kembali ke bot + pesan maaf ke tamu.
    Sebelumnya nomor kembali ke bot diam-diam setelah 1 jam dan tamu tidak pernah dijawab.
Pakai: python3 patch_v12126_respon_median.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.125)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.126: respon-median'
STAMP = time.strftime('%Y%m%d-%H%M%S')

def one(s, old, rel):
    n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:90]); return s.index(old)
def rep(s, old, new, rel):
    one(s, old, rel); return s.replace(old, new)
def patch(rel, fn):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    assert 'v1.2.125: wa-tampilan-sama' in s, rel + ': butuh v1.2.125'
    s2 = fn(s, rel); assert TAG in s2, rel
    shutil.copy2(p, p + '.bak-v12126-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s2); print('OK', rel)

SWEEP = r"""/* ---------- SWEEP 1b (v1.2.126: respon-median): Kembali ke Bot bila Agent Tidak Membalas ----------
 * Chat yang diserahkan ke agent (kata kunci, batas AI, AI gagal) tapi belum di-claim & belum dibalas
 * siapa pun selama N menit: nomor kembali ke bot + pesan maaf ke tamu. Sebelumnya nomor kembali ke
 * bot diam-diam (waModeSweepIdle, 1 jam) dan tamu tidak pernah dijawab sampai ia menulis lagi. */
define('DEI_HF_TEXT_ID', "Mohon maaf membuat Anda menunggu \xF0\x9F\x99\x8F Tim kami belum sempat membalas. Sementara itu asisten virtual kami siap membantu \xE2\x80\x94 silakan sampaikan kembali pertanyaan Anda di sini.");
define('DEI_HF_TEXT_EN', "Sorry to keep you waiting \xF0\x9F\x99\x8F Our team hasn't been able to reply yet. In the meantime our virtual assistant is ready to help \xE2\x80\x94 please send your question again here.");
function deiHfConf($s) {
    $c = is_array($s['handover_fallback'] ?? null) ? $s['handover_fallback'] : [];
    return [
        'enabled' => !empty($c['enabled']),
        'minutes' => max(5, min(240, (int)($c['minutes'] ?? 15))),
        'text'    => mb_substr(trim((string)($c['text'] ?? '')), 0, 500),
    ];
}
function deiHfText($hf, $lang) {
    if ($hf['text'] !== '') return $hf['text'];
    return ($lang === 'en') ? DEI_HF_TEXT_EN : DEI_HF_TEXT_ID;
}
// Tamu masih menunggu & belum pernah dikirimi fallback untuk penantian ini (dipakai juga oleh waModeSweepIdle).
function deiHfPending($st, $now) {
    $since = (int)($st['guest_waiting_since'] ?? 0);
    return $since > 0 && ($st['last_from'] ?? '') === 'guest' && ($now - $since) <= 20 * 3600
        && (int)($st['hf_since'] ?? 0) !== $since;
}
function handoverFallbackSweep($s) {
    if (deiIsManual($s)) return [];
    $hf = deiHfConf($s);
    if (!$hf['enabled']) return [];
    $wa = waConf($s);
    if (!($wa['enabled'] ?? false)) return [];
    $all = convStateReadAll();
    if (!is_array($all) || empty($all)) return [];
    $now = time();
    $batas = $hf['minutes'] * 60;
    $keepCtx = ($wa['keep_context'] ?? true);
    $out = [];
    foreach ($all as $num => $st) {
        $num = (string)$num;
        if (!is_array($st) || !deiHfPending($st, $now)) continue;
        $since = (int)$st['guest_waiting_since'];
        $wait = $now - $since;
        if ($wait < $batas) continue;
        if (waGetMode($num) !== 'human' || waClaimGet($num)) continue;   // bot yang pegang / agent sedang pegang
        $text = deiHfText($hf, (string)($st['lang'] ?? 'id'));
        if (escDry()) { escDryLog(['via' => 'handover_fallback', 'to' => $num, 'msg' => $text]); $out[] = ['number' => $num, 'ok' => true, 'dry' => true]; continue; }
        // tandai dulu, baru kirim -> tick yang tumpang-tindih tidak mengirim dua kali
        $klaim = convStateMutate(function (&$a) use ($num, $since) {
            if ((int)($a[$num]['guest_waiting_since'] ?? 0) !== $since || (int)($a[$num]['hf_since'] ?? 0) === $since) return false;
            $a[$num]['hf_since'] = $since;
            return true;
        }, $num);
        if (!$klaim) continue;
        try { waSetMode($num, 'bot'); } catch (\Throwable $e) { error_log('handover_fallback mode: ' . $e->getMessage()); }
        $ok = waSend($wa, $num, $text);
        $menit = (int)floor($wait / 60);
        $out[] = ['number' => $num, 'ok' => (bool)$ok, 'wait_min' => $menit];
        if (!$ok) continue;
        convReply($num, 'bot');   // tamu sudah mendapat jawaban: hentikan eskalasi, catat balasan pertama
        if ($keepCtx) { $h = waLoadHistory($num); $h[] = ['role' => 'assistant', 'content' => $text]; waSaveHistory($num, $h); }
        logPrepend([
            'ts' => date('Y-m-d H:i:s'), 'q' => '', 'a' => $text, 'ip' => $num,
            'channel' => 'whatsapp', 'dir' => 'closing',
            'utm_source' => 'whatsapp', 'utm_medium' => 'handover_fallback', 'utm_campaign' => '', 'page' => '', 'referrer' => '',
        ], (int)($s['api']['log_limit'] ?? 500));
        try { waAuditLog('handover_fallback', 'system', $num, ['wait_min' => $menit]); } catch (\Throwable $e) {}
        try { tgNotify($s, "\xE2\x86\xA9\xEF\xB8\x8F [WhatsApp] +" . $num . " tidak dibalas agent " . $menit . " menit \xE2\x80\x94 dikembalikan ke bot."); } catch (\Throwable $e) {}
    }
    return $out;
}

/* ---------- SWEEP 2: Eskalasi ---------- */"""

def f_api(s, rel):
    s = rep(s, "define('DEI_VERSION', 'v1.2.125');   // v1.2.125: wa-tampilan-sama",
               "define('DEI_VERSION', 'v1.2.126');   // v1.2.126: respon-median", rel)
    # --- statistik
    s = rep(s, "    $A = ['frt' => $z(), 'frt_agent' => $z(), 'wait' => $z(),",
               "    $A = ['frt' => $z(), 'frt_bot' => $z(), 'frt_agent' => $z(), 'wait' => $z(),", rel)
    s = rep(s, "    $nums = []; $daily = []; $hourly = array_fill(0, 24, 0); $wday = array_fill(1, 7, 0);\n",
               "    $nums = []; $daily = []; $hourly = array_fill(0, 24, 0); $wday = array_fill(1, 7, 0);\n"
               "    $L = ['frt' => [], 'frt_bot' => [], 'frt_agent' => []];   // v1.2.126: respon-median — nilai mentah untuk median & terlama\n", rel)
    s = rep(s, "            if ((int)$c['first_agent_at']) $frtA = (int)$c['first_agent_at'] - max($hand, $o);\n",
               "            // v1.2.126: respon-median — agent membalas tanpa serah terima & tanpa balasan bot sebelumnya: hitung dari pesan pertama (bukan 0)\n"
               "            $fa = (int)$c['first_agent_at']; $fb = (int)($c['first_bot_at'] ?? 0);\n"
               "            $hs = (($c['handover_reason'] ?? '') === 'agent_reply' && (!$fb || $fb > $fa)) ? $o : max($hand, $o);\n"
               "            if ($fa) $frtA = $fa - $hs;\n"
               "            $frtB = $fb ? $fb - $o : null;\n"
               "            $add($A['frt_bot'], $frtB);\n"
               "            foreach (['frt' => $frt, 'frt_bot' => $frtB, 'frt_agent' => $frtA] as $lk => $lv) if ($lv !== null && $lv >= 0) $L[$lk][] = (int)$lv;\n", rel)
    s = rep(s, "    foreach ($A as $k => $a) $avg[$k] = convAvg($a['sum'], $a['n']);\n",
               "    foreach ($A as $k => $a) $avg[$k] = convAvg($a['sum'], $a['n']);\n"
               "    $med = []; $mx = [];   // v1.2.126: respon-median\n"
               "    foreach ($L as $k => $v) {\n"
               "        sort($v); $n = count($v);\n"
               "        $med[$k] = $n ? (int)(($n % 2) ? $v[intdiv($n, 2)] : round(($v[$n / 2 - 1] + $v[$n / 2]) / 2)) : null;\n"
               "        $mx[$k] = $n ? (int)$v[$n - 1] : null;\n"
               "    }\n", rel)
    s = rep(s, "        'totals' => $T, 'avg' => $avg,\n",
               "        'totals' => $T, 'avg' => $avg, 'med' => $med, 'max' => $mx,   // v1.2.126: respon-median\n", rel)
    s = rep(s, "'totals' => $prev['totals'], 'avg' => $prev['avg'],",
               "'totals' => $prev['totals'], 'avg' => $prev['avg'], 'med' => $prev['med'],", rel)
    # --- sweep fallback
    s = rep(s, "/* ---------- SWEEP 2: Eskalasi ---------- */", SWEEP, rel)
    s = rep(s, "        try { $r['escalated'] = escalationSweep($s); } catch (\\Throwable $e) { $r['escalated'] = []; $r['err_escalation'] = $e->getMessage(); }\n",
               "        try { $r['escalated'] = escalationSweep($s); } catch (\\Throwable $e) { $r['escalated'] = []; $r['err_escalation'] = $e->getMessage(); }\n"
               "        try { $hfr = handoverFallbackSweep($s); if ($hfr) $r['handover_fallback'] = $hfr; } catch (\\Throwable $e) { $r['err_handover_fallback'] = $e->getMessage(); }   // v1.2.126: respon-median\n", rel)
    # idle sweep: jangan kembalikan diam-diam bila fallback aktif & tamu masih menunggu
    s = rep(s, "    if (deiIsManual()) return 0;          // v1.2.58: tidak ada bot untuk dikembalikan\n",
               "    if (deiIsManual()) return 0;          // v1.2.58: tidak ada bot untuk dikembalikan\n"
               "    $hfCs = null;   // v1.2.126: respon-median — fallback aktif: tamu yang masih menunggu ditangani handoverFallbackSweep (dengan pesan)\n"
               "    try { if (deiHfConf(getSettings())['enabled']) $hfCs = convStateReadAll(); } catch (\\Throwable $e) { $hfCs = null; }\n", rel)
    s = rep(s, "        if (!empty($claims[$k])) continue;                     // masih dipegang agent\n",
               "        if (!empty($claims[$k])) continue;                     // masih dipegang agent\n"
               "        if (is_array($hfCs) && is_array($hfCs[$k] ?? null) && deiHfPending($hfCs[$k], $now)) continue;   // v1.2.126\n", rel)
    # simpan pengaturan
    s = rep(s, "                $merged['ai_limit'] = deiMergeSettings($current['ai_limit'] ?? [], $incoming['ai_limit']);\n            }\n",
               "                $merged['ai_limit'] = deiMergeSettings($current['ai_limit'] ?? [], $incoming['ai_limit']);\n            }\n"
               "            if (isset($incoming['handover_fallback']) && is_array($incoming['handover_fallback'])) {   // v1.2.126: respon-median\n"
               "                $merged['handover_fallback'] = deiMergeSettings($current['handover_fallback'] ?? [], $incoming['handover_fallback']);\n"
               "            }\n", rel)
    s = rep(s, "        if (isset($merged['ai_limit']) && is_array($merged['ai_limit'])) $merged['ai_limit'] = deiAiLimitConf($merged);   // v1.2.97: batas-ai\n",
               "        if (isset($merged['ai_limit']) && is_array($merged['ai_limit'])) $merged['ai_limit'] = deiAiLimitConf($merged);   // v1.2.97: batas-ai\n"
               "        if (isset($merged['handover_fallback']) && is_array($merged['handover_fallback'])) $merged['handover_fallback'] = deiHfConf($merged);   // v1.2.126\n", rel)
    return s

CARD = """      <!-- v1.2.126: respon-median — kembali ke bot bila agent tidak membalas -->
      <div class="card"><h3>Kembali ke Bot bila Agent Tidak Membalas</h3>
        <div class="desc">Chat yang sudah diserahkan ke agent (kata kunci handoff, batas balasan AI, AI gagal) tapi <b>belum di-claim dan belum dibalas</b> selama waktu ini: nomor kembali ke bot dan tamu menerima pesan di bawah, supaya tidak menunggu tanpa jawaban. Tidak berlaku di Mode Manual dan untuk chat yang sedang dipegang agent.</div>
        <div class="toggle-row"><div><div class="tt">Aktifkan</div><div class="help">Tanpa ini nomor tetap kembali ke bot setelah 1 jam, tetapi diam-diam — tamu baru dijawab bila ia menulis lagi.</div></div><label class="switch"><input type="checkbox" id="hf_enabled"><span class="sl"></span></label></div>
        <div class="grid2">
          <div class="row"><label class="fl">Tunggu agent (menit)</label><input type="number" id="hf_minutes" min="5" max="240" step="1" value="15"><div class="help">5–240. Saran 15.</div></div>
        </div>
        <div class="row"><label class="fl">Pesan ke tamu</label><textarea id="hf_text" rows="2" placeholder="Mohon maaf membuat Anda menunggu 🙏 Tim kami belum sempat membalas. Sementara itu asisten virtual kami siap membantu — silakan sampaikan kembali pertanyaan Anda di sini."></textarea><div class="help">Kosongkan untuk memakai pesan bawaan (otomatis bahasa Inggris untuk tamu berbahasa Inggris). Admin juga diberi tahu lewat Telegram bila aktif.</div></div>
      </div>

      <!-- v1.2.96: jeda-balasan -->"""

def f_html(s, rel):
    s = rep(s, "      <!-- v1.2.96: jeda-balasan -->", CARD, rel)
    s = rep(s, '<script src="app.js?v=1.2.117"></script><!-- v1.2.117: filter-lead-rating -->',
               '<script src="app.js?v=1.2.126"></script><!-- v1.2.126: respon-median -->', rel)
    return s

def f_js(s, rel):
    s = rep(s, "    var dt = function (k) { return svDelta(A[k], PA[k], true, true); };\n",
               "    var dt = function (k) { return svDelta(A[k], PA[k], true, true); };\n"
               "    // v1.2.126: respon-median — median jadi angka utama (tidak terseret satu-dua chat sangat lama)\n"
               "    var M = r.med || {}, X = r.max || {}, PM = r.prev.med || {};\n"
               "    var dtm = function (k) { return svDelta(M[k], PM[k], true, true); };\n"
               "    var subm = function (pre, k) { return pre + 'rata-rata ' + svDur(A[k]) + (X[k] != null && X[k] > (M[k] || 0) ? ' · terlama ' + svDur(X[k]) : ''); };\n", rel)
    s = rep(s, "      svCard('Respon Pertama', svDur(A.frt), 'bot atau agent', dt('frt'), 'Rata-rata jeda dari pesan pertama pelanggan sampai balasan pertama.') +\n"
               "      svCard('Respon Pertama Agent', svDur(A.frt_agent), 'sejak diserahkan ke agent', dt('frt_agent'), 'Rata-rata jeda dari diserahkan ke manusia sampai balasan pertama agent.') +\n",
               "      svCard('Respon Pertama Bot', svDur(M.frt_bot), subm('median · ', 'frt_bot'), dtm('frt_bot'), 'Median jeda dari pesan pertama pelanggan sampai balasan pertama bot. Median = nilai tengah, tidak terseret satu-dua chat yang sangat lama; rata-rata dan terlama di bawahnya.') +\n"
               "      svCard('Respon Pertama Agent', svDur(M.frt_agent), subm('median sejak diserahkan · ', 'frt_agent'), dtm('frt_agent'), 'Median jeda dari diserahkan ke manusia sampai balasan pertama agent (agent membalas tanpa serah terima: dari pesan pertama pelanggan).') +\n", rel)
    s = rep(s, "      $('#al_text').value = al.text || '';\n",
               "      $('#al_text').value = al.text || '';\n"
               "      var hf = res.settings.handover_fallback || {};   // v1.2.126: respon-median\n"
               "      if ($('#hf_enabled')) { $('#hf_enabled').checked = hf.enabled === true; $('#hf_minutes').value = hf.minutes || 15; $('#hf_text').value = hf.text || ''; }\n", rel)
    s = rep(s, "      ai_limit: { max: Math.max(0, Math.min(50, Math.round(+$('#al_max').value || 0))), text: $('#al_text').value.trim() },   // v1.2.97: batas-ai\n",
               "      ai_limit: { max: Math.max(0, Math.min(50, Math.round(+$('#al_max').value || 0))), text: $('#al_text').value.trim() },   // v1.2.97: batas-ai\n"
               "      handover_fallback: $('#hf_enabled') ? { enabled: $('#hf_enabled').checked, minutes: Math.max(5, Math.min(240, Math.round(+$('#hf_minutes').value || 15))), text: $('#hf_text').value.trim() } : undefined,   // v1.2.126: respon-median\n", rel)
    return s

patch('api/index.php', f_api)
patch('dashboard/chatbot-ai/index.html', f_html)
patch('dashboard/chatbot-ai/app.js', f_js)
print('selesai')
