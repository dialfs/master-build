# v1.2.148: selesai-tanpa-flag — tombol Selesai tetap muncul walau data daftar tanpa flag,
# status chat langsung berubah setelah Selesai, dan peringatan saat daftar jatuh ke endpoint lama.
import sys, os, shutil, time
T = os.path.expanduser(sys.argv[1])
J = os.path.join(T, 'dashboard/chatbot-ai/app.js'); H = os.path.join(T, 'dashboard/chatbot-ai/index.html'); A = os.path.join(T, 'api/index.php')
ts = time.strftime('%Y%m%d-%H%M%S')
for f in (H, J, A): shutil.copy2(f, f + '.bak-v12148-' + ts)
def rep(path, old, new):
    s = open(path, encoding='utf-8').read()
    if new in s: print('skip'); return
    assert s.count(old) == 1, (path, old[:70]); open(path, 'w', encoding='utf-8').write(s.replace(old, new))

# 1) Tombol Selesai: pakai data chat terpilih (termasuk cache); flag kosong = belum selesai
rep(J, """    var _li129 = (waState.convs || []).filter(function (c) { return String(c.number) === String(num); })[0];   // v1.2.129: wa-selesai-lama; v1.2.130: selesai-fix — chat lama tanpa percakapan aktif
    var _openConv = res.conv && ['open', 'handover', 'assigned'].indexOf(res.conv.status) > -1;
    if ((_openConv || (_li129 && _li129.flag && _li129.flag !== 'done')) && waState.isAdmin) {""",
"""    var _li129 = waConvOf140(num);   // v1.2.129: wa-selesai-lama; v1.2.130: selesai-fix; v1.2.148: selesai-tanpa-flag — termasuk chat terpilih di luar filter
    var _openConv = res.conv && ['open', 'handover', 'assigned'].indexOf(res.conv.status) > -1;
    if ((_openConv || (_li129 && _li129.flag !== 'done')) && waState.isAdmin) {   // v1.2.148: flag kosong (data lama) = belum selesai""")

# 2) Setelah Selesai: status di layar langsung diperbarui (chat terpilih tidak lagi tampil "perlu perhatian")
rep(J, """    var li = (waState.convs || []).filter(function (c) { return String(c.number) === String(num); })[0] || {};   // v1.2.131: log-selesai
    api('wa_resolve', { method: 'POST', body: { number: num, prev_flag: li.flag || '', waiting_sec: li.waiting_sec || 0, last_msg: li.last_q || '' } }).then(function (res) {
      if (res && res.ok) { toast('Percakapan ditandai selesai.'); fetchWaThread(num);""",
"""    var li = waConvOf140(num) || {};   // v1.2.131: log-selesai; v1.2.148: selesai-tanpa-flag
    api('wa_resolve', { method: 'POST', body: { number: num, prev_flag: li.flag || '', waiting_sec: li.waiting_sec || 0, last_msg: li.last_q || '' } }).then(function (res) {
      if (res && res.ok) {
        (waState.res148 = waState.res148 || {})[String(num)] = li.last_ts || true;   // v1.2.148: diingat untuk mode cadangan
        if (li.number !== undefined) {   // v1.2.148: selesai-tanpa-flag — jangan tunggu polling
          li.flag = 'done'; li.flag_note = 'Ditandai selesai' + (waState.me ? ' oleh ' + waState.me : '');
          li.needs_attention = false; li.awaiting = false; li.waiting_sec = 0; li.claim = null;
          if (li.status === 'claimed' || li.status === 'human_unclaimed' || li.status === 'takeover_requested') { li.status = 'bot'; li.mode = 'bot'; }
        }
        toast('Percakapan ditandai selesai.'); fetchWaThread(num);""")

# 3) Peringatan saat daftar chat jatuh ke endpoint lama (tanpa status Selesai/Belum dibalas)
rep(J, """      if (!res || !res.ok) {
        // Fallback to old endpoint jika v2 error (backward compat)
        fetchWaConvsLegacy(silent);""",
"""      if (!res || !res.ok) {
        // Fallback to old endpoint jika v2 error (backward compat)
        if (window.console) console.warn('[v1.2.148] wa_conversations_v2 gagal, pakai daftar lama:', res);
        if (!waState.legacyWarn148 && !(res && /autentikasi/i.test(res.error || ''))) {   // v1.2.148: selesai-tanpa-flag
          waState.legacyWarn148 = true;
          toast('Daftar chat dimuat dengan mode cadangan (' + ((res && res.error) || 'server tidak merespons') + '). Status Selesai/Belum dibalas tidak tampil — muat ulang halaman.', true);
        }
        fetchWaConvsLegacy(silent);""")
rep(J, """      waState.convs = res.conversations || [];
      waState.convCache = waState.convCache || {};   // v1.2.141""",
"""      waState.legacyWarn148 = false; waState.res148 = {};   // v1.2.148: selesai-tanpa-flag
      waState.convs = res.conversations || [];
      waState.convCache = waState.convCache || {};   // v1.2.141""")

# 4) Mode cadangan: hak Supervisor/Admin diambil dari data login (server tetap memeriksa)
rep(J, """      waState.convs = res.conversations || [];
      renderWaConvs();
      var awaiting = waState.convs.filter(function (c) { return c.awaiting; }).length;""",
"""      waState.convs = res.conversations || [];
      if (!waState.isAdmin && user && ['super_admin', 'admin', 'supervisor'].indexOf(user.role) > -1) waState.isAdmin = true;   // v1.2.148: selesai-tanpa-flag
      waState.convs.forEach(function (c) {   // v1.2.148: chat yang baru ditandai Selesai tetap tampil selesai sampai ada pesan baru
        var r = (waState.res148 || {})[String(c.number)];
        if (r && (r === true || String(c.last_ts || '') <= String(r))) { c.flag = 'done'; c.flag_note = 'Ditandai selesai'; c.needs_attention = false; c.awaiting = false; }
      });
      renderWaConvs();
      var awaiting = waState.convs.filter(function (c) { return c.awaiting; }).length;""")

rep(H, '<script src="app.js?v=1.2.147"></script><!-- v1.2.147: leads-kanban -->',
       '<script src="app.js?v=1.2.148"></script><!-- v1.2.148: selesai-tanpa-flag -->')
rep(A, "define('DEI_VERSION', 'v1.2.147');   // v1.2.147: leads-kanban",
       "define('DEI_VERSION', 'v1.2.148');   // v1.2.148: selesai-tanpa-flag")
print('OK')
