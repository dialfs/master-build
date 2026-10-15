# Uji dua mode (file vs mysql+redis)

Regresi untuk lapisan penyimpanan v1.2.71. Butuh: PHP 8.x (pdo_mysql, redis), MySQL/MariaDB
(root tanpa password, user `sj`/`sjpass`), Redis di 6379, Python 3.

```bash
cd tools/uji-dua-mode
python3 mock.py sends.log &           # tiruan OpenRouter (1,5 dtk), Meta Graph, Telegram, pusat
./mkapp.sh appfile; ./srv.sh appfile 8101
./mkapp.sh appdb db; ./srv.sh appdb 8102
DATA_UJI=/path/data-uji.tgz ./run_all.sh
```

Yang diuji: (1) 9 endpoint dashboard identik di dua mode dengan data asli, (2) jalur tulis
dashboard + echo HP, (3) auto-closing via cron_tick, (4) beban 1.200 pesan / 16 worker tanpa
balasan ganda, (5) worker dibunuh di tengah job, (6) Redis mati -> fallback.
App uji (`app*/`, `eq*/`) dibuat ulang tiap jalan; jangan di-commit.
