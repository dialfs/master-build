#!/usr/bin/env python3
"""v1.2.140 biaya-sa: perkiraan biaya scan chat lama (Topik & Divisi) hanya tampil untuk Super Admin. Idempoten.
Pakai: patch_v12140_biaya_sa.py [~/Herd/dei-tenant]"""
import os, sys, shutil, time
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.140: biaya-sa'; STAMP = time.strftime('%Y%m%d-%H%M%S'); done = set()
def rep(fp, a, b):
    s = open(fp, encoding='utf-8').read()
    if b in s: return
    assert s.count(a) == 1, (fp, s.count(a), a[:100])
    if fp not in done: shutil.copy2(fp, fp + '.bak-v12140-' + STAMP); done.add(fp)
    open(fp, 'w', encoding='utf-8').write(s.replace(a, b))
API = T + '/api/index.php'; A = T + '/dashboard/chatbot-ai/app.js'; H = T + '/dashboard/chatbot-ai/index.html'
rep(API, "define('DEI_VERSION', 'v1.2.139');   // v1.2.139: topik-riwayat", "define('DEI_VERSION', 'v1.2.140');   // " + TAG)
rep(API, """        if (!empty($in['estimate'])) jsonOut(['ok' => true, 'estimate' => tpBackfillStart($u['username'], $days, !empty($in['all']), true), 'quota' => tpQuota()]);""",
"""        $tpSa = ($u['role'] ?? '') === 'super_admin';   // """ + TAG + """: perkiraan biaya hanya untuk Super Admin
        if (!empty($in['estimate'])) { $tpE = tpBackfillStart($u['username'], $days, !empty($in['all']), true); if (!$tpSa) unset($tpE['cost_idr']); jsonOut(['ok' => true, 'estimate' => $tpE, 'quota' => tpQuota()]); }""")
rep(API, """        jsonOut(['ok' => true, 'backfill' => tpBackfillStart($u['username'], $days, !empty($in['all'])), 'quota' => tpQuota()]);""",
"""        $tpB = tpBackfillStart($u['username'], $days, !empty($in['all'])); if (!$tpSa) unset($tpB['cost_idr']);
        jsonOut(['ok' => true, 'backfill' => $tpB, 'quota' => tpQuota()]);""")
rep(A, """          'Memakai ' + fmt(e.take) + ' kuota · perkiraan biaya ±Rp' + fmt(e.cost_idr) + ' · selesai ±' + fmt(e.minutes) + ' menit.\\n\\nLanjutkan?';""",
       """          'Memakai ' + fmt(e.take) + ' kuota' + (e.cost_idr != null ? ' · perkiraan biaya ±Rp' + fmt(e.cost_idr) : '') + ' · selesai ±' + fmt(e.minutes) + ' menit.\\n\\nLanjutkan?';   // """ + TAG)
rep(H, '<script src="app.js?v=1.2.139"></script><!-- v1.2.139: topik-riwayat -->', '<script src="app.js?v=1.2.140"></script><!-- ' + TAG + ' -->')
print('patch v1.2.140 OK; file diubah:', len(done))
