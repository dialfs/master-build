#!/usr/bin/env python3
"""v1.2.137 kembali-bot: pengaturan on/off + menit untuk (a) claim lepas otomatis (30 mnt) dan
(b) mode manusia tanpa claim kembali ke bot (1 jam); balasan agent kini memperbarui aktivitas claim. Idempoten."""
import os, sys, shutil, time
T=os.path.expanduser(sys.argv[1] if len(sys.argv)>1 else '~/Herd/dei-tenant'); TAG='v1.2.137: kembali-bot'
STAMP=time.strftime('%Y%m%d-%H%M%S'); done=set()
def rep(p,a,b):
    fp=T+'/'+p; s=open(fp,encoding='utf-8').read()
    if b in s: return
    assert s.count(a)==1,(p,s.count(a),a[:90])
    if fp not in done: shutil.copy2(fp, fp+'.bak-v12137-'+STAMP); done.add(fp)
    open(fp,'w',encoding='utf-8').write(s.replace(a,b))
API='api/index.php'; A='dashboard/chatbot-ai/app.js'; H='dashboard/chatbot-ai/index.html'

rep(API,"define('DEI_VERSION', 'v1.2.136');   // v1.2.136: aktif-fix","define('DEI_VERSION', 'v1.2.137');   // "+TAG)

# --- konfigurasi
rep(API,"define('WA_MODE_IDLE_SEC', 3600);   // 1 jam\n",
"""define('WA_MODE_IDLE_SEC', 3600);   // 1 jam
// """+TAG+""": settings.handback — keduanya bisa dimatikan & diatur menitnya (bawaan = perilaku lama: nyala, 30 / 60).
//   claim_*: chat yang di-claim agent dilepas & kembali ke bot bila agent tidak membalas N menit (waClaimAutoProcess)
//   idle_*:  nomor mode manusia TANPA claim kembali ke bot setelah N menit (waModeSweepIdle)
function deiHandbackConf($s) {
    $c = is_array($s['handback'] ?? null) ? $s['handback'] : [];
    return [
        'claim_enabled' => !array_key_exists('claim_enabled', $c) || !empty($c['claim_enabled']),
        'claim_minutes' => max(5, min(1440, (int)($c['claim_minutes'] ?? 30))),
        'idle_enabled'  => !array_key_exists('idle_enabled', $c) || !empty($c['idle_enabled']),
        'idle_minutes'  => max(15, min(1440, (int)($c['idle_minutes'] ?? 60))),
    ];
}
""")

# --- sapu mode idle (tanpa claim)
rep(API,"""    if (deiIsManual()) return 0;          // v1.2.58: tidak ada bot untuk dikembalikan
    $hfCs = null;""","""    if (deiIsManual()) return 0;          // v1.2.58: tidak ada bot untuk dikembalikan
    $hb = deiHandbackConf(getSettings());   // """+TAG+"""
    if (!$hb['idle_enabled']) return 0;
    $idleSec = $hb['idle_minutes'] * 60;
    $hfCs = null;""")
rep(API,"        if ($ts > 0 && ($now - $ts) < WA_MODE_IDLE_SEC) continue;","        if ($ts > 0 && ($now - $ts) < $idleSec) continue;   // "+TAG)
rep(API,"""        error_log('wa: ' . $n . ' nomor kembali ke mode bot (manual idle > '
                  . (int)(WA_MODE_IDLE_SEC / 60) . ' menit)');""","""        error_log('wa: ' . $n . ' nomor kembali ke mode bot (manual idle > '
                  . (int)($idleSec / 60) . ' menit)');""")

# --- claim lepas otomatis
rep(API,"    $INACTIVITY_TIMEOUT = 30 * 60;  // 30 menit\n",
"    $hb = deiHandbackConf(getSettings());   // "+TAG+"\n    $INACTIVITY_TIMEOUT = $hb['claim_minutes'] * 60;  // bawaan 30 menit\n")
rep(API,"""        if (deiIsManual()) continue;
        $lastActivity = $claim['last_agent_activity'] ?? $claim['claimed_at'] ?? 0;""","""        if (deiIsManual()) continue;
        if (!$hb['claim_enabled']) continue;   // """+TAG+""": dimatikan -> claim bertahan sampai Selesai / dilepas
        $lastActivity = $claim['last_agent_activity'] ?? $claim['claimed_at'] ?? 0;""")

# --- bug: balasan agent tidak pernah memperbarui last_agent_activity
rep(API,"""/** Write audit log entry. Keep last 500 entries. */""","""// """+TAG+""": balasan agent (dashboard / lampiran / HP) memperbarui aktivitas claim siapa pun pemegangnya.
// Sebelumnya waClaimTouchActivity tidak pernah dipanggil -> claim lepas 30 menit setelah claim walau agent aktif.
function waClaimTouchAny($number) {
    return deiWithLock('wa-claims', function () use ($number) {
        $number = waNormNum($number);
        if ($number === '') return;
        $claims = readJson(waClaimFile(), []);
        if (!is_array($claims) || !isset($claims[$number]) || !is_array($claims[$number])) return;
        $claims[$number]['last_agent_activity'] = time();
        writeJson(waClaimFile(), $claims);
    });
}

/** Write audit log entry. Keep last 500 entries. */""")
rep(API,"""function deiRecordAgentReply($num, $agent, $src = 'dashboard') {
    try {""","""function deiRecordAgentReply($num, $agent, $src = 'dashboard') {
    try { waClaimTouchAny($num); } catch (\\Throwable $e) { error_log('claim touch: ' . $e->getMessage()); }   // """+TAG+"""
    try {""")

# --- simpan pengaturan
rep(API,"""            if (isset($incoming['reply_delay']) && is_array($incoming['reply_delay'])) {   // v1.2.96: jeda-balasan
                $merged['reply_delay'] = deiMergeSettings(""","""            if (isset($incoming['handback']) && is_array($incoming['handback'])) {   // """+TAG+"""
                $merged['handback'] = deiMergeSettings($current['handback'] ?? [], $incoming['handback']);
            }
            if (isset($incoming['reply_delay']) && is_array($incoming['reply_delay'])) {   // v1.2.96: jeda-balasan
                $merged['reply_delay'] = deiMergeSettings(""")
rep(API,"""        if (isset($merged['handover_fallback']) && is_array($merged['handover_fallback'])) $merged['handover_fallback'] = deiHfConf($merged);   // v1.2.126
""","""        if (isset($merged['handover_fallback']) && is_array($merged['handover_fallback'])) $merged['handover_fallback'] = deiHfConf($merged);   // v1.2.126
        if (isset($merged['handback']) && is_array($merged['handback'])) $merged['handback'] = deiHandbackConf($merged);   // """+TAG+"""
""")

# --- UI
rep(H,"""      <!-- v1.2.126: respon-median — kembali ke bot bila agent tidak membalas -->""","""      <!-- """+TAG+""" -->
      <div class="card"><h3>Kembali ke Bot Otomatis</h3>
        <div class="desc">Kapan chat yang dipegang manusia dikembalikan ke bot tanpa pesan ke tamu. Bila dimatikan, chat tetap di agent sampai ditekan <b>Selesai</b> atau dilepas. Tidak berlaku di Mode Manual (di sana chat tidak pernah kembali ke bot).</div>
        <div class="toggle-row"><div><div class="tt">Lepas claim bila agent tidak membalas</div><div class="help">Chat yang di-claim / diambil alih agent. Dihitung dari balasan terakhir agent (dashboard atau HP), atau dari waktu claim bila belum membalas.</div></div><label class="switch"><input type="checkbox" id="hb_claim_enabled"><span class="sl"></span></label></div>
        <div class="grid2">
          <div class="row"><label class="fl">Lepas setelah (menit)</label><input type="number" id="hb_claim_minutes" min="5" max="1440" step="1" value="30"><div class="help">5–1440. Bawaan 30.</div></div>
        </div>
        <div class="toggle-row"><div><div class="tt">Kembalikan nomor tanpa claim ke bot</div><div class="help">Nomor yang pindah ke mode manusia (kata kunci handoff, batas balasan AI, balasan dari HP) tapi tidak di-claim siapa pun. Dihitung dari handoff atau balasan agent terakhir; pesan tamu tidak memperpanjang.</div></div><label class="switch"><input type="checkbox" id="hb_idle_enabled"><span class="sl"></span></label></div>
        <div class="grid2">
          <div class="row"><label class="fl">Kembali setelah (menit)</label><input type="number" id="hb_idle_minutes" min="15" max="1440" step="1" value="60"><div class="help">15–1440. Bawaan 60.</div></div>
        </div>
        <div class="help">Bila keduanya mati dan tidak ada agent yang membalas, tamu tidak dijawab bot sama sekali — aktifkan "Kembali ke Bot bila Agent Tidak Membalas" di bawah atau Eskalasi Darurat.</div>
      </div>

      <!-- v1.2.126: respon-median — kembali ke bot bila agent tidak membalas -->""")
rep(H,"Bila 1 jam tidak ada agent yang membalas, nomor kembali ke bot dan hitungan mulai dari nol.</div>",
      "Bila tidak ada agent yang membalas, nomor kembali ke bot sesuai pengaturan <b>Kembali ke Bot Otomatis</b> dan hitungan mulai dari nol.</div>")
rep(H,"Tanpa ini nomor tetap kembali ke bot setelah 1 jam, tetapi diam-diam — tamu baru dijawab bila ia menulis lagi.",
      "Tanpa ini nomor kembali ke bot diam-diam sesuai pengaturan Kembali ke Bot Otomatis — tamu baru dijawab bila ia menulis lagi.")
rep(H,'<script src="app.js?v=1.2.136"></script><!-- v1.2.136: aktif-fix -->','<script src="app.js?v=1.2.137"></script><!-- '+TAG+' -->')

rep(A,"""      if ($('#hf_enabled')) { $('#hf_enabled').checked = hf.enabled === true; $('#hf_minutes').value = hf.minutes || 15; $('#hf_text').value = hf.text || ''; }
""","""      if ($('#hf_enabled')) { $('#hf_enabled').checked = hf.enabled === true; $('#hf_minutes').value = hf.minutes || 15; $('#hf_text').value = hf.text || ''; }
      var hb = res.settings.handback || {};   // """+TAG+"""
      if ($('#hb_claim_enabled')) { $('#hb_claim_enabled').checked = hb.claim_enabled !== false; $('#hb_claim_minutes').value = hb.claim_minutes || 30; $('#hb_idle_enabled').checked = hb.idle_enabled !== false; $('#hb_idle_minutes').value = hb.idle_minutes || 60; }
""")
rep(A,"""text: $('#hf_text').value.trim() } : undefined,   // v1.2.126: respon-median
""","""text: $('#hf_text').value.trim() } : undefined,   // v1.2.126: respon-median
      handback: $('#hb_claim_enabled') ? { claim_enabled: $('#hb_claim_enabled').checked, claim_minutes: Math.max(5, Math.min(1440, Math.round(+$('#hb_claim_minutes').value || 30))), idle_enabled: $('#hb_idle_enabled').checked, idle_minutes: Math.max(15, Math.min(1440, Math.round(+$('#hb_idle_minutes').value || 60))) } : undefined,   // """+TAG+"""
""")
print('ok')
