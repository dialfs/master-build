    /* ---------- v1.2.223: laporan-pdf ---------- */
    case 'rpt_get': {
        requireAuth(['super_admin', 'admin']);
        rpGuard223();
        jsonOut(['ok' => true] + rpPublicConf223(rpConf223()));
        break;
    }
    case 'rpt_save': {   // body: weekly{on,dow,hour,sections[]}, monthly{on,dom,hour,sections[]}, to_admins, to_spv, to_sales, extra_email, extra_wa, via, engine, chrome_bin
        $u = requireAuth(['super_admin', 'admin']);
        rpGuard223();
        $in = bodyInput(); $old = rpConf223();
        $list = function ($v) { return is_array($v) ? $v : preg_split('/[\s,;]+/', (string)$v, -1, PREG_SPLIT_NO_EMPTY); };
        $em = []; $bad = [];
        foreach ($list($in['extra_email'] ?? []) as $e) { $v = deiValidEmail($e); if ($v === '') $bad[] = $e; elseif (!in_array($v, $em, true)) $em[] = $v; }
        $wa = [];
        foreach ($list($in['extra_wa'] ?? []) as $n) { $v = ntfNum222($n); if ($v === '') $bad[] = $n; elseif (!in_array($v, $wa, true)) $wa[] = $v; }
        if ($bad) jsonOut(['ok' => false, 'error' => 'Tidak valid: ' . implode(', ', array_slice(array_map('strval', $bad), 0, 5))], 400);
        if (count($em) > 10 || count($wa) > 10) jsonOut(['ok' => false, 'error' => 'Maksimal 10 email dan 10 nomor WhatsApp tambahan.'], 400);
        $cb = trim((string)($in['chrome_bin'] ?? $old['chrome_bin']));
        if (($u['role'] ?? '') !== 'super_admin') $cb = $old['chrome_bin'];   // lokasi Chromium hanya diubah Super Admin
        elseif ($cb !== '' && !preg_match('#^/[A-Za-z0-9._/+-]{1,200}$#', $cb)) jsonOut(['ok' => false, 'error' => 'Lokasi Chromium tidak valid (contoh: /usr/bin/chromium).'], 400);
        $pk = function ($x, $kind) use ($old) {
            $x = is_array($x) ? $x : [];
            $o = ['on' => !empty($x['on']), 'hour' => (int)($x['hour'] ?? $old[$kind]['hour']), 'sections' => array_values(array_map('strval', (array)($x['sections'] ?? $old[$kind]['sections'])))];
            if ($kind === 'weekly') $o['dow'] = (int)($x['dow'] ?? $old['weekly']['dow']); else $o['dom'] = (int)($x['dom'] ?? $old['monthly']['dom']);
            return $o;
        };
        $c = ['weekly' => $pk($in['weekly'] ?? null, 'weekly'), 'monthly' => $pk($in['monthly'] ?? null, 'monthly'),
              'to_admins' => !empty($in['to_admins']), 'to_spv' => !empty($in['to_spv']), 'to_sales' => !empty($in['to_sales']),
              'extra_email' => $em, 'extra_wa' => $wa, 'via' => (string)($in['via'] ?? 'email'), 'engine' => (string)($in['engine'] ?? 'auto'), 'chrome_bin' => $cb,
              'updated_at' => wibDate('Y-m-d H:i:s'), 'updated_by' => (string)$u['username']];
        foreach (['weekly', 'monthly'] as $k) if ($c[$k]['on'] && !$c[$k]['sections']) jsonOut(['ok' => false, 'error' => 'Pilih minimal satu bagian laporan.'], 400);
        writeJson(RP_CONF_FILE, $c);
        // Baru dinyalakan / jadwal diubah setelah lewat jadwal periode ini -> mulai periode berikutnya (tidak langsung mengirim laporan yang sudah lewat)
        $st = readJson(RP_STATE_FILE, []); if (!is_array($st)) $st = []; $nc = rpConf223(); $chg = false;
        foreach (['weekly' => 'dow', 'monthly' => 'dom'] as $k => $dk) {
            $was = $old[$k]['on'] && $old[$k][$dk] === $nc[$k][$dk] && $old[$k]['hour'] === $nc[$k]['hour'];
            if (!$nc[$k]['on'] || $was || !rpDue223($k, $nc)) continue;
            [$key, $f, $t] = rpPeriod223($k, $nc);
            if (($st[$k]['key'] ?? '') === $key && !empty($st[$k]['done'])) continue;
            $st[$k] = ['key' => $key, 'from' => $f, 'to' => $t, 'files' => [], 'sent' => [], 'log' => [], 'done' => true, 'skipped' => 1, 'done_at' => ''];
            $chg = true;
        }
        if ($chg) writeJson(RP_STATE_FILE, $st);
        jsonOut(['ok' => true] + rpPublicConf223(rpConf223()));
        break;
    }
    case 'rpt_make': {   // body: kind weekly|monthly|custom, from, to (custom), sections[] (opsional). Hasil: id arsip -> unduh lewat rpt_file
        $u = requireAuth(['super_admin', 'admin', 'supervisor']);
        rpGuard223();
        $in = bodyInput(); $cf = rpConf223(); $kind = (string)($in['kind'] ?? 'weekly');
        if ($kind === 'custom') {
            $from = substr((string)($in['from'] ?? ''), 0, 10); $to = substr((string)($in['to'] ?? ''), 0, 10);
            $a = wibDayStart($from); $b = wibDayStart($to);
            if ($a === null || $b === null || $b < $a) jsonOut(['ok' => false, 'error' => 'Rentang tanggal tidak valid.'], 400);
            if ($b - $a > 92 * 86400) jsonOut(['ok' => false, 'error' => 'Rentang maksimal 93 hari.'], 400);
            $sections = $cf['monthly']['sections'];
        } else {
            if (!in_array($kind, ['weekly', 'monthly'], true)) $kind = 'weekly';
            [, $from, $to] = rpPeriod223($kind, $cf); $sections = $cf[$kind]['sections'];
        }
        if (is_array($in['sections'] ?? null) && $in['sections']) $sections = array_values(array_intersect(array_keys(rpSections223()), array_map('strval', $in['sections'])));
        if (!$sections) jsonOut(['ok' => false, 'error' => 'Pilih minimal satu bagian laporan.'], 400);
        @set_time_limit(120);
        $r = rpBuild223($kind, $from, $to, $sections, ['scope' => null, 'user' => null, 'for' => ''], ['by' => (string)$u['username']], $cf);
        if (!$r['ok']) jsonOut(['ok' => false, 'error' => $r['error']], 500);
        jsonOut(['ok' => true, 'id' => $r['id'], 'name' => $r['name'], 'size' => strlen($r['pdf']), 'engine' => $r['engine'], 'warn' => $r['warn']]);
        break;
    }
    case 'rpt_file': {   // GET id — unduh PDF arsip (login)
        requireAuth(['super_admin', 'admin', 'supervisor']);
        rpGuard223();
        rpStream223((string)($_GET['id'] ?? ''), !empty($_GET['inline']));
        break;
    }
    case 'rpt_dl': {   // publik bertanda tangan: f, e, s (tautan di email/WA, berlaku RP_LINK_DAYS hari)
        $id = (string)($_GET['f'] ?? ''); $exp = (int)($_GET['e'] ?? 0); $sig = (string)($_GET['s'] ?? '');
        if (!preg_match('/^\d{8}-[0-9a-f]{12}$/', $id) || $exp < time() || !hash_equals(rpSig223($id, $exp), $sig)) {
            http_response_code(403); header('Content-Type: text/html; charset=utf-8');
            echo '<!DOCTYPE html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><body style="font-family:Arial,sans-serif;padding:40px;color:#15152b"><h3>Tautan laporan tidak berlaku</h3><p>Tautan sudah kedaluwarsa atau tidak valid. Buka dashboard &gt; Laporan &amp; Log &gt; Laporan Berkala untuk mengunduh ulang.</p></body>';
            exit;
        }
        rpStream223($id, true);
        break;
    }
    case 'rpt_test': {   // body: kind weekly|monthly — kirim laporan periode terakhir ke saya (email &/atau WA sesuai pengaturan)
        $u = requireAuth(['super_admin', 'admin']);
        rpGuard223();
        $in = bodyInput(); $kind = (string)($in['kind'] ?? 'weekly'); if (!in_array($kind, ['weekly', 'monthly'], true)) $kind = 'weekly';
        $cf = rpConf223(); [, $from, $to] = rpPeriod223($kind, $cf);
        $Rs = rpRecipients223(['to_admins' => true, 'to_spv' => true, 'to_sales' => true] + $cf, (string)$u['username']);
        if (!$Rs) jsonOut(['ok' => false, 'error' => 'Akun Anda tidak ditemukan.'], 400);
        $R = $Rs[0]; [$waOk, $waWhy] = rpWaReady223(); $ch = rpChannels223($cf, $R, $waOk);
        if (!$ch['email'] && !$ch['wa']) jsonOut(['ok' => false, 'error' => 'Isi email atau nomor WhatsApp Anda dulu di Profil Saya.' . (!$waOk && $R[3] !== '' ? ' (' . $waWhy . ')' : '')], 400);
        @set_time_limit(120);
        $b = rpBuild223($kind, $from, $to, $cf[$kind]['sections'], ['scope' => $R[4], 'user' => $R[5], 'for' => $R[4] === null ? '' : $R[1]], ['by' => (string)$u['username'], 'test' => 1], $cf);
        if (!$b['ok']) jsonOut(['ok' => false, 'error' => $b['error']], 500);
        $link = rpLink223($b['id']); $out = ['ok' => true, 'id' => $b['id'], 'engine' => $b['engine'], 'warn' => $b['warn'], 'size' => strlen($b['pdf'])];
        if ($ch['email']) { $r = rpSendMail223($R, $b['D'], $b['pdf'], $b['name'], $link, true); $out['email'] = ['ok' => !empty($r['ok']), 'to' => deiMaskEmail($R[2]), 'attached' => !empty($r['attached']), 'error' => (string)($r['error'] ?? '')]; }
        if ($ch['wa']) { $r = rpSendWa223($R, $b['D'], $b['pdf'], $b['name'], $link); $out['wa'] = ['ok' => !empty($r['ok']), 'to' => $R[3], 'via' => (string)($r['via'] ?? ''), 'error' => (string)($r['error'] ?? '')]; }
        if (empty($out['email']['ok']) && empty($out['wa']['ok'])) { $out['ok'] = false; $out['error'] = trim(($out['email']['error'] ?? '') . ' ' . ($out['wa']['error'] ?? '')) ?: 'Pengiriman gagal.'; }
        jsonOut($out);
        break;
    }
    case 'rpt_lib': {   // pasang mesin PDF (dompdf) sekarang
        requireAuth(['super_admin', 'admin']);
        rpGuard223();
        @set_time_limit(120);
        [$ok, $m] = rpLibInstall223();
        jsonOut(['ok' => $ok, 'message' => $m, 'error' => $ok ? '' : $m] + rpPublicConf223(rpConf223()), $ok ? 200 : 500);
        break;
    }
