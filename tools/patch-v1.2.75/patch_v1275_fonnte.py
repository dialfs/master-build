#!/usr/bin/env python3
"""v1.2.75 — Koneksi Fonnte dari dashboard (scan QR / kode tautan, status, putuskan, pasang webhook).
Idempoten: backup -> str.replace anchor -> lapor. Jalankan: python3 patch_v1275_fonnte.py <root dei-tenant>"""
import sys, os, shutil, time
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/Herd/dei-tenant')
TS = time.strftime('%Y%m%d-%H%M%S')
MARK = 'v1.2.75: koneksi perangkat Fonnte'

def patch(rel, pairs):
    p = os.path.join(ROOT, rel)
    src = open(p, encoding='utf-8').read()
    if MARK in src:
        print('SKIP (sudah):', rel); return
    out = src
    for old, new in pairs:
        n = out.count(old)
        if n != 1:
            sys.exit('ANCHOR %s di %s ditemukan %d kali: %r' % ('?', rel, n, old[:80]))
        out = out.replace(old, new)
    shutil.copy2(p, p + '.bak-fonnteqr-' + TS)
    open(p, 'w', encoding='utf-8').write(out)
    print('OK:', rel)

# ---------------------------------------------------------------- api/index.php
PHP_HELPER = r'''// v1.2.75: koneksi perangkat Fonnte — panggil API perangkat (qr / device / disconnect / update-device).
// Fonnte membalas HTTP 200 walau gagal; status ada di badan balasan.
function fonnteApi($token, $path, $fields = []) {
    $ch = curl_init('https://api.fonnte.com/' . $path);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_TIMEOUT        => 20,
        CURLOPT_CONNECTTIMEOUT => 8,
        CURLOPT_HTTPHEADER     => ['Authorization: ' . $token],
        CURLOPT_POSTFIELDS     => http_build_query($fields),
    ]);
    $resp = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err  = curl_error($ch);
    curl_close($ch);
    if ($resp === false || $code < 200 || $code >= 300) {
        error_log('fonnteApi ' . $path . ' HTTP ' . $code . ' ' . $err);
        return ['status' => false, 'reason' => 'Server Fonnte tidak dapat dihubungi (HTTP ' . $code . ').'];
    }
    $d = json_decode((string)$resp, true);
    return is_array($d) ? $d : ['status' => false, 'reason' => 'Balasan Fonnte tidak dikenali.'];
}
function fonnteReason($d, $fallback) {
    $r = trim((string)($d['reason'] ?? ($d['detail'] ?? '')));
    return $r !== '' ? $r : $fallback;
}

function waSend($wa, $to, $text) {'''

PHP_CASE = r'''    /* ---------- v1.2.75: koneksi perangkat Fonnte dari dashboard (scan QR) ---------- */
    // Token Fonnte tetap di server & hanya diisi Super Admin. Admin klien cukup
    // menekan Hubungkan lalu scan QR (atau kode tautan) dari HP-nya.
    case 'fonnte_conn': {
        $u  = requireAuth(['super_admin', 'admin']);
        $in = bodyInput();
        $op = (string)($in['op'] ?? 'status');
        $s  = getSettings();
        $wa = waConf($s);
        if (($wa['provider'] ?? 'meta') !== 'fonnte') jsonOut(['ok' => false, 'error' => 'Penyedia WhatsApp bukan Fonnte.'], 400);
        $tok = (string)($wa['fonnte_token'] ?? '');
        if ($tok === '') jsonOut(['ok' => false, 'error' => 'Token Fonnte belum diisi Super Admin.'], 400);

        if ($op === 'status') {
            $d = fonnteApi($tok, 'device');
            if (empty($d['status'])) jsonOut(['ok' => false, 'error' => fonnteReason($d, 'Gagal membaca status perangkat.')]);
            $dev = preg_replace('/\D/', '', (string)($d['device'] ?? ''));
            // Nomor perangkat dipakai menyaring webhook — isi otomatis kalau masih kosong.
            if ($dev !== '' && trim((string)($wa['fonnte_device'] ?? '')) === '') {
                $s2 = getSettings();
                $s2['whatsapp_api']['fonnte_device'] = $dev;
                writeJson(SETTINGS_FILE, $s2);
            }
            jsonOut([
                'ok'        => true,
                'connected' => (strtolower((string)($d['device_status'] ?? '')) === 'connect'),
                'device'    => $dev,
                'name'      => (string)($d['name'] ?? ''),
                'package'   => (string)($d['package'] ?? ''),
                'quota'     => $d['quota'] ?? null,
                'expired'   => (string)($d['expired'] ?? ''),
            ]);
        }

        if ($op === 'qr') {
            $f = [];
            if (($in['type'] ?? 'qr') === 'code') {
                $num = preg_replace('/\D/', '', (string)($in['whatsapp'] ?? ''));
                if (strpos($num, '0') === 0) $num = '62' . substr($num, 1);
                if (strlen($num) < 9 || strlen($num) > 15) jsonOut(['ok' => false, 'error' => 'Nomor WhatsApp tidak valid.'], 400);
                $f = ['type' => 'code', 'whatsapp' => $num];
            }
            $d = fonnteApi($tok, 'qr', $f);
            if (!empty($d['status'])) {
                $out = ['ok' => true, 'connected' => false];
                $img = preg_replace('/[^A-Za-z0-9+\/=]/', '', (string)($d['url'] ?? ''));
                if ($img !== '') $out['qr'] = 'data:image/png;base64,' . $img;
                if (!empty($d['code'])) $out['code'] = (string)$d['code'];
                jsonOut($out);
            }
            $r = fonnteReason($d, 'Gagal mengambil QR.');
            if (stripos($r, 'already connect') !== false) jsonOut(['ok' => true, 'connected' => true]);
            jsonOut(['ok' => false, 'error' => $r]);
        }

        if ($op === 'disconnect') {
            $d = fonnteApi($tok, 'disconnect');
            $r = fonnteReason($d, 'Gagal memutuskan.');
            $ok = !empty($d['status']) || stripos($r, 'already disconnect') !== false;
            if ($ok) { try { waAuditLog('fonnte_disconnect', $u['username'], '', []); } catch (\Throwable $e) {} }
            jsonOut($ok ? ['ok' => true] : ['ok' => false, 'error' => $r]);
        }

        if ($op === 'webhook') {
            if (($u['role'] ?? '') !== 'super_admin') jsonOut(['ok' => false, 'error' => 'Khusus Super Admin.'], 403);
            $key = (string)($wa['fonnte_webhook_key'] ?? '');
            if ($key === '') jsonOut(['ok' => false, 'error' => 'Kunci webhook belum ada — simpan pengaturan dengan penyedia Fonnte dulu.'], 400);
            $base = deiSelfApiUrl();
            if (strpos($base, 'https://') !== 0) jsonOut(['ok' => false, 'error' => 'Webhook butuh alamat https publik. Alamat saat ini: ' . $base], 400);
            $p    = fonnteApi($tok, 'device');
            $name = trim((string)($p['name'] ?? ''));
            if (mb_strlen($name) < 2) $name = deiTenantName($s);
            $hook = $base . '?action=wa_webhook_fonnte&key=' . rawurlencode($key);
            $f = ['name' => mb_substr($name, 0, 30), 'webhook' => $hook];
            $dev = preg_replace('/\D/', '', (string)($p['device'] ?? ''));
            if ($dev !== '') $f['device'] = $dev;
            $d = fonnteApi($tok, 'update-device', $f);
            if (empty($d['status'])) jsonOut(['ok' => false, 'error' => fonnteReason($d, 'Gagal memasang webhook.')]);
            try { waAuditLog('fonnte_webhook_set', $u['username'], '', []); } catch (\Throwable $e) {}
            jsonOut(['ok' => true, 'webhook' => $base . '?action=wa_webhook_fonnte&key=••••']);
        }

        jsonOut(['ok' => false, 'error' => 'op tidak dikenal'], 400);
        break;
    }

    case 'wa_audit_log': {'''

patch('api/index.php', [
    ("function waSend($wa, $to, $text) {", PHP_HELPER),
    ("    case 'wa_audit_log': {", PHP_CASE),
    ("define('DEI_VERSION', 'v1.2.74');", "define('DEI_VERSION', 'v1.2.75');"),
])

# ---------------------------------------------------------------- index.html
HTML_CARD = '''      <!-- v1.2.75: koneksi perangkat Fonnte (Admin & Super Admin) -->
      <div class="card" data-role-card="super_admin,admin" id="fonConnCard" style="display:none"><h3>Koneksi WhatsApp</h3>
        <div class="desc">Sambungkan nomor WhatsApp ke chatbot. Klik <b>Hubungkan</b>, lalu di HP buka WhatsApp › Perangkat Tertaut › Tautkan Perangkat dan scan QR yang muncul.</div>
        <div class="row" style="flex-direction:row;gap:10px;align-items:center;flex-wrap:wrap">
          <span class="pill off" id="fonc_pill">Memeriksa…</span>
          <span class="help" id="fonc_info" style="margin:0"></span>
        </div>
        <div class="row" style="flex-direction:row;gap:8px;flex-wrap:wrap">
          <button class="btn" id="fonc_connect" type="button">Hubungkan (scan QR)</button>
          <button class="btn ghost" id="fonc_code" type="button">Pakai kode tautan</button>
          <button class="btn ghost" id="fonc_refresh" type="button">Cek status</button>
          <button class="btn ghost" id="fonc_disconnect" type="button" style="display:none">Putuskan</button>
          <button class="btn ghost" id="fonc_webhook" type="button" data-role-card="super_admin">Pasang webhook otomatis</button>
        </div>
        <div class="row hide" id="fonc_numrow" style="flex-direction:row;gap:8px;align-items:center;flex-wrap:wrap">
          <input type="tel" id="fonc_num" class="mono" placeholder="Nomor WA, mis. 0812xxxxxxx" style="flex:1;min-width:180px">
          <button class="btn" id="fonc_code_go" type="button">Minta kode</button>
        </div>
        <div id="fonc_box" class="hide" style="text-align:center;padding:14px;border:1px dashed var(--line,#d0d0d0);border-radius:8px;margin-top:8px">
          <img id="fonc_qr" alt="QR WhatsApp" style="width:260px;max-width:100%;display:none;margin:0 auto">
          <div id="fonc_codeval" class="mono" style="font-size:26px;letter-spacing:4px;font-weight:700;display:none"></div>
          <div class="help" id="fonc_hint" style="margin-top:8px"></div>
          <button class="btn ghost" id="fonc_cancel" type="button" style="margin-top:8px">Tutup</button>
        </div>
        <div class="help" style="margin-top:8px">Fonnte memakai jalur tidak resmi — hindari kirim pesan massal agar nomor tidak diblokir WhatsApp.</div>
      </div>
      <div class="card" data-role-card="super_admin"><h3>WhatsApp Bot</h3>'''
patch('dashboard/chatbot-ai/index.html', [
    ('      <div class="card" data-role-card="super_admin"><h3>WhatsApp Bot</h3>', HTML_CARD),
])

# ---------------------------------------------------------------- app.js
JS_FUNCS = r'''  // v1.2.75: koneksi perangkat Fonnte dari dashboard — admin cukup scan QR.
  var _fonc = { poll: null, qrT: null, stopT: null, mode: 'qr' };
  function foncStop() {
    clearInterval(_fonc.poll); clearInterval(_fonc.qrT); clearTimeout(_fonc.stopT);
    _fonc.poll = _fonc.qrT = _fonc.stopT = null;
    var b = $('#fonc_box'); if (b) b.classList.add('hide');
  }
  function foncSet(st) {
    var p = $('#fonc_pill'), inf = $('#fonc_info');
    if (!p) return;
    if (st.error) { p.className = 'pill off'; p.textContent = 'Status tidak diketahui'; inf.textContent = st.error; return; }
    p.className = 'pill ' + (st.connected ? 'on' : 'off');
    p.textContent = st.connected ? 'Tersambung' : 'Belum tersambung';
    var bits = [];
    if (st.device) bits.push('Nomor ' + st.device);
    if (st.package) bits.push('Paket ' + st.package);
    if (st.quota !== null && st.quota !== undefined && st.quota !== '') bits.push('Kuota ' + st.quota);
    if (st.expired) bits.push('Aktif s/d ' + st.expired);
    inf.textContent = bits.join(' · ');
    $('#fonc_connect').style.display = st.connected ? 'none' : '';
    $('#fonc_code').style.display = st.connected ? 'none' : '';
    $('#fonc_disconnect').style.display = st.connected ? '' : 'none';
    if (st.connected) $('#fonc_numrow').classList.add('hide');
  }
  function foncStatus(silent) {
    return api('fonnte_conn', { method: 'POST', body: { op: 'status' } }).then(function (r) {
      if (!r.ok) { if (!silent) foncSet({ error: r.error || 'Gagal membaca status.' }); return null; }
      var wasPolling = !!_fonc.poll;
      foncSet(r);
      if (r.connected && wasPolling) { foncStop(); toast('WhatsApp tersambung.'); }
      return r;
    }).catch(function () { if (!silent) foncSet({ error: 'Koneksi bermasalah.' }); });
  }
  function foncFetch(num) {
    var body = { op: 'qr' };
    if (_fonc.mode === 'code') { body.type = 'code'; body.whatsapp = num; }
    return api('fonnte_conn', { method: 'POST', body: body }).then(function (r) {
      if (!_fonc.poll) return;   // sudah ditutup
      if (!r.ok) { foncStop(); toast(r.error || 'Gagal mengambil QR.', true); return; }
      if (r.connected) { foncStop(); foncStatus(); return; }
      var img = $('#fonc_qr'), cv = $('#fonc_codeval'), h = $('#fonc_hint');
      if (r.qr) {
        img.src = r.qr; img.style.display = 'block'; cv.style.display = 'none';
        h.textContent = 'Di HP: WhatsApp › Perangkat Tertaut › Tautkan Perangkat, lalu scan. QR diperbarui otomatis.';
      } else if (r.code) {
        cv.textContent = r.code; cv.style.display = ''; img.style.display = 'none';
        h.textContent = 'Di HP: WhatsApp › Perangkat Tertaut › Tautkan Perangkat › Tautkan dengan nomor telepon, lalu masukkan kode ini.';
      } else {
        h.textContent = 'Fonnte belum mengirim QR. Tunggu sebentar…';
      }
    }).catch(function () { $('#fonc_hint').textContent = 'Koneksi bermasalah, mencoba lagi…'; });
  }
  function foncStart(mode, num) {
    foncStop();
    _fonc.mode = mode;
    $('#fonc_box').classList.remove('hide');
    $('#fonc_qr').style.display = 'none'; $('#fonc_codeval').style.display = 'none';
    $('#fonc_hint').textContent = mode === 'code' ? 'Meminta kode tautan…' : 'Mengambil QR…';
    _fonc.poll = setInterval(function () { foncStatus(true); }, 4000);
    if (mode === 'qr') _fonc.qrT = setInterval(function () { foncFetch(); }, 30000);   // QR WA cepat kedaluwarsa
    _fonc.stopT = setTimeout(function () {
      if (!_fonc.poll) return;
      foncStop(); toast('Waktu habis. Klik Hubungkan lagi bila belum tersambung.', true);
    }, 180000);
    foncFetch(num);
  }
  function foncInit(wa) {
    var card = $('#fonConnCard'); if (!card) return;
    var on = (wa.provider === 'fonnte') && !!wa.fonnte_token_is_set;
    card.style.display = on ? '' : 'none';
    if (!on) { foncStop(); return; }
    if (card.dataset.wired !== '1') {
      card.dataset.wired = '1';
      $('#fonc_connect').onclick = function () { $('#fonc_numrow').classList.add('hide'); foncStart('qr'); };
      $('#fonc_code').onclick = function () { $('#fonc_numrow').classList.toggle('hide'); $('#fonc_num').focus(); };
      $('#fonc_code_go').onclick = function () {
        var n = $('#fonc_num').value.replace(/\D/g, '');
        if (n.length < 9) { toast('Isi nomor WhatsApp yang akan ditautkan.', true); return; }
        foncStart('code', n);
      };
      $('#fonc_refresh').onclick = function () { foncStatus(); };
      $('#fonc_cancel').onclick = function () { foncStop(); };
      $('#fonc_disconnect').onclick = function () {
        if (!confirm('Putuskan WhatsApp dari chatbot? Bot berhenti membalas sampai disambungkan lagi.')) return;
        api('fonnte_conn', { method: 'POST', body: { op: 'disconnect' } }).then(function (r) {
          toast(r.ok ? 'WhatsApp diputuskan.' : (r.error || 'Gagal memutuskan.'), !r.ok);
          foncStatus();
        });
      };
      $('#fonc_webhook').onclick = function () {
        var b = this; b.disabled = true;
        api('fonnte_conn', { method: 'POST', body: { op: 'webhook' } }).then(function (r) {
          b.disabled = false;
          toast(r.ok ? 'Webhook Fonnte terpasang.' : (r.error || 'Gagal memasang webhook.'), !r.ok);
        }).catch(function () { b.disabled = false; });
      };
    }
    foncStatus();
  }

  // v1.2.54: Embedded Signup coexistence (WA Business App + Cloud API di satu nomor)'''

patch('dashboard/chatbot-ai/app.js', [
    ('  // v1.2.54: Embedded Signup coexistence (WA Business App + Cloud API di satu nomor)', JS_FUNCS),
    ("      var s = res.settings, w = s.widget || {}, a = s.api || {};\n      $('#w_chatbot').checked",
     "      var s = res.settings, w = s.widget || {}, a = s.api || {};\n      foncInit(s.whatsapp_api || {});   // v1.2.75\n      $('#w_chatbot').checked"),
])
print('selesai')
