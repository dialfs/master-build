#!/usr/bin/env python3
"""v1.2.168 kuota-unit (TENANT): jumlah Unit Bisnis aktif mengikuti paket dari pusat (features.max_business_units).
Tanpa pusat / pusat lama = 10. Unit di atas batas disimpan tapi nonaktif (yang terakhir ditambahkan lebih dulu).
Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HTML = T + '/dashboard/chatbot-ai/index.html'
TAG = 'v1.2.168: kuota-unit'; stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label):
    n = s.count(old); assert n == 1, '%s: anchor %d kali' % (label, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    shutil.copy2(p, p + '.bak-v12168-' + stamp); wr(p, fn(s)); print('OK', p)

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.167');   // v1.2.167:",
               "define('DEI_VERSION', 'v1.2.168');   // " + TAG + " — jumlah unit bisnis ikut paket (Growth 3, Business 5, Pro 10); v1.2.167:", 'versi')
    s = rep(s, """define('BU_MAX', 10);
function deiUnitsAll() {
    $d = readJson(BU_FILE, []);
    $out = [];
    foreach ((array)($d['units'] ?? []) as $u) {
        if (is_array($u) && !empty($u['id']) && trim((string)($u['name'] ?? '')) !== '') $out[] = $u;
    }
    return $out;
}""", """define('BU_MAX', 50);   // """ + TAG + """: batas teknis; batas paket dari pusat (features.max_business_units)
if (!defined('DEI_DEFAULT_MAX_UNITS')) define('DEI_DEFAULT_MAX_UNITS', 10);   // tanpa pusat / pusat lama
function deiUnitsLimit() {
    $f = [];
    try { $f = deiFeatures(); } catch (\\Throwable $e) { error_log('deiUnitsLimit: ' . $e->getMessage()); }
    return max(0, min(BU_MAX, (int)($f['max_business_units'] ?? DEI_DEFAULT_MAX_UNITS)));
}
// $all = false: hanya unit aktif (urutan penambahan; yang terakhir nonaktif lebih dulu bila paket turun).
function deiUnitsAll($all = false) {
    $d = readJson(BU_FILE, []);
    $out = [];
    foreach ((array)($d['units'] ?? []) as $u) {
        if (is_array($u) && !empty($u['id']) && trim((string)($u['name'] ?? '')) !== '') $out[] = $u;
    }
    return $all ? $out : array_slice($out, 0, deiUnitsLimit());
}""", 'units')
    s = rep(s, """        jsonOut(['ok' => true, 'units' => deiUnitsAll(), 'channels' => $chs, 'categories' => array_values($cats),
                 'max' => BU_MAX,""", """        jsonOut(['ok' => true, 'units' => deiUnitsAll(true), 'channels' => $chs, 'categories' => array_values($cats),
                 'max' => deiUnitsLimit(), 'tier' => (string)(deiFeatures()['tier'] ?? ''), /* """ + TAG + """ */""", 'get_units')
    s = rep(s, """        $used = []; $ids = []; $out = [];
        foreach ((array)($in['units'] ?? []) as $u) {""", """        $used = []; $ids = []; $out = [];
        $buLim = deiUnitsLimit(); $buCap = min(BU_MAX, max($buLim, count(deiUnitsAll(true))));   // """ + TAG + """: unit lama di atas paket tetap boleh disimpan, tambah baru tidak
        $buNew = 0; foreach ((array)($in['units'] ?? []) as $u) { if (is_array($u) && trim((string)($u['name'] ?? '')) !== '') $buNew++; }
        if ($buNew > $buCap) jsonOut(['ok' => false, 'error' => $buLim > 0 ? 'Paket Anda maksimal ' . $buLim . ' unit bisnis. Hubungi DEI untuk upgrade.' : 'Unit Bisnis tersedia mulai paket Growth. Hubungi DEI untuk upgrade.'], 400);
        foreach ((array)($in['units'] ?? []) as $u) {""", 'save1')
    s = rep(s, "            if (count($out) >= BU_MAX) break;\n        }\n        writeJson(BU_FILE,",
               "            if (count($out) >= $buCap) break;\n        }\n        writeJson(BU_FILE,", 'save2')
    s = rep(s, "        'max_wa_numbers'  => max(0, (int)($cap['max_wa_numbers'] ?? DEI_DEFAULT_MAX_WA_NUMBERS)),   // v1.2.99: lisensi-nomor\n        'trial'",
               "        'max_wa_numbers'  => max(0, (int)($cap['max_wa_numbers'] ?? DEI_DEFAULT_MAX_WA_NUMBERS)),   // v1.2.99: lisensi-nomor\n"
               "        'max_business_units' => max(0, (int)($cap['max_business_units'] ?? DEI_DEFAULT_MAX_UNITS)),   // " + TAG + "\n"
               "        'tier'            => strtolower((string)($cap['tier'] ?? '')),\n        'trial'", 'features')
    s = rep(s, "            'wa_numbers' => $wn, 'max_wa_numbers' => (int)($f['max_wa_numbers'] ?? DEI_DEFAULT_MAX_WA_NUMBERS),   // v1.2.99",
               "            'wa_numbers' => $wn, 'max_wa_numbers' => (int)($f['max_wa_numbers'] ?? DEI_DEFAULT_MAX_WA_NUMBERS),   // v1.2.99\n"
               "            'business_units' => count((array)(readJson(BU_FILE, [])['units'] ?? [])), 'max_business_units' => (int)($f['max_business_units'] ?? DEI_DEFAULT_MAX_UNITS),   // " + TAG, 'stats')
    return s

def js(s):
    s = rep(s, "buMax = res.max || 10; buDirty = false;", "buMax = res.max != null ? +res.max : 10; buDirty = false;   /* " + TAG + " */", 'max')
    s = rep(s, "      if (m) m.textContent = res.updated_at ? ('Diperbarui ' + res.updated_at.slice(0, 16) + (res.updated_by ? ' oleh ' + res.updated_by : '')) : '';",
               "      if (m) m.textContent = 'Kuota paket: ' + buData.length + '/' + buMax + ' unit' + (res.updated_at ? (' · Diperbarui ' + res.updated_at.slice(0, 16) + (res.updated_by ? ' oleh ' + res.updated_by : '')) : '');", 'meta')
    s = rep(s, "      if (buData.length >= buMax) { toast('Maksimal ' + buMax + ' unit.', true); return; }",
               "      if (buData.length >= buMax) { toast(buMax ? 'Paket Anda maksimal ' + buMax + ' unit bisnis. Hubungi DEI untuk upgrade.' : 'Unit Bisnis tersedia mulai paket Growth (3 unit), Business (5), Pro (10).', true); return; }", 'add')
    s = rep(s, """    if (!buData.length) {
      wrap.innerHTML = '<div class="card kb-empty\"""", """    if (ba) ba.style.display = (!buMax && !buData.length) ? 'none' : '';   // """ + TAG + """
    if (!buMax && !buData.length) {
      wrap.innerHTML = '<div class="card kb-empty" style="padding:40px 20px;text-align:center">Unit Bisnis belum termasuk paket Anda.<br>Tersedia mulai paket <b>Growth</b> (3 unit), <b>Business</b> (5 unit), dan <b>Pro</b> (10 unit). Hubungi tim DEI untuk upgrade.</div>';
      return;
    }
    if (!buData.length) {
      wrap.innerHTML = '<div class="card kb-empty\"""", 'empty')
    s = rep(s, """      return '<div class="card bu-card">' +
        '<h3>' + ico('layers', 16) + ' ' + (esc(u.name) || '<i style="color:var(--muted)">Unit baru</i>') + '</h3>' +""",
               """      var off = i >= buMax;   // """ + TAG + """
      return '<div class="card bu-card"' + (off ? ' style="opacity:.6"' : '') + '>' +
        '<h3>' + ico('layers', 16) + ' ' + (esc(u.name) || '<i style="color:var(--muted)">Unit baru</i>') +
          (off ? ' <span style="font-size:12px;font-weight:600;color:#b45309;background:#fef3c7;border-radius:6px;padding:2px 8px">Nonaktif: di luar kuota paket (' + buMax + ' unit)</span>' : '') + '</h3>' +""", 'card')
    s = rep(s, "      var us = res.units || [], cur = sel.value;", "      var us = (res.units || []).slice(0, res.max != null ? +res.max : 10), cur = sel.value;   // " + TAG, 'test')
    return s

def html(s):
    return rep(s, '<script src="app.js?v=1.2.167"></script><!-- v1.2.167: unit-bisnis -->',
                  '<script src="app.js?v=1.2.168"></script><!-- ' + TAG + ' --><!-- v1.2.167: unit-bisnis -->', 'html')

patch(API, api); patch(JS, js); patch(HTML, html)
