#!/usr/bin/env python3
"""v1.2.111: blokir-total — status lisensi 'blocked' (di atas suspended): seluruh URL tenant 403.
Pakai: python3 patch_v12111_blokir.py ~/Herd (idempoten)"""
import sys, os, shutil, time
D = os.path.dirname(os.path.abspath(__file__))
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd'); T = H + '/dei-tenant'
TAG = 'v1.2.111: blokir-total'
stamp = time.strftime('%Y%m%d-%H%M%S')
rd = lambda f: open(os.path.join(D, f), encoding='utf-8').read()
P = {
 'api/index.php': [
  ("define('DEI_VERSION', 'v1.2.110');   // v1.2.110: customer-feedback", "define('DEI_VERSION', 'v1.2.111');   // " + TAG),
  ("define('WEB_VISITOR_LIMIT', 5000);\n\nswitch ($action) {\n",
   "define('WEB_VISITOR_LIMIT', 5000);\n\n" + rd('blk_funcs.php') + "switch ($action) {\n\n" + rd('blk_case.php')),
  # efek samping suspended juga untuk blocked
  ("function applyStatusSideEffects($newStatus, $settings) {\n    if ($newStatus !== 'suspended') return;",
   "function applyStatusSideEffects($newStatus, $settings) {\n    if (!deiLicOff($newStatus)) return;   // v1.2.111: blocked juga"),
  # getLicenseStatus: transisi + sinkron blokir
  ("    if ($oldStatus !== 'suspended' && $newStatus === 'suspended') {\n        applyStatusSideEffects('suspended', $settings);\n    }\n    writeJson(LIC_CACHE_FILE, $newCache);\n",
   "    if (!deiLicOff($oldStatus) && deiLicOff($newStatus)) {   // v1.2.111\n        applyStatusSideEffects($newStatus, $settings);\n    }\n    writeJson(LIC_CACHE_FILE, $newCache);\n    deiSyncBlock($newStatus);   // v1.2.111: blokir-total\n"),
  ("        'stats'       => deiCollectStats(),   // v1.2.57\n    ]);",
   "        'stats'       => deiCollectStats(),   // v1.2.57\n        'lic_caps'    => ['blocked'],   // v1.2.111: paham status blocked\n    ]);"),
  # cek manual dari dashboard
  ("        writeJson(LIC_CACHE_FILE, $newCache);\n        if ($oldStatus !== 'suspended' && $newStatus === 'suspended') {\n            applyStatusSideEffects('suspended', $s);\n        }\n",
   "        writeJson(LIC_CACHE_FILE, $newCache);\n        if (!deiLicOff($oldStatus) && deiLicOff($newStatus)) {   // v1.2.111\n            applyStatusSideEffects($newStatus, $s);\n        }\n        deiSyncBlock($newStatus);   // v1.2.111: blokir-total\n"),
  ("            'api_url'      => deiSelfApiUrl(),   // v1.2.56: dipakai pusat untuk cron_tick\n",
   "            'api_url'      => deiSelfApiUrl(),   // v1.2.56: dipakai pusat untuk cron_tick\n            'lic_caps'     => ['blocked'],   // v1.2.111\n"),
  # penegakan chat: blocked = suspended
  ("    $lic = getLicenseStatus($s);\n    if (($lic['status'] ?? '') === 'suspended') return false;",
   "    $lic = getLicenseStatus($s);\n    if (deiLicOff($lic['status'] ?? '')) return false;   // v1.2.111"),
  ("    $lic = getLicenseStatus($s);\n    if ($lic['status'] === 'suspended') {\n        $answer",
   "    $lic = getLicenseStatus($s);\n    if (deiLicOff($lic['status'])) {   // v1.2.111\n        $answer"),
  ("        $lic = getLicenseStatus($s);\n        if ($lic['status'] === 'suspended') {\n            jsonOut(['ok' => true, 'answer'",
   "        $lic = getLicenseStatus($s);\n        if (deiLicOff($lic['status'])) {   // v1.2.111\n            jsonOut(['ok' => true, 'answer'"),
  # cron_tick: terima status dorongan pusat; tenant terblokir tidak menjalankan sweep
  ("        if (PHP_SAPI !== 'cli' && !empty($_SERVER['HTTP_X_DEI_FEATURES'])) deiApplyPushedFeatures($_SERVER['HTTP_X_DEI_FEATURES']);   // v1.2.60\n",
   "        if (PHP_SAPI !== 'cli' && !empty($_SERVER['HTTP_X_DEI_FEATURES'])) deiApplyPushedFeatures($_SERVER['HTTP_X_DEI_FEATURES']);   // v1.2.60\n"
   "        if (PHP_SAPI !== 'cli' && !empty($_SERVER['HTTP_X_DEI_LICENSE'])) deiApplyLicensePush($_SERVER['HTTP_X_DEI_LICENSE'], $s);   // v1.2.111: blokir-total\n"
   "        if (is_file(LIC_BLOCK_FLAG)) { deiHtaccessBlock(true); jsonOut(['ok' => true, 'version' => DEI_VERSION, 'blocked' => true, 'closed' => [], 'escalated' => []]); }\n"),
 ],
}
for f, reps in P.items():
    p = T + '/' + f; s = open(p, encoding='utf-8').read(); o = s
    for a, b in reps:
        if b in s: continue
        assert s.count(a) == 1, 'anchor tidak unik/tidak ada di ' + f + ' (' + str(s.count(a)) + '): ' + a[:70]
        s = s.replace(a, b)
    if s != o:
        shutil.copy2(p, p + '.bak-v12111-' + stamp)
        open(p, 'w', encoding='utf-8').write(s); print('patched', f)
    else: print('sudah', f)
