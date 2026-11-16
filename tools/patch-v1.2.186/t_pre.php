/* v1.2.186: grup-inbox — Dashboard Grup (pusat) memakai inbox WA tenant atas nama akun tenant yang dipetakan.
 * Auth: X-Tenant-Id + X-License-Key (pusat) + X-Dei-Grp-User (username di tenant). Hak akses tetap mengikuti
 * peran akun itu (requireAuth berjalan seperti biasa). Hanya aksi inbox WA berikut yang boleh diteruskan. */
if ($action === 'grp_as') {
    if (!deiCentralAuthOk()) jsonOut(['ok' => false, 'error' => 'Kredensial pusat tidak cocok.'], 401);
    $grpAct186 = (string)($_GET['act'] ?? '');
    if (!in_array($grpAct186, ['wa_conversations_v2', 'wa_thread', 'wa_send_manual', 'wa_send_media', 'wa_resolve', 'wa_media'], true)) jsonOut(['ok' => false, 'error' => 'Aksi tidak diizinkan.'], 400);
    $grpUser186 = trim((string)($_SERVER['HTTP_X_DEI_GRP_USER'] ?? ''));
    $grpOk186 = false;
    foreach ((array)readJson(USERS_FILE, []) as $x) if (is_array($x) && $grpUser186 !== '' && ($x['username'] ?? '') === $grpUser186 && empty($x['internal'])) $grpOk186 = true;
    if (!$grpOk186) jsonOut(['ok' => false, 'error' => 'Akun tenant yang dihubungkan (' . mb_substr($grpUser186, 0, 60) . ') tidak ditemukan di tenant ini.'], 403);
    $GLOBALS['dei_grp_as'] = $grpUser186;
    $action = $grpAct186; $_GET['action'] = $grpAct186;
}

