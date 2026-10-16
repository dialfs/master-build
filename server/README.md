# DEI Chatbot — server sendiri (Halte Bus)

Paket ini menjalankan **kode DEI Chatbot yang sama** (`dei-master.zip`) di VPS sendiri,
dengan mesin yang lebih kuat: MySQL untuk data per pesan, Redis untuk antrean, dan
worker yang memanggil AI. Update DEI otomatis berlaku di sini lewat jalur rilis yang sama.

```
Meta WA ──► Nginx + PHP-FPM (webhook: cek tanda tangan, antre, 200 < 100 ms)
                 │
                 ▼
           Redis  q:wa ──► worker × N  (php api/index.php action=wa_worker)
                                │  waProcessIncoming() — kode sama dengan tenant DEI
                                ├──► Provider AI (OpenRouter / Claude)
                                ├──► MySQL (log, kontak, sesi, conv-state)
                                └──► Meta: kirim balasan
cron tiap menit ─► action=cron_tick (auto-closing, eskalasi, sapu claim, bersih sesi)
dei-pusat (chat.deintegra.com) ─► lisensi, kuota, update
```

## Saklar di kode (v1.2.71)

Berkas opsional `data/server.php` (tidak pernah disentuh updater):

| Kunci | Shared hosting (bawaan) | Server Halte Bus |
| --- | --- | --- |
| `storage` | `file` — JSON seperti biasa | `mysql` — log, kontak, sesi WA, conv-state di MySQL |
| `queue` | `sync` — diproses di request webhook | `redis` — webhook mengantre, worker memproses |

Tanpa `data/server.php` perilakunya **identik dengan v1.2.70** (diuji: 9 endpoint dashboard
memberi output sama persis dengan data asli).

Yang dijamin di mode antrean:
- **Tidak dibalas ganda** — `wamid` dari Meta dicatat; kiriman ulang diabaikan.
- **Urut per nomor** — kunci Redis per nomor; nomor berbeda tetap paralel.
- **Tahan worker mati** — job yang sedang diproses disimpan di `q:wa:proc:<slot>` dan diantre
  ulang saat slot itu hidup lagi (maks 3 percobaan, lalu ke `q:wa:dead`).
- **Redis mati** — webhook otomatis memproses langsung (perilaku lama), idempotensi pindah ke MySQL.

Pengaturan tambahan per klien di `data/server.php` (v1.2.72, dipasang otomatis oleh `add-client.sh`):

| Kunci | Fungsi |
| --- | --- |
| `debounce_sec` => 2 | Bubble beruntun dari satu nomor (jeda < 2 dtk) digabung jadi satu panggilan AI & satu balasan. Uji: 600 bubble / 200 nomor -> 200 panggilan AI, tidak ada yang hilang. Menambah ±2 dtk ke waktu balas. |
| `ai_fallback` => ['provider' => 'openrouter', 'model' => 'anthropic/claude-haiku-4.5'] | Kalau AI utama gagal, dicoba sekali dengan model cadangan. |
| `ai_fail_handoff` => true, `ai_fail_text` | Kalau semua AI gagal: pelanggan dapat `ai_fail_text`, nomor dialihkan ke agent (mode manusia), notifikasi Telegram. |

| `brand` => 'haltebus' (v1.2.73) | Dashboard tampil sebagai **Haltebus Chatbot**: warna merah Haltebus, nama "DEI" diganti "Haltebus". Ikon/logo/manifest disalin dari `server/brand/haltebus/` oleh `add-client.sh` (pakai `BRAND=none` untuk tampilan DEI). |

| `redbus` (v1.2.81) | Link redBus otomatis untuk pertanyaan harga/tiket: `['op_id' => '18107', 'cities' => ['Jakarta' => 193490, 'Purwokerto' => 194407, 'Jogja' => 'Yogyakarta']]` (nilai = ID kota redBus, atau nama kota lain sebagai alias; opsional `'label' => 'Cek harga & pesan tiket:'`). AI menulis tag `[[REDBUS:asal|tujuan|YYYY-MM-DD]]`, server menggantinya dengan link (tanggal kosong = hari ini). ID kota diambil dari URL redBus (`fromCityId`). Tanpa kunci ini fitur mati. |

`wa_queue_status` menampilkan `queue_active`; `false` berarti Redis tidak terjangkau (health.sh mengirim peringatan).

Hasil uji beban (AI tiruan 1,5 dtk/pesan): 16 worker = ±10 pesan/detik, 1.200 pesan dari
400 nomor tanpa balasan ganda dan tanpa riwayat hilang. Target 10.000 pesan/hari ≈ puncak 5/detik.

## Pasang VPS baru (Ubuntu 24.04 / 26.04 LTS) — dari Mac, satu perintah

```bash
cd ~/Herd/master-build && git pull
./server/deploy-vps.sh root@212.85.25.180 sinarjaya haltebus.chat/sinarjaya 8
```

`deploy-vps.sh` (password root diminta sekali): cek DNS & OS → kirim `server/` + `~/Herd/dei-pusat/master/dei-master.zip`
→ `install-server.sh` (aman diulang; ukuran MySQL/Redis ikut RAM, swap 2 GB kalau belum ada)
→ `add-client.sh` (dilewati kalau klien sudah ada) → cek antrean & HTTPS.
Password admin awal dicetak sekali dan disalin ke `~/hb-deploy-<slug>.txt` — catat, lalu hapus berkas itu.

Lalu isi `/etc/dei/alert.conf` (Telegram) dan `/etc/dei/backup.conf` (rclone off-site — wajib untuk produksi).

## Tambah klien

Dua bentuk alamat:

| Bentuk | Contoh | Catatan |
| --- | --- | --- |
| **Path** (bawaan Halte Bus) | `haltebus.chat/sinarjaya` | Satu domain + satu sertifikat untuk semua klien. Path wajib = slug. Vhost `dei-host-haltebus.chat`, tiap klien satu berkas `/etc/nginx/dei-paths/haltebus.chat/<slug>.conf`. |
| Domain sendiri | `chat.sinarjaya.com` | Vhost sendiri + sertifikat sendiri; DNS domain itu diarahkan ke VPS. |

```bash
# di VPS (atau ulangi deploy-vps.sh dengan slug lain dari Mac)
sudo /opt/dei/server/add-client.sh sinarjaya haltebus.chat/sinarjaya 8
```

Alamat klien mode path: dashboard `https://haltebus.chat/<slug>/` (→ login), `…/<slug>/login`,
webhook Meta `https://haltebus.chat/<slug>/api/index.php?action=wa_webhook`.
Dashboard & API menghitung base path sendiri dari URL, jadi kode tidak berubah.

Yang dibuat per klien:

| Per klien | Contoh `sinarjaya` |
| --- | --- |
| User Linux | `dei-sinarjaya` (PHP-FPM, worker, cron jalan sebagai user ini) |
| Folder | `/var/www/sinarjaya` |
| Database + user MySQL | `sinarjaya_chat` / `dei-sinarjaya` (password acak di `data/server.php`) |
| Prefix Redis | `sinarjaya:` |
| Worker | supervisord `dei-sinarjaya-worker:*` (16 proses) |
| Cron | `/etc/cron.d/dei-sinarjaya` |
| Akun dashboard awal | `admin` + password acak (dicetak sekali di akhir) |

Setelah itu:
1. Login dashboard, ganti password admin.
2. Daftarkan tenant di dei-pusat, isi `tenant_id` + `license_key` di **Pengaturan › Server Pusat**.
3. Hubungkan WhatsApp (Embedded Signup / coexistence) — webhook: `https://<domain>/api/index.php?action=wa_webhook`.
4. Pindahan dari tenant lama: salin `data/*.json` lama ke `data/`, lalu
   `sudo -u dei-<slug> php /var/www/<slug>/api/index.php action=db_import`.

## Update

```bash
sudo /opt/dei/server/update-all.sh            # semua klien
sudo /opt/dei/server/update-all.sh sinarjaya  # satu klien
```

Memakai updater bawaan aplikasi (`action=update_cli` = tombol "Pasang Update" di dashboard:
unduh dari pusat, cek md5, backup, ganti 5 berkas), lalu menjalankan ulang worker.

## Operasional

| Perlu | Perintah |
| --- | --- |
| Status antrean | `sudo -u dei-<slug> php /var/www/<slug>/api/index.php action=wa_queue_status` |
| Worker | `sudo supervisorctl status` · `sudo supervisorctl restart dei-<slug>-worker:*` |
| Log worker / PHP | `/var/log/dei/<slug>-worker.log` · `/var/log/dei/<slug>-php.log` |
| Tambah worker | ubah `numprocs` di `/etc/supervisor/conf.d/dei-<slug>.conf`, lalu `supervisorctl update` |
| Backup | otomatis 02:30 → `/var/backups/dei/<slug>/` (+ rclone bila diisi), simpan 30 hari |
| Restore DB | `gunzip -c <file>-db.sql.gz \| mysql <slug>_chat` |
| Health | tiap 5 menit: layanan mati, antrean > 200, worker 0, job gagal permanen → Telegram |

Catatan: dei-pusat juga memanggil `cron_tick` lewat HTTP tiap menit (untuk dorongan fitur &
notifikasi rilis). Cron lokal tetap dipasang supaya klien jalan walau pusat tidak terjangkau;
`cron.lock` mencegah dua tick bertabrakan.

## Aturan pengembangan (wajib, supaya update tetap berlaku di dua mode)

Data yang ditulis tiap pesan **hanya** lewat fungsi lapisan penyimpanan di `api/index.php`
(blok `v1.2.71: DRIVER PENYIMPANAN`):

| Data | Pakai | Jangan |
| --- | --- | --- |
| Log percakapan | `logPrepend`, `logMutate`, `logReadAll`, `logReadByNumber` | `readJson(LOG_FILE…)` |
| Kontak WA | `waContactUpdate`, `waContactGet`, `waGetContacts` | `writeJson(CONTACTS_FILE…)` |
| Sesi WA | `waLoadHistory`, `waSaveHistory` | berkas `wa-sessions/` langsung |
| Conv-state | `convStateMutate($fn, $num)`, `convStateReadAll` | `readJson(CONV_STATE_FILE…)` |
| Status kecil (mode, claim, usage) | fungsi yang sudah ada — sudah dibungkus `deiWithLock` | baca-ubah-tulis tanpa kunci |

`tools/cek-storage.py` memeriksa aturan ini dan **menolak rilis** yang melanggar:

```bash
python3 tools/cek-storage.py dei-chatbot-ai/api/index.php
```
