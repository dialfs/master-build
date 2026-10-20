#!/usr/bin/env python3
"""v1.2.94 (lanjutan) — masa simpan media WA: bawaan 7 hari, pilihan 14 / 30 hari (Widget & API › WhatsApp Bot).
Jalankan SETELAH patch_v1294_wa_media.py.  Pemakaian: python3 patch_v1294_media_days.py <root dei-tenant>  (idempoten)"""
import sys, os, time, shutil
TEN = sys.argv[1]
STAMP = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.94: media-days'

def patch(root, rel, pairs):
    p = os.path.join(root, rel)
    s = open(p, encoding='utf-8').read()
    if MARK in s: print('sudah dipatch:', rel); return
    for old, new in pairs:
        n = s.count(old)
        if n != 1: sys.exit(f'GAGAL {rel}: anchor {n}x:\n{old[:200]}')
        s = s.replace(old, new)
    shutil.copy2(p, p + '.bak-v1294d-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

patch(TEN, 'api/index.php', [
    ("    return max(1, min(365, (int)($s['whatsapp_api']['media_days'] ?? 30)));\n",
     "    $d = (int)($s['whatsapp_api']['media_days'] ?? 7);   // " + MARK + ": bawaan 7, pilihan 7/14/30\n"
     "    return in_array($d, [7, 14, 30], true) ? $d : 7;\n"),
    (" * wa_media (wajib login), dihapus otomatis setelah media_days hari (bawaan 30).",
     " * wa_media (wajib login), dihapus otomatis setelah media_days hari (bawaan 7; pilihan 14/30)."),
])

patch(TEN, 'dashboard/chatbot-ai/index.html', [
    ('          <label class="switch"><input type="checkbox" id="wa_enabled"><span class="sl"></span></label></div>\n',
     '          <label class="switch"><input type="checkbox" id="wa_enabled"><span class="sl"></span></label></div>\n'
     '        <div class="row"><label class="fl">Simpan media di dashboard</label><select id="wa_media_days">'
     '<option value="7">7 hari (bawaan)</option><option value="14">14 hari</option><option value="30">30 hari</option></select>'
     '<div class="help">Gambar, video, pesan suara &amp; dokumen dari WhatsApp disimpan di dashboard selama ini, lalu dihapus otomatis. Salinan asli tetap ada di HP / WhatsApp Business.</div></div><!-- ' + MARK + ' -->\n'),
])

patch(TEN, 'dashboard/chatbot-ai/app.js', [
    ("      $('#wa_enabled').checked = wa.enabled === true;\n",
     "      $('#wa_enabled').checked = wa.enabled === true;\n"
     "      if ($('#wa_media_days')) $('#wa_media_days').value = String([7, 14, 30].indexOf(+wa.media_days) !== -1 ? +wa.media_days : 7);   // " + MARK + "\n"),
    ("      enabled: $('#wa_enabled').checked,\n      phone_number_id: $('#wa_pnid').value.trim(),\n",
     "      enabled: $('#wa_enabled').checked,\n"
     "      media_days: $('#wa_media_days') ? +$('#wa_media_days').value || 7 : 7,   // " + MARK + "\n"
     "      phone_number_id: $('#wa_pnid').value.trim(),\n"),
])
print('selesai')
