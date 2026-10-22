    /* ---------- v1.2.104: skor-risiko-wa — panel Kesehatan nomor (WAHA) ---------- */
    case 'wa_health': {
        $u  = requireAuth(['super_admin', 'admin', 'supervisor']);
        $in = bodyInput();
        $op = (string)($in['op'] ?? ($_GET['op'] ?? 'get'));
        $s  = getSettings();
        $wa = waConf($s);
        if (!whOn($wa)) jsonOut(['ok' => false, 'error' => 'Pemantauan kesehatan nomor khusus penyedia WAHA.'], 400);
        if ($op === 'summary') { $r = whScoreAll($s, false); jsonOut(['ok' => true, 'nums' => is_array($r) ? ($r['nums'] ?? []) : []]); }
        $ch = preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? ($_GET['ch'] ?? 'utama')));
        $conf = null; $label = '';
        foreach (whChannels($s) as $c) { if ($c[0] === $ch) { $conf = $c[2]; $label = $c[1]; } }
        if ($conf === null) jsonOut(['ok' => false, 'error' => 'Nomor tidak ditemukan atau terkunci.'], 404);
        $canEdit = in_array(($u['role'] ?? ''), ['super_admin', 'admin'], true);
        if ($op === 'apply_cfg') {
            if (!$canEdit) jsonOut(['ok' => false, 'error' => 'Khusus Super Admin / Admin.'], 403);
            list($ok, $err) = whApplyCfg($conf);
            if ($ok) { try { waAuditLog('wa_health_cfg', $u['username'], '', ['ch' => $ch]); } catch (\Throwable $e) {} }
            jsonOut($ok ? ['ok' => true] : ['ok' => false, 'error' => $err]);
        }
        if ($op === 'set_since') {
            if (!$canEdit) jsonOut(['ok' => false, 'error' => 'Khusus Super Admin / Admin.'], 403);
            $dt = trim((string)($in['date'] ?? ''));
            $ts = 0;
            if ($dt !== '') {
                $ts = preg_match('/^\d{4}-\d{2}-\d{2}$/', $dt) ? (int)strtotime($dt . ' 00:00:00 +0700') : 0;
                if ($ts <= 0 || $ts > time()) jsonOut(['ok' => false, 'error' => 'Tanggal tidak valid.'], 400);
            }
            whUpdate($ch, function (&$d) use ($ts) {
                if ($ts > 0) { $d['paired_at'] = $ts; $d['paired_src'] = 'manual'; }
                else unset($d['paired_at'], $d['paired_src']);
            });
            whScoreAll($s, true);
            jsonOut(['ok' => true]);
        }
        whScoreAll($s, false);
        $sc = whScore($ch);
        whStoreRow($ch, $label, $conf, $sc);
        jsonOut(['ok' => true, 'label' => $label, 'can_edit' => $canEdit, 'health' => $sc]);
        break;
    }

