    var _bSync = $('#btnEsSync');   // v1.2.225: es-coex — ulangi subscribe + sinkron kontak & riwayat
    if (_bSync) _bSync.onclick = function () {
      if (!confirm('Ulangi subscribe webhook dan sinkron kontak + riwayat chat dari aplikasi WhatsApp Business? Sinkron hanya bisa dalam 24 jam setelah nomor dihubungkan.')) return;
      var st = $('#es_status'); if (st) { st.textContent = 'Menyinkronkan…'; st.style.color = ''; }
      api('wa_es_sync', { method: 'POST', body: {} }).then(function (r) {
        if (!r || !r.ok) { if (st) { st.textContent = 'Gagal: ' + ((r && r.error) || 'tidak diketahui'); st.style.color = '#b42318'; } return; }
        var sy = r.sync || {}, sb = r.subscribe || {};
        var txt = 'Webhook: ' + (sb.ok ? (sb.override ? 'diarahkan ke tenant ini' : 'pakai URL app') : 'gagal (' + (sb.error || '') + ')')
          + ' · Kontak: ' + (sy.smb_app_state_sync === 'ok' ? 'diminta' : (sy.smb_app_state_sync || '-'))
          + ' · Riwayat: ' + (sy.history === 'ok' ? 'diminta' : (sy.history || '-'));
        if (st) { st.textContent = txt; st.style.color = (sb.ok && sy.history === 'ok') ? '#1a7f37' : '#b42318'; }
      });
    };
