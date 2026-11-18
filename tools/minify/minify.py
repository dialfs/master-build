#!/usr/bin/env python3
"""Minify JS tenant untuk paket rilis (sejak v1.2.197: kode-terlindung).
Sumber di dei-tenant tetap utuh; hasil minified hanya masuk update.zip & master.
Pakai dari build_vXXXX.py:  from minify import minify_js;  minify_js(src, out, versi)
Butuh node. terser dibundel di tools/minify/node_modules (fallback: npx -y terser@5)."""
import os, subprocess, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
PRE = '/* DEI Chatbot %s — (c) PT Daya Estima Integra. Hak cipta dilindungi; dilarang menyalin, mengubah atau mendistribusikan. */'
def minify_js(src, out, version):
    node = shutil.which('node')
    assert node, 'node tidak ditemukan — pasang Node.js (brew install node) untuk build rilis'
    t = os.path.join(HERE, 'node_modules', 'terser', 'bin', 'terser')
    cmd = [node, t] if os.path.isfile(t) else ['npx', '-y', 'terser@5']
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(cmd + [src, '-c', '-m', '--comments', 'false', '-o', out], check=True)
    body = open(out, encoding='utf-8').read()
    open(out, 'w', encoding='utf-8').write(PRE % version + '\n' + body)   # terser 5 mengabaikan --preamble di CLI
    subprocess.run([node, '--check', out], check=True)
    a, b = os.path.getsize(src), os.path.getsize(out)
    assert b > 1000 and b < a, 'hasil minify mencurigakan: %s (%d -> %d)' % (src, a, b)
    print('minify %-36s %7d -> %7d B' % (os.path.relpath(src, os.path.dirname(os.path.dirname(src))), a, b))
    return out
