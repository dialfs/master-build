#!/usr/bin/env python3
"""v1.2.153 jadwal-kirim — backend. Idempoten. Pakai: patch_api.py <api/index.php>"""
import sys, shutil, time
P = sys.argv[1]
src = open(P, encoding='utf-8').read()
if 'v1.2.153: jadwal-kirim' in src:
    print('sudah dipatch'); sys.exit(0)
shutil.copy2(P, P + '.bak-v12153-' + time.strftime('%Y%m%d-%H%M%S'))

def rep(old, new, cnt=1):
    global src
    n = src.count(old)
    assert n == cnt, f'anchor {n}x (harus {cnt}): {old[:80]!r}'
    src = src.replace(old, new)

rep("define('DEI_VERSION', 'v1.2.152');   // v1.2.152: tombol-warna",
    "define('DEI_VERSION', 'v1.2.153');   // v1.2.153: jadwal-kirim")

rep("define('USERS_FILE', DATA_DIR . '/users.json');\n",
    "define('USERS_FILE', DATA_DIR . '/users.json');\n"
    "define('SCHED_FILE', DATA_DIR . '/sched-msgs.json');   // v1.2.153: jadwal-kirim\n"
    "define('SCHED_DIR', DATA_DIR . '/sched-msgs');\n")

FUNCS = r'''/* ============================================================================
 * v1.2.153: jadwal-kirim — pesan WA terjadwal dari thread Percakapan WA.
 * data/sched-msgs.json {items:{id:{...}}} dikunci deiWithLock('sched'); sama untuk
 * mode file & mysql (data kecil). Yang selesai diarsip ke data/sched-msgs/YYYY-MM.jsonl
 * dan tetap di berkas 48 jam supaya statusnya terlihat di thread.
 * Dikirim oleh cron_tick (schedSweep) memakai waSend, dicatat sebagai balasan agent.
 * ========================================================================== */
define('SCHED_MIN_AHEAD', 60);          // dtk (UI meminta >= 2 menit)
define('SCHED_MAX_AHEAD', 30 * 86400);
define('SCHED_MAX_LATE', 6 * 3600);    // cron mati lebih lama -> expired
define('SCHED_RETRY', 1800);        // gagal kirim: dicoba ulang tiap tick selama 30 menit
define('SCHED_PER_NUM', 10);
define('SCHED_PER_TENANT', 500);
define('SCHED_KEEP', 2 * 86400);

function schedMutate($fn) {
    return deiWithLock('sched', function () use ($fn) {
        $db = readJson(SCHED_FILE, []);
        if (!is_array($db) || !is_array($db['items'] ?? null)) $db = ['items' => []];
        $r = $fn($db);
        writeJson(SCHED_FILE, $db);
        return $r;
    });
}
function schedReadAll() {
    $db = readJson(SCHED_FILE, []);
    return (is_array($db) && is_array($db['items'] ?? null)) ? $db['items'] : [];
}
function schedArchive($it) {
    if (!is_dir(SCHED_DIR)) @mkdir(SCHED_DIR, 0755, true);
    @file_put_contents(SCHED_DIR . '/' . wibDate('Y-m', (int)($it['created_at'] ?? time())) . '.jsonl',
        json_encode($it, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_INVALID_UTF8_SUBSTITUTE) . "\n", FILE_APPEND | LOCK_EX);
}
function schedPublic($it, $u = null) {
    $o = array_intersect_key($it, array_flip(['id', 'num', 'at', 'text', 'by', 'by_name', 'created_at', 'cancel_on_reply', 'status', 'sent_at', 'reason', 'last_err', 'cancelled_by']));
    if ($u) $o['can'] = schedCanManage($u, $it);
    return $o;
}
function schedCanManage($u, $it) {
    return deiIsLead((string)($u['role'] ?? '')) || (string)($it['by'] ?? '') === (string)($u['username'] ?? '');
}
// Agent biasa hanya melihat jadwalnya sendiri; Supervisor/Admin/SA melihat semua.
function schedVisible($u, $num = '') {
    $out = [];
    $lead = deiIsLead((string)($u['role'] ?? ''));
    foreach (schedReadAll() as $it) {
        if ($num !== '' && (string)($it['num'] ?? '') !== $num) continue;
        if (!$lead && (string)($it['by'] ?? '') !== (string)($u['username'] ?? '')) continue;
        $out[] = $it;
    }
    usort($out, function ($a, $b) { return (int)$a['at'] <=> (int)$b['at']; });
    return $out;
}
function schedPendingCounts($u) {
    $c = [];
    foreach (schedVisible($u) as $it) {
        if (in_array($it['status'] ?? '', ['pending', 'sending'], true)) { $n = (string)$it['num']; $c[$n] = ($c[$n] ?? 0) + 1; }
    }
    return $c;
}
// Pesan masuk terakhir (detik) dari nomor ini; $winCh = '' -> semua nomor bisnis.
function schedLastInbound($num, $winCh, $logs = null) {
    foreach (($logs === null ? logReadAll() : $logs) as $e) {
        if (($e['channel'] ?? '') === 'whatsapp' && waNormNum($e['ip'] ?? '') === $num && ($e['q'] ?? '') !== ''
            && ($winCh === null || waInboundOnCh($e, $winCh))) return (int)strtotime((string)$e['ts']);
    }
    return 0;
}
// Batas akhir boleh kirim teks bebas (WhatsApp API resmi: 24 jam sejak pesan pelanggan).
function schedWindowEnd($num, $s, $logs = null) {
    if (waWinFree($num, $s)) return PHP_INT_MAX;
    $li = schedLastInbound($num, waWinCh($num, $s), $logs);
    return $li > 0 ? $li + 86400 : 0;
}
// Pemeriksaan saat membuat/mengubah jadwal (memanggil jsonOut bila ditolak).
function schedCheckInput($u, $num, $text, $at, $s, $selfId = '') {
    deiGuardSpvScope($u, $num);
    deiGuardAgentStage($u, $num);
    if (($u['role'] ?? '') === 'wa_agent') {
        $cl = waClaimGet($num);
        if ($cl && ($cl['agent_username'] ?? '') !== $u['username']) jsonOut(['ok' => false, 'error' => 'Chat ini dipegang ' . ($cl['agent_username'] ?? 'agent lain') . '. Minta take-over dulu.'], 403);
    }
    if ($text === '') jsonOut(['ok' => false, 'error' => 'Isi pesan wajib diisi.'], 400);
    $now = time();
    if ($at < $now + SCHED_MIN_AHEAD) jsonOut(['ok' => false, 'error' => 'Waktu kirim minimal 2 menit dari sekarang.'], 400);
    if ($at > $now + SCHED_MAX_AHEAD) jsonOut(['ok' => false, 'error' => 'Jadwal paling lama 30 hari ke depan.'], 400);
    $we = schedWindowEnd($num, $s);
    if ($we !== PHP_INT_MAX && $at >= $we) {
        jsonOut(['ok' => false, 'error' => $we <= $now
            ? 'Jendela 24 jam tertutup — WhatsApp API resmi tidak mengizinkan teks bebas sampai pelanggan mengirim pesan lagi.'
            : 'Jendela 24 jam WhatsApp API resmi untuk chat ini berakhir ' . wibDate('d/m H:i', $we) . ' WIB. Jadwalkan sebelum jam itu.'], 400);
    }
    $nNum = 0; $nAll = 0;
    foreach (schedReadAll() as $it) {
        if (($it['id'] ?? '') === $selfId || !in_array($it['status'] ?? '', ['pending', 'sending'], true)) continue;
        $nAll++; if ((string)$it['num'] === $num) $nNum++;
    }
    if ($selfId === '' && $nNum >= SCHED_PER_NUM) jsonOut(['ok' => false, 'error' => 'Maksimal ' . SCHED_PER_NUM . ' jadwal tertunda per kontak.'], 400);
    if ($selfId === '' && $nAll >= SCHED_PER_TENANT) jsonOut(['ok' => false, 'error' => 'Maksimal ' . SCHED_PER_TENANT . ' jadwal tertunda per tenant.'], 400);
}
function schedUserByName($un) {
    foreach ((array)readJson(USERS_FILE, []) as $x) { if (($x['username'] ?? '') === $un) return $x; }
    return null;
}
// Kirim satu jadwal. Hasil: ['st' => sent|skipped|expired|failed|pending, 'reason' => ...]
function schedSendOne($it, $s, $now, &$logs) {
    $num = (string)$it['num'];
    $at  = (int)$it['at'];
    if ($now - $at > SCHED_MAX_LATE) return ['st' => 'expired', 'reason' => 'Terlambat lebih dari 6 jam dari jadwal (cron tidak berjalan) — tidak dikirim.'];
    if ($logs === null) $logs = logReadAll();
    if (!empty($it['cancel_on_reply'])) {
        $li = schedLastInbound($num, null, $logs);
        if ($li > (int)$it['created_at']) return ['st' => 'skipped', 'reason' => 'Pelanggan sudah membalas setelah jadwal dibuat — dibatalkan otomatis.'];
    }
    $by = schedUserByName((string)$it['by']);
    if (!$by) return ['st' => 'skipped', 'reason' => 'Akun pembuat jadwal sudah dihapus.'];
    if (($by['role'] ?? '') === 'wa_agent') {
        $cl = waClaimGet($num);
        if ($cl && ($cl['agent_username'] ?? '') !== $it['by']) return ['st' => 'skipped', 'reason' => 'Chat sudah dipegang ' . ($cl['agent_username'] ?? 'agent lain') . '.'];
        if (!deiAgentCanReplyNum($by, $num)) return ['st' => 'skipped', 'reason' => 'Lead Rating kontak di luar izin balas akun pembuat.'];
    }
    $we = schedWindowEnd($num, $s, $logs);
    if ($we !== PHP_INT_MAX && $now >= $we) return ['st' => 'skipped', 'reason' => 'Jendela 24 jam WhatsApp API resmi sudah tertutup.'];
    $text = (string)$it['text'];
    if (!empty($GLOBALS['dei_dry'])) { $GLOBALS['esc_dry_log'][] = ['sched' => $it['id'], 'to' => $num, 'text' => $text]; return ['st' => 'pending', 'dry' => 1]; }
    $wa = waConf($s);
    $GLOBALS['dei_out_src'] = 'agent';
    $GLOBALS['wa_reply_to'] = '';
    if (!waSend($wa, $num, $text)) {
        $wr = trim((string)($GLOBALS['wa_last_error'] ?? '')) ?: 'gagal mengirim via WhatsApp';
        if ($now - $at < SCHED_RETRY) return ['st' => 'pending', 'reason' => '', 'last_err' => $wr];
        return ['st' => 'failed', 'reason' => 'Gagal terkirim selama 30 menit: ' . $wr];
    }
    $oid = (string)($GLOBALS['wa_last_out_id'] ?? '');
    try { waSetMode($num, 'human', 'agent_reply'); } catch (\Throwable $e) {}
    try { deiRecordAgentReply($num, (string)$it['by'], 'sched'); } catch (\Throwable $e) {}
    try { convReply($num, 'agent'); } catch (\Throwable $e) {}
    if ($wa['keep_context'] ?? true) {
        $h = waLoadHistory($num); $h[] = ['role' => 'assistant', 'content' => $text]; waSaveHistory($num, $h);
    }
    logPrepend([
        'ts' => date('Y-m-d H:i:s'), 'q' => '', 'a' => $text, 'ip' => $num,
        'channel' => 'whatsapp', 'dir' => 'manual', 'sched' => (string)$it['id'], 'sched_by' => (string)$it['by'],
        'utm_source' => 'whatsapp', 'utm_medium' => 'manual', 'utm_campaign' => '', 'page' => '', 'referrer' => '',
    ] + array_filter(['out_id' => $oid]), (int)($s['api']['log_limit'] ?? 500));
    $logs = null;   // log berubah
    try { waAuditLog('sched_sent', (string)$it['by'], $num, ['id' => $it['id'], 'late' => max(0, $now - $at)]); } catch (\Throwable $e) {}
    return ['st' => 'sent'];
}
// Ambil (kunci) satu jadwal untuk dikirim -> status 'sending'. null bila sudah diambil/berubah.
function schedTake($id, $now, $force = false) {
    return schedMutate(function (&$db) use ($id, $now, $force) {
        $x = $db['items'][$id] ?? null;
        if (!$x || ($x['status'] ?? '') !== 'pending' || (!$force && (int)$x['at'] > $now)) return null;
        $db['items'][$id]['status'] = 'sending'; $db['items'][$id]['try_at'] = $now;
        return $db['items'][$id];
    });
}
function schedFinish($id, $res) {
    $fin = schedMutate(function (&$db) use ($id, $res) {
        if (!isset($db['items'][$id])) return null;
        $x = &$db['items'][$id];
        $x['status'] = $res['st'];
        if (array_key_exists('last_err', $res)) $x['last_err'] = $res['last_err'];
        if ($res['st'] === 'pending') return null;
        $x['reason'] = (string)($res['reason'] ?? '');
        $x['done_at'] = time();
        if ($res['st'] === 'sent') { $x['sent_at'] = time(); unset($x['last_err']); }
        return $x;
    });
    if ($fin) schedArchive($fin);
    return $fin;
}
function schedSweep($s) {
    $now = time();
    $all = schedReadAll();
    if (!$all) return [];
    $due = []; $stale = false; $old = false;
    foreach ($all as $id => $it) {
        $st = $it['status'] ?? '';
        if ($st === 'pending' && (int)$it['at'] <= $now) $due[] = $it;
        elseif ($st === 'sending' && $now - (int)($it['try_at'] ?? 0) > 600) $stale = true;
        elseif (!in_array($st, ['pending', 'sending'], true) && $now - (int)($it['done_at'] ?? $now) > SCHED_KEEP) $old = true;
    }
    if ($stale || $old) schedMutate(function (&$db) use ($now) {
        foreach ($db['items'] as $id => $x) {
            $st = $x['status'] ?? '';
            if ($st === 'sending' && $now - (int)($x['try_at'] ?? 0) > 600) $db['items'][$id]['status'] = 'pending';   // proses sebelumnya mati di tengah jalan
            elseif (!in_array($st, ['pending', 'sending'], true) && $now - (int)($x['done_at'] ?? $now) > SCHED_KEEP) unset($db['items'][$id]);
        }
    });
    if (!$due) return [];
    usort($due, function ($a, $b) { return (int)$a['at'] <=> (int)$b['at']; });
    $out = []; $logs = null;
    wa_sched_loop:
    foreach (array_slice($due, 0, 20) as $it) {
        $t = schedTake((string)$it['id'], $now);
        if (!$t) continue;
        try { $res = schedSendOne($t, $s, $now, $logs); }
        catch (\Throwable $e) { $res = ['st' => 'pending', 'last_err' => $e->getMessage()]; }
        schedFinish((string)$t['id'], $res);
        $out[] = ['id' => $t['id'], 'num' => $t['num'], 'st' => $res['st']] + (!empty($res['dry']) ? ['dry' => 1] : []);
    }
    return $out;
}

'''
FUNCS = FUNCS.replace('    wa_sched_loop:\n', '')
rep("function autoClosingSweep($s) {\n", FUNCS + "function autoClosingSweep($s) {\n")

# cron_tick
rep("        try { $r['escalated'] = escalationSweep($s); }",
    "        try { $scr = schedSweep($s); if ($scr) $r['sched'] = $scr; } catch (\\Throwable $e) { $r['err_sched'] = $e->getMessage(); }   // v1.2.153: jadwal-kirim\n"
    "        try { $r['escalated'] = escalationSweep($s); }")

ACTIONS = r'''    /* ---------- v1.2.153: jadwal-kirim — pesan WA terjadwal ---------- */
    case 'sched_list': {
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $num = waNormNum($_GET['number'] ?? '');
        if ($num !== '') deiGuardAgentPrivate($u, $num);
        jsonOut(['ok' => true, 'items' => array_map(function ($x) use ($u) { return schedPublic($x, $u); }, schedVisible($u, $num))]);
        break;
    }
    case 'sched_create':
    case 'sched_update': {
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $s = getSettings();
        $in = bodyInput();
        $text = trim((string)($in['text'] ?? ''));
        if (mb_strlen($text) > 4000) $text = mb_substr($text, 0, 4000);
        $at = (int)($in['at'] ?? 0);
        $cor = !array_key_exists('cancel_on_reply', $in) || !empty($in['cancel_on_reply']);
        if ($action === 'sched_update') {
            $id = (string)($in['id'] ?? '');
            $cur = schedReadAll()[$id] ?? null;
            if (!$cur || ($cur['status'] ?? '') !== 'pending') jsonOut(['ok' => false, 'error' => 'Jadwal tidak ditemukan atau sudah diproses.'], 404);
            if (!schedCanManage($u, $cur)) jsonOut(['ok' => false, 'error' => 'Hanya pembuat jadwal atau Supervisor/Admin yang boleh mengubah.'], 403);
            $num = (string)$cur['num'];
            schedCheckInput($u, $num, $text, $at, $s, $id);
            $it = schedMutate(function (&$db) use ($id, $text, $at, $cor) {
                $x = $db['items'][$id] ?? null;
                if (!$x || ($x['status'] ?? '') !== 'pending') return null;
                $db['items'][$id]['text'] = $text; $db['items'][$id]['at'] = $at; $db['items'][$id]['cancel_on_reply'] = $cor ? 1 : 0;
                $db['items'][$id]['updated_at'] = time();
                return $db['items'][$id];
            });
            if (!$it) jsonOut(['ok' => false, 'error' => 'Jadwal sudah diproses.'], 409);
            waAuditLog('sched_update', $u['username'], $num, ['id' => $id, 'at' => $at]);
        } else {
            $num = waNormNum($in['number'] ?? '');
            if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
            deiGuardAgentPrivate($u, $num);
            schedCheckInput($u, $num, $text, $at, $s);
            $it = ['id' => 's' . wibDate('ymd') . bin2hex(random_bytes(4)), 'num' => $num, 'at' => $at, 'text' => $text,
                   'by' => $u['username'], 'by_name' => (string)($u['name'] ?? $u['username']), 'created_at' => time(),
                   'cancel_on_reply' => $cor ? 1 : 0, 'status' => 'pending'];
            schedMutate(function (&$db) use ($it) { $db['items'][$it['id']] = $it; });
            waAuditLog('sched_create', $u['username'], $num, ['id' => $it['id'], 'at' => $at]);
        }
        jsonOut(['ok' => true, 'item' => schedPublic($it, $u)]);
        break;
    }
    case 'sched_cancel': {
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $id = (string)(bodyInput()['id'] ?? '');
        $cur = schedReadAll()[$id] ?? null;
        if (!$cur) jsonOut(['ok' => false, 'error' => 'Jadwal tidak ditemukan.'], 404);
        if (!schedCanManage($u, $cur)) jsonOut(['ok' => false, 'error' => 'Hanya pembuat jadwal atau Supervisor/Admin yang boleh membatalkan.'], 403);
        $fin = schedMutate(function (&$db) use ($id, $u) {
            $x = $db['items'][$id] ?? null;
            if (!$x || ($x['status'] ?? '') !== 'pending') return null;
            $db['items'][$id]['status'] = 'cancelled'; $db['items'][$id]['done_at'] = time();
            $db['items'][$id]['cancelled_by'] = $u['username'];
            $db['items'][$id]['reason'] = 'Dibatalkan oleh ' . ($u['name'] ?? $u['username']) . '.';
            return $db['items'][$id];
        });
        if (!$fin) jsonOut(['ok' => false, 'error' => 'Jadwal sudah diproses (sedang/sudah terkirim).'], 409);
        schedArchive($fin);
        waAuditLog('sched_cancel', $u['username'], (string)$cur['num'], ['id' => $id]);
        jsonOut(['ok' => true]);
        break;
    }
    case 'sched_send_now': {
        $u = requireAuth(['super_admin','admin','wa_agent']);
        $s = getSettings();
        $id = (string)(bodyInput()['id'] ?? '');
        $cur = schedReadAll()[$id] ?? null;
        if (!$cur) jsonOut(['ok' => false, 'error' => 'Jadwal tidak ditemukan.'], 404);
        if (!schedCanManage($u, $cur)) jsonOut(['ok' => false, 'error' => 'Hanya pembuat jadwal atau Supervisor/Admin.'], 403);
        $t = schedTake($id, time(), true);
        if (!$t) jsonOut(['ok' => false, 'error' => 'Jadwal sudah diproses.'], 409);
        $logs = null;
        $t['cancel_on_reply'] = 0;   // dikirim atas perintah langsung
        $t['at'] = time();
        try { $res = schedSendOne($t, $s, time(), $logs); } catch (\Throwable $e) { $res = ['st' => 'pending', 'last_err' => $e->getMessage()]; }
        if ($res['st'] === 'pending') {
            schedFinish($id, $res);
            jsonOut(['ok' => false, 'error' => 'Gagal mengirim: ' . ($res['last_err'] ?? 'coba lagi') . '. Jadwal tetap menunggu.'], 502);
        }
        $fin = schedFinish($id, $res);
        if ($res['st'] !== 'sent') jsonOut(['ok' => false, 'error' => (string)($res['reason'] ?? 'Tidak terkirim.')], 409);
        jsonOut(['ok' => true, 'item' => $fin ? schedPublic($fin, $u) : null]);
        break;
    }

'''
rep("    case 'wa_send_manual': {\n", ACTIONS + "    case 'wa_send_manual': {\n")

# wa_thread: jadwal milik chat ini
rep("            'claim' => waClaimGet($num),   // v1.2.141: filter-chat-terpilih — status claim tidak bergantung pada daftar terfilter\n        ]);",
    "            'claim' => waClaimGet($num),   // v1.2.141: filter-chat-terpilih — status claim tidak bergantung pada daftar terfilter\n"
    "            'sched' => (function () use ($u, $num) { try { return array_map(function ($x) use ($u) { return schedPublic($x, $u); }, schedVisible($u, $num)); } catch (\\Throwable $e) { return []; } })(),   // v1.2.153: jadwal-kirim\n"
    "            'win_end' => (function () use ($num, $s116) { $w = schedWindowEnd($num, $s116); return $w === PHP_INT_MAX ? 0 : $w; })(),\n"
    "        ]);")

# daftar: jumlah jadwal tertunda per nomor
rep("            'agents' => deiIsLead($u['role']) ? deiAssignableUsers($u) : [],\n        ]);",
    "            'agents' => deiIsLead($u['role']) ? deiAssignableUsers($u) : [],\n"
    "            'sched' => (function () use ($u) { try { return (object)schedPendingCounts($u); } catch (\\Throwable $e) { return (object)[]; } })(),   // v1.2.153: jadwal-kirim\n"
    "        ]);")

open(P, 'w', encoding='utf-8').write(src)
print('OK')
