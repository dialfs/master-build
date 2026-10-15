# Uji mode server di Mac (Herd + DBngin + Redis)

Untuk melihat mode `mysql + redis` jalan di laptop sebelum membeli VPS.
Tenant `dei-tenant` (deintegra) **tidak diubah** — pakai situs Herd terpisah.

## 1. Siapkan layanan

```bash
# MySQL: buka DBngin, start MySQL 8 (port 3306)
# Redis:
brew install redis && brew services start redis
# Pastikan PHP Herd punya ekstensi redis & pdo_mysql:
php -m | grep -Ei 'redis|pdo_mysql'
```

Kalau ekstensi `redis` tidak ada, mode antrean otomatis mati (jatuh ke `sync`) — mode
`mysql` tetap bisa diuji.

## 2. Buat situs uji

```bash
cd ~/Herd
unzip ~/Herd/master-build/dei-master-v1.2.71.zip -d hb-sinarjaya-tmp
mv hb-sinarjaya-tmp/dei-chatbot-ai hb-sinarjaya && rmdir hb-sinarjaya-tmp
mysql -uroot -h127.0.0.1 -e "CREATE DATABASE sj_chat CHARACTER SET utf8mb4"
cat > hb-sinarjaya/data/server.php <<'PHP'
<?php return [
  'storage' => 'mysql', 'queue' => 'redis',
  'db'    => ['host' => '127.0.0.1', 'port' => 3306, 'name' => 'sj_chat', 'user' => 'root', 'pass' => ''],
  'redis' => ['host' => '127.0.0.1', 'port' => 6379, 'prefix' => 'sj:'],
];
PHP
cd hb-sinarjaya
php api/index.php action=db_init
php api/index.php action=wa_queue_status
```

Situs terbuka di `http://hb-sinarjaya.test`. Akun: salin `data/users.json` dari dei-tenant,
atau isi satu pengguna `{"username":"admin","password":"<teks>","role":"super_admin","migrated_3role":true}`
(password teks biasa otomatis di-hash saat login pertama).

## 3. Coba dengan data deintegra (opsional)

```bash
cp ~/Herd/dei-tenant/data/{chatbot-log.json,wa-contacts.json,leads.json,knowledge-base.json,settings.json} data/
cp -r ~/Herd/dei-tenant/data/wa-sessions data/
php api/index.php action=db_import
```

Dashboard harus menampilkan percakapan, kontak, dan laporan yang sama dengan dei-tenant.

## 4. Jalankan worker

Di Terminal terpisah (di VPS ini diurus supervisord):

```bash
cd ~/Herd/hb-sinarjaya && php api/index.php action=wa_worker slot=0
```

Webhook Meta tidak bisa menjangkau laptop; untuk uji kiriman WA sungguhan pakai VPS
(atau tunnel seperti `cloudflared`).
