    case 'sales_rep': {   // v1.2.221: laporan-sales — GET from, to (Y-m-d), sales (id | _none), div. Sales: sesuai hak lihat.
        $u = requireAuth(['super_admin', 'admin', 'supervisor']);
        crmGuard215();
        $fromD = (string)($_GET['from'] ?? wibDate('Y-m-01')); $toD = (string)($_GET['to'] ?? wibToday());
        $a = wibDayStart($fromD); $b = wibDayStart($toD);
        if ($a === null || $b === null || $b < $a) jsonOut(['ok' => false, 'error' => 'Rentang tanggal tidak valid (YYYY-MM-DD).'], 400);
        if ($b - $a > 370 * 86400) jsonOut(['ok' => false, 'error' => 'Rentang maksimal 1 tahun.'], 400);
        $only = null; $own = false;
        if (($u['role'] ?? '') === 'sales') {
            if (crmMySales216($u) === '') jsonOut(['ok' => false, 'error' => 'Akun Sales Anda belum terhubung ke data Sales.'], 400);
            $only = crmSalesVisible219($u); $own = is_array($only) && count($only) === 1;
        }
        $fs = preg_replace('/[^A-Za-z0-9_-]/', '', (string)($_GET['sales'] ?? ''));
        $fd = mb_substr(trim((string)($_GET['div'] ?? '')), 0, 40);
        $rep = crmRep221($fromD, $toD, $only, $fs, $fd);
        if ($rep === null) jsonOut(['ok' => false, 'error' => 'Rentang tanggal tidak valid.'], 400);
        if (($u['role'] ?? '') === 'sales') unset($rep['targets']);
        jsonOut(['ok' => true, 'own' => $own, 'can_target' => in_array(($u['role'] ?? ''), ['super_admin', 'admin'], true)] + $rep);
        break;
    }
    case 'sales_target_save': {   // v1.2.221: laporan-sales — POST {targets: {sid: {rev, deals, acts}}} per bulan
        $u = requireAuth(['super_admin', 'admin']);
        crmGuard215();
        $in = bodyInput();
        $map = slMap(); $out = [];
        foreach ((array)($in['targets'] ?? []) as $sid => $t) {
            $sid = (string)$sid; if (!isset($map[$sid]) || !is_array($t)) continue;
            $x = ['rev' => crmMoney216($t['rev'] ?? 0), 'deals' => max(0, min(100000, (int)($t['deals'] ?? 0))), 'acts' => max(0, min(100000, (int)($t['acts'] ?? 0)))];
            if ($x['rev'] || $x['deals'] || $x['acts']) $out[$sid] = $x;
        }
        writeJson(SALES_TARGET_FILE, $out);
        try { waAuditLog('sales_target_set', (string)$u['username'], '', ['n' => count($out)]); } catch (\Throwable $e) {}
        jsonOut(['ok' => true, 'targets' => srTargets221()]);
        break;
    }
