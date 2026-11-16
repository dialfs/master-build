    /* ======================================================================
     * v1.2.185: master-grup — dipanggil server pusat untuk Dashboard Grup
     * (satu login klien grup untuk beberapa tenant). Auth: X-Tenant-Id +
     * X-License-Key (deiCentralAuthOk), sama dengan stats_pull/update_remote.
     *  - grp_users  : daftar akun tenant (untuk memetakan user grup -> akun tenant)
     *  - grp_report : angka ringkas + tren harian untuk laporan gabungan
     * Tidak ada isi chat yang dikirim.
     * ==================================================================== */
    case 'grp_users': {
        if (!deiCentralAuthOk()) jsonOut(['ok' => false, 'error' => 'Kredensial pusat tidak cocok.'], 401);
        $out = [];
        foreach ((array)readJson(USERS_FILE, []) as $x) {
            if (!is_array($x) || !empty($x['internal'])) continue;
            $out[] = ['username' => (string)($x['username'] ?? ''), 'name' => (string)($x['name'] ?? ''), 'role' => (string)($x['role'] ?? '')];
        }
        jsonOut(['ok' => true, 'version' => DEI_VERSION, 'users' => $out]);
    }
    case 'grp_report': {
        if (!deiCentralAuthOk()) jsonOut(['ok' => false, 'error' => 'Kredensial pusat tidak cocok.'], 401);
        $fromD = substr((string)($_GET['from'] ?? ''), 0, 10);
        $toD   = substr((string)($_GET['to'] ?? ''), 0, 10);
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $toD))   $toD   = wibToday();
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $fromD)) $fromD = wibDate('Y-m-01');
        $fromTs = wibDayStart($fromD); $toTs = wibDayStart($toD);
        if ($fromTs === null || $toTs === null || $toTs < $fromTs) jsonOut(['ok' => false, 'error' => 'Rentang tanggal tidak valid.'], 400);
        $days = (int)(($toTs - $fromTs) / 86400) + 1;
        if ($days > 93) jsonOut(['ok' => false, 'error' => 'Rentang maksimal 93 hari.'], 400);
        $toEnd = $toTs + 86399;

        // Percakapan (Kinerja Layanan)
        $s = getSettings();
        $chLabels = [];
        foreach (waChannels($s) as $x) $chLabels[(string)$x['id']] = (string)$x['label'];
        $cs = convStats(convStoreRange($fromTs, $toEnd), $fromTs, $toEnd, $chLabels);
        $names = [];
        foreach ((array)readJson(USERS_FILE, []) as $us) if (is_array($us)) $names[$us['username'] ?? ''] = $us['name'] ?? ($us['username'] ?? '');
        $agents = [];
        foreach ($cs['agents'] as $r) {
            $agents[] = ['agent' => $r['agent'], 'name' => $names[$r['agent']] ?? $r['agent'], 'assigned' => $r['assigned'], 'resolved' => $r['resolved'],
                         'in_progress' => $r['in_progress'], 'frt' => $r['frt'], 'resolution' => $r['resolution']];
        }

        // Pesan bot (log chat): per hari, per channel, pelanggan unik
        $daily = [];
        for ($d = $fromTs; $d <= $toTs; $d += 86400) $daily[wibDate('Y-m-d', $d)] = ['date' => wibDate('Y-m-d', $d), 'chats' => 0, 'wa' => 0, 'web' => 0, 'conv' => 0, 'resolved' => 0, 'leads' => 0];
        $uniq = []; $msgs = ['total' => 0, 'wa' => 0, 'web' => 0, 'ai_errors' => 0];
        foreach ((array)logReadAll() as $l) {
            if (!is_array($l) || in_array(($l['dir'] ?? ''), ['manual', 'closing'], true)) continue;
            $d = substr((string)($l['ts'] ?? ''), 0, 10);
            if (!isset($daily[$d])) continue;
            $wa = ((string)($l['channel'] ?? '')) === 'whatsapp';
            $msgs['total']++; $msgs[$wa ? 'wa' : 'web']++;
            if (!empty($l['ai_error'])) $msgs['ai_errors']++;
            $daily[$d]['chats']++; $daily[$d][$wa ? 'wa' : 'web']++;
            $who = (string)($l['ip'] ?? '');   // WA: nomor pelanggan; web: IP pengunjung
            if ($who !== '' && empty($l['grp'])) $uniq[($wa ? 'w:' : 's:') . $who] = 1;
        }
        foreach ($cs['daily'] as $r) if (isset($daily[$r['date']])) { $daily[$r['date']]['conv'] = (int)$r['total']; $daily[$r['date']]['resolved'] = (int)$r['resolved']; }

        // Leads
        $ld = ['new' => 0, 'open' => 0, 'by_status' => []];
        foreach (leadsGetAll() as $L) {
            if (!is_array($L)) continue;
            $st = (string)($L['status'] ?? 'baru');
            if (in_array($st, ['baru', 'qualified', 'follow_up'], true)) $ld['open']++;
            $cd = substr((string)($L['created_at'] ?? ''), 0, 10);
            if ($cd === '' || !isset($daily[$cd])) continue;
            $ld['new']++; $daily[$cd]['leads']++;
            $ld['by_status'][$st] = ($ld['by_status'][$st] ?? 0) + 1;
        }

        jsonOut(['ok' => true, 'version' => DEI_VERSION, 'from' => $fromD, 'to' => $toD, 'days' => $days,
            'tracking_since' => convTrackingSince(),
            'conv' => ['totals' => $cs['totals'], 'avg' => $cs['avg'], 'med' => $cs['med'], 'handover_reasons' => $cs['handover_reasons']],
            'msgs' => $msgs + ['customers' => count($uniq)],
            'leads' => $ld,
            'daily' => array_values($daily),
            'agents' => $agents,
            'channels' => array_map(function ($c) { return ['ch' => $c['ch'], 'label' => $c['label'], 'total' => $c['total'], 'resolved' => $c['resolved'], 'unassigned' => $c['unassigned'], 'frt' => $c['frt']]; }, $cs['channels']),
        ]);
    }
