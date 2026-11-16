#!/usr/bin/env python3
"""v1.2.185 (master-grup): Dashboard Grup tahap 1 — satu login klien grup untuk beberapa tenant.
Tenant:
- api/index.php: action grp_users & grp_report (auth X-Tenant-Id + X-License-Key), sso_login menerima token
  bertanda grup untuk akun yang dipetakan (peran apa pun), log masuk metode "sso_grup".
- app.js: label log masuk "Dashboard Grup"; index.html: cache-buster app.js?v=1.2.185.
Pusat:
- backend/group-lib.php (baru), backend/index.php: group_* (admin) + grp_* (Dashboard Grup).
- admin/index.html: kartu Dashboard Grup. grup/index.html (baru). dev/deploy.sh: chmod folder grup.
Idempoten.  Pakai: patch_v12185.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
D = os.path.dirname(os.path.abspath(__file__))
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
T = H + '/dei-tenant'; P = H + '/dei-pusat'
TAG = 'v1.2.185: master-grup'; NEED = 'v1.2.184: lupa-password'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12185-' + stamp)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)

# ---------- tenant api ----------
API = T + '/api/index.php'; s = rd(API)
if TAG in s: print('sudah:', API)
else:
    assert NEED in s, 'butuh v1.2.184'
    s = rep(s, "    case 'stats_pull': {\n", rd(D + '/t_cases.php') + "    case 'stats_pull': {\n", what='case stats_pull')
    s = rep(s, "        $wantSa = !empty($p['sa']);\n",
               "        $wantSa = !empty($p['sa']);\n"
               "        $wantGrp = !$wantSa && !empty($p['g']);   // " + TAG + " — masuk dari Dashboard Grup (akun terpetakan, peran apa pun)\n", what='wantSa')
    s = rep(s, "        if (!in_array($role, ['super_admin', 'admin'], true)) { deiLoginLog($uname, false, 'sso', 'not_admin'",
               "        if (!$wantGrp && !in_array($role, ['super_admin', 'admin'], true)) { deiLoginLog($uname, false, 'sso', 'not_admin'", what='not_admin')
    s = rep(s, "        deiLoginLog($uname, true, 'sso', '', ['name' => $found['name'] ?? $uname, 'role' => $role] + (!empty($found['internal']) ? ['in' => 1] : []));\n",
               "        deiLoginLog($uname, true, $wantGrp ? 'sso_grup' : 'sso', '', ['name' => $found['name'] ?? $uname, 'role' => $role] + (!empty($found['internal']) ? ['in' => 1] : [])\n"
               "            + ($wantGrp ? ['grp' => mb_substr((string)($p['name'] ?? ''), 0, 60)] : []));   // " + TAG + "\n", what='sso log')
    old = "define('DEI_VERSION', 'v1.2.184');   //"
    i = s.index(old)
    s = s[:i] + "define('DEI_VERSION', 'v1.2.185');   // " + TAG + " — Dashboard Grup: laporan gabungan & masuk dari grup; v1.2.184:" + s[i + len(old):]
    save(API, s)

AJ = T + '/dashboard/chatbot-ai/app.js'; s = rd(AJ)
if TAG in s: print('sudah:', AJ)
else:
    s = rep(s, "  var LL_METHOD = { password: 'Password', sso: 'Tautan dari Pusat' };\n",
               "  var LL_METHOD = { password: 'Password', sso: 'Tautan dari Pusat', sso_grup: 'Dashboard Grup' };   // " + TAG + "\n", what='LL_METHOD')
    save(AJ, s)

IH = T + '/dashboard/chatbot-ai/index.html'; s = rd(IH)
if TAG in s: print('sudah:', IH)
else:
    s = rep(s, '<script src="app.js?v=1.2.181"></script>', '<script src="app.js?v=1.2.185"></script><!-- ' + TAG + ' -->', what='cache-buster')
    save(IH, s)

# ---------- pusat ----------
GL = P + '/backend/group-lib.php'
if os.path.exists(GL) and rd(GL) == rd(D + '/group-lib.php'): print('sudah:', GL)
else: save(GL, rd(D + '/group-lib.php'))

PB = P + '/backend/index.php'; s = rd(PB)
if TAG in s: print('sudah:', PB)
else:
    s = rep(s, "require_once __DIR__ . '/update-push-lib.php';   // v1.2.174: update-dari-pusat\n",
               "require_once __DIR__ . '/update-push-lib.php';   // v1.2.174: update-dari-pusat\n"
               "require_once __DIR__ . '/group-lib.php';   // " + TAG + "\n", what='require')
    s = rep(s, " *   - push_update       pasang rilis terbaru ke tenant dari pusat (v1.2.174: update-dari-pusat)\n",
               " *   - push_update       pasang rilis terbaru ke tenant dari pusat (v1.2.174: update-dari-pusat)\n"
               " *   - group_*           kelola Dashboard Grup (" + TAG + ")\n"
               " *\n * Dashboard Grup (/grup/, header X-Grp-Token): grp_login, grp_me, grp_report, grp_sso, grp_forgot, grp_reset*, grp_password\n", what='doc')
    s = rep(s, "    case 'report_back': {\n", rd(D + '/p_cases.php') + "    case 'report_back': {\n", what='case report_back')
    s = rep(s, "header('Access-Control-Allow-Headers: Content-Type, X-Auth-Token, X-Tenant-Id, X-License-Key');",
               "header('Access-Control-Allow-Headers: Content-Type, X-Auth-Token, X-Tenant-Id, X-License-Key, X-Grp-Token');   // " + TAG, what='cors')
    save(PB, s)

AD = P + '/admin/index.html'; s = rd(AD)
if TAG in s: print('sudah:', AD)
else:
    s = rep(s, "  <!-- v1.2.90: Pendaftaran mandiri -->\n", rd(D + '/a_card.html') + "\n  <!-- v1.2.90: Pendaftaran mandiri -->\n", what='admin card')
    s = rep(s, "loadWaReq(); setInterval(loadWaReq, 60000);\n</script>", "loadWaReq(); setInterval(loadWaReq, 60000);\n" + rd(D + '/a_js.js') + "</script>", what='admin js')
    save(AD, s)

GI = P + '/grup/index.html'
if os.path.exists(GI) and rd(GI) == rd(D + '/grup-index.html'): print('sudah:', GI)
else: save(GI, rd(D + '/grup-index.html'))

DS = P + '/dev/deploy.sh'; s = rd(DS)
if 'releases daftar grup' in s: print('sudah:', DS)
else:
    s = rep(s, 'admin backend master releases daftar ', 'admin backend master releases daftar grup ', n=2, what='deploy chmod')
    save(DS, s); os.chmod(DS, 0o755)
print('selesai', TAG)
