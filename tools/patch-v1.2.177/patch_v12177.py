#!/usr/bin/env python3
"""v1.2.177 headline-iklan (TENANT, di atas v1.2.176): dua opsi nama campaign chat iklan Click-to-WhatsApp.
- Token Meta Ads terisi  -> nama campaign asli dari Meta Marketing API (seperti v1.2.176).
- Token kosong / iklan belum terbaca -> HEADLINE iklan (dulu "iklan <ID>"). Baris & atribusi v1.2.176 ikut.
- Teks dashboard: kartu laporan "Campaign / Headline Iklan", keterangan kartu Meta Ads disesuaikan.
Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HTML = T + '/dashboard/chatbot-ai/index.html'
TAG = 'v1.2.177: headline-iklan'; stamp = time.strftime('%Y%m%d-%H%M%S')
NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    assert 'v1.2.176: meta-campaign' in s, 'butuh berkas v1.2.176: ' + p
    if not NOBAK: shutil.copy2(p, p + '.bak-v12177-' + stamp)
    wr(p, fn(s)); print('OK', p)
C = '   // ' + TAG

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.176');   // v1.2.176:",
               "define('DEI_VERSION', 'v1.2.177');   // " + TAG + " — tanpa token Meta Ads, campaign iklan CTWA = headline iklan; v1.2.176:", 'versi')
    s = rep(s, "    $cmp = $adId !== '' ? 'iklan ' . $adId : $hl;\n",
               "    $cmp = $hl !== '' ? $hl : ($adId !== '' ? 'iklan ' . $adId : '');" + C + " — cadangan = headline\n", 'cadangan')
    s = rep(s, "    return $memo[$ad] !== '' ? $memo[$ad] : $cmp;\n",
               "    if ($memo[$ad] !== '') return $memo[$ad];\n"
               "    $hl = (string)($l['wa_hl'] ?? '');" + C + " — belum ada nama dari Meta: pakai headline\n"
               "    return $hl !== '' ? $hl : $cmp;\n", 'deiWaCmp')
    return s

def js(s):
    return rep(s, "'Belum ada token — chat dari iklan CTWA tercatat sebagai \"iklan <ID iklan>\".';",
                  "'Belum ada token — campaign chat dari iklan CTWA memakai headline iklan.';" + C, 'status')

def html(s):
    s = rep(s, "        <h3>Campaign (UTM Campaign)</h3>\n",
               "        <h3>Campaign / Headline Iklan</h3><!-- " + TAG + " -->\n", 'judul')
    s = rep(s, '        <div class="desc">Nama kampanye dari URL Builder.</div>\n',
               '        <div class="desc">Web: nama kampanye dari UTM. WhatsApp dari iklan Click-to-WhatsApp: nama campaign Meta bila token Meta Ads terpasang, selain itu headline iklan.</div>\n', 'desc')
    s = rep(s, 'nama campaign diambil otomatis dari Meta Marketing API dan tampil di laporan Source / Medium / Campaign.</div>',
               'nama campaign diambil otomatis dari Meta Marketing API dan tampil di laporan Source / Medium / Campaign. Tanpa token, laporan memakai headline iklan.</div>', 'kartu')
    return s

patch(API, api); patch(JS, js); patch(HTML, html)
