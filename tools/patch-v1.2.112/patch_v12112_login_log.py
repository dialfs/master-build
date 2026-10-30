#!/usr/bin/env python3
"""v1.2.112 login-log: riwayat login dasbor (sukses & gagal, IP, perangkat).
Pakai: python3 patch_v12112_login_log.py [~/Herd/dei-tenant]
Idempoten: backup -> str.replace anchor -> versi. Lint (php -l) dijalankan terpisah."""
import os, sys, time, shutil

ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.112: login-log'
STAMP = time.strftime('%Y%m%d-%H%M%S')
HERE = os.path.dirname(os.path.abspath(__file__))
part = lambda n: open(os.path.join(HERE, n), encoding='utf-8').read()

def patch(rel, edits):
    p = os.path.join(ROOT, rel)
    s = open(p, encoding='utf-8').read()
    if TAG in s:
        print('sudah dipatch:', rel); return
    shutil.copy2(p, p + '.bak-v12112-' + STAMP)
    for old, new in edits:
        n = s.count(old)
        assert n == 1, '%s: anchor ditemukan %dx: %r' % (rel, n, old[:80])
        s = s.replace(old, new)
    assert TAG in s, rel + ': TAG tidak masuk'
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

# ---------------- api/index.php ----------------
API = [
    # versi
    (
        "define('DEI_VERSION', 'v1.2.111');   // v1.2.111: blokir-total",
        "define('DEI_VERSION', 'v1.2.112');   // v1.2.112: login-log",
    ),
    # fungsi
    (
        "/** Returns null if OK, or an error string explaining why password is too weak. */",
        part('ll_funcs.php') + "\n/** Returns null if OK, or an error string explaining why password is too weak. */",
    ),
    # login: terkunci
    (
        "            $mins = (int)ceil($remaining / 60);\n"
        "            jsonOut(['ok' => false, 'error' => \"Terlalu banyak percobaan. Coba lagi dalam $mins menit.\"], 429);",
        "            $mins = (int)ceil($remaining / 60);\n"
        "            deiLoginLog($username, false, 'password', 'locked');   // v1.2.112\n"
        "            jsonOut(['ok' => false, 'error' => \"Terlalu banyak percobaan. Coba lagi dalam $mins menit.\"], 429);",
    ),
    # login: penanda akun ditemukan
    (
        "        $users = readJson(USERS_FILE, []);\n"
        "        foreach ($users as $idx => $u) {\n"
        "            if (($u['username'] ?? '') !== $username) continue;\n"
        "            $stored = (string)($u['password'] ?? '');",
        "        $users = readJson(USERS_FILE, []);\n"
        "        $llFound = false;   // v1.2.112\n"
        "        foreach ($users as $idx => $u) {\n"
        "            if (($u['username'] ?? '') !== $username) continue;\n"
        "            $llFound = true;\n"
        "            $stored = (string)($u['password'] ?? '');",
    ),
    # login: kursi
    (
        "                if (($role === 'wa_agent' || $role === 'supervisor') && !deiSeatAllowed($username, $role, $users)) {\n"
        "                    jsonOut(['ok' => false, 'error' => deiSeatMsg($role, deiFeatures())], 403);",
        "                if (($role === 'wa_agent' || $role === 'supervisor') && !deiSeatAllowed($username, $role, $users)) {\n"
        "                    deiLoginLog($username, false, 'password', 'seat_limit', ['name' => $u['name'] ?? $username, 'role' => $role]);   // v1.2.112\n"
        "                    jsonOut(['ok' => false, 'error' => deiSeatMsg($role, deiFeatures())], 403);",
    ),
    # login: sukses
    (
        "                    jsonOut(['ok' => false, 'error' => deiSeatMsg($role, deiFeatures())], 403);\n"
        "                }\n"
        "                jsonOut([",
        "                    jsonOut(['ok' => false, 'error' => deiSeatMsg($role, deiFeatures())], 403);\n"
        "                }\n"
        "                deiLoginLog($username, true, 'password', '', ['name' => $u['name'] ?? $username, 'role' => $role] + (!empty($u['internal']) ? ['in' => 1] : []));   // v1.2.112\n"
        "                jsonOut([",
    ),
    # login: gagal
    (
        "        lockoutRecordFail($username);\n"
        "        jsonOut(['ok' => false, 'error' => 'Username atau password salah.'], 401);",
        "        lockoutRecordFail($username);\n"
        "        deiLoginLog($username, false, 'password', $llFound ? 'wrong_password' : 'unknown_user');   // v1.2.112\n"
        "        jsonOut(['ok' => false, 'error' => 'Username atau password salah.'], 401);",
    ),
    # sso: gagal akun / peran, sukses
    (
        "        if (!$found) jsonOut(['ok' => false, 'error' => 'Akun tidak ditemukan.'], 401);\n"
        "        $role = (string)($found['role'] ?? '');\n"
        "        if ($wantSa && $role !== 'super_admin') jsonOut(['ok' => false, 'error' => 'Akun ini bukan Super Admin.'], 403);\n"
        "        if (!in_array($role, ['super_admin', 'admin'], true)) jsonOut(['ok' => false, 'error' => 'Masuk otomatis hanya untuk Admin.'], 403);\n"
        "        lockoutClear($uname);",
        "        if (!$found) { deiLoginLog($uname, false, 'sso', 'unknown_user'); jsonOut(['ok' => false, 'error' => 'Akun tidak ditemukan.'], 401); }   // v1.2.112\n"
        "        $role = (string)($found['role'] ?? '');\n"
        "        if ($wantSa && $role !== 'super_admin') { deiLoginLog($uname, false, 'sso', 'not_sa', ['role' => $role]); jsonOut(['ok' => false, 'error' => 'Akun ini bukan Super Admin.'], 403); }\n"
        "        if (!in_array($role, ['super_admin', 'admin'], true)) { deiLoginLog($uname, false, 'sso', 'not_admin', ['role' => $role]); jsonOut(['ok' => false, 'error' => 'Masuk otomatis hanya untuk Admin.'], 403); }\n"
        "        lockoutClear($uname);\n"
        "        deiLoginLog($uname, true, 'sso', '', ['name' => $found['name'] ?? $uname, 'role' => $role] + (!empty($found['internal']) ? ['in' => 1] : []));",
    ),
    # get_users: login terakhir
    (
        "        $scU = deiSpvScope($meU, $users);",
        "        $llLastMap = deiLoginLastMap();   // v1.2.112\n"
        "        foreach ($safe as $i => $su) { $safe[$i]['last_login'] = $llLastMap[$su['username']]['ts'] ?? ''; }\n"
        "        $scU = deiSpvScope($meU, $users);",
    ),
    # endpoint
    (
        "    case 'wa_audit_log': {",
        part('ll_cases.php') + "\n    case 'wa_audit_log': {",
    ),
]

# ---------------- index.html ----------------
HTML = [
    (
        "<th>Supervisor</th><th></th></tr></thead><tbody id=\"tblUsers\"></tbody></table></div>\n"
        "      </div>\n"
        "    </section>",
        "<th>Supervisor</th><th>Login terakhir</th><th></th></tr></thead><tbody id=\"tblUsers\"></tbody></table></div>\n"
        "      </div>\n" + part('ll_card.html') +
        "    </section>",
    ),
    (
        "          <tr><td style=\"padding:6px 0;color:var(--muted)\">Role</td><td id=\"profileRole\" style=\"font-weight:600\">-</td></tr>\n"
        "        </table>\n"
        "      </div>\n",
        "          <tr><td style=\"padding:6px 0;color:var(--muted)\">Role</td><td id=\"profileRole\" style=\"font-weight:600\">-</td></tr>\n"
        "        </table>\n"
        "      </div>\n" + part('ll_profile.html'),
    ),
]

# ---------------- app.js ----------------
JS = [
    (
        "  function loadUsers() {\n",
        part('ll_app.js') + "  function loadUsers() {\n",
    ),
    (
        "    toggleSpvRow();\n"
        "  }\n"
        "  // v1.2.59: supervisor atasan WA Agent",
        "    toggleSpvRow();\n"
        "    loadLoginLog();   // v1.2.112\n"
        "  }\n"
        "  // v1.2.59: supervisor atasan WA Agent",
    ),
    (
        "      btn.dataset.wired = 'true';\n"
        "    }\n"
        "  }\n"
        "  function changeOwnPassword() {",
        "      btn.dataset.wired = 'true';\n"
        "    }\n"
        "    loadMyLoginLog();   // v1.2.112\n"
        "  }\n"
        "  function changeOwnPassword() {",
    ),
    (
        "'<span class=\"help\" style=\"font-size:11px\">—</span>') : '') + '</td>' +\n",
        "'<span class=\"help\" style=\"font-size:11px\">—</span>') : '') + '</td>' +\n"
        "          '<td class=\"mono\" style=\"font-size:12px;white-space:nowrap;color:var(--muted)\">' + (u.last_login ? esc(u.last_login) : '—') + '</td>' +\n",
    ),
]

patch('api/index.php', API)
patch('dashboard/chatbot-ai/index.html', HTML)
patch('dashboard/chatbot-ai/app.js', JS)
print('selesai', TAG)
