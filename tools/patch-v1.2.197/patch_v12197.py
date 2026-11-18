#!/usr/bin/env python3
"""v1.2.197 (kode-terlindung): perlindungan kode tenant.
- api/index.php: blok bertanda di root .htaccess tenant (ditulis otomatis, diulang tiap cron_tick bila hilang)
  yang menolak unduhan berkas cadangan/arsip/catatan (.bak*, .zip, .tar.gz, .md, .log, .sh, .py, .sql, .git, composer.*).
- .htaccess (paket master/instalasi baru) membawa blok yang sama.
- app.js & chat-widget.js dikirim dalam bentuk minified (dikerjakan build_v12197.py, sumber lokal tetap utuh).
Butuh v1.2.196. Idempoten.  Pakai: patch_v12197.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
T = H + '/dei-tenant'
TAG = 'v1.2.197: kode-terlindung'; NEED = 'v1.2.196: tombol-bantuan'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12197-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)

MARK_A = '# DEI-HARDEN-START v1.2.197 (otomatis - jangan diedit)'
MARK_B = '# DEI-HARDEN-END'
BODY = r'''<FilesMatch "\.(bak|orig)([-._]|$)|\.(zip|tar|gz|tgz|rar|7z|sql|log|md|sh|py|command)$|^(error_log|composer\.json|composer\.lock)$">
  <IfModule mod_authz_core.c>
    Require all denied
  </IfModule>
  <IfModule !mod_authz_core.c>
    Order deny,allow
    Deny from all
  </IfModule>
</FilesMatch>
RedirectMatch 403 (^|/)\.git(/|$)
'''
BLOCK = MARK_A + '\n' + BODY + MARK_B + '\n'

API = T + '/api/index.php'; s = rd(API)
if TAG in s: print('sudah:', API)
else:
    assert NEED in s, 'butuh v1.2.196'
    s = rep(s, "define('DEI_VERSION', 'v1.2.196');   // ", "define('DEI_VERSION', 'v1.2.197');   // " + TAG + " — blokir unduhan berkas cadangan/arsip di folder tenant, JS dikirim minified; ", what='DEI_VERSION')
    php_body = BODY.replace('\\', '\\\\').replace("'", "\\'")
    a = "function deiSyncBlock($st) {\n"
    s = rep(s, a, """/* """ + TAG + """ — blok bertanda di root .htaccess: berkas cadangan (.bak*), arsip (.zip/.tar.gz),
 * catatan (.md/.log), skrip (.sh/.py/.sql), .git dan composer.* tidak bisa diunduh lewat web.
 * Ditulis sekali (penanda HT_HARDEN_FLAG) dan diperiksa ulang tiap cron_tick. Data & media sudah aman di data/. */
define('HT_HARDEN_MARK_A', '""" + MARK_A + """');
define('HT_HARDEN_MARK_B', '""" + MARK_B + """');
define('HT_HARDEN_FLAG', DATA_DIR . '/.ht-harden-v1');
function deiHtaccessHarden() {
    $p = dirname(__DIR__) . '/.htaccess';
    $s = is_file($p) ? (string)@file_get_contents($p) : '';
    if (strpos($s, HT_HARDEN_MARK_A) !== false) return true;
    if (is_file($p) && $s === '') return false;   // gagal baca: jangan menimpa
    $blk = HT_HARDEN_MARK_A . "\\n" . '""" + php_body + """' . HT_HARDEN_MARK_B . "\\n";
    $out = $s === '' ? $blk : rtrim($s, "\\r\\n") . "\\n\\n" . $blk;
    $perm = is_file($p) ? (@fileperms($p) & 0777) : 0;
    if ($perm && !is_writable($p)) @chmod($p, 0644);
    $ok = @file_put_contents($p, $out, LOCK_EX) !== false;
    if ($perm && !($perm & 0200)) @chmod($p, $perm);
    return $ok;
}
""" + a, what='deiSyncBlock')
    a = "/* Penjaga: tenant diblokir -> semua request ditolak 403 (kecuali pusat yang sah). */\n"
    s = rep(s, a, "if (PHP_SAPI !== 'cli' && !is_file(HT_HARDEN_FLAG) && deiHtaccessHarden()) @file_put_contents(HT_HARDEN_FLAG, gmdate('c'));   // " + TAG + "\n\n" + a, what='penjaga')
    a = "    case 'cron_tick': {\n        $s = getSettings();\n"
    s = rep(s, a, a + "        if (!is_file(LIC_BLOCK_FLAG) && deiHtaccessHarden() && !is_file(HT_HARDEN_FLAG)) @file_put_contents(HT_HARDEN_FLAG, gmdate('c'));   // " + TAG + "\n", what='cron_tick')
    save(API, s)

HT = T + '/.htaccess'; s = rd(HT)
if MARK_A in s: print('sudah:', HT)
else: save(HT, s.rstrip('\r\n') + '\n\n' + BLOCK)
print('selesai', TAG)
