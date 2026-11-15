#!/usr/bin/env python3
"""v1.2.179 tahap b (di atas patch_v12179.py): pemberitahuan juga untuk status tidak WORKING selain logout paksa.
- Tenant cron_tick (tiap ±5 menit): GET status tiap sesi WAHA. Tidak WORKING >= 10 menit (FAILED, STOPPED, STARTING macet,
  SCAN_QR_CODE, sesi hilang) -> deiWaDownNotify(status). Sekali per kejadian putus; WORKING lagi -> siap lagi.
  Dilewati: WAHA tak terjangkau (masalah gateway), nomor yang belum pernah tersambung, putus karena diputus dari dashboard.
- Logout paksa (webhook) tetap langsung, dan menandai kejadian supaya cron tidak mengirim dobel.
- Pusat: teks pesan menyesuaikan status.
Idempoten.  Pakai: patch_v12179b.py [~/Herd]"""
import os, sys, time, shutil
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
API = H + '/dei-tenant/api/index.php'; PB = H + '/dei-pusat/backend/index.php'
TAG = 'v1.2.179: notif-putus-wa'; TAGB = 'notif-putus-wa: tidak-working'; stamp = time.strftime('%Y%m%d-%H%M%S')
NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAGB in s: print('sudah:', p); return
    assert TAG in s, 'jalankan patch_v12179.py dulu: ' + p
    if not NOBAK: shutil.copy2(p, p + '.bak-v12179b-' + stamp)
    wr(p, fn(s)); print('OK', p)
C = '   // ' + TAGB

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.179');   // v1.2.179: notif-putus-wa — WA pemberitahuan ke pemilik saat nomor WAHA terputus (perlu scan ulang);",
               "define('DEI_VERSION', 'v1.2.179');   // v1.2.179: notif-putus-wa — WA pemberitahuan ke pemilik saat nomor WAHA terputus atau tidak WORKING >= 10 menit;", 'versi')
    s = rep(s, "        if ($kind === 'logout') deiWaDownNotify($label, (string)((whRead($ch)['num'] ?? '') ?: ($wa['waha_number'] ?? '')));   // v1.2.179: notif-putus-wa\n",
               "        if ($kind === 'logout') {   // v1.2.179: notif-putus-wa\n"
               "            deiWaDownNotify($label, (string)((whRead($ch)['num'] ?? '') ?: ($wa['waha_number'] ?? '')), 'SCAN_QR_CODE', time());\n"
               "            whUpdate($ch, function (&$x) { $dn = is_array($x['dn'] ?? null) ? $x['dn'] : []; $dn['since'] = (int)($dn['since'] ?? 0) ?: time(); $dn['sent'] = time(); $x['dn'] = $dn; });" + C + "\n"
               "        }\n", 'whAlert')
    s = rep(s, "function deiWaDownNotify($label, $num) {\n", "function deiWaDownNotify($label, $num, $status = 'SCAN_QR_CODE', $since = 0) {" + C + "\n", 'sig')
    s = rep(s, "                'phone' => waNormNum($s['wa_alert']['phone'] ?? ''), 'dashboard' => deiDashboardUrl()])]);\n",
               "                'phone' => waNormNum($s['wa_alert']['phone'] ?? ''), 'dashboard' => deiDashboardUrl(),\n"
               "                'status' => mb_substr((string)$status, 0, 20), 'since' => (int)$since])]);" + C + "\n", 'body')
    s = rep(s, "// Pasang ulang konfigurasi sesi (webhook + message.ack). PUT me-restart sesi WAHA beberapa detik.\n",
               "/* " + TAGB + ": cron — sesi WAHA tidak WORKING >= 10 menit -> WA pemberitahuan, sekali per kejadian.\n"
               " * Status dibaca langsung dari WAHA (tidak bergantung webhook). Gateway tak terjangkau / ditolak = dilewati. */\n"
               "function whDownCron($s) {\n"
               "    $out = [];\n"
               "    if (!empty($GLOBALS['dei_dry'])) return $out;\n"
               "    $chs = whChannels($s);\n"
               "    if (!$chs) return $out;\n"
               "    if (!is_dir(WA_HEALTH_DIR)) @mkdir(WA_HEALTH_DIR, 0755, true);\n"
               "    $mf = WA_HEALTH_DIR . '/down-cron.json';\n"
               "    if ((int)(readJson($mf, [])['at'] ?? 0) > time() - 240) return $out;   // tiap ±5 menit\n"
               "    writeJson($mf, ['at' => time()]);\n"
               "    foreach ($chs as $c) {\n"
               "        list($ch, $label, $conf) = $c;\n"
               "        if (trim((string)($conf['waha_url'] ?? '')) === '') continue;\n"
               "        list($code, $d) = wahaApi($conf, 'GET', '/api/sessions/' . rawurlencode(wahaSession($conf)));\n"
               "        if ($code === 404) $st = 'TIDAK ADA';\n"
               "        elseif ($code >= 200 && $code < 300) $st = strtoupper(trim((string)($d['status'] ?? '')));\n"
               "        else continue;\n"
               "        if ($st === '') continue;\n"
               "        $now = time(); $send = null;\n"
               "        whUpdate($ch, function (&$x) use ($st, $now, $conf, &$send) {\n"
               "            $dn = is_array($x['dn'] ?? null) ? $x['dn'] : [];\n"
               "            if ($st === 'WORKING') { $x['dn'] = ['ok_at' => $now]; return; }\n"
               "            if (empty($dn['since'])) $dn['since'] = ((string)($x['st'] ?? '') === $st && (int)($x['st_at'] ?? 0) > 0) ? (int)$x['st_at'] : $now;\n"
               "            $lastOk = (int)($dn['ok_at'] ?? 0);\n"
               "            foreach ((array)($x['ev'] ?? []) as $e) if ((string)($e[1] ?? '') === 'WORKING') $lastOk = max($lastOk, (int)($e[0] ?? 0));\n"
               "            $paired = $lastOk > 0 || (string)($x['num'] ?? '') !== '' || waNormNum($conf['waha_number'] ?? '') !== '';\n"
               "            $man = (int)($x['mk']['manual_at'] ?? 0);\n"
               "            $manual = $man > 0 && $man >= $lastOk - 60;   // diputus dari dashboard\n"
               "            if ($paired && !$manual && empty($dn['sent']) && $now - (int)$dn['since'] >= 600) {\n"
               "                $dn['sent'] = $now; $send = [(string)($x['num'] ?? ''), (int)$dn['since']];\n"
               "            }\n"
               "            $dn['st'] = $st; $x['dn'] = $dn;\n"
               "        });\n"
               "        if ($send) { deiWaDownNotify($label, $send[0] !== '' ? $send[0] : (string)($conf['waha_number'] ?? ''), $st, $send[1]); $out[] = $ch . ':' . $st; }\n"
               "    }\n"
               "    return $out;\n"
               "}\n"
               "// Pasang ulang konfigurasi sesi (webhook + message.ack). PUT me-restart sesi WAHA beberapa detik.\n", 'fungsi cron')
    s = rep(s, "        try { $whc = whEnsureCfgCron($s);",
               "        try { $whd = whDownCron($s); if ($whd) $r['wa_down'] = $whd; } catch (\\Throwable $e) { $r['err_wa_down'] = $e->getMessage(); }" + C + "\n"
               "        try { $whc = whEnsureCfgCron($s);", 'cron_tick')
    return s

def pusat(s):
    s = rep(s, "        $lbl = ($label !== '' && $label !== 'Nomor utama' && preg_replace('/\\D/', '', $label) !== $num) ? ' (' . $label . ')' : '';\n",
               "        $lbl = ($label !== '' && $label !== 'Nomor utama' && preg_replace('/\\D/', '', $label) !== $num) ? ' (' . $label . ')' : '';\n"
               "        $st = strtoupper(preg_replace('/[^A-Za-z_ ]/', '', (string)($body['status'] ?? 'SCAN_QR_CODE'))) ?: 'SCAN_QR_CODE';" + C + "\n"
               "        $stTxt = ['FAILED' => 'gagal tersambung (FAILED)', 'STOPPED' => 'berhenti (STOPPED)', 'STARTING' => 'macet saat menyambung (STARTING)', 'TIDAK ADA' => 'sesi tidak ditemukan'][$st] ?? $st;\n"
               "        $sinceTs = (int)($body['since'] ?? 0); $jam = $sinceTs > 0 ? ' sejak ' . gmdate('H:i', $sinceTs + 7 * 3600) . ' WIB' : '';\n", 'status')
    s = rep(s, "            suTelegram(\"Nomor WA{$numTxt}{$lbl} tenant {$name} ({$tid}) terputus (perlu scan QR ulang). Tidak ada nomor pemberitahuan pemilik.\");\n",
               "            suTelegram(\"Nomor WA{$numTxt}{$lbl} tenant {$name} ({$tid}) \" . ($st === 'SCAN_QR_CODE' ? 'terputus (perlu scan QR ulang)' : \"tidak tersambung: {$stTxt}{$jam}\") . \". Tidak ada nomor pemberitahuan pemilik.\");\n", 'tg')
    s = rep(s, "        $txt = \"⚠️ *Nomor WhatsApp chatbot {$name} terputus*{$lbl}\\n\\n\"\n"
               "             . \"WhatsApp melepas tautan nomor{$numTxt}, jadi bot berhenti membalas chat di nomor itu.\\n\\n\"\n"
               "             . \"Cara menyambungkan lagi: buka dashboard › Widget & API › Koneksi WhatsApp › *Hubungkan (scan QR)*, lalu scan dari HP nomor tersebut (WhatsApp › Perangkat Tertaut).\"\n",
               "        $txt = $st === 'SCAN_QR_CODE'\n"
               "             ? \"⚠️ *Nomor WhatsApp chatbot {$name} terputus*{$lbl}\\n\\n\"\n"
               "             . \"WhatsApp melepas tautan nomor{$numTxt}, jadi bot berhenti membalas chat di nomor itu.\\n\\n\"\n"
               "             . \"Cara menyambungkan lagi: buka dashboard › Widget & API › Koneksi WhatsApp › *Hubungkan (scan QR)*, lalu scan dari HP nomor tersebut (WhatsApp › Perangkat Tertaut).\"\n"
               "             : \"⚠️ *Nomor WhatsApp chatbot {$name} tidak tersambung*{$lbl}\\n\\n\"\n"
               "             . \"Nomor{$numTxt} berstatus {$stTxt}{$jam}, jadi bot tidak membalas chat di nomor itu.\\n\\n\"\n"
               "             . \"Coba buka dashboard › Widget & API › Koneksi WhatsApp › *Cek status*. Kalau tetap tidak tersambung, klik *Hubungkan (scan QR)* lalu scan ulang dari HP nomor tersebut.\";" + C + "\n"
               "        $txt .= \"\"\n", 'teks')
    return s

patch(API, api)
patch(PB, pusat)
