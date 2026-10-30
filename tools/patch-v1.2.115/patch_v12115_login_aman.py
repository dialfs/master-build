#!/usr/bin/env python3
"""v1.2.115 login-aman: tombol lihat password + batas 3x gagal -> kunci 15 menit (sisa percobaan & hitung mundur).
Pakai: python3 patch_v12115_login_aman.py [~/Herd/dei-tenant]  (idempoten)"""
import os, sys, time, shutil
ROOT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Herd/dei-tenant')
TAG = 'v1.2.115: login-aman'
STAMP = time.strftime('%Y%m%d-%H%M%S')
def patch(rel, edits):
    p = os.path.join(ROOT, rel); s = open(p, encoding='utf-8').read()
    if TAG in s: print('sudah dipatch:', rel); return
    shutil.copy2(p, p + '.bak-v12115-' + STAMP)
    for old, new in edits:
        n = s.count(old); assert n == 1, '%s: anchor %dx: %r' % (rel, n, old[:80]); s = s.replace(old, new)
    assert TAG in s, rel; open(p, 'w', encoding='utf-8').write(s); print('OK', rel)

patch('api/index.php', [
 ("define('DEI_VERSION', 'v1.2.114');   // v1.2.114: kontak-jumlah",
  "define('DEI_VERSION', 'v1.2.115');   // v1.2.115: login-aman"),
 ("define('LOCKOUT_MAX_TRIES', 5);",
  "define('LOCKOUT_MAX_TRIES', 3);   // v1.2.115: 3x gagal -> kunci 15 menit"),
 ("""    $m[$k] = $row;
    writeJson(LOCKOUT_FILE, $m);
}""",
  """    $m[$k] = $row;
    writeJson(LOCKOUT_FILE, $m);
    // v1.2.115: balikan sisa percobaan (0 = baru saja dikunci)
    return isset($row['locked_until']) ? 0 : max(0, LOCKOUT_MAX_TRIES - $tries);
}"""),
 ("""            jsonOut(['ok' => false, 'error' => "Terlalu banyak percobaan. Coba lagi dalam $mins menit."], 429);""",
  """            jsonOut(['ok' => false, 'error' => "Terlalu banyak percobaan. Coba lagi dalam $mins menit.", 'locked' => true, 'retry_after' => $remaining], 429);"""),
 ("""        lockoutRecordFail($username);
        deiLoginLog($username, false, 'password', $llFound ? 'wrong_password' : 'unknown_user');   // v1.2.112
        jsonOut(['ok' => false, 'error' => 'Username atau password salah.'], 401);""",
  """        $left = lockoutRecordFail($username);   // v1.2.115
        deiLoginLog($username, false, 'password', $llFound ? 'wrong_password' : 'unknown_user');   // v1.2.112
        if ($left <= 0) {
            jsonOut(['ok' => false, 'error' => 'Username atau password salah. Terlalu banyak percobaan — coba lagi dalam ' . (int)(LOCKOUT_WINDOW_SEC / 60) . ' menit.', 'locked' => true, 'retry_after' => LOCKOUT_WINDOW_SEC], 429);
        }
        jsonOut(['ok' => false, 'error' => 'Username atau password salah. Sisa ' . $left . ' percobaan sebelum dikunci ' . (int)(LOCKOUT_WINDOW_SEC / 60) . ' menit.', 'tries_left' => $left], 401);"""),
])

patch('dashboard/chatbot-ai/login.html', [
 ("""  .hint{margin-top:18px;text-align:center;font-size:12px;color:var(--muted)}
</style>""",
  """  .hint{margin-top:18px;text-align:center;font-size:12px;color:var(--muted)}
  /* v1.2.115: login-aman — tombol lihat password */
  .pw-wrap{position:relative}
  .pw-wrap input{padding-right:46px}
  .pw-eye{position:absolute;right:6px;top:50%;transform:translateY(-50%);width:36px;height:36px;padding:0;background:transparent;color:var(--muted);border-radius:8px;display:flex;align-items:center;justify-content:center}
  .pw-eye:hover{background:#f0f0f7;color:var(--ink)}
  .pw-eye svg{width:20px;height:20px}
</style>"""),
 ("""      <input id="p" type="password" autocomplete="current-password" required>""",
  """      <div class="pw-wrap">
        <input id="p" type="password" autocomplete="current-password" required>
        <button type="button" class="pw-eye" id="pwEye" aria-label="Tampilkan password" title="Tampilkan password">
          <svg id="eyeOn" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>
          <svg id="eyeOff" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:none"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><path d="M14.12 14.12a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
        </button>
      </div>"""),
 ("""      btn = document.getElementById('btn');
""",
  """      btn = document.getElementById('btn');

  // v1.2.115: login-aman — lihat/sembunyikan password
  (function () {
    var p = document.getElementById('p'), eye = document.getElementById('pwEye'),
        on = document.getElementById('eyeOn'), off = document.getElementById('eyeOff');
    eye.addEventListener('click', function () {
      var show = p.type === 'password';
      p.type = show ? 'text' : 'password';
      on.style.display = show ? 'none' : ''; off.style.display = show ? '' : 'none';
      var t = show ? 'Sembunyikan password' : 'Tampilkan password';
      eye.setAttribute('aria-label', t); eye.title = t;
      p.focus();
    });
  })();

  // v1.2.115: hitung mundur saat akun dikunci (per username, tahan refresh)
  var LKEY = 'dei_login_lock', lockTimer = null;
  function lockGet() { try { return JSON.parse(localStorage.getItem(LKEY) || 'null'); } catch (e) { return null; } }
  function lockSet(u, sec) { try { localStorage.setItem(LKEY, JSON.stringify({ u: u.toLowerCase().trim(), until: Date.now() + sec * 1000 })); } catch (e) {} }
  function lockTick() {
    clearInterval(lockTimer); lockTimer = null;
    var l = lockGet(), u = document.getElementById('u').value.toLowerCase().trim();
    if (!l || l.until <= Date.now()) { try { localStorage.removeItem(LKEY); } catch (e) {} btn.disabled = false; btn.textContent = 'Masuk'; return; }
    if (u && l.u !== u) { btn.disabled = false; btn.textContent = 'Masuk'; return; }
    var draw = function () {
      var s = Math.ceil((l.until - Date.now()) / 1000);
      if (s <= 0) { lockTick(); err.style.display = 'none'; return; }
      btn.disabled = true;
      btn.textContent = 'Coba lagi dalam ' + Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2);
    };
    draw(); lockTimer = setInterval(draw, 1000);
  }
  document.getElementById('u').addEventListener('input', lockTick);
  if (!ssoM_pending()) lockTick();
  function ssoM_pending() { return /[#&]sso=/.test(location.hash || ''); }
"""),
 ("""      } else {
        err.textContent = (res && res.error) || 'Gagal masuk.';
        err.style.display = 'block';
        btn.disabled = false; btn.textContent = 'Masuk';
      }""",
  """      } else {
        err.textContent = (res && res.error) || 'Gagal masuk.';
        err.style.display = 'block';
        btn.disabled = false; btn.textContent = 'Masuk';
        if (res && res.locked && res.retry_after) { lockSet(document.getElementById('u').value, res.retry_after); lockTick(); }   // v1.2.115
        else { var pw = document.getElementById('p'); pw.value = ''; pw.focus(); }
      }"""),
])
print('selesai', TAG)
