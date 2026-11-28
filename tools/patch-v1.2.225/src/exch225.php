        // 2) Simpan kredensial + aktifkan provider Meta (verify_token disiapkan dulu: Meta memanggil
        //    handshake ke webhook tenant ini saat override_callback_uri dipasang).   // v1.2.225: es-coex
        $vt = (string)($wa['verify_token'] ?? '');
        if ($vt === '') $vt = bin2hex(random_bytes(12));
        $cur['whatsapp_api'] = array_merge($wa, [
            'provider'        => 'meta',
            'enabled'         => true,
            'access_token'    => $token,
            'verify_token'    => $vt,
            'phone_number_id' => ($pnid !== '' ? $pnid : ($wa['phone_number_id'] ?? '')),
            'waba_id'         => ($waba !== '' ? $waba : ($wa['waba_id'] ?? '')),
            'es_onboarded_at' => date('Y-m-d H:i:s'),
        ]);
        writeJson(SETTINGS_FILE, $cur);
        $pnidS = (string)$cur['whatsapp_api']['phone_number_id']; $wabaS = (string)$cur['whatsapp_api']['waba_id'];

        // 3) Langganan app ke WABA + arahkan webhook WABA ini ke tenant ini.
        $warn = [];
        $sub = ['ok' => false, 'error' => 'WABA ID tidak diterima dari Embedded Signup'];
        if ($wabaS !== '') $sub = deiEsSubscribe($ver, $wabaS, $token, $vt);
        if (empty($sub['ok'])) $warn[] = 'Subscribe app ke WABA gagal (' . ($sub['error'] ?? '') . ') — subscribe manual di Meta lalu klik Sinkron ulang.';
        elseif (!empty($sub['note'])) $warn[] = $sub['note'];

        // 4) Tarik kontak & riwayat chat dari aplikasi WhatsApp Business (sekali, dalam 24 jam).
        $sync = $pnidS !== '' ? deiEsSmbSync($ver, $pnidS, $token) : [];
        foreach ($sync as $t => $r) if ($r !== 'ok') $warn[] = 'Sinkron ' . ($t === 'history' ? 'riwayat chat' : 'kontak') . ' gagal: ' . $r . ' — ulangi lewat tombol Sinkron ulang (batas 24 jam).';
        try { waAuditLog('es_onboard', 'system', '', ['waba' => $wabaS, 'pnid' => $pnidS, 'sub' => !empty($sub['ok']), 'override' => (string)($sub['override'] ?? ''), 'sync' => $sync]); } catch (\Throwable $e) {}

        jsonOut([
            'ok'              => true,
            'phone_number_id' => $pnidS,
            'waba_id'         => $wabaS,
            'webhook'         => (string)($sub['override'] ?? ''),
            'sync'            => $sync,
            'warning'         => implode(' ', $warn),
        ]);
        break;
    }
    case 'wa_es_sync': {   // v1.2.225: es-coex — ulangi subscribe + sinkron kontak/riwayat (maks. 24 jam setelah onboarding)
        requireAuth(['super_admin']);
        $cur = getSettings(); $wa = is_array($cur['whatsapp_api'] ?? null) ? $cur['whatsapp_api'] : [];
        $ver = trim((string)($wa['es_graph_version'] ?? '')) ?: 'v21.0';
        $token = (string)($wa['access_token'] ?? ''); $pnidS = (string)($wa['phone_number_id'] ?? ''); $wabaS = (string)($wa['waba_id'] ?? '');
        if ($token === '' || $pnidS === '') jsonOut(['ok' => false, 'error' => 'Nomor belum terhubung lewat Embedded Signup.'], 400);
        $vt = (string)($wa['verify_token'] ?? '');
        if ($vt === '') { $vt = bin2hex(random_bytes(12)); $cur['whatsapp_api']['verify_token'] = $vt; writeJson(SETTINGS_FILE, $cur); }
        $sub = $wabaS !== '' ? deiEsSubscribe($ver, $wabaS, $token, $vt) : ['ok' => false, 'error' => 'WABA ID kosong'];
        $sync = deiEsSmbSync($ver, $pnidS, $token);
        jsonOut(['ok' => true, 'subscribe' => $sub, 'sync' => $sync]);
        break;
    }
