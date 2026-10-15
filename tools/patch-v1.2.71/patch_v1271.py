#!/usr/bin/env python3
"""v1.2.71 — driver penyimpanan (file|mysql) + antrean (sync|redis) + worker.
Idempoten: berhenti kalau penanda v1.2.71 sudah ada. Pakai: patch_v1271.py <api/index.php>"""
import re, sys, pathlib

P = pathlib.Path(sys.argv[1])
src = P.read_text(encoding='utf-8')
HERE = pathlib.Path(__file__).parent
if 'function deiServerConf()' in src:
    print('sudah terpasang'); sys.exit(0)

def rep(old, new, count=1):
    global src
    n = src.count(old)
    if n != count:
        raise SystemExit(f'ANCHOR {n}x (harus {count}): {old[:90]!r}')
    src = src.replace(old, new)

# 0. versi
src = re.sub(r"define\('DEI_VERSION', 'v[0-9.]+'\);", "define('DEI_VERSION', 'v1.2.71');", src, count=1)

# 1. semua pembaca log -> logReadAll() (kecuali di dalam logMutate)
LM = "        $logs = readJson(LOG_FILE, []);\n        if (!is_array($logs)) $logs = [];\n        $r = $fn($logs);"
rep(LM, "@@LOGMUTATE_READ@@")
n_reads = src.count('readJson(LOG_FILE, [])')
src = src.replace('readJson(LOG_FILE, [])', 'logReadAll()')
src = src.replace("@@LOGMUTATE_READ@@", LM)
print('pembaca log diganti:', n_reads)

# 2. logMutate / logPrepend: cabang mysql
rep("function logMutate($fn, $limit = null) {\n",
    "function logMutate($fn, $limit = null) {\n"
    "    if (deiStorageMysql()) return logDbMutate($fn);   // v1.2.71: tabel dei_log, riwayat tidak dipangkas\n")
rep("function logPrepend($entry, $limit) {\n",
    "// v1.2.71: di mode mysql cukup INSERT; nilai kembali hanya [entri baru] -- jangan diandalkan.\n"
    "function logPrepend($entry, $limit) {\n"
    "    if (deiStorageMysql()) { logDbInsert($entry); return [$entry]; }\n")

# 3. sisipkan blok driver setelah logPrepend
anchor = "    return logMutate(function (&$logs) use ($entry) { array_unshift($logs, $entry); }, $limit);\n}\n"
rep(anchor, anchor + (HERE / 'block_storage.php').read_text(encoding='utf-8'))

# 4. hitungan lead pakai log per nomor di mode mysql
rep("    $logs = logPrepend(array_merge($logBase, ['a' => $answer], $deiAiError ? ['ai_error' => true] : []), $logLimit);  // v1.2.17 + v1.2.58 kunci\n",
    "    $logs = logPrepend(array_merge($logBase, ['a' => $answer], $deiAiError ? ['ai_error' => true] : []), $logLimit);  // v1.2.17 + v1.2.58 kunci\n"
    "    if (deiStorageMysql()) $logs = logReadByNumber($from, 400);   // v1.2.71\n")

# 5. sesi WA
rep("""function waLoadHistory($from) {
    $f = waSessionFile($from);""",
"""function waLoadHistory($from) {
    if (deiStorageMysql()) {   // v1.2.71
        $st = deiDb()->prepare('SELECT ts, turns FROM dei_wa_sessions WHERE num = ?');
        $st->execute([preg_replace('/[^0-9]/', '', (string)$from)]);
        $r = $st->fetch();
        if (!$r || (int)$r['ts'] < time() - 6 * 3600) return [];
        $t = json_decode($r['turns'], true);
        return is_array($t) ? $t : [];
    }
    $f = waSessionFile($from);""")
rep("""function waSaveHistory($from, $turns) {
""",
"""function waSaveHistory($from, $turns) {
    if (deiStorageMysql()) {   // v1.2.71
        deiDb()->prepare('INSERT INTO dei_wa_sessions (num, ts, turns) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE ts = VALUES(ts), turns = VALUES(turns)')
            ->execute([preg_replace('/[^0-9]/', '', (string)$from), time(), logEncode(array_values(array_slice($turns, -16)))]);
        return;
    }
""")

# 6. kontak
rep("""function waGetContacts() {
    $c = readJson(CONTACTS_FILE, []);""",
"""function waGetContacts() {
    if (deiStorageMysql()) {   // v1.2.71
        $out = [];
        foreach (deiDb()->query('SELECT num, body FROM dei_contacts')->fetchAll() as $r) {
            $c = json_decode($r['body'], true);
            if (is_array($c)) $out[(string)$r['num']] = $c;
        }
        return $out;
    }
    $c = readJson(CONTACTS_FILE, []);""")
rep("""    $nameWa = trim((string)$nameWa);
    $all = waGetContacts();
    $now = date('Y-m-d H:i:s');
    if (!isset($all[$number]) || !is_array($all[$number])) {
        $all[$number] = ['name_wa' => '', 'name_manual' => '', 'first_seen' => $now, 'last_seen' => $now];
    }
    if ($nameWa !== '') $all[$number]['name_wa'] = mb_substr($nameWa, 0, 100);
    $all[$number]['last_seen'] = $now;
    writeJson(CONTACTS_FILE, $all);
}""",
"""    $nameWa = trim((string)$nameWa);
    waContactUpdate($number, function (&$c) use ($nameWa) {   // v1.2.71: atomik, dua mode
        if ($nameWa !== '') $c['name_wa'] = mb_substr($nameWa, 0, 100);
        $c['last_seen'] = date('Y-m-d H:i:s');
    });
}""")
rep("    $all = ($contacts === null) ? waGetContacts() : $contacts;\n",
    "    $all = ($contacts === null) ? waContactsFor($number) : $contacts;   // v1.2.71\n", count=3)
rep("""    $all = waGetContacts();
    $now = date('Y-m-d H:i:s');
    if (!isset($all[$number]) || !is_array($all[$number])) {
        $all[$number] = ['name_wa' => '', 'name_manual' => '', 'first_seen' => $now, 'last_seen' => $now];
    }
    $all[$number]['stage']            = $stage;
    $all[$number]['vip']              = ($stage === 'active_customer') ? (bool)$vip : false;
    $all[$number]['stage_updated_at'] = $now;
    writeJson(CONTACTS_FILE, $all);
    return true;""",
"""    waContactUpdate($number, function (&$c) use ($stage, $vip) {   // v1.2.71
        $c['stage']            = $stage;
        $c['vip']              = ($stage === 'active_customer') ? (bool)$vip : false;
        $c['stage_updated_at'] = date('Y-m-d H:i:s');
    });
    return true;""")
rep("""    $all = waGetContacts();
    $now = date('Y-m-d H:i:s');
    if (!isset($all[$number]) || !is_array($all[$number])) {
        $all[$number] = ['name_wa' => '', 'name_manual' => '', 'first_seen' => $now, 'last_seen' => $now];
    }
    if ($custName !== null) $all[$number]['cust_name'] = mb_substr(trim((string)$custName), 0, 100);
    if ($custDob  !== null) $all[$number]['cust_dob']  = $custDob;
    writeJson(CONTACTS_FILE, $all);
    return true;""",
"""    waContactUpdate($number, function (&$c) use ($custName, $custDob) {   // v1.2.71
        if ($custName !== null) $c['cust_name'] = mb_substr(trim((string)$custName), 0, 100);
        if ($custDob  !== null) $c['cust_dob']  = $custDob;
    });
    return true;""")
rep("""                $allC = waGetContacts();
                if (!isset($allC[$phone]) || !is_array($allC[$phone])) {
                    $allC[$phone] = [
                        'name_wa'    => '',
                        'name_manual'=> '',
                        'first_seen' => $now,
                        'last_seen'  => $now,
                        'stage'      => 'new',
                    ];
                }
                // Koreksi manual agent tidak ditimpa.
                if (trim((string)($allC[$phone]['name_manual'] ?? '')) === '') {
                    $allC[$phone]['name_manual'] = $name;
                }
                $allC[$phone]['last_seen']   = $now;
                $allC[$phone]['web_consent'] = $consent;
                if (empty($allC[$phone]['source'])) $allC[$phone]['source'] = 'web_widget';
                writeJson(CONTACTS_FILE, $allC);""",
"""                waContactUpdate($phone, function (&$c, $isNew) use ($name, $consent, $now) {   // v1.2.71
                    if ($isNew) $c['stage'] = 'new';
                    // Koreksi manual agent tidak ditimpa.
                    if (trim((string)($c['name_manual'] ?? '')) === '') $c['name_manual'] = $name;
                    $c['last_seen']   = $now;
                    $c['web_consent'] = $consent;
                    if (empty($c['source'])) $c['source'] = 'web_widget';
                });""")
rep("""        $all = waGetContacts();
        $now = date('Y-m-d H:i:s');
        if (!isset($all[$num]) || !is_array($all[$num])) {
            $all[$num] = ['name_wa' => '', 'name_manual' => '', 'first_seen' => $now, 'last_seen' => $now];
        }
        $all[$num]['name_manual'] = $nm;   // kosong = kembali pakai nama profil WA
        writeJson(CONTACTS_FILE, $all);
        jsonOut(['ok' => true, 'number' => $num, 'name' => waContactName($num, $all)]);""",
"""        waContactUpdate($num, function (&$c) use ($nm) { $c['name_manual'] = $nm; });   // v1.2.71; kosong = kembali pakai nama profil WA
        jsonOut(['ok' => true, 'number' => $num, 'name' => waContactName($num)]);""")
if 'writeJson(CONTACTS_FILE' in src.replace("            writeJson(CONTACTS_FILE, $all);\n            return $row;", ''):
    raise SystemExit('masih ada writeJson(CONTACTS_FILE) di luar waContactUpdate')

# 6b. nama kontak di log: lewat waGetContacts (dua mode), bukan baca berkas langsung
rep("    $c = readJson(DATA_DIR . '/wa-contacts.json', []);\n", "    $c = waGetContacts();   // v1.2.71\n")

# 6c. conv-state: pembaca -> convStateReadAll(); convStateMutate menerima $num (mode mysql: satu baris)
rep("        $all = readJson(CONV_STATE_FILE, []);\n        if (!is_array($all)) $all = [];\n        $res = $fn($all);", "@@CSM@@")
n = src.count('readJson(CONV_STATE_FILE, [])')
src = src.replace('readJson(CONV_STATE_FILE, [])', 'convStateReadAll()')
src = src.replace("@@CSM@@", "        $all = readJson(CONV_STATE_FILE, []);\n        if (!is_array($all)) $all = [];\n        $res = $fn($all);")
print('pembaca conv-state diganti:', n)
rep("function convStateMutate($fn) {\n", "function convStateMutate($fn, $num = null) {\n"
    "    // v1.2.71: mode mysql mengunci satu baris; $num wajib (semua pemanggil mengubah satu nomor)\n"
    "    if (deiStorageMysql()) {\n"
    "        if ($num === null || waNormNum($num) === '') throw new \\RuntimeException('convStateMutate: $num wajib di mode mysql');\n"
    "        return convStateDbMutateOne($fn, $num);\n"
    "    }\n")
for old in ["        convStateMutate(function (&$all) use ($num, $text, $lang, $bye) {",
            "        $inc = convStateMutate(function (&$all) use ($num, $who) {",
            "        $klaim = convStateMutate(function (&$a) use ($num, $lastAt) {",
            "        $ok = convStateMutate(function (&$a) use ($num, $since, $target, $incId) {"]:
    if src.count(old) != 1: raise SystemExit('anchor conv ' + old)
    i = src.index(old) + len(old)
    # cari penutup "});" pertama setelah pembuka pada indentasi yang sama
    ind = old[:len(old) - len(old.lstrip())]
    k = src.index("\n" + ind + "});", i)
    src = src[:k] + "\n" + ind + "}, $num);" + src[k + len("\n" + ind + "});"):]
rep("            convStateMutate(function (&$a) use ($num) { if (isset($a[$num])) $a[$num]['esc_acked'] = 1; });",
    "            convStateMutate(function (&$a) use ($num) { if (isset($a[$num])) $a[$num]['esc_acked'] = 1; }, $num);")
left = [l for l in src.split('\n') if 'convStateMutate(function' in l]
print('pemanggil convStateMutate:', len(left))

# 7. kunci untuk baca-ubah-tulis berkas status yang disentuh tiap pesan
def wrap(sig, params, lock):
    global src
    head = f"function {sig} {{\n"
    if src.count(head) != 1:
        raise SystemExit('fungsi tidak ditemukan: ' + sig)
    name = sig.split('(')[0]
    uses = ', '.join(p.split('=')[0].strip() for p in params.split(',') if p.strip())
    call_args = uses
    use_clause = f" use ({uses})" if uses else ''
    wrapper = (f"// v1.2.71: dibungkus kunci '{lock}' supaya worker paralel tidak saling menimpa.\n"
               f"function {sig} {{\n"
               f"    return deiWithLock('{lock}', function (){use_clause} {{ return {name}_nolock({call_args}); }});\n"
               f"}}\n")
    src = src.replace(head, wrapper + f"function {name}_nolock{sig[len(name):]} {{\n")

wrap('waSetMode($from, $mode)', '$from, $mode', 'wa-modes')
wrap('waModeSweepIdle()', '', 'wa-modes')
wrap('waClaimSet($number, $claim)', '$number, $claim', 'wa-claims')
wrap('waClaimTouchActivity($number, $agent)', '$number, $agent', 'wa-claims')
wrap('waClaimAutoProcess()', '', 'wa-claims')
wrap('waAuditLog($action, $agent, $number, $extra = [])', '$action, $agent, $number, $extra', 'wa-audit')
wrap('recordUsage($usage)', '$usage', 'usage')
# rate limit: Redis di mode antrean, kunci berkas di mode file
rep("function checkRateLimit($ip, $limit) {\n",
"""// v1.2.71: mode antrean memakai Redis (INCR per jam); mode file memakai kunci berkas.
function checkRateLimit($ip, $limit) {
    if (deiQueueRedis()) {
        try {
            $k = 'rl:' . $ip . ':' . intdiv(time(), 3600);
            $n = deiRedis()->incr($k);
            if ($n === 1) deiRedis()->expire($k, 3700);
            return $n <= $limit;
        } catch (\\Throwable $e) { error_log('ratelimit redis: ' . $e->getMessage()); return true; }
    }
    return deiWithLock('ratelimit', function () use ($ip, $limit) { return checkRateLimit_nolock($ip, $limit); });
}
function checkRateLimit_nolock($ip, $limit) {
""")

# 8. respondAndContinue: LiteSpeed juga
rep("    echo $body;\n    fastcgi_finish_request();\n",
    "    echo $body;\n"
    "    if (function_exists('fastcgi_finish_request')) fastcgi_finish_request();\n"
    "    elseif (function_exists('litespeed_finish_request')) litespeed_finish_request();   // v1.2.71: LiteSpeed (Niagahoster)\n")
src = src.replace("$earlyAck = function_exists('fastcgi_finish_request');",
                  "$earlyAck = function_exists('fastcgi_finish_request') || function_exists('litespeed_finish_request');   // v1.2.71")

# 9. webhook Meta: isi loop dipindah ke fungsi bersama (dipakai webhook & worker)
start = """        $payload  = json_decode($raw, true);
        $logLimit = (int)($s['api']['log_limit'] ?? 500);
        $keepCtx  = ($wa['keep_context'] ?? true);

        foreach (($payload['entry'] ?? []) as $entry) {"""
end = """        if (!$earlyAck) { echo 'EVENT_RECEIVED'; }
        exit;
    }

    /* ---------- PUBLIC: webhook Fonnte"""
i = src.index(start); j = src.index(end)
if src.count(start) != 1 or src.count(end) != 1: raise SystemExit('anchor webhook')
loop = src[i + len(start) - len("        foreach (($payload['entry'] ?? []) as $entry) {"):j]
msg_old = """                foreach ($messages as $msg) {
                    $from = $msg['from'] ?? '';
                    if ($from === '') continue;
                    // v1.2.19: simpan nama kontak (tidak menimpa koreksi manual)
                    $deiFromKey = preg_replace('/\\D/', '', (string)$from);
                    $deiWaName  = $waProfileNames[$deiFromKey] ?? '';
                    try { waSaveContact($from, $deiWaName); }
                    catch (\\Throwable $e) { error_log('waSaveContact: ' . $e->getMessage()); }

                    if (($msg['type'] ?? '') !== 'text') {
                        // v1.2.58: mode Manual tidak membalas otomatis; tandai saja supaya agent tahu
                        if (deiIsManual($s)) {
                            waProcessIncoming($s, $wa, $from, deiNonTextLabel($msg['type'] ?? ''), $deiWaName, $change['value']['metadata'] ?? []);
                            continue;
                        }
                        waSend($wa, $from, 'Maaf, untuk saat ini saya hanya bisa membalas pesan teks.');
                        continue;
                    }
                    $text = trim($msg['text']['body'] ?? '');
                    if ($text === '') continue;
                    // v1.2.36: alur pemrosesan dipindah ke fungsi bersama
                    waProcessIncoming($s, $wa, $from, $text, $deiWaName, $change['value']['metadata'] ?? []);
                }
"""
if loop.count(msg_old) != 1: raise SystemExit('anchor loop pesan')
msg_new = """                foreach ($messages as $msg) {
                    $from = $msg['from'] ?? '';
                    if ($from === '') continue;
                    // v1.2.71: satu nomor diproses berurutan (mode antrean); nomor lain paralel
                    $meta = $change['value']['metadata'] ?? [];
                    deiNumLock($from, function () use ($s, $wa, $msg, $waProfileNames, $meta) {
                        waHandleMetaMessage($s, $wa, $msg, $waProfileNames, $meta);
                    });
                }
"""
loop = loop.replace(msg_old, msg_new)
# dedent 4 spasi
loop = '\n'.join(l[4:] if l.startswith('    ') else l for l in loop.split('\n'))
func = """/* v1.2.71: isi kiriman webhook Meta — dipakai webhook (mode sync) dan worker (mode redis). */
function waHandleMetaPayload($s, $wa, $payload) {
    if (!is_array($payload)) return;
    if (!($wa['enabled'] ?? false)) return;
    if (($wa['provider'] ?? 'meta') !== 'meta') return;
    $logLimit = (int)($s['api']['log_limit'] ?? 500);
    $keepCtx  = ($wa['keep_context'] ?? true);

""" + loop.rstrip() + """
}

/* v1.2.71: satu pesan masuk dari Meta. Kiriman ulang Meta (wamid sama) diabaikan. */
function waHandleMetaMessage($s, $wa, $msg, $waProfileNames, $metadata) {
    $from = $msg['from'] ?? '';
    if ($from === '') return;
    $wamid = (string)($msg['id'] ?? '');
    if ($wamid !== '' && waMsgSeen($wamid)) return;
    try {
        // v1.2.19: simpan nama kontak (tidak menimpa koreksi manual)
        $deiFromKey = preg_replace('/\\D/', '', (string)$from);
        $deiWaName  = $waProfileNames[$deiFromKey] ?? '';
        try { waSaveContact($from, $deiWaName); }
        catch (\\Throwable $e) { error_log('waSaveContact: ' . $e->getMessage()); }

        if (($msg['type'] ?? '') !== 'text') {
            // v1.2.58: mode Manual tidak membalas otomatis; tandai saja supaya agent tahu
            if (deiIsManual($s)) {
                waProcessIncoming($s, $wa, $from, deiNonTextLabel($msg['type'] ?? ''), $deiWaName, $metadata);
                return;
            }
            waSend($wa, $from, 'Maaf, untuk saat ini saya hanya bisa membalas pesan teks.');
            return;
        }
        $text = trim($msg['text']['body'] ?? '');
        if ($text === '') return;
        // v1.2.36: alur pemrosesan dipindah ke fungsi bersama
        waProcessIncoming($s, $wa, $from, $text, $deiWaName, $metadata);
    } finally {
        // Ditandai juga saat gagal di tengah jalan: lebih baik tidak dibalas ganda.
        if ($wamid !== '') waMsgMarkSeen($wamid);
    }
}

"""
src = src[:i] + """        waHandleMetaPayload($s, $wa, json_decode($raw, true));   // v1.2.71: isi loop pindah ke fungsi bersama
""" + src[j:]
rep("// Per-number short conversation memory (flat-file, expires after 6h idle).\n",
    func + "// Per-number short conversation memory (flat-file, expires after 6h idle).\n")
# enqueue sebelum earlyAck
rep("""        // Acknowledge Meta right away on PHP-FPM, then keep working in the
        // background.""",
"""        // v1.2.71: mode antrean — simpan & antre, Meta langsung dapat 200; worker yang memproses.
        // Kalau Redis bermasalah, jatuh ke pemrosesan langsung (perilaku lama).
        if (deiQueueRedis()) {
            try {
                deiRedis()->lPush('q:wa', json_encode(['raw' => $raw, 'at' => time(), 'try' => 0]));
                http_response_code(200);
                echo 'EVENT_RECEIVED';
                exit;
            } catch (\\Throwable $e) { error_log('antrean WA gagal, proses langsung: ' . $e->getMessage()); }
        }

        // Acknowledge Meta right away on PHP-FPM, then keep working in the
        // background.""")

# 10. cron_tick: bersih-bersih sesi + segarkan cache lisensi/kuota (CLI)
rep("""        try { $r['escalated'] = escalationSweep($s); } catch (\\Throwable $e) { $r['escalated'] = []; $r['err_escalation'] = $e->getMessage(); }
""",
"""        try { $r['escalated'] = escalationSweep($s); } catch (\\Throwable $e) { $r['escalated'] = []; $r['err_escalation'] = $e->getMessage(); }
        try { $r['sessions_purged'] = deiPurgeSessions(); } catch (\\Throwable $e) { $r['err_purge'] = $e->getMessage(); }   // v1.2.71
        // v1.2.71: di server sendiri cron (CLI) yang menyegarkan cache pusat, bukan pesan masuk
        if (PHP_SAPI === 'cli') { try { getLicenseStatus($s); getCapStatus($s); } catch (\\Throwable $e) {} }
""")

# 11a. izinkan aksi CLI baru
rep("    if (!in_array($action, ['cron_tick'], true)) { fwrite(STDERR, \"CLI hanya untuk action=cron_tick\\n\"); exit(1); }",
    "    if (!in_array($action, ['cron_tick', 'wa_worker', 'wa_queue_status', 'db_init', 'db_import', 'update_cli'], true)) { fwrite(STDERR, \"CLI: action=cron_tick|wa_worker|wa_queue_status|db_init|db_import|update_cli\\n\"); exit(1); }   // v1.2.71\n"
    "    // v1.2.71: update_cli = update_check lalu langsung update_apply (dipakai update-all.sh di server sendiri)\n"
    "    if ($action === 'update_cli') { $action = 'update_check'; $GLOBALS['dei_cli_chain'] = true; }")

# 11b. updater bisa dijalankan dari CLI (server sendiri) — tetap lewat kode updater yang sama
rep("    case 'update_check': {\n        requireAuth(['super_admin']);\n",
    "    case 'update_check': {\n        if (PHP_SAPI !== 'cli') requireAuth(['super_admin']);   // v1.2.71: CLI = admin server\n")
rep(r"""        jsonOut([
            'ok'               => true,
            'current'          => $current,
            'latest'           => $data['latest'] ?? null,""", r"""        // v1.2.71: `php api/index.php action=update_cli` -> langsung pasang, tanpa dashboard
        if (!empty($GLOBALS['dei_cli_chain'])) {
            if (empty($data['update_available'])) { echo "update_cli: sudah versi terbaru ($current)\n"; exit(0); }
            $GLOBALS['dei_cli_update'] = ['zip_url' => $data['zip_url'] ?? '', 'manifest_url' => $data['manifest_url'] ?? '', 'target' => $data['latest'] ?? ''];
            goto dei_cli_update_apply;
        }
        jsonOut([
            'ok'               => true,
            'current'          => $current,
            'latest'           => $data['latest'] ?? null,""")
rep(r"""    case 'update_apply': {
        requireAuth(['super_admin']);
        $in = bodyInput();""", r"""    case 'update_apply': {
        dei_cli_update_apply:   // v1.2.71: tujuan lompatan update_cli
        if (PHP_SAPI === 'cli' && !empty($GLOBALS['dei_cli_update'])) { $in = $GLOBALS['dei_cli_update']; }
        else { requireAuth(['super_admin']); $in = bodyInput(); }""")

# 11. aksi CLI baru: wa_worker, wa_queue_status, db_init, db_import
rep("    case 'cron_tick': {\n", (HERE / 'block_actions.php').read_text(encoding='utf-8') + "    case 'cron_tick': {\n")

P.write_text(src, encoding='utf-8')
print('OK v1.2.71 terpasang')
