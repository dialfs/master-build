#!/usr/bin/env python3
"""v1.2.179 tahap c (di atas patch_v12179b.py): pengingat 1x sehari selama nomor masih belum WORKING (maks 7 pengingat).
Tenant whDownCron: dn.sent >= 24 jam lalu & masih tidak WORKING -> kirim lagi dengan reminder=n. Pusat: teks pengingat.
Idempoten.  Pakai: patch_v12179c.py [~/Herd]"""
import os, sys, time, shutil
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
API = H + '/dei-tenant/api/index.php'; PB = H + '/dei-pusat/backend/index.php'
NEED = 'notif-putus-wa: tidak-working'; TAGC = 'notif-putus-wa: pengingat'; stamp = time.strftime('%Y%m%d-%H%M%S')
NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAGC in s: print('sudah:', p); return
    assert NEED in s, 'jalankan patch_v12179b.py dulu: ' + p
    if not NOBAK: shutil.copy2(p, p + '.bak-v12179c-' + stamp)
    wr(p, fn(s)); print('OK', p)
C = '   // ' + TAGC

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.179');   // v1.2.179: notif-putus-wa — WA pemberitahuan ke pemilik saat nomor WAHA terputus atau tidak WORKING >= 10 menit;",
               "define('DEI_VERSION', 'v1.2.179');   // v1.2.179: notif-putus-wa — WA pemberitahuan ke pemilik saat nomor WAHA terputus atau tidak WORKING >= 10 menit, pengingat 1x sehari;", 'versi')
    s = rep(s, "function deiWaDownNotify($label, $num, $status = 'SCAN_QR_CODE', $since = 0) {",
               "function deiWaDownNotify($label, $num, $status = 'SCAN_QR_CODE', $since = 0, $reminder = 0) {", 'sig')
    s = rep(s, "                'status' => mb_substr((string)$status, 0, 20), 'since' => (int)$since])]);",
               "                'status' => mb_substr((string)$status, 0, 20), 'since' => (int)$since, 'reminder' => (int)$reminder])]);", 'body')
    s = rep(s, "            if ($paired && !$manual && empty($dn['sent']) && $now - (int)$dn['since'] >= 600) {\n"
               "                $dn['sent'] = $now; $send = [(string)($x['num'] ?? ''), (int)$dn['since']];\n"
               "            }\n",
               "            if ($paired && !$manual && empty($dn['sent']) && $now - (int)$dn['since'] >= 600) {\n"
               "                $dn['sent'] = $now; $send = [(string)($x['num'] ?? ''), (int)$dn['since'], 0];\n"
               "            } elseif ($paired && !$manual && !empty($dn['sent']) && $now - (int)$dn['sent'] >= 86400 - 600 && (int)($dn['rem'] ?? 0) < 7) {" + C + "\n"
               "                $dn['rem'] = (int)($dn['rem'] ?? 0) + 1; $dn['sent'] = $now; $send = [(string)($x['num'] ?? ''), (int)$dn['since'], $dn['rem']];\n"
               "            }\n", 'cron')
    s = rep(s, "$st, $send[1]); $out[] = $ch . ':' . $st; }",
               "$st, $send[1], $send[2]); $out[] = $ch . ':' . $st . ($send[2] ? ':r' . $send[2] : ''); }", 'call')
    return s

def pusat(s):
    s = rep(s, "        $sinceTs = (int)($body['since'] ?? 0); $jam = $sinceTs > 0 ? ' sejak ' . gmdate('H:i', $sinceTs + 7 * 3600) . ' WIB' : '';\n",
               "        $sinceTs = (int)($body['since'] ?? 0); $jam = $sinceTs > 0 ? ' sejak ' . gmdate('H:i', $sinceTs + 7 * 3600) . ' WIB' : '';\n"
               "        $rem = max(0, min(30, (int)($body['reminder'] ?? 0)));" + C + "\n"
               "        if ($rem && $sinceTs > 0) {\n"
               "            $bln = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];\n"
               "            $w = $sinceTs + 7 * 3600; $jam = ' sejak ' . gmdate('j', $w) . ' ' . $bln[(int)gmdate('n', $w)] . ' ' . gmdate('H:i', $w) . ' WIB';\n"
               "        }\n", 'rem')
    s = rep(s, "        if ($phone === '') {\n            suTelegram(",
               "        if ($phone === '' && $rem) jsonOut(['ok' => true, 'sent' => false, 'reason' => 'no_phone']);" + C + "\n"
               "        if ($phone === '') {\n            suTelegram(", 'tg')
    s = rep(s, "        $txt .= \"\"\n",
               "        if ($rem) {" + C + "\n"
               "            $hari = $sinceTs > 0 ? max(1, (int)floor(($now - $sinceTs) / 86400)) : $rem;\n"
               "            $txt = \"🔔 *Pengingat: nomor WhatsApp chatbot {$name} masih belum tersambung*{$lbl}\\n\\n\"\n"
               "                 . \"Nomor{$numTxt} belum tersambung{$jam} ({$hari} hari), jadi bot belum membalas chat di nomor itu.\\n\\n\"\n"
               "                 . \"Sambungkan lagi: buka dashboard › Widget & API › Koneksi WhatsApp › *Hubungkan (scan QR)*, lalu scan dari HP nomor tersebut (WhatsApp › Perangkat Tertaut).\";\n"
               "        }\n"
               "        $txt .= \"\"\n", 'teks')
    return s

patch(API, api)
patch(PB, pusat)
