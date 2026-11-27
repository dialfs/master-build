    case 'add_contact': {   // v1.2.224: kontak-manual — tambah satu kontak dari menu Kontak
        $me = requireAuth(['super_admin', 'admin', 'wa_agent']);
        if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'POST') jsonOut(['ok' => false, 'error' => 'Gunakan POST.'], 405);
        $in  = bodyInput();
        $num = contactImportNormNum($in['number'] ?? '');
        if ($num === '') jsonOut(['ok' => false, 'error' => 'Nomor WhatsApp tidak valid. Contoh: 0812xxxxxxx atau +62 812xxxxxxx.'], 400);
        $nm = trim(preg_replace('/\s+/u', ' ', (string)($in['name'] ?? '')));
        if ($nm === '') jsonOut(['ok' => false, 'error' => 'Nama kontak wajib diisi.'], 400);
        $nm = mb_substr($nm, 0, 100);
        $stage = (string)($in['stage'] ?? 'new');
        if (!contactStageValid($stage)) jsonOut(['ok' => false, 'error' => 'Lead Rating tidak dikenal.'], 400);
        $vip = ($stage === 'active_customer') && !empty($in['vip']);
        $custDob = trim((string)($in['cust_dob'] ?? ''));
        if ($custDob !== '' && !preg_match('/^\d{4}-\d{2}-\d{2}$/', $custDob)) jsonOut(['ok' => false, 'error' => 'Format tanggal lahir tidak valid (YYYY-MM-DD).'], 400);
        if ($stage !== 'active_customer') $custDob = '';
        // Agent yang dibatasi Lead Rating hanya boleh menambah kontak di Lead Rating yang ia tangani.
        $allowed = deiUserReplyStages($me);
        if ($allowed && !deiStageAllowed($allowed, $stage, $vip)) {
            jsonOut(['ok' => false, 'error' => 'Akun Anda hanya menangani kontak dengan Lead Rating: ' . deiReplyStagesLabel($allowed) . '.'], 403);
        }
        $now = date('Y-m-d H:i:s'); $by = (string)($me['username'] ?? '?');
        $made = false;
        $row = waContactUpdate($num, function (&$c, $isNew) use ($nm, $stage, $vip, $custDob, $now, $by, &$made) {
            if (!$isNew) return false;   // sudah ada -> jangan ditimpa
            $c['name_manual'] = $nm;
            $c['first_seen'] = $now;
            $c['last_seen'] = '';        // belum pernah chat
            $c['stage'] = $stage; $c['vip'] = $vip; $c['stage_updated_at'] = $now;
            if ($stage === 'active_customer') { $c['cust_name'] = $nm; if ($custDob !== '') $c['cust_dob'] = $custDob; }
            $c['man'] = ['at' => $now, 'by' => $by];
            $made = true;
        });
        if (!$made) {
            jsonOut(['ok' => false, 'exists' => true, 'number' => $num, 'name' => waContactName($num),
                     'error' => 'Nomor +' . $num . ' sudah ada di Kontak' . (waContactName($num) !== '' ? ' (' . waContactName($num) . ')' : '') . '.'], 409);
        }
        try { waAuditLog('contact_add', $by, $num, ['stage' => $stage]); } catch (\Throwable $e) {}
        jsonOut(['ok' => true, 'number' => $num, 'name' => waContactName($num), 'stage' => $stage, 'vip' => $vip]);
        break;
    }

