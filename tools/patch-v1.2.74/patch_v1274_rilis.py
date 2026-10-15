#!/usr/bin/env python3
"""v1.2.74 tahap 3 — rilis bertipe "perbaikan" hanya untuk Super Admin.
  * release_notes: untuk selain super_admin, rilis type=perbaikan dibuang SEBELUM latest/unread dihitung
    (daftar, lencana menu, banner, status "Pembaruan tersedia")
  * deiReleaseNotify: push rilis perbaikan hanya ke super_admin
  * UI: filter "Perbaikan" disembunyikan untuk Admin; "Rilis terbaru" tidak lebih rendah dari versi terpasang
Idempoten. Pakai: patch_v1274_rilis.py <root>"""
import sys, pathlib

ROOT = pathlib.Path(sys.argv[1])
F_API = ROOT / 'api/index.php'
F_JS = ROOT / 'dashboard/chatbot-ai/app.js'


def rep(src, old, new, count=1):
    n = src.count(old)
    if n != count:
        raise SystemExit(f'ANCHOR {n}x (harus {count}): {old[:90]!r}')
    return src.replace(old, new)


api = F_API.read_text(encoding='utf-8')
if 'deiRelVisible(' not in api:
    api = rep(api, "function deiReleaseNotify($latest) {", """/* v1.2.74: rilis bertipe "perbaikan" hanya ditampilkan ke Super Admin */
function deiRelVisible($r, $role) {
    return $role === 'super_admin' || (($r['type'] ?? '') !== 'perbaikan');
}

function deiReleaseNotify($latest) {""")
    api = rep(api, """    $title = '';
    foreach (($notes['releases'] ?? []) as $r) {
        if ($r['version'] === $latest) { $title = $r['title'] !== '' ? $r['title'] : mb_substr($r['changelog'], 0, 110); break; }
    }""", """    $title = '';
    $relType = '';
    foreach (($notes['releases'] ?? []) as $r) {
        if ($r['version'] === $latest) { $title = $r['title'] !== '' ? $r['title'] : mb_substr($r['changelog'], 0, 110); $relType = (string)($r['type'] ?? ''); break; }
    }
    $pushRoles = $relType === 'perbaikan' ? ['super_admin'] : ['super_admin', 'admin'];   // v1.2.74""")
    api = rep(api, """in_array(($u['role'] ?? ''), ['super_admin', 'admin'], true) && in_array($un, $subs, true)) $targets[] = $un;""",
              """in_array(($u['role'] ?? ''), $pushRoles, true) && in_array($un, $subs, true)) $targets[] = $un;""")
    api = rep(api, """        $n = deiFetchReleaseNotes(!empty($_GET['refresh']));
        $rel = $n['releases'] ?? [];
        $latest = $rel[0]['version'] ?? null;""", """        $n = deiFetchReleaseNotes(!empty($_GET['refresh']));
        $rel = array_values(array_filter($n['releases'] ?? [], function ($r) use ($u) { return deiRelVisible($r, $u['role'] ?? ''); }));   // v1.2.74
        $latest = $rel[0]['version'] ?? null;""")
    F_API.write_text(api, encoding='utf-8')
    print('api: ok')
else:
    print('api: sudah terpasang')

js = F_JS.read_text(encoding='utf-8')
if 'v1.2.74: perbaikan' not in js:
    js = rep(js, """    $('#relInstalled').textContent = inst || '–';
    $('#relLatest').textContent = d.latest || '–';""", """    $('#relInstalled').textContent = inst || '–';
    // v1.2.74: perbaikan khusus Super Admin — rilis terbaru yang terlihat bisa lebih rendah dari versi terpasang
    $('#relLatest').textContent = (d.latest && inst && relVerCmp(inst, d.latest) > 0) ? inst : (d.latest || '–');""")
    js = rep(js, """    if (!relState.wired) {
      relState.wired = true;""", """    if (!relState.wired) {
      relState.wired = true;
      if (role !== 'super_admin') $$('#relFilters [data-f="perbaikan"]').forEach(function (b) { b.style.display = 'none'; });""")
    js = rep(js, "body: '<p>Catatan rilis fitur baru dan perbaikan. Saat ada versi baru,",
             "body: '<p>Catatan rilis fitur baru dan peningkatan. Saat ada versi baru,")
    F_JS.write_text(js, encoding='utf-8')
    print('js: ok')
else:
    print('js: sudah terpasang')
