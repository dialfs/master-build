#!/usr/bin/env python3
"""v1.2.178 foto-otomatis (TENANT, di atas v1.2.177): opsi per entri KB "Kirim otomatis tanpa diminta".
- Entri KB berfoto + centang foto_auto -> bot WA menyertakan fotonya setiap kali menjawab memakai info entri itu,
  walau pelanggan tidak minta foto. Sekali per percakapan (8 pesan terakhir); diminta lagi -> dikirim lagi.
- Tanpa centang: perilaku lama (hanya bila diminta).
Idempoten: backup -> replace anchor."""
import os, sys, time, shutil
T = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
API = T + '/api/index.php'; JS = T + '/dashboard/chatbot-ai/app.js'
TAG = 'v1.2.178: foto-otomatis'; stamp = time.strftime('%Y%m%d-%H%M%S')
NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def rep(s, old, new, label, n=1):
    c = s.count(old); assert c == n, '%s: anchor %d kali (harus %d)' % (label, c, n); return s.replace(old, new)
def patch(p, fn, need):
    s = rd(p)
    if TAG in s: print('sudah:', p); return
    assert need in s, 'butuh berkas v1.2.177/v1.2.95: ' + p
    if not NOBAK: shutil.copy2(p, p + '.bak-v12178-' + stamp)
    wr(p, fn(s)); print('OK', p)
C = '   // ' + TAG

def api(s):
    s = rep(s, "define('DEI_VERSION', 'v1.2.177');   // v1.2.177:",
               "define('DEI_VERSION', 'v1.2.178');   // " + TAG + " — foto KB bisa dikirim otomatis tanpa diminta; v1.2.177:", 'versi')
    # prompt: tandai entri otomatis
    s = rep(s, "    $deiFotoOn = deiKbFotoAktif($s, $channel); $deiAdaFoto = false;   // v1.2.95: kb-foto\n",
               "    $deiFotoOn = deiKbFotoAktif($s, $channel); $deiAdaFoto = false; $deiAdaAuto = false;   // v1.2.95: kb-foto; " + TAG + "\n", 'flag')
    s = rep(s, "        if ($deiFoto) $deiAdaFoto = true;\n"
               "        $kbText .= '[' . $cat . '] ' . $tit . \"\\n\" . $con . ($deiFoto ? \"\\n(\" . count($deiFoto) . ' foto tersedia — kode [[FOTO:' . $e['id'] . ']])' : '') . \"\\n\\n\";\n",
               "        if ($deiFoto) $deiAdaFoto = true;\n"
               "        $deiAuto = $deiFoto && !empty($e['foto_auto']); if ($deiAuto) $deiAdaAuto = true;" + C + "\n"
               "        $kbText .= '[' . $cat . '] ' . $tit . \"\\n\" . $con . ($deiFoto ? \"\\n(\" . count($deiFoto) . ' foto tersedia — kode [[FOTO:' . $e['id'] . ']]' . ($deiAuto ? ' — KIRIM OTOMATIS' : '') . ')' : '') . \"\\n\\n\";\n", 'kbText')
    s = rep(s, "    if ($deiAdaFoto) $deiPriceBlk = trim($deiPriceBlk . \"\\n\\n\" . deiKbFotoPrompt());   // v1.2.95: kb-foto\n",
               "    if ($deiAdaFoto) $deiPriceBlk = trim($deiPriceBlk . \"\\n\\n\" . deiKbFotoPrompt($deiAdaAuto));   // v1.2.95: kb-foto; " + TAG + "\n", 'pakai prompt')
    s = rep(s, "function deiKbFotoPrompt() {\n",
               "function deiKbFotoPrompt($auto = false) {" + C + "\n", 'sig')
    s = rep(s, "        . \"Jika foto yang diminta tidak ada di Knowledge Base, katakan fotonya belum tersedia.\";\n}\n",
               "        . \"Jika foto yang diminta tidak ada di Knowledge Base, katakan fotonya belum tersedia.\"\n"
               "        . ($auto ? \"\\nPENGECUALIAN — entri bertanda 'KIRIM OTOMATIS': setiap kali jawabanmu memakai informasi dari entri itu, \"\n"
               "            . \"tulis kodenya di baris terakhir walau pelanggan TIDAK meminta foto (tetap maksimal 2 kode). \"\n"
               "            . \"Cukup sekali per percakapan: jangan tulis lagi bila kode yang sama sudah ada di balasanmu sebelumnya, kecuali pelanggan meminta fotonya lagi.\" : '');" + C + "\n}\n", 'prompt auto')
    # penjaga server: foto otomatis yang sudah terkirim di riwayat tidak diulang kecuali diminta
    s = rep(s, "    if ($ok) list($answer, $deiFotoIds) = deiKbFotoExtract($answer);\n",
               "    if ($ok) list($answer, $deiFotoIds) = deiKbFotoExtract($answer);\n"
               "    if ($deiFotoIds) $deiFotoIds = deiKbFotoAutoDedupe($deiFotoIds, $history, $text);" + C + "\n", 'dedupe call')
    s = rep(s, "/* Buang kode foto dari jawaban AI. Hasil: [teks bersih, daftar id entri]. */\n",
               "/* " + TAG + ": entri foto_auto yang kodenya sudah ada di riwayat (8 pesan terakhir) tidak dikirim ulang,\n"
               " * kecuali pesan pelanggan memang meminta foto. Entri biasa tidak disentuh. */\n"
               "function deiKbFotoAutoDedupe($ids, $history, $text) {\n"
               "    if (preg_match('/foto|gambar|photo|pic|lihat|liat|kirim|tunjuk|katalog|menu|qr/i', (string)$text)) return $ids;\n"
               "    $auto = [];\n"
               "    foreach ((array)readJson(KB_FILE, []) as $e) { if (!empty($e['id']) && !empty($e['foto_auto'])) $auto[(string)$e['id']] = true; }\n"
               "    if (!$auto) return $ids;\n"
               "    $past = '';\n"
               "    foreach (array_slice((array)$history, -8) as $h) { if (($h['role'] ?? '') === 'assistant') $past .= (string)($h['content'] ?? ''); }\n"
               "    return array_values(array_filter($ids, function ($id) use ($auto, $past) {\n"
               "        return !isset($auto[$id]) || stripos($past, '[[FOTO:' . $id . ']]') === false;\n"
               "    }));\n"
               "}\n"
               "/* Buang kode foto dari jawaban AI. Hasil: [teks bersih, daftar id entri]. */\n", 'dedupe fn')
    # simpan field
    s = rep(s, "                'images'   => deiKbFotoClean($e['images'] ?? []),   // v1.2.95: kb-foto\n",
               "                'images'   => deiKbFotoClean($e['images'] ?? []),   // v1.2.95: kb-foto\n"
               "                'foto_auto' => !empty($e['foto_auto']),"+ C + "\n", 'save_kb')
    s = rep(s, "                'images'   => deiKbFotoClean(array_merge(...array_map(function ($a) { return (array)($a['images'] ?? []); }, $anggota))),   // v1.2.95: kb-foto\n",
               "                'images'   => deiKbFotoClean(array_merge(...array_map(function ($a) { return (array)($a['images'] ?? []); }, $anggota))),   // v1.2.95: kb-foto\n"
               "                'foto_auto' => (bool)array_filter($anggota, function ($a) { return !empty($a['foto_auto']); }),"+ C + "\n", 'merge')
    return s

def js(s):
    s = rep(s, "'</div><div class=\"help\">Dikirim bot WhatsApp bila pelanggan minta, mis. <i>\"bisa kirim foto kamarnya?\"</i>, <i>\"ada foto menunya?\"</i>, <i>\"kirim QR pembayarannya\"</i>. Maks 6 foto per entri. Tulis judul & isi yang jelas supaya bot tahu foto ini tentang apa, lalu klik <b>Simpan</b>.</div>';",
               "'</div>' + (imgs.length ? '<label style=\"display:flex;align-items:center;gap:6px;margin:4px 0 6px;font-size:13px;cursor:pointer\"><input type=\"checkbox\" class=\"kb-foto-auto\"' + (e.foto_auto ? ' checked' : '') + '> Kirim otomatis tanpa diminta</label>' : '') +" + C + "\n"
               "      '<div class=\"help\">' + (e.foto_auto ? 'Dikirim bot WhatsApp <b>otomatis</b> setiap kali bot menjawab memakai info entri ini (sekali per percakapan), walau pelanggan tidak minta foto.' : 'Dikirim bot WhatsApp bila pelanggan minta, mis. <i>\"bisa kirim foto kamarnya?\"</i>, <i>\"ada foto menunya?\"</i>, <i>\"kirim QR pembayarannya\"</i>. Centang <b>Kirim otomatis</b> agar foto langsung ikut terkirim tanpa diminta.') + ' Maks 6 foto per entri. Tulis judul & isi yang jelas supaya bot tahu foto ini tentang apa, lalu klik <b>Simpan</b>.</div>';", 'help')
    s = rep(s, "    edEl.querySelectorAll('.kb-img-del').forEach(function (b) {   // v1.2.95: kb-foto\n",
               "    var kbFa = edEl.querySelector('.kb-foto-auto');" + C + "\n"
               "    if (kbFa) kbFa.onchange = function () { kbData[si].foto_auto = kbFa.checked; kbMarkDirty(); renderKb(); };\n"
               "    edEl.querySelectorAll('.kb-img-del').forEach(function (b) {   // v1.2.95: kb-foto\n", 'handler')
    return s

patch(API, api, 'v1.2.177: headline-iklan')
patch(JS, js, 'v1.2.95: kb-foto')
