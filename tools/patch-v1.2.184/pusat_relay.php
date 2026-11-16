    /* v1.2.184: lupa-password — tenant meminta pusat mengirim email transaksional (reset password).
     * Pengirim selalu noreply@deintegra.com. Hanya jenis pw_reset / pw_changed.
     * Batas: 20 email/jam per tenant, 5 email/jam per alamat. Log: data/mail-log.json (500 terakhir). */
    case 'mail_relay': {
        $body = bodyInput();
        $tenantId = trim((string)($body['tenant_id'] ?? '')); $licenseKey = trim((string)($body['license_key'] ?? ''));
        if ($tenantId === '' || $licenseKey === '') jsonOut(['ok' => false, 'error' => 'tenant_id & license_key wajib.'], 400);
        $tenant = null;
        foreach (readJson(TENANTS_FILE, []) as $t) { if (tidEq($t['tenant_id'] ?? '', $tenantId)) { $tenant = $t; break; } }
        if (!$tenant) jsonOut(['ok' => false, 'error' => 'Tenant tidak terdaftar di server pusat.'], 404);
        if (!hash_equals((string)($tenant['license_key'] ?? ''), $licenseKey)) jsonOut(['ok' => false, 'error' => 'License key tidak cocok.'], 403);
        $tid = strtolower((string)$tenant['tenant_id']);
        $kind = (string)($body['kind'] ?? '');
        if (!in_array($kind, ['pw_reset', 'pw_changed'], true)) jsonOut(['ok' => false, 'error' => 'Jenis email tidak diizinkan.'], 400);
        $to = strtolower(trim((string)($body['to'] ?? '')));
        if ($to === '' || strlen($to) > 190 || preg_match('/[\r\n,;\s]/', $to) || !filter_var($to, FILTER_VALIDATE_EMAIL)) jsonOut(['ok' => false, 'error' => 'Alamat email tidak valid.'], 400);
        $subject = mb_substr(trim(preg_replace('/[\r\n]+/', ' ', (string)($body['subject'] ?? ''))), 0, 150);
        $text = mb_substr((string)($body['text'] ?? ''), 0, 20000);
        $html = mb_substr((string)($body['html'] ?? ''), 0, 60000);
        if ($subject === '' || trim($text) === '') jsonOut(['ok' => false, 'error' => 'Subjek & isi wajib.'], 400);
        $fromName = mb_substr(trim(preg_replace('/[\r\n"<>\\\\]+/', ' ', (string)($body['from_name'] ?? ''))), 0, 40);
        if ($fromName === '') $fromName = 'DEI Chatbot';
        $now = time(); $rf = DATA_DIR . '/mail-relay.json';
        $fp = @fopen($rf, 'c+'); $rows = [];
        if ($fp) { flock($fp, LOCK_EX); $rows = json_decode((string)stream_get_contents($fp), true); if (!is_array($rows)) $rows = []; }
        $rows = array_values(array_filter($rows, function ($r) use ($now) { return (int)($r['t'] ?? 0) > $now - 3600; }));
        $nT = 0; $nTo = 0;
        foreach ($rows as $r) { if (($r['tid'] ?? '') === $tid) $nT++; if (($r['to'] ?? '') === md5($to)) $nTo++; }
        $lim = $nT >= 20 ? 'tenant' : ($nTo >= 5 ? 'to' : '');
        if ($lim === '') $rows[] = ['t' => $now, 'tid' => $tid, 'to' => md5($to)];
        if ($fp) { ftruncate($fp, 0); rewind($fp); fwrite($fp, json_encode($rows)); fflush($fp); flock($fp, LOCK_UN); fclose($fp); }
        if ($lim !== '') jsonOut(['ok' => false, 'error' => 'Batas pengiriman email tercapai, coba lagi nanti.', 'limit' => $lim], 429);
        $from = 'noreply@deintegra.com';
        $b = 'dei-' . bin2hex(random_bytes(8));
        $hdr = 'From: =?UTF-8?B?' . base64_encode($fromName) . '?= <' . $from . ">\r\n"
             . "MIME-Version: 1.0\r\n"
             . 'Message-ID: <' . bin2hex(random_bytes(12)) . "@deintegra.com>\r\n"
             . "Auto-Submitted: auto-generated\r\n"
             . 'X-DEI-Tenant: ' . preg_replace('/[^a-z0-9._-]/', '', $tid) . "\r\n"
             . 'Content-Type: multipart/alternative; boundary="' . $b . '"';
        $mb = "--$b\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($text))
            . ($html !== '' ? "--$b\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($html)) : '')
            . "--$b--\r\n";
        $subj = '=?UTF-8?B?' . base64_encode($subject) . '?=';
        $ok = false; $via = '';
        if (function_exists('mail')) {
            $ok = @mail($to, $subj, $mb, $hdr, '-f' . $from); $via = '-f';
            if (!$ok) { $ok = @mail($to, $subj, $mb, $hdr); $via = 'plain'; }
        }
        $lf = DATA_DIR . '/mail-log.json'; $log = readJson($lf, []); if (!is_array($log)) $log = [];
        $at = strpos($to, '@'); $mask = substr($to, 0, min(2, $at)) . str_repeat('*', max(1, $at - 2)) . substr($to, $at);
        array_unshift($log, ['ts' => gmdate('Y-m-d H:i:s', $now + 7 * 3600), 'tid' => $tid, 'kind' => $kind, 'to' => $mask, 'ok' => $ok, 'via' => $via]);
        writeJson($lf, array_slice($log, 0, 500));
        if (!$ok) suTelegram("Gagal kirim email {$kind} tenant {$tid} ke {$mask} (mail() false).");
        jsonOut(['ok' => true, 'sent' => (bool)$ok]);
    }

