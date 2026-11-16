#!/usr/bin/env python3
"""v1.2.188: mitra-portal — Portal Mitra (/mitra/). Patch KHUSUS PUSAT, di atas v1.2.187 (mitra).

  python3 patch_pusat_v12188.py <root dei-pusat>

- backend/partner-lib.php diperbarui (email unik, hash password tidak dikirim ke panel)
- backend/partner-portal-lib.php (baru) + mitra/index.html (baru)
- backend/index.php: require, action mitra_* dan partner_portal_link
- admin/index.html: tautan portal di modal mitra
- dev/deploy.sh: folder mitra ikut di-chmod
Idempoten (penanda "v1.2.188: mitra-portal"); backup *.bak-v12188-<waktu> untuk file yang berubah.
"""
import os, shutil, sys, time

MARK = 'v1.2.188: mitra-portal'
NEED = 'v1.2.187: mitra'
STAMP = time.strftime('%Y%m%d-%H%M%S')
HERE = os.path.dirname(os.path.abspath(__file__))


def die(msg):
    print('GAGAL: ' + msg)
    sys.exit(1)


def rep(s, old, new, path, n=1):
    if s.count(old) != n:
        die('jangkar tidak cocok di %s (%d, harus %d): %r' % (path, s.count(old), n, old[:90]))
    return s.replace(old, new)


def patch(root, rel, fn, need=NEED):
    path = os.path.join(root, rel)
    if not os.path.isfile(path):
        die('tidak ada: ' + path)
    with open(path, encoding='utf-8') as f:
        s = f.read()
    if MARK in s:
        print('lewati (sudah dipatch): ' + rel)
        return
    if need and need not in s:
        die(rel + ' belum dipatch v1.2.187 (jalankan patch_pusat_v12187.py dulu)')
    out = fn(s, rel)
    shutil.copy2(path, path + '.bak-v12188-' + STAMP)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(out)
    print('dipatch: ' + rel)


def put(root, src, rel):
    a = os.path.join(HERE, src)
    b = os.path.join(root, rel)
    if not os.path.isfile(a):
        die(src + ' tidak ada di samping skrip ini')
    if os.path.isfile(b) and open(a, 'rb').read() == open(b, 'rb').read():
        print('lewati (sama): ' + rel)
        return
    os.makedirs(os.path.dirname(b), exist_ok=True)
    if os.path.isfile(b):
        shutil.copy2(b, b + '.bak-v12188-' + STAMP)
    shutil.copy2(a, b)
    print('disalin: ' + rel)


PHP_CASES = r'''    /* ---------- v1.2.188: mitra-portal — Portal Mitra (/mitra/, lihat backend/partner-portal-lib.php) ---------- */
    case 'mitra_login': {
        $in = bodyInput();
        $email = grpEmail($in['email'] ?? ''); $pw = (string)($in['password'] ?? '');
        $bad = 'Email atau password salah.';
        if ($email === '' || $pw === '') jsonOut(['ok' => false, 'error' => $bad], 401);
        if (grpRlBlocked('mitra|' . $email)) jsonOut(['ok' => false, 'error' => 'Terlalu banyak percobaan. Coba lagi 15 menit lagi.'], 429);
        $m = ptpFindByEmail($email);
        if (!$m || empty($m['password']) || !password_verify($pw, (string)$m['password'])) { grpRlFail('mitra|' . $email); jsonOut(['ok' => false, 'error' => $bad], 401); }
        if (empty($m['active'])) jsonOut(['ok' => false, 'error' => 'Akun mitra Anda dinonaktifkan. Hubungi DEI.'], 403);
        grpRlClear('mitra|' . $email);
        ptpUpdate((string)$m['id'], ['last_login' => wibDate('Y-m-d H:i:s')]);
        jsonOut(['ok' => true, 'token' => ptpMakeToken((string)$m['id'])]);
    }
    case 'mitra_me': {
        $m = ptpRequire();
        jsonOut(['ok' => true] + ptpView($m, readJson(TENANTS_FILE, [])));
    }
    case 'mitra_forgot': {
        $email = grpEmail(bodyInput()['email'] ?? '');
        $msg = 'Bila email terdaftar, tautan reset password sudah dikirim. Cek Inbox/Spam.';
        if ($email === '' || grpRlBlocked('mitra-forgot|' . $email)) jsonOut(['ok' => true, 'message' => $msg]);
        grpRlFail('mitra-forgot|' . $email); grpRlFail('mitra-forgot|' . $email);   // maks 4 permintaan / 15 menit
        $m = ptpFindByEmail($email);
        if ($m && !empty($m['active'])) ptpSendLink($m, false);
        jsonOut(['ok' => true, 'message' => $msg]);
    }
    case 'mitra_reset_check': {
        $pid = ptpResetLookup((string)(bodyInput()['token'] ?? ''), false);
        $m = $pid !== null ? ptFind($pid) : null;
        if (!$m) jsonOut(['ok' => false, 'error' => 'Tautan tidak berlaku atau sudah dipakai. Minta tautan baru.'], 400);
        jsonOut(['ok' => true, 'name' => (string)$m['name'], 'email' => (string)($m['email'] ?? '')]);
    }
    case 'mitra_reset': {
        $in = bodyInput(); $pw = (string)($in['password'] ?? '');
        if (($e = grpPwOk($pw)) !== '') jsonOut(['ok' => false, 'error' => $e], 400);
        $pid = ptpResetLookup((string)($in['token'] ?? ''), true);
        $m = $pid !== null ? ptFind($pid) : null;
        if (!$m) jsonOut(['ok' => false, 'error' => 'Tautan tidak berlaku atau sudah dipakai. Minta tautan baru.'], 400);
        if (empty($m['active'])) jsonOut(['ok' => false, 'error' => 'Akun mitra Anda dinonaktifkan. Hubungi DEI.'], 403);
        if (!ptpUpdate((string)$m['id'], ['password' => password_hash($pw, PASSWORD_DEFAULT), 'pw_changed_at' => time() - 1, 'last_login' => wibDate('Y-m-d H:i:s')])) jsonOut(['ok' => false, 'error' => 'Gagal menyimpan password.'], 500);
        if (!empty($m['email'])) grpRlClear('mitra|' . strtolower((string)$m['email']));
        jsonOut(['ok' => true, 'token' => ptpMakeToken((string)$m['id'])]);
    }
    case 'mitra_password': {
        $m = ptpRequire();
        $in = bodyInput(); $pw = (string)($in['new'] ?? '');
        if (!password_verify((string)($in['old'] ?? ''), (string)($m['password'] ?? ''))) jsonOut(['ok' => false, 'error' => 'Password lama salah.'], 400);
        if (($e = grpPwOk($pw)) !== '') jsonOut(['ok' => false, 'error' => $e], 400);
        if (!ptpUpdate((string)$m['id'], ['password' => password_hash($pw, PASSWORD_DEFAULT), 'pw_changed_at' => time() - 1])) jsonOut(['ok' => false, 'error' => 'Gagal menyimpan password.'], 500);
        jsonOut(['ok' => true, 'token' => ptpMakeToken((string)$m['id'])]);
    }
    case 'partner_portal_link': {   // admin: tautan buat password portal (email, atau disalin)
        requireAdmin();
        $in = bodyInput();
        $m = ptFind((string)($in['id'] ?? ''));
        if (!$m) jsonOut(['ok' => false, 'error' => 'Mitra tidak ditemukan.'], 404);
        if (trim((string)($m['email'] ?? '')) === '') jsonOut(['ok' => false, 'error' => 'Isi email mitra dulu, lalu simpan.'], 400);
        if (!empty($in['email'])) jsonOut(['ok' => true, 'sent' => ptpSendLink($m, empty($m['password']))]);
        jsonOut(['ok' => true, 'url' => ptpResetLink((string)$m['id'], 3 * 86400)]);
    }

'''


def p_index(s, rel):
    a = "require_once __DIR__ . '/partner-lib.php';   // v1.2.187: mitra\n"
    s = rep(s, a, a + "require_once __DIR__ . '/partner-portal-lib.php';   // v1.2.188: mitra-portal\n", rel)
    a = "        jsonOut(['ok' => true, 'partner' => $res]);"
    s = rep(s, a, "        jsonOut(['ok' => true, 'partner' => ptPublic($res)]);", rel)
    a = "    /* v1.2.138: filter-topik: klasifikasi topik chat WA untuk tenant"
    s = rep(s, a, PHP_CASES + a, rel)
    return s


JS_PORTAL_BLOCK = r'''    ${id?`<div class="hint" style="margin-top:12px"><b>Portal mitra</b> (<a href="../mitra/" target="_blank" rel="noopener">/mitra/</a>): ${p.email?(p.has_password?'sudah punya password'+(p.last_login?', login terakhir '+esc(p.last_login):', belum pernah login'):'belum membuat password')+` · <a href="#" onclick="ptPortal('${esc(p.id)}',1);return false">kirim tautan lewat email</a> · <a href="#" onclick="ptPortal('${esc(p.id)}',0);return false">salin tautan</a>`:'isi email mitra lalu simpan untuk memberi akses.'}</div>`:'<div class="hint" style="margin-top:12px">Setelah disimpan, buka <b>Ubah</b> untuk mengirim tautan akses Portal Mitra ke emailnya.</div>'}
'''

JS_PORTAL_FN = r'''// v1.2.188: mitra-portal — tautan buat password Portal Mitra
window.ptPortal=function(id,email){
  api('partner_portal_link',{method:'POST',body:{id,email:email?1:0}}).then(r=>{
    if(!r.ok){ toast(r.error||'Gagal.',true); return; }
    if(email){ toast(r.sent?'Email tautan terkirim.':'Email gagal terkirim — pakai "salin tautan".',!r.sent); return; }
    (navigator.clipboard?navigator.clipboard.writeText(r.url):Promise.reject()).then(()=>toast('Tautan disalin (berlaku 3 hari, sekali pakai).'),()=>prompt('Salin tautan ini:',r.url));
  });
};
'''


def p_admin(s, rel):
    a = '    <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="pt_active"'
    s = rep(s, a, JS_PORTAL_BLOCK + a, rel)
    a = '<label>Email</label><input id="pt_email"'
    s = rep(s, a, '<label>Email (dipakai mitra untuk login Portal Mitra)</label><input id="pt_email"', rel)
    a = "ptLoad();\n</script>"
    s = rep(s, a, JS_PORTAL_FN + a, rel)
    a = "Tautan pendaftaran: <code>${esc(r.signup_url||'')}?ref=KODE</code>"
    s = rep(s, a, a + ' · Portal mitra: <a href="../mitra/" target="_blank" rel="noopener">/mitra/</a>', rel)
    return s


def p_deploy(s, rel):
    return rep(s, 'releases daftar grup -type', 'releases daftar grup mitra -type', rel, 2).replace(
        '\n', '\n# ' + MARK + ' — folder mitra ikut di-chmod\n', 1)


def main():
    if len(sys.argv) != 2:
        die('pakai: python3 patch_pusat_v12188.py <root dei-pusat>')
    root = os.path.abspath(sys.argv[1])
    if not os.path.isfile(os.path.join(root, 'backend', 'partner-lib.php')):
        die('backend/partner-lib.php belum ada (jalankan patch_pusat_v12187.py dulu): ' + root)
    put(root, 'partner-lib.php', 'backend/partner-lib.php')
    put(root, 'partner-portal-lib.php', 'backend/partner-portal-lib.php')
    put(root, 'mitra-index.html', 'mitra/index.html')
    patch(root, 'backend/index.php', p_index)
    patch(root, 'admin/index.html', p_admin)
    dep = os.path.join(root, 'dev', 'deploy.sh')
    if os.path.isfile(dep):
        patch(root, 'dev/deploy.sh', p_deploy, need='')
    print('SELESAI v1.2.188 mitra-portal')


if __name__ == '__main__':
    main()
