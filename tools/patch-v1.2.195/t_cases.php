    /* ---------- v1.2.195: web-balas — PUBLIC: pengunjung minta bicara dengan tim ---------- */
    case 'web_human': {
        if ($_SERVER['REQUEST_METHOD'] !== 'POST') jsonOut(['ok' => false, 'error' => 'Method not allowed'], 405);
        $s = getSettings();
        if (!deiWebHumanConf($s)['enabled']) jsonOut(['ok' => false, 'error' => 'Fitur ini tidak aktif.'], 403);
        if (!checkRateLimit('webhuman:' . clientIp(), 20)) jsonOut(['ok' => false, 'error' => 'Terlalu banyak permintaan.'], 429);
        $in = bodyInput();
        $convId = trim((string)($in['conversation_id'] ?? '')); $visitorId = trim((string)($in['visitor_id'] ?? ''));
        $convs = webConvReadAll();
        $idx = webConvFind($convs, $convId);
        if ($convId === '' || $idx < 0 || ($convs[$idx]['visitor_id'] ?? '') !== $visitorId) jsonOut(['ok' => false, 'error' => 'Conversation not found'], 404);
        $msgs = webConvLoadMessages($convId);
        if (deiWebHold($convs[$idx]) === '') {
            $sup = deiSupportSelf();
            $text = $sup ? 'Baik, percakapan ini kami teruskan ke tim DEI. Mohon tunggu, balasan akan muncul di sini. Anda tetap bisa menulis pesan.'
                         : 'Baik, percakapan ini kami teruskan ke tim kami. Mohon tunggu, balasan akan muncul di sini. Anda tetap bisa menulis pesan.';
            $msgs[] = ['role' => 'assistant', 'content' => $text, 'ts' => date('Y-m-d H:i:s'), 'sys' => 'human_req'];
            webConvSaveMessages($convId, $msgs);
            if ($sup) {   // tenant Support: judul percakapan = siapa yang bertanya, walau belum ada pesan
                $hc = deiSupportCtxClean($in['context'] ?? null);
                if ($hc && (!empty($hc['business']) || !empty($hc['tenant_id']))) {
                    $convs[$idx]['title'] = mb_substr(trim(($hc['business'] ?? '') . (!empty($hc['tenant_id']) ? ' (' . $hc['tenant_id'] . ')' : '') . (!empty($hc['user']) ? ' · ' . $hc['user'] : '')), 0, 80);
                    $convs[$idx]['ctx'] = $hc;
                }
            }
            $convs[$idx]['human_req'] = time();
            $convs[$idx]['last_ts'] = date('Y-m-d H:i:s');
            $convs[$idx]['message_count'] = count($msgs);
            webConvWrite($convs);
            $lastQ = '';
            for ($i = count($msgs) - 1; $i >= 0; $i--) { if (($msgs[$i]['role'] ?? '') === 'user') { $lastQ = (string)$msgs[$i]['content']; break; } }
            deiWebNotify($convs[$idx], 'Pengunjung web minta bicara dengan tim', ($convs[$idx]['title'] ?? 'Pengunjung') . ($lastQ !== '' ? ': ' . $lastQ : ''));
        }
        jsonOut(['ok' => true, 'status' => deiWebPub($convs[$idx]), 'total' => count($msgs),
                 'messages' => array_map('deiWebMsgOut', array_slice($msgs, -1))]);
        break;
    }

    /* ---------- v1.2.195: web-balas — PUBLIC: pengunjung mengambil pesan baru (balasan tim) ---------- */
    case 'web_poll': {
        $convId = trim((string)($_GET['conversation_id'] ?? '')); $visitorId = trim((string)($_GET['visitor_id'] ?? ''));
        if ($convId === '' || $visitorId === '') jsonOut(['ok' => false, 'error' => 'conversation_id and visitor_id required'], 400);
        if (!checkRateLimit('webpoll:' . clientIp(), 600)) jsonOut(['ok' => false, 'error' => 'Terlalu banyak permintaan.'], 429);
        $convs = webConvReadAll();
        $idx = webConvFind($convs, $convId);
        if ($idx < 0 || ($convs[$idx]['visitor_id'] ?? '') !== $visitorId) jsonOut(['ok' => false, 'error' => 'Conversation not found'], 404);
        $msgs = webConvLoadMessages($convId);
        $after = max(0, (int)($_GET['after'] ?? 0));
        jsonOut(['ok' => true, 'status' => deiWebPub($convs[$idx]), 'total' => count($msgs),
                 'messages' => array_map('deiWebMsgOut', array_slice($msgs, min($after, count($msgs))))]);
        break;
    }

    /* ---------- v1.2.195: web-balas — ADMIN: pegang / balas / kembalikan ke bot ---------- */
    case 'web_claim': {
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        $convId = trim((string)(bodyInput()['conversation_id'] ?? ''));
        list($convs, $idx) = deiWebAdminConv($u, $convId, true);
        $convs[$idx]['agent'] = (string)$u['username'];
        $convs[$idx]['agent_name'] = (string)($u['name'] ?? $u['username']);
        $convs[$idx]['agent_at'] = time();
        $convs[$idx]['agent_last'] = time();
        webConvWrite($convs);
        jsonOut(['ok' => true, 'web' => deiWebAdminStatus($convs[$idx], $u)]);
        break;
    }
    case 'web_reply': {
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        $in = bodyInput();
        $convId = trim((string)($in['conversation_id'] ?? ''));
        $text = trim(str_replace("\r", '', (string)($in['text'] ?? '')));
        if ($text === '') jsonOut(['ok' => false, 'error' => 'Balasan kosong.'], 400);
        if (mb_strlen($text) > 4000) $text = mb_substr($text, 0, 4000);
        list($convs, $idx) = deiWebAdminConv($u, $convId, true);
        $now = date('Y-m-d H:i:s');
        $name = (string)($u['name'] ?? $u['username']);
        $msgs = webConvLoadMessages($convId);
        $msgs[] = ['role' => 'agent', 'content' => $text, 'ts' => $now, 'by' => $name, 'by_u' => (string)$u['username']];
        webConvSaveMessages($convId, $msgs);
        $convs[$idx]['agent'] = (string)$u['username'];
        $convs[$idx]['agent_name'] = $name;
        if (empty($convs[$idx]['agent_at'])) $convs[$idx]['agent_at'] = time();
        $convs[$idx]['agent_last'] = time();
        unset($convs[$idx]['human_req']);
        $convs[$idx]['last_ts'] = $now;
        $convs[$idx]['last_answer'] = mb_substr($text, 0, 120);
        $convs[$idx]['message_count'] = count($msgs);
        webConvWrite($convs);
        jsonOut(['ok' => true, 'web' => deiWebAdminStatus($convs[$idx], $u)]);
        break;
    }
    case 'web_release': {
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        $convId = trim((string)(bodyInput()['conversation_id'] ?? ''));
        list($convs, $idx) = deiWebAdminConv($u, $convId, true);
        $was = deiWebHold($convs[$idx]);
        unset($convs[$idx]['agent'], $convs[$idx]['agent_name'], $convs[$idx]['agent_at'], $convs[$idx]['agent_last'], $convs[$idx]['human_req']);
        if ($was !== '') {
            $msgs = webConvLoadMessages($convId);
            $msgs[] = ['role' => 'assistant', 'content' => 'Percakapan dikembalikan ke asisten otomatis. Silakan lanjutkan bertanya kapan saja.', 'ts' => date('Y-m-d H:i:s'), 'sys' => 'release'];
            webConvSaveMessages($convId, $msgs);
            $convs[$idx]['message_count'] = count($msgs);
        }
        webConvWrite($convs);
        jsonOut(['ok' => true, 'web' => deiWebAdminStatus($convs[$idx], $u)]);
        break;
    }

