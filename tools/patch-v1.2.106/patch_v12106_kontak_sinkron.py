#!/usr/bin/env python3
"""v1.2.106: kontak-sinkron — lead rating yang diubah dari Percakapan WA ikut berubah di menu Kontak.
Akar: tab dashboard dimuat sekali (loaded[tab]); contactData di-cache dan saveContactStage() tidak menyentuhnya.
Pakai: python3 patch_v12106_kontak_sinkron.py ~/Herd   (idempoten)"""
import sys, os, shutil, time
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd'); T = H + '/dei-tenant'
TAG = 'v1.2.106: kontak-sinkron'
stamp = time.strftime('%Y%m%d-%H%M%S')
P = {
 'api/index.php': [
  ("define('DEI_VERSION', 'v1.2.105');", "define('DEI_VERSION', 'v1.2.106');   // " + TAG),
 ],
 'dashboard/chatbot-ai/index.html': [
  ('<script src="app.js?v=1.2.105"></script><!-- v1.2.105: riwayat-wa-waha -->',
   '<script src="app.js?v=1.2.106"></script><!-- ' + TAG + ' -->'),
 ],
 'dashboard/chatbot-ai/app.js': [
  ("    if (!loaded[tab]) { loaded[tab] = true; if (loaders[tab]) loaders[tab](); }\n  }",
   "    if (!loaded[tab]) { loaded[tab] = true; if (loaders[tab]) loaders[tab](); }\n"
   "    else if (tab === 'kontak') fetchContacts();   // " + TAG + " (data Kontak selalu segar)\n  }"),
  ("      if (r && r.ok) {\n        toast('Tag disimpan.');",
   "      if (r && r.ok) {\n        toast('Tag disimpan.');\n"
   "        // " + TAG + " — sinkronkan cache menu Kontak (sebelumnya perubahan dari\n"
   "        // Percakapan WA tidak pernah sampai ke contactData karena tab dimuat sekali).\n"
   "        for (var _ci = 0; _ci < contactData.length; _ci++) {\n"
   "          if (String(contactData[_ci].number) === String(num)) {\n"
   "            contactData[_ci].stage = r.stage || stage;\n"
   "            contactData[_ci].vip = (r.vip !== undefined) ? !!r.vip : !!vip;\n"
   "            break;\n"
   "          }\n"
   "        }\n"
   "        if ($('#contactList') && $('#panel-kontak') && $('#panel-kontak').classList.contains('active')) renderContacts();"),
 ],
}
for f, reps in P.items():
    p = T + '/' + f; s = open(p, encoding='utf-8').read(); o = s
    for a, b in reps:
        if b in s: continue
        assert s.count(a) == 1, 'anchor tidak unik/tidak ada di ' + f + ': ' + a[:60]
        s = s.replace(a, b)
    if s != o:
        shutil.copy2(p, p + '.bak-v12106-' + stamp)
        open(p, 'w', encoding='utf-8').write(s); print('patched', f)
    else: print('sudah', f)
