    /* ---------- v1.2.184: lupa-password (publik) ---------- */
    case 'forgot_password': {
        $in = bodyInput();
        $q = trim((string)($in['login'] ?? ''));
        if ($q === '' || mb_strlen($q) > 190) jsonOut(['ok' => false, 'error' => 'Isi username atau email Anda.'], 400);
        $msg = 'Jika username/email tersebut terdaftar dan punya email, tautan reset password sudah dikirim (berlaku 30 menit). Cek Inbox dan folder Spam. Tidak menerima email? Minta Admin atau Super Admin Anda mengganti password.';
        $ip = clientIp();
        $users = readJson(USERS_FILE, []);
        $ql = mb_strtolower($q); $hit = null;
        foreach ($users as $x) {
            if (empty($x['internal']) && mb_strtolower((string)($x['username'] ?? '')) === $ql) { $hit = $x; break; }
        }
        if (!$hit && ($qe = deiValidEmail($q)) !== '') {
            $m = [];
            foreach ($users as $x) if (empty($x['internal']) && deiUserEmail($x) === $qe) $m[] = $x;
            if (count($m) === 1) $hit = $m[0];
        }
        $to = $hit ? deiUserEmail($hit) : '';
        $tok = deiPwResetStore(function (&$all, $now) use ($ip, $hit, $to) {
            $ipN = 0; $uN = 0;
            foreach ($all as $r) {
                if ((int)($r['at'] ?? 0) >= $now - 900 && ($r['ip'] ?? '') === $ip) $ipN++;
                if ($hit && (int)($r['at'] ?? 0) >= $now - 3600 && ($r['u'] ?? '') === $hit['username']) $uN++;
            }
            if ($ipN >= 5) return 'ip';
            if (!$hit || $to === '') { $all['x' . bin2hex(random_bytes(6))] = ['u' => '', 'at' => $now, 'exp' => 0, 'ip' => $ip, 'used' => 1]; return ''; }
            if ($uN >= 3) return '';
            foreach ($all as $k => $r) if (($r['u'] ?? '') === $hit['username']) $all[$k]['used'] = 1;   // tautan lama gugur
            $t = bin2hex(random_bytes(32));
            $all[hash('sha256', $t)] = ['u' => $hit['username'], 'at' => $now, 'exp' => $now + PWRESET_TTL, 'ip' => $ip];
            return $t;
        });
        if ($tok === 'ip') jsonOut(['ok' => false, 'error' => 'Terlalu banyak permintaan reset dari jaringan ini. Coba lagi dalam 15 menit.'], 429);
        if ($tok !== '') {
            $r = deiPwResetMail($hit, $to, deiDashboardUrl() . 'login.html#reset=' . $tok, $ip);
            $h = hash('sha256', $tok);
            deiPwResetStore(function (&$all) use ($h, $r) { if (isset($all[$h])) $all[$h]['mail'] = !empty($r['ok']) ? ('ok:' . ($r['via'] ?? '')) : ('gagal:' . mb_substr((string)($r['error'] ?? ''), 0, 120)); });
            if (empty($r['ok'])) error_log('[lupa-password] email gagal ke ' . deiMaskEmail($to) . ': ' . ($r['error'] ?? ''));
        }
        jsonOut(['ok' => true, 'message' => $msg]);
        break;
    }

    case 'reset_password_check': {   // v1.2.184: lupa-password
        $in = bodyInput();
        $t = strtolower(trim((string)($in['token'] ?? '')));
        $rec = preg_match('/^[a-f0-9]{64}$/', $t) ? (readJson(PWRESET_FILE, [])[hash('sha256', $t)] ?? null) : null;
        if (!$rec || !empty($rec['used']) || (int)($rec['exp'] ?? 0) < time()) {
            jsonOut(['ok' => false, 'error' => 'Tautan reset tidak valid, sudah dipakai, atau kedaluwarsa. Minta tautan baru.', 'expired' => true], 400);
        }
        jsonOut(['ok' => true, 'username' => (string)$rec['u'], 'expires_in' => max(0, (int)$rec['exp'] - time())]);
        break;
    }

    case 'reset_password': {   // v1.2.184: lupa-password
        $in = bodyInput();
        $t = strtolower(trim((string)($in['token'] ?? '')));
        $pw = (string)($in['new_password'] ?? '');
        if (!preg_match('/^[a-f0-9]{64}$/', $t)) jsonOut(['ok' => false, 'error' => 'Tautan reset tidak valid. Minta tautan baru.', 'expired' => true], 400);
        $weak = checkPasswordStrength($pw);
        if ($weak) jsonOut(['ok' => false, 'error' => $weak], 400);
        $h = hash('sha256', $t);
        $un = deiPwResetStore(function (&$all, $now) use ($h) {
            $r = $all[$h] ?? null;
            if (!$r || !empty($r['used']) || (int)($r['exp'] ?? 0) < $now) return '';
            foreach ($all as $k => $x) if (($x['u'] ?? '') === $r['u']) $all[$k]['used'] = 1;
            $all[$h]['done'] = $now;
            return (string)$r['u'];
        });
        if ($un === '') jsonOut(['ok' => false, 'error' => 'Tautan reset tidak valid, sudah dipakai, atau kedaluwarsa. Minta tautan baru.', 'expired' => true], 400);
        $users = readJson(USERS_FILE, []); $uRow = null;
        foreach ($users as $i => $x) {
            if (($x['username'] ?? '') !== $un) continue;
            $users[$i]['password'] = password_hash($pw, PASSWORD_DEFAULT);
            $users[$i]['pw_changed_at'] = time();
            $uRow = $users[$i];
            break;
        }
        if (!$uRow) jsonOut(['ok' => false, 'error' => 'Akun tidak ditemukan.'], 404);
        writeJson(USERS_FILE, $users);
        lockoutClear($un);
        try { if (($em = deiUserEmail($uRow)) !== '') deiPwChangedMail($uRow, $em, clientIp()); } catch (\Throwable $e) { error_log('pw_changed mail: ' . $e->getMessage()); }
        jsonOut(['ok' => true, 'username' => $un, 'message' => 'Password berhasil diganti. Silakan masuk dengan password baru.']);
        break;
    }

