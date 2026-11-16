    /* ---------- v1.2.186: grup-inbox — inbox gabungan Dashboard Grup ---------- */
    case 'grp_inbox': {
        [, , $g, $u] = grpRequire();
        $tt = grpInboxTenants($g, $u);
        if (!$tt) jsonOut(['ok' => true, 'tenants' => [], 'conversations' => [], 'note' => ($u['role'] ?? '') === 'viewer' ? 'Akun Anda hanya untuk melihat laporan.' : 'Akun Anda belum dihubungkan ke akun tenant mana pun. Hubungi DEI.']);
        $jobs = [];
        foreach ($tt as $tid => [$t, $un]) $jobs[$tid] = [$t, 'grp_as', ['act' => 'wa_conversations_v2', 'filter' => 'all'], grpAsHdr($un, $u)];
        $conv = []; $st = [];
        foreach (grpFetchMulti($jobs, 25) as $tid => $r) {
            $t = $tt[$tid][0];
            if (empty($r['ok'])) { $st[] = ['tenant_id' => $tid, 'name' => (string)($t['name'] ?? $tid), 'ok' => false, 'error' => grpInboxVerNote($t, $r)]; continue; }
            $rows = (array)($r['conversations'] ?? []);
            usort($rows, function ($a, $b) { return strcmp((string)($b['last_ts'] ?? ''), (string)($a['last_ts'] ?? '')); });
            $rows = array_slice($rows, 0, 150);
            foreach ($rows as $c) if (is_array($c)) $conv[] = ['tenant_id' => $tid] + grpConvSlim($c);
            $st[] = ['tenant_id' => $tid, 'name' => (string)($t['name'] ?? $tid), 'ok' => true, 'role' => (string)($r['role'] ?? ''), 'total' => count((array)($r['conversations'] ?? [])),
                     'unreplied' => (int)($r['counts']['unreplied'] ?? 0)];
        }
        usort($conv, function ($a, $b) { return strcmp($b['last_ts'], $a['last_ts']); });
        jsonOut(['ok' => true, 'tenants' => $st, 'conversations' => $conv]);
    }
    case 'grp_thread': {
        [, , $g, $u] = grpRequire();
        $tid = tidNorm((string)($_GET['tenant_id'] ?? '')); $tt = grpInboxTenants($g, $u);
        if (!isset($tt[$tid])) jsonOut(['ok' => false, 'error' => 'Inbox tenant ini tidak termasuk akses Anda.'], 403);
        [$t, $un] = $tt[$tid];
        $r = grpAsCall($t, $un, $u, 'wa_thread', ['number' => (string)($_GET['number'] ?? ''), 'limit' => max(60, min(1000, (int)($_GET['limit'] ?? 60)))]);
        if (empty($r['ok'])) jsonOut(['ok' => false, 'error' => grpInboxVerNote($t, $r)], (int)($r['_http'] ?? 0) === 403 ? 403 : 400);
        $keep = ['ok', 'number', 'mode', 'group', 'conv', 'window_open', 'messages', 'total', 'ch', 'wa_prov', 'reply_ok', 'stage', 'vip', 'claim'];
        jsonOut(array_intersect_key($r, array_flip($keep)) + ['tenant_id' => $tid, 'as' => $un]);
    }
    case 'grp_send': case 'grp_resolve': {
        [, , $g, $u] = grpRequire();
        $in = bodyInput(); $tid = tidNorm((string)($in['tenant_id'] ?? '')); $tt = grpInboxTenants($g, $u);
        if (!isset($tt[$tid])) jsonOut(['ok' => false, 'error' => 'Inbox tenant ini tidak termasuk akses Anda.'], 403);
        [$t, $un] = $tt[$tid];
        $body = ['number' => (string)($in['number'] ?? '')];
        if ($action === 'grp_send') { $body['text'] = (string)($in['text'] ?? ''); if (!empty($in['reply_to'])) $body['reply_to'] = (string)$in['reply_to']; }
        $r = grpAsCall($t, $un, $u, $action === 'grp_send' ? 'wa_send_manual' : 'wa_resolve', [], $body, 40);
        $code = (int)($r['_http'] ?? 200); unset($r['_http']);
        if (empty($r['ok'])) jsonOut(['ok' => false, 'error' => grpInboxVerNote($t, $r + ['_http' => $code])], $code >= 400 && $code < 600 ? $code : 400);
        jsonOut($r);
    }
    case 'grp_send_media': {
        [, , $g, $u] = grpRequire();
        $tid = tidNorm((string)($_POST['tenant_id'] ?? '')); $tt = grpInboxTenants($g, $u);
        if (!isset($tt[$tid])) jsonOut(['ok' => false, 'error' => 'Inbox tenant ini tidak termasuk akses Anda.'], 403);
        $f = $_FILES['file'] ?? null;
        if (!is_array($f) || (int)($f['error'] ?? 4) !== UPLOAD_ERR_OK) jsonOut(['ok' => false, 'error' => 'Unggah file gagal' . (is_array($f) ? ' (kode ' . (int)$f['error'] . ')' : '') . '. Batas server ' . ini_get('upload_max_filesize') . '.'], 400);
        [$t, $un] = $tt[$tid];
        $mp = ['number' => (string)($_POST['number'] ?? ''), 'caption' => (string)($_POST['caption'] ?? ''),
               'file' => new CURLFile((string)$f['tmp_name'], (string)($f['type'] ?? 'application/octet-stream'), basename((string)($f['name'] ?? 'file')))];
        $r = grpAsCall($t, $un, $u, 'wa_send_media', [], ['__multipart' => $mp], 120);
        $code = (int)($r['_http'] ?? 200); unset($r['_http']);
        if (empty($r['ok'])) jsonOut(['ok' => false, 'error' => grpInboxVerNote($t, $r + ['_http' => $code])], $code >= 400 && $code < 600 ? $code : 400);
        jsonOut($r);
    }
    case 'grp_media': {
        [, , $g, $u] = grpRequire(true);
        $tid = tidNorm((string)($_GET['tenant_id'] ?? '')); $tt = grpInboxTenants($g, $u);
        $fq = (string)($_GET['f'] ?? '');
        if (!isset($tt[$tid]) || !preg_match('#^\d{6,20}/[a-f0-9]{20}\.[a-z0-9]{1,5}$#', $fq)) { http_response_code(404); header('Content-Type: text/plain'); echo 'not found'; exit; }
        [$t, $un] = $tt[$tid];
        [$code, $ct, $body] = grpAsCall($t, $un, $u, 'wa_media', ['f' => $fq] + (!empty($_GET['dl']) ? ['dl' => 1] : []), null, 60, true);
        http_response_code($code);
        $safe = $code === 200 && preg_match('#^(image/(jpeg|png|gif|webp)|video/|audio/)#i', $ct);   // jangan sajikan HTML/SVG tenant di origin pusat
        if ($code === 200 && !$safe) { $ct = 'application/octet-stream'; $_GET['dl'] = 1; }
        header('Content-Type: ' . ($code === 200 ? $ct : 'text/plain'));
        header("Content-Security-Policy: default-src 'none'; sandbox");
        header('Cache-Control: private, max-age=3600');
        header('X-Content-Type-Options: nosniff');
        if (!empty($_GET['dl'])) header('Content-Disposition: attachment; filename="' . basename($fq) . '"');
        echo $body; exit;
    }

