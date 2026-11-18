#!/usr/bin/env python3
"""v1.2.202 (id-noweb): id pesan keluar WAHA engine NOWEB/GOWS ikut tersimpan.
NOWEB membalas /api/sendText dkk dengan {key:{remoteJid, fromMe, id}, message, ...} tanpa 'id' di akar,
jadi wahaMsgId() mengembalikan '' -> out_id kosong -> tombol Balas, Edit, Hapus tidak muncul di bubble keluar.
wahaMsgId kini juga membaca key{} (juga di message.key / _data.key) dan menyusun id gaya WAHA
"true_<jid>_<id>" (@s.whatsapp.net -> @c.us). Pesan yang terkirim sebelum versi ini tetap tanpa id.
Butuh v1.2.201. Idempoten.  Pakai: patch_v12202.py [~/Herd | root-dei-tenant] [--no-backup]"""
import os, sys, time, shutil
arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd'
H = os.path.expanduser(arg)
T = H if os.path.isfile(H + '/api/index.php') else H + '/dei-tenant'
TAG = 'v1.2.202: id-noweb'; NEED = 'v1.2.201: transfer-nomor'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK and os.path.exists(p): shutil.copy2(p, p + '.bak-v12202-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HT = T + '/dashboard/chatbot-ai/index.html'

s = rd(API)
if TAG not in s:
    assert NEED in s, 'butuh v1.2.201 dulu'
    s = rep(s, "define('DEI_VERSION', 'v1.2.201');   // v1.2.201:",
            "define('DEI_VERSION', 'v1.2.202');   // " + TAG + " — id pesan keluar WAHA NOWEB tersimpan (Balas/Edit/Hapus muncul); v1.2.201:", what='DEI_VERSION')
    s = rep(s, "function wahaMsgId($p) {\n"
               "    $id = $p['id'] ?? '';\n"
               "    if (is_array($id)) $id = $id['_serialized'] ?? ($id['id'] ?? '');\n"
               "    return (string)$id;\n"
               "}\n",
               "function wahaMsgId($p) {\n"
               "    if (!is_array($p)) return '';\n"
               "    $id = $p['id'] ?? '';\n"
               "    if (is_array($id)) $id = $id['_serialized'] ?? ($id['id'] ?? '');\n"
               "    $id = (string)$id;\n"
               "    if ($id !== '') return $id;\n"
               "    // " + TAG + ": NOWEB/GOWS -> {key:{remoteJid, fromMe, id}} (bisa juga di message.key / _data.key)\n"
               "    $k = $p['key'] ?? ($p['message']['key'] ?? ($p['_data']['key'] ?? null));\n"
               "    if (!is_array($k) || (string)($k['id'] ?? '') === '') return '';\n"
               "    $jid = str_replace('@s.whatsapp.net', '@c.us', (string)($k['remoteJid'] ?? ($k['remote'] ?? '')));\n"
               "    return $jid !== '' ? ((!empty($k['fromMe']) ? 'true' : 'false') . '_' . $jid . '_' . (string)$k['id']) : (string)$k['id'];\n"
               "}\n", what='wahaMsgId')
    save(API, s)
else: print('sudah', API)

s = rd(HT)
if TAG not in s:
    s = rep(s, '<script src="app.js?v=1.2.201"></script><!-- v1.2.201: transfer-nomor -->',
            '<script src="app.js?v=1.2.202"></script><!-- ' + TAG + ' --><!-- v1.2.201: transfer-nomor -->', what='app.js?v')
    save(HT, s)
else: print('sudah', HT)
s = rd(JS)
if TAG not in s:
    s = rep(s, "  /* ---- v1.2.200: edit-hapus-pesan — edit & hapus pesan keluar (WAHA) ---- */\n",
            "  /* ---- v1.2.200: edit-hapus-pesan — edit & hapus pesan keluar (WAHA) ---- */\n  // " + TAG + ": id pesan keluar NOWEB kini tersimpan (perubahan di api)\n", what='js mark')
    save(JS, s)
else: print('sudah', JS)
print('patch v1.2.202 selesai')
