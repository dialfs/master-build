#!/usr/bin/env python3
"""v1.2.167 unit-bisnis — satu tenant, beberapa usaha (rental mobil, villa, fashion, ...).
Tiap unit: nama, kanal (nomor WA / widget web), kategori KB, instruksi khusus. Daftar harga bisa ditandai per unit.
Idempoten: backup -> replace anchor -> verifikasi."""
import os, sys, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HTML = T + '/dashboard/chatbot-ai/index.html'
TAG = 'v1.2.167: unit-bisnis'
stamp = time.strftime('%Y%m%d-%H%M%S')

def rd(p): return open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, count=1):
    n = s.count(old)
    assert n == count, '%s: anchor ditemukan %d kali (harus %d)' % (label, n, count)
    return s.replace(old, new)

for p in (API, JS, HTML):
    if TAG in rd(p):
        print('sudah dipatch:', p); continue
    shutil.copy2(p, p + '.bak-v12167-' + stamp)

# ============================== API ==============================
s = rd(API)
if TAG not in s:
    s = rep(s, "define('DEI_VERSION', 'v1.2.166');   // v1.2.166:",
            "define('DEI_VERSION', 'v1.2.167');   // v1.2.167: unit-bisnis — satu tenant beberapa usaha (kanal WA/web, kategori KB, instruksi & harga per unit); v1.2.166:", 'versi')

    FUNCS = r'''/* ============================================================================
 * v1.2.167: unit-bisnis — satu tenant, beberapa usaha (mis. rental mobil, villa, fashion).
 * data/business-units.json = {units:[{id,name,channels[],categories[],instructions}], updated_at, updated_by}
 * Kanal: 'utama' / id nomor WA tambahan / 'web'. Satu kanal hanya milik satu unit.
 * KB yang dikirim ke AI: entri berkategori milik unit + entri yang kategorinya tidak diklaim unit mana pun (umum).
 * Daftar harga: item tanpa unit = umum; item ber-unit hanya dikirim untuk unit itu.
 * Tanpa unit / kanal tidak dipetakan -> perilaku lama (semua KB, semua harga).
 * ========================================================================= */
define('BU_FILE', DATA_DIR . '/business-units.json');
define('BU_MAX', 10);
function deiUnitsAll() {
    $d = readJson(BU_FILE, []);
    $out = [];
    foreach ((array)($d['units'] ?? []) as $u) {
        if (is_array($u) && !empty($u['id']) && trim((string)($u['name'] ?? '')) !== '') $out[] = $u;
    }
    return $out;
}
// $ch: id kanal ('utama', id nomor, 'web') atau '#<id unit>' (Tes Chatbot). '#' saja = tanpa unit.
function deiUnitFor($ch) {
    $ch = (string)$ch;
    if ($ch === '') return null;
    $units = deiUnitsAll();
    if (!$units) return null;
    if ($ch[0] === '#') {
        $id = substr($ch, 1);
        foreach ($units as $u) { if ((string)$u['id'] === $id) return $u; }
        return null;
    }
    foreach ($units as $u) { if (in_array($ch, (array)($u['channels'] ?? []), true)) return $u; }
    return null;
}
function deiUnitCatKey($c) { return mb_strtolower(trim((string)$c)); }
function deiUnitFilterKb($kb, $unit) {
    $mine = []; $claimed = [];
    foreach (deiUnitsAll() as $u) {
        foreach ((array)($u['categories'] ?? []) as $c) {
            $k = deiUnitCatKey($c);
            if ($k === '') continue;
            $claimed[$k] = 1;
            if ((string)$u['id'] === (string)$unit['id']) $mine[$k] = 1;
        }
    }
    return array_values(array_filter((array)$kb, function ($e) use ($mine, $claimed) {
        $k = deiUnitCatKey(is_array($e) ? ($e['category'] ?? '') : '');
        return isset($mine[$k]) || !isset($claimed[$k]);
    }));
}
function deiUnitPromptBlock($unit) {
    $nm = trim((string)$unit['name']);
    $lain = [];
    foreach (deiUnitsAll() as $u) { if ((string)$u['id'] !== (string)$unit['id']) $lain[] = trim((string)$u['name']); }
    $b = "=== UNIT BISNIS: " . $nm . " ===\n"
       . "Percakapan ini masuk lewat kanal khusus " . $nm . ". Fokus pada produk/layanan " . $nm . " dan jawab berdasarkan Knowledge Base yang diberikan.\n";
    if ($lain) {
        $b .= "Usaha lain perusahaan ini (" . implode(', ', $lain) . ") TIDAK dilayani di kanal ini. Jika pelanggan menanyakannya, jawab singkat bahwa kanal ini khusus "
            . $nm . " lalu arahkan sesuai instruksi unit di bawah (jika ada). Jangan memberi harga atau detail usaha lain.\n";
        $b .= "Jika pertanyaan ambigu (mis. 'harga per hari berapa?'), anggap yang dimaksud adalah " . $nm . ".\n";
    }
    $ins = trim((string)($unit['instructions'] ?? ''));
    if ($ins !== '') $b .= "Instruksi khusus unit " . $nm . ":\n" . $ins . "\n";
    return trim($b);
}

'''
    s = rep(s, "function generateAnswer($s, $message, $history = [], $channel = '') {",
            FUNCS + "function generateAnswer($s, $message, $history = [], $channel = '', $unitCh = '') {   // v1.2.167: unit-bisnis ($unitCh)", 'generateAnswer')

    s = rep(s, "    // v1.2.53: aturan bahasa ditempel PALING AKHIR supaya jadi instruksi terakhir\n",
            "    $deiUnit = null;   // v1.2.167: unit-bisnis\n"
            "    try { $deiUnit = deiUnitFor($unitCh); } catch (\\Throwable $e) { error_log('deiUnitFor: ' . $e->getMessage()); }\n"
            "    if ($deiUnit) $persona .= \"\\n\\n\" . deiUnitPromptBlock($deiUnit);\n"
            "    // v1.2.53: aturan bahasa ditempel PALING AKHIR supaya jadi instruksi terakhir\n", 'unit persona')

    s = rep(s, "    $kbAll       = readJson(KB_FILE, []);\n    $kbHitsUsed  = count($kbAll);\n    $deiPriceBlk = pricelistPromptBlock();",
            "    $kbAll       = readJson(KB_FILE, []);\n"
            "    if ($deiUnit) $kbAll = deiUnitFilterKb($kbAll, $deiUnit);   // v1.2.167: unit-bisnis\n"
            "    $kbHitsUsed  = count($kbAll);\n"
            "    $deiPriceBlk = pricelistPromptBlock($deiUnit);   // v1.2.167: unit-bisnis", 'kb filter')

    s = rep(s, "function pricelistPromptBlock() {\n    $pl = pricelistGet();\n    $rows = '';\n    foreach ($pl['items'] as $it) {\n        if (!is_array($it)) continue;\n",
            "function pricelistPromptBlock($unit = null) {   // v1.2.167: unit-bisnis\n    $pl = pricelistGet();\n    $rows = '';\n    foreach ($pl['items'] as $it) {\n        if (!is_array($it)) continue;\n"
            "        $iu = (string)($it['unit'] ?? '');   // v1.2.167: item ber-unit hanya untuk unit itu\n"
            "        if ($iu !== '' && $unit && (string)$unit['id'] !== $iu) continue;   // tanpa unit = semua harga (perilaku lama)\n", 'pricelist block')

    s = rep(s, "                'note'  => mb_substr(trim((string)($it['note'] ?? '')), 0, 200),\n            ];",
            "                'note'  => mb_substr(trim((string)($it['note'] ?? '')), 0, 200),\n"
            "                'unit'  => preg_replace('/[^a-z0-9_]/', '', (string)($it['unit'] ?? '')),   // v1.2.167: unit-bisnis\n            ];", 'save_pricelist')

    s = rep(s, "generateAnswer($s, $text, $history, 'whatsapp');   // v1.2.89",
            "generateAnswer($s, $text, $history, 'whatsapp', (string)($wa['_ch'] ?? 'utama'));   // v1.2.89; v1.2.167: unit-bisnis", 'wa call')

    s = rep(s, "        list($ok, $answer, $kbUsed, $usage) = generateAnswer($s, $message, $history);\n",
            "        $deiUnitCh = 'web';   // v1.2.167: unit-bisnis — Tes Chatbot boleh memilih unit\n"
            "        if (isset($in['unit_test']) && is_string($in['unit_test']) && $in['unit_test'] !== '' && getAuthenticatedUserSilent()) $deiUnitCh = $in['unit_test'];\n"
            "        list($ok, $answer, $kbUsed, $usage) = generateAnswer($s, $message, $history, '', $deiUnitCh);\n", 'web call')

    ACTIONS = r'''    /* ---------- v1.2.167: unit-bisnis ---------- */
    case 'get_units': {
        requireAuth(['super_admin', 'admin']);
        $chs = [];
        foreach (waChannels() as $c) $chs[] = ['id' => (string)$c['id'], 'label' => 'WhatsApp: ' . (string)$c['label'] . ((string)$c['number'] !== '' && strpos((string)$c['label'], (string)$c['number']) === false ? ' (+' . $c['number'] . ')' : '')];
        $chs[] = ['id' => 'web', 'label' => 'Widget website'];
        $cats = [];
        foreach ((array)readJson(KB_FILE, []) as $e) {
            $c = trim((string)(is_array($e) ? ($e['category'] ?? '') : ''));
            if ($c !== '' && !isset($cats[mb_strtolower($c)])) $cats[mb_strtolower($c)] = $c;
        }
        $d = readJson(BU_FILE, []);
        jsonOut(['ok' => true, 'units' => deiUnitsAll(), 'channels' => $chs, 'categories' => array_values($cats),
                 'max' => BU_MAX, 'updated_at' => (string)($d['updated_at'] ?? ''), 'updated_by' => (string)($d['updated_by'] ?? '')]);
        break;
    }
    case 'save_units': {
        $me = requireAuth(['super_admin', 'admin']);
        $in = bodyInput();
        $valid = ['web' => 1];
        foreach (waChannels() as $c) $valid[(string)$c['id']] = 1;
        foreach ((array)(readJson(BU_FILE, [])['units'] ?? []) as $u) {   // kanal nomor yang sedang di luar paket tetap disimpan
            foreach ((array)(is_array($u) ? ($u['channels'] ?? []) : []) as $c) { if (is_string($c) && preg_match('/^[A-Za-z0-9_\-]{1,40}$/', $c)) $valid[$c] = 1; }
        }
        $used = []; $ids = []; $out = [];
        foreach ((array)($in['units'] ?? []) as $u) {
            if (!is_array($u)) continue;
            $nm = mb_substr(trim((string)($u['name'] ?? '')), 0, 60);
            if ($nm === '') continue;
            $id = preg_replace('/[^a-z0-9_]/', '', (string)($u['id'] ?? ''));
            if ($id === '' || isset($ids[$id])) $id = 'u_' . substr(md5(uniqid('', true)), 0, 8);
            $ids[$id] = 1;
            $ch = [];
            foreach ((array)($u['channels'] ?? []) as $c) {
                $c = (string)$c;
                if (!isset($valid[$c]) || isset($used[$c])) continue;   // satu kanal hanya milik satu unit
                $used[$c] = 1; $ch[] = $c;
            }
            $cat = []; $seen = [];
            foreach ((array)($u['categories'] ?? []) as $c) {
                $c = mb_substr(trim((string)$c), 0, 60);
                if ($c === '' || isset($seen[mb_strtolower($c)])) continue;
                $seen[mb_strtolower($c)] = 1; $cat[] = $c;
                if (count($cat) >= 50) break;
            }
            $out[] = ['id' => $id, 'name' => $nm, 'channels' => $ch, 'categories' => $cat,
                      'instructions' => mb_substr(trim((string)($u['instructions'] ?? '')), 0, 2000)];
            if (count($out) >= BU_MAX) break;
        }
        writeJson(BU_FILE, ['units' => $out, 'updated_at' => date('Y-m-d H:i:s'), 'updated_by' => (string)($me['username'] ?? '')]);
        jsonOut(['ok' => true, 'units' => $out]);
        break;
    }

    case 'get_kb': {'''
    s = rep(s, "    case 'get_kb': {", ACTIONS, 'actions')
    wr(API, s)

# ============================== HTML ==============================
h = rd(HTML)
if TAG not in h:
    h = rep(h, '<button class="btn ghost sm kb-tab" data-kbtab="harga"><span data-ico="wallet" data-ico-size="14"></span> Daftar Harga</button>',
            '<button class="btn ghost sm kb-tab" data-kbtab="harga"><span data-ico="wallet" data-ico-size="14"></span> Daftar Harga</button>\n'
            '        <button class="btn ghost sm kb-tab" data-kbtab="unit"><span data-ico="layers" data-ico-size="14"></span> Unit Bisnis</button><!-- v1.2.167: unit-bisnis -->', 'html tab')
    h = rep(h, '      <!-- v1.2.22: DAFTAR HARGA -->',
            '''      <!-- v1.2.167: unit-bisnis -->
      <div id="kbTabUnit" style="display:none">
        <div class="card">
          <div class="toolbar" style="margin-bottom:0;flex-wrap:wrap">
            <button class="btn" id="btnAddUnit">+ Tambah Unit</button>
            <button class="btn ghost" id="btnSaveUnits"><span data-ico="save" data-ico-size="15"></span> Simpan Unit</button>
            <span id="unitMeta" class="help" style="margin-left:auto"></span>
          </div>
          <p style="margin:10px 2px 0;color:var(--muted);font-size:13px;line-height:1.5">
            Untuk tenant yang punya <strong>lebih dari satu usaha</strong> (mis. Rental Mobil, Villa, Fashion).
            Tiap unit melayani kanal tertentu (nomor WA / widget website) dan hanya memakai kategori KB miliknya.
            Kategori yang <strong>tidak dipilih unit mana pun</strong> dianggap umum dan dipakai semua unit (mis. Lokasi, Kontak, Jam Buka).
            Kanal yang tidak masuk unit mana pun tetap memakai seluruh KB seperti biasa.
          </p>
        </div>
        <div id="unitList"></div>
      </div><!-- /kbTabUnit -->

      <!-- v1.2.22: DAFTAR HARGA -->''', 'html panel')
    h = rep(h, '<button class="btn" id="testSend">Kirim</button>',
            '<select id="testUnit" style="display:none;max-width:220px" title="Uji sebagai unit bisnis"></select><!-- v1.2.167: unit-bisnis -->\n'
            '          <button class="btn" id="testSend">Kirim</button>', 'html test')
    h = rep(h, '  .kb-search:empty{display:none}',
            '  .kb-search:empty{display:none}\n'
            '  /* v1.2.167: unit-bisnis */\n'
            '  .bu-card h3{display:flex;align-items:center;gap:8px;margin-top:0}\n'
            '  .bu-chks{display:flex;flex-wrap:wrap;gap:6px 14px}\n'
            '  .bu-chk{display:flex;align-items:center;gap:6px;font-size:13.5px;cursor:pointer}\n'
            '  .bu-chk small{color:var(--muted)}\n'
            '  .bu-chk input{width:auto;margin:0}\n'
            '  .pr-unit-tag{display:inline-block;font-size:11px;background:var(--bg);border-radius:10px;padding:1px 7px;margin-left:6px;color:var(--muted)}', 'html css')
    h = h.replace('<script src="app.js?v=1.2.166"></script>', '<script src="app.js?v=1.2.167"></script><!-- v1.2.167: unit-bisnis -->')
    assert 'app.js?v=1.2.167' in h
    wr(HTML, h)

# ============================== JS ==============================
j = rd(JS)
if TAG not in j:
    j = rep(j, "    'tag':           '<path d=\"M12.6 2.6A2 2 0 0 0 11.2 2H4a2 2 0 0 0-2 2v7.2a2 2 0 0 0 .6 1.4l8.7 8.7a2.4 2.4 0 0 0 3.4 0l6.6-6.6a2.4 2.4 0 0 0 0-3.4z\"/><circle cx=\"7.5\" cy=\"7.5\" r=\".5\" fill=\"currentColor\"/>'   // v1.2.124: wa-layout-penuh",
            "    'tag':           '<path d=\"M12.6 2.6A2 2 0 0 0 11.2 2H4a2 2 0 0 0-2 2v7.2a2 2 0 0 0 .6 1.4l8.7 8.7a2.4 2.4 0 0 0 3.4 0l6.6-6.6a2.4 2.4 0 0 0 0-3.4z\"/><circle cx=\"7.5\" cy=\"7.5\" r=\".5\" fill=\"currentColor\"/>',   // v1.2.124: wa-layout-penuh\n"
            "    'layers':        '<path d=\"m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z\"/><path d=\"m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65\"/><path d=\"m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65\"/>'   // v1.2.167: unit-bisnis", 'icon')

    j = rep(j, "    var entri = document.getElementById('kbTabEntri');\n    var harga = document.getElementById('kbTabHarga');\n"
               "    if (entri) entri.style.display = (which === 'entri') ? '' : 'none';\n    if (harga) harga.style.display = (which === 'harga') ? '' : 'none';\n"
               "    if (which === 'harga' && !priceData.length) fetchPricelist();\n",
            "    var entri = document.getElementById('kbTabEntri');\n    var harga = document.getElementById('kbTabHarga');\n"
            "    if (entri) entri.style.display = (which === 'entri') ? '' : 'none';\n    if (harga) harga.style.display = (which === 'harga') ? '' : 'none';\n"
            "    var unitT = document.getElementById('kbTabUnit');   // v1.2.167: unit-bisnis\n"
            "    if (unitT) unitT.style.display = (which === 'unit') ? '' : 'none';\n"
            "    if (which === 'unit') { if (buData === null || !buDirty) fetchUnits(); else renderUnits(); }\n"
            "    if (which === 'harga' && buData === null) fetchUnits(function () { renderPricelist(); });\n"
            "    if (which === 'harga' && !priceData.length) fetchPricelist();\n", 'switch tab')

    # pricelist: tag di daftar + pilihan unit di editor
    j = rep(j, "        (p.note ? '<small>' + esc(p.note) + '</small>' : '') + '</button>';\n    }).join('') || '<div class=\"kb-empty\">' + (priceData.length ? 'Tidak ada item yang cocok.'",
            "        (p.note ? '<small>' + esc(p.note) + '</small>' : '') + (p.unit && buName(p.unit) ? '<span class=\"pr-unit-tag\">' + esc(buName(p.unit)) + '</span>' : '') + '</button>';   // v1.2.167\n    }).join('') || '<div class=\"kb-empty\">' + (priceData.length ? 'Tidak ada item yang cocok.'", 'pr list tag')
    j = rep(j, "'<div class=\"row\"><label class=\"fl\">Catatan (opsional)</label><textarea class=\"pr-note\" style=\"min-height:120px\" placeholder=\"mis. termasuk sarapan 2 orang\">' + esc(p.note || '') + '</textarea></div>' +",
            "'<div class=\"row\"><label class=\"fl\">Catatan (opsional)</label><textarea class=\"pr-note\" style=\"min-height:120px\" placeholder=\"mis. termasuk sarapan 2 orang\">' + esc(p.note || '') + '</textarea></div>' +\n"
            "        ((buData && buData.length) || p.unit ? '<div class=\"row\"><label class=\"fl\">Unit bisnis</label><select class=\"pr-unit\"><option value=\"\">Umum (semua unit)</option>' +   // v1.2.167: unit-bisnis\n"
            "          (buData || []).map(function (u) { return '<option value=\"' + esc(u.id) + '\"' + (p.unit === u.id ? ' selected' : '') + '>' + esc(u.name) + '</option>'; }).join('') +\n"
            "          (p.unit && !buName(p.unit) ? '<option value=\"' + esc(p.unit) + '\" selected>(unit dihapus)</option>' : '') + '</select></div>' : '') +", 'pr editor')
    j = rep(j, "    edEl.querySelector('.pr-note').oninput = function (ev) { priceData[si].note = ev.target.value; prMarkDirty(); };\n",
            "    edEl.querySelector('.pr-note').oninput = function (ev) { priceData[si].note = ev.target.value; prMarkDirty(); };\n"
            "    var _pu = edEl.querySelector('.pr-unit'); if (_pu) _pu.onchange = function (ev) { priceData[si].unit = ev.target.value; prMarkDirty(); renderPricelist(); };   // v1.2.167\n", 'pr unit handler')

    UNITS_JS = r'''
  /* ---- v1.2.167: unit-bisnis ------------------------------------------ */
  var buData = null, buChannels = [], buCats = [], buDirty = false, buMax = 10;
  function buName(id) { var u = (buData || []).filter(function (x) { return x.id === id; })[0]; return u ? (u.name || '(tanpa nama)') : ''; }
  function fetchUnits(cb) {
    api('get_units').then(function (res) {
      if (!res || !res.ok) { toast((res && res.error) || 'Gagal memuat unit bisnis.', true); return; }
      buData = res.units || []; buChannels = res.channels || []; buCats = res.categories || []; buMax = res.max || 10; buDirty = false;
      var m = document.getElementById('unitMeta');
      if (m) m.textContent = res.updated_at ? ('Diperbarui ' + res.updated_at.slice(0, 16) + (res.updated_by ? ' oleh ' + res.updated_by : '')) : '';
      if (cb) cb(); else renderUnits();
    });
  }
  function buMark() { buDirty = true; var b = document.getElementById('btnSaveUnits'); if (b) b.classList.add('kb-dirty'); }
  function renderUnits() {
    var wrap = document.getElementById('unitList'); if (!wrap) return;
    var bs = document.getElementById('btnSaveUnits'); if (bs) { bs.classList.toggle('kb-dirty', buDirty); bs.onclick = saveUnits; }
    var ba = document.getElementById('btnAddUnit');
    if (ba) ba.onclick = function () {
      if (buData.length >= buMax) { toast('Maksimal ' + buMax + ' unit.', true); return; }
      buData.push({ id: 'u_' + Date.now().toString(36), name: '', channels: [], categories: [], instructions: '' });
      buMark(); renderUnits();
      var ins = wrap.querySelectorAll('.bu-name'); if (ins.length) ins[ins.length - 1].focus();
    };
    if (!buData.length) {
      wrap.innerHTML = '<div class="card kb-empty" style="padding:40px 20px;text-align:center">Belum ada unit bisnis. Semua nomor WA &amp; widget memakai seluruh Knowledge Base.<br>Klik <b>+ Tambah Unit</b> bila tenant ini punya lebih dari satu usaha.</div>';
      return;
    }
    var chOwner = {};
    buData.forEach(function (u) { (u.channels || []).forEach(function (c) { if (!chOwner[c]) chOwner[c] = u; }); });
    var allCats = buCats.slice(), seen = {};
    allCats.forEach(function (c) { seen[c.toLowerCase()] = 1; });
    buData.forEach(function (u) { (u.categories || []).forEach(function (c) { if (!seen[c.toLowerCase()]) { seen[c.toLowerCase()] = 1; allCats.push(c); } }); });
    wrap.innerHTML = buData.map(function (u, i) {
      var chs = buChannels.map(function (c) {
        var on = (u.channels || []).indexOf(c.id) !== -1, ow = chOwner[c.id];
        return '<label class="bu-chk"><input type="checkbox" class="bu-ch" data-i="' + i + '" value="' + esc(c.id) + '"' + (on ? ' checked' : '') + '> ' + esc(c.label) +
          (!on && ow ? ' <small>(dipakai ' + esc(ow.name || 'unit lain') + ')</small>' : '') + '</label>';
      }).join('') || '<span class="help">Belum ada kanal.</span>';
      var mine = {}; (u.categories || []).forEach(function (c) { mine[c.toLowerCase()] = 1; });
      var cats = allCats.map(function (c) {
        var others = buData.filter(function (x, k) { return k !== i && (x.categories || []).some(function (y) { return y.toLowerCase() === c.toLowerCase(); }); })
          .map(function (x) { return x.name || 'unit lain'; });
        var gone = buCats.every(function (y) { return y.toLowerCase() !== c.toLowerCase(); });
        return '<label class="bu-chk"><input type="checkbox" class="bu-cat" data-i="' + i + '" value="' + esc(c) + '"' + (mine[c.toLowerCase()] ? ' checked' : '') + '> ' + esc(c) +
          (others.length ? ' <small>(juga ' + esc(others.join(', ')) + ')</small>' : '') + (gone ? ' <small>(tidak ada di KB)</small>' : '') + '</label>';
      }).join('') || '<span class="help">KB belum punya kategori. Isi kolom kategori di entri KB dulu (mis. Rental Mobil, Villa, Fashion).</span>';
      var nCh = (u.channels || []).length, nCat = (u.categories || []).length;
      return '<div class="card bu-card">' +
        '<h3>' + ico('layers', 16) + ' ' + (esc(u.name) || '<i style="color:var(--muted)">Unit baru</i>') + '</h3>' +
        '<div class="row"><label class="fl">Nama unit</label><input type="text" class="bu-name" data-i="' + i + '" maxlength="60" value="' + esc(u.name || '') + '" placeholder="mis. Rental Mobil"></div>' +
        '<div class="row"><label class="fl">Kanal yang dilayani unit ini</label><div class="bu-chks">' + chs + '</div>' +
          (!nCh ? '<div class="help" style="margin-top:4px">Belum ada kanal: unit ini hanya bisa dicoba lewat Tes Chatbot.</div>' : '') + '</div>' +
        '<div class="row"><label class="fl">Kategori KB milik unit ini</label><div class="bu-chks">' + cats + '</div>' +
          (!nCat ? '<div class="help" style="margin-top:4px">Tanpa kategori: unit ini hanya memakai kategori umum.</div>' : '') + '</div>' +
        '<div class="row"><label class="fl">Instruksi khusus (opsional)</label><textarea class="bu-ins" data-i="' + i + '" maxlength="2000" style="min-height:90px" placeholder="mis. Kamu melayani sewa mobil lepas kunci &amp; dengan sopir. Untuk villa, arahkan ke WA 0812-xxxx.">' + esc(u.instructions || '') + '</textarea></div>' +
        '<div style="text-align:right"><button class="btn danger sm bu-del" data-i="' + i + '">' + ico('trash-2', 14) + ' Hapus unit</button></div>' +
      '</div>';
    }).join('');
    $$('#unitList .bu-name').forEach(function (el) { el.oninput = function () { buData[+el.dataset.i].name = el.value; buMark(); }; el.onchange = renderUnits; });
    $$('#unitList .bu-ins').forEach(function (el) { el.oninput = function () { buData[+el.dataset.i].instructions = el.value; buMark(); }; });
    $$('#unitList .bu-ch').forEach(function (el) {
      el.onchange = function () {
        var i = +el.dataset.i, v = el.value;
        buData.forEach(function (u, k) {   // satu kanal hanya milik satu unit
          u.channels = (u.channels || []).filter(function (c) { return c !== v; });
          if (k === i && el.checked) u.channels.push(v);
        });
        buMark(); renderUnits();
      };
    });
    $$('#unitList .bu-cat').forEach(function (el) {
      el.onchange = function () {
        var u = buData[+el.dataset.i], v = el.value;
        u.categories = (u.categories || []).filter(function (c) { return c.toLowerCase() !== v.toLowerCase(); });
        if (el.checked) u.categories.push(v);
        buMark(); renderUnits();
      };
    });
    $$('#unitList .bu-del').forEach(function (el) {
      el.onclick = function () {
        var u = buData[+el.dataset.i];
        if (!confirm('Hapus unit "' + (u.name || 'tanpa nama') + '"?\nKanalnya kembali memakai seluruh KB.')) return;
        buData.splice(+el.dataset.i, 1); buMark(); renderUnits();
      };
    });
  }
  function saveUnits() {
    var kosong = buData.filter(function (u) { return !(u.name || '').trim(); }).length;
    if (kosong && !confirm(kosong + ' unit belum diberi nama dan tidak akan disimpan. Lanjut?')) return;
    api('save_units', { method: 'POST', body: { units: buData } }).then(function (res) {
      if (res && res.ok) { toast('Unit bisnis disimpan (' + (res.units || []).length + ' unit).'); fetchUnits(); }
      else toast((res && res.error) || 'Gagal menyimpan.', true);
    });
  }

  /* ---- v1.2.22: daftar harga ----------------------------------------- */'''
    j = rep(j, "\n  /* ---- v1.2.22: daftar harga ----------------------------------------- */", UNITS_JS, 'units js')

    # Tes Chatbot: pilih unit
    j = rep(j, "    $('#testInput').addEventListener('keydown', function (e) { if (e.key === 'Enter') testSend(); });\n  }",
            "    $('#testInput').addEventListener('keydown', function (e) { if (e.key === 'Enter') testSend(); });\n"
            "    api('get_units').then(function (res) {   // v1.2.167: unit-bisnis — uji sebagai unit\n"
            "      var sel = document.getElementById('testUnit'); if (!sel || !res || !res.ok) return;\n"
            "      var us = res.units || [], cur = sel.value;\n"
            "      if (!us.length) { sel.style.display = 'none'; sel.innerHTML = ''; return; }\n"
            "      sel.innerHTML = '<option value=\"\">Otomatis (seperti widget web)</option><option value=\"#\">Tanpa unit (semua KB)</option>' +\n"
            "        us.map(function (u) { return '<option value=\"#' + esc(u.id) + '\">Unit: ' + esc(u.name) + '</option>'; }).join('');\n"
            "      sel.value = cur; if (sel.value !== cur) sel.value = '';\n"
            "      sel.style.display = '';\n"
            "      sel.onchange = function () { testHist = []; $('#test-body').innerHTML = ''; };\n"
            "    });\n  }", 'test init')
    j = rep(j, "body: JSON.stringify({ message: v, history: testHist.slice(-8), utm: { utm_source: 'dashboard', utm_medium: 'test', page: '/dashboard/test' } }) })",
            "body: JSON.stringify({ message: v, history: testHist.slice(-8), unit_test: (($('#testUnit') || {}).value || ''), utm: { utm_source: 'dashboard', utm_medium: 'test', page: '/dashboard/test' } }) })   // v1.2.167: unit_test", 'test send')
    wr(JS, j)

for p in (API, JS, HTML):
    assert TAG in rd(p) or (p == HTML and 'v1.2.167: unit-bisnis' in rd(p)), 'tag hilang: ' + p
print('OK patch v1.2.167')
