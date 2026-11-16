#!/usr/bin/env python3
"""v1.2.188b: mitra-duitku — komisi mitra hanya dari pembayaran lewat Duitku. Patch KHUSUS PUSAT, di atas v1.2.188.

  python3 patch_pusat_v12188b.py <root dei-pusat>

- backend/index.php: action partner_manual dihapus
- admin/index.html: form "Catat pembayaran manual" dihapus; tenant yang tagihannya manual diberi tanda
- backend/partner-lib.php: ptTenantRow membawa `duitku`
Idempoten (penanda "v1.2.188b: mitra-duitku"); backup *.bak-v12188b-<waktu>.
"""
import os, shutil, sys, time

MARK = 'v1.2.188b: mitra-duitku'
NEED = 'v1.2.188: mitra-portal'
STAMP = time.strftime('%Y%m%d-%H%M%S')
HERE = os.path.dirname(os.path.abspath(__file__))


def die(msg):
    print('GAGAL: ' + msg)
    sys.exit(1)


def rep(s, old, new, path):
    if s.count(old) != 1:
        die('jangkar tidak cocok di %s (%d): %r' % (path, s.count(old), old[:90]))
    return s.replace(old, new)


def cut(s, start, end, new, path):
    """Ganti teks dari `start` sampai tepat sebelum `end`."""
    if s.count(start) != 1 or s.count(end) != 1:
        die('jangkar potong tidak cocok di %s: %r / %r' % (path, start[:60], end[:60]))
    a = s.index(start); b = s.index(end)
    if b <= a:
        die('urutan jangkar salah di ' + path)
    return s[:a] + new + s[b:]


def patch(root, rel, fn):
    path = os.path.join(root, rel)
    with open(path, encoding='utf-8') as f:
        s = f.read()
    if MARK in s:
        print('lewati (sudah dipatch): ' + rel)
        return
    if NEED not in s:
        die(rel + ' belum dipatch v1.2.188 (jalankan patch_pusat_v12188.py dulu)')
    out = fn(s, rel)
    shutil.copy2(path, path + '.bak-v12188b-' + STAMP)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(out)
    print('dipatch: ' + rel)


def p_index(s, rel):
    return cut(s, "    case 'partner_manual': {", "    case 'partner_void': {",
               "    // v1.2.188b: mitra-duitku — tidak ada pencatatan pembayaran manual: komisi hanya dari pesanan Duitku yang lunas\n", rel)


def p_admin(s, rel):
    s = cut(s, '      <details style="margin-top:14px"><summary style="cursor:pointer;font-weight:600">Catat pembayaran manual',
            "      </div><div class=\"actions\"><button class=\"ghost\" style=\"margin-right:auto\" onclick=\"ptSync(",
            '      <div class="hint" style="margin-top:12px">Komisi hanya dari pembayaran lewat Duitku (halaman /bayar/). Pembayaran transfer atau invoice di luar Duitku tidak menghasilkan komisi.</div>\n', rel)
    s = cut(s, "window.ptManual=function(pid){", "window.ptVoid=function(id){", "// " + MARK + " — form pembayaran manual dihapus\n", rel)
    a = "Komisi tercatat otomatis saat pesanan Duitku lunas; pembayaran transfer/invoice dicatat lewat <b>Detail › Catat pembayaran manual</b>."
    s = rep(s, a, "Komisi <b>hanya dari pembayaran lewat Duitku</b> (halaman /bayar/), tercatat otomatis saat pesanan lunas; transfer atau invoice di luar Duitku tidak menghasilkan komisi.", rel)
    a = "(t.tier==='trial'?'<span class=\"badge idle\">trial</span>':'<span class=\"badge off\">tidak aktif</span>')}</td>"
    s = rep(s, a, a[:-5] + "${t.duitku===false?' <span class=\"badge off\" title=\"Tenant ini ditagih manual, jadi tidak bisa membayar lewat Duitku dan tidak menghasilkan komisi. Beri tanggal masa aktif (expires_at) atau aktifkan bayar mandiri supaya bisa lewat /bayar/.\">tagihan manual</span>':''}</td>", rel)
    return s


def main():
    if len(sys.argv) != 2:
        die('pakai: python3 patch_pusat_v12188b.py <root dei-pusat>')
    root = os.path.abspath(sys.argv[1])
    src = os.path.join(HERE, 'partner-lib.php'); dst = os.path.join(root, 'backend', 'partner-lib.php')
    if not os.path.isfile(src) or not os.path.isfile(dst):
        die('partner-lib.php tidak ada (di samping skrip atau di backend/)')
    if open(src, 'rb').read() != open(dst, 'rb').read():
        shutil.copy2(dst, dst + '.bak-v12188b-' + STAMP); shutil.copy2(src, dst); print('disalin: backend/partner-lib.php')
    else:
        print('lewati (sama): backend/partner-lib.php')
    patch(root, 'backend/index.php', p_index)
    patch(root, 'admin/index.html', p_admin)
    print('SELESAI v1.2.188b mitra-duitku')


if __name__ == '__main__':
    main()
