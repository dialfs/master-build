    /* ---------- v1.2.138: filter-topik ---------- */
    case 'tp_get': {
        $u = requireAuth(['super_admin', 'admin', 'supervisor', 'wa_agent']);
        $isAdm = in_array($u['role'], ['super_admin', 'admin'], true);
        $plan = tpPlan();
        $out = ['ok' => true, 'conf' => $isAdm ? tpConf() : tpClientConf(), 'active' => tpActive(), 'plan' => $plan,
                'locked' => !$plan['ok'], 'locked_msg' => $plan['ok'] ? '' : tpLockedMsg(), 'quota' => tpQuota(), 'backfill' => tpBackfillState()];
        if ($isAdm) {
            $ps = [];
            foreach (tpPresets() as $k => $p) $ps[] = ['key' => $k] + $p;
            $out['presets'] = $ps;
            $lab = 0; foreach (waGetContacts() as $c) if (is_array($c['tp'] ?? null) && !empty($c['tp']['t'])) $lab++;
            $out['labeled'] = $lab;
        }
        jsonOut($out);
        break;
    }
    case 'tp_save': {
        $u = requireAuth(['super_admin', 'admin']);
        $in = bodyInput();
        $plan = tpPlan();
        if (!$plan['ok'] && !empty($in['enabled'])) jsonOut(['ok' => false, 'error' => tpLockedMsg()], 403);
        $prev = tpConf();
        $c = tpConfClean($in);
        if ($c['enabled'] && !$c['topics']) jsonOut(['ok' => false, 'error' => 'Isi minimal satu topik sebelum mengaktifkan.'], 400);
        $c['updated_at'] = wibDate('Y-m-d H:i:s'); $c['by'] = (string)$u['username'];
        writeJson(TP_CONF_FILE, $c);
        unset($GLOBALS['dei_tp_conf'], $GLOBALS['dei_tp_active']);
        $bf = tpBackfillState();
        $started = null;
        if ($c['enabled'] && !$prev['enabled'] && !$bf) $started = tpBackfillStart($u['username']);   // pertama kali diaktifkan -> backfill 7 hari
        jsonOut(['ok' => true, 'conf' => tpConf(), 'active' => tpActive(), 'backfill' => $started ?: tpBackfillState()]);
        break;
    }
    case 'tp_backfill': {
        $u = requireAuth(['super_admin', 'admin']);
        if (!tpActive()) jsonOut(['ok' => false, 'error' => tpPlan()['ok'] ? 'Aktifkan Filter Topik dulu.' : tpLockedMsg()], 400);
        $in = bodyInput();
        $days = (int)($in['days'] ?? 7); if (!in_array($days, [1, 3, 7, 14, 30], true)) $days = 7;
        jsonOut(['ok' => true, 'backfill' => tpBackfillStart($u['username'], $days, !empty($in['all'])), 'quota' => tpQuota()]);
        break;
    }
    case 'tp_label': {
        $u = requireAuth(['super_admin', 'admin', 'supervisor', 'wa_agent']);
        $in = bodyInput();
        $num = waNormNum($in['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'number wajib'], 400);
        deiGuardAgentPrivate($u, $num);
        if (!tpPlan()['ok']) jsonOut(['ok' => false, 'error' => tpLockedMsg()], 403);
        $op = (string)($in['op'] ?? 'set');
        if ($op === 'auto') {   // buka kunci & klasifikasi ulang oleh AI di tick berikutnya
            waContactUpdate($num, function (&$c) { if (!is_array($c['tp'] ?? null)) return false; $c['tp']['lk'] = 0; $c['tp']['by'] = 'ai'; });
            try { convStateMutate(function (&$a) use ($num) { $st = is_array($a[$num] ?? null) ? $a[$num] : ['last_at' => time()]; $st['tp_due'] = 1; $st['tp_err_at'] = 0; $a[$num] = $st; }, $num); }
            catch (\Throwable $e) { error_log('tp_label auto: ' . $e->getMessage()); }
        } else {
            $t = array_slice(array_values(array_unique(array_map('strval', (array)($in['t'] ?? [])))), 0, 6);
            tpStore($num, $t, (string)($in['m'] ?? ''), (string)$u['username'], true, 1);
        }
        try { waAuditLog('topic_label', $u['username'], $num, ['op' => $op, 'm' => (string)($in['m'] ?? '')]); } catch (\Throwable $e) {}
        jsonOut(['ok' => true, 'number' => $num, 'tp' => tpPublic(waContactGet($num) ?: [])]);
        break;
    }

