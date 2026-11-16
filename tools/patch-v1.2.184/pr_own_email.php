    case 'update_own_email': {
        // v1.2.184: lupa-password — email pemulihan akun sendiri (konfirmasi password)
        $u = requireAuth(['super_admin', 'admin', 'wa_agent']);
        $in = bodyInput();
        $raw = trim((string)($in['email'] ?? ''));
        $pw = (string)($in['current_password'] ?? '');
        $em = deiValidEmail($raw);
        if ($raw !== '' && $em === '') jsonOut(['ok' => false, 'error' => 'Format email tidak valid.'], 400);
        if ($pw === '') jsonOut(['ok' => false, 'error' => 'Masukkan password Anda untuk konfirmasi.'], 400);
        $users = readJson(USERS_FILE, []);
        if (deiEmailTaken($em, $u['username'], $users)) jsonOut(['ok' => false, 'error' => 'Email ini sudah dipakai akun lain.'], 400);
        foreach ($users as $i => $x) {
            if (($x['username'] ?? '') !== $u['username']) continue;
            if (!password_verify($pw, (string)($x['password'] ?? ''))) jsonOut(['ok' => false, 'error' => 'Password salah.'], 400);
            if ($em === '') unset($users[$i]['email']); else $users[$i]['email'] = $em;
            writeJson(USERS_FILE, $users);
            jsonOut(['ok' => true, 'email' => $em, 'reset_email' => deiUserEmail($users[$i])]);
        }
        jsonOut(['ok' => false, 'error' => 'User tidak ditemukan.'], 404);
        break;
    }

