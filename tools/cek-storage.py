#!/usr/bin/env python3
"""Penjaga aturan v1.2.71: data panas (log, kontak, sesi WA, conv-state) hanya boleh
disentuh lewat lapisan penyimpanan, supaya fitur baru otomatis jalan di mode file
(shared hosting) DAN mode mysql (server Halte Bus).

Pakai: tools/cek-storage.py dei-chatbot-ai/api/index.php   -> exit 1 kalau melanggar.
Baris yang sengaja dikecualikan diberi komentar:  // cek-storage: boleh
"""
import re, sys

# pola -> fungsi yang boleh memakainya
RULES = {
    r"readJson\(LOG_FILE":            {'logMutate', 'logReadAll'},
    r"writeJson\(LOG_FILE":           {'logMutate'},
    r"readJson\(CONTACTS_FILE":       {'waGetContacts'},
    r"writeJson\(CONTACTS_FILE":      {'waContactUpdate'},
    r"(read|write)Json\(CONV_STATE_FILE": {'convStateMutate'},
    r"waSessionFile\(":               {'waSessionFile', 'waLoadHistory', 'waSaveHistory'},
    r"WA_SESSIONS_DIR":               {'waSessionFile', 'waSaveHistory', 'deiPurgeSessions'},
    r"CONV_OPEN_FILE|CONV_DIR":       {'convStoreMutate', 'convStoreGet', 'convStoreOpen', 'convStoreEvict', 'convStoreRange', 'convFileAppend', 'convTrackingSince'},   # v1.2.101
    r"['\"](wa-contacts|chatbot-log|conv-state|conv-open)\.json['\"]": set(),
}
src = open(sys.argv[1], encoding='utf-8').read().split('\n')
func, bad = '<luar fungsi>', []
for no, line in enumerate(src, 1):
    m = re.match(r'^function\s+(\w+)\s*\(', line)
    if m: func = m.group(1)
    elif re.match(r'^(\}|switch\s*\(|\$action\s*=)', line) and not line.startswith('}'): func = '<luar fungsi>'
    if line.lstrip().startswith(('//', '*', '/*')) or 'cek-storage: boleh' in line: continue
    if re.match(r"^define\(", line): continue
    for pat, allowed in RULES.items():
        if re.search(pat, line) and func not in allowed:
            bad.append(f'{no}: [{func}] {line.strip()[:110]}')
if bad:
    print('cek-storage: GAGAL — data panas disentuh di luar lapisan penyimpanan (lihat blok v1.2.71):')
    print('\n'.join('  ' + b for b in bad))
    sys.exit(1)
print('cek-storage: OK')
