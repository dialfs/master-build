#!/usr/bin/env python3
"""v1.2.184 (lupa-password): reset password lewat email dari halaman login.
Tenant:
- api/index.php: forgot_password / reset_password_check / reset_password (publik), update_own_email,
  email pemulihan di save_user/get_users/me, token sesi lama gugur setelah password diganti (pw_changed_at).
- login.html: link "Lupa password?", form minta tautan, form password baru (#reset=<token>).
- index.html + app.js: kolom Email di form Pengguna, kartu Email Pemulihan di Profil Saya.
Pusat:
- backend/index.php: action mail_relay (noreply@deintegra.com, pw_reset/pw_changed, batas 20/jam tenant, 5/jam alamat).
Idempoten.  Pakai: patch_v12184.py [~/Herd] [--no-backup]"""
import os, sys, time, shutil
D = os.path.dirname(os.path.abspath(__file__))
H = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '~/Herd')
T = H + '/dei-tenant'; P = H + '/dei-pusat'
TAG = 'v1.2.184: lupa-password'; NEED = 'v1.2.183: foto-otomatis-cocok'
stamp = time.strftime('%Y%m%d-%H%M%S'); NOBAK = '--no-backup' in sys.argv
rd = lambda p: open(p, encoding='utf-8').read()
def rep(s, old, new, n=1, what=''):
    c = s.count(old)
    assert c == n, 'anchor %s: ditemukan %d, harus %d' % (what or old[:60], c, n)
    return s.replace(old, new)
def save(p, s):
    if not NOBAK: shutil.copy2(p, p + '.bak-v12184-' + stamp)
    open(p, 'w', encoding='utf-8').write(s); print('OK', p)

# ---------- tenant api ----------
API = T + '/api/index.php'; s = rd(API)
if TAG in s: print('sudah:', API)
else:
    assert NEED in s, 'butuh v1.2.183'
    s = rep(s, "function checkPasswordStrength($pw) {\n", rd(D + '/pr_funcs.php') + "function checkPasswordStrength($pw) {\n", what='checkPasswordStrength')
    s = rep(s, "            if ($changed) writeJson(USERS_FILE, $users);\n            $u['role'] = $role;\n",
               "            if ($changed) writeJson(USERS_FILE, $users);\n"
               "            if (deiTokenBeforePwChange($u)) jsonOut(['ok' => false, 'error' => 'Password akun ini sudah diganti. Silakan login kembali.'], 401);   // v1.2.184: lupa-password\n"
               "            $u['role'] = $role;\n", what='requireAuth')
    s = rep(s, "    case 'login': {\n", rd(D + '/pr_cases.php') + "    case 'login': {\n", what='case login')
    s = rep(s, "    case 'update_own_password': {\n", rd(D + '/pr_own_email.php') + "    case 'update_own_password': {\n", what='case update_own_password')
    s = rep(s, "                $users[$i]['password'] = password_hash($newPw, PASSWORD_DEFAULT);\n                $found = true;\n",
               "                $users[$i]['password'] = password_hash($newPw, PASSWORD_DEFAULT);\n"
               "                $users[$i]['pw_changed_at'] = time();   // v1.2.184: lupa-password — sesi lama gugur\n                $found = true;\n", what='own pw')
    s = rep(s, "            'tour_seen' => (int)($u['tour_seen'] ?? 0),   // v1.2.74\n        ]]);\n",
               "            'tour_seen' => (int)($u['tour_seen'] ?? 0),   // v1.2.74\n"
               "            'email' => (string)($u['email'] ?? ''), 'reset_email' => deiUserEmail($u),   // v1.2.184: lupa-password\n        ]]);\n", what='me')
    s = rep(s, "                'name'       => $u['name'] ?? '',\n                'role'       => $u['role'] ?? 'editor',\n",
               "                'name'       => $u['name'] ?? '',\n                'email'      => (string)($u['email'] ?? ''),   // v1.2.184: lupa-password\n                'role'       => $u['role'] ?? 'editor',\n", what='get_users')
    s = rep(s, "        $password = (string)($in['password'] ?? '');\n        // v1.2.12 Fase 2",
               "        $password = (string)($in['password'] ?? '');\n"
               "        // v1.2.184: lupa-password — email pemulihan (opsional; null = tidak diubah)\n"
               "        $emailSet = null;\n"
               "        if (array_key_exists('email', $in)) {\n"
               "            $emRaw = trim((string)$in['email']); $emailSet = deiValidEmail($emRaw);\n"
               "            if ($emRaw !== '' && $emailSet === '') jsonOut(['ok' => false, 'error' => 'Format email tidak valid.'], 400);\n"
               "            if (deiEmailTaken($emailSet, $username)) jsonOut(['ok' => false, 'error' => 'Email ini sudah dipakai akun lain.'], 400);\n"
               "        }\n"
               "        // v1.2.12 Fase 2", what='save_user email')
    s = rep(s, "                if ($password !== '') $users[$i]['password'] = password_hash($password, PASSWORD_DEFAULT);\n                $found = true;\n",
               "                if ($password !== '') { $users[$i]['password'] = password_hash($password, PASSWORD_DEFAULT); $users[$i]['pw_changed_at'] = time(); }   // v1.2.184: sesi lama gugur\n"
               "                if ($emailSet !== null) { if ($emailSet === '') unset($users[$i]['email']); else $users[$i]['email'] = $emailSet; }   // v1.2.184\n"
               "                $found = true;\n", what='save_user update')
    s = rep(s, "            if ($role === 'wa_agent' && $spvSet !== null && $spvSet !== '') $users[count($users) - 1]['supervisor'] = $spvSet;   // v1.2.59\n",
               "            if ($role === 'wa_agent' && $spvSet !== null && $spvSet !== '') $users[count($users) - 1]['supervisor'] = $spvSet;   // v1.2.59\n"
               "            if ($emailSet) $users[count($users) - 1]['email'] = $emailSet;   // v1.2.184: lupa-password\n", what='save_user new')
    i = s.index("define('DEI_VERSION', 'v1.2.183');   //")
    s = s[:i] + "define('DEI_VERSION', 'v1.2.184');   // " + TAG + " — reset password lewat email; v1.2.183:" + s[i + len("define('DEI_VERSION', 'v1.2.183');   //"):]
    save(API, s)

# ---------- login.html ----------
LG = T + '/dashboard/chatbot-ai/login.html'; s = rd(LG)
if TAG in s: print('sudah:', LG)
else:
    s = rep(s, '  .pw-eye svg{width:20px;height:20px}\n', '  .pw-eye svg{width:20px;height:20px}\n'
        '  /* v1.2.184: lupa-password */\n'
        '  .lnk{color:var(--brand);text-decoration:none;font-weight:500;font-size:13px}\n'
        '  .lnk:hover{text-decoration:underline}\n'
        '  .okm{background:#ecfdf3;color:#166534;font-size:13px;line-height:1.5;padding:10px 12px;border-radius:8px;margin-bottom:16px;display:none}\n'
        '  .fp-h{font-size:17px;font-weight:700;margin-bottom:6px}\n'
        '  .fp-p{color:var(--muted);font-size:13px;line-height:1.55;margin-bottom:16px}\n'
        '  .fp-chk{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--muted);margin:-4px 0 12px;font-weight:400}\n'
        '  .fp-chk input{width:auto}\n')
    s = rep(s, '  <form class="card" id="form">\n', '  <div class="card" id="cardBox">\n')
    s = rep(s, '    <div class="err" id="err"></div>\n', '    <div class="err" id="err"></div>\n    <div class="okm" id="okMsg"></div>\n    <form id="form">\n')
    s = rep(s, '    <button type="submit" id="btn">Masuk</button>\n  </form>\n', rd(D + '/pr_login.html'))
    s = rep(s, '  if (!ssoM) (function () {\n', "  if (!ssoM && !/[#&]reset=/.test(location.hash || '')) (function () {   // v1.2.184: tautan reset tidak dialihkan ke dashboard\n")
    s = rep(s, "  });\n})();\n</script>", "  });\n\n" + rd(D + '/pr_login.js') + "})();\n</script>")
    save(LG, s)

# ---------- index.html ----------
IX = T + '/dashboard/chatbot-ai/index.html'; s = rd(IX)
if TAG in s: print('sudah:', IX)
else:
    a = '          <div class="row"><label class="fl">Nama</label><input type="text" id="u_name" name="dei_new_name" autocomplete="off"></div>\n'
    s = rep(s, a, a + '          <div class="row"><label class="fl">Email</label><input type="text" inputmode="email" id="u_email" name="dei_new_email" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="untuk Lupa password (opsional)"></div>   <!-- ' + TAG + ' -->\n')
    a = '          <tr><td style="padding:6px 0;color:var(--muted)">Role</td><td id="profileRole" style="font-weight:600">-</td></tr>\n        </table>\n      </div>\n'
    s = rep(s, a, '          <tr><td style="padding:6px 0;color:var(--muted)">Role</td><td id="profileRole" style="font-weight:600">-</td></tr>\n'
        '          <tr><td style="padding:6px 0;color:var(--muted)">Email pemulihan</td><td id="profileEmailView" style="font-weight:600">-</td></tr>\n'
        '        </table>\n      </div>\n'
        '      <!-- ' + TAG + ' -->\n'
        '      <div class="card" id="peCard" style="margin-bottom:16px">\n'
        '        <h3 style="margin:0 0 6px 0;font-size:15px">Email Pemulihan</h3>\n'
        '        <p class="hint" style="font-size:12px;color:var(--muted);margin:0 0 10px">Dipakai untuk &ldquo;Lupa password?&rdquo; di halaman login. <span id="peNote"></span></p>\n'
        '        <div style="margin-bottom:10px"><label style="display:block;font-size:13px;color:var(--muted);margin-bottom:4px">Email</label><input type="text" inputmode="email" id="profileEmail" class="input" autocomplete="email" autocapitalize="none" spellcheck="false" placeholder="nama@domain.com (kosongkan untuk menghapus)"></div>\n'
        '        <div style="margin-bottom:10px"><label style="display:block;font-size:13px;color:var(--muted);margin-bottom:4px">Password Anda (konfirmasi)</label><input type="password" id="profileEmailPw" class="input" autocomplete="current-password" placeholder="Masukkan password saat ini"></div>\n'
        '        <button class="btn" id="btnSaveEmail" type="button">Simpan Email</button>\n'
        '      </div>\n')
    save(IX, s)

# ---------- app.js ----------
AJ = T + '/dashboard/chatbot-ai/app.js'; s = rd(AJ)
if TAG in s: print('sudah:', AJ)
else:
    s = rep(s, "    if (!body.username) { toast('Username wajib diisi.', true); return; }\n",
               "    if (!body.username) { toast('Username wajib diisi.', true); return; }\n"
               "    if ($('#u_email')) {   // v1.2.184: lupa-password\n"
               "      body.email = $('#u_email').value.trim();\n"
               "      if (body.email && !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(body.email)) { toast('Format email tidak valid.', true); $('#u_email').focus(); return; }\n"
               "    }\n")
    s = rep(s, "data-n=\"' + esc(u.name) + '\"", "data-n=\"' + esc(u.name) + '\" data-e=\"' + esc(u.email || '') + '\"")
    s = rep(s, "$('#u_name').value = b.dataset.n; ", "$('#u_name').value = b.dataset.n; if ($('#u_email')) $('#u_email').value = b.dataset.e || '';   /* v1.2.184 */ ")
    s = rep(s, "    $('#u_name').value = ''; $('#u_password').value = '';\n", "    $('#u_name').value = ''; $('#u_password').value = '';\n    if ($('#u_email')) $('#u_email').value = '';   // v1.2.184: lupa-password\n")
    s = rep(s, "'<td class=\"mono\">' + esc(u.username) + '</td>' +",
               "'<td class=\"mono\">' + esc(u.username) + (u.email && u.email !== u.username ? '<div style=\"font-size:11px;color:var(--muted);font-family:inherit\" title=\"Email pemulihan\">' + esc(u.email) + '</div>' : '') + '</td>' +   // v1.2.184")
    s = rep(s, "    loadMyLoginLog();   // v1.2.112\n  }\n",
               "    loadMyLoginLog();   // v1.2.112\n    loadProfileEmail();   // " + TAG + "\n  }\n"
               "  // " + TAG + " — email pemulihan di Profil Saya\n"
               "  function peNote(em) {\n"
               "    if ($('#profileEmailView')) $('#profileEmailView').textContent = em || '— (belum diisi)';\n"
               "    var n = $('#peNote'); if (!n) return;\n"
               "    n.textContent = em ? ('Tautan reset dikirim ke ' + em + '.') : 'Belum ada email — fitur Lupa password belum bisa dipakai untuk akun ini.';\n"
               "    n.style.color = em ? '' : '#b45309';\n"
               "  }\n"
               "  function loadProfileEmail() {\n"
               "    var b = $('#btnSaveEmail'); if (!b) return;\n"
               "    if (!b.dataset.wired) { b.dataset.wired = '1'; b.onclick = saveOwnEmail; }\n"
               "    $('#profileEmailPw').value = '';\n"
               "    api('me').then(function (res) {\n"
               "      if (!res || !res.ok) return;\n"
               "      var u = res.user || {};\n"
               "      $('#profileEmail').value = u.email || '';\n"
               "      peNote(u.reset_email || '');\n"
               "    }).catch(function () {});\n"
               "  }\n"
               "  function saveOwnEmail() {\n"
               "    var em = $('#profileEmail').value.trim(), pw = $('#profileEmailPw').value;\n"
               "    if (em && !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(em)) { toast('Format email tidak valid.', true); $('#profileEmail').focus(); return; }\n"
               "    if (!pw) { toast('Masukkan password Anda untuk konfirmasi.', true); $('#profileEmailPw').focus(); return; }\n"
               "    var b = $('#btnSaveEmail'); b.disabled = true;\n"
               "    api('update_own_email', { method: 'POST', body: { email: em, current_password: pw } }).then(function (res) {\n"
               "      b.disabled = false;\n"
               "      if (!res || !res.ok) { toast((res && res.error) || 'Gagal menyimpan email.', true); return; }\n"
               "      $('#profileEmailPw').value = '';\n"
               "      toast(em ? 'Email pemulihan disimpan.' : 'Email pemulihan dihapus.');\n"
               "      peNote(res.reset_email || '');\n"
               "    }).catch(function () { b.disabled = false; });\n"
               "  }\n")
    save(AJ, s)

# ---------- pusat ----------
PB = P + '/backend/index.php'; s = rd(PB)
if TAG in s or "case 'mail_relay':" in s: print('sudah:', PB)
else:
    s = rep(s, "    case 'report_back': {\n", rd(D + '/pusat_relay.php').replace('v1.2.184: lupa-password', TAG) + "    case 'report_back': {\n")
    save(PB, s)
