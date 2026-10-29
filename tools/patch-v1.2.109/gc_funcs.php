/* v1.2.109: guest-comment — survei kepuasan tamu (Guest Comment). Mulai paket Business.
 *  - WhatsApp: tamu mengetik kata kunci (mis. "GUEST COMMENT", bisa dari QR wa.me) -> bot memandu
 *    nama, nomor kamar, rating 1–5 per aspek, komentar. Alur terpandu TANPA AI (tidak memakai kuota AI).
 *  - Web: form publik ?action=gc_form (QR di kamar/front desk, atau tautan dari bot widget).
 *  - Rating rendah (<= ambang) -> notifikasi push/Telegram + WA ke nomor staf (opsional).
 *  - Tautan ulasan Google ditawarkan ke SEMUA tamu (tanpa menyaring rating — kebijakan Google).
 * Data: data/guest-comment.json (pengaturan), data/guest-comments.json (entri, terbaru di depan),
 *       data/gc-sessions.json (sesi WA berjalan, kedaluwarsa GC_SESSION_TTL). */
if (!defined('GC_CONF_FILE')) define('GC_CONF_FILE', DATA_DIR . '/guest-comment.json');
if (!defined('GC_FILE')) define('GC_FILE', DATA_DIR . '/guest-comments.json');
if (!defined('GC_SESS_FILE')) define('GC_SESS_FILE', DATA_DIR . '/gc-sessions.json');
if (!defined('GC_MAX')) define('GC_MAX', 5000);
if (!defined('GC_SESSION_TTL')) define('GC_SESSION_TTL', 1800);
if (!defined('GC_TIERS')) define('GC_TIERS', 'business,pro,custom,enterprise');   // paket yang mendapat fitur ini

function gcDefaults() {
    return [
        'enabled'  => false,
        'aspects'  => [
            ['id' => 'overall', 'label' => 'Kesan keseluruhan', 'label_en' => 'Overall experience'],
            ['id' => 'room',    'label' => 'Kamar',             'label_en' => 'Room'],
            ['id' => 'clean',   'label' => 'Kebersihan',        'label_en' => 'Cleanliness'],
            ['id' => 'staff',   'label' => 'Pelayanan staf',    'label_en' => 'Staff service'],
            ['id' => 'fnb',     'label' => 'Makanan & minuman', 'label_en' => 'Food & beverage'],
        ],
        'ask_name' => true,
        'ask_room' => true,
        'ask_phone_web' => true,
        'intro'    => "Terima kasih sudah menginap bersama kami \xF0\x9F\x99\x8F Mohon luangkan 1 menit untuk mengisi guest comment.",
        'intro_en' => "Thank you for staying with us \xF0\x9F\x99\x8F Please spare a minute to share your guest comment.",
        'thanks'   => 'Terima kasih atas masukan Anda! Setiap komentar kami baca untuk terus memperbaiki layanan.',
        'thanks_en'=> 'Thank you for your feedback! We read every comment to keep improving our service.',
        'review_url'     => '',
        'review_text'    => 'Bila berkenan, bagikan juga pengalaman Anda di Google: {link}',
        'review_text_en' => 'If you have a moment, please share your experience on Google too: {link}',
        'low'      => 2,
        'alert_wa' => '',
        'keywords' => ['guest comment', 'guest feedback', 'kesan pesan', 'kesan dan pesan', 'survei tamu', 'isi survei'],
        'ai_hint'  => true,
    ];
}
function gcSlug($t) {
    $t = strtolower(preg_replace('/[^A-Za-z0-9]+/', '_', (string)$t));
    return substr(trim($t, '_'), 0, 24);
}
function gcClean($in) {
    $d = gcDefaults();
    $in = is_array($in) ? $in : [];
    $o = ['enabled' => !empty($in['enabled'])];
    foreach (['ask_name', 'ask_room', 'ask_phone_web', 'ai_hint'] as $k) $o[$k] = array_key_exists($k, $in) ? !empty($in[$k]) : $d[$k];
    $asp = []; $seen = [];
    foreach ((array)($in['aspects'] ?? $d['aspects']) as $a) {
        if (!is_array($a)) continue;
        $l = mb_substr(trim((string)($a['label'] ?? '')), 0, 60);
        $le = mb_substr(trim((string)($a['label_en'] ?? '')), 0, 60);
        if ($l === '' && $le === '') continue;
        if ($l === '') $l = $le;
        $id = gcSlug($a['id'] ?? '');
        if ($id === '') $id = gcSlug($le !== '' ? $le : $l);
        if ($id === '') $id = 'a' . (count($asp) + 1);
        $base = $id; $n = 2;
        while (isset($seen[$id])) $id = substr($base, 0, 20) . '_' . $n++;
        $seen[$id] = 1;
        $asp[] = ['id' => $id, 'label' => $l, 'label_en' => $le];
        if (count($asp) >= 8) break;
    }
    $o['aspects'] = $asp ?: $d['aspects'];
    foreach (['intro', 'intro_en', 'thanks', 'thanks_en', 'review_text', 'review_text_en'] as $k) {
        $v = array_key_exists($k, $in) ? trim(str_replace("\r", '', (string)$in[$k])) : $d[$k];
        $o[$k] = mb_substr($v, 0, 600);
    }
    $u = trim((string)($in['review_url'] ?? ''));
    $o['review_url'] = preg_match('~^https?://[^\s<>"]{3,500}$~i', $u) ? $u : '';
    $o['low'] = max(1, min(4, (int)($in['low'] ?? $d['low'])));
    $nums = [];
    foreach (preg_split('/[,;\n]+/', (string)($in['alert_wa'] ?? '')) as $x) {
        $x = preg_replace('/\D/', '', $x);
        if ($x === '') continue;
        if ($x[0] === '0') $x = '62' . substr($x, 1);
        if (strlen($x) >= 9 && strlen($x) <= 15) $nums[$x] = $x;
        if (count($nums) >= 5) break;
    }
    $o['alert_wa'] = implode(', ', array_values($nums));
    $kw = [];
    $kwIn = $in['keywords'] ?? $d['keywords'];
    if (is_string($kwIn)) $kwIn = preg_split('/[,\n]+/', $kwIn);
    foreach ((array)$kwIn as $k) {
        $k = trim(preg_replace('/\s+/', ' ', mb_strtolower((string)$k, 'UTF-8')));
        if (mb_strlen($k) >= 3 && mb_strlen($k) <= 40) $kw[$k] = $k;
        if (count($kw) >= 15) break;
    }
    $o['keywords'] = $kw ? array_values($kw) : $d['keywords'];
    return $o;
}
function gcConf() {
    if (isset($GLOBALS['dei_gc_conf'])) return $GLOBALS['dei_gc_conf'];
    $raw = readJson(GC_CONF_FILE, []);
    return $GLOBALS['dei_gc_conf'] = gcClean(array_replace(gcDefaults(), is_array($raw) ? $raw : []));
}
// Paket: tanpa server pusat (instalasi sendiri) = boleh. Trial & Starter/Growth = belum.
function gcPlan() {
    if (isset($GLOBALS['dei_gc_plan'])) return $GLOBALS['dei_gc_plan'];
    $s = getSettings();
    $cs = $s['central_server'] ?? [];
    if (empty($cs['url']) || empty($cs['tenant_id']) || empty($cs['license_key'])) return $GLOBALS['dei_gc_plan'] = ['ok' => true, 'tier' => '', 'trial' => false];
    $cap = [];
    try { $cap = getCapStatus($s); } catch (\Throwable $e) { error_log('gcPlan: ' . $e->getMessage()); }
    $tier = strtolower(trim((string)($cap['tier'] ?? '')));
    $trial = !empty($cap['trial']) || $tier === 'trial';
    $ok = !$trial && in_array($tier, explode(',', GC_TIERS), true);
    return $GLOBALS['dei_gc_plan'] = ['ok' => $ok, 'tier' => $trial ? 'trial' : $tier, 'trial' => $trial];
}
function gcActive() { return gcPlan()['ok'] && gcConf()['enabled']; }
function gcLockedMsg() { return 'Guest Comment tersedia mulai paket Business. Hubungi ' . deiBrandVendor() . ' untuk upgrade paket.'; }
function gcApiBase() {
    $u = deiSelfApiUrl();
    if ($u === '' || strpos($u, '://localhost') !== false) { $r = deiRememberedApiUrl(); if ($r !== '') $u = $r; }
    return $u;
}
function gcFormUrl($room = '') {
    $b = gcApiBase();
    if ($b === '') return '';
    return $b . '?action=gc_form' . ($room !== '' ? '&room=' . rawurlencode($room) : '');
}
function gcAspLabel($a, $lang) { return ($lang === 'en' && trim((string)($a['label_en'] ?? '')) !== '') ? $a['label_en'] : $a['label']; }
function gcTxt($k, $lang) {
    $T = [
        'ask_name'    => ['Boleh kami tahu nama Anda?', 'May we have your name?'],
        'ask_room'    => ['Nomor kamar Anda? (ketik *-* bila tidak ingat)', 'Your room number? (type *-* if you don\'t remember)'],
        'ask_rate'    => ["*{n}/{t}* Bagaimana penilaian Anda untuk *{a}*?\nBalas angka *1–5* (1 = sangat buruk, 5 = sangat baik).",
                          "*{n}/{t}* How would you rate *{a}*?\nReply with *1–5* (1 = very poor, 5 = excellent)."],
        'bad_rate'    => ['Mohon balas dengan angka *1* sampai *5* ya. Ketik *batal* untuk berhenti.', 'Please reply with a number from *1* to *5*. Type *cancel* to stop.'],
        'ask_comment' => ['Terakhir, ada komentar, saran, atau hal yang perlu kami perbaiki? Ketik *-* bila tidak ada.',
                          'Lastly, any comments, suggestions, or things we should improve? Type *-* if none.'],
        'stop_hint'   => ['(ketik *batal* untuk berhenti)', '(type *cancel* to stop)'],
        'cancelled'   => ['Baik, pengisian guest comment dibatalkan. Silakan kirim pesan bila ada yang bisa kami bantu.', 'Okay, the guest comment has been cancelled. Feel free to message us if you need anything.'],
    ];
    return $T[$k][$lang === 'en' ? 1 : 0] ?? '';
}
function gcNorm($t) { return trim(preg_replace('/\s+/u', ' ', mb_strtolower(preg_replace('/[^\p{L}\p{N}\s#-]/u', ' ', (string)$t), 'UTF-8'))); }
function gcMatchKeyword($text, $conf) {
    $n = ' ' . gcNorm($text) . ' ';
    if (mb_strlen($n) > 120) return false;   // pesan panjang = pertanyaan biasa, bukan perintah
    foreach ($conf['keywords'] as $k) {
        if (mb_strpos($n, ' ' . gcNorm($k) . ' ') !== false) return true;
    }
    return false;
}
function gcLangOf($text) {
    $l = deiDeteksiBahasa($text);
    if ($l === 'en' || $l === 'id') return $l;
    $n = ' ' . gcNorm($text) . ' ';
    if (preg_match('/ (i|my|give|would|like|leave|please|feedback) /', $n) && !preg_match('/ (saya|ingin|mau|isi|kesan|survei) /', $n)) return 'en';
    return 'id';
}
function gcIsSkip($t) { return in_array(gcNorm($t), ['', '-', 'skip', 'lewati', 'tidak ada', 'tidak', 'ga ada', 'gak ada', 'nggak ada', 'enggak', 'no', 'none', 'nothing', 'n a', 'na', 'tdk ada'], true) || trim((string)$t) === '-'; }
function gcIsCancel($t) { return in_array(gcNorm($t), ['batal', 'cancel', 'stop', 'berhenti', 'keluar', 'batalkan', 'quit', 'exit'], true); }
function gcParseRating($t) {
    $t = trim((string)$t);
    if (preg_match('/^\D{0,3}([1-5])(?!\d)/u', $t, $m)) return (int)$m[1];
    $st = preg_match_all('/\x{2B50}|\x{1F31F}|\x{2605}/u', $t);
    if ($st >= 1 && $st <= 5) return $st;
    $w = ['satu' => 1, 'dua' => 2, 'tiga' => 3, 'empat' => 4, 'lima' => 5, 'one' => 1, 'two' => 2, 'three' => 3, 'four' => 4, 'five' => 5];
    $n = gcNorm($t);
    return $w[$n] ?? 0;
}
function gcRatingStats($ratings, $low) {
    $v = array_values(array_filter(array_map('intval', (array)$ratings), function ($x) { return $x >= 1 && $x <= 5; }));
    $avg = $v ? round(array_sum($v) / count($v), 2) : 0;
    $isLow = false;
    foreach ($v as $x) if ($x <= $low) $isLow = true;
    return [$avg, $isLow];
}

/* --- entri --- */
function gcAll() { $d = readJson(GC_FILE, []); return is_array($d) ? $d : []; }
function gcStore($e) {
    $conf = gcConf();
    list($avg, $low) = gcRatingStats($e['ratings'] ?? [], $conf['low']);
    $labels = [];
    foreach ($conf['aspects'] as $a) if (isset($e['ratings'][$a['id']])) $labels[$a['id']] = $a['label'];
    $e = array_merge([
        'id' => 'g' . wibDate('ymdHis') . bin2hex(random_bytes(2)),
        'ts' => wibDate('Y-m-d H:i:s'), 'channel' => 'web', 'num' => '', 'name' => '', 'room' => '', 'phone' => '',
        'lang' => 'id', 'ratings' => [], 'comment' => '', 'wa_ch' => '', 'status' => 'baru', 'note' => '',
    ], $e, ['labels' => $labels, 'avg' => $avg, 'low' => $low]);
    deiWithLock('gc', function () use ($e) {
        $all = gcAll();
        array_unshift($all, $e);
        if (count($all) > GC_MAX) $all = array_slice($all, 0, GC_MAX);
        writeJson(GC_FILE, $all);
    });
    if ($low) { try { gcAlert($e); } catch (\Throwable $ex) { error_log('gcAlert: ' . $ex->getMessage()); } }
    return $e;
}
function gcAlert($e) {
    $s = getSettings();
    $conf = gcConf();
    $who = trim(($e['name'] !== '' ? $e['name'] : 'Tamu') . ($e['room'] !== '' ? ' (kamar ' . $e['room'] . ')' : ''));
    $det = [];
    foreach ($conf['aspects'] as $a) if (isset($e['ratings'][$a['id']])) $det[] = $a['label'] . ' ' . (int)$e['ratings'][$a['id']];
    $title = 'Guest comment rendah: ' . $who;
    $body = 'Rata-rata ' . $e['avg'] . '/5 · ' . implode(', ', $det) . ($e['comment'] !== '' ? ' — "' . mb_substr($e['comment'], 0, 120) . '"' : '');
    $subs = array_keys((array)readJson(DATA_DIR . '/push-subs.json', []));
    $targets = [];
    foreach ((array)readJson(USERS_FILE, []) as $u) {
        $un = (string)($u['username'] ?? '');
        if ($un !== '' && in_array(($u['role'] ?? ''), ['super_admin', 'admin', 'supervisor'], true) && in_array($un, $subs, true)) $targets[] = $un;
    }
    if ($targets) sendPushToUsers($targets, $title, mb_substr($body, 0, 180), deiDashboardUrl() . '#gc', 'dei-gc');
    tgNotify($s, "\xE2\x9A\xA0\xEF\xB8\x8F " . $title . "\n" . $body . ($e['num'] !== '' ? "\nWA: +" . $e['num'] : ($e['phone'] !== '' ? "\nHP: " . $e['phone'] : '')));
    if ($conf['alert_wa'] !== '') {
        $wa = waConf($s);
        {
            $txt = "\xE2\x9A\xA0\xEF\xB8\x8F *Guest comment rendah*\n" . $who . "\nRata-rata *" . $e['avg'] . "/5*\n" . implode("\n", $det)
                 . ($e['comment'] !== '' ? "\n\nKomentar: " . mb_substr($e['comment'], 0, 500) : '')
                 . ($e['num'] !== '' ? "\n\nWA tamu: +" . $e['num'] : ($e['phone'] !== '' ? "\n\nHP tamu: " . $e['phone'] : ''));
            foreach (explode(', ', $conf['alert_wa']) as $n) {
                if ($n === '' || $n === $e['num']) continue;
                if (!waSend($wa, $n, $txt)) error_log('gcAlert WA ' . $n . ': ' . (string)($GLOBALS['wa_last_error'] ?? ''));
            }
        }
    }
}

/* --- sesi WA --- */
function gcSessMutate($fn) {
    return deiWithLock('gcsess', function () use ($fn) {
        $all = readJson(GC_SESS_FILE, []);
        if (!is_array($all)) $all = [];
        $now = time();
        foreach ($all as $k => $v) { if ((int)($v['at'] ?? 0) < $now - GC_SESSION_TTL) unset($all[$k]); }
        $r = $fn($all);
        writeJson(GC_SESS_FILE, $all);
        return $r;
    });
}
function gcSessGet($num) { return gcSessMutate(function (&$all) use ($num) { return $all[$num] ?? null; }); }
function gcSessPut($num, $st) { gcSessMutate(function (&$all) use ($num, $st) { if ($st === null) unset($all[$num]); else $all[$num] = $st + ['at' => time()]; return true; }); }
function gcQuestion($st, $conf) {
    $step = $st['steps'][$st['i']] ?? '';
    $lang = $st['lang'];
    if ($step === 'name') return gcTxt('ask_name', $lang);
    if ($step === 'room') return gcTxt('ask_room', $lang);
    if ($step === 'comment') return gcTxt('ask_comment', $lang);
    $asp = array_values(array_filter($st['steps'], function ($x) { return strpos($x, 'r:') === 0; }));
    $n = array_search($step, $asp, true);
    foreach ($conf['aspects'] as $a) {
        if ('r:' . $a['id'] === $step) return strtr(gcTxt('ask_rate', $lang), ['{n}' => (string)($n + 1), '{t}' => (string)count($asp), '{a}' => gcAspLabel($a, $lang)]);
    }
    return '';
}
function gcThanks($conf, $lang) {
    $t = trim((string)($lang === 'en' ? ($conf['thanks_en'] ?: $conf['thanks']) : $conf['thanks']));
    if ($conf['review_url'] !== '') {
        $r = trim((string)($lang === 'en' ? ($conf['review_text_en'] ?: $conf['review_text']) : $conf['review_text']));
        if ($r === '') $r = '{link}';
        if (strpos($r, '{link}') === false) $r .= ' {link}';
        $t .= "\n\n" . str_replace('{link}', $conf['review_url'], $r);
    }
    return $t;
}
// Dipanggil dari waProcessIncoming sebelum handoff/AI. true = pesan sudah ditangani alur survei.
function gcWaHandle($s, $wa, $from, $text, $senderName, $metaInfo) {
    if (!empty($metaInfo['_no_reply']) || !empty($metaInfo['_media'])) {
        // stiker/media: biarkan alur biasa, sesi survei tetap menunggu
        return false;
    }
    $num = waNormNum($from);
    if ($num === '' || !gcActive()) return false;
    $conf = gcConf();
    $st = gcSessGet($num);
    if (!$st && !gcMatchKeyword($text, $conf)) return false;
    $lic = getLicenseStatus($s);
    if (($lic['status'] ?? '') === 'suspended') return false;

    $reply = '';
    if (!$st) {
        $lang = gcLangOf($text);
        $room = preg_match('/#\s*([A-Za-z0-9][A-Za-z0-9-]{0,9})/u', (string)$text, $m) ? $m[1] : '';
        $steps = [];
        if ($conf['ask_name']) $steps[] = 'name';
        if ($conf['ask_room'] && $room === '') $steps[] = 'room';
        foreach ($conf['aspects'] as $a) $steps[] = 'r:' . $a['id'];
        $steps[] = 'comment';
        $st = ['lang' => $lang, 'steps' => $steps, 'i' => 0, 'name' => $conf['ask_name'] ? '' : mb_substr(trim((string)$senderName), 0, 60),
               'room' => $room, 'ratings' => [], 'comment' => '', 'bad' => 0, 'ch' => (string)($wa['_ch'] ?? ''), 'started' => time()];
        $intro = trim((string)($lang === 'en' ? ($conf['intro_en'] ?: $conf['intro']) : $conf['intro']));
        $reply = ($intro !== '' ? $intro . "\n\n" : '') . gcQuestion($st, $conf) . "\n" . gcTxt('stop_hint', $lang);
        gcSessPut($num, $st);
    } elseif (gcIsCancel($text)) {
        gcSessPut($num, null);
        $reply = gcTxt('cancelled', $st['lang']);
    } else {
        $step = $st['steps'][$st['i']] ?? 'comment';
        $t = trim((string)$text);
        $advance = true;
        if ($step === 'name') {
            $st['name'] = gcIsSkip($t) ? mb_substr(trim((string)$senderName), 0, 60) : mb_substr($t, 0, 60);
        } elseif ($step === 'room') {
            $st['room'] = gcIsSkip($t) ? '' : mb_substr(preg_replace('/^(kamar|room|no\.?|nomor)\s*/iu', '', $t), 0, 20);
        } elseif ($step === 'comment') {
            $st['comment'] = gcIsSkip($t) ? '' : mb_substr($t, 0, 2000);
        } else {
            $r = gcParseRating($t);
            if ($r > 0) { $st['ratings'][substr($step, 2)] = $r; $st['bad'] = 0; }
            elseif (gcIsSkip($t) && $st['bad'] >= 1) { $st['bad'] = 0; }   // tamu memang tidak mau menilai aspek ini
            else { $advance = false; $st['bad']++; }
        }
        if (!$advance) {
            $reply = gcTxt('bad_rate', $st['lang']) . "\n\n" . gcQuestion($st, $conf);
            if ($st['bad'] >= 3) {   // jelas bukan menjawab survei -> hentikan, lanjut ke bot biasa
                gcSessPut($num, null);
                return false;
            }
            gcSessPut($num, $st);
        } else {
            $st['i']++;
            if ($st['i'] >= count($st['steps'])) {
                gcSessPut($num, null);
                $entry = gcStore(['channel' => 'whatsapp', 'num' => $num, 'name' => $st['name'], 'room' => $st['room'],
                                  'lang' => $st['lang'], 'ratings' => $st['ratings'], 'comment' => $st['comment'], 'wa_ch' => $st['ch']]);
                $reply = gcThanks($conf, $st['lang']);
            } else {
                gcSessPut($num, $st);
                $reply = gcQuestion($st, $conf);
            }
        }
    }
    // kirim + catat (dihitung sebagai pesan sistem: tidak menambah hitungan Batas Balasan AI)
    $reply = stripMarkdownIfEnabled($reply, $s);
    if (waSend($wa, $from, $reply)) convReply($from, 'system');
    if ($wa['keep_context'] ?? true) {
        $h = waLoadHistory($from);
        $h[] = ['role' => 'user', 'content' => $text];
        $h[] = ['role' => 'assistant', 'content' => $reply];
        waSaveHistory($from, $h);
    }
    $log = ['ts' => date('Y-m-d H:i:s'), 'q' => $text, 'a' => $reply, 'ip' => $from, 'channel' => 'whatsapp', 'utm_source' => 'whatsapp',
            'utm_medium' => 'chat', 'utm_campaign' => '', 'page' => '', 'referrer' => '', 'gc' => 1];
    if (!empty($wa['_ch'])) $log['wa_ch'] = (string)$wa['_ch'];
    logPrepend($log, (int)($s['api']['log_limit'] ?? 500));
    return true;
}
// Instruksi tambahan ke AI supaya tamu yang ingin memberi masukan diarahkan ke survei.
function gcPromptBlock($channel) {
    if (!gcActive()) return '';
    $c = gcConf();
    if (!$c['ai_hint']) return '';
    if ($channel === 'whatsapp') {
        return "=== GUEST COMMENT ===\nJika tamu ingin memberi kesan, komentar, saran, keluhan, atau penilaian tentang menginap/layanan, minta tamu mengetik persis: "
             . mb_strtoupper($c['keywords'][0], 'UTF-8') . " (sistem akan memandu survei singkat 1 menit). Jangan mengumpulkan penilaian sendiri.";
    }
    $u = gcFormUrl();
    if ($u === '') return '';
    return "=== GUEST COMMENT ===\nJika tamu ingin memberi kesan, komentar, saran, keluhan, atau penilaian tentang menginap/layanan, arahkan ke form guest comment singkat ini: " . $u;
}
function gcPublicConf($lang) {
    $c = gcConf();
    $asp = [];
    foreach ($c['aspects'] as $a) $asp[] = ['id' => $a['id'], 'label' => $a['label'], 'label_en' => $a['label_en']];
    return ['aspects' => $asp, 'ask_name' => $c['ask_name'], 'ask_room' => $c['ask_room'], 'ask_phone' => $c['ask_phone_web'],
            'intro' => $c['intro'], 'intro_en' => $c['intro_en'], 'thanks' => $c['thanks'], 'thanks_en' => $c['thanks_en'],
            'review_url' => $c['review_url'], 'review_text' => $c['review_text'], 'review_text_en' => $c['review_text_en']];
}
function gcFormHtml($s, $active, $room) {
    $J = JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT;
    $name = deiTenantName($s);
    $color = (string)($s['appearance']['primary_color'] ?? '#140383');
    if (!preg_match('/^#[0-9a-fA-F]{3,8}$/', $color)) $color = '#140383';
    $logo = (string)($s['appearance']['avatar_image'] ?? '');
    if ($logo !== '' && !preg_match('~^(https?://|/|data:image/)~', $logo)) $logo = '';
    $data = ['active' => $active, 'room' => $room, 'name' => $name, 'logo' => $logo,
             'conf' => $active ? gcPublicConf('id') : null, 'api' => '?action=gc_submit',
             'langs' => (array)($s['bot']['languages'] ?? ['id'])];
    $h = function ($x) { return htmlspecialchars((string)$x, ENT_QUOTES, 'UTF-8'); };
    ob_start(); ?>
<!doctype html>
<html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Guest Comment · <?= $h($name) ?></title><meta name="robots" content="noindex">
<style>
:root{--c:<?= $h($color) ?>;--ink:#1d1d2b;--mut:#6b6b80;--line:#e5e5ee;--bg:#f5f5f9}
*{box-sizing:border-box}body{margin:0;font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--bg)}
.w{max-width:560px;margin:0 auto;padding:20px 16px 40px}
.hd{display:flex;align-items:center;gap:12px;margin-bottom:14px}.hd img{width:44px;height:44px;border-radius:12px;object-fit:cover}
.hd b{font-size:17px;display:block}.hd small{color:var(--mut)}
.lg{margin-left:auto;display:flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:#fff}
.lg button{border:0;background:none;padding:6px 12px;font:600 13px system-ui;cursor:pointer;color:var(--mut)}.lg button.on{background:var(--c);color:#fff}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;margin-bottom:14px}
.intro{margin:0;color:#3a3a4c}
label.f{display:block;font-weight:600;font-size:14px;margin:0 0 6px}
input[type=text],input[type=tel],textarea{width:100%;border:1px solid var(--line);border-radius:10px;padding:11px 12px;font:inherit;background:#fff}
input:focus,textarea:focus{outline:2px solid color-mix(in srgb,var(--c) 35%,transparent);border-color:var(--c)}
.row{margin-bottom:14px}.row:last-child{margin-bottom:0}.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.asp{padding:12px 0;border-top:1px solid var(--line)}.asp:first-child{border-top:0;padding-top:0}
.asp .t{font-weight:600;margin-bottom:8px}
.stars{display:flex;gap:6px}.stars button{flex:1;min-width:0;height:46px;border:1px solid var(--line);border-radius:10px;background:#fff;font:600 16px system-ui;color:var(--mut);cursor:pointer}
.stars button.on{background:var(--c);border-color:var(--c);color:#fff}
.scale{display:flex;justify-content:space-between;font-size:12px;color:var(--mut);margin-top:4px}
.btn{width:100%;border:0;border-radius:12px;background:var(--c);color:#fff;font:600 16px system-ui;padding:14px;cursor:pointer}
.btn[disabled]{opacity:.6}.err{color:#b42318;font-size:14px;margin:10px 0 0;display:none}
.done{text-align:center;padding:32px 18px}.done .ic{font-size:44px}.done a.btn{display:inline-block;text-decoration:none;width:auto;padding:12px 22px;margin-top:10px}
.hp{position:absolute;left:-9999px}.ft{text-align:center;color:var(--mut);font-size:12px;margin-top:18px}
@media (max-width:380px){.g2{grid-template-columns:1fr}.stars button{height:42px}}
</style></head><body><div class="w" id="app"></div>
<script>
(function(){
var D=<?= json_encode($data, $J) ?>;
var L=(navigator.language||'id').slice(0,2)==='en'&&D.langs.indexOf('en')>=0?'en':'id';
try{var q=new URLSearchParams(location.search).get('lang');if(q==='en'||q==='id')L=q;}catch(e){}
var R={};var st={sent:false};
var T={id:{t:'Guest Comment',name:'Nama',room:'Nomor kamar',phone:'No. HP / WhatsApp (opsional)',cm:'Komentar & saran',cmp:'Ceritakan pengalaman Anda, atau hal yang perlu kami perbaiki…',
 lo:'Sangat buruk',hi:'Sangat baik',send:'Kirim',sending:'Mengirim…',need:'Mohon beri nilai untuk semua aspek.',fail:'Gagal mengirim. Coba lagi.',off:'Form guest comment belum tersedia.',again:'Isi lagi'},
 en:{t:'Guest Comment',name:'Name',room:'Room number',phone:'Phone / WhatsApp (optional)',cm:'Comments & suggestions',cmp:'Tell us about your stay, or anything we should improve…',
 lo:'Very poor',hi:'Excellent',send:'Submit',sending:'Sending…',need:'Please rate every aspect.',fail:'Could not submit. Please try again.',off:'The guest comment form is not available.',again:'Submit another'}};
function e(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function x(k){return T[L][k];}
function pick(a,b){return L==='en'&&b?b:a;}
function head(){return '<div class="hd">'+(D.logo?'<img src="'+e(D.logo)+'" alt="">':'')+'<div><b>'+e(D.name)+'</b><small>'+x('t')+'</small></div>'+
 ('<div class="lg"><button type="button" data-l="id" class="'+(L==='id'?'on':'')+'">ID</button><button type="button" data-l="en" class="'+(L==='en'?'on':'')+'">EN</button></div>')+'</div>';}
function draw(){
 var a=document.getElementById('app'),C=D.conf,h=head();
 if(!D.active){a.innerHTML=h+'<div class="card done"><div class="ic">🛎️</div><p>'+x('off')+'</p></div>';wire();return;}
 if(st.sent){var rv=C.review_url?pick(C.review_text,C.review_text_en)||'{link}':'';
  var rb='';if(C.review_url){var parts=rv.split('{link}');rb='<p>'+e(parts[0]).replace(/\n/g,'<br>')+'</p><a class="btn" href="'+e(C.review_url)+'" target="_blank" rel="noopener">Google Review ★</a>'+(parts[1]?'<p>'+e(parts[1])+'</p>':'');}
  a.innerHTML=h+'<div class="card done"><div class="ic">🙏</div><p>'+e(pick(C.thanks,C.thanks_en)).replace(/\n/g,'<br>')+'</p>'+rb+'</div>';wire();return;}
 var f='<form id="f" novalidate><div class="card"><p class="intro">'+e(pick(C.intro,C.intro_en)).replace(/\n/g,'<br>')+'</p></div><div class="card">';
 if(C.ask_name||C.ask_room){f+='<div class="'+(C.ask_name&&C.ask_room?'g2 ':'')+'row">';
  if(C.ask_name)f+='<div><label class="f" for="nm">'+x('name')+'</label><input type="text" id="nm" maxlength="60" autocomplete="name" value="'+e(st.nm||'')+'"></div>';
  if(C.ask_room)f+='<div><label class="f" for="rm">'+x('room')+'</label><input type="text" id="rm" maxlength="20" value="'+e(st.rm!=null?st.rm:D.room)+'"></div>';
  f+='</div>';}
 if(C.ask_phone)f+='<div class="row"><label class="f" for="ph">'+x('phone')+'</label><input type="tel" id="ph" maxlength="20" autocomplete="tel" value="'+e(st.ph||'')+'"></div>';
 f+='</div><div class="card">';
 C.aspects.forEach(function(s){f+='<div class="asp"><div class="t">'+e(pick(s.label,s.label_en))+'</div><div class="stars" data-a="'+e(s.id)+'">';
  for(var i=1;i<=5;i++)f+='<button type="button" data-v="'+i+'" class="'+(R[s.id]>=i?'on':'')+'" aria-label="'+i+'">'+i+'</button>';
  f+='</div><div class="scale"><span>'+x('lo')+'</span><span>'+x('hi')+'</span></div></div>';});
 f+='</div><div class="card"><label class="f" for="cm">'+x('cm')+'</label><textarea id="cm" rows="4" maxlength="2000" placeholder="'+x('cmp')+'">'+e(st.cm||'')+'</textarea>'+
  '<input class="hp" type="text" id="hp" tabindex="-1" autocomplete="off"></div><button class="btn" id="sb" type="submit">'+x('send')+'</button><p class="err" id="er"></p></form>';
 a.innerHTML=h+f;wire();
}
function keep(){var g=function(i){var el=document.getElementById(i);return el?el.value:undefined;};st.nm=g('nm');st.rm=g('rm');st.ph=g('ph');st.cm=g('cm');}
function wire(){
 Array.prototype.forEach.call(document.querySelectorAll('.lg button'),function(b){b.onclick=function(){keep();L=b.dataset.l;draw();};});
 Array.prototype.forEach.call(document.querySelectorAll('.stars button'),function(b){b.onclick=function(){var p=b.parentNode;R[p.dataset.a]=+b.dataset.v;
  Array.prototype.forEach.call(p.children,function(c){c.classList.toggle('on',+c.dataset.v<=+b.dataset.v);});};});
 var f=document.getElementById('f');if(!f)return;
 f.onsubmit=function(ev){ev.preventDefault();keep();var er=document.getElementById('er');er.style.display='none';
  for(var i=0;i<D.conf.aspects.length;i++){if(!R[D.conf.aspects[i].id]){er.textContent=x('need');er.style.display='block';return;}}
  var sb=document.getElementById('sb');sb.disabled=true;sb.textContent=x('sending');
  fetch(D.api,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:st.nm||'',room:st.rm||'',phone:st.ph||'',comment:st.cm||'',ratings:R,lang:L,hp:document.getElementById('hp').value})})
  .then(function(r){return r.json();}).then(function(j){if(j&&j.ok){st.sent=true;draw();window.scrollTo(0,0);}else{throw new Error(j&&j.error||'');}})
  .catch(function(err){sb.disabled=false;sb.textContent=x('send');er.textContent=err.message||x('fail');er.style.display='block';});};
}
draw();
})();
</script></body></html>
<?php
    return ob_get_clean();
}
