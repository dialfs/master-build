#!/usr/bin/env python3
"""v1.2.104: skor-risiko-wa — skor risiko suspend per nomor WhatsApp (WAHA), heuristik 0–100.
Tenant: pengumpulan data (pesan masuk/keluar per jam, chat duluan, teks kembar, message.ack, session.status),
skor di cron_tick tiap 15 menit, panel Kesehatan di kartu Nomor WhatsApp, push admin saat Bahaya / logout paksa.
Pusat: skor ikut statistik cron, lencana di tabel tenant + rincian, Telegram saat nomor masuk Bahaya.
Idempoten. Pakai: patch_v12104_skor_wa.py <Herd>   (blok kode dibaca dari folder skrip ini)"""
import sys, os, time, shutil
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd'); T = H + '/dei-tenant'; P = H + '/dei-pusat'
D = os.path.dirname(os.path.abspath(__file__))
TAG = 'v1.2.104: skor-risiko-wa'
st = time.strftime('%Y%m%d-%H%M%S')
blk = lambda f: open(os.path.join(D, f), encoding='utf-8').read()

def patch(path, pairs):
    s = open(path, encoding='utf-8').read()
    if TAG in s: print('sudah:', path); return
    shutil.copy2(path, path + '.bak-v12104-' + st)
    for old, new in pairs:
        c = s.count(old); assert c == 1, (path, c, old[:100])
        s = s.replace(old, new)
    assert TAG in s, ('tag tidak masuk', path)
    open(path, 'w', encoding='utf-8').write(s); print('patched:', path)

# ---------------- dei-tenant/api/index.php ----------------
patch(T + '/api/index.php', [
 ("define('DEI_VERSION', 'v1.2.103');", "define('DEI_VERSION', 'v1.2.104');"),
 ("            'events'  => ['message.any', 'session.status'],",
  "            'events'  => ['message.any', 'session.status', 'message.ack'],   // v1.2.104: skor-risiko-wa (centang)"),
 ("function waSendWaha($wa, $to, $text) {", blk('block_wa_health.php') + "function waSendWaha($wa, $to, $text) {"),
 # kirim teks WAHA: catat hasil
 ("""    list($c, $d) = wahaApi($wa, 'POST', '/api/sendText', ['session' => wahaSession($wa), 'chatId' => $to . '@c.us', 'text' => $text]);
    if ($c >= 200 && $c < 300) {
        $id = is_array($d) ? wahaMsgId($d) : '';
        if ($id !== '') wahaRememberSent($to, $id, '');
        return true;
    }
    $GLOBALS['wa_last_error'] = wahaErr($c, $d, 'Kirim lewat WAHA gagal.');""",
  """    list($c, $d) = wahaApi($wa, 'POST', '/api/sendText', ['session' => wahaSession($wa), 'chatId' => $to . '@c.us', 'text' => $text]);
    if ($c >= 200 && $c < 300) {
        $id = is_array($d) ? wahaMsgId($d) : '';
        if ($id !== '') wahaRememberSent($to, $id, '');
        whOut($wa, $to, (string)($GLOBALS['dei_out_src'] ?? 'bot'), true, $id, $text);   // v1.2.104: skor-risiko-wa
        return true;
    }
    whOut($wa, $to, (string)($GLOBALS['dei_out_src'] ?? 'bot'), false);   // v1.2.104
    $GLOBALS['wa_last_error'] = wahaErr($c, $d, 'Kirim lewat WAHA gagal.');"""),
 # kirim foto WAHA
 ("        if ($c >= 200 && $c < 300) { $id = is_array($d) ? wahaMsgId($d) : ''; if ($id !== '') wahaRememberSent($to, $id, ''); return true; }\n        $GLOBALS['wa_last_error'] = wahaErr($c, $d, 'Kirim foto lewat WAHA gagal.');",
  "        if ($c >= 200 && $c < 300) { $id = is_array($d) ? wahaMsgId($d) : ''; if ($id !== '') wahaRememberSent($to, $id, ''); whOut($wa, $to, (string)($GLOBALS['dei_out_src'] ?? 'bot'), true, $id, ''); return true; }   // v1.2.104\n        whOut($wa, $to, (string)($GLOBALS['dei_out_src'] ?? 'bot'), false);\n        $GLOBALS['wa_last_error'] = wahaErr($c, $d, 'Kirim foto lewat WAHA gagal.');"),
 # echo HP & pesan masuk
 ("""        if (($p['source'] ?? '') === 'api' || wahaSentByUs($num, $id, $body)) return null;
        if (in_array($type, deiWaMediaTypes(), true)) {   // v1.2.94: wa-media""",
  """        if (($p['source'] ?? '') === 'api' || wahaSentByUs($num, $id, $body)) return null;
        whOut($wa, $num, 'hp', true, $id, $body);   // v1.2.104: skor-risiko-wa — diketik dari HP
        if (in_array($type, deiWaMediaTypes(), true)) {   // v1.2.94: wa-media"""),
 ("    $msg = ['from' => $num, 'id' => $id, 'type' => $type];",
  "    whIn($wa, $num);   // v1.2.104: skor-risiko-wa\n    $msg = ['from' => $num, 'id' => $id, 'type' => $type];"),
 # webhook: session.status & message.ack
 ("        if (!in_array((string)($evt['event'] ?? ''), ['message', 'message.any'], true)) { echo 'OK'; exit; }",
  """        // v1.2.104: skor-risiko-wa — status sesi & centang untuk skor kesehatan nomor
        if ((string)($evt['event'] ?? '') === 'session.status') { whStatus($wa, $evt); echo 'OK'; exit; }
        if ((string)($evt['event'] ?? '') === 'message.ack') { whAck($wa, is_array($evt['payload'] ?? null) ? $evt['payload'] : []); echo 'OK'; exit; }
        if (!in_array((string)($evt['event'] ?? ''), ['message', 'message.any'], true)) { echo 'OK'; exit; }"""),
 # sesi baru dibuat dengan config terbaru
 ("        if (empty($d['status'])) $d['status'] = 'STARTING';",
  "        if (empty($d['status'])) $d['status'] = 'STARTING';\n        whMark($wa, 'cfg_at');   // v1.2.104: config sudah berlangganan message.ack"),
 # waha_conn: logout manual & pasang webhook = bukan sinyal risiko
 ("            list($c, $d) = wahaApi($wa, 'POST', '/api/sessions/' . $sp . '/logout');",
  "            whMark($wa, 'manual_at');   // v1.2.104: logout dari dashboard bukan logout paksa\n            list($c, $d) = wahaApi($wa, 'POST', '/api/sessions/' . $sp . '/logout');"),
 ("            if ((string)($wa['waha_webhook_key'] ?? '') === '') jsonOut(['ok' => false, 'error' => 'Kunci webhook belum ada — simpan pengaturan dengan penyedia WAHA dulu.'], 400);",
  "            if ((string)($wa['waha_webhook_key'] ?? '') === '') jsonOut(['ok' => false, 'error' => 'Kunci webhook belum ada — simpan pengaturan dengan penyedia WAHA dulu.'], 400);\n            whMark($wa, 'cfg_at');   // v1.2.104: restart karena PUT bukan sinyal risiko"),
 # balasan agent dari dashboard
 ("        if (!waSend($wa, $num, $text)) {",
  "        $GLOBALS['dei_out_src'] = 'agent';   // v1.2.104: skor-risiko-wa\n        if (!waSend($wa, $num, $text)) {"),
 # cron
 ("        try { $r['routed'] = deiRouteDrain(20, $s); } catch (\\Throwable $e) { $r['err_routing'] = $e->getMessage(); }   // v1.2.100: routing",
  "        try { $r['routed'] = deiRouteDrain(20, $s); } catch (\\Throwable $e) { $r['err_routing'] = $e->getMessage(); }   // v1.2.100: routing\n"
  "        try { $whc = whEnsureCfgCron($s); if ($whc) $r['wa_health_cfg'] = $whc; $whs = whScoreAll($s, false); if ($whs) $r['wa_health'] = count($whs['nums'] ?? []); } catch (\\Throwable $e) { $r['err_wa_health'] = $e->getMessage(); }   // v1.2.104: skor-risiko-wa"),
 # statistik ke pusat
 ("        'topic_scans'           => (function () {",
  "        'wa_health'             => (function () { try { return whStatsSummary(); } catch (\\Throwable $e) { return null; } })(),   // v1.2.104: skor-risiko-wa\n        'topic_scans'           => (function () {"),
 # action
 ("    case 'wa_numbers': {", blk('block_wa_health_action.php') + "    case 'wa_numbers': {"),
 ("                     'channels' => waChannels($s), 'numbers' => $rows]);",
  "                     'channels' => waChannels($s), 'numbers' => $rows,\n                     'health' => whOn($wa) ? (object)(readJson(WA_HEALTH_SCORE_FILE, [])['nums'] ?? []) : null]);   // v1.2.104: skor-risiko-wa"),
])

# ---------------- dashboard app.js ----------------
patch(T + '/dashboard/chatbot-ai/app.js', [
 ("  function wnLoad() {", blk('block_wa_health.js').replace('/* v1.2.104: skor-risiko-wa', '/* ' + TAG, 1) + "  function wnLoad() {"),
 ("      _wn.teams = r.teams || [];   // v1.2.100: routing",
  "      _wn.teams = r.teams || [];   // v1.2.100: routing\n      var _wh = r.health || {};   // v1.2.104: skor-risiko-wa"),
 ("<th>Tim</th><th></th></tr></thead><tbody>' +   // v1.2.100: routing",
  "<th>Tim</th>' + (waha ? '<th>Kesehatan</th>' : '') + '<th></th></tr></thead><tbody>' +   // v1.2.100: routing; v1.2.104: kesehatan"),
 ("'<td class=\"mono\" style=\"font-size:12px\">' + esc(idc) + '</td><td style=\"font-size:12px\">' + (x.team ? esc(_tn[x.team] || x.team) : '<span style=\"color:var(--muted)\">Semua</span>') + '</td><td style=\"white-space:nowrap;text-align:right\">' + acts + '</td></tr>';",
  "'<td class=\"mono\" style=\"font-size:12px\">' + esc(idc) + '</td><td style=\"font-size:12px\">' + (x.team ? esc(_tn[x.team] || x.team) : '<span style=\"color:var(--muted)\">Semua</span>') + '</td>' + (waha ? '<td>' + (x.locked ? '' : whBadge(_wh[x.id], x.id)) + '</td>' : '') + '<td style=\"white-space:nowrap;text-align:right\">' + acts + '</td></tr>';"),
 ("        else if (b.dataset.wn === 'qr') wnConnect(row);",
  "        else if (b.dataset.wn === 'qr') wnConnect(row);\n        else if (b.dataset.wn === 'health') whOpen(row);   // v1.2.104"),
])

# ---------------- dashboard index.html ----------------
patch(T + '/dashboard/chatbot-ai/index.html', [
 ("        <div id=\"wn_list\"></div>",
  "        <div id=\"wn_list\"></div>\n        <div id=\"wn_health\" class=\"hide\" style=\"border:1px solid var(--line,#e6e6ef);border-radius:10px;padding:14px;margin-top:10px\"></div><!-- v1.2.104: skor-risiko-wa -->"),
 ('<script src="app.js?v=1.2.101"></script><!-- v1.2.101: percakapan -->', '<script src="app.js?v=1.2.104"></script><!-- v1.2.104: skor-risiko-wa -->'),
])

# ---------------- dei-pusat ----------------
patch(P + '/backend/index.php', [
 ("""    // v1.2.68: pemakaian kuota scan topik bulan ini
    if (is_array($in['topic_scans'] ?? null)) {""",
  """    // v1.2.104: skor-risiko-wa — skor kesehatan nomor WAHA (tanpa isi chat)
    if (is_array($in['wa_health']['nums'] ?? null)) {
        $nums = [];
        foreach (array_slice($in['wa_health']['nums'], 0, 21) as $n) {
            if (!is_array($n)) continue;
            $nums[] = ['ch' => substr(preg_replace('/[^A-Za-z0-9_]/', '', (string)($n['ch'] ?? '')), 0, 20),
                       'label' => mb_substr(strip_tags((string)($n['label'] ?? '')), 0, 40),
                       'number' => substr(preg_replace('/\\D/', '', (string)($n['number'] ?? '')), 0, 16),
                       'score' => max(0, min(100, (int)($n['score'] ?? 0))),
                       'level' => in_array(($n['level'] ?? ''), ['aman', 'waspada', 'bahaya'], true) ? $n['level'] : 'aman',
                       'partial' => !empty($n['partial']),
                       'top' => array_map(function ($x) { return mb_substr(strip_tags((string)$x), 0, 140); }, array_slice((array)($n['top'] ?? []), 0, 3))];
        }
        $out['wa_health'] = ['at' => (int)($in['wa_health']['at'] ?? 0), 'nums' => $nums];
    }
    // v1.2.68: pemakaian kuota scan topik bulan ini
    if (is_array($in['topic_scans'] ?? null)) {"""),
])

patch(P + '/backend/cron-tick.php', [
 ("    $status[$tid] = $row;\n",
  """    // v1.2.104: skor-risiko-wa — Telegram saat nomor WAHA tenant masuk zona Bahaya, sekali lagi saat kembali aman
    if ($ok && is_array($j['stats']['wa_health']['nums'] ?? null)) {
        $wh = is_array($prev['wa_alert'] ?? null) ? $prev['wa_alert'] : [];
        foreach ($j['stats']['wa_health']['nums'] as $n) {
            $k = (string)($n['ch'] ?? '');
            if ($k === '') continue;
            $lv = (string)($n['level'] ?? '');
            $nm = (string)($n['label'] ?? $k) . (!empty($n['number']) ? ' (+' . $n['number'] . ')' : '');
            if ($lv === 'bahaya' && empty($wh[$k])) {
                if (!$dry) ctTelegram("\\xE2\\x9A\\xA0 Nomor WA berisiko suspend: {$tid} \\xE2\\x80\\x94 {$nm}\\nSkor " . (int)($n['score'] ?? 0) . "/100\\n" . implode("\\n", array_slice((array)($n['top'] ?? []), 0, 3)));
                $wh[$k] = time();
            } elseif ($lv === 'aman' && !empty($wh[$k])) {
                if (!$dry) ctTelegram("\\xE2\\x9C\\x85 Nomor WA kembali aman: {$tid} \\xE2\\x80\\x94 {$nm} (skor " . (int)($n['score'] ?? 0) . ")");
                unset($wh[$k]);
            }
        }
        $row['wa_alert'] = $wh;
    } elseif (!empty($prev['wa_alert'])) $row['wa_alert'] = $prev['wa_alert'];
    $status[$tid] = $row;
"""),
])

patch(P + '/admin/index.html', [
 ("function load(){\n  api('list_tenants').then(res=>{",
  """// v1.2.104: skor-risiko-wa — lencana nomor WAHA paling berisiko + rincian per nomor
const WH_C = {aman:['#dcfce7','#166534','Aman'], waspada:['#fef3c7','#92400e','Waspada'], bahaya:['#fee2e2','#991b1b','Bahaya']};
function whCell(t, st){
  const w = st && st.wa_health; if(!w || !w.nums || !w.nums.length) return '';
  const worst = w.nums.slice().sort((a,b)=>b.score-a.score)[0], c = WH_C[worst.level] || WH_C.aman;
  return ` <a href="#" onclick="showWaHealth('${esc(t.tenant_id)}');return false" class="badge" title="${esc(w.nums.map(n=>(n.label||n.ch)+': '+n.score+' ('+n.level+')').join('\\n'))}" style="background:${c[0]};color:${c[1]};text-decoration:none">WA ${worst.score}</a>`;
}
window.showWaHealth = function(id){
  api('list_tenants').then(res=>{
    const t = (res.tenants||[]).find(x=>String(x.tenant_id).toLowerCase()===String(id).toLowerCase());
    if(!t){ toast('Tenant tidak ditemukan.',true); return; }
    const w = ((t.cron&&t.cron.stats)||{}).wa_health || (t.last_stats||{}).wa_health;
    const at = w && w.at ? new Date((w.at+7*3600)*1000).toISOString().replace('T',' ').slice(0,16)+' WIB' : '–';
    $('#modal').innerHTML = `
      <h3>Kesehatan Nomor WA — ${esc(t.name||t.tenant_id)}</h3>
      <div class="modal-body">
        <div class="hint" style="margin-bottom:10px">Skor 0–100 perkiraan risiko suspend (heuristik dari pola pemakaian, bukan data resmi WhatsApp). Dihitung tenant tiap 15 menit · terakhir ${esc(at)}.</div>
        ${(w&&w.nums||[]).map(n=>{ const c = WH_C[n.level]||WH_C.aman; return `
          <div style="border:1px solid var(--line,#e5e7eb);border-radius:8px;padding:10px;margin-bottom:8px">
            <div><span class="badge" style="background:${c[0]};color:${c[1]}">${n.score} · ${c[2]}${n.partial?'*':''}</span> <b>${esc(n.label||n.ch)}</b> ${n.number?'<span class="mono">+'+esc(n.number)+'</span>':''}</div>
            ${(n.top||[]).length ? '<ul style="margin:6px 0 0;padding-left:18px;font-size:13px">'+n.top.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>' : '<div class="hint" style="margin-top:4px">Tidak ada faktor risiko.</div>'}
          </div>`; }).join('') || '<div class="hint">Belum ada laporan (tenant v1.2.104+ dengan WAHA).</div>'}
        <div class="hint">* data belum 24 jam. Telegram dikirim saat nomor masuk Bahaya (≥60) dan saat kembali Aman.</div>
      </div>
      <div class="actions"><button class="ghost" onclick="closeModal()">Tutup</button></div>`;
    $('#modalBg').classList.add('show');
  });
};

function load(){
  api('list_tenants').then(res=>{"""),
 ("""            <td>${esc(t.name||'')}${st.wa_provider==='fonnte'?' <span class="badge idle" title="Masih memakai Fonnte — pindahkan ke WAHA">Fonnte</span>':''}</td><!-- v1.2.92: fonnte-off -->""",
  """            <td>${esc(t.name||'')}${st.wa_provider==='fonnte'?' <span class="badge idle" title="Masih memakai Fonnte — pindahkan ke WAHA">Fonnte</span>':''}${whCell(t, st)}</td><!-- v1.2.92: fonnte-off; v1.2.104: skor-risiko-wa -->"""),
])
print('selesai v1.2.104')
