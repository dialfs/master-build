#!/usr/bin/env python3
"""v1.2.201 (transfer-nomor): menu "Transfer ke…" di kepala chat Percakapan WA menggabungkan
Agent + Nomor WhatsApp bisnis lain, supaya Supervisor/Admin bisa langsung memindah chat ke nomor
bisnis lain dari menu yang sama (dulu terpisah: dropdown nomor berlabel nomor aktif, tidak terlihat
seperti tombol pindah). Tanpa agent: dropdown "Pindah ke nomor…". Pindah tetap lewat wa_set_ch.
- app.js + index.html (app.js?v=1.2.201) + api/index.php (DEI_VERSION).
Butuh v1.2.200. Idempoten.  Pakai: patch_v12201.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.201: transfer-nomor'; NEED = 'v1.2.200: edit-hapus-pesan'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12201-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

s = rd(API)
if TAG not in s:
    assert NEED in s, 'butuh v1.2.200 dulu'
    s = rep(s, "define('DEI_VERSION', 'v1.2.200');   // v1.2.200:",
            "define('DEI_VERSION', 'v1.2.201');   // " + TAG + " — menu Transfer ke… gabung Agent + nomor WhatsApp bisnis; v1.2.200:", what='DEI_VERSION')
    save(API, s)
else: print('sudah', API)

s = rd(JS)
if TAG not in s:
    assert NEED in s, 'butuh v1.2.200 dulu'
    s = rep(s, "    // v1.2.58: Supervisor/Admin — serahkan chat ke agent tertentu\n",
               "    var _ag201 = '', _chO201 = '', _chCur201 = '';   // " + TAG + "\n"
               "    // v1.2.58: Supervisor/Admin — serahkan chat ke agent tertentu\n", what='var')
    s = rep(s, "      toolBtns += '<span class=\"wa-assign\">' + ico('user-round',13) + '<select id=\"waAssignSel\">' + _opsi + '</select></span>';\n",
               "      _ag201 = _opsi.replace('<option value=\"\">Transfer ke Agent</option>', '');   // " + TAG + ": dirakit di bawah bersama nomor bisnis\n", what='agent emit')
    s = rep(s, "      toolBtns += '<span class=\"wa-assign\" title=\"Nomor bisnis yang dipakai membalas chat ini. Pilih nomor lain untuk memindah.\">' + ico('phone',13) +\n"
               "        '<select id=\"waChMoveSel\"><option value=\"\">' + esc(_curCh144 ? _lbl146(_curCh144) : 'Nomor bisnis') + '</option>' +\n"
               "        _chs116.filter(function (c) { return c.id !== _cur116; }).map(function (c) {\n"
               "          return '<option value=\"' + esc(c.id) + '\"' + (c.number ? ' title=\"+' + esc(c.number) + '\"' : '') + '>' + esc(_lbl146(c)) + '</option>';\n"
               "        }).join('') + '</select></span>';\n",
               "      _chCur201 = _curCh144 ? _lbl146(_curCh144) : 'Nomor bisnis';   // " + TAG + "\n"
               "      _chO201 = _chs116.filter(function (c) { return c.id !== _cur116; }).map(function (c) {\n"
               "        var l = _lbl146(c), n = String(c.number || '');\n"
               "        return '<option value=\"ch:' + esc(c.id) + '\"' + (n ? ' title=\"+' + esc(n) + '\"' : '') + '>' + esc(l) + (n && l.replace(/\\D/g, '') !== n ? ' (+' + esc(n) + ')' : '') + '</option>';\n"
               "      }).join('');\n", what='ch emit')
    s = rep(s, "    // v1.2.19: nama kontak (dari daftar percakapan) + tombol koreksi\n",
               "    // " + TAG + ": satu menu Transfer ke… = Agent + Nomor WhatsApp bisnis\n"
               "    if (_ag201 && _chO201) toolBtns += '<span class=\"wa-assign\" title=\"Serahkan chat ke agent lain, atau pindahkan ke nomor WhatsApp bisnis lain (sekarang: ' + esc(_chCur201) + ')\">' + ico('user-round',13) +\n"
               "      '<select id=\"waAssignSel\"><option value=\"\">Transfer ke…</option><optgroup label=\"Agent\">' + _ag201 + '</optgroup>' +\n"
               "      '<optgroup label=\"Nomor WhatsApp bisnis (sekarang: ' + esc(_chCur201) + ')\">' + _chO201 + '</optgroup></select></span>';\n"
               "    else if (_ag201) toolBtns += '<span class=\"wa-assign\">' + ico('user-round',13) + '<select id=\"waAssignSel\"><option value=\"\">Transfer ke Agent</option>' + _ag201 + '</select></span>';\n"
               "    else if (_chO201) toolBtns += '<span class=\"wa-assign\" title=\"Pindahkan chat ke nomor WhatsApp bisnis lain (sekarang: ' + esc(_chCur201) + ')\">' + ico('phone',13) +\n"
               "      '<select id=\"waAssignSel\"><option value=\"\">Pindah ke nomor…</option>' + _chO201 + '</select></span>';\n"
               "\n"
               "    // v1.2.19: nama kontak (dari daftar percakapan) + tombol koreksi\n", what='emit gabung')
    s = rep(s, "    if ($('#waAssignSel')) $('#waAssignSel').onchange = function () { assignNumber(num, this.value, this); };   // v1.2.58\n",
               "    if ($('#waAssignSel')) $('#waAssignSel').onchange = function () {   // v1.2.58; " + TAG + ": nilai 'ch:<id>' = pindah nomor bisnis\n"
               "      var v = this.value;\n"
               "      if (v.indexOf('ch:') === 0) { var id = v.slice(3), tc = (res.channels || []).filter(function (c) { return c.id === id; })[0]; moveWaChan(num, id, this, (tc && tc.prov) || res.wa_prov); }\n"
               "      else assignNumber(num, v, this);\n"
               "    };\n", what='onchange')
    s = rep(s, "    var msg = 'Pindahkan chat ini ke nomor ' + label + '?",
               "    label = label.replace(/\\s*\\(\\+\\d+\\)$/, '');   // " + TAG + "\n"
               "    var msg = 'Pindahkan chat ini ke nomor ' + label + '?", what='label')
    save(JS, s)
else: print('sudah', JS)

s = rd(HT)
if TAG not in s:
    s = rep(s, '<script src="app.js?v=1.2.200"></script><!-- v1.2.200: edit-hapus-pesan -->',
            '<script src="app.js?v=1.2.201"></script><!-- ' + TAG + ' --><!-- v1.2.200: edit-hapus-pesan -->', what='app.js?v')
    save(HT, s)
else: print('sudah', HT)
print('patch v1.2.201 selesai')
