#!/usr/bin/env python3
"""v1.2.171 produk-varian (TENANT): tab "Daftar Harga" jadi "Produk" — tiap produk punya harga atau beberapa
varian (tombol + Tambah varian) dan Detail produk. Bot menerima nama + harga semua produk; detail dikirim
semua bila total kecil, atau hanya maks 5 produk yang cocok dengan pesan pelanggan.
Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
PROD = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prod.php')
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HTML = T + '/dashboard/chatbot-ai/index.html'
TAG = 'v1.2.171: produk-varian'; stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    shutil.copy2(p, p + '.bak-v12171-' + stamp); wr(p, fn(s)); print('OK', p)
C = '   // ' + TAG

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.170');   // v1.2.170:",
               "define('DEI_VERSION', 'v1.2.171');   // " + TAG + " — Daftar Harga jadi Produk: varian harga + detail produk, detail dipilih sesuai pertanyaan; v1.2.170:", 'versi')
    a = "// Susun blok instruksi + daftar harga untuk dikirim ke model.\n"
    b = "/* ============================================================\n * v1.2.20: Leads"
    assert s.count(a) == 1 and s.count(b) == 1, 'anchor fungsi harga'
    i, j = s.index(a), s.index(b)
    assert i < j and 'function pricelistPromptBlock(' in s[i:j], 'fungsi harga tidak di antara anchor'
    s = s[:i] + rd(PROD).rstrip() + "\n\n" + s[j:]
    s = rep(s, "$deiPriceBlk = pricelistPromptBlock($deiUnit);",
               "$deiPriceBlk = pricelistPromptBlock($deiUnit, $message, $history);" + C + " —", 'caller')
    s = rep(s, "                'note'  => mb_substr(trim((string)($it['note'] ?? '')), 0, 200),\n",
               "                'note'  => mb_substr(trim((string)($it['note'] ?? '')), 0, 2000),   // " + TAG + " — detail produk\n"
               "                'variants' => prVarClean($it['variants'] ?? []),   // " + TAG + "\n", 'save')
    return s

def js(s):
    s = rep(s, "priceData.unshift({ id: nid, item: '', price: '', note: '' });",
               "priceData.unshift({ id: nid, item: '', price: '', note: '', variants: [] });   // " + TAG, 'add')
    s = rep(s, "'Gagal memuat daftar harga.'", "'Gagal memuat daftar produk.'", 'load err')
    s = rep(s, "  function renderPricelist() {\n",
               "  function prAmt(p) {   // " + TAG + "\n"
               "    var v = (p.variants || []).filter(function (x) { return (x.name || '').trim() || (x.price || '').trim(); });\n"
               "    return v.length ? v.length + ' varian' : (p.price || '').trim();\n"
               "  }\n"
               "  function renderPricelist() {\n", 'prAmt')
    s = rep(s, "if (term && ((p.item || '') + ' ' + (p.price || '') + ' ' + (p.note || '')).toLowerCase()",
               "if (term && ((p.item || '') + ' ' + (p.price || '') + ' ' + (p.note || '') + ' ' + (p.variants || []).map(function (v) { return (v.name || '') + ' ' + (v.price || ''); }).join(' ')).toLowerCase()", 'search')
    s = rep(s, "'<span class=\"pr-amt' + ((p.price || '').trim() ? '' : ' empty') + '\">' + (esc(p.price) || 'belum ada harga') + '</span></span>' +\n        (p.note ? '<small>' + esc(p.note) + '</small>' : '')",
               "'<span class=\"pr-amt' + (prAmt(p) ? '' : ' empty') + '\">' + (esc(prAmt(p)) || 'belum ada harga') + '</span></span>' +\n        (p.note ? '<small>' + esc(p.note.length > 120 ? p.note.slice(0, 120) + '…' : p.note) + '</small>' : '')", 'list')
    s = rep(s, "'Tidak ada item yang cocok.' : 'Belum ada harga. Klik \"+ Tambah Baris\" untuk mulai.'",
               "'Tidak ada produk yang cocok.' : 'Belum ada produk. Klik \"+ Tambah Produk\" untuk mulai.'", 'empty')
    s = rep(s, "Pilih item di kiri untuk melihat &amp; mengedit,<br>atau klik <b>+ Tambah Baris</b>.",
               "Pilih produk di kiri untuk melihat &amp; mengedit,<br>atau klik <b>+ Tambah Produk</b>.", 'empty ed')
    s = rep(s, "      var p = priceData[si];\n      ed = '<div class=\"kb-ed-head\"><button class=\"btn ghost sm kb-back\">&larr; Daftar</button>' +\n          '<span class=\"help\">Item ' +",
               "      var p = priceData[si];\n      var pv = Array.isArray(p.variants) ? p.variants : (p.variants = []);   // " + TAG + "\n      ed = '<div class=\"kb-ed-head\"><button class=\"btn ghost sm kb-back\">&larr; Daftar</button>' +\n          '<span class=\"help\">Produk ' +", 'ed head')
    old_rows = ("        '<div class=\"row\"><label class=\"fl\">Nama item</label><input type=\"text\" class=\"pr-item\" maxlength=\"150\" value=\"' + esc(p.item || '') + '\" placeholder=\"mis. Deluxe Room (weekday)\"></div>' +\n"
                "        '<div class=\"row\"><label class=\"fl\">Harga</label><input type=\"text\" class=\"pr-price\" maxlength=\"100\" value=\"' + esc(p.price || '') + '\" placeholder=\"mis. Rp 750.000 / malam\"></div>' +\n"
                "        '<div class=\"row\"><label class=\"fl\">Catatan (opsional)</label><textarea class=\"pr-note\" style=\"min-height:120px\" placeholder=\"mis. termasuk sarapan 2 orang\">' + esc(p.note || '') + '</textarea></div>' +\n")
    new_rows = ("        '<div class=\"row\"><label class=\"fl\">Nama produk</label><input type=\"text\" class=\"pr-item\" maxlength=\"150\" value=\"' + esc(p.item || '') + '\" placeholder=\"mis. Deluxe Room / Audiobook Lunas Hutang\"></div>' +   // " + TAG + "\n"
                "        (pv.length ? '' : '<div class=\"row\"><label class=\"fl\">Harga</label><input type=\"text\" class=\"pr-price\" maxlength=\"100\" value=\"' + esc(p.price || '') + '\" placeholder=\"mis. Rp 750.000 / malam\"></div>') +\n"
                "        '<div class=\"row\"><label class=\"fl\">Varian' + (pv.length ? ' (nama &amp; harga)' : ' (opsional)') + '</label>' +\n"
                "          pv.map(function (v, k) {\n"
                "            return '<div class=\"pv-row\"><input type=\"text\" class=\"pv-name\" data-k=\"' + k + '\" maxlength=\"100\" value=\"' + esc(v.name || '') + '\" placeholder=\"Nama varian, mis. Paket A\">' +\n"
                "              '<input type=\"text\" class=\"pv-price\" data-k=\"' + k + '\" maxlength=\"100\" value=\"' + esc(v.price || '') + '\" placeholder=\"Harga, mis. Rp 100.000\">' +\n"
                "              '<button type=\"button\" class=\"btn ghost sm pv-del\" data-k=\"' + k + '\" title=\"Hapus varian\">' + ico('x', 13) + '</button></div>';\n"
                "          }).join('') +\n"
                "          '<button type=\"button\" class=\"btn ghost sm pv-add\">+ Tambah varian</button>' +\n"
                "          (pv.length ? '' : '<div class=\"help\" style=\"margin-top:4px\">Pakai varian kalau produk punya beberapa pilihan harga (ukuran, paket, durasi).</div>') + '</div>' +\n"
                "        '<div class=\"row\"><label class=\"fl\">Detail produk (opsional)</label><textarea class=\"pr-note\" maxlength=\"2000\" style=\"min-height:140px\" placeholder=\"Isi, manfaat, spesifikasi, cara pakai, syarat…\">' + esc(p.note || '') + '</textarea>' +\n"
                "          '<div class=\"help\" style=\"margin-top:4px\">Bot memakai detail ini untuk menjawab pertanyaan tentang produk ini. Maks 2.000 karakter.</div></div>' +\n")
    s = rep(s, old_rows, new_rows, 'ed rows')
    s = rep(s, "ico('trash-2',14) + ' Hapus item</button>'", "ico('trash-2',14) + ' Hapus produk</button>'", 'del btn')
    s = rep(s, "'<div class=\"kb-side\"><div class=\"kb-count\">' + shown.length + ' item</div>",
               "'<div class=\"kb-side\"><div class=\"kb-count\">' + shown.length + ' produk</div>", 'count')
    s = rep(s, "    edEl.querySelector('.pr-price').oninput = function (ev) {\n      priceData[si].price = ev.target.value; prMarkDirty();",
               "    var _pp = edEl.querySelector('.pr-price'); if (_pp) _pp.oninput = function (ev) {   // " + TAG + " — tidak ada bila bervarian\n      priceData[si].price = ev.target.value; prMarkDirty();", 'price h')
    s = rep(s, "    edEl.querySelector('.pr-note').oninput = function (ev) { priceData[si].note = ev.target.value; prMarkDirty(); };\n",
               "    edEl.querySelector('.pr-note').oninput = function (ev) { priceData[si].note = ev.target.value; prMarkDirty(); };\n"
               "    var pvAmt = function () { var l = li(); if (!l) return; var a = l.querySelector('.pr-amt'), t = prAmt(priceData[si]); a.textContent = t || 'belum ada harga'; a.classList.toggle('empty', !t); };   // " + TAG + "\n"
               "    $$('#priceList .pv-name').forEach(function (el) { el.oninput = function () { priceData[si].variants[+el.dataset.k].name = el.value; prMarkDirty(); pvAmt(); }; });   // " + TAG + "\n"
               "    $$('#priceList .pv-price').forEach(function (el) { el.oninput = function () { priceData[si].variants[+el.dataset.k].price = el.value; prMarkDirty(); pvAmt(); }; });\n"
               "    $$('#priceList .pv-del').forEach(function (el) { el.onclick = function () { priceData[si].variants.splice(+el.dataset.k, 1); prMarkDirty(); renderPricelist(); }; });\n"
               "    edEl.querySelector('.pv-add').onclick = function () {\n"
               "      var pp = priceData[si]; if (!Array.isArray(pp.variants)) pp.variants = [];\n"
               "      if (!pp.variants.length && (pp.price || '').trim()) { pp.variants.push({ name: '', price: pp.price }); pp.price = ''; }   // harga lama jadi varian pertama\n"
               "      pp.variants.push({ name: '', price: '' }); prMarkDirty(); renderPricelist();\n"
               "      var ins = [].slice.call(document.querySelectorAll('#priceList .pv-name')).filter(function (x) { return !x.value; }); if (ins.length) ins[0].focus();\n"
               "    };\n", 'var h')
    s = rep(s, "if (!confirm('Hapus item \"' + (priceData[si].item || 'tanpa nama') + '\"?')) return;",
               "if (!confirm('Hapus produk \"' + (priceData[si].item || 'tanpa nama') + '\"?')) return;", 'del confirm')
    s = rep(s, "      return (p.item || '').trim() && !(p.price || '').trim();\n    }).length;\n    if (tanpaHarga && !confirm(tanpaHarga + ' baris punya nama tapi harganya kosong.\\nBaris itu tidak akan dipakai bot. Tetap simpan?')) return;",
               "      return (p.item || '').trim() && !(p.price || '').trim() && !(p.variants || []).some(function (v) { return (v.price || '').trim(); });   // " + TAG + "\n    }).length;\n    if (tanpaHarga && !confirm(tanpaHarga + ' produk belum punya harga.\\nBot akan bilang harganya belum tersedia (produk tanpa harga dan tanpa detail tidak dipakai bot). Tetap simpan?')) return;", 'save warn')
    s = rep(s, "toast('Daftar harga disimpan (' + res.count + ' item).');", "toast('Produk disimpan (' + res.count + ' produk).');", 'toast')
    s = rep(s, "Tab <b>Daftar Harga</b> untuk harga produk/layanan.", "Tab <b>Produk</b> untuk harga, varian &amp; detail produk/layanan.", 'tour')
    s = rep(s, "t: 'Mengatur daftar harga', k: 'harga price pricelist daftar harga tarif biaya produk paket',\n      s: ['Buka menu <b>Knowledge Base</b> → tab <b>Daftar Harga</b>.', 'Tambah / ubah item harga lalu simpan. Bot memakai daftar ini saat ditanya harga.'],\n      show: [{ tab: 'kb', pre: hClick('.kb-tab[data-kbtab=\"harga\"]'), el: '#kbTabHarga', title: 'Daftar Harga', body: '<p>Kelola harga produk / layanan di sini.</p>' }] },",
               "t: 'Mengatur produk & harga', k: 'harga price pricelist daftar harga tarif biaya produk paket varian detail',   // " + TAG + "\n      s: ['Buka menu <b>Knowledge Base</b> → tab <b>Produk</b>.', 'Klik <b>+ Tambah Produk</b>, isi nama, harga (atau <b>+ Tambah varian</b> untuk beberapa pilihan harga) dan detail produk, lalu simpan.', 'Bot memakai harga & detail ini saat pelanggan bertanya tentang produk.'],\n      show: [{ tab: 'kb', pre: hClick('.kb-tab[data-kbtab=\"harga\"]'), el: '#kbTabHarga', title: 'Produk', body: '<p>Kelola produk, varian harga &amp; detailnya di sini.</p>' }] },", 'panduan')
    return s

def html(s):
    s = rep(s, '<span data-ico="wallet" data-ico-size="14"></span> Daftar Harga</button>',
               '<span data-ico="wallet" data-ico-size="14"></span> Produk</button><!-- ' + TAG + ' -->', 'tab')
    s = rep(s, 'id="priceSearch" placeholder="Cari item / harga..."', 'id="priceSearch" placeholder="Cari produk / varian / harga..."', 'search')
    s = rep(s, '<button class="btn" id="btnAddPrice">+ Tambah Baris</button>', '<button class="btn" id="btnAddPrice">+ Tambah Produk</button>', 'add')
    s = rep(s, '<span data-ico="save" data-ico-size="15"></span> Simpan Daftar Harga</button>', '<span data-ico="save" data-ico-size="15"></span> Simpan Produk</button>', 'save')
    s = rep(s, "            Daftar ini jadi <strong>satu-satunya sumber harga</strong> bagi bot: menang atas\n            Knowledge Base, dan bot dilarang menghitung total &mdash; ia hanya menyebut harga\n            satuan lalu mengarahkan ke tim Anda.\n",
               "            Isi tiap produk dengan harga (atau beberapa <strong>varian</strong>) dan <strong>detail produk</strong>.\n            Ini jadi <strong>satu-satunya sumber harga</strong> bagi bot: menang atas\n            Knowledge Base, dan bot dilarang menghitung total &mdash; ia hanya menyebut harga\n            satuan lalu mengarahkan ke tim Anda.\n", 'intro')
    s = rep(s, "            <strong>Penting:</strong> hapus entri harga lama di tab Entri KB. Kalau dua tempat\n            memuat angka berbeda, bot bisa memakai yang salah tanpa ketahuan.\n",
               "            <strong>Penting:</strong> hapus entri harga lama di tab Entri KB. Kalau dua tempat\n            memuat angka berbeda, bot bisa memakai yang salah tanpa ketahuan. Detail produk yang\n            sudah dipindah ke sini sebaiknya juga dihapus dari Entri KB.\n", 'warn')
    s = rep(s, "  .pr-row{display:flex;gap:10px;align-items:baseline}\n",
               "  .pr-row{display:flex;gap:10px;align-items:baseline}\n"
               "  .pv-row{display:flex;gap:6px;margin-bottom:6px;align-items:center}.pv-row .pv-name{flex:1 1 55%;min-width:0}.pv-row .pv-price{flex:1 1 45%;min-width:0}.pv-row .pv-del{flex:0 0 auto}   /* " + TAG + " */\n", 'css')
    s = rep(s, '<script src="app.js?v=1.2.169"></script>', '<script src="app.js?v=1.2.171"></script><!-- ' + TAG + ' -->', 'cache')
    return s

patch(API, api); patch(JS, js); patch(HTML, html)
