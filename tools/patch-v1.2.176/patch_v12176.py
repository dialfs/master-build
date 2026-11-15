#!/usr/bin/env python3
"""v1.2.176 meta-campaign (TENANT): nama campaign asli untuk chat dari iklan Click-to-WhatsApp.
- Referral CTWA menyimpan ad ID (wa_ad) + headline; campaign = nama campaign dari Meta Marketing API
  (ad -> campaign/adset/ad, cache data/meta-ads-cache.json), cadangan "iklan <ad ID>" bila token belum ada.
- Laporan (report + statistik ke pusat) membaca nama dari cache untuk baris lama yang masih "iklan <ID>".
- Token Meta Ads (ads_read) di Pengaturan Widget, super admin: meta_ads_get / meta_ads_save / meta_ads_test.
Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HTML = T + '/dashboard/chatbot-ai/index.html'
TAG = 'v1.2.176: meta-campaign'; stamp = time.strftime('%Y%m%d-%H%M%S')
NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    if not NOBAK: shutil.copy2(p, p + '.bak-v12176-' + stamp)
    wr(p, fn(s)); print('OK', p)
C = '   // ' + TAG

FUNCS = r'''/* ---------- v1.2.176: meta-campaign — nama campaign iklan CTWA dari Meta Marketing API ----------
 * Webhook WhatsApp hanya membawa ad ID + headline. Dengan token ads_read (Pengaturan Widget › Meta Ads)
 * ad ID diterjemahkan ke nama campaign / ad set / iklan. Cache per iklan: berhasil 30 hari, gagal 1 jam. */
if (!defined('DEI_META_GRAPH')) define('DEI_META_GRAPH', 'https://graph.facebook.com/v23.0');
function deiMetaAdsToken() { return trim((string)(getSettings()['meta_ads']['token'] ?? '')); }
function deiMetaAdsCacheFile() { return DATA_DIR . '/meta-ads-cache.json'; }
function deiMetaGraph($path, $token, $timeout = 4) {
    if (!function_exists('curl_init')) return ['ok' => false, 'error' => 'cURL tidak tersedia di server.'];
    $url = DEI_META_GRAPH . '/' . ltrim($path, '/') . (strpos($path, '?') === false ? '?' : '&') . 'access_token=' . rawurlencode($token);
    $ch = curl_init($url);
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => $timeout, CURLOPT_CONNECTTIMEOUT => 3]);
    $raw = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $cerr = curl_error($ch); curl_close($ch);
    if ($raw === false) return ['ok' => false, 'error' => 'Koneksi ke Meta gagal: ' . $cerr];
    $d = json_decode((string)$raw, true);
    if (!is_array($d)) return ['ok' => false, 'error' => 'Respons Meta tidak valid (HTTP ' . $code . ').'];
    if (isset($d['error'])) return ['ok' => false, 'error' => mb_substr((string)($d['error']['message'] ?? 'Error Meta'), 0, 200), 'code' => (int)($d['error']['code'] ?? 0)];
    return ['ok' => true, 'data' => $d];
}
/* Nama iklan dari cache; $fetch = boleh memanggil Meta bila belum ada / cache gagal kedaluwarsa. */
function deiMetaAdInfo($adId, $fetch = true) {
    $adId = preg_replace('/\D/', '', (string)$adId);
    if ($adId === '') return null;
    $all = readJson(deiMetaAdsCacheFile(), []); if (!is_array($all)) $all = [];
    $c = is_array($all[$adId] ?? null) ? $all[$adId] : null;
    if ($c && !empty($c['campaign']) && time() - (int)($c['t'] ?? 0) < 30 * 86400) return $c;
    if ($c && empty($c['campaign']) && time() - (int)($c['t'] ?? 0) < 3600) return $c;
    if (!$fetch) return $c;
    $tok = deiMetaAdsToken();
    if ($tok === '') return $c;
    $r = deiMetaGraph($adId . '?fields=name,adset{name},campaign{name}', $tok);
    $n = $r['ok'] ? ['campaign' => mb_substr((string)($r['data']['campaign']['name'] ?? ''), 0, 150),
                     'adset' => mb_substr((string)($r['data']['adset']['name'] ?? ''), 0, 150),
                     'ad' => mb_substr((string)($r['data']['name'] ?? ''), 0, 150), 't' => time()]
                  : ['campaign' => '', 'err' => (string)($r['error'] ?? ''), 't' => time()];
    if ($c && !empty($c['campaign']) && !$r['ok']) return $c;   // pernah berhasil: pakai nama lama
    deiWithLock('meta-ads-cache', function () use ($adId, $n) {
        $all = readJson(deiMetaAdsCacheFile(), []); if (!is_array($all)) $all = [];
        $all[$adId] = $n;
        if (count($all) > 3000) $all = array_slice($all, -3000, null, true);
        writeJson(deiMetaAdsCacheFile(), $all);
    });
    return $n;
}
/* Campaign untuk baris log: baris iklan CTWA yang tercatat sebelum namanya diketahui ikut diperbarui. */
function deiWaCmp($l) {
    $cmp = (string)($l['utm_campaign'] ?? '');
    $ad = (string)($l['wa_ad'] ?? '');
    if ($ad === '') return $cmp;
    static $memo = [];
    if (!array_key_exists($ad, $memo)) { try { $i = deiMetaAdInfo($ad, false); } catch (\Throwable $e) { $i = null; } $memo[$ad] = (string)($i['campaign'] ?? ''); }
    return $memo[$ad] !== '' ? $memo[$ad] : $cmp;
}

'''

ENDP = r'''    /* ---------- v1.2.176: meta-campaign — token Meta Ads (ads_read), super admin ---------- */
    case 'meta_ads_get': {
        requireAuth(['super_admin']);
        $tok = deiMetaAdsToken();
        $cache = readJson(deiMetaAdsCacheFile(), []); if (!is_array($cache)) $cache = [];
        $okN = 0; $lastErr = '';
        foreach ($cache as $c) { if (!empty($c['campaign'])) $okN++; elseif (!empty($c['err'])) $lastErr = (string)$c['err']; }
        jsonOut(['ok' => true, 'token_set' => $tok !== '', 'masked' => maskKey($tok), 'ads_known' => $okN, 'last_err' => $lastErr,
                 'checked_at' => (string)(getSettings()['meta_ads']['checked_at'] ?? ''), 'who' => (string)(getSettings()['meta_ads']['who'] ?? '')]);
        break;
    }
    case 'meta_ads_save':
    case 'meta_ads_test': {
        requireAuth(['super_admin']);
        if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') jsonOut(['ok' => false, 'error' => 'Gunakan POST.'], 405);
        $in = bodyInput();
        $s = getSettings();
        $tok = $action === 'meta_ads_save' ? trim((string)($in['token'] ?? '')) : deiMetaAdsToken();
        if ($action === 'meta_ads_save' && $tok === '') {
            unset($s['meta_ads']); writeJson(SETTINGS_FILE, $s);
            jsonOut(['ok' => true, 'cleared' => true]);
        }
        if ($tok === '') jsonOut(['ok' => false, 'error' => 'Token belum diisi.'], 400);
        if (!preg_match('/^[A-Za-z0-9_\-|.]{20,600}$/', $tok)) jsonOut(['ok' => false, 'error' => 'Format token tidak dikenali.'], 400);
        $r = deiMetaGraph('me?fields=id,name', $tok);
        if (!$r['ok']) jsonOut(['ok' => false, 'error' => 'Token ditolak Meta: ' . $r['error']], 400);
        $who = (string)($r['data']['name'] ?? ($r['data']['id'] ?? ''));
        if ($action === 'meta_ads_save') {
            $s['meta_ads'] = ['token' => $tok, 'who' => $who, 'checked_at' => date('Y-m-d H:i:s')];
            writeJson(SETTINGS_FILE, $s);
            // cache gagal dibuang supaya iklan yang tertunda langsung dicoba lagi
            deiWithLock('meta-ads-cache', function () {
                $all = readJson(deiMetaAdsCacheFile(), []); if (!is_array($all)) $all = [];
                foreach ($all as $k => $v) { if (empty($v['campaign'])) unset($all[$k]); }
                writeJson(deiMetaAdsCacheFile(), $all);
            });
        }
        // coba terjemahkan iklan yang sudah tercatat (maks 10)
        $ads = [];
        foreach (readJson(DATA_DIR . '/wa-attr.json', []) as $a) { if (is_array($a) && !empty($a['ad_id'])) $ads[(string)$a['ad_id']] = 1; }
        $done = [];
        foreach (array_slice(array_keys($ads), -10) as $ad) {
            $i = deiMetaAdInfo($ad, true);
            $done[] = ['ad_id' => (string)$ad, 'campaign' => (string)($i['campaign'] ?? ''), 'err' => (string)($i['err'] ?? '')];
        }
        jsonOut(['ok' => true, 'who' => $who, 'ads' => $done]);
        break;
    }

'''

CARD = '''      <div class="card" data-role-card="super_admin"><!-- v1.2.176: meta-campaign -->
        <h3>Meta Ads — Nama Campaign Iklan WhatsApp</h3>
        <div class="desc">Iklan Click-to-WhatsApp (Facebook/Instagram) hanya mengirim ID iklan, bukan nama campaign atau UTM. Dengan token Meta (izin <b>ads_read</b>), nama campaign diambil otomatis dari Meta Marketing API dan tampil di laporan Source / Medium / Campaign.</div>
        <div class="row"><label class="fl">Token Meta Ads (ads_read)</label><input type="password" id="ma_token" autocomplete="off" placeholder="Tempel System User token (EAA...)"><div class="help" id="ma_status">Memuat…</div></div>
        <div class="row"><button class="btn" type="button" id="ma_save">Simpan &amp; Uji Token</button> <button class="btn ghost" type="button" id="ma_test">Uji Ulang</button> <button class="btn ghost" type="button" id="ma_clear">Hapus Token</button></div>
        <div class="help" id="ma_result"></div>
      </div>
'''

JSF = r'''
  /* ---- v1.2.176: meta-campaign — token Meta Ads ---- */
  function maStatus() {
    if (!$('#ma_status')) return;
    api('meta_ads_get').then(function (r) {
      if (!r || !r.ok) { $('#ma_status').textContent = (r && r.error) || 'Tidak bisa memuat.'; return; }
      $('#ma_status').textContent = r.token_set
        ? 'Token tersimpan (' + r.masked + (r.who ? ' · ' + r.who : '') + '). Iklan dikenali: ' + r.ads_known + (r.last_err ? ' · Error terakhir: ' + r.last_err : '')
        : 'Belum ada token — chat dari iklan CTWA tercatat sebagai "iklan <ID iklan>".';
    });
  }
  function maShow(r) {
    if (!r || !r.ok) { toast((r && r.error) || 'Gagal.', true); $('#ma_result').textContent = (r && r.error) || ''; return; }
    if (r.cleared) { toast('Token dihapus.'); $('#ma_result').textContent = ''; maStatus(); return; }
    var ads = (r.ads || []).map(function (a) { return 'iklan ' + a.ad_id + ' → ' + (a.campaign || ('gagal: ' + (a.err || '-'))); });
    $('#ma_result').textContent = 'Token valid' + (r.who ? ' (' + r.who + ')' : '') + '.' + (ads.length ? ' ' + ads.join(' · ') : ' Belum ada chat iklan CTWA baru untuk diuji.');
    toast('Token Meta valid.'); maStatus();
  }
  function maBind() {
    if (!$('#ma_save') || $('#ma_save').__b) return; $('#ma_save').__b = 1;
    $('#ma_save').onclick = function () {
      var v = $('#ma_token').value.trim(); if (!v) { toast('Tempel token dulu.', true); return; }
      api('meta_ads_save', { method: 'POST', body: { token: v } }).then(function (r) { if (r && r.ok) $('#ma_token').value = ''; maShow(r); });
    };
    $('#ma_test').onclick = function () { api('meta_ads_test', { method: 'POST', body: {} }).then(maShow); };
    $('#ma_clear').onclick = function () { if (confirm('Hapus token Meta Ads?')) api('meta_ads_save', { method: 'POST', body: { token: '' } }).then(maShow); };
  }
'''

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.175');   // v1.2.175:",
               "define('DEI_VERSION', 'v1.2.176');   // " + TAG + " — nama campaign asli untuk chat dari iklan Click-to-WhatsApp (Meta Marketing API); v1.2.175:", 'versi')
    # referral: simpan ad ID + headline, campaign cadangan "iklan <ID>"
    old = ("    $cmp = trim((string)($r['headline'] ?? '')); if ($cmp === '' && !empty($r['source_id'])) $cmp = 'ad ' . $r['source_id'];\n"
           "    return deiWaAttrNorm(['src' => stripos($url, 'instagram') !== false ? 'instagram' : 'facebook',\n"
           "        'med' => ($type === '' || $type === 'ad') ? 'ctwa' : 'ctwa_' . $type, 'cmp' => $cmp,\n"
           "        'gclid' => (string)($r['ctwa_clid'] ?? ''), 'page' => $url, 'how' => 'ctwa']);\n")
    new = ("    $adId = preg_replace('/\\D/', '', (string)($r['source_id'] ?? '')); $hl = trim((string)($r['headline'] ?? ''));" + C + "\n"
           "    $cmp = $adId !== '' ? 'iklan ' . $adId : $hl;\n"
           "    if ($adId !== '') { try { $inf = deiMetaAdInfo($adId, true); if (!empty($inf['campaign'])) $cmp = (string)$inf['campaign']; } catch (\\Throwable $e) { error_log('meta-campaign: ' . $e->getMessage()); } }\n"
           "    $a = deiWaAttrNorm(['src' => stripos($url, 'instagram') !== false ? 'instagram' : 'facebook',\n"
           "        'med' => ($type === '' || $type === 'ad') ? 'ctwa' : 'ctwa_' . $type, 'cmp' => $cmp,\n"
           "        'gclid' => (string)($r['ctwa_clid'] ?? ''), 'page' => $url, 'how' => 'ctwa']);\n"
           "    if ($adId !== '') $a['ad_id'] = $adId;\n"
           "    if ($hl !== '') $a['hl'] = mb_substr($hl, 0, 150);\n"
           "    return $a;\n")
    s = rep(s, old, new, 'referral')
    # apply: tandai baris dengan ad ID, pakai nama dari cache bila sudah ada
    s = rep(s, "    $row['wa_attr']      = (string)($a['how'] ?? 'ref');\n    return $row;\n",
               "    $row['wa_attr']      = (string)($a['how'] ?? 'ref');\n"
               "    if (!empty($a['ad_id'])) {" + C + "\n"
               "        $row['wa_ad'] = (string)$a['ad_id'];\n"
               "        if (!empty($a['hl'])) $row['wa_hl'] = (string)$a['hl'];\n"
               "        $row['utm_campaign'] = deiWaCmp($row);\n"
               "    }\n"
               "    return $row;\n", 'apply')
    s = rep(s, "/* ---------- v1.2.175: wa-atribusi — sumber iklan/UTM untuk chat WhatsApp ----------\n",
               FUNCS + "/* ---------- v1.2.175: wa-atribusi — sumber iklan/UTM untuk chat WhatsApp ----------\n", 'funcs')
    # laporan
    s = rep(s, "            $cmp = ($l['utm_campaign'] ?? '') !== '' ? $l['utm_campaign'] : '(none)';\n",
               "            $cmpV = deiWaCmp($l);" + C + "\n"
               "            $cmp = $cmpV !== '' ? $cmpV : '(none)';\n", 'report')
    s = rep(s, "            $cmp = ((string)($l['utm_campaign'] ?? '')) !== '' ? (string)$l['utm_campaign'] : '(none)';\n",
               "            $cmpV = deiWaCmp($l);" + C + "\n"
               "            $cmp = $cmpV !== '' ? $cmpV : '(none)';\n", 'stats')
    s = rep(s, "            $merged = deiMergeSettings($current, $incoming);\n",
               "            unset($incoming['meta_ads']);" + C + " — token hanya lewat meta_ads_save\n"
               "            $merged = deiMergeSettings($current, $incoming);\n", 'merge')
    # mask token di get_settings
    s = rep(s, "        // mask the API key\n",
               "        if (isset($s['meta_ads'])) $s['meta_ads'] = ['token_set' => !empty($raw['meta_ads']['token'])];" + C + "\n"
               "        // mask the API key\n", 'mask')
    s = rep(s, "    /* ---------- v1.2.175: wa-atribusi — widget mendaftarkan kode ref", ENDP + "    /* ---------- v1.2.175: wa-atribusi — widget mendaftarkan kode ref", 'endp')
    return s

def js(s):
    s = rep(s, "      if ($('#w_wa_attr')) $('#w_wa_attr').checked = w.wa_attr !== false;   // v1.2.175: wa-atribusi\n",
               "      if ($('#w_wa_attr')) $('#w_wa_attr').checked = w.wa_attr !== false;   // v1.2.175: wa-atribusi\n"
               "      if ($('#ma_status') && user && user.role === 'super_admin') { maBind(); maStatus(); }" + C + "\n", 'load')
    s = rep(s, "  /* ---- helpers --------------------------------------------------------- */\n",
               JSF + "\n  /* ---- helpers --------------------------------------------------------- */\n", 'funcs')
    return s

def html(s):
    old = ('          <div class="row"><label class="fl">Pesan Default</label><input type="text" id="w_wa_msg"></div>\n'
           '        </div>\n'
           '      </div>\n')
    return rep(s, old, old + CARD, 'card')

patch(API, api); patch(JS, js); patch(HTML, html)
