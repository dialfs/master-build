#!/usr/bin/env python3
"""v1.2.89 — HEMAT PESAN WA (Meta menagih per pesan keluar sejak 1 Okt 2026).
  1. Debounce juga di mode file (shared hosting, tanpa Redis): bubble beruntun satu nomor
     ditahan N detik (bawaan 3) lalu dijawab SEKALI. Hanya bila webhook bisa ack lebih dulu
     (PHP-FPM/LiteSpeed). Mode Redis tetap memakai server.php 'debounce_sec' bila diisi.
  2. Ucapan penutup ("ok makasih", 👍) setelah jawaban bot yang bukan pertanyaan -> tidak dibalas.
  3. Instruksi prompt "satu jawaban tuntas" khusus kanal WhatsApp (ditaruh SETELAH titik cache).
  4. Pesan sistem (terlalu banyak pesan / hanya teks / kuota / lisensi) maks sekali per periode per nomor.
  5. Penghitung 'saved' (bubble yang tidak jadi dikirim) di wa-out + kartu dashboard.
  Pengaturan: settings.wa_hemat {debounce_sec, skip_ack, prompt} — admin & super_admin.
Idempoten. Pakai: patch_v1289_hemat.py <dei-chatbot-ai>"""
import re, sys, pathlib
ROOT = pathlib.Path(sys.argv[1])

def patch(path, marker, edits, version=False):
    p = ROOT / path; A = p.read_text(encoding='utf-8')
    if marker in A: print(path, ': sudah terpasang'); return
    for old, new in edits:
        c = A.count(old)
        if c != 1: raise SystemExit(f'{path}: ANCHOR {c}x: {old[:90]!r}')
        A = A.replace(old, new)
    if version:
        A, n = re.subn(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.89');", A, count=1)
        if n != 1: raise SystemExit('DEI_VERSION tidak ketemu')
    p.write_text(A, encoding='utf-8'); print(path, ': OK')

API = []
# ---- penghitung 'saved'
API.append(("""        if (!isset($all[$m]) || !is_array($all[$m])) $all[$m] = ['service' => 0, 'template' => 0];
        $k = ($kind === 'template') ? 'template' : 'service';""",
"""        if (!isset($all[$m]) || !is_array($all[$m])) $all[$m] = ['service' => 0, 'template' => 0];
        $k = in_array($kind, ['template', 'saved'], true) ? $kind : 'service';   // v1.2.89: 'saved' = bubble yang tidak jadi dikirim"""))
API.append(("""    return ['service' => (int)($r['service'] ?? 0), 'template' => (int)($r['template'] ?? 0)];
}""",
"""    return ['service' => (int)($r['service'] ?? 0), 'template' => (int)($r['template'] ?? 0), 'saved' => (int)($r['saved'] ?? 0)];   // v1.2.89
}

/* v1.2.89: HEMAT PESAN WA. Sejak 1 Okt 2026 Meta menagih tiap service message yang
 * terkirim (lewat 1.000 gratis/nomor/bulan). settings.wa_hemat:
 *   debounce_sec (0-8, bawaan 3) — bubble beruntun satu nomor dijawab sekali
 *   skip_ack     (bawaan true)  — "ok makasih" setelah jawaban bot (bukan pertanyaan) tidak dibalas
 *   prompt       (bawaan true)  — instruksi "satu jawaban tuntas" untuk kanal WhatsApp */
function deiHematConf($s = null) {
    if ($s === null) $s = getSettings();
    $h = is_array($s['wa_hemat'] ?? null) ? $s['wa_hemat'] : [];
    return [
        'debounce_sec' => array_key_exists('debounce_sec', $h) ? max(0.0, min(8.0, (float)$h['debounce_sec'])) : 3.0,
        'skip_ack'     => !array_key_exists('skip_ack', $h) || !empty($h['skip_ack']),
        'prompt'       => !array_key_exists('prompt', $h) || !empty($h['prompt']),
    ];
}
// Pesan sistem ke satu nomor maks sekali per $ttl detik. true = boleh kirim sekarang (dan dicatat).
function deiSysOnce($num, $kind, $ttl) {
    $k = preg_replace('/\\D/', '', (string)$num) . ':' . $kind;
    try {
        return deiWithLock('sysonce', function () use ($k, $ttl) {
            $f = DATA_DIR . '/sys-once.json';
            $all = readJson($f, []);
            if (!is_array($all)) $all = [];
            $now = time();
            foreach ($all as $kk => $t) { if ((int)$t < $now - 86400) unset($all[$kk]); }
            if (isset($all[$k]) && (int)$all[$k] > $now - $ttl) return false;
            $all[$k] = $now;
            writeJson($f, $all);
            return true;
        });
    } catch (\\Throwable $e) { error_log('deiSysOnce: ' . $e->getMessage()); return true; }
}
// Instruksi gaya balasan WhatsApp. Ditempel di blok SETELAH titik cache supaya cache KB tetap utuh.
function deiHematPromptBlock() {
    return "=== GAYA BALASAN WHATSAPP (HEMAT PESAN) ===\\n"
         . "Setiap balasanmu dikirim sebagai SATU pesan WhatsApp dan setiap pesan berbiaya. Karena itu:\\n"
         . "- Jawab tuntas dalam satu balasan. Sertakan sekaligus info yang hampir pasti ditanyakan berikutnya (mis. harga + jadwal + cara pesan/link).\\n"
         . "- Bila perlu data dari pelanggan, tanyakan SEMUA yang dibutuhkan sekaligus dalam satu pesan, jangan satu per satu.\\n"
         . "- Jangan menutup dengan basa-basi yang memancing balasan tanpa isi (mis. \\"Ada lagi yang bisa dibantu?\\") kecuali memang perlu.\\n"
         . "- Tetap ringkas dan mudah dibaca.";
}"""))
# ---- debounce mode file
API.append(("""function deiDebounceSec() {
    return deiQueueRedis() ? max(0.0, min(5.0, (float)(deiServerConf()['debounce_sec'] ?? 0))) : 0.0;
}""",
"""function deiDebounceSec() {
    if (!deiQueueRedis()) return 0.0;
    // v1.2.89: server.php 'debounce_sec' menang; kalau tidak diisi pakai pengaturan Hemat Pesan
    $sc = deiServerConf();
    return max(0.0, min(5.0, array_key_exists('debounce_sec', $sc) ? (float)$sc['debounce_sec'] : deiHematConf()['debounce_sec']));
}
/* v1.2.89: DEBOUNCE MODE FILE (shared hosting, tanpa Redis). Tiap webhook mencatat pesannya
 * di data/.debounce/<nomor>.json lalu menunggu sampai nomor itu diam N detik (maks 8).
 * Hanya proses yang pesannya PALING AKHIR yang menjawab — semua teks digabung jadi satu.
 * Proses lain berhenti tanpa membalas: [null, []]. Butuh webhook yang sudah ack ke Meta. */
function deiDebounceFileCollect($s, $num, $wamid, $text) {
    if (deiQueueRedis() || $wamid === '') return [$text, []];
    $sec = deiHematConf($s)['debounce_sec'];
    if ($sec <= 0) return [$text, []];
    if (PHP_SAPI !== 'cli' && !function_exists('fastcgi_finish_request') && !function_exists('litespeed_finish_request')) return [$text, []];
    $k = preg_replace('/\\D/', '', (string)$num);
    if ($k === '') return [$text, []];
    $dir = DATA_DIR . '/.debounce';
    if (!is_dir($dir)) @mkdir($dir, 0755, true);
    $f = $dir . '/' . $k . '.json';
    $rw = function ($fn) use ($f, $k) {
        return deiWithLock('deb_' . $k, function () use ($f, $fn) {
            $items = is_file($f) ? json_decode((string)@file_get_contents($f), true) : [];
            if (!is_array($items)) $items = [];
            $batas = microtime(true) - 600;
            $items = array_values(array_filter($items, function ($it) use ($batas) { return is_array($it) && (float)($it['t'] ?? 0) > $batas; }));
            $res = $fn($items);
            if ($items) @file_put_contents($f, json_encode($items, JSON_UNESCAPED_UNICODE), LOCK_EX); else @unlink($f);
            return $res;
        });
    };
    try {
        $rw(function (&$items) use ($wamid, $text) { $items[] = ['id' => (string)$wamid, 'text' => $text, 't' => microtime(true)]; });
        $stop = microtime(true) + 8;
        while (microtime(true) < $stop) {
            $last = $rw(function (&$items) { $e = end($items); return $e ? (float)$e['t'] : 0.0; });
            $wait = $last + $sec - microtime(true);
            if ($wait <= 0) break;
            usleep((int)(min($wait, 0.5) * 1e6));
        }
        return $rw(function (&$items) use ($wamid) {
            $e = end($items);
            if (!$e || (string)$e['id'] !== (string)$wamid) return [null, []];   // ada pesan lebih baru -> dia yang menjawab
            $texts = []; $ids = [];
            foreach ($items as $it) {
                $id = (string)($it['id'] ?? '');
                if ($id === '' || isset($ids[$id])) continue;
                $ids[$id] = true;
                $t = trim((string)($it['text'] ?? ''));
                if ($t !== '') $texts[] = $t;
            }
            $items = [];
            return [implode("\\n", $texts), array_keys($ids)];
        });
    } catch (\\Throwable $e) {
        error_log('debounce file: ' . $e->getMessage());
        return [$text, []];
    }
}"""))
API.append(("""            waSend($wa, $from, 'Maaf, untuk saat ini saya hanya bisa membalas pesan teks.');
            return;
        }
        $text = trim($msg['text']['body'] ?? '');""",
"""            if (deiSysOnce($from, 'nontext', 1800)) waSend($wa, $from, 'Maaf, untuk saat ini saya hanya bisa membalas pesan teks.');
            else waOutCount('saved');   // v1.2.89
            return;
        }
        $text = trim($msg['text']['body'] ?? '');"""))
API.append(("""            list($text, $mergedIds) = deiDebounceCollect($from, $wamid, $text);
            if ($text === '') return;
        }""",
"""            if (deiQueueRedis()) {
                list($text, $mergedIds) = deiDebounceCollect($from, $wamid, $text);
            } else {
                list($text, $mergedIds) = deiDebounceFileCollect($s, $from, $wamid, $text);   // v1.2.89
                if ($text === null) { waOutCount('saved'); return; }   // digabung ke pesan berikutnya
            }
            if (count($mergedIds ?? []) > 1 && deiQueueRedis()) { for ($i = 1; $i < count($mergedIds); $i++) waOutCount('saved'); }
            if ($text === '') return;
        }"""))
# ---- pesan sistem dibatasi
API.append(("""    if (!deiIsManual($s) && !checkRateLimit('wa:' . $from, $limit)) {
        waSend($wa, $from, 'Anda mengirim terlalu banyak pesan. Mohon tunggu sebentar ya.');
        return;
    }""",
"""    if (!deiIsManual($s) && !checkRateLimit('wa:' . $from, $limit)) {
        if (deiSysOnce($from, 'ratelimit', 600)) waSend($wa, $from, 'Anda mengirim terlalu banyak pesan. Mohon tunggu sebentar ya.');
        else waOutCount('saved');   // v1.2.89
        return;
    }"""))
API.append(("""    // Bot mode — generate and send an automatic answer.
    // v1.1.3: license enforcement
    $lic = getLicenseStatus($s);
    if ($lic['status'] === 'suspended') {
        $answer = $lic['message'] ?: LIC_DEFAULT_SUSPEND_MSG;
        if (waSend($wa, $from, $answer)) convReply($from, 'system');   // v1.2.56""",
"""    // v1.2.89: ucapan penutup ("ok makasih", 👍) setelah jawaban bot yang bukan pertanyaan -> tidak dibalas
    $hemat = deiHematConf($s);
    if ($hemat['skip_ack'] && $keepCtx && trim($text) !== '' && deiIsClosingPhrase($text)) {
        $hAck = waLoadHistory($from);
        $lastT = end($hAck);
        $lastA = (is_array($lastT) && ($lastT['role'] ?? '') === 'assistant') ? rtrim((string)($lastT['content'] ?? '')) : '';
        if ($lastA !== '' && mb_strpos(mb_substr($lastA, -25), '?') === false) {
            $hAck[] = ['role' => 'user', 'content' => $text];
            waSaveHistory($from, $hAck);
            logPrepend(array_merge($logBase, ['a' => '', 'hemat' => 'ack']), $logLimit);
            waOutCount('saved');
            return;
        }
    }

    // Bot mode — generate and send an automatic answer.
    // v1.1.3: license enforcement
    $lic = getLicenseStatus($s);
    if ($lic['status'] === 'suspended') {
        $answer = $lic['message'] ?: LIC_DEFAULT_SUSPEND_MSG;
        if (!deiSysOnce($from, 'suspended', 21600)) { waOutCount('saved'); logPrepend(array_merge($logBase, ['a' => '', 'suspended' => true]), $logLimit); return; }   // v1.2.89
        if (waSend($wa, $from, $answer)) convReply($from, 'system');   // v1.2.56"""))
API.append(("""        $answer = $cap['message'] ?: CAP_DEFAULT_MSG;
        if (waSend($wa, $from, $answer)) convReply($from, 'system');   // v1.2.56""",
"""        $answer = $cap['message'] ?: CAP_DEFAULT_MSG;
        if (!deiSysOnce($from, 'cap', 21600)) { waOutCount('saved'); logPrepend(array_merge($logBase, ['a' => '', 'cap_reached' => true]), $logLimit); return; }   // v1.2.89
        if (waSend($wa, $from, $answer)) convReply($from, 'system');   // v1.2.56"""))
# ---- prompt khusus WA
API.append(("""    list($ok, $answer, $_kbUsed, $usage) = generateAnswer($s, $text, $history);""",
"""    list($ok, $answer, $_kbUsed, $usage) = generateAnswer($s, $text, $history, 'whatsapp');   // v1.2.89"""))
API.append(("""function generateAnswer($s, $message, $history = []) {""",
"""function generateAnswer($s, $message, $history = [], $channel = '') {"""))
API.append(("""    if ($deiRbBlk !== '') $deiPriceBlk = trim($deiPriceBlk . "\\n\\n" . $deiRbBlk);""",
"""    if ($deiRbBlk !== '') $deiPriceBlk = trim($deiPriceBlk . "\\n\\n" . $deiRbBlk);
    if ($channel === 'whatsapp' && deiHematConf($s)['prompt']) $deiPriceBlk = trim($deiPriceBlk . "\\n\\n" . deiHematPromptBlock());   // v1.2.89"""))
# ---- simpan pengaturan (admin)
API.append(("""            if (isset($incoming['escalation']) && is_array($incoming['escalation'])) {
                $escIn = $incoming['escalation'];""",
"""            if (isset($incoming['wa_hemat']) && is_array($incoming['wa_hemat'])) {   // v1.2.89
                $merged['wa_hemat'] = deiMergeSettings($current['wa_hemat'] ?? [], $incoming['wa_hemat']);
            }
            if (isset($incoming['escalation']) && is_array($incoming['escalation'])) {
                $escIn = $incoming['escalation'];"""))
API.append(("""                                            'service' => $o['service'], 'template' => $o['template'],""",
"""                                            'service' => $o['service'], 'template' => $o['template'], 'saved' => $o['saved'],   // v1.2.89"""))
patch('api/index.php', 'function deiHematConf(', API, version=True)

HTML = [("""      <div class="card"><h3>Eskalasi Darurat (Emergency Call)</h3>""",
"""      <!-- v1.2.89: HEMAT PESAN WA -->
      <div class="card"><h3>Hemat Pesan WhatsApp</h3>
        <div class="desc">Meta menagih tiap pesan yang dikirim bot/agent (lewat 1.000 gratis per nomor per bulan). Pengaturan ini mengurangi jumlah bubble tanpa mengurangi isi jawaban.</div>
        <div class="row"><label class="fl">Gabung pesan beruntun (detik)</label><input type="number" id="hm_debounce" min="0" max="8" step="1" value="3"><div class="help">Tamu yang mengetik beberapa bubble ("halo" · "mau tanya" · "harga ke Solo?") dijawab <b>sekali</b> setelah diam sekian detik. 0 = mati. Saran 3.</div></div>
        <div class="toggle-row"><div><div class="tt">Jangan balas ucapan penutup</div><div class="help">"ok makasih", "siap", 👍 setelah jawaban bot tidak dibalas lagi. Tetap dibalas bila bot sebelumnya mengajukan pertanyaan.</div></div><label class="switch"><input type="checkbox" id="hm_skip_ack"><span class="sl"></span></label></div>
        <div class="toggle-row"><div><div class="tt">Jawaban tuntas dalam satu pesan</div><div class="help">Bot diminta menjawab lengkap sekaligus dan menanyakan semua data yang perlu dalam satu pesan.</div></div><label class="switch"><input type="checkbox" id="hm_prompt"><span class="sl"></span></label></div>
        <div class="help">Pesan sistem (terlalu banyak pesan, hanya bisa teks, kuota habis) kini dikirim maksimal sekali per periode per nomor.</div>
      </div>

      <div class="card"><h3>Eskalasi Darurat (Emergency Call)</h3>""")]
patch('dashboard/chatbot-ai/index.html', 'id="hm_debounce"', HTML)

JS = [("""      var ac = res.settings.auto_closing || {}, ec = res.settings.escalation || {};""",
"""      var ac = res.settings.auto_closing || {}, ec = res.settings.escalation || {};
      var hm = res.settings.wa_hemat || {};   // v1.2.89
      $('#hm_debounce').value = (hm.debounce_sec === undefined || hm.debounce_sec === null) ? 3 : hm.debounce_sec;
      $('#hm_skip_ack').checked = hm.skip_ack !== false;
      $('#hm_prompt').checked = hm.prompt !== false;"""),
("""      escalation: esc_
    } };""",
"""      escalation: esc_,
      wa_hemat: {   // v1.2.89
        debounce_sec: Math.max(0, Math.min(8, Math.round(+$('#hm_debounce').value || 0))),
        skip_ack: $('#hm_skip_ack').checked,
        prompt: $('#hm_prompt').checked
      }
    } };"""),
("""          if (tp > 0) note += ' · ' + tp + ' template (berbayar)';""",
"""          if (tp > 0) note += ' · ' + tp + ' template (berbayar)';
          if (wo.saved > 0) note += ' · ' + wo.saved + ' dihemat';   // v1.2.89""")]
patch('dashboard/chatbot-ai/app.js', 'wa_hemat: {', JS)
