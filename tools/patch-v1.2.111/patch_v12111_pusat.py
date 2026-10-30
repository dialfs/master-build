#!/usr/bin/env python3
"""v1.2.111: blokir-total — sisi pusat: status 'blocked' di admin, push langsung ke tenant, cron ikut membawa status.
Pakai: python3 patch_v12111_pusat.py ~/Herd (idempoten)"""
import sys, os, shutil, time
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd'); P = H + '/dei-pusat'
stamp = time.strftime('%Y%m%d-%H%M%S')
PUSH = r"""        writeJson(TENANTS_FILE, $tenants);
        // v1.2.111: blokir-total — dorong status ke tenant SEKARANG (tidak menunggu cache 24 jam)
        $push = ['ok' => false, 'error' => 'api_url tenant belum diketahui'];
        $pt = null;
        foreach ($tenants as $tt) if (tidEq($tt['tenant_id'] ?? '', $id)) { $pt = $tt; break; }
        $pUrl = trim((string)($pt['api_url'] ?? ''));
        if ($pUrl !== '') {
            $ch = curl_init($pUrl . (strpos($pUrl, '?') === false ? '?' : '&') . 'action=license_push');
            curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 12, CURLOPT_CONNECTTIMEOUT => 6,
                CURLOPT_FOLLOWLOCATION => true, CURLOPT_MAXREDIRS => 2, CURLOPT_POST => true, CURLOPT_POSTFIELDS => '',
                CURLOPT_HTTPHEADER => ['X-Tenant-Id: ' . tidNorm($pt['tenant_id']), 'X-License-Key: ' . ($pt['license_key'] ?? ''),
                    'User-Agent: DEI-Pusat/1.2.111',
                    'X-Dei-License: ' . json_encode(['status' => $status, 'message' => $msg, 'expires_at' => $expires], JSON_UNESCAPED_UNICODE)]]);
            $pr = curl_exec($ch); $pc = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
            $pj = json_decode((string)$pr, true);
            if ($pc === 200 && !empty($pj['ok'])) $push = ['ok' => true, 'blocked' => !empty($pj['blocked']), 'htaccess_ok' => $pj['htaccess_ok'] ?? null];
            elseif (is_array($pj) && ($pj['error'] ?? '') !== '') $push = ['ok' => false, 'error' => 'HTTP ' . $pc . ': ' . $pj['error']];
            else $push = ['ok' => false, 'error' => 'HTTP ' . $pc . ($pc === 400 || $pc === 404 ? ' (tenant belum v1.2.111 — berlaku saat cek lisensi berikutnya)' : '')];
        }
        jsonOut(['ok' => true, 'license_status' => $status, 'expires_at' => $expires, 'push' => $push]);
"""
R = {
 'backend/index.php': [
  ("        if (!in_array($status, ['active', 'expired', 'suspended'], true)) {\n            jsonOut(['ok' => false, 'error' => 'Status harus salah satu: active, expired, suspended.'], 400);",
   "        if (!in_array($status, ['active', 'expired', 'suspended', 'blocked'], true)) {   // v1.2.111: blocked\n            jsonOut(['ok' => false, 'error' => 'Status harus salah satu: active, expired, suspended, blocked.'], 400);"),
  ("        writeJson(TENANTS_FILE, $tenants);\n        jsonOut(['ok' => true, 'license_status' => $status, 'expires_at' => $expires]);\n", PUSH),
  ("            'license_status'   => $tenant['license_status']  ?? 'active',\n",
   "            // v1.2.111: tenant lama belum paham 'blocked' -> kirim 'suspended' (chat tetap mati)\n"
   "            'license_status'   => (($tenant['license_status'] ?? 'active') === 'blocked' && !in_array('blocked', (array)(bodyInput()['lic_caps'] ?? []), true)) ? 'suspended' : ($tenant['license_status'] ?? 'active'),\n"),
 ],
 'backend/cron-tick.php': [
  ("    if (empty($t['active']) || ($t['license_status'] ?? 'active') === 'suspended') continue;\n",
   "    $ctLic = (string)($t['license_status'] ?? 'active');\n"
   "    if (empty($t['active']) || $ctLic === 'suspended') continue;\n"
   "    // v1.2.111: blocked tetap di-tick (status ikut terdorong, tenant tidak menjalankan sweep) — kecuali tenant versi lama\n"
   "    if ($ctLic === 'blocked' && version_compare(ltrim((string)($t['current_version'] ?? 'v0'), 'v'), '1.2.111', '<')) continue;\n"),
  ("            'X-Dei-Latest: ' . $ctLatest,\n",
   "            'X-Dei-Latest: ' . $ctLatest,\n"
   "            'X-Dei-License: ' . json_encode(['status' => $ctLic, 'message' => (string)($t['suspend_message'] ?? ''), 'expires_at' => (string)($t['expires_at'] ?? '')], JSON_UNESCAPED_UNICODE),   // v1.2.111\n"),
 ],
 'admin/index.html': [
  ("const statusColors = {active:'#16a34a', expired:'#d97706', suspended:'#c4302b'};",
   "const statusColors = {active:'#16a34a', expired:'#d97706', suspended:'#c4302b', blocked:'#111827'};"),
  ("suspended:'SUSPENDED (chat mati + token klien dikosongkan)'};",
   "suspended:'SUSPENDED (chat mati + token klien dikosongkan)', blocked:'DIBLOKIR (seluruh URL tenant 403)'};"),
  ("          <option value=\"suspended\"  ${status==='suspended'?'selected':''}>suspended — chat mati, balas pesan kustom, token klien dikosongkan</option>\n",
   "          <option value=\"suspended\"  ${status==='suspended'?'selected':''}>suspended — chat mati, balas pesan kustom, token klien dikosongkan</option>\n"
   "          <option value=\"blocked\"    ${status==='blocked'?'selected':''}>blocked — BLOKIR TOTAL: dashboard, login, widget &amp; API tidak bisa dibuka sama sekali (403) + token dikosongkan</option>\n"),
  ("Untuk pulihkan: unsuspend dulu, lalu klien/Anda isi ulang token manual di dashboard tenant.</div>",
   "Untuk pulihkan: unsuspend dulu, lalu klien/Anda isi ulang token manual di dashboard tenant.<br><b>blocked</b> (v1.2.111+): semua URL tenant langsung menjawab 403 Forbidden, bot tidak membalas apa pun. Buka lagi = ubah ke active (langsung berlaku), lalu isi ulang token.</div>"),
  ("  if(newStatus === 'suspended'){\n",
   "  if(newStatus === 'blocked'){\n"
   "    if(!confirm('Yakin BLOKIR TOTAL tenant ini?\\n\\nSeluruh URL tenant (dashboard, login, widget, API) langsung tidak bisa dibuka (403 Forbidden), bot tidak membalas apa pun, dan token Claude/WA/Telegram klien DIKOSONGKAN.\\n\\nUntuk membuka: ubah status ke active, lalu isi ulang token.')) return;\n"
   "  }\n"
   "  if(newStatus === 'suspended'){\n"),
  ("    if(res.ok){ toast('Status diubah jadi ' + res.license_status); closeModal(); load(); }\n    else toast(res.error||'Gagal.',true);\n  });\n};\nwindow.applyTierPreset",
   "    if(res.ok){ const p=res.push||{}; toast('Status diubah jadi ' + res.license_status + (p.ok ? ' — langsung diterapkan di tenant' + (p.htaccess_ok===false?' (⚠ .htaccess tak bisa ditulis, hanya API yang terblokir)':'') : ' — tenant: ' + (p.error||'belum terjangkau')), !p.ok && res.license_status==='blocked'); closeModal(); load(); }\n    else toast(res.error||'Gagal.',true);\n  });\n};\nwindow.applyTierPreset"),
 ],
}
for f, reps in R.items():
    p = P + '/' + f; s = open(p, encoding='utf-8').read(); o = s
    for a, b in reps:
        if b in s: continue
        assert s.count(a) == 1, 'anchor tidak unik/tidak ada di ' + f + ' (' + str(s.count(a)) + '): ' + a[:70]
        s = s.replace(a, b)
    if s != o:
        shutil.copy2(p, p + '.bak-v12111-' + stamp)
        open(p, 'w', encoding='utf-8').write(s); print('patched', f)
    else: print('sudah', f)
