    /* v1.2.111: blokir-total — pusat mendorong status lisensi (langsung saat admin mengubah status) */
    case 'license_push': {
        if (PHP_SAPI !== 'cli' && !deiCentralAuthOk()) {
            if (is_file(LIC_BLOCK_FLAG)) deiBlockedOut();
            jsonOut(['ok' => false, 'error' => 'Kredensial pusat tidak cocok.'], 401);
        }
        $raw = $_SERVER['HTTP_X_DEI_LICENSE'] ?? '';
        if ($raw === '') $raw = (string)file_get_contents('php://input');
        $st = deiApplyLicensePush($raw, getSettings());
        if ($st === null) jsonOut(['ok' => false, 'error' => 'Data lisensi tidak valid.'], 400);
        jsonOut(['ok' => true, 'version' => DEI_VERSION, 'license_status' => $st,
            'blocked' => is_file(LIC_BLOCK_FLAG), 'htaccess_ok' => (bool)($GLOBALS['dei_block_ht'] ?? true)]);
    }

