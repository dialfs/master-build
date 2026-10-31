#!/usr/bin/env python3
r"""v1.2.132 kb-url: tambah Knowledge Base dari link URL halaman website.
- API kb_fetch_url (admin/super_admin): server mengambil halaman (hanya http/https publik; IP privat/lokal
  ditolak, tiap redirect dicek ulang, IP dipaku lewat CURLOPT_RESOLVE), teks dibersihkan, dikembalikan
  ke dashboard beserta daftar link halaman lain di domain yang sama.
- Dashboard: tombol "Impor URL" di tab Entri KB. Teks dipotong lalu disusun AI lewat kb_from_text
  (sama seperti Impor PDF). Entri belum tersimpan sampai klik Simpan Perubahan.
Pakai: python3 patch_v12132_kb_url.py [~/Herd/dei-tenant] (idempoten; butuh v1.2.131)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.132: kb-url'
NEED = 'v1.2.131: selesai-spv'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def rep(s, old, new, rel):
    n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:100]); return s.replace(old, new)
def patch(rel, fn):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    assert NEED in s, rel + ': butuh v1.2.131'
    s2 = fn(s, rel); assert TAG in s2, rel
    shutil.copy2(p, p + '.bak-v12132-' + STAMP)
    open(p, 'w', encoding='utf-8').write(s2); print('OK', rel)

PHP_HELPERS = r'''/* ============================================================================
 * v1.2.132: kb-url — impor Knowledge Base dari URL halaman website.
 * Server mengambil halaman (hanya http/https ke IP publik; IP privat/lokal
 * ditolak, tiap redirect dicek ulang & IP dipaku lewat CURLOPT_RESOLVE supaya
 * tidak bisa dibelokkan DNS), teks dibersihkan lalu dikembalikan ke dashboard.
 * Penyusunan entri tetap lewat kb_from_text (sama seperti Impor PDF).
 * ========================================================================= */
define('KB_URL_MAX_BYTES', 3 * 1024 * 1024);
define('KB_URL_MAX_TEXT', 60000);
function deiKbUrlIpPublic($ip) {
    if (stripos($ip, '::ffff:') === 0 && filter_var(substr($ip, 7), FILTER_VALIDATE_IP, FILTER_FLAG_IPV4)) $ip = substr($ip, 7);
    if (!filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE)) return false;
    if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4)) {
        $n = ip2long($ip);
        if (($n & 0xFFC00000) === (ip2long('100.64.0.0') & 0xFFC00000)) return false;   // CGNAT 100.64/10
        if (($n & 0xFF000000) === 0) return false;                                       // 0.0.0.0/8
    } else {
        $l = strtolower($ip);
        if (strpos($l, 'fc') === 0 || strpos($l, 'fd') === 0 || strpos($l, 'fe8') === 0 || $l === '::1' || $l === '::') return false;
    }
    return true;
}
function deiKbUrlHostIps($host) {
    if (filter_var($host, FILTER_VALIDATE_IP)) return [$host];
    $ips = [];
    $recs = @dns_get_record($host, DNS_A | DNS_AAAA);
    foreach ((array)$recs as $r) { if (!empty($r['ip'])) $ips[] = $r['ip']; if (!empty($r['ipv6'])) $ips[] = $r['ipv6']; }
    if (!$ips) { $v4 = @gethostbynamel($host); if ($v4) $ips = $v4; }
    return array_values(array_unique($ips));
}
function deiKbUrlFetch($url) {
    for ($hop = 0; $hop <= 5; $hop++) {
        $p = parse_url($url);
        $sch = strtolower((string)($p['scheme'] ?? ''));
        $host = strtolower(trim((string)($p['host'] ?? ''), '[]'));
        if (!in_array($sch, ['http', 'https'], true) || $host === '') return [false, 'URL harus diawali http:// atau https://.'];
        if (isset($p['user']) || isset($p['pass'])) return [false, 'URL berisi username/password tidak didukung.'];
        $port = (int)($p['port'] ?? ($sch === 'https' ? 443 : 80));
        if (!in_array($port, [80, 443, 8080, 8443], true)) return [false, 'Port ' . $port . ' tidak diizinkan.'];
        if ($host === 'localhost' || preg_match('/\.(local|localhost|internal|lan|home|test)$/', $host)) return [false, 'Alamat lokal tidak diizinkan.'];
        $ips = deiKbUrlHostIps($host);
        if (!$ips) return [false, 'Domain tidak ditemukan: ' . $host];
        foreach ($ips as $ip) { if (!deiKbUrlIpPublic($ip)) return [false, 'Alamat jaringan internal tidak diizinkan.']; }
        $body = ''; $tooBig = false;
        $ch = curl_init($url);
        $opt = [
            CURLOPT_FOLLOWLOCATION => false,
            CURLOPT_CONNECTTIMEOUT => 8, CURLOPT_TIMEOUT => 25,
            CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; DEI-Chatbot-KB/1.0; +https://deintegra.com)',
            CURLOPT_HTTPHEADER => ['Accept: text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5', 'Accept-Language: id,en;q=0.8'],
            CURLOPT_ENCODING => '',
            CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_WRITEFUNCTION => function ($c, $d) use (&$body, &$tooBig) {
                $body .= $d;
                if (strlen($body) > KB_URL_MAX_BYTES) { $tooBig = true; return 0; }
                return strlen($d);
            },
        ];
        if (defined('CURLOPT_PROTOCOLS')) $opt[CURLOPT_PROTOCOLS] = CURLPROTO_HTTP | CURLPROTO_HTTPS;
        if (!filter_var($host, FILTER_VALIDATE_IP)) {
            $ip = $ips[0];
            $opt[CURLOPT_RESOLVE] = [$host . ':' . $port . ':' . (strpos($ip, ':') !== false ? '[' . $ip . ']' : $ip)];
        }
        curl_setopt_array($ch, $opt);
        curl_exec($ch);
        $err  = curl_errno($ch) ? curl_error($ch) : '';
        $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $ct   = (string)curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
        $loc  = (string)curl_getinfo($ch, CURLINFO_REDIRECT_URL);
        curl_close($ch);
        if ($code >= 300 && $code < 400 && $loc !== '') { $url = $loc; continue; }
        if ($err !== '' && !$tooBig) return [false, 'Gagal mengambil halaman: ' . $err];
        if ($code >= 400) return [false, 'Halaman merespons HTTP ' . $code . ($code == 403 ? ' (situs menolak akses otomatis)' : '') . '.'];
        if (stripos($ct, 'pdf') !== false) return [false, 'Link ini file PDF — unduh dulu lalu gunakan Impor PDF.'];
        if ($ct !== '' && !preg_match('#text/|html|xml#i', $ct)) return [false, 'Isi link bukan halaman web (' . $ct . ').'];
        return [true, ['body' => $body, 'ctype' => $ct, 'url' => $url]];
    }
    return [false, 'Terlalu banyak redirect.'];
}
function deiKbUrlAbs($href, $base) {
    $href = trim(html_entity_decode((string)$href, ENT_QUOTES | ENT_HTML5, 'UTF-8'));
    if ($href === '' || $href[0] === '#' || preg_match('#^(mailto|tel|javascript|data|whatsapp|sms):#i', $href)) return '';
    $b = parse_url($base); $origin = $b['scheme'] . '://' . $b['host'] . (isset($b['port']) ? ':' . $b['port'] : '');
    if (preg_match('#^https?://#i', $href)) $u = $href;
    elseif (strpos($href, '//') === 0) $u = $b['scheme'] . ':' . $href;
    elseif ($href[0] === '/') $u = $origin . $href;
    elseif ($href[0] === '?') $u = $origin . ($b['path'] ?? '/') . $href;
    else { $dir = preg_replace('#/[^/]*$#', '/', $b['path'] ?? '/'); $u = $origin . $dir . $href; }
    $u = preg_replace('/#.*$/', '', $u);
    $q = parse_url($u); if (!$q || empty($q['host'])) return '';
    $path = $q['path'] ?? '/'; $segs = [];
    foreach (explode('/', $path) as $sg) { if ($sg === '..') array_pop($segs); elseif ($sg !== '.') $segs[] = $sg; }
    $path = implode('/', $segs); if ($path === '' || $path[0] !== '/') $path = '/' . $path;
    return strtolower($q['scheme']) . '://' . strtolower($q['host']) . (isset($q['port']) ? ':' . $q['port'] : '') . $path . (isset($q['query']) ? '?' . $q['query'] : '');
}
function deiKbUrlWalk($node, &$out) {
    static $blocks = ['p'=>1,'div'=>1,'section'=>1,'article'=>1,'main'=>1,'header'=>1,'footer'=>1,'aside'=>1,'ul'=>1,'ol'=>1,
        'table'=>1,'tr'=>1,'dl'=>1,'dt'=>1,'dd'=>1,'blockquote'=>1,'pre'=>1,'address'=>1,'figure'=>1,'figcaption'=>1,'hr'=>1,'details'=>1,'summary'=>1];
    foreach ($node->childNodes as $c) {
        if ($c->nodeType === XML_TEXT_NODE || $c->nodeType === XML_CDATA_SECTION_NODE) { $out .= preg_replace('/\s+/u', ' ', $c->nodeValue); continue; }
        if ($c->nodeType !== XML_ELEMENT_NODE) continue;
        $t = strtolower($c->nodeName);
        if ($t === 'br') { $out .= "\n"; continue; }
        if (preg_match('/^h([1-6])$/', $t, $m)) { $out .= "\n\n" . str_repeat('#', min(3, (int)$m[1])) . ' '; deiKbUrlWalk($c, $out); $out .= "\n"; continue; }
        if ($t === 'li') { $out .= "\n- "; deiKbUrlWalk($c, $out); $out .= "\n"; continue; }
        if ($t === 'td' || $t === 'th') { deiKbUrlWalk($c, $out); $out .= ' | '; continue; }
        if ($t === 'img') { $alt = trim((string)$c->getAttribute('alt')); if (mb_strlen($alt) > 15) $out .= ' ' . $alt . ' '; continue; }
        $blk = isset($blocks[$t]);
        if ($blk) $out .= "\n";
        deiKbUrlWalk($c, $out);
        if ($blk) $out .= "\n";
    }
}
function deiKbUrlToText($html, $ctype, $url) {
    $cs = '';
    if (preg_match('/charset=["\']?([\w.:-]+)/i', $ctype, $m)) $cs = $m[1];
    elseif (preg_match('/<meta[^>]+charset=["\']?([\w.:-]+)/i', substr($html, 0, 4096), $m)) $cs = $m[1];
    try {
        if ($cs !== '' && !in_array(strtoupper($cs), ['UTF-8', 'UTF8'], true)) { $c = @mb_convert_encoding($html, 'UTF-8', $cs); if (is_string($c) && $c !== '') $html = $c; }
        elseif (!mb_check_encoding($html, 'UTF-8')) $html = mb_convert_encoding($html, 'UTF-8', 'Windows-1252');
    } catch (\Throwable $e) { if (!mb_check_encoding($html, 'UTF-8')) $html = mb_convert_encoding($html, 'UTF-8', 'Windows-1252'); }

    $title = ''; $desc = ''; $text = ''; $links = [];
    $isHtml = stripos($ctype, 'html') !== false || stripos($ctype, 'xml') !== false || preg_match('/<(html|body|div|p)\b/i', substr($html, 0, 5000));
    if (!$isHtml) {
        $text = $html;
    } elseif (class_exists('DOMDocument')) {
        $d = new DOMDocument();
        $prev = libxml_use_internal_errors(true);
        $d->loadHTML('<?xml encoding="UTF-8">' . $html, LIBXML_NOWARNING | LIBXML_NOERROR | LIBXML_NONET | LIBXML_COMPACT);
        libxml_clear_errors(); libxml_use_internal_errors($prev);
        $x = new DOMXPath($d);
        $n = $x->query('//title')->item(0); if ($n) $title = trim(preg_replace('/\s+/u', ' ', $n->textContent));
        foreach (['//meta[@name="description"]/@content', '//meta[@property="og:description"]/@content'] as $q) {
            $n = $x->query($q)->item(0); if ($n && trim($n->nodeValue) !== '') { $desc = trim($n->nodeValue); break; }
        }
        $baseN = $x->query('//base/@href')->item(0); $base = $baseN ? deiKbUrlAbs($baseN->nodeValue, $url) : '';
        if ($base === '') $base = $url;
        $h0 = preg_replace('/^www\./', '', strtolower((string)parse_url($url, PHP_URL_HOST)));
        $self = preg_replace('/\/$/', '', $url);
        foreach ($x->query('//a[@href]') as $a) {   // link diambil sebelum menu dibuang — menu biasanya berisi halaman penting
            $u = deiKbUrlAbs($a->getAttribute('href'), $base);
            if ($u === '' || preg_replace('/^www\./', '', (string)parse_url($u, PHP_URL_HOST)) !== $h0) continue;
            if (preg_match('/\.(jpe?g|png|gif|webp|svg|ico|css|js|zip|rar|mp4|mp3|webm|xml|json|docx?|xlsx?|pptx?)(\?|$)/i', $u)) continue;
            if (preg_match('#/(wp-admin|wp-login|login|logout|cart|checkout|my-account|feed)(/|$|\?)#i', $u)) continue;
            $k = preg_replace('/\/$/', '', $u);
            if ($k === $self || isset($links[$k])) continue;
            $lt = trim(preg_replace('/\s+/u', ' ', $a->textContent));
            $links[$k] = ['url' => $u, 'text' => mb_substr($lt !== '' ? $lt : (string)$a->getAttribute('title'), 0, 80)];
            if (count($links) >= 80) break;
        }
        $drop = [];
        foreach (['script','style','noscript','svg','iframe','template','nav','form','button','select','canvas','object','embed','video','audio','map'] as $tg) {
            foreach ($d->getElementsByTagName($tg) as $n) $drop[] = $n;
        }
        foreach ($x->query('//*[@hidden] | //*[@aria-hidden="true"] | //*[contains(translate(@style," ",""),"display:none")]'
            . ' | //*[contains(@class,"cookie") or contains(@id,"cookie")]') as $n) $drop[] = $n;
        foreach ($drop as $n) { if ($n->parentNode) $n->parentNode->removeChild($n); }
        $body = $d->getElementsByTagName('body')->item(0) ?: $d->documentElement;
        if ($body) deiKbUrlWalk($body, $text);
    } else {
        if (preg_match('/<title[^>]*>(.*?)<\/title>/is', $html, $m)) $title = trim(html_entity_decode(strip_tags($m[1]), ENT_QUOTES | ENT_HTML5, 'UTF-8'));
        if (preg_match('/<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)/i', $html, $m)) $desc = html_entity_decode($m[1], ENT_QUOTES | ENT_HTML5, 'UTF-8');
        $h = preg_replace('#<(script|style|noscript|svg|iframe|template|nav|form|button|select|head)\b.*?</\1>#is', ' ', $html);
        $h = preg_replace('#<!--.*?-->#s', ' ', $h);
        $h = preg_replace('#<(h[1-6])\b[^>]*>#i', "\n\n## ", $h);
        $h = preg_replace('#<li\b[^>]*>#i', "\n- ", $h);
        $h = preg_replace('#</?(p|div|section|article|main|header|footer|aside|ul|ol|table|tr|dl|dt|dd|blockquote|pre|address|br|hr|h[1-6]|li)\b[^>]*>#i', "\n", $h);
        $h = preg_replace('#</t[dh]>#i', ' | ', $h);
        $text = html_entity_decode(strip_tags($h), ENT_QUOTES | ENT_HTML5, 'UTF-8');
    }
    // rapikan: spasi, baris kosong, baris berulang
    $lines = []; $prev = null; $seen = [];
    foreach (preg_split('/\r\n|\r|\n/', $text) as $ln) {
        $ln = trim(preg_replace('/[ \t\x{00A0}]+/u', ' ', $ln), " |");
        if ($ln === '' || $ln === '-' || $ln === '#') { if ($prev !== '') $lines[] = ''; $prev = ''; continue; }
        $k = mb_strtolower($ln);
        if ($k === $prev || (mb_strlen($ln) < 120 && isset($seen[$k]) && $seen[$k] >= 2)) continue;   // menu/teks yang berulang-ulang
        $seen[$k] = ($seen[$k] ?? 0) + 1;
        $lines[] = $ln; $prev = $k;
    }
    $text = trim(implode("\n", $lines));
    if ($desc !== '' && mb_stripos($text, mb_substr($desc, 0, 60)) === false) $text = $desc . "\n\n" . $text;
    return ['title' => mb_substr($title, 0, 160), 'text' => mb_substr($text, 0, KB_URL_MAX_TEXT), 'full_chars' => mb_strlen($text), 'links' => array_values($links)];
}

'''

PHP_CASE = r'''    case 'kb_fetch_url': {   // v1.2.132: kb-url — ambil teks halaman web (tidak menyimpan apa pun)
        requireAuth(['super_admin', 'admin']);
        @set_time_limit(90);
        if (!function_exists('curl_init')) jsonOut(['ok' => false, 'error' => 'Ekstensi cURL tidak tersedia di server.'], 500);
        $in = bodyInput();
        $url = trim((string)($in['url'] ?? ''));
        if ($url !== '' && !preg_match('#^[a-z][a-z0-9+.-]*://#i', $url)) $url = 'https://' . $url;
        if ($url === '' || strlen($url) > 2000 || !filter_var($url, FILTER_VALIDATE_URL)) jsonOut(['ok' => false, 'error' => 'URL tidak valid.'], 422);
        list($okF, $r) = deiKbUrlFetch($url);
        if (!$okF) jsonOut(['ok' => false, 'error' => $r], 422);
        $res = deiKbUrlToText($r['body'], $r['ctype'], $r['url']);
        jsonOut(['ok' => true, 'url' => $r['url'], 'title' => $res['title'], 'text' => $res['text'],
                 'chars' => mb_strlen($res['text']), 'truncated' => $res['full_chars'] > KB_URL_MAX_TEXT, 'links' => $res['links']]);
        break;
    }

    case 'kb_from_text': {'''

def f_api(s, rel):
    s = rep(s, "define('DEI_VERSION', 'v1.2.131');   // v1.2.131: selesai-spv",
               "define('DEI_VERSION', 'v1.2.132');   // " + TAG, rel)
    s = rep(s, "/* ============================================================================\n * v1.2.95: kb-foto",
               PHP_HELPERS + "/* ============================================================================\n * v1.2.95: kb-foto", rel)
    s = rep(s, "    case 'kb_from_text': {", PHP_CASE, rel)
    s = rep(s, '             . "- Abaikan daftar isi, header/footer, nomor halaman, dan teks yang tidak berguna bagi customer.\\n"',
               '             . "- Abaikan daftar isi, header/footer, nomor halaman, dan teks yang tidak berguna bagi customer.\\n"\n'
               '             . "- Untuk halaman website: abaikan menu navigasi, banner cookie, tombol, ajakan berlangganan, dan teks hak cipta.\\n"   // ' + TAG, rel)
    return s

JS_FN = r'''  /* ---- v1.2.132: kb-url — impor dari URL halaman website (server ambil teks, AI menyusun entri via kb_from_text) ---- */
  var KB_URL_MAX = 10;
  function openKbUrl(prefill) {
    var box = document.getElementById('pdfResult');
    box.style.display = '';
    box.innerHTML = '<h3 style="margin-top:0">' + ico('globe', 16) + ' Impor dari URL Website</h3>' +
      '<p class="help" style="margin:0 0 8px">Tempel link halaman (satu per baris, maks ' + KB_URL_MAX + '). Sistem membaca isi halaman lalu AI menyusun entri KB. ' +
      'Halaman yang isinya dimuat lewat JavaScript atau dilindungi login mungkin tidak terbaca.</p>' +
      '<textarea id="kbUrlInput" rows="4" style="width:100%" placeholder="https://contoh.com/fasilitas&#10;https://contoh.com/harga">' + esc(prefill || '') + '</textarea>' +
      '<div style="display:flex;gap:8px;margin-top:10px"><button class="btn" id="btnKbUrlGo">Ambil &amp; Susun Entri</button>' +
      '<button class="btn ghost" id="btnKbUrlCancel">Batal</button></div>';
    var ta = document.getElementById('kbUrlInput'); ta.focus();
    document.getElementById('btnKbUrlCancel').onclick = function () { box.style.display = 'none'; };
    document.getElementById('btnKbUrlGo').onclick = function () {
      var seen = {}, urls = ta.value.split(/[\s,]+/).map(function (u) { return u.trim(); })
        .filter(function (u) { if (!u || seen[u]) return false; seen[u] = 1; return /^(https?:\/\/)?[^\s\/]+\.[^\s\/]+/i.test(u); });
      if (!urls.length) { toast('Masukkan minimal satu link halaman.', true); return; }
      if (urls.length > KB_URL_MAX) { toast('Maksimal ' + KB_URL_MAX + ' link sekali impor. ' + urls.length + ' link dimasukkan.', true); return; }
      importKbUrls(urls);
    };
  }
  function importKbUrls(urls) {
    var box = document.getElementById('pdfResult');
    var stop = false, added = 0, ui = 0, phase = '', pct = 0, results = [], found = {}, done = {};
    box.style.display = '';
    var show = function (html) { box.innerHTML = '<h3 style="margin-top:0">' + ico('globe', 16) + ' Impor dari URL Website</h3>' + html; };
    var progress = function () {
      show('<div style="display:flex;align-items:center;gap:12px">' +
        '<div style="flex:1;height:8px;background:var(--bg);border-radius:6px;overflow:hidden">' +
        '<div style="height:100%;width:' + pct + '%;background:var(--brand);transition:width .3s"></div></div>' +
        '<span class="help">Halaman ' + Math.min(ui + 1, urls.length) + ' / ' + urls.length + ' · ' + added + ' entri</span>' +
        '<button class="btn ghost sm" id="btnUrlStop">Hentikan</button></div>' +
        '<p class="help" style="margin-top:8px;word-break:break-all">' + esc(phase) + '</p>');
      var b = document.getElementById('btnUrlStop'); if (b) b.onclick = function () { stop = true; b.disabled = true; b.textContent = 'Menghentikan…'; };
    };
    var one = function (url) {
      var r = { url: url, title: '', entries: 0, error: '', note: '' };
      results.push(r);
      phase = 'Mengambil ' + url + ' …'; pct = Math.round(ui / urls.length * 100); progress();
      return api('kb_fetch_url', { method: 'POST', body: { url: url } }).then(function (res) {
        if (!res || !res.ok) { r.error = (res && res.error) || 'Respons tidak valid dari server.'; return; }
        r.url = res.url || url; r.title = res.title || '';
        done[String(r.url).replace(/\/$/, '')] = 1; done[String(url).replace(/\/$/, '')] = 1;
        (res.links || []).forEach(function (l) { var k = String(l.url).replace(/\/$/, ''); if (!found[k]) found[k] = l; });
        if ((res.chars || 0) < 80) { r.note = 'Teks halaman hampir kosong — kemungkinan dimuat lewat JavaScript. Salin isinya manual atau gunakan PDF.'; return; }
        if (res.truncated) r.note = 'Halaman sangat panjang; hanya 60.000 karakter pertama yang diproses.';
        var host = ''; try { host = new URL(r.url).hostname.replace(/^www\./, ''); } catch (e) {}
        var src = (r.title || host || 'Website').slice(0, 80);
        var chunks = chunkText([res.text], 7000), ci = 0;
        var nextChunk = function () {
          if (stop || ci >= chunks.length) return;
          phase = 'AI menyusun entri dari "' + src + '" (bagian ' + (ci + 1) + ' / ' + chunks.length + ') …';
          pct = Math.round((ui + (ci + 0.5) / chunks.length) / urls.length * 100); progress();
          return api('kb_from_text', { method: 'POST', body: { text: chunks[ci], source: src + ' — ' + r.url } }).then(function (rs) {
            if (rs && rs.ok) {
              (rs.entries || []).forEach(function (e, k) {
                kbData.unshift({ id: 'kb_' + Date.now() + '_' + ui + '_' + ci + '_' + k, category: e.category || host || 'Website', title: e.title || '', content: e.content || '', topic: '' });
                added++; r.entries++;
              });
              if ((rs.entries || []).length) { kbMarkDirty(); renderKb(); }
            } else {
              r.error = (rs && rs.error) || 'Respons tidak valid dari server.';
              if (/API key|belum dikonfigurasi/i.test(r.error)) stop = true;
            }
          }).catch(function (er) { r.error = (er && er.message) || 'Koneksi gagal.'; }).then(function () { ci++; return nextChunk(); });
        };
        return nextChunk();
      }).catch(function (er) { r.error = (er && er.message) || 'Koneksi gagal.'; });
    };
    var next = function () {
      if (stop || ui >= urls.length) return finish();
      return one(urls[ui]).then(function () { ui++; return next(); });
    };
    var finish = function () {
      var rows = results.map(function (r) {
        var st = r.error ? '<span style="color:var(--warn)">' + esc(r.error) + '</span>'
          : (r.entries ? '<b>' + r.entries + ' entri</b>' : '<span class="help">0 entri</span>');
        return '<li style="margin:4px 0;word-break:break-all">' + (r.title ? esc(r.title) + ' — ' : '') + '<span class="help">' + esc(r.url) + '</span> · ' + st +
          (r.note ? '<br><span class="help" style="color:var(--warn)">' + esc(r.note) + '</span>' : '') + '</li>';
      }).join('');
      var more = Object.keys(found).filter(function (k) { return !done[k]; }).slice(0, 60).map(function (k) { return found[k]; });
      var moreHtml = more.length ? '<details style="margin-top:12px"' + (added ? '' : ' open') + '><summary><b>Halaman lain di situs ini (' + more.length + ')</b> — centang untuk ikut diimpor</summary>' +
        '<div style="max-height:260px;overflow:auto;margin:8px 0;border:1px solid var(--line, #e5e7eb);border-radius:8px;padding:6px 10px">' +
        more.map(function (l, i) {
          return '<label style="display:flex;gap:8px;align-items:flex-start;margin:4px 0;font-size:13px;cursor:pointer"><input type="checkbox" class="kb-url-more" value="' + esc(l.url) + '" style="margin-top:3px">' +
            '<span style="word-break:break-all">' + (l.text ? esc(l.text) + ' <span class="help">' + esc(l.url) + '</span>' : esc(l.url)) + '</span></label>';
        }).join('') + '</div><button class="btn sm" id="btnUrlMore">Impor halaman terpilih</button></details>' : '';
      show('<p><b>' + added + ' entri</b> ditambahkan dari ' + results.length + ' halaman' + (stop ? ' (dihentikan)' : '') + '.</p>' +
        '<ul style="margin:6px 0 0;padding-left:18px">' + rows + '</ul>' +
        '<p class="help" style="margin-top:8px">Entri belum tersimpan. Periksa isinya di daftar, jalankan <b>Analisa Duplikat</b> bila perlu, lalu klik <b>Simpan Perubahan</b>.</p>' +
        moreHtml +
        '<div style="display:flex;gap:8px;margin-top:10px"><button class="btn ghost sm" id="btnUrlAgain">Impor URL lain</button><button class="btn ghost sm" id="btnUrlClose">Tutup</button></div>');
      document.getElementById('btnUrlClose').onclick = function () { box.style.display = 'none'; };
      document.getElementById('btnUrlAgain').onclick = function () { openKbUrl(''); };
      var bm = document.getElementById('btnUrlMore');
      if (bm) bm.onclick = function () {
        var sel = $$('#pdfResult .kb-url-more').filter(function (c) { return c.checked; }).map(function (c) { return c.value; });
        if (!sel.length) { toast('Centang minimal satu halaman.', true); return; }
        if (sel.length > KB_URL_MAX) { toast('Maksimal ' + KB_URL_MAX + ' halaman sekali impor.', true); return; }
        importKbUrls(sel);
      };
      if (added) toast(added + ' entri dari website ditambahkan — klik "Simpan Perubahan" untuk menyimpan.');
    };
    return next();
  }
  function saveKb() {'''

def f_js(s, rel):
    s = rep(s, "  function saveKb() {", JS_FN, rel)
    s = rep(s, "    $('#kbPdfFile').onchange = function (e) { importKbPdf(e.target.files && e.target.files[0]); e.target.value = ''; };\n",
               "    $('#kbPdfFile').onchange = function (e) { importKbPdf(e.target.files && e.target.files[0]); e.target.value = ''; };\n"
               "    var _bku = $('#btnImportUrl'); if (_bku) _bku.onclick = function () { openKbUrl(''); };   // " + TAG + "\n", rel)
    return s

def f_html(s, rel):
    s = rep(s, '<script src="app.js?v=1.2.131"></script><!-- v1.2.131: selesai-spv -->',
               '<script src="app.js?v=1.2.132"></script><!-- ' + TAG + ' -->', rel)
    s = rep(s, '          <input type="file" id="kbPdfFile" accept=".pdf,application/pdf" style="display:none">\n',
               '          <input type="file" id="kbPdfFile" accept=".pdf,application/pdf" style="display:none">\n'
               '          <button class="btn ghost" id="btnImportUrl"><span data-ico="globe" data-ico-size="15"></span> Impor URL</button><!-- ' + TAG + ' -->\n', rel)
    return s

patch('api/index.php', f_api)
patch('dashboard/chatbot-ai/app.js', f_js)
patch('dashboard/chatbot-ai/index.html', f_html)
