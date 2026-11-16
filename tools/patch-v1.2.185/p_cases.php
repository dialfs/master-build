    /* ========================================================
     * v1.2.185: master-grup — Dashboard Grup (lihat backend/group-lib.php)
     * ====================================================== */

    // ---------- Admin Pusat: kelola grup ----------
    case 'group_list': {
        requireAdmin();
        $tn = grpTenantsById(); $out = [];
        foreach (grpAll() as $g) {
            $out[] = ['id' => $g['id'], 'name' => $g['name'] ?? '', 'created' => $g['created'] ?? '',
                      'tenant_ids' => array_values((array)($g['tenant_ids'] ?? [])),
                      'tenants' => array_map(function ($id) use ($tn) { $t = $tn[$id] ?? null;
                          return ['tenant_id' => $id, 'name' => $t['name'] ?? $id, 'exists' => (bool)$t, 'version' => $t['current_version'] ?? '', 'api_url' => (bool)trim((string)($t['api_url'] ?? ''))]; }, (array)($g['tenant_ids'] ?? [])),
                      'users' => array_map('grpUserPublic', (array)($g['users'] ?? []))];
        }
        jsonOut(['ok' => true, 'groups' => $out, 'max_tenants' => GRP_MAX_TENANTS, 'min_version' => GRP_MIN_VER, 'url' => grpBaseUrl()]);
    }
    case 'group_save': {
        requireAdmin();
        $in = bodyInput(); $tn = grpTenantsById();
        $name = mb_substr(trim((string)($in['name'] ?? '')), 0, 80);
        if ($name === '') jsonOut(['ok' => false, 'error' => 'Nama grup wajib.'], 400);
        $ids = [];
        foreach ((array)($in['tenant_ids'] ?? []) as $x) { $x = tidNorm((string)$x); if ($x !== '' && isset($tn[$x]) && !in_array($x, $ids, true)) $ids[] = $x; }
        if (count($ids) > GRP_MAX_TENANTS) jsonOut(['ok' => false, 'error' => 'Maksimal ' . GRP_MAX_TENANTS . ' tenant per grup.'], 400);
        $groups = grpAll(); $id = (string)($in['id'] ?? ''); $found = false;
        foreach ($groups as $i => $g) if (($g['id'] ?? '') === $id && $id !== '') {
            $groups[$i]['name'] = $name; $groups[$i]['tenant_ids'] = $ids; $found = true;
            foreach ((array)($g['users'] ?? []) as $ui => $u) {   // batasan user & pemetaan ikut dirapikan
                $groups[$i]['users'][$ui]['tenants'] = array_values(array_intersect((array)($u['tenants'] ?? []), $ids));
                $groups[$i]['users'][$ui]['map'] = array_intersect_key((array)($u['map'] ?? []), array_flip($ids));
            }
        }
        if (!$found) { $id = grpId('g'); $groups[] = ['id' => $id, 'name' => $name, 'tenant_ids' => $ids, 'created' => wibDate('Y-m-d H:i:s'), 'users' => []]; }
        grpSaveAll($groups);
        jsonOut(['ok' => true, 'id' => $id]);
    }
    case 'group_delete': {
        requireAdmin();
        $id = (string)(bodyInput()['id'] ?? '');
        $groups = array_values(array_filter(grpAll(), function ($g) use ($id) { return ($g['id'] ?? '') !== $id; }));
        grpSaveAll($groups);
        jsonOut(['ok' => true]);
    }
    case 'group_user_save': {
        requireAdmin();
        $in = bodyInput(); $groups = grpAll();
        $gi = null; foreach ($groups as $i => $g) if (($g['id'] ?? '') === (string)($in['group_id'] ?? '')) $gi = $i;
        if ($gi === null) jsonOut(['ok' => false, 'error' => 'Grup tidak ditemukan.'], 404);
        $g = $groups[$gi]; $gt = (array)($g['tenant_ids'] ?? []);
        $email = grpEmail($in['email'] ?? '');
        if ($email === '') jsonOut(['ok' => false, 'error' => 'Email tidak valid.'], 400);
        $uid = (string)($in['id'] ?? '');
        $dup = grpFindUser($groups, $email);
        if ($dup && !($dup[0] === $gi && ($groups[$gi]['users'][$dup[1]]['id'] ?? '') === $uid)) jsonOut(['ok' => false, 'error' => 'Email ini sudah dipakai user grup lain.'], 400);
        $role = in_array(($in['role'] ?? ''), ['manager', 'viewer'], true) ? $in['role'] : 'manager';
        $tenants = array_values(array_intersect(array_map('tidNorm', array_map('strval', (array)($in['tenants'] ?? []))), $gt));
        $map = [];
        foreach ((array)($in['map'] ?? []) as $tid => $un) { $tid = tidNorm((string)$tid); $un = mb_substr(trim((string)$un), 0, 60); if ($un !== '' && in_array($tid, $gt, true)) $map[$tid] = $un; }
        $pw = (string)($in['password'] ?? '');
        if ($pw !== '' && ($e = grpPwOk($pw)) !== '') jsonOut(['ok' => false, 'error' => $e], 400);
        $row = null; $ui = null;
        foreach ((array)($g['users'] ?? []) as $i => $u) if (($u['id'] ?? '') === $uid && $uid !== '') { $row = $u; $ui = $i; }
        $isNew = $row === null;
        if ($isNew) $row = ['id' => grpId('u'), 'created' => wibDate('Y-m-d H:i:s')];
        $row['email'] = $email; $row['name'] = mb_substr(trim((string)($in['name'] ?? '')), 0, 80); $row['role'] = $role;
        $row['tenants'] = $tenants; $row['map'] = $map; $row['disabled'] = !empty($in['disabled']);
        if ($pw !== '') { $row['password'] = password_hash($pw, PASSWORD_DEFAULT); $row['pw_changed_at'] = time(); }
        if ($isNew) $groups[$gi]['users'][] = $row; else $groups[$gi]['users'][$ui] = $row;
        grpSaveAll($groups);
        $sent = null;
        if (!empty($in['send_invite'])) $sent = grpSendLink($groups[$gi], $row, empty($row['password']) || $isNew);
        jsonOut(['ok' => true, 'id' => $row['id'], 'invite_sent' => $sent]);
    }
    case 'group_user_delete': {
        requireAdmin();
        $in = bodyInput(); $groups = grpAll();
        foreach ($groups as $i => $g) if (($g['id'] ?? '') === (string)($in['group_id'] ?? ''))
            $groups[$i]['users'] = array_values(array_filter((array)($g['users'] ?? []), function ($u) use ($in) { return ($u['id'] ?? '') !== (string)($in['id'] ?? ''); }));
        grpSaveAll($groups);
        jsonOut(['ok' => true]);
    }
    case 'group_user_link': {   // tautan atur password (dikirim email + bisa disalin admin)
        requireAdmin();
        $in = bodyInput();
        foreach (grpAll() as $g) if (($g['id'] ?? '') === (string)($in['group_id'] ?? '')) foreach ((array)($g['users'] ?? []) as $u) if (($u['id'] ?? '') === (string)($in['id'] ?? '')) {
            if (!empty($in['email'])) jsonOut(['ok' => true, 'sent' => grpSendLink($g, $u, empty($u['password']))]);
            jsonOut(['ok' => true, 'url' => grpResetLink((string)$u['email'], 3 * 86400)]);
        }
        jsonOut(['ok' => false, 'error' => 'User tidak ditemukan.'], 404);
    }
    case 'group_tenant_users': {   // daftar akun di tenant, untuk memetakan user grup
        requireAdmin();
        $tid = tidNorm((string)($_GET['tenant_id'] ?? ''));
        $t = grpTenantsById()[$tid] ?? null;
        if (!$t) jsonOut(['ok' => false, 'error' => 'Tenant tidak ditemukan.'], 404);
        $r = grpFetchMulti(['x' => [$t, 'grp_users', []]], 15)['x'];
        if (empty($r['ok'])) jsonOut(['ok' => false, 'error' => grpVerNote($t, $r)]);
        jsonOut(['ok' => true, 'users' => $r['users'] ?? []]);
    }

    // ---------- Dashboard Grup (/grup/) ----------
    case 'grp_login': {
        $in = bodyInput();
        $email = grpEmail($in['email'] ?? ''); $pw = (string)($in['password'] ?? '');
        $bad = 'Email atau password salah.';
        if ($email === '' || $pw === '') jsonOut(['ok' => false, 'error' => $bad], 401);
        if (grpRlBlocked($email)) jsonOut(['ok' => false, 'error' => 'Terlalu banyak percobaan. Coba lagi 15 menit lagi.'], 429);
        $groups = grpAll(); $f = grpFindUser($groups, $email);
        $u = $f ? $groups[$f[0]]['users'][$f[1]] : null;
        if (!$u || empty($u['password']) || !password_verify($pw, (string)$u['password'])) { grpRlFail($email); jsonOut(['ok' => false, 'error' => $bad], 401); }
        if (!empty($u['disabled'])) jsonOut(['ok' => false, 'error' => 'Akun Anda dinonaktifkan. Hubungi DEI.'], 403);
        grpRlClear($email);
        $groups[$f[0]]['users'][$f[1]]['last_login'] = wibDate('Y-m-d H:i:s');
        grpSaveAll($groups);
        jsonOut(['ok' => true, 'token' => grpMakeToken($email)]);
    }
    case 'grp_me': {
        [, , $g, $u] = grpRequire();
        $tn = grpTenantsById(); $list = [];
        foreach (grpUserTenantIds($g, $u) as $tid) {
            $t = $tn[$tid] ?? null; if (!$t) continue;
            $list[] = ['tenant_id' => $tid, 'name' => (string)($t['name'] ?? $tid), 'active' => !empty($t['active']),
                       'version' => (string)($t['current_version'] ?? ''),
                       'can_open' => ($u['role'] ?? 'manager') === 'manager' && !empty(((array)($u['map'] ?? []))[$tid])];
        }
        jsonOut(['ok' => true, 'user' => ['email' => $u['email'], 'name' => $u['name'] ?? '', 'role' => $u['role'] ?? 'manager'],
                 'group' => ['id' => $g['id'], 'name' => $g['name'] ?? ''], 'tenants' => $list]);
    }
    case 'grp_report': {
        [, , $g, $u] = grpRequire();
        $from = substr((string)($_GET['from'] ?? ''), 0, 10); $to = substr((string)($_GET['to'] ?? ''), 0, 10);
        $tn = grpTenantsById(); $jobs = [];
        foreach (grpUserTenantIds($g, $u) as $tid) if (isset($tn[$tid])) $jobs[$tid] = [$tn[$tid], 'grp_report', ['from' => $from, 'to' => $to]];
        $out = [];
        foreach (grpFetchMulti($jobs, 25) as $tid => $r) {
            $t = $tn[$tid];
            if (empty($r['ok'])) { $out[] = ['tenant_id' => $tid, 'name' => (string)($t['name'] ?? $tid), 'ok' => false, 'error' => grpVerNote($t, $r)]; continue; }
            unset($r['_http']);
            $out[] = ['tenant_id' => $tid, 'name' => (string)($t['name'] ?? $tid)] + $r;
        }
        jsonOut(['ok' => true, 'from' => $from, 'to' => $to, 'tenants' => $out]);
    }
    case 'grp_sso': {
        [, , $g, $u] = grpRequire();
        $tid = tidNorm((string)(bodyInput()['tenant_id'] ?? ''));
        if (!in_array($tid, grpUserTenantIds($g, $u), true)) jsonOut(['ok' => false, 'error' => 'Tenant ini tidak termasuk akses Anda.'], 403);
        if (($u['role'] ?? 'manager') !== 'manager') jsonOut(['ok' => false, 'error' => 'Akun Anda hanya untuk melihat laporan.'], 403);
        $un = (string)(((array)($u['map'] ?? []))[$tid] ?? '');
        if ($un === '') jsonOut(['ok' => false, 'error' => 'Akun Anda belum dihubungkan ke akun di tenant ini. Hubungi DEI.'], 400);
        $t = grpTenantsById()[$tid] ?? null;
        $dash = $t ? suTenantDashUrl($t) : '';
        if ($dash === '') jsonOut(['ok' => false, 'error' => 'URL tenant belum diketahui.'], 400);
        $p = ['t' => $tid, 'u' => $un, 'exp' => time() + 120, 'n' => bin2hex(random_bytes(12)), 'g' => (string)$g['id'], 'name' => (string)($u['name'] ?? '')];
        $b = rtrim(strtr(base64_encode(json_encode($p)), '+/', '-_'), '=');
        jsonOut(['ok' => true, 'url' => $dash . '#sso=' . rawurlencode($b . '.' . hash_hmac('sha256', $b, (string)$t['license_key']))]);
    }
    case 'grp_forgot': {
        $email = grpEmail(bodyInput()['email'] ?? '');
        $msg = 'Bila email terdaftar, tautan reset password sudah dikirim. Cek Inbox/Spam.';
        if ($email === '' || grpRlBlocked('forgot|' . $email)) jsonOut(['ok' => true, 'message' => $msg]);
        grpRlFail('forgot|' . $email); grpRlFail('forgot|' . $email);   // maks 4 permintaan / 15 menit
        $groups = grpAll(); $f = grpFindUser($groups, $email);
        if ($f && empty($groups[$f[0]]['users'][$f[1]]['disabled'])) grpSendLink($groups[$f[0]], $groups[$f[0]]['users'][$f[1]], false);
        jsonOut(['ok' => true, 'message' => $msg]);
    }
    case 'grp_reset_check': {
        $email = grpResetLookup((string)(bodyInput()['token'] ?? ''), false);
        if ($email === null) jsonOut(['ok' => false, 'error' => 'Tautan tidak berlaku atau sudah dipakai. Minta tautan baru.'], 400);
        jsonOut(['ok' => true, 'email' => $email]);
    }
    case 'grp_reset': {
        $in = bodyInput(); $pw = (string)($in['password'] ?? '');
        if (($e = grpPwOk($pw)) !== '') jsonOut(['ok' => false, 'error' => $e], 400);
        $email = grpResetLookup((string)($in['token'] ?? ''), true);
        if ($email === null) jsonOut(['ok' => false, 'error' => 'Tautan tidak berlaku atau sudah dipakai. Minta tautan baru.'], 400);
        $groups = grpAll(); $f = grpFindUser($groups, $email);
        if (!$f) jsonOut(['ok' => false, 'error' => 'Akun tidak ditemukan.'], 404);
        $groups[$f[0]]['users'][$f[1]]['password'] = password_hash($pw, PASSWORD_DEFAULT);
        $groups[$f[0]]['users'][$f[1]]['pw_changed_at'] = time();
        grpSaveAll($groups); grpRlClear($email);
        jsonOut(['ok' => true, 'email' => $email]);
    }
    case 'grp_password': {
        [$gi, $ui, , $u] = grpRequire();
        $in = bodyInput(); $pw = (string)($in['new'] ?? '');
        if (!password_verify((string)($in['old'] ?? ''), (string)($u['password'] ?? ''))) jsonOut(['ok' => false, 'error' => 'Password lama salah.'], 400);
        if (($e = grpPwOk($pw)) !== '') jsonOut(['ok' => false, 'error' => $e], 400);
        $groups = grpAll();
        $groups[$gi]['users'][$ui]['password'] = password_hash($pw, PASSWORD_DEFAULT);
        $groups[$gi]['users'][$ui]['pw_changed_at'] = time() - 1;
        grpSaveAll($groups);
        jsonOut(['ok' => true, 'token' => grpMakeToken((string)$u['email'])]);
    }

