#!/usr/bin/env python3
"""v1.2.189: mitra-masuk — admin pusat bisa masuk ke Portal Mitra milik mitra mana pun. Patch KHUSUS PUSAT, di atas v1.2.188b.

  python3 patch_pusat_v12189.py <root dei-pusat>

- backend/partner-portal-lib.php + mitra/index.html diperbarui (token admin, mode admin)
- backend/index.php: action partner_portal_as; mitra_me membawa admin_view; mitra_password menolak sesi admin
- admin/index.html: tombol "Masuk" di daftar mitra dan di Detail
Idempoten (penanda "v1.2.189: mitra-masuk"); backup *.bak-v12189-<waktu>.
"""
import os, shutil, sys, time

MARK = 'v1.2.189: mitra-masuk'
NEED = 'v1.2.188b: mitra-duitku'
STAMP = time.strftime('%Y%m%d-%H%M%S')
HERE = os.path.dirname(os.path.abspath(__file__))


def die(msg):
    print('GAGAL: ' + msg)
    sys.exit(1)


def rep(s, old, new, path):
    if s.count(old) != 1:
        die('jangkar tidak cocok di %s (%d): %r' % (path, s.count(old), old[:90]))
    return s.replace(old, new)


def patch(root, rel, fn):
    path = os.path.join(root, rel)
    with open(path, encoding='utf-8') as f:
        s = f.read()
    if MARK in s:
        print('lewati (sudah dipatch): ' + rel)
        return
    if NEED not in s:
        die(rel + ' belum dipatch v1.2.188b (jalankan patch_pusat_v12188b.py dulu)')
    out = fn(s, rel)
    shutil.copy2(path, path + '.bak-v12189-' + STAMP)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(out)
    print('dipatch: ' + rel)


def put(root, src, rel):
    a = os.path.join(HERE, src); b = os.path.join(root, rel)
    if not os.path.isfile(a) or not os.path.isfile(b):
        die('tidak ada: ' + src + ' atau ' + rel)
    if open(a, 'rb').read() == open(b, 'rb').read():
        print('lewati (sama): ' + rel)
        return
    shutil.copy2(b, b + '.bak-v12189-' + STAMP)
    shutil.copy2(a, b)
    print('disalin: ' + rel)


PHP_AS = r'''    case 'partner_portal_as': {   // v1.2.189: mitra-masuk — admin membuka Portal Mitra sebagai mitra ini (hanya lihat, sesi pendek)
        $adm = requireAdmin();
        $m = ptFind((string)(bodyInput()['id'] ?? ''));
        if (!$m) jsonOut(['ok' => false, 'error' => 'Mitra tidak ditemukan.'], 404);
        error_log('partner_portal_as: admin ' . ($adm['username'] ?? '?') . ' membuka portal mitra ' . $m['code'] . ' (' . $m['id'] . ')');
        jsonOut(['ok' => true, 'url' => ptpBaseUrl() . '#as=' . ptpMakeToken((string)$m['id'], null, 'a')]);
    }
'''


def p_index(s, rel):
    a = "        jsonOut(['ok' => true] + ptpView($m, readJson(TENANTS_FILE, [])));"
    s = rep(s, a, "        jsonOut(['ok' => true] + ptpView($m, readJson(TENANTS_FILE, [])) + ['admin_view' => !empty($m['_admin'])]);", rel)
    a = "        $m = ptpRequire();\n        $in = bodyInput(); $pw = (string)($in['new'] ?? '');\n"
    s = rep(s, a, "        $m = ptpRequire();\n        if (!empty($m['_admin'])) jsonOut(['ok' => false, 'error' => 'Mode admin hanya untuk melihat.'], 403);\n        $in = bodyInput(); $pw = (string)($in['new'] ?? '');\n", rel)
    a = "    case 'partner_portal_link': {"
    s = rep(s, a, PHP_AS + a, rel)
    return s


JS_AS = r'''// v1.2.189: mitra-masuk — buka Portal Mitra sebagai mitra ini (tab baru, hanya lihat)
window.ptAs=function(id){
  const w=window.open('about:blank','_blank');
  api('partner_portal_as',{method:'POST',body:{id}}).then(r=>{
    if(!r.ok){ if(w) w.close(); toast(r.error||'Gagal.',true); return; }
    if(w) w.location.href=r.url; else location.href=r.url;
  });
};
'''


def p_admin(s, rel):
    a = """<button class="ghost" onclick="ptDetail('${esc(p.id)}')">Detail</button> <button class="ghost" onclick="ptEdit('${esc(p.id)}')">Ubah</button></td></tr>`"""
    s = rep(s, a, a[:-11] + """ <button class="ghost" onclick="ptAs('${esc(p.id)}')" title="Buka Portal Mitra sebagai mitra ini (hanya lihat)">Masuk</button></td></tr>`""", rel)
    a = """<button class="ghost" onclick="closeModal()">Tutup</button><button onclick="ptPayout("""
    s = rep(s, a, """<button class="ghost" onclick="ptAs('${esc(p.id)}')" title="Buka Portal Mitra sebagai mitra ini (hanya lihat)">Masuk sebagai mitra</button>""" + a, rel)
    a = "ptLoad();\n</script>"
    s = rep(s, a, JS_AS + a, rel)
    return s


def main():
    if len(sys.argv) != 2:
        die('pakai: python3 patch_pusat_v12189.py <root dei-pusat>')
    root = os.path.abspath(sys.argv[1])
    put(root, 'partner-portal-lib.php', 'backend/partner-portal-lib.php')
    put(root, 'mitra-index.html', 'mitra/index.html')
    patch(root, 'backend/index.php', p_index)
    patch(root, 'admin/index.html', p_admin)
    print('SELESAI v1.2.189 mitra-masuk')


if __name__ == '__main__':
    main()
