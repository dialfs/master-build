#!/usr/bin/env python3
"""v1.2.102: closing-sekali — (1) auto-closing maks 1x per 12 jam per nomor, (2) ucapan penutup/penolakan
lebih luas ("trimakasih", "tks", "blm kak", "tidak ada"), (3) AI tidak bertanya "ada lagi?" saat tamu pamit,
(4) riwayat ke AI dirapikan (tak diawali assistant, peran berurutan digabung), (5) alasan gagal AI dicatat
di log + coba ulang sekali untuk galat sementara. Idempoten. Pakai: patch_v12102_closing.py <dei-tenant>"""
import sys, os, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
F = T + '/api/index.php'
s = open(F, encoding='utf-8').read()
if 'v1.2.102: closing-sekali' in s:
    print('sudah terpasang'); sys.exit(0)
shutil.copy2(F, F + '.bak-v12102-' + time.strftime('%Y%m%d-%H%M%S'))

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, old[:80])
    s = s.replace(old, new)

rep("define('DEI_VERSION', 'v1.2.101');", "define('DEI_VERSION', 'v1.2.102');")

# (2) ucapan penutup lebih luas
rep("""    $inti = '(ok|oke|okey|okay|okeh|okee+|okok|sip|siap|baik|baiklah|noted|mantap|mantab|thanks?|thank you|thankyou|thx|tq|ty|makasih|makasi|maksih|trims|terima ?kasih|terimakasih|sama ?sama)';
    $ekor = '( (ya|yah|kak|ka|kk|min|mas|mbak|mba|pak|bu|bang|banyak|sekali|so much|a lot|very much|' . $inti . '))*';
    return (bool)preg_match('/^' . $inti . $ekor . '$/u', $t);
}""", """    $inti = '(ok|oke|okey|okay|okeh|okee+|okok|sip|siap|baik|baiklah|noted|mantap|mantab|thanks?|thank you|thankyou|thx|tq|ty|tks|tengkyu|makasih|makasi|maksih|makasii+|trims|trimakasih|trimakasi|terimakasih|terima ?kasih|terima ?kasi|sama ?sama|suwun|nuhun|hatur nuhun)';
    $ekor = '( (ya|yah|yaa+|kak|ka|kk|kakak|min|mas|mbak|mba|pak|bu|bang|banyak|sekali|so much|a lot|very much|' . $inti . '))*';
    if (preg_match('/^' . $inti . $ekor . '$/u', $t)) return true;
    // v1.2.102: closing-sekali — jawaban "tidak ada / belum" (biasanya atas pertanyaan "ada lagi?")
    $tidak = '(sementara|smntara|smtr|sementara ini|untuk sementara|utk sementara|udah|sudah|sdh|udh|itu|itu aja|itu saja|cukup|cukup itu)? ?(belum|blm|blom|belom|tidak|tdk|gak|ga|gk|nggak|ngga|enggak|engga|no|nope|nothing|cukup|sudah|udah|sdh|udh|aman|enough)( (ada|ad|dulu|dl|lagi|lg|itu|aja|saja|kok|sih|cukup|jelas|paham|tau|tahu|thanks|' . $inti . '|ya|yah|kak|ka|kk|kakak|min|mas|mbak|mba|pak|bu|bang))*';
    if (preg_match('/^' . $tidak . '$/u', $t)) return true;
    // pesan pendek yang DIAKHIRI terima kasih ("maaf kejauhan, trimakasih ya kak") tanpa tanda tanya
    if (mb_strpos($asli, '?') === false && count(explode(' ', $t)) <= 8
        && !preg_match('/(^| )(berapa|brp|apa|apakah|ada|ad|bisa|bs|gimana|gmn|bagaimana|kapan|dimana|mana|mau|minta|tolong|info|harga|booking|book|pesan|reservasi|kamar|cek|check|how|what|when|where|can|could|please|pls)( |$)/u', $t)
        && preg_match('/(^| )' . $inti . '( (ya|yah|yaa+|kak|ka|kk|kakak|min|mas|mbak|mba|pak|bu|bang|banyak|sekali))*$/u', $t)) return true;
    return false;
}""")
rep("""function deiIsClosingPhrase($t) {
    $t = mb_strtolower(trim((string)$t), 'UTF-8');""", """function deiIsClosingPhrase($t) {
    $t = mb_strtolower(trim((string)$t), 'UTF-8');
    $asli = $t;   // v1.2.102""")

# (1) auto-closing maks 1x per 12 jam
rep("""        if (!empty($st['closing_sent_at']) || !empty($st['guest_bye'])) continue;
        $lastAt = (int)($st['last_at'] ?? 0);""", """        if (!empty($st['closing_sent_at']) || !empty($st['guest_bye'])) continue;
        if ($now - (int)($st['closing_once_at'] ?? 0) < DEI_AC_GAP_SEC) continue;   // v1.2.102: closing-sekali
        $lastAt = (int)($st['last_at'] ?? 0);""")
rep("""            $a[$num]['closing_sent_at'] = time();
            return true;""", """            if (time() - (int)($a[$num]['closing_once_at'] ?? 0) < DEI_AC_GAP_SEC) return false;   // v1.2.102
            $a[$num]['closing_sent_at'] = time();
            $a[$num]['closing_once_at'] = time();   // v1.2.102: TIDAK di-reset oleh pesan tamu/bot
            return true;""")
rep("""function deiAcConf($s) {""", """if (!defined('DEI_AC_GAP_SEC')) define('DEI_AC_GAP_SEC', 12 * 3600);   // v1.2.102: closing-sekali — jeda minimal antar closing per nomor
function deiAcConf($s) {""")

# (3) AI: jangan bertanya "ada lagi?" — ditempel di blok tak-ter-cache
rep("""    $deiWaktuBlk = deiKonteksWaktu();        // v1.2.35: dipasang di SEMUA jalur di bawah""",
"""    // v1.2.102: closing-sekali — cegah AI mengulang "ada lagi yang bisa dibantu?"
    $deiPriceBlk = trim($deiPriceBlk . "\\n\\n" . "=== PENUTUP PERCAKAPAN ===\\n"
        . "Jika pelanggan berterima kasih, pamit, atau menyatakan tidak ada/belum ada pertanyaan lagi, balas SATU kalimat penutup singkat yang sopan TANPA pertanyaan apa pun. "
        . "Jangan pernah menanyakan 'apakah ada lagi yang bisa dibantu' atau sejenisnya (sistem sudah mengirimnya otomatis). "
        . "Jika pelanggan mengeluh ditanya berulang, minta maaf singkat dan JANGAN bertanya lagi.");
    $deiWaktuBlk = deiKonteksWaktu();        // v1.2.35: dipasang di SEMUA jalur di bawah""")

# (4) riwayat rapi
rep("""        if ($content !== '') $messages[] = ['role' => $role, 'content' => $content];
    }
    $messages[] = ['role' => 'user', 'content' => $message];
    return $messages;
}""", """        if ($content === '') continue;
        // v1.2.102: closing-sekali — riwayat tidak boleh diawali assistant & peran berurutan digabung
        // (closing otomatis / balasan dari HP menambah assistant ekstra -> urutan pecah -> AI error)
        if (!$messages && $role === 'assistant') continue;
        $n = count($messages);
        if ($n && $messages[$n - 1]['role'] === $role) { $messages[$n - 1]['content'] .= "\\n\\n" . $content; continue; }
        $messages[] = ['role' => $role, 'content' => $content];
    }
    $n = count($messages);
    if ($n && $messages[$n - 1]['role'] === 'user') $messages[$n - 1]['content'] .= "\\n\\n" . $message;
    else $messages[] = ['role' => 'user', 'content' => $message];
    return $messages;
}""")

# (5) coba ulang sekali untuk galat sementara + catat alasan
rep("""function callClaude($settings, $systemBlocks, $messages) {
    $r = callClaudeOnce($settings, $systemBlocks, $messages);
    if (!empty($r[0])) return $r;""", """function callClaude($settings, $systemBlocks, $messages) {
    $r = callClaudeOnce($settings, $systemBlocks, $messages);
    // v1.2.102: closing-sekali — galat sementara (timeout/overloaded/429/5xx) dicoba ulang sekali
    if (empty($r[0]) && preg_match('/Gagal terhubung|overload|rate.?limit|HTTP (429|5\\d\\d)|timed? ?out|internal server|529|503|502/i', (string)($r[1] ?? ''))) {
        usleep(1500000);
        $r = callClaudeOnce($settings, $systemBlocks, $messages);
    }
    if (empty($r[0])) $GLOBALS['dei_ai_last_err'] = mb_substr((string)($r[1] ?? ''), 0, 200);
    if (!empty($r[0])) return $r;""")
rep("""$deiAiError ? ['ai_error' => true] : []""", """$deiAiError ? ['ai_error' => true, 'ai_err' => (string)($GLOBALS['dei_ai_last_err'] ?? '')] : []""")
rep("""        $answer = 'Maaf, saya sedang mengalami gangguan. Silakan coba lagi sebentar lagi.';
        $deiAiError = true;""", """        $answer = 'Maaf, saya sedang mengalami gangguan. Silakan coba lagi sebentar lagi.';
        $deiAiError = true;
        if (empty($GLOBALS['dei_ai_last_err'])) $GLOBALS['dei_ai_last_err'] = $ok ? 'jawaban AI kosong' : mb_substr((string)$answer0, 0, 200);   // v1.2.102
        error_log('[ai_fail] wa ' . $from . ': ' . (string)$GLOBALS['dei_ai_last_err']);""")
rep("""    list($ok, $answer, $_kbUsed, $usage) = generateAnswer($s, $text, $history, 'whatsapp');   // v1.2.89""",
"""    list($ok, $answer, $_kbUsed, $usage) = generateAnswer($s, $text, $history, 'whatsapp');   // v1.2.89
    $answer0 = $answer;   // v1.2.102""")

open(F, 'w', encoding='utf-8').write(s)
print('OK', F)

# (6) OpenRouter: jawaban kosong (model "thinking" spt gemini-2.5-flash menghabiskan max_tokens untuk penalaran) -> coba ulang
s = open(F, encoding='utf-8').read()
if 'v1.2.102: or-kosong' not in s:
    old = """    $answer = $data['choices'][0]['message']['content'] ?? '';
    if (is_array($answer)) { // beberapa model balas array segmen
        $t=''; foreach ($answer as $seg){ $t .= is_array($seg)?($seg['text']??''):(string)$seg; } $answer=$t;
    }"""
    new = """    if (isset($data['error']) && empty($data['choices'])) return [false, 'AI error: ' . (string)($data['error']['message'] ?? 'tanpa pesan'), []];   // v1.2.102: or-kosong
    $answer = $data['choices'][0]['message']['content'] ?? '';
    if (is_array($answer)) { // beberapa model balas array segmen
        $t=''; foreach ($answer as $seg){ $t .= is_array($seg)?($seg['text']??''):(string)$seg; } $answer=$t;
    }
    // v1.2.102: or-kosong — konten kosong (penalaran memakan max_tokens / respons hampa): ulang sekali, jatah lebih besar, penalaran minim
    if (trim((string)$answer) === '' && empty($settings['api']['_or_retry'])) {
        $fin = (string)($data['choices'][0]['finish_reason'] ?? '');
        error_log('openrouter: jawaban kosong (finish=' . $fin . ', out=' . (int)($data['usage']['completion_tokens'] ?? 0) . ') -> coba ulang');
        $s2 = $settings; $s2['api']['_or_retry'] = 1;
        $s2['api']['max_tokens'] = max(1500, (int)($settings['api']['max_tokens'] ?? 400) * 4);
        $s2['api']['_or_reasoning'] = ['effort' => 'low', 'exclude' => true];
        $r2 = callOpenRouter($s2, $systemBlocks, $messages);
        if (!empty($r2[0]) && trim((string)$r2[1]) !== '') return $r2;
        return [false, 'AI error: jawaban kosong (finish=' . $fin . ')', []];
    }"""
    assert s.count(old) == 1
    s = s.replace(old, new)
    old2 = """        'usage'      => ['include' => true],   // v1.2.69: OpenRouter mengembalikan usage.cost (USD) asli
    ];"""
    new2 = old2 + """
    if (!empty($settings['api']['_or_reasoning'])) $payload['reasoning'] = $settings['api']['_or_reasoning'];   // v1.2.102: or-kosong"""
    assert s.count(old2) == 1
    s = s.replace(old2, new2)
    open(F, 'w', encoding='utf-8').write(s)
    print('OK or-kosong')

# (7) WAHA: balasan dari HP ke chat @lid sering tidak terbaca -> simpan peta lid->nomor dari pesan MASUK, catat yang terbuang
s = open(F, encoding='utf-8').read()
if 'v1.2.102: hp-lid' not in s:
    old = """    foreach (['remoteJidAlt', 'senderPn', 'participantPn'] as $f) {
        $alt = wahaJidNum($k[$f] ?? '');
        if ($alt !== '') return $alt;
    }
    $lid = preg_replace('/\\D/', '', substr($jid, 0, -4));
    if ($lid === '') return '';
    $f = DATA_DIR . '/waha-lids.json';
    $cache = readJson($f, []);
    if (!empty($cache[$lid])) return (string)$cache[$lid];"""
    new = """    $lid = preg_replace('/\\D/', '', substr($jid, 0, -4));
    $f = DATA_DIR . '/waha-lids.json';
    foreach (['remoteJidAlt', 'senderPn', 'participantPn', 'remoteJidPn'] as $kf) {   // v1.2.102: hp-lid (+ simpan peta)
        $alt = wahaJidNum($k[$kf] ?? '');
        if ($alt === '') $alt = wahaJidNum($p['_data'][$kf] ?? '');
        if ($alt !== '') {
            if ($lid !== '') { try { deiWithLock('waha-lids', function () use ($f, $lid, $alt) {
                $all = readJson($f, []); if (!is_array($all)) $all = [];
                if (($all[$lid] ?? '') !== $alt) { $all[$lid] = $alt; if (count($all) > 5000) $all = array_slice($all, -5000, null, true); writeJson($f, $all); }
            }); } catch (\\Throwable $e) {} }
            return $alt;
        }
    }
    if ($lid === '') return '';
    $cache = readJson($f, []);
    if (!empty($cache[$lid])) return (string)$cache[$lid];"""
    assert s.count(old) == 1, s.count(old)
    s = s.replace(old, new)
    old2 = """    if ($num === '') {
        if ($chat !== '') error_log('waha: lawan bicara tidak terbaca (' . $chat . ')');
        return null;
    }"""
    new2 = """    if ($num === '') {
        if ($chat !== '') error_log('waha: lawan bicara tidak terbaca (' . $chat . ')');
        // v1.2.102: hp-lid — jejak pesan yang terbuang (diagnosa balasan HP yang tidak muncul)
        try { $df = DATA_DIR . '/waha-dropped.json'; $dl = readJson($df, []); if (!is_array($dl)) $dl = [];
            $dl[] = ['t' => date('Y-m-d H:i:s'), 'fromMe' => $fromMe ? 1 : 0, 'chat' => $chat, 'from' => (string)($p['from'] ?? ''), 'to' => (string)($p['to'] ?? ''), 'body' => mb_substr((string)($p['body'] ?? ''), 0, 60)];
            writeJson($df, array_slice($dl, -200)); } catch (\\Throwable $e) {}
        return null;
    }"""
    assert s.count(old2) == 1
    s = s.replace(old2, new2)
    open(F, 'w', encoding='utf-8').write(s)
    print('OK hp-lid')
