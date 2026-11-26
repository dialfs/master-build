    case 'ntf_get': {   // v1.2.222: notif-wa — pengaturan notifikasi tim via WhatsApp
        requireAuth(['super_admin', 'admin']);
        jsonOut(['ok' => true] + ntfPublic222(true));
        break;
    }
    case 'ntf_save': {   // v1.2.222: notif-wa — POST {on, ch, kinds:{id:mode}, users:{username: wa}}
        $u = requireAuth(['super_admin', 'admin']);
        $in = bodyInput();
        $cur = ntfConf222(); $d = readJson(NTF_FILE, []); if (!is_array($d)) $d = [];
        if (array_key_exists('on', $in)) $d['on'] = !empty($in['on']);
        if (array_key_exists('ch', $in)) {
            $ch = preg_replace('/[^A-Za-z0-9_-]/', '', (string)$in['ch']); $hit = null;
            foreach (ntfChannels222() as $c) if ($c['id'] === $ch) $hit = $c;
            if (!$hit) jsonOut(['ok' => false, 'error' => 'Nomor pengirim tidak ditemukan.'], 400);
            if (!$hit['ok'] && !empty($d['on'])) jsonOut(['ok' => false, 'error' => $hit['why']], 400);
            $d['ch'] = $ch;
        }
        if (!empty($d['on']) && !array_key_exists('ch', $in) && !array_key_exists('ch', $d)) $d['ch'] = 'utama';
        if (is_array($in['kinds'] ?? null)) {
            foreach (ntfKinds222() as $id => $x) if (isset($in['kinds'][$id]) && in_array((string)$in['kinds'][$id], $x[1], true)) $d['kinds'][$id] = (string)$in['kinds'][$id];
        }
        if (!empty($d['on'])) {
            $okCh = false; foreach (ntfChannels222() as $c) if ($c['id'] === (string)($d['ch'] ?? 'utama') && $c['ok']) $okCh = true;
            if (!$okCh) jsonOut(['ok' => false, 'error' => 'Pilih nomor pengirim yang sudah terhubung (WAHA) sebelum mengaktifkan notifikasi WhatsApp.'], 400);
        }
        if (is_array($in['users'] ?? null)) {
            $users = readJson(USERS_FILE, []); $bad = []; $chg = 0;
            foreach ($users as $i => $x) {
                $un = (string)($x['username'] ?? ''); if ($un === '' || !empty($x['internal']) || !array_key_exists($un, $in['users'])) continue;
                if (($u['role'] ?? '') === 'admin' && ($x['role'] ?? '') === 'super_admin' && $un !== $u['username']) continue;   // Admin tidak mengubah Super Admin
                $raw = trim((string)$in['users'][$un]); $n = ntfNum222($raw);
                if ($raw !== '' && $n === '') { $bad[] = (string)($x['name'] ?? $un); continue; }
                if ($n === '') { if (isset($users[$i]['wa'])) { unset($users[$i]['wa']); $chg++; } }
                elseif (($users[$i]['wa'] ?? '') !== $n) { $users[$i]['wa'] = $n; $chg++; }
            }
            if ($bad) jsonOut(['ok' => false, 'error' => 'Nomor WhatsApp tidak valid untuk: ' . implode(', ', $bad) . '. Contoh: 0812xxxxxxx'], 400);
            if ($chg) writeJson(USERS_FILE, $users);
        }
        $d['updated_at'] = date('Y-m-d H:i:s'); $d['updated_by'] = (string)$u['username'];
        writeJson(NTF_FILE, $d);
        ntfConf222(true); ntfActive222(true);
        try { waAuditLog('ntf_wa_set', (string)$u['username'], '', ['on' => !empty($d['on']), 'ch' => (string)($d['ch'] ?? '')]); } catch (\Throwable $e) {}
        jsonOut(['ok' => true] + ntfPublic222(true));
        break;
    }
    case 'ntf_me': {   // v1.2.222: notif-wa — nomor WA notifikasi akun sendiri
        $u = requireAuth(['super_admin', 'admin', 'supervisor', 'wa_agent']);
        $me = null; foreach ((array)readJson(USERS_FILE, []) as $x) if (is_array($x) && ($x['username'] ?? '') === $u['username']) $me = $x;
        $cf = ntfConf222(); $lab = '';
        foreach (ntfChannels222() as $c) if ($c['id'] === $cf['ch']) $lab = $c['label'] . ($c['number'] !== '' && strpos($c['label'], $c['number']) === false ? ' (+' . $c['number'] . ')' : '');
        $act = [];
        foreach (ntfKinds222() as $id => $x) if (ntfWantWa222($id)) $act[] = $x[0];
        jsonOut(['ok' => true, 'wa' => ntfUserWa222($me), 'active' => ntfActive222(), 'sender' => $lab, 'kinds' => $act]);
        break;
    }
    case 'update_own_wa': {   // v1.2.222: notif-wa — POST {wa}
        $u = requireAuth(['super_admin', 'admin', 'supervisor', 'wa_agent']);
        $in = bodyInput(); $raw = trim((string)($in['wa'] ?? '')); $n = ntfNum222($raw);
        if ($raw !== '' && $n === '') jsonOut(['ok' => false, 'error' => 'Nomor WhatsApp tidak valid. Contoh: 0812xxxxxxx'], 400);
        $users = readJson(USERS_FILE, []);
        foreach ($users as $i => $x) {
            if (($x['username'] ?? '') !== $u['username']) continue;
            if ($n === '') unset($users[$i]['wa']); else $users[$i]['wa'] = $n;
            writeJson(USERS_FILE, $users);
            jsonOut(['ok' => true, 'wa' => $n]);
        }
        jsonOut(['ok' => false, 'error' => 'User tidak ditemukan.'], 404);
        break;
    }
    case 'ntf_test': {   // v1.2.222: notif-wa — kirim pesan uji ke nomor WA akun sendiri (atau username lain oleh admin)
        $u = requireAuth(['super_admin', 'admin', 'supervisor', 'wa_agent']);
        $in = bodyInput(); $target = (string)$u['username'];
        if (!empty($in['username']) && in_array(($u['role'] ?? ''), ['super_admin', 'admin'], true)) $target = (string)$in['username'];
        $x = null; foreach ((array)readJson(USERS_FILE, []) as $y) if (is_array($y) && ($y['username'] ?? '') === $target) $x = $y;
        if (!$x) jsonOut(['ok' => false, 'error' => 'User tidak ditemukan.'], 404);
        $n = ntfUserWa222($x);
        if ($n === '') jsonOut(['ok' => false, 'error' => 'Nomor WhatsApp untuk notifikasi belum diisi.'], 400);
        [$w, $err] = ntfSender222();
        if (!$w) jsonOut(['ok' => false, 'error' => $err], 400);
        $kind = (string)($in['kind'] ?? 'test'); $nm = trim((string)($x['name'] ?? '')) ?: $target;
        if ($kind === 'crm_remind' && crmOk215()) {
            $today = wibDate('Y-m-d'); $it = crmDueItems215(wibDate('Y-m-d', time() + 86400), $target)[$target] ?? [];
            [$txt, ] = ntfRemindText222($x, $it, $today, true);
        } elseif ($kind === 'crm_weekly' && crmOk215()) {
            $sid = ($x['role'] ?? '') === 'sales' ? crmSalesVisible219($x) : null;
            $rep = crmPerf217(wibDate('Y-m-d', time() - 7 * 86400), wibDate('Y-m-d', time() - 86400), $sid);
            $txt = ntfWeeklyText222($nm, $rep, $sid !== null && count((array)$sid) === 1, true);
        } else {
            $kind = 'test';
            $txt = ntfHead222('Uji notifikasi') . "\n\nHalo " . $nm . ', nomor ini akan menerima notifikasi tim dari dashboard ' . deiBrandProduct() . ' (pengingat, laporan, task, dan lead sesuai pengaturan). Balasan ke nomor ini tidak dijawab bot.';
        }
        $r = ntfWaSend222($n, $txt, $kind, $nm, true);
        if (empty($r['ok'])) jsonOut(['ok' => false, 'error' => (string)($r['error'] ?? 'Gagal kirim.')], 502);
        jsonOut(['ok' => true, 'to' => $n]);
        break;
    }
