  /* v1.2.114: kontak-jumlah -- angka total per Lead Rating di tombol filter */
  function contactUpdateCounts() {
    var n = { all: contactData.length, vip_birthday_today: 0 };
    var _d = new Date();
    var _mmdd = String(_d.getMonth() + 1).padStart(2, '0') + '-' + String(_d.getDate()).padStart(2, '0');
    contactData.forEach(function (c) {
      var st = c.stage || 'new';
      n[st] = (n[st] || 0) + 1;
      if (c.vip && c.cust_dob && c.cust_dob.slice(5) === _mmdd) n.vip_birthday_today++;
    });
    $$('.contact-filter').forEach(function (b) {
      var sp = b.querySelector('.cf-n');
      if (!sp) {
        sp = document.createElement('span');
        sp.className = 'cf-n';
        sp.style.cssText = 'margin-left:6px;padding:0 6px;border-radius:999px;background:rgba(0,0,0,.07);font-size:11px;font-weight:700;line-height:18px;display:inline-block';
        b.appendChild(sp);
      }
      sp.textContent = (n[b.dataset.contactStage] || 0).toLocaleString('id-ID');
    });
  }
