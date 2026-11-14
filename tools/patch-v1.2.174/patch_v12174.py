#!/usr/bin/env python3
"""v1.2.174 update-dari-pusat (TENANT): action=update_remote — pusat memicu update (kredensial X-Tenant-Id + X-License-Key,
sama dengan cron_tick). Jalur: update_check -> update_apply (rantai yang sama dengan update_cli). Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
API = T + '/api/index.php'
TAG = 'v1.2.174: update-dari-pusat'; stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    shutil.copy2(p, p + '.bak-v12174-' + stamp); wr(p, fn(s)); print('OK', p)
C = '   // ' + TAG

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.173');   // v1.2.173:",
               "define('DEI_VERSION', 'v1.2.174');   // " + TAG + " — tim DEI bisa memasang pembaruan langsung dari pusat; v1.2.173:", 'versi')
    s = rep(s, "    case 'update_check': {\n        if (PHP_SAPI !== 'cli') requireAuth(['super_admin']);   // v1.2.71: CLI = admin server\n",
        "    /* ---------- " + TAG + " — pusat memasang versi terbaru (POST, kredensial sama dengan cron_tick) ---------- */\n"
        "    case 'update_remote': {\n"
        "        if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') jsonOut(['ok' => false, 'error' => 'Gunakan POST.'], 405);\n"
        "        $cs = getSettings()['central_server'] ?? [];\n"
        "        $tidWant = strtolower(trim((string)($cs['tenant_id'] ?? ''))); $licWant = (string)($cs['license_key'] ?? '');\n"
        "        if ($tidWant === '' || $licWant === '') jsonOut(['ok' => false, 'error' => 'Server pusat belum dikonfigurasi.'], 403);\n"
        "        $tidGot = strtolower(trim((string)($_SERVER['HTTP_X_TENANT_ID'] ?? ''))); $licGot = trim((string)($_SERVER['HTTP_X_LICENSE_KEY'] ?? ''));\n"
        "        if (!hash_equals($tidWant, $tidGot) || !hash_equals($licWant, $licGot)) jsonOut(['ok' => false, 'error' => 'Kredensial pusat tidak cocok.'], 401);\n"
        "        @ignore_user_abort(true); @set_time_limit(170);\n"
        "        $GLOBALS['dei_cli_chain'] = true; $GLOBALS['dei_remote_upd'] = true;\n"
        "        goto dei_remote_update_check;\n"
        "    }\n\n"
        "    case 'update_check': {\n"
        "        dei_remote_update_check:" + C + "\n"
        "        if (PHP_SAPI !== 'cli' && empty($GLOBALS['dei_remote_upd'])) requireAuth(['super_admin']);   // v1.2.71: CLI = admin server; v1.2.174: atau pusat (update_remote)\n", 'update_remote')
    s = rep(s, "            if (empty($data['update_available'])) { echo \"update_cli: sudah versi terbaru ($current)\\n\"; exit(0); }\n",
               "            if (empty($data['update_available']) && !empty($GLOBALS['dei_remote_upd'])) jsonOut(['ok' => true, 'version' => $current, 'updated' => false, 'latest' => $data['latest'] ?? null]);" + C + "\n"
               "            if (empty($data['update_available'])) { echo \"update_cli: sudah versi terbaru ($current)\\n\"; exit(0); }\n", 'chain no-update')
    s = rep(s, "        if (PHP_SAPI === 'cli' && !empty($GLOBALS['dei_cli_update'])) { $in = $GLOBALS['dei_cli_update']; }\n",
               "        if ((PHP_SAPI === 'cli' || !empty($GLOBALS['dei_remote_upd'])) && !empty($GLOBALS['dei_cli_update'])) { $in = $GLOBALS['dei_cli_update']; }" + C + "\n", 'apply input')
    return s

patch(API, api)
