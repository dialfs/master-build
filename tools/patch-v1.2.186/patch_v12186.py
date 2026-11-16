#!/usr/bin/env python3
"""v1.2.186 (grup-inbox): Dashboard Grup tahap 2 — inbox gabungan (baca, balas teks/file, Selesai) semua tenant grup.
Tenant (paket: api/index.php):
- action grp_as: pusat (X-Tenant-Id + X-License-Key) menjalankan wa_conversations_v2 / wa_thread / wa_send_manual /
  wa_send_media / wa_resolve / wa_media atas nama akun tenant terpetakan (X-Dei-Grp-User); requireAuth memakai akun itu.
Pusat:
- backend/group-lib.php: grpAsCall, grpInboxTenants, token media lewat query; backend/index.php: grp_inbox, grp_thread,
  grp_send, grp_send_media, grp_resolve, grp_media. grup/index.html: tab Inbox.
Idempoten.  Pakai: patch_v12186.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
D = os.path.dirname(os.path.abspath(__file__))
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
T = H + '/dei-tenant'; P = H + '/dei-pusat'
TAG = 'v1.2.186: grup-inbox'; NEED = 'v1.2.185: master-grup'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12186-' + stamp)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)

API = T + '/api/index.php'; s = rd(API)
if TAG in s: print('sudah:', API)
else:
    assert NEED in s, 'butuh v1.2.185'
    s = rep(s, "/* Penjaga: tenant diblokir -> semua request ditolak 403 (kecuali pusat yang sah). */\n",
               rd(D + '/t_pre.php') + "/* Penjaga: tenant diblokir -> semua request ditolak 403 (kecuali pusat yang sah). */\n", what='penjaga')
    s = rep(s, "    $username = tokenUsername(requestToken());\n",
               "    $username = isset($GLOBALS['dei_grp_as']) ? (string)$GLOBALS['dei_grp_as'] : tokenUsername(requestToken());   // " + TAG + "\n", n=2, what='auth')
    old = "define('DEI_VERSION', 'v1.2.185');   //"
    i = s.index(old)
    s = s[:i] + "define('DEI_VERSION', 'v1.2.186');   // " + TAG + " — inbox gabungan Dashboard Grup (baca & balas atas nama akun tenant); v1.2.185:" + s[i + len(old):]
    save(API, s)

GL = P + '/backend/group-lib.php'; s = rd(GL)
if TAG in s: print('sudah:', GL)
else:
    assert NEED in s, 'group-lib v1.2.185 belum ada'
    save(GL, rd(D + '/group-lib.php'))

PB = P + '/backend/index.php'; s = rd(PB)
if TAG in s: print('sudah:', PB)
else:
    assert NEED in s, 'pusat butuh v1.2.185'
    s = rep(s, " * Dashboard Grup (/grup/, header X-Grp-Token): grp_login, grp_me, grp_report, grp_sso, grp_forgot, grp_reset*, grp_password\n",
               " * Dashboard Grup (/grup/, header X-Grp-Token): grp_login, grp_me, grp_report, grp_sso, grp_forgot, grp_reset*, grp_password\n"
               " *   + inbox gabungan (" + TAG + "): grp_inbox, grp_thread, grp_send, grp_send_media, grp_resolve, grp_media\n", what='doc')
    s = rep(s, "    case 'report_back': {\n", rd(D + '/p_cases.php') + "    case 'report_back': {\n", what='case report_back')
    save(PB, s)

GI = P + '/grup/index.html'; s = rd(GI)
if TAG in s: print('sudah:', GI)
else:
    assert NEED in s
    save(GI, rd(D + '/grup-index.html'))
print('selesai', TAG)
