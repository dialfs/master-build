  // v1.2.184: lupa-password — minta tautan reset & atur password baru dari tautan email
  (function () {
    var lf = document.getElementById('form'), fp = document.getElementById('fpForm'), rp = document.getElementById('rpForm'),
        okb = document.getElementById('okMsg'), fpBtn = document.getElementById('fpBtn'), rpBtn = document.getElementById('rpBtn');
    if (!fp || !rp) return;
    function view(v) {
      lf.style.display = v === 'login' ? '' : 'none'; fp.style.display = v === 'fp' ? '' : 'none'; rp.style.display = v === 'rp' ? '' : 'none';
      err.style.display = 'none'; okb.style.display = 'none';
    }
    function showErr(t) { err.textContent = t; err.style.display = 'block'; okb.style.display = 'none'; }
    function showOk(t) { okb.textContent = t; okb.style.display = 'block'; err.style.display = 'none'; }
    function post(action, body) {
      return fetch(API + '?action=' + action, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
        .then(function (r) { return r.json().catch(function () { return { ok: false, error: 'Respons server tidak valid (HTTP ' + r.status + ').' }; }); });
    }
    function pwBad(pw) {
      var miss = [];
      if (pw.length < 8) miss.push('minimal 8 karakter');
      if (!/[a-z]/.test(pw)) miss.push('huruf kecil');
      if (!/[A-Z]/.test(pw)) miss.push('huruf besar');
      if (!/[0-9]/.test(pw)) miss.push('angka');
      return miss.length ? 'Password belum memenuhi syarat: ' + miss.join(', ') + '.' : '';
    }
    document.getElementById('fpLink').addEventListener('click', function (e) {
      e.preventDefault(); view('fp');
      var q = document.getElementById('fpQ'); if (!q.value) q.value = document.getElementById('u').value.trim(); q.focus();
    });
    Array.prototype.forEach.call(document.querySelectorAll('[data-back-login]'), function (a) {
      a.addEventListener('click', function (e) { e.preventDefault(); view('login'); document.getElementById('u').focus(); });
    });
    var cdTimer = null;
    function cooldown(sec) {
      clearInterval(cdTimer); fpBtn.disabled = true;
      var end = Date.now() + sec * 1000;
      var draw = function () {
        var s = Math.ceil((end - Date.now()) / 1000);
        if (s <= 0) { clearInterval(cdTimer); fpBtn.disabled = false; fpBtn.textContent = 'Kirim ulang tautan'; return; }
        fpBtn.textContent = 'Kirim ulang dalam ' + s + ' dtk';
      };
      draw(); cdTimer = setInterval(draw, 1000);
    }
    fp.addEventListener('submit', function (e) {
      e.preventDefault();
      var q = document.getElementById('fpQ').value.trim();
      if (!q) { showErr('Isi username atau email Anda.'); return; }
      fpBtn.disabled = true; fpBtn.textContent = 'Mengirim...';
      post('forgot_password', { login: q }).then(function (res) {
        if (res && res.ok) { showOk(res.message || 'Tautan reset sudah dikirim. Cek email Anda.'); cooldown(60); }
        else { showErr((res && res.error) || 'Gagal mengirim tautan reset.'); fpBtn.disabled = false; fpBtn.textContent = 'Kirim tautan reset'; }
      }).catch(function () { showErr('Tidak dapat terhubung ke server.'); fpBtn.disabled = false; fpBtn.textContent = 'Kirim tautan reset'; });
    });
    document.getElementById('rpShow').addEventListener('change', function () {
      var t = this.checked ? 'text' : 'password';
      document.getElementById('rpPw').type = t; document.getElementById('rpPw2').type = t;
    });
    var m = /[#&]reset=([a-f0-9]{64})/i.exec(location.hash || '');
    if (!m) return;
    var tok = m[1];
    try { history.replaceState(null, '', location.pathname); } catch (e) {}
    view('rp');
    rpBtn.disabled = true; rpBtn.textContent = 'Memeriksa tautan...';
    function dead(msg) {
      showErr(msg || 'Tautan reset tidak valid atau kedaluwarsa.');
      rpBtn.disabled = false; rpBtn.textContent = 'Minta tautan baru';
      rpBtn.dataset.dead = '1';
    }
    post('reset_password_check', { token: tok }).then(function (res) {
      if (!res || !res.ok) { dead(res && res.error); return; }
      document.getElementById('rpWho').textContent = res.username;
      document.getElementById('rpWhoRow').style.display = '';
      rpBtn.disabled = false; rpBtn.textContent = 'Simpan password baru';
      document.getElementById('rpPw').focus();
    }).catch(function () { dead('Tidak dapat terhubung ke server.'); });
    rp.addEventListener('submit', function (e) {
      e.preventDefault();
      if (rpBtn.dataset.dead) { delete rpBtn.dataset.dead; view('fp'); document.getElementById('fpQ').focus(); return; }
      var a = document.getElementById('rpPw').value, b = document.getElementById('rpPw2').value;
      var bad = pwBad(a);
      if (bad) { showErr(bad); return; }
      if (a !== b) { showErr('Konfirmasi password tidak sama.'); return; }
      rpBtn.disabled = true; rpBtn.textContent = 'Menyimpan...';
      post('reset_password', { token: tok, new_password: a }).then(function (res) {
        if (res && res.ok) {
          try { localStorage.removeItem(TK); localStorage.removeItem(UK); localStorage.removeItem(LKEY); } catch (e2) {}
          view('login');
          document.getElementById('u').value = res.username || '';
          var p = document.getElementById('p'); p.value = ''; p.focus();
          btn.disabled = false; btn.textContent = 'Masuk';
          showOk(res.message || 'Password berhasil diganti. Silakan masuk.');
        } else if (res && res.expired) { dead(res.error); }
        else { showErr((res && res.error) || 'Gagal menyimpan password.'); rpBtn.disabled = false; rpBtn.textContent = 'Simpan password baru'; }
      }).catch(function () { showErr('Tidak dapat terhubung ke server.'); rpBtn.disabled = false; rpBtn.textContent = 'Simpan password baru'; });
    });
  })();
