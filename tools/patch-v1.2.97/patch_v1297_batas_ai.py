#!/usr/bin/env python3
"""v1.2.97 — Batas balasan AI per percakapan WhatsApp sebelum diserahkan ke agent (mis. 5 bubble).
Setelah AI membalas N kali, pesan berikutnya tidak dijawab AI: nomor pindah ke mode manusia
(notifikasi + eskalasi seperti handoff biasa), opsional kirim pesan serah terima sekali.
Ikut aturan lama: tanpa agent 1 jam -> kembali ke bot. Hitungan direset tiap nomor masuk mode
manusia (handoff apa pun), saat agent membalas, dan saat percakapan baru (tamu diam > 24 jam).
Pemakaian: python3 patch_v1297_batas_ai.py <root dei-tenant>   (idempoten; backup *.bak-v1297-*)
Butuh v1.2.96 sudah terpasang."""
import sys, os, time, shutil
TEN = sys.argv[1]
STAMP = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.97: batas-ai'

def patch(root, rel, pairs):
    p = os.path.join(root, rel)
    s = open(p, encoding='utf-8').read()
    if MARK in s: print('sudah dipatch:', rel); return
    if 'v1.2.96: mengetik' not in s: sys.exit('GAGAL: v1.2.96 belum terpasang di ' + rel)
    for old, new in pairs:
        n = s.count(old)
        if n != 1: sys.exit(f'GAGAL {rel}: anchor {n}x:\n{old[:200]}')
        s = s.replace(old, new)
    shutil.copy2(p, p + '.bak-v1297-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

PHP_FUNCS = r'''/* v1.2.97: batas-ai — BATAS BALASAN AI per percakapan WhatsApp.
 * settings.ai_limit = { max: 0 (mati) .. 50, text: pesan serah terima (kosong = tidak dikirim) }
 * Hitungan = conv-state[nomor].bot_n (naik di convReply('bot')). */
function deiAiLimitConf($s = null) {
    if ($s === null) $s = getSettings();
    $a = is_array($s['ai_limit'] ?? null) ? $s['ai_limit'] : [];
    return [
        'max'  => max(0, min(50, (int)($a['max'] ?? 0))),
        'text' => mb_substr(trim((string)($a['text'] ?? '')), 0, 500),
    ];
}
function convBotCount($num) {
    $num = waNormNum($num);
    if ($num === '') return 0;
    try {
        return (int)convStateMutate(function (&$all) use ($num) { return (int)($all[$num]['bot_n'] ?? 0); }, $num);
    } catch (\Throwable $e) { error_log('convBotCount: ' . $e->getMessage()); return 0; }
}
function convBotReset($num) {
    $num = waNormNum($num);
    if ($num === '') return;
    try {
        convStateMutate(function (&$all) use ($num) { if (isset($all[$num]) && is_array($all[$num])) $all[$num]['bot_n'] = 0; }, $num);
    } catch (\Throwable $e) { error_log('convBotReset: ' . $e->getMessage()); }
}
'''

OLD_HUMAN = '''    if ($mode === 'human') {
        // Admin is handling this number — record, notify, do NOT auto-reply.
        if ($keepCtx) {
            $history = waLoadHistory($from);
            $history[] = ['role' => 'user', 'content' => $text];
            waSaveHistory($from, $history);
        }
        logPrepend(array_merge($logBase, ['a' => '', 'awaiting' => true]), $logLimit);
        tgNotify($s, "\\xF0\\x9F\\x93\\xA9 [WhatsApp] " . $from . ":\\n\\"" . $text . "\\"\\n\\xF0\\x9F\\x99\\x8B menunggu admin");
'''
NEW_HUMAN = '''    if ($mode === 'human') {
        // Admin is handling this number — record, notify, do NOT auto-reply.
        $deiAiLimA = '';   // v1.2.97: batas-ai — pesan serah terima (sekali, saat batas tercapai)
        if ($deiAiLimitHit && $deiAiLim['text'] !== '' && waSend($wa, $from, $deiAiLim['text'])) $deiAiLimA = $deiAiLim['text'];
        if ($keepCtx) {
            $history = waLoadHistory($from);
            $history[] = ['role' => 'user', 'content' => $text];
            if ($deiAiLimA !== '') $history[] = ['role' => 'assistant', 'content' => $deiAiLimA];
            waSaveHistory($from, $history);
        }
        logPrepend(array_merge($logBase, ['a' => $deiAiLimA, 'awaiting' => true], $deiAiLimitHit ? ['ai_limit' => true] : []), $logLimit);
        tgNotify($s, "\\xF0\\x9F\\x93\\xA9 [WhatsApp] " . $from . ":\\n\\"" . $text . "\\"\\n\\xF0\\x9F\\x99\\x8B "
            . ($deiAiLimitHit ? 'batas ' . $deiAiLim['max'] . ' balasan AI tercapai — menunggu admin' : 'menunggu admin'));
'''

patch(TEN, 'api/index.php', [
    ("define('DEI_VERSION', 'v1.2.96');", "define('DEI_VERSION', 'v1.2.97');"),
    ("// Pesan sistem ke satu nomor maks sekali per $ttl detik.",
     PHP_FUNCS + "// Pesan sistem ke satu nomor maks sekali per $ttl detik."),
    # hitung balasan bot; agent membalas = reset
    ("            $st['closing_sent_at'] = 0;\n            $all[$num] = $st;\n            return $inc;\n",
     "            $st['closing_sent_at'] = 0;\n"
     "            if ($who === 'bot') $st['bot_n'] = (int)($st['bot_n'] ?? 0) + 1;   // v1.2.97: batas-ai\n"
     "            elseif ($who === 'agent') $st['bot_n'] = 0;\n"
     "            $all[$num] = $st;\n            return $inc;\n"),
    # percakapan baru (tamu diam > 24 jam) = reset
    ("            $wasWaiting = !empty($st['guest_waiting_since']);\n",
     "            if ((int)($st['last_at'] ?? 0) < $now - 86400) $st['bot_n'] = 0;   // v1.2.97: batas-ai\n"
     "            $wasWaiting = !empty($st['guest_waiting_since']);\n"),
    # masuk mode manusia lewat jalur apa pun = reset
    ("function waSetMode($from, $mode) {\n    return deiWithLock('wa-modes', function () use ($from, $mode) { return waSetMode_nolock($from, $mode); });\n}\n",
     "function waSetMode($from, $mode) {\n    $r = deiWithLock('wa-modes', function () use ($from, $mode) { return waSetMode_nolock($from, $mode); });\n"
     "    if ($mode === 'human') convBotReset($from);   // v1.2.97: batas-ai — kembali ke bot nanti mulai dari nol\n"
     "    return $r;\n}\n"),
    # pemicu serah terima
    ("    if ($mode === 'bot' && !empty($ho['enabled']) && waMatchHandoff($text, $ho['keywords'] ?? [])) {\n        waSetMode($from, 'human');\n        $mode = 'human';\n    }\n",
     "    if ($mode === 'bot' && !empty($ho['enabled']) && waMatchHandoff($text, $ho['keywords'] ?? [])) {\n        waSetMode($from, 'human');\n        $mode = 'human';\n    }\n"
     "    // v1.2.97: batas-ai — AI sudah membalas N kali: serahkan ke agent (ucapan penutup & stiker tidak memicu)\n"
     "    $deiAiLim = deiAiLimitConf($s); $deiAiLimitHit = false;\n"
     "    if ($mode === 'bot' && $deiAiLim['max'] > 0 && !deiIsManual($s) && empty($metaInfo['_no_reply'])\n"
     "        && !deiIsClosingPhrase($text) && convBotCount($from) >= $deiAiLim['max']) {\n"
     "        waSetMode($from, 'human');\n        $mode = 'human';\n        $deiAiLimitHit = true;\n    }\n"),
    (OLD_HUMAN, NEW_HUMAN),
    # simpan (Admin)
    ("            if (isset($incoming['reply_delay']) && is_array($incoming['reply_delay'])) {   // v1.2.96: jeda-balasan\n",
     "            if (isset($incoming['ai_limit']) && is_array($incoming['ai_limit'])) {   // v1.2.97: batas-ai\n"
     "                $merged['ai_limit'] = deiMergeSettings($current['ai_limit'] ?? [], $incoming['ai_limit']);\n"
     "            }\n"
     "            if (isset($incoming['reply_delay']) && is_array($incoming['reply_delay'])) {   // v1.2.96: jeda-balasan\n"),
    ("        if (isset($merged['reply_delay']) && is_array($merged['reply_delay'])) {   // v1.2.96: jeda-balasan\n",
     "        if (isset($merged['ai_limit']) && is_array($merged['ai_limit'])) $merged['ai_limit'] = deiAiLimitConf($merged);   // v1.2.97: batas-ai\n"
     "        if (isset($merged['reply_delay']) && is_array($merged['reply_delay'])) {   // v1.2.96: jeda-balasan\n"),
])

HTML_CARD = '''      <!-- v1.2.97: batas-ai -->
      <div class="card"><h3>Batas Balasan AI (WhatsApp)</h3>
        <div class="desc">Setelah AI membalas sekian kali dalam satu percakapan, pesan berikutnya <b>tidak dijawab AI</b>: nomor pindah ke mode manusia dan menunggu agent (notifikasi &amp; eskalasi berjalan seperti handoff biasa). Bila 1 jam tidak ada agent yang membalas, nomor kembali ke bot dan hitungan mulai dari nol.</div>
        <div class="grid2">
          <div class="row"><label class="fl">Maks balasan AI per percakapan</label><input type="number" id="al_max" min="0" max="50" step="1" value="0"><div class="help">0 = tidak dibatasi. Contoh: 5.</div></div>
        </div>
        <div class="row"><label class="fl">Pesan serah terima (opsional)</label><textarea id="al_text" rows="2" placeholder="Terima kasih, pertanyaan Anda akan dilanjutkan oleh tim kami. Mohon tunggu sebentar ya 🙏"></textarea><div class="help">Dikirim sekali saat batas tercapai. Kosongkan bila tidak perlu.</div></div>
        <div class="help">Hitungan direset saat agent membalas atau mengambil alih, dan saat tamu kembali setelah 24 jam. Ucapan penutup ("ok makasih") dan stiker tidak memicu serah terima.</div>
      </div>

'''
patch(TEN, 'dashboard/chatbot-ai/index.html', [
    ('      <!-- v1.2.96: jeda-balasan -->', HTML_CARD + '      <!-- v1.2.96: jeda-balasan -->'),
])

patch(TEN, 'dashboard/chatbot-ai/app.js', [
    ("      rdLoad(res.settings.reply_delay);   // v1.2.96: jeda-balasan\n",
     "      rdLoad(res.settings.reply_delay);   // v1.2.96: jeda-balasan\n"
     "      var al = res.settings.ai_limit || {};   // v1.2.97: batas-ai\n"
     "      $('#al_max').value = al.max || 0;\n"
     "      $('#al_text').value = al.text || '';\n"),
    ("      reply_delay: rd_,   // v1.2.96: jeda-balasan\n",
     "      reply_delay: rd_,   // v1.2.96: jeda-balasan\n"
     "      ai_limit: { max: Math.max(0, Math.min(50, Math.round(+$('#al_max').value || 0))), text: $('#al_text').value.trim() },   // v1.2.97: batas-ai\n"),
])
print('selesai')
