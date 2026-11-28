    case 'wa_template_create': {   // v1.2.226: buat-template — buat message template baru di WABA (Meta Cloud API)
        $u = requireAuth(['super_admin', 'admin']);
        $in = bodyInput();
        $wa = waConf(getSettings());
        $wa = waMetaChanConf($wa, preg_replace('/[^A-Za-z0-9_]/', '', (string)($in['ch'] ?? '')));
        if (($wa['provider'] ?? 'meta') !== 'meta') jsonOut(['ok' => false, 'error' => 'Template hanya untuk penyedia Meta Cloud API resmi.'], 400);
        $token = (string)($wa['access_token'] ?? ''); $waba = (string)($wa['waba_id'] ?? '');
        if ($token === '' || $waba === '') jsonOut(['ok' => false, 'error' => 'WABA ID atau Access Token belum diisi di menu Widget & API.'], 400);
        $name = strtolower(trim((string)($in['name'] ?? '')));
        $name = preg_replace('/[^a-z0-9_]+/', '_', $name); $name = trim($name, '_');
        $cat  = strtoupper(trim((string)($in['category'] ?? 'UTILITY')));
        $lang = preg_replace('/[^A-Za-z_]/', '', (string)($in['language'] ?? 'id'));
        $head = trim((string)($in['header'] ?? ''));
        $body = trim((string)($in['body'] ?? ''));
        $foot = trim((string)($in['footer'] ?? ''));
        $ex   = array_values(array_map('strval', (array)($in['examples'] ?? [])));
        if ($name === '' || strlen($name) > 512) jsonOut(['ok' => false, 'error' => 'Nama template wajib diisi (huruf kecil, angka, garis bawah).'], 400);
        if (!in_array($cat, ['MARKETING', 'UTILITY'], true)) jsonOut(['ok' => false, 'error' => 'Kategori harus Marketing atau Utility.'], 400);
        if ($lang === '') $lang = 'id';
        if ($body === '' || mb_strlen($body) > 1024) jsonOut(['ok' => false, 'error' => 'Isi pesan wajib diisi (maks. 1024 karakter).'], 400);
        if (mb_strlen($head) > 60) jsonOut(['ok' => false, 'error' => 'Header maks. 60 karakter.'], 400);
        if (mb_strlen($foot) > 60) jsonOut(['ok' => false, 'error' => 'Footer maks. 60 karakter.'], 400);
        if (preg_match('/\{\{/', $head . $foot)) jsonOut(['ok' => false, 'error' => 'Variabel {{n}} hanya boleh di isi pesan.'], 400);
        preg_match_all('/\{\{\s*(\d+)\s*\}\}/', $body, $m);
        $n = !empty($m[1]) ? max(array_map('intval', $m[1])) : 0;
        if ($n > 0) {
            for ($i = 1; $i <= $n; $i++) if (!in_array((string)$i, $m[1], true)) jsonOut(['ok' => false, 'error' => 'Variabel harus berurutan mulai {{1}} (tidak ada {{' . $i . '}}).'], 400);
            if (count($ex) < $n || in_array('', array_map('trim', array_slice($ex, 0, $n)), true)) jsonOut(['ok' => false, 'error' => 'Isi contoh untuk setiap variabel {{1}}–{{' . $n . '}}.'], 400);
        }
        $comps = [];
        if ($head !== '') $comps[] = ['type' => 'HEADER', 'format' => 'TEXT', 'text' => $head];
        $b = ['type' => 'BODY', 'text' => $body];
        if ($n > 0) $b['example'] = ['body_text' => [array_slice($ex, 0, $n)]];
        $comps[] = $b;
        if ($foot !== '') $comps[] = ['type' => 'FOOTER', 'text' => $foot];
        $payload = ['name' => $name, 'language' => $lang, 'category' => $cat, 'components' => $comps];
        $ch = curl_init('https://graph.facebook.com/v21.0/' . rawurlencode($waba) . '/message_templates');
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true, CURLOPT_TIMEOUT => 25,
            CURLOPT_HTTPHEADER => ['Authorization: Bearer ' . $token, 'Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode($payload)]);
        $raw = curl_exec($ch); $hc = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
        $d = json_decode((string)$raw, true);
        if ($hc < 200 || $hc >= 300) {
            $e = is_array($d) ? ($d['error'] ?? []) : [];
            $msg = trim((string)($e['error_user_msg'] ?? $e['message'] ?? ('HTTP ' . $hc)));
            error_log('wa_template_create HTTP ' . $hc . ': ' . mb_substr((string)$raw, 0, 300));
            jsonOut(['ok' => false, 'error' => 'Meta menolak template: ' . $msg], 502);
        }
        try { waAuditLog('template_create', (string)($u['username'] ?? ''), '', ['name' => $name, 'cat' => $cat, 'lang' => $lang, 'id' => (string)($d['id'] ?? '')]); } catch (\Throwable $e) {}
        jsonOut(['ok' => true, 'id' => (string)($d['id'] ?? ''), 'status' => (string)($d['status'] ?? 'PENDING'), 'category' => (string)($d['category'] ?? $cat), 'name' => $name]);
        break;
    }
