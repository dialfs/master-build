#!/usr/bin/env python3
"""v1.2.155 statistik-kontak — kartu Kontak WhatsApp (baru/aktif/percakapan/unik) hari ini/minggu ini/bulan ini,
dan label lama 'Percakapan' (yang sebenarnya jumlah pesan) diganti 'Pesan'. Idempoten. Pakai: patch_v12155.py <dei-tenant>"""
import sys, shutil, time
T = sys.argv[1]; TAG = 'v1.2.155: statistik-kontak'
A = T + '/api/index.php'; H = T + '/dashboard/chatbot-ai/index.html'; J = T + '/dashboard/chatbot-ai/app.js'
api, ht, js = (open(p, encoding='utf-8').read() for p in (A, H, J))
if all(TAG in s for s in (api, ht, js)):
    print('sudah dipatch'); sys.exit(0)
stamp = time.strftime('%Y%m%d-%H%M%S')
for p in (A, H, J): shutil.copy2(p, p + '.bak-v12155-' + stamp)
def rep(s, old, new, cnt=1):
    n = s.count(old); assert n == cnt, f'anchor {n}x (harus {cnt}): {old[:90]!r}'
    return s.replace(old, new)

# ---------------- API ----------------
api = rep(api, "define('DEI_VERSION', 'v1.2.154');   // v1.2.154: hp-firm",
               "define('DEI_VERSION', 'v1.2.155');   // " + TAG)
api = rep(api, "    return $t === false ? null : $t - 7 * 3600;\n}\n",
r"""    return $t === false ? null : $t - 7 * 3600;
}
/* """ + TAG + r""" — kontak WhatsApp per periode WIB (hari ini / minggu ini mulai Senin / bulan ini).
 *  new           : nomor yang chat di periode ini & pertama kali terlihat (first_seen kontak) di periode ini
 *  active        : nomor yang ada interaksi apa pun (pesan pelanggan, balasan bot/agent, closing, telepon)
 *  conversations : percakapan yang DIBUKA di periode ini (mesin percakapan v1.2.101)
 *  unique        : nomor unik yang mengirim pesan (chat) di periode ini
 * Sumber: log (terpangkas log_limit) + record percakapan (tidak terpangkas), digabung. */
function deiContactStats($logs) {
    $now = time();
    $day = wibDayStart(wibToday($now));
    $per = ['today' => $day, 'week' => $day - ((int)wibDate('N', $now) - 1) * 86400, 'month' => wibDayStart(wibDate('Y-m-01', $now))];
    $minTs = min($per);
    $act = []; $chat = []; $conv = [];
    foreach ($per as $k => $_) { $act[$k] = []; $chat[$k] = []; $conv[$k] = 0; }
    foreach ((array)$logs as $e) {
        if (!is_array($e) || ($e['channel'] ?? '') !== 'whatsapp') continue;
        $num = waNormNum($e['ip'] ?? ''); if ($num === '') continue;
        $t = strtotime((string)($e['ts'] ?? '')); if ($t === false || $t < $minTs) continue;
        $in = in_array((string)($e['dir'] ?? ''), ['', 'in'], true) && trim((string)($e['q'] ?? '')) !== '';
        foreach ($per as $k => $st) {
            if ($t < $st) continue;
            $act[$k][$num] = 1;
            if ($in) $chat[$k][$num] = 1;
        }
    }
    try { $recs = convStoreRange($minTs - CONV_EXPIRE_SEC, $now); } catch (\Throwable $e) { $recs = []; }
    foreach ((array)$recs as $c) {
        if (!is_array($c)) continue;
        $num = waNormNum($c['num'] ?? ''); if ($num === '') continue;
        $op = (int)($c['opened_at'] ?? 0); $la = max($op, (int)($c['last_at'] ?? 0));
        foreach ($per as $k => $st) {
            if ($op >= $st) {
                $conv[$k]++;
                if ((int)($c['guest_msgs'] ?? 0) > 0 && (string)($c['origin'] ?? '') !== 'outbound') $chat[$k][$num] = 1;
            }
            if ($la >= $st) $act[$k][$num] = 1;
        }
    }
    try { $contacts = waGetContacts(); } catch (\Throwable $e) { $contacts = []; }
    $out = [];
    foreach ($per as $k => $st) {
        $new = 0;
        foreach ($chat[$k] as $num => $_) {
            $fs = isset($contacts[$num]['first_seen']) ? strtotime((string)$contacts[$num]['first_seen']) : false;
            if ($fs === false || $fs >= $st) $new++;
        }
        $out[$k] = ['from' => wibDate('Y-m-d', $st), 'new' => $new, 'active' => count($act[$k] + $chat[$k]),
                    'conversations' => $conv[$k], 'unique' => count($chat[$k])];
    }
    return $out;
}
""")
api = rep(api, "            'range' => ['from' => $from, 'to' => $to, 'channel' => $chFilter],\n",
               "            'range' => ['from' => $from, 'to' => $to, 'channel' => $chFilter],\n"
               "            'contacts' => deiContactStats($logs),   // " + TAG + "\n")

# ---------------- HTML ----------------
ht = rep(ht, '<script src="app.js?v=1.2.154"></script><!-- v1.2.154: hp-firm -->',
             '<script src="app.js?v=1.2.155"></script><!-- ' + TAG + ' -->')
ht = rep(ht, '/* v1.2.154: hp-firm: layar HP tidak geser ke samping / mantul */\n',
    '/* ' + TAG + ' */\n'
    '.cs-head{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;margin-bottom:14px}\n'
    '.cs-head h3{margin:0}.cs-head .desc{margin:3px 0 0}\n'
    '#contactCards{margin-bottom:0}\n'
    '.stat .h{color:var(--muted);font-size:11.5px;margin-top:6px;line-height:1.35;opacity:.85}\n'
    '@media (max-width:860px){#contactCards{grid-template-columns:1fr 1fr}}\n'
    '/* v1.2.154: hp-firm: layar HP tidak geser ke samping / mantul */\n')
ht = rep(ht, '      <div class="card">\n        <div class="toolbar">\n          <div class="row"><label class="fl">Dari tanggal</label><input type="date" id="repFrom">',
    '      <div class="card" id="contactStats" style="display:none"><!-- ' + TAG + ' -->\n'
    '        <div class="cs-head">\n'
    '          <div><h3>Kontak WhatsApp</h3><div class="desc" id="csDesc">Tidak terpengaruh filter tanggal di bawah.</div></div>\n'
    '          <div class="lg-presets" id="csPresets" style="margin:0"><button type="button" data-p="today">Hari ini</button><button type="button" data-p="week">Minggu ini</button><button type="button" data-p="month">Bulan ini</button></div>\n'
    '        </div>\n'
    '        <div class="stats" id="contactCards"></div>\n'
    '      </div>\n\n'
    '      <div class="card">\n        <div class="toolbar">\n          <div class="row"><label class="fl">Dari tanggal</label><input type="date" id="repFrom">')
ht = rep(ht, '<div class="desc">Proporsi percakapan menurut source / medium (UTM).</div>',
             '<div class="desc">Proporsi pesan menurut source / medium (UTM).</div>')
ht = rep(ht, '<div class="desc">Percakapan &amp; pengunjung unik per hari.</div>',
             '<div class="desc">Pesan &amp; pengunjung unik per hari (1 pesan = 1 tanya-jawab).</div>')

# ---------------- JS ----------------
js = rep(js, "  function loadReports() {\n",
r"""  /* """ + TAG + r""" — kartu Kontak WhatsApp */
  var csData = null, csPer = 'today', csWired = false;
  try { var _cp = localStorage.getItem('dei_cs_per'); if (['today', 'week', 'month'].indexOf(_cp) !== -1) csPer = _cp; } catch (e) {}
  function csCard(v, l, h) { return '<div class="stat"><div class="v">' + v + '</div><div class="l">' + l + '</div><div class="h">' + h + '</div></div>'; }
  function csRender() {
    var wrap = $('#contactStats'), box = $('#contactCards');
    if (!wrap || !box) return;
    if (!csData) { wrap.style.display = 'none'; return; }
    wrap.style.display = '';
    if (!csWired) {
      csWired = true;
      $$('#csPresets button').forEach(function (b) {
        b.addEventListener('click', function () {
          csPer = b.getAttribute('data-p');
          try { localStorage.setItem('dei_cs_per', csPer); } catch (e) {}
          csRender();
        });
      });
    }
    var d = csData[csPer] || {}, w = { today: 'hari ini', week: 'minggu ini', month: 'bulan ini' }[csPer];
    var n = function (v) { return (+v || 0).toLocaleString('id-ID'); };
    box.innerHTML =
      csCard(n(d['new']), 'Kontak Baru', 'Nomor yang pertama kali chat ' + w) +
      csCard(n(d.active), 'Kontak Aktif', 'Nomor yang berinteraksi ' + w + ' (pelanggan, bot, atau agent)') +
      csCard(n(d.conversations), 'Percakapan', 'Percakapan WhatsApp yang dimulai ' + w) +
      csCard(n(d.unique), 'Kontak Unik', 'Nomor WhatsApp unik yang mengirim chat ' + w);
    $$('#csPresets button').forEach(function (b) { b.classList.toggle('on', b.getAttribute('data-p') === csPer); });
    var desc = $('#csDesc');
    if (desc) desc.textContent = (csPer === 'today' ? '' : 'Sejak ' + d.from + '. ') + 'Tidak terpengaruh filter tanggal di bawah.';
  }

  function loadReports() {
""")
js = rep(js, "        statCard(s.total, 'Total Percakapan') +\n        statCard(s.today, 'Hari Ini') +",
             "        statCard(s.total, 'Total Pesan') +          // " + TAG + ": dulu 'Total Percakapan' (isinya jumlah pesan)\n"
             "        statCard(s.today, 'Pesan Hari Ini') +")
js = rep(js, "        statCard(s.unique_ips, 'Pengunjung Unik');\n",
             "        statCard(s.unique_ips, 'Pengunjung Unik');\n      csData = res.contacts || null; csRender();   // " + TAG + "\n")
js = rep(js, "display:inline-block\"></span>Percakapan</span>' +",
             "display:inline-block\"></span>Pesan</span>' +")
for p, s in ((A, api), (H, ht), (J, js)): open(p, 'w', encoding='utf-8').write(s)
print('OK', TAG)
