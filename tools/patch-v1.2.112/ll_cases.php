    /* ---------- v1.2.112: login-log — riwayat login (Super Admin & Admin) ---------- */
    case 'login_log': {
        $me   = requireAuth(['super_admin', 'admin']);
        $isSa = ($me['role'] ?? '') === 'super_admin';
        $all  = (array)readJson(LOGIN_LOG_FILE, []);
        $intl = [];
        foreach ((array)readJson(USERS_FILE, []) as $x) if (!empty($x['internal'])) $intl[$x['username'] ?? ''] = 1;
        // Admin tidak melihat aktivitas akun internal DEI (sama seperti daftar Pengguna)
        if (!$isSa) $all = array_values(array_filter($all, function ($e) use ($intl) {
            return is_array($e) && empty($e['in']) && !isset($intl[$e['u'] ?? '']);
        }));
        $now = time();
        $ok24 = 0; $fail24 = 0; $names = [];
        foreach ($all as $e) {
            if (!is_array($e)) continue;
            if ((int)($e['t'] ?? 0) >= $now - 86400) { if (!empty($e['ok'])) $ok24++; else $fail24++; }
            $names[(string)($e['u'] ?? '')] = 1;
        }
        unset($names['']);
        $names = array_keys($names); sort($names, SORT_NATURAL | SORT_FLAG_CASE);
        $days   = min(LOGIN_LOG_DAYS, max(1, (int)($_GET['days'] ?? 30)));
        $status = (string)($_GET['status'] ?? '');
        $fu     = trim((string)($_GET['user'] ?? ''));
        $cut    = $now - $days * 86400;
        $rows = array_values(array_filter($all, function ($e) use ($cut, $status, $fu) {
            if (!is_array($e) || (int)($e['t'] ?? 0) < $cut) return false;
            if ($status === 'ok' && empty($e['ok'])) return false;
            if ($status === 'fail' && !empty($e['ok'])) return false;
            if ($fu !== '' && strcasecmp((string)($e['u'] ?? ''), $fu) !== 0) return false;
            return true;
        }));
        $limit = min(1000, max(10, (int)($_GET['limit'] ?? 300)));
        jsonOut(['ok' => true, 'entries' => array_slice($rows, 0, $limit), 'total' => count($rows),
                 'usernames' => $names, 'stats' => ['ok24' => $ok24, 'fail24' => $fail24], 'days' => $days]);
        break;
    }
    /* v1.2.112: riwayat login akun sendiri (Profil Saya) */
    case 'my_login_log': {
        $me = requireAuth();
        $mine = [];
        foreach ((array)readJson(LOGIN_LOG_FILE, []) as $e) {
            if (!is_array($e) || ($e['u'] ?? '') !== ($me['username'] ?? '')) continue;
            unset($e['ua']);
            $mine[] = $e;
            if (count($mine) >= 10) break;
        }
        jsonOut(['ok' => true, 'entries' => $mine]);
        break;
    }
