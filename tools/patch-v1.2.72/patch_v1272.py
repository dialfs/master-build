#!/usr/bin/env python3
"""v1.2.72 — khusus server sendiri (aktif hanya lewat data/server.php):
  * debounce_sec   : gabung bubble beruntun satu nomor jadi satu panggilan AI (mode antrean)
  * ai_fallback    : model cadangan kalau AI utama gagal
  * ai_fail_handoff: kalau semua AI gagal -> nomor dialihkan ke agent + notifikasi
  * wa_queue_status: jujur saat Redis tidak terjangkau
Tanpa kunci-kunci itu perilaku = v1.2.71. Idempoten. Pakai: patch_v1272.py <api/index.php>"""
import re, sys, pathlib

P = pathlib.Path(sys.argv[1])
src = P.read_text(encoding='utf-8')
if 'function deiDebounceCollect(' in src:
    print('sudah terpasang'); sys.exit(0)
if 'function deiServerConf()' not in src:
    raise SystemExit('butuh v1.2.71 dulu')

def rep(old, new, count=1):
    global src
    n = src.count(old)
    if n != count:
        raise SystemExit(f'ANCHOR {n}x (harus {count}): {old[:90]!r}')
    src = src.replace(old, new)

src = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.72');", src, count=1)

# 1. Fallback AI di satu pintu callClaude()
rep("function callClaude($settings, $systemBlocks, $messages) {\n",
r"""/* v1.2.72: model cadangan (server sendiri). data/server.php:
 *   'ai_fallback' => ['provider' => 'openrouter', 'model' => 'anthropic/claude-haiku-4.5']
 * Kalau AI utama gagal, dicoba sekali dengan model cadangan. Tanpa kunci itu = perilaku lama. */
function callClaude($settings, $systemBlocks, $messages) {
    $r = callClaudeOnce($settings, $systemBlocks, $messages);
    if (!empty($r[0])) return $r;
    $fb = deiServerConf()['ai_fallback'] ?? null;
    if (!is_array($fb) || empty($fb['model'])) return $r;
    $s2 = $settings;
    $prov = (string)($fb['provider'] ?? ($settings['api']['provider'] ?? 'anthropic'));
    if ($prov === 'openrouter') { $s2['api']['provider'] = 'openrouter'; $s2['api']['openrouter_model'] = (string)$fb['model']; }
    else { $s2['api']['provider'] = 'anthropic'; $s2['api']['model'] = (string)$fb['model']; }
    error_log('AI utama gagal (' . mb_substr((string)($r[1] ?? ''), 0, 120) . ') -> coba cadangan ' . $fb['model']);
    $r2 = callClaudeOnce($s2, $systemBlocks, $messages);
    if (!empty($r2[0])) { $GLOBALS['dei_ai_fallback_used'] = (string)$fb['model']; return $r2; }
    return $r;
}
function callClaudeOnce($settings, $systemBlocks, $messages) {
""")

# 2. Semua AI gagal -> alihkan ke agent (opsional)
rep("""    if (!$ok || trim($answer) === '') {
        $answer = 'Maaf, saya sedang mengalami gangguan. Silakan coba lagi sebentar lagi.';
        $deiAiError = true;
    } else {""",
"""    if (!$ok || trim($answer) === '') {
        $answer = 'Maaf, saya sedang mengalami gangguan. Silakan coba lagi sebentar lagi.';
        $deiAiError = true;
        // v1.2.72 (server sendiri): 'ai_fail_handoff' => true -> agent yang lanjut, pelanggan tidak disuruh mencoba lagi
        if (!empty(deiServerConf()['ai_fail_handoff'])) {
            $answer = (string)(deiServerConf()['ai_fail_text'] ?? 'Terima kasih, pesan Anda sudah kami terima. Tim kami akan segera membalas.');
            try { waSetMode($from, 'human'); } catch (\\Throwable $e) { error_log('ai_fail_handoff: ' . $e->getMessage()); }
            tgNotify($s, "\\xE2\\x9A\\xA0\\xEF\\xB8\\x8F [WhatsApp] AI gagal menjawab +" . $from . " \\xE2\\x80\\x94 dialihkan ke agent:\\n\\"" . $text . "\\"");
        }
    } else {""")

# 3. Debounce: buffer per nomor diisi webhook, dikuras worker
rep("""            try {
                deiRedis()->lPush('q:wa', json_encode(['raw' => $raw, 'at' => time(), 'try' => 0]));""",
"""            try {
                deiDebounceBuffer(json_decode($raw, true));   // v1.2.72: catat teks per nomor sebelum diantre
                deiRedis()->lPush('q:wa', json_encode(['raw' => $raw, 'at' => time(), 'try' => 0]));""")

rep("""        $text = trim($msg['text']['body'] ?? '');
        if ($text === '') return;
        // v1.2.36: alur pemrosesan dipindah ke fungsi bersama
        waProcessIncoming($s, $wa, $from, $text, $deiWaName, $metadata);
    } finally {
        // Ditandai juga saat gagal di tengah jalan: lebih baik tidak dibalas ganda.
        if ($wamid !== '') waMsgMarkSeen($wamid);
    }""",
"""        $text = trim($msg['text']['body'] ?? '');
        if ($text === '') return;
        // v1.2.72: bubble beruntun dari nomor ini digabung (mode antrean + debounce_sec)
        if (!deiIsManual($s) && waGetMode($from) === 'bot') {
            list($text, $mergedIds) = deiDebounceCollect($from, $wamid, $text);
            if ($text === '') return;
        }
        // v1.2.36: alur pemrosesan dipindah ke fungsi bersama
        waProcessIncoming($s, $wa, $from, $text, $deiWaName, $metadata);
    } finally {
        // Ditandai juga saat gagal di tengah jalan: lebih baik tidak dibalas ganda.
        if ($wamid !== '') waMsgMarkSeen($wamid);
        foreach (($mergedIds ?? []) as $mid) { if ($mid !== $wamid) waMsgMarkSeen($mid); }   // v1.2.72
    }""")

rep("/* v1.2.71: satu pesan masuk dari Meta.",
r"""/* v1.2.72: DEBOUNCE (server sendiri, data/server.php 'debounce_sec' => 2).
 * Webhook mencatat teks tiap pesan ke buf:wa:<nomor> + waktu pesan terakhir.
 * Worker yang memegang kunci nomor menunggu sampai nomor itu diam debounce_sec
 * (maks 8 dtk), lalu menguras buffer: semua bubble jadi SATU panggilan AI.
 * Job pesan lain yang ikut tergabung nanti dilewati karena wamid-nya sudah ditandai. */
function deiDebounceSec() {
    return deiQueueRedis() ? max(0.0, min(5.0, (float)(deiServerConf()['debounce_sec'] ?? 0))) : 0.0;
}
function deiDebounceBuffer($payload) {
    if (deiDebounceSec() <= 0 || !is_array($payload)) return;
    try {
        $r = deiRedis();
        foreach (($payload['entry'] ?? []) as $en) foreach (($en['changes'] ?? []) as $ch) foreach (($ch['value']['messages'] ?? []) as $m) {
            if (($m['type'] ?? '') !== 'text') continue;
            $num = preg_replace('/\D/', '', (string)($m['from'] ?? ''));
            $txt = trim((string)($m['text']['body'] ?? ''));
            if ($num === '' || $txt === '') continue;
            $r->rPush('buf:wa:' . $num, json_encode(['id' => (string)($m['id'] ?? ''), 'text' => $txt], JSON_UNESCAPED_UNICODE));
            $r->expire('buf:wa:' . $num, 600);
            $r->set('last:wa:' . $num, (string)microtime(true), ['ex' => 600]);
        }
    } catch (\Throwable $e) { error_log('debounce buffer: ' . $e->getMessage()); }
}
// Kembalikan [teks gabungan, wamid yang ikut digabung]. Tanpa debounce: [teks sendiri, []].
function deiDebounceCollect($num, $wamid, $text) {
    $sec = deiDebounceSec();
    if ($sec <= 0) return [$text, []];
    try {
        $r = deiRedis();
        $k = preg_replace('/\D/', '', (string)$num);
        $stop = microtime(true) + 8;
        while (true) {
            $wait = (float)$r->get('last:wa:' . $k) + $sec - microtime(true);
            if ($wait <= 0 || microtime(true) > $stop) break;
            usleep((int)(min($wait, 0.5) * 1e6));
        }
        $res = $r->multi()->lRange('buf:wa:' . $k, 0, -1)->del('buf:wa:' . $k)->exec();
        $texts = []; $ids = [];
        foreach ((array)($res[0] ?? []) as $it) {
            $j = json_decode((string)$it, true);
            $id = (string)($j['id'] ?? '');
            if ($id === '' || isset($ids[$id])) continue;
            if ($id !== $wamid && waMsgSeen($id)) continue;          // sudah diproses sendiri sebelumnya
            $ids[$id] = true;
            $texts[] = trim((string)($j['text'] ?? ''));
        }
        if (!isset($ids[(string)$wamid])) { array_unshift($texts, $text); $ids[(string)$wamid] = true; }
        $texts = array_values(array_filter($texts, 'strlen'));
        return [implode("\n", $texts), array_keys($ids)];
    } catch (\Throwable $e) {
        error_log('debounce: ' . $e->getMessage());
        return [$text, []];
    }
}

/* v1.2.71: satu pesan masuk dari Meta.""")

# 4. Status antrean jujur
rep("""        $out = ['ok' => true, 'version' => DEI_VERSION, 'storage' => deiServerConf()['storage'], 'queue' => deiServerConf()['queue']];
        if (deiQueueRedis()) {""",
"""        $out = ['ok' => true, 'version' => DEI_VERSION, 'storage' => deiServerConf()['storage'], 'queue' => deiServerConf()['queue'],
                'queue_active' => deiQueueRedis(), 'debounce_sec' => deiDebounceSec(),
                'ai_fallback' => (string)(deiServerConf()['ai_fallback']['model'] ?? ''), 'ai_fail_handoff' => !empty(deiServerConf()['ai_fail_handoff'])];   // v1.2.72
        if (deiServerConf()['queue'] === 'redis' && !deiQueueRedis()) {
            $out['ok'] = false;
            $out['warning'] = 'Redis tidak terjangkau: antrean TIDAK aktif, pesan diproses langsung oleh webhook.';
        }
        if (deiQueueRedis()) {""")

P.write_text(src, encoding='utf-8')
print('OK v1.2.72 terpasang')
