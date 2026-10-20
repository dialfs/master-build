# Gateway WAHA — kit VPS

Dipakai tenant DEI Chatbot (hosting biasa/versi JSON maupun server sendiri) dengan penyedia **WAHA**.
Satu VPS bisa melayani banyak tenant: satu **sesi** = satu nomor WA, nama sesi unik per tenant. Sejak WAHA 2026.6.1 semua fitur eks-Plus (termasuk sesi tanpa batas) ada di image gratis `devlikeapro/waha` — pakai versi >= 2026.6.1.

## 0. Satu VPS dengan chatbot (Halte Bus) — paling sederhana
WAHA cukup di localhost, tanpa domain/HTTPS sendiri:
```bash
ssh root@212.85.25.180 'bash -s' < ~/Herd/master-build/server/waha/install-waha.sh
```
Lalu di dashboard tenant: URL Server WAHA `http://127.0.0.1:3000`, API Key dari output skrip, Nama Sesi = slug (mis. `sinarjaya`).
Langkah 1–2 di bawah hanya untuk WAHA yang dipakai tenant di server lain (mis. cPanel).

## 1. Pasang
```bash
apt install -y docker.io docker-compose-v2 nginx certbot python3-certbot-nginx
mkdir -p /opt/waha && cd /opt/waha            # salin docker-compose.yml + .env.example ke sini
cp .env.example .env && nano .env             # isi WAHA_API_KEY (acak panjang) & WAHA_DASH_PASS
docker compose up -d && docker compose logs -f --tail 50
```

## 2. HTTPS (nginx)
`/etc/nginx/sites-available/waha`:
```nginx
server {
  server_name wa.domain-anda.com;
  client_max_body_size 50m;
  location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 120s;
  }
}
```
```bash
ln -s /etc/nginx/sites-available/waha /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx
certbot --nginx -d wa.domain-anda.com
```

## 3. Hubungkan tenant
Tenant di cPanel (mis. Pomelotel): `bash ~/Herd/master-build/server/waha/waha-tenant.sh pomeloteljkt` — cek/pasang WAHA publik, cetak URL + API key + nama sesi untuk diisi.
1. Dashboard tenant (Super Admin) › Widget & API › WhatsApp Bot › Penyedia **WAHA**: isi URL (`https://wa.domain-anda.com`), API Key, Nama Sesi (unik per tenant, mis. `sinarjaya`). Aktifkan bot, Simpan.
2. Kartu **Koneksi WhatsApp** › **Hubungkan (scan QR)** — sesi dibuat otomatis lengkap dengan webhook (`message.any` + `session.status`, HMAC SHA-512). Admin klien bisa melakukan langkah ini sendiri.
3. Sesi lama / ganti domain tenant: Super Admin klik **Pasang webhook otomatis**.

## Opsi media
Di `.env`: `WAHA_DOWNLOAD_MEDIA=true` (bawaan sejak v1.2.94 — tenant mengunduh media dari sini dalam 3 menit, lalu menyimpannya 30 hari) atau `false`, lalu `./media.sh on|off` (atau ubah `.env` + `docker compose up -d`).

| | `false` (mati) | `true` (nyala) |
|---|---|---|
| Disk & CPU | hemat | file diunduh, dihapus otomatis setelah `WAHA_FILES_LIFETIME` detik (bawaan 180) |
| Dashboard | tercatat "[Pesan media]" | tercatat jenisnya: gambar / video / audio / dokumen |
| Bot | balas "hanya bisa teks" | sama (bot DEI hanya memproses teks) |

Berlaku untuk semua sesi di server ini. Ubah opsi = container restart sebentar; sesi tersambung lagi otomatis.

## Catatan
- Tenant di cPanel: kalau webhook ditolak (403/406) oleh ModSecurity/Imunify, whitelist IP VPS di hosting.
- Backup folder `sessions/` — hilang = semua nomor harus scan ulang.
- Jalur tidak resmi (WhatsApp Web): hindari blast; risiko blokir sama seperti Fonnte.
- Cek nama variabel env & tag image di dokumentasi WAHA saat memasang (waha.devlike.pro) — pin `WAHA_TAG` ke versi yang sudah dicoba.
