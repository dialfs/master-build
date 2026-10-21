
    /* ---------- v1.2.101: percakapan — tandai selesai (tombol "Selesai" di thread) ---------- */
    case 'wa_resolve': {
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        deiGuardSpvScope($u, $num);
        $cl = waClaimGet($num);
        $owner = $cl ? (string)($cl['agent_username'] ?? '') : '';
        $isAdmin = in_array($u['role'], ['super_admin', 'admin', 'supervisor'], true);
        if (!$isAdmin && $owner !== '' && $owner !== $u['username']) {
            jsonOut(['ok' => false, 'error' => 'Chat ini dipegang ' . $owner . '. Hanya pemegang chat atau admin yang bisa menandai selesai.'], 403);
        }
        $ok = convTrack($num, 'resolve', ['agent' => $u['username']]);
        $c = convStoreGet($num);
        if (!$ok && !convIsFinal($c)) jsonOut(['ok' => false, 'error' => 'Tidak ada percakapan aktif untuk nomor ini.'], 409);
        // selesai = chat dilepas: Mode AI kembali ke bot, Mode Manual kembali ke antrean untuk pesan berikutnya
        if ($cl) {
            waClaimSet($num, null);
            agentEvent('release', $owner, $num, ['by' => $u['username'], 'resolve' => 1]);
        } else {
            waSetMode($num, 'bot');
        }
        try { convStateMutate(function (&$a) use ($num, $u) {
            $st = is_array($a[$num] ?? null) ? $a[$num] : ['last_at' => time()];
            $st['res_at'] = time(); $st['res_by'] = $u['username']; $st['guest_waiting_since'] = 0;
            $st['esc_level'] = 0; $st['esc_inc'] = '';
            $a[$num] = $st;
        }, $num); } catch (\Throwable $e) { error_log('wa_resolve conv-state: ' . $e->getMessage()); }
        waAuditLog('resolve', $u['username'], $num, ['from_agent' => $owner]);
        jsonOut(['ok' => true, 'number' => $num, 'conv' => convPublic($c)]);
        break;
    }

    /* ---------- v1.2.101: laporan kinerja layanan (dari record percakapan) ---------- */
    case 'conv_report':
    case 'conv_list':
    case 'conv_export': {
        $u = requireAuth(['super_admin', 'admin', 'supervisor']);
        $todayWib = wibToday();
        $fromD = (string)($_GET['from'] ?? wibDate('Y-m-01'));
        $toD   = (string)($_GET['to'] ?? $todayWib);
        $fromTs = wibDayStart($fromD); $toTs = wibDayStart($toD);
        if ($fromTs === null || $toTs === null || $toTs < $fromTs) jsonOut(['ok' => false, 'error' => 'Rentang tanggal tidak valid (YYYY-MM-DD).'], 400);
        $days = (int)(($toTs - $fromTs) / 86400) + 1;
        if ($days > 93) jsonOut(['ok' => false, 'error' => 'Rentang maksimal 93 hari (3 bulan).'], 400);
        $toTs += 86399;
        $ch = (string)($_GET['ch'] ?? '');
        $s = getSettings();
        $chLabels = [];
        foreach (waChannels($s) as $x) $chLabels[(string)$x['id']] = (string)$x['label'];
        $filt = function ($recs) use ($ch) {
            if ($ch === '') return $recs;
            return array_values(array_filter($recs, function ($c) use ($ch) { return ((string)($c['ch'] ?? '') ?: 'utama') === $ch; }));
        };
        $recs = $filt(convStoreRange($fromTs, $toTs));

        if ($action === 'conv_report') {
            $cur = convStats($recs, $fromTs, $toTs, $chLabels);
            $pTo = $fromTs - 1; $pFrom = $fromTs - $days * 86400;
            $prevRecs = $filt(convStoreRange($pFrom, $pTo));
            $prev = convStats($prevRecs, $pFrom, $pTo, $chLabels);
            $users = readJson(USERS_FILE, []); $names = [];
            foreach ((array)$users as $us) $names[$us['username'] ?? ''] = $us['name'] ?? ($us['username'] ?? '');
            foreach ($cur['agents'] as &$r) $r['name'] = $names[$r['agent']] ?? $r['agent'];
            unset($r);
            jsonOut(['ok' => true, 'from' => $fromD, 'to' => $toD, 'days' => $days,
                'prev' => ['from' => wibDate('Y-m-d', $pFrom), 'to' => wibDate('Y-m-d', $pTo), 'totals' => $prev['totals'], 'avg' => $prev['avg'], 'has_data' => count($prevRecs) > 0],
                'channels_all' => count($chLabels) > 1 ? array_map(function ($k, $v) { return ['id' => $k, 'label' => $v]; }, array_keys($chLabels), $chLabels) : [],
                'tracking_since' => convTrackingSince(),
                'timeout_hours' => (int)(CONV_TIMEOUT_SEC / 3600), 'reopen_minutes' => (int)(CONV_REOPEN_SEC / 60),
            ] + $cur);
        }

        // daftar / CSV
        $kind = (string)($_GET['kind'] ?? '');
        $keep = function ($c) use ($kind) {
            $st = (string)($c['status'] ?? '');
            $hand = (int)($c['handover_at'] ?? 0); $bot = (int)($c['bot_msgs'] ?? 0) > 0;
            switch ($kind) {
                case 'unassigned':   return $st === 'handover';
                case 'in_progress':  return in_array($st, ['open', 'handover', 'assigned'], true);
                case 'assigned':     return (int)($c['assigned_at'] ?? 0) > 0;
                case 'resolved':     return $st === 'resolved';
                case 'bot_resolved': return $st === 'resolved' && $bot && !$hand && (int)($c['agent_msgs'] ?? 0) === 0;
                case 'to_agent':     return $bot && $hand;
                case 'expired':      return $st === 'expired';
                default:             return true;
            }
        };
        $agentF = (string)($_GET['agent'] ?? '');
        $rows = [];
        foreach (array_reverse($recs) as $c) {
            if (!$keep($c)) continue;
            if ($agentF !== '' && (string)($c['agent'] ?? '') !== $agentF) continue;
            $rows[] = $c;
        }
        if ($action === 'conv_export') {
            $names = convContactNames($rows);
            header('Content-Type: text/csv; charset=utf-8');
            header('Content-Disposition: attachment; filename="percakapan-' . $fromD . '_' . $toD . '.csv"');
            $out = fopen('php://output', 'w');
            fwrite($out, "\xEF\xBB\xBF");
            $tgl = function ($t) { return $t ? wibDate('Y-m-d H:i:s', (int)$t) : ''; };
            $dur = function ($a, $b) { return ($a && $b && $b >= $a) ? ($b - $a) : ''; };
            fputcsv($out, ['ID', 'Nomor', 'Nama', 'Nomor bisnis', 'Asal', 'Status', 'Dibuka', 'Balasan pertama', 'Serah ke agent', 'Alasan serah', 'Di-assign', 'Agent', 'Balasan agent pertama', 'Selesai', 'Diselesaikan oleh',
                           'Pesan pelanggan', 'Pesan bot', 'Pesan agent', 'FRT (dtk)', 'FRT agent (dtk)', 'Waktu antre (dtk)', 'Waktu selesai (dtk)', 'Dibuka ulang']);
            foreach ($rows as $c) {
                $rb = (string)($c['resolved_by'] ?? '');
                fputcsv($out, [$c['id'], '+' . $c['num'], $names[$c['num']] ?? '', $chLabels[(string)($c['ch'] ?? '') ?: 'utama'] ?? ($c['ch'] ?? ''), $c['origin'] ?? '', $c['status'],
                    $tgl($c['opened_at']), $tgl($c['first_reply_at']), $tgl($c['handover_at']), $c['handover_reason'] ?? '', $tgl($c['assigned_at']), $c['agent'] ?? '', $tgl($c['first_agent_at']),
                    $tgl($c['resolved_at']), $rb === 'agent' ? ('agent: ' . ($c['resolver'] ?? '')) : $rb,
                    (int)$c['guest_msgs'], (int)$c['bot_msgs'], (int)$c['agent_msgs'],
                    $dur($c['opened_at'], $c['first_reply_at']), $dur(max((int)$c['handover_at'], (int)$c['opened_at']), $c['first_agent_at']),
                    $dur($c['handover_at'], $c['assigned_at']), $dur($c['opened_at'], $c['resolved_at']), (int)($c['reopen_n'] ?? 0)]);
            }
            fclose($out);
            exit;
        }
        $per = max(10, min(200, (int)($_GET['per'] ?? 50)));
        $page = max(1, (int)($_GET['page'] ?? 1));
        $slice = array_slice($rows, ($page - 1) * $per, $per);
        $names = convContactNames($slice);
        $list = [];
        foreach ($slice as $c) { $p = convPublic($c); $p['name'] = $names[$c['num']] ?? ''; $p['ch_label'] = $chLabels[(string)($c['ch'] ?? '') ?: 'utama'] ?? ''; $list[] = $p; }
        jsonOut(['ok' => true, 'total' => count($rows), 'page' => $page, 'per' => $per, 'rows' => $list]);
        break;
    }
