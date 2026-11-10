#!/usr/bin/env python3
"""v1.2.163 thread-lengkap — Percakapan WA hanya menampilkan 60 entri terakhir per nomor; sisanya tidak bisa dibuka
 (kasus deintegra 10 Nov 2026: 6285168698884, 92 entri hari ini, 32 entri 08:00–10:54 tidak tampil).
 1. api wa_thread: parameter ?limit= (60..5000, bawaan 60) + 'total' (jumlah entri nomor ini di log).
 2. app.js: tombol "Muat pesan sebelumnya (N lagi)" di atas thread; tiap klik +100 entri, posisi baca dipertahankan;
    polling memakai batas yang sama sehingga pesan lama tidak hilang lagi.
 Idempoten. Pakai: patch_v12163.py <dei-tenant>"""
import sys, shutil, time
T = sys.argv[1]; TAG = 'v1.2.163: thread-lengkap'
A = T + '/api/index.php'; J = T + '/dashboard/chatbot-ai/app.js'; Hh = T + '/dashboard/chatbot-ai/index.html'
api = open(A, encoding='utf-8').read()
if TAG in api:
    print('sudah dipatch'); sys.exit(0)
st = time.strftime('%Y%m%d-%H%M%S')
for f in (A, J, Hh): shutil.copy2(f, f + '.bak-v12163-' + st)
def rep(s, old, new, cnt=1):
    n = s.count(old); assert n == cnt, f'anchor {n}x (harus {cnt}): {old[:90]!r}'
    return s.replace(old, new)

api = rep(api, "define('DEI_VERSION', 'v1.2.161');   // v1.2.161: kutip-wa-cocok — kutipan balasan pelanggan tidak lagi 'Pesan sebelumnya (pesan)'",
               "define('DEI_VERSION', 'v1.2.163');   // " + TAG + " — thread WA bisa memuat pesan sebelumnya (dulu terpotong 60 entri)")
api = rep(api, """        $msgs = array_slice($msgs, 0, 60);
        // v1.2.161: kutipan""",
"""        // """ + TAG + """: dulu terpotong tetap 60 entri tanpa jalan ke pesan lama
        $tot163 = count($msgs);
        $lim163 = max(60, min(5000, (int)($_GET['limit'] ?? 60)));
        $msgs = array_slice($msgs, 0, $lim163);
        // v1.2.161: kutipan""")
api = rep(api, """            'messages' => $msgs,
            'channels' => (function () { $s0 = getSettings();""",
"""            'messages' => $msgs,
            'total' => $tot163,   // """ + TAG + """
            'channels' => (function () { $s0 = getSettings();""")

js = open(J, encoding='utf-8').read()
js = rep(js, """    api('wa_thread', { query: '&number=' + encodeURIComponent(num) + ((waState.wiAll && waState.wiAll[num]) ? '&imp_all=1' : '') /* v1.2.105 */ }).then(function (res) {""",
"""    var lim163 = (waState.thLim || {})[num] || 60;   // """ + TAG + """
    api('wa_thread', { query: '&number=' + encodeURIComponent(num) + '&limit=' + lim163 + ((waState.wiAll && waState.wiAll[num]) ? '&imp_all=1' : '') /* v1.2.105 */ }).then(function (res) {""")
js = rep(js, """    var _waHtml = _wiH + (res.messages || []).map(function (m) {   // v1.2.123: dirakit dulu, dipasang hanya bila berubah""",
"""    // """ + TAG + """: tombol muat pesan sebelumnya (server mengirim N entri terbaru + total)
    var _more163 = Math.max(0, (+res.total || 0) - (res.messages || []).length);
    var _moreH163 = _more163 > 0 ? '<div style="text-align:center;margin:6px 0 10px"><button type="button" class="btn ghost" id="waMoreBtn" style="padding:6px 14px;font-size:12px;display:inline-flex;align-items:center;gap:4px">' +
      ico('chevron-down', 13, 'style="transform:rotate(180deg)"') + ' Muat pesan sebelumnya (' + _more163 + ' lagi)</button></div>' : '';
    var _waHtml = _wiH + _moreH163 + (res.messages || []).map(function (m) {   // v1.2.123: dirakit dulu, dipasang hanya bila berubah""")
js = rep(js, """    wiThreadBind(res);   // v1.2.105
    $('#waReplyBar').style.display = 'block';""",
"""    wiThreadBind(res);   // v1.2.105
    if ($('#waMoreBtn')) $('#waMoreBtn').onclick = function () {   // """ + TAG + """
      this.disabled = true; this.textContent = 'Memuat…';
      waState.thLim = waState.thLim || {}; waState.thLim[num] = ((waState.thLim[num] || 60) + 100);
      waState.waStick = false; fetchWaThread(num);
    };
    $('#waReplyBar').style.display = 'block';""")

html = open(Hh, encoding='utf-8').read()
html = rep(html, '<script src="app.js?v=1.2.160"></script><!-- v1.2.160: hapus-jadwal -->',
                 '<script src="app.js?v=1.2.163"></script><!-- ' + TAG + ' --><!-- v1.2.160: hapus-jadwal -->')
open(A, 'w', encoding='utf-8').write(api); open(J, 'w', encoding='utf-8').write(js); open(Hh, 'w', encoding='utf-8').write(html)
print('OK', TAG)
