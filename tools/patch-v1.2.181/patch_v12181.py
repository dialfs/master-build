#!/usr/bin/env python3
"""v1.2.181 (kb-simpan-aman): perubahan KB (mis. centang "Kirim otomatis") tidak hilang diam-diam.
1. Centang "Kirim otomatis tanpa diminta" langsung tersimpan (tidak perlu klik Simpan).
2. Membuka ulang tab Knowledge Base tidak lagi menimpa perubahan yang belum disimpan.
3. Peringatan browser saat menutup/refresh halaman dengan perubahan KB belum disimpan.
4. Revisi KB (rev): save_kb menolak bila KB sudah diubah dari tab/perangkat lain sejak dimuat
   (dulu: tab lama menimpa diam-diam -> centang/foto/entri baru di tab lain hilang).
Idempoten.  Pakai: patch_v12181.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
T = H + '/dei-tenant'
API = T + '/api/index.php'; APP = T + '/dashboard/chatbot-ai/app.js'; IDX = T + '/dashboard/chatbot-ai/index.html'
TAG = 'v1.2.181: kb-simpan-aman'; NEED = 'v1.2.180: sesi-per-tenant'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    assert NEED in s, 'jalankan patch v1.2.180 dulu: ' + p
    if not NOBAK: shutil.copy2(p, p + '.bak-v12181-' + stamp)
    wr(p, fn(s)); print('OK', p)
C = '   // ' + TAG

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.180');   //", "define('DEI_VERSION', 'v1.2.181');   // " + TAG + " — centang KB langsung tersimpan, tab lama tidak menimpa KB; v1.2.180:", 'versi')
    s = rep(s, "        jsonOut(['ok' => true, 'kb' => readJson(KB_FILE, [])]);\n",
               "        jsonOut(['ok' => true, 'kb' => readJson(KB_FILE, []), 'rev' => deiKbRev()]);" + C + "\n", 'get_kb')
    s = rep(s, "        $kb = is_array($in['kb'] ?? null) ? $in['kb'] : [];\n        // sanitize entries\n",
               "        $kb = is_array($in['kb'] ?? null) ? $in['kb'] : [];\n"
               "        if (isset($in['rev']) && (string)$in['rev'] !== '' && empty($in['force']) && (string)$in['rev'] !== deiKbRev()) {" + C + "\n"
               "            jsonOut(['ok' => false, 'conflict' => true, 'error' => 'Knowledge Base sudah diubah dari tab atau perangkat lain sejak halaman ini dimuat. Muat ulang dulu supaya perubahan itu tidak tertimpa.']);\n"
               "        }\n"
               "        // sanitize entries\n", 'save_kb rev')
    s = rep(s, "        } catch (\\Throwable $e) {}\n        jsonOut(['ok' => true, 'count' => count($clean)]);\n",
               "        } catch (\\Throwable $e) {}\n        jsonOut(['ok' => true, 'count' => count($clean), 'rev' => deiKbRev()]);" + C + "\n", 'save_kb out')
    s = rep(s, "function deiKbFotoPrompt($auto = false) {",
               "function deiKbRev() { clearstatcache(true, KB_FILE); return is_file(KB_FILE) ? (string)md5_file(KB_FILE) : '';" + C + " — sidik KB untuk cegah tab lama menimpa\n}\n"
               "function deiKbFotoPrompt($auto = false) {", 'rev fn')
    return s

def app(s):
    s = rep(s, "  var kbData = [];\n  function loadKb() {\n    ensureCategories(function () {   // v1.2.13: kategori dulu supaya dropdown topik lengkap\n      renderCatManager();\n      api('get_kb').then(function (res) { if (res.ok) { kbData = res.kb || []; renderKb(); } });\n",
               "  var kbData = [], kbRev = '';" + C + "\n"
               "  window.addEventListener('beforeunload', function (ev) { if (kbDirty) { ev.preventDefault(); ev.returnValue = ''; } });" + C + ": peringatan perubahan KB belum disimpan\n"
               "  function loadKb() {\n    ensureCategories(function () {   // v1.2.13: kategori dulu supaya dropdown topik lengkap\n      renderCatManager();\n"
               "      if (kbDirty && kbData.length) { renderKb(); return; }" + C + ": buka ulang tab KB tidak menimpa perubahan yang belum disimpan\n"
               "      api('get_kb').then(function (res) { if (res.ok) { kbData = res.kb || []; kbRev = res.rev || ''; renderKb(); } });\n", 'loadKb')
    s = rep(s, "api('get_kb').then(function (k) { if (k.ok) { kbData = k.kb || []; renderKb(); } });",
               "api('get_kb').then(function (k) { if (k.ok) { kbData = k.kb || []; kbRev = k.rev || ''; kbDirty = false; kbSaveUi(); renderKb(); } });" + C, 'reload', 2)
    s = rep(s, "    if (kbFa) kbFa.onchange = function () { kbData[si].foto_auto = kbFa.checked; kbMarkDirty(); renderKb(); };",
               "    if (kbFa) kbFa.onchange = function () { kbData[si].foto_auto = kbFa.checked; kbMarkDirty(); renderKb(); saveKb(); };" + C + ": centang langsung tersimpan", 'centang')
    s = rep(s, "  function saveKb() {\n    api('save_kb', { method: 'POST', body: { kb: kbData } }).then(function (res) {\n      if (res.ok) { kbDirty = false;",
               "  function saveKb(force) {" + C + "\n    api('save_kb', { method: 'POST', body: { kb: kbData, rev: kbRev, force: force === true } }).then(function (res) {\n"
               "      if (res && res.conflict) {" + C + "\n"
               "        if (confirm(res.error + '\\n\\nOK = muat ulang (perubahan di halaman ini dibuang)\\nBatal = tetap simpan versi halaman ini (menimpa perubahan dari tab/perangkat lain)')) {\n"
               "          api('get_kb').then(function (k) { if (k.ok) { kbData = k.kb || []; kbRev = k.rev || ''; kbDirty = false; kbSaveUi(); renderKb(); toast('Knowledge Base dimuat ulang.'); } });\n"
               "        } else saveKb(true);\n"
               "        return;\n"
               "      }\n"
               "      if (res.ok) { kbRev = res.rev || kbRev; kbDirty = false;", 'saveKb')
    return s

def idx(s):
    return rep(s, '<script src="app.js?v=1.2.180"></script><!-- v1.2.180: sesi-per-tenant -->', '<script src="app.js?v=1.2.181"></script><!-- ' + TAG + ' --><!-- v1.2.180: sesi-per-tenant -->', 'idx')

patch(API, api); patch(APP, app); patch(IDX, idx)
