#!/usr/bin/env python3
"""v1.2.175 wa-atribusi (TENANT): chat WhatsApp membawa sumber iklan/UTM.
- Widget: klik link WhatsApp di situs ditandai kode "(ref #XXXXXX)" + UTM/gclid/referrer disimpan (action=wa_ref).
- Pesan WA dengan kode itu -> atribusi per nomor (30 hari), kode dibuang dari teks (AI & dashboard).
- Iklan Click-to-WhatsApp: `referral` (Meta Cloud API) / ctwaContext-externalAdReply (WAHA).
- Pengaturan: Status Widget > Lacak Sumber Iklan ke WhatsApp (widget.wa_attr, bawaan aktif).
Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'; HTML = T + '/dashboard/chatbot-ai/index.html'; W = T + '/assets/js/chat-widget.js'
TAG = 'v1.2.175: wa-atribusi'; stamp = time.strftime('%Y%m%d-%H%M%S')
NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    if not NOBAK: shutil.copy2(p, p + '.bak-v12175-' + stamp)
    wr(p, fn(s)); print('OK', p)
C = '   // ' + TAG

FUNCS = r'''/* ---------- v1.2.175: wa-atribusi — sumber iklan/UTM untuk chat WhatsApp ----------
 * Widget menandai klik link WhatsApp di situs dengan kode "(ref #XXXXXX)" dan menyimpan UTM-nya (action=wa_ref).
 * Pesan WA yang membawa kode itu -> atribusi disimpan per nomor (berlaku 30 hari), kodenya dibuang dari teks.
 * Iklan Click-to-WhatsApp: objek `referral` (Meta Cloud API) / ctwaContext-externalAdReply (WAHA). */
function deiWaRefRe() { return '/[ \t]*\(?\s*\bref\s*#\s*([A-HJ-NP-Z2-9]{6})\b\s*\)?/i'; }
function deiWaAttrNorm($a) {
    $a = is_array($a) ? $a : [];
    $c = function ($k, $n) use ($a) { $v = $a[$k] ?? ''; $v = is_scalar($v) ? (string)$v : ''; $v = (string)@preg_replace('/[\x00-\x1F\x7F]/u', '', $v); return mb_substr(trim($v), 0, $n); };
    return ['src' => $c('src', 80), 'med' => $c('med', 80), 'cmp' => $c('cmp', 150), 'gclid' => $c('gclid', 200),
            'page' => $c('page', 300), 'ref' => $c('ref', 300), 'how' => $c('how', 10)];
}
function deiWaRefSave($code, $a) {
    return deiWithLock('wa-refs', function () use ($code, $a) {
        $f = DATA_DIR . '/wa-refs.json'; $all = readJson($f, []); if (!is_array($all)) $all = [];
        $lim = time() - 30 * 86400;
        foreach ($all as $k => $v) { if (!is_array($v) || (int)($v['t'] ?? 0) < $lim) unset($all[$k]); }
        if (isset($all[$code])) return false;
        if (count($all) >= 5000) $all = array_slice($all, -4000, null, true);
        $all[$code] = deiWaAttrNorm($a) + ['t' => time()];
        writeJson($f, $all);
        return true;
    });
}
function deiWaRefGet($code) {
    $all = readJson(DATA_DIR . '/wa-refs.json', []);
    return (is_array($all) && is_array($all[$code] ?? null)) ? $all[$code] : null;
}
function deiWaReferralAttr($r) {
    if (!is_array($r) || !$r) return null;
    $url = (string)($r['source_url'] ?? ''); $type = strtolower((string)($r['source_type'] ?? ''));
    $cmp = trim((string)($r['headline'] ?? '')); if ($cmp === '' && !empty($r['source_id'])) $cmp = 'ad ' . $r['source_id'];
    return deiWaAttrNorm(['src' => stripos($url, 'instagram') !== false ? 'instagram' : 'facebook',
        'med' => ($type === '' || $type === 'ad') ? 'ctwa' : 'ctwa_' . $type, 'cmp' => $cmp,
        'gclid' => (string)($r['ctwa_clid'] ?? ''), 'page' => $url, 'how' => 'ctwa']);
}
function deiWaAttrSave($from, $a) {
    $num = preg_replace('/\D/', '', (string)$from);
    if ($num === '' || !is_array($a)) return;
    deiWithLock('wa-attr', function () use ($num, $a) {
        $f = DATA_DIR . '/wa-attr.json'; $all = readJson($f, []); if (!is_array($all)) $all = [];
        $lim = time() - 90 * 86400;
        foreach ($all as $k => $v) { if (!is_array($v) || (int)($v['t'] ?? 0) < $lim) unset($all[$k]); }
        unset($all[$num]); $a['t'] = time(); $all[$num] = $a;
        if (count($all) > 20000) $all = array_slice($all, -20000, null, true);
        writeJson($f, $all);
    });
}
/* Kode ref di teks -> simpan atribusi nomor ini; kembalikan teks tanpa kode. */
function deiWaAttrIngest($from, $text) {
    $text = (string)$text;
    if (!preg_match(deiWaRefRe(), $text, $m)) return $text;
    $code = strtoupper($m[1]);
    $r = deiWaRefGet($code);
    if ($r) { $a = deiWaAttrNorm($r); $a['how'] = 'ref'; $a['code'] = $code; deiWaAttrSave($from, $a); }
    $t = trim((string)preg_replace(deiWaRefRe(), '', $text));
    return $t !== '' ? $t : 'Halo';
}
function deiWaAttrFor($from) {
    $num = preg_replace('/\D/', '', (string)$from); if ($num === '') return null;
    $all = readJson(DATA_DIR . '/wa-attr.json', []);
    $a = (is_array($all) && is_array($all[$num] ?? null)) ? $all[$num] : null;
    if (!$a || time() - (int)($a['t'] ?? 0) > 30 * 86400) return null;
    return $a;
}
/* Baris log WA: ganti source/medium sintetis (whatsapp / chat) dengan atribusi nomor ini bila ada. */
function deiWaAttrApply($row, $from) {
    try { $a = deiWaAttrFor($from); } catch (\Throwable $e) { $a = null; }
    if (!$a) return $row;
    $row['utm_source']   = (string)($a['src'] ?? '');
    $row['utm_medium']   = (string)($a['med'] ?? '');
    $row['utm_campaign'] = (string)($a['cmp'] ?? '');
    $row['page']         = (string)($a['page'] ?? '');
    $row['referrer']     = (string)($a['ref'] ?? '');
    $row['wa_attr']      = (string)($a['how'] ?? 'ref');
    return $row;
}
/* WAHA: data iklan CTWA di _data (WEBJS ctwaContext / NOWEB-GOWS contextInfo.externalAdReply) -> bentuk `referral` Meta. */
function wahaAdReferral($p) {
    $d = is_array($p['_data'] ?? null) ? $p['_data'] : []; if (!$d) return null;
    $hit = null; $conv = '';
    $walk = function ($n, $depth) use (&$walk, &$hit, &$conv) {
        if ($hit !== null || $depth > 8 || !is_array($n)) return;
        foreach ($n as $k => $v) {
            if ($k === 'conversionSource' && is_string($v) && $conv === '') $conv = $v;
            if (($k === 'externalAdReply' || $k === 'ctwaContext') && is_array($v)) { $hit = $v; return; }
            if (is_array($v)) $walk($v, $depth + 1);
            if ($hit !== null) return;
        }
    };
    $walk($d, 0);
    if (!is_array($hit)) return null;
    $g = function ($ks) use ($hit) { foreach ($ks as $k) { if (isset($hit[$k]) && is_scalar($hit[$k]) && (string)$hit[$k] !== '') return (string)$hit[$k]; } return ''; };
    $sid = $g(['sourceId', 'source_id']); $clid = $g(['ctwaClid', 'ctwa_clid']);
    $typ = strtolower($g(['sourceType', 'source_type'])); if (!preg_match('/^[a-z_]+$/', $typ)) $typ = '';
    if ($sid === '' && $clid === '' && $typ !== 'ad' && stripos($conv, 'ad') === false) return null;
    return ['source_url' => $g(['sourceUrl', 'source_url']), 'source_type' => $typ !== '' ? $typ : 'ad', 'source_id' => $sid,
            'headline' => $g(['title', 'headline']), 'body' => $g(['body', 'description']), 'ctwa_clid' => $clid];
}

'''

WAREF = r'''    /* ---------- v1.2.175: wa-atribusi — widget mendaftarkan kode ref klik WhatsApp + UTM-nya (publik) ---------- */
    case 'wa_ref': {
        if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') jsonOut(['ok' => false, 'error' => 'Gunakan POST.'], 405);
        if (!checkRateLimit('waref:' . clientIp(), 120)) jsonOut(['ok' => false, 'error' => 'Terlalu banyak permintaan.'], 429);
        $in = json_decode((string)file_get_contents('php://input'), true);
        if (!is_array($in)) jsonOut(['ok' => false, 'error' => 'Data tidak valid.'], 400);
        $code = strtoupper(trim((string)($in['code'] ?? '')));
        if (!preg_match('/^[A-HJ-NP-Z2-9]{6}$/', $code)) jsonOut(['ok' => false, 'error' => 'Kode tidak valid.'], 400);
        $ok = deiWaRefSave($code, ['src' => $in['src'] ?? '', 'med' => $in['med'] ?? '', 'cmp' => $in['cmp'] ?? '', 'gclid' => $in['gclid'] ?? '',
                                   'page' => $in['page'] ?? '', 'ref' => $in['ref'] ?? '']);
        jsonOut(['ok' => (bool)$ok]);
        break;
    }

'''

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.174');   // v1.2.174:",
               "define('DEI_VERSION', 'v1.2.175');   // " + TAG + " — chat WhatsApp membawa sumber iklan/UTM (kode ref dari situs, iklan CTWA); v1.2.174:", 'versi')
    s = rep(s, "'gc_submit'];   // v1.2.56; v1.2.109: guest-comment",
               "'gc_submit', 'wa_ref'];   // v1.2.56; v1.2.109: guest-comment; " + TAG, 'public')
    s = rep(s, "function waProcessIncoming($s, $wa, $from, $text, $senderName = '', $metaInfo = []) {\n"
               "    $logLimit = (int)($s['api']['log_limit'] ?? 500);\n"
               "    $keepCtx  = ($wa['keep_context'] ?? true);\n",
            FUNCS +
               "function waProcessIncoming($s, $wa, $from, $text, $senderName = '', $metaInfo = []) {\n"
               "    $logLimit = (int)($s['api']['log_limit'] ?? 500);\n"
               "    $keepCtx  = ($wa['keep_context'] ?? true);\n"
               "    // " + TAG + " — kode ref dari situs -> sumber chat nomor ini; kode dibuang dari teks\n"
               "    try {\n"
               "        $text = deiWaAttrIngest($from, $text);\n"
               "        if (isset($metaInfo['_q_show'])) $metaInfo['_q_show'] = trim((string)preg_replace(deiWaRefRe(), '', (string)$metaInfo['_q_show']));\n"
               "    } catch (\\Throwable $e) { error_log('wa-atribusi: ' . $e->getMessage()); }\n", 'ingest')
    s = rep(s, "    if (isset($metaInfo['_q_show'])) $logBase['q'] = (string)$metaInfo['_q_show'];   // v1.2.94: wa-media\n",
               "    $logBase = deiWaAttrApply($logBase, $from);" + C + "\n"
               "    if (isset($metaInfo['_q_show'])) $logBase['q'] = (string)$metaInfo['_q_show'];   // v1.2.94: wa-media\n", 'logBase')
    s = rep(s, "'utm_medium' => 'chat', 'utm_campaign' => '', 'page' => '', 'referrer' => '', 'gc' => 1];\n",
               "'utm_medium' => 'chat', 'utm_campaign' => '', 'page' => '', 'referrer' => '', 'gc' => 1];\n"
               "    $log = deiWaAttrApply($log, $from);" + C + "\n", 'gc log')
    s = rep(s, "    $GLOBALS['dei_in_ctx'] = is_array($msg['context'] ?? null) ? $msg['context'] : null;   // v1.2.121: pelanggan mengutip pesan\n",
               "    $GLOBALS['dei_in_ctx'] = is_array($msg['context'] ?? null) ? $msg['context'] : null;   // v1.2.121: pelanggan mengutip pesan\n"
               "    if (is_array($msg['referral'] ?? null) && $msg['referral']) {   // " + TAG + " — iklan Click-to-WhatsApp (disimpan sebelum debounce)\n"
               "        try { deiWaAttrSave($from, deiWaReferralAttr($msg['referral'])); } catch (\\Throwable $e) { error_log('wa-atribusi ctwa: ' . $e->getMessage()); }\n"
               "    }\n", 'meta referral')
    s = rep(s, "    $msg = ['from' => $num, 'id' => $id, 'type' => $type];\n    $rt121",
               "    $msg = ['from' => $num, 'id' => $id, 'type' => $type];\n"
               "    try { $ref175 = wahaAdReferral($p); if ($ref175) $msg['referral'] = $ref175; } catch (\\Throwable $e) {}" + C + "\n"
               "    $rt121", 'waha referral')
    s = rep(s, "    case 'bootstrap': {\n", WAREF + "    case 'bootstrap': {\n", 'wa_ref')
    s = rep(s, "                'whatsapp_message' => $s['widget']['whatsapp_message'] ?? '',\n",
               "                'whatsapp_message' => $s['widget']['whatsapp_message'] ?? '',\n"
               "                'wa_attr'          => (bool)($s['widget']['wa_attr'] ?? true)," + C + "\n", 'bootstrap')
    s = rep(s, "$allowedWidget = ['chatbot_enabled', 'whatsapp_enabled', 'whatsapp_number', 'whatsapp_message', 'lead_form'];   // v1.2.53",
               "$allowedWidget = ['chatbot_enabled', 'whatsapp_enabled', 'whatsapp_number', 'whatsapp_message', 'lead_form', 'wa_attr'];   // v1.2.53; " + TAG, 'allowed')
    return s

def js(s):
    s = rep(s, "      $('#w_whatsapp').checked = w.whatsapp_enabled !== false;\n",
               "      $('#w_whatsapp').checked = w.whatsapp_enabled !== false;\n"
               "      if ($('#w_wa_attr')) $('#w_wa_attr').checked = w.wa_attr !== false;" + C + "\n", 'load')
    s = rep(s, "        whatsapp_enabled: $('#w_whatsapp').checked,\n",
               "        whatsapp_enabled: $('#w_whatsapp').checked,\n"
               "        wa_attr: $('#w_wa_attr') ? $('#w_wa_attr').checked : true," + C + "\n", 'save')
    return s

def html(s):
    old = ('          <label class="switch"><input type="checkbox" id="w_whatsapp"><span class="sl"></span></label></div>\n')
    return rep(s, old, old +
        '        <div class="toggle-row"><div><div class="tt">Lacak Sumber Iklan ke WhatsApp</div><div class="td">Klik tombol/link WhatsApp di website diberi kode ref singkat, supaya chat WA tercatat dengan source / medium / campaign asli (UTM, Google Ads, Meta). Iklan Click-to-WhatsApp terbaca otomatis.</div></div>\n'
        '          <label class="switch"><input type="checkbox" id="w_wa_attr"><span class="sl"></span></label></div><!-- ' + TAG + ' -->\n', 'toggle')

WJS = r'''
  /* ---- v1.2.175: wa-atribusi — UTM / klik iklan dibawa ke chat WhatsApp lewat kode ref ---- */
  var WA_ATTR_ON = false, WA_DEF_MSG = '';
  var ATTR_KEY = 'dei_attr', ATTR_TTL = 30 * 864e5;
  var WA_RE = /^(https?:\/\/)?(wa\.me|api\.whatsapp\.com|web\.whatsapp\.com|(www\.)?whatsapp\.com\/send)|^whatsapp:\/\/send/i;
  var REF_RE = /\(?\s*\bref\s*#\s*[A-HJ-NP-Z2-9]{6}\b\s*\)?/i;
  function attrNow() {
    var p; try { p = new URLSearchParams(window.location.search); } catch (e) { return null; }
    var s = p.get('utm_source') || '', m = p.get('utm_medium') || '', c = p.get('utm_campaign') || '';
    var g = p.get('gclid') || p.get('gbraid') || p.get('wbraid') || '', fb = p.get('fbclid') || '', tt = p.get('ttclid') || '';
    var r = document.referrer || '', h = '', a = null;
    try { h = r ? new URL(r).hostname.replace(/^www\./, '') : ''; } catch (e) {}
    if (s || m || c) a = { src: s, med: m, cmp: c };
    else if (g) a = { src: 'google', med: 'cpc', cmp: '' };
    else if (tt) a = { src: 'tiktok', med: 'cpc', cmp: '' };
    else if (fb) a = { src: 'facebook', med: 'social', cmp: '' };
    else if (h && h !== location.hostname.replace(/^www\./, '')) {
      var se = h.match(/(^|\.)(google|bing|yahoo|duckduckgo|yandex|ecosia|baidu)\./i);
      var so = h.match(/(^|\.)(facebook|instagram|tiktok|youtube|linkedin|twitter|x|t)\.(com|co)$/i);
      a = se ? { src: se[2].toLowerCase(), med: 'organic', cmp: '' } : (so ? { src: so[2].toLowerCase(), med: 'social', cmp: '' } : { src: h, med: 'referral', cmp: '' });
    }
    if (a) { a.gclid = g; a.page = (location.pathname + location.search).slice(0, 300); a.ref = r.slice(0, 300); a.t = Date.now(); }
    return a;
  }
  function attrGet() {   /* sentuhan terakhir yang bukan direct, berlaku 30 hari */
    var now = attrNow(), old = null;
    if (now) { try { localStorage.setItem(ATTR_KEY, JSON.stringify(now)); } catch (e) {} return now; }
    try { old = JSON.parse(localStorage.getItem(ATTR_KEY) || 'null'); } catch (e) {}
    return (old && old.t && Date.now() - old.t < ATTR_TTL) ? old : null;
  }
  attrGet();
  function waCode() {
    var ch = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789', s = '', r = null;
    try { r = window.crypto.getRandomValues(new Uint8Array(6)); } catch (e) {}
    for (var i = 0; i < 6; i++) s += ch.charAt((r ? r[i] : Math.floor(Math.random() * 256)) % 32);
    return s;
  }
  function waSendRef(code, a) {
    var body = JSON.stringify({ code: code, src: a.src || '', med: a.med || '', cmp: a.cmp || '', gclid: a.gclid || '', page: a.page || '', ref: a.ref || '' });
    var url = API + '?action=wa_ref';
    try { if (navigator.sendBeacon && navigator.sendBeacon(url, new Blob([body], { type: 'text/plain' }))) return; } catch (e) {}
    try { fetch(url, { method: 'POST', body: body, keepalive: true, mode: 'no-cors', headers: { 'Content-Type': 'text/plain' } }); } catch (e) {}
  }
  function waTag(url) {
    if (!WA_ATTR_ON || typeof url !== 'string' || !WA_RE.test(url)) return url;
    var u; try { u = new URL(url, location.href); } catch (e) { return url; }
    var t = u.searchParams.get('text') || '';
    if (REF_RE.test(t)) return url;
    var code = waCode();
    waSendRef(code, attrGet() || { src: '', med: '', cmp: '', page: (location.pathname + location.search).slice(0, 300), ref: (document.referrer || '').slice(0, 300) });
    u.searchParams.delete('text');
    var q = u.searchParams.toString();
    u.search = (q ? q + '&' : '') + 'text=' + encodeURIComponent((t || WA_DEF_MSG || 'Halo, saya mau tanya.') + ' (ref #' + code + ')');
    return u.toString();
  }
  function waOnClick(e) {
    if (!WA_ATTR_ON) return;
    var n = e.target;
    while (n && n.nodeType === 1 && n.tagName !== 'A') n = n.parentNode;
    if (!n || n.nodeType !== 1) return;
    var h = n.getAttribute('href') || '';
    if (WA_RE.test(h)) { var t = waTag(h); if (t !== h) n.setAttribute('href', t); }
  }
  document.addEventListener('click', waOnClick, true);
  document.addEventListener('auxclick', waOnClick, true);
  try {
    var deiOpen = window.open;
    window.open = function (u) { var a = Array.prototype.slice.call(arguments); if (typeof u === 'string') a[0] = waTag(u); return deiOpen.apply(window, a); };
  } catch (e) {}
'''

def widget(s):
    s = rep(s, "/* DEI AI Chat Widget v1.2.58 —", "/* DEI AI Chat Widget v1.2.175 (" + TAG + ") —", 'header')
    s = rep(s, "  /* ---- helpers --------------------------------------------------------- */\n",
               WJS + "\n  /* ---- helpers --------------------------------------------------------- */\n", 'blok')
    s = rep(s, "  function init(cfg) {\n", "  function init(cfg) {\n    WA_ATTR_ON = cfg.wa_attr !== false; WA_DEF_MSG = cfg.whatsapp_message || '';" + C + "\n", 'init')
    return s

patch(API, api); patch(JS, js); patch(HTML, html); patch(W, widget)
