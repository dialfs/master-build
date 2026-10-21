#!/usr/bin/env python3
"""v1.2.99 (pusat) — batas nomor WhatsApp tambahan per tenant (fitur max_wa_numbers).
- tenants.json: max_wa_numbers (0..20, bawaan 0 = tanpa nomor tambahan).
- Dikirim ke tenant lewat cap_info (check_update) dan header X-Dei-Features (cron_tick) -> berlaku <= 1 menit.
- set_seats / set_cap menerima max_wa_numbers (opsional). Stats tenant: seats.wa_numbers & max_wa_numbers.
- Panel admin: kolom Kursi Tim menampilkan "W terpakai/batas"; modal Kursi Tim punya isian Nomor WA tambahan.
Pemakaian: python3 patch_v1299_pusat_lisensi_nomor.py <root dei-pusat>   (idempoten; backup *.bak-v1299-*)"""
import sys, os, time, shutil
ROOT = sys.argv[1]
STAMP = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.99: lisensi-nomor'

def patch(rel, pairs):
    p = os.path.join(ROOT, rel)
    s = open(p, encoding='utf-8').read()
    if MARK in s: print('sudah dipatch:', rel); return
    for old, new in pairs:
        n = s.count(old)
        if n != 1: sys.exit(f'GAGAL {rel}: anchor {n}x:\n{old[:300]}')
        s = s.replace(old, new)
    shutil.copy2(p, p + '.bak-v1299-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s)
    print('OK', rel)

patch('backend/index.php', [
    ("                         'max_agents' => (int)($se['max_agents'] ?? 0), 'max_supervisors' => (int)($se['max_supervisors'] ?? 0),\n",
     "                         'max_agents' => (int)($se['max_agents'] ?? 0), 'max_supervisors' => (int)($se['max_supervisors'] ?? 0),\n"
     "                         'wa_numbers' => (int)($se['wa_numbers'] ?? 0), 'max_wa_numbers' => (int)($se['max_wa_numbers'] ?? 0),   // v1.2.99: lisensi-nomor\n"),
    ("                'topic_scan_quota'     => (int)($tenant['topic_scan_quota'] ?? 10),   // v1.2.68\n",
     "                'topic_scan_quota'     => (int)($tenant['topic_scan_quota'] ?? 10),   // v1.2.68\n"
     "                'max_wa_numbers'       => (int)($tenant['max_wa_numbers'] ?? 0),      // v1.2.99: lisensi-nomor (nomor WA tambahan)\n"),
    ("                'topic_scan_quota'  => 10,          // v1.2.68: scan topik AI / bulan (0 = tanpa batas)\n",
     "                'topic_scan_quota'  => 10,          // v1.2.68: scan topik AI / bulan (0 = tanpa batas)\n"
     "                'max_wa_numbers'    => 0,           // v1.2.99: lisensi-nomor — nomor WA tambahan (0 = tidak ada)\n"),
    # set_seats
    ("        if ($maxSpv < 0 || $maxSpv > 50) jsonOut(['ok' => false, 'error' => 'Maks. Supervisor harus 0..50 (0 = tanpa batas).'], 400);\n"
     "        $tenants = readJson(TENANTS_FILE, []);\n",
     "        if ($maxSpv < 0 || $maxSpv > 50) jsonOut(['ok' => false, 'error' => 'Maks. Supervisor harus 0..50 (0 = tanpa batas).'], 400);\n"
     "        $maxWa = array_key_exists('max_wa_numbers', $in) ? (int)$in['max_wa_numbers'] : null;   // v1.2.99: lisensi-nomor\n"
     "        if ($maxWa !== null && ($maxWa < 0 || $maxWa > 20)) jsonOut(['ok' => false, 'error' => 'Nomor WA tambahan harus 0..20.'], 400);\n"
     "        $tenants = readJson(TENANTS_FILE, []);\n"),
    ("                if (array_key_exists('white_label', $in)) $t['white_label'] = !empty($in['white_label']);\n",
     "                if (array_key_exists('white_label', $in)) $t['white_label'] = !empty($in['white_label']);\n"
     "                if ($maxWa !== null) $t['max_wa_numbers'] = $maxWa;   // v1.2.99\n"
     "                $maxWaOut = (int)($t['max_wa_numbers'] ?? 0);\n"),
    ("        jsonOut(['ok' => true, 'max_agents' => $maxAgents, 'max_supervisors' => $maxSpv]);\n",
     "        jsonOut(['ok' => true, 'max_agents' => $maxAgents, 'max_supervisors' => $maxSpv, 'max_wa_numbers' => $maxWaOut ?? 0]);   // v1.2.99\n"),
    # set_cap
    ("        if ($tsqIn !== null && ($tsqIn < 0 || $tsqIn > 1000)) jsonOut(['ok' => false, 'error' => 'Kuota scan topik harus 0..1000 (0 = tanpa batas).'], 400);\n",
     "        if ($tsqIn !== null && ($tsqIn < 0 || $tsqIn > 1000)) jsonOut(['ok' => false, 'error' => 'Kuota scan topik harus 0..1000 (0 = tanpa batas).'], 400);\n"
     "        $mwIn      = array_key_exists('max_wa_numbers', $in) ? (int)$in['max_wa_numbers'] : null;   // v1.2.99: lisensi-nomor\n"
     "        if ($mwIn !== null && ($mwIn < 0 || $mwIn > 20)) jsonOut(['ok' => false, 'error' => 'Nomor WA tambahan harus 0..20.'], 400);\n"),
    ("                if ($tsqIn !== null)     $t['topic_scan_quota'] = $tsqIn;   // v1.2.68\n",
     "                if ($tsqIn !== null)     $t['topic_scan_quota'] = $tsqIn;   // v1.2.68\n"
     "                if ($mwIn !== null)      $t['max_wa_numbers'] = $mwIn;      // v1.2.99\n"),
    ("'white_label' => $wlIn, 'topic_scan_quota' => $tsqIn]);\n",
     "'white_label' => $wlIn, 'topic_scan_quota' => $tsqIn, 'max_wa_numbers' => $mwIn]);   // v1.2.99\n"),
])

patch('backend/cron-tick.php', [
    ("'topic_scan_quota' => (int)($t['topic_scan_quota'] ?? 10), 'trial' => suTrialPayload($t)])],   // v1.2.90: trial\n",
     "'topic_scan_quota' => (int)($t['topic_scan_quota'] ?? 10), 'trial' => suTrialPayload($t),\n"
     "                'max_wa_numbers' => (int)($t['max_wa_numbers'] ?? 0)])],   // v1.2.90: trial; v1.2.99: lisensi-nomor\n"),
])

patch('backend/signup-lib.php', [
    ("                     'white_label' => false, 'topic_scan_quota' => (int)$cfg['topic_scan_quota'],\n",
     "                     'white_label' => false, 'topic_scan_quota' => (int)$cfg['topic_scan_quota'], 'max_wa_numbers' => 0,   // v1.2.99: lisensi-nomor\n"),
    ("            'topic_scan_quota' => (int)$cfg['topic_scan_quota'],\n            'install_path'",
     "            'topic_scan_quota' => (int)$cfg['topic_scan_quota'], 'max_wa_numbers' => 0,   // v1.2.99: lisensi-nomor\n            'install_path'"),
])

patch('admin/index.html', [
    ("  const sync = se && (se.max_agents !== ma || se.max_supervisors !== ms)\n",
     "  const mw = t.max_wa_numbers ?? 0;   // v1.2.99: lisensi-nomor — nomor WA tambahan (0 = tidak ada, bukan tanpa batas)\n"
     "  const wPart = (()=>{ const u = se && se.wa_numbers != null ? se.wa_numbers : null;\n"
     "    if (!mw && !u) return '';\n"
     "    const cls = u == null ? 'idle' : (u > mw ? 'off' : (u >= mw ? 'idle' : 'ok'));\n"
     "    return ` <span class=\"badge ${cls}\" title=\"Nomor WhatsApp tambahan terpakai / batas paket\">W ${u == null ? '–' : u}/${mw}</span>`; })();\n"
     "  const sync = se && (se.max_agents !== ma || se.max_supervisors !== ms || (se.max_wa_numbers != null && se.max_wa_numbers !== mw))\n"),
    ("${part(se?se.agents:null, ma, 'A')} ${part(se?se.supervisors:null, ms, 'S')}${sync}</a>`;\n",
     "${part(se?se.agents:null, ma, 'A')} ${part(se?se.supervisors:null, ms, 'S')}${wPart}${sync}</a>`;\n"),
    ("          <div style=\"flex:1\"><label>Maks. Supervisor</label><input id=\"s_max_spv\" type=\"number\" min=\"0\" max=\"50\" value=\"${t.max_supervisors ?? 1}\"></div>\n        </div>\n",
     "          <div style=\"flex:1\"><label>Maks. Supervisor</label><input id=\"s_max_spv\" type=\"number\" min=\"0\" max=\"50\" value=\"${t.max_supervisors ?? 1}\"></div>\n        </div>\n"
     "        <div class=\"row\" style=\"gap:8px;margin-top:8px\"><!-- v1.2.99: lisensi-nomor -->\n"
     "          <div style=\"flex:1\"><label>Nomor WA tambahan</label><input id=\"s_max_wa\" type=\"number\" min=\"0\" max=\"20\" value=\"${t.max_wa_numbers ?? 0}\"></div>\n"
     "          <div style=\"flex:1;align-self:end\" class=\"hint\">Di luar nomor utama. 0 = tidak ada. ${se && se.wa_numbers != null ? 'Terpakai: <b>' + se.wa_numbers + '</b>.' : 'Pemakaian tampil setelah tenant v1.2.99.'} Nomor yang terakhir ditambahkan terkunci lebih dulu bila batas diturunkan.</div>\n"
     "        </div>\n"),
    ("  const a = parseInt($('#s_max_agents').value, 10), s = parseInt($('#s_max_spv').value, 10);\n",
     "  const a = parseInt($('#s_max_agents').value, 10), s = parseInt($('#s_max_spv').value, 10), w = parseInt($('#s_max_wa').value, 10);   // v1.2.99\n"
     "  if(isNaN(w) || w<0 || w>20){ toast('Nomor WA tambahan harus 0..20.',true); return; }\n"),
    ("  api('set_seats',{method:'POST',body:{tenant_id:id, max_agents:a, max_supervisors:s}}).then(res=>{\n"
     "    if(res.ok){ toast('Kursi tersimpan: '+res.max_agents+' agent / '+res.max_supervisors+' supervisor'); closeModal(); load(); }\n",
     "  api('set_seats',{method:'POST',body:{tenant_id:id, max_agents:a, max_supervisors:s, max_wa_numbers:w}}).then(res=>{\n"
     "    if(res.ok){ toast('Tersimpan: '+res.max_agents+' agent / '+res.max_supervisors+' supervisor / '+res.max_wa_numbers+' nomor WA tambahan'); closeModal(); load(); }\n"),
    ("<th title=\"Akun terpakai / batas kursi paket. Klik untuk mengubah.\">Kursi Tim</th>",
     "<th title=\"Akun terpakai / batas kursi paket (A = WA Agent, S = Supervisor, W = nomor WA tambahan). Klik untuk mengubah.\">Kursi Tim</th>"),
])
print('selesai')
