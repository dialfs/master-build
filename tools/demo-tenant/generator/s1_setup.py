import json, subprocess, os
from drv import *

s = rj('settings.json')
s['api'] = {
    'provider': 'openrouter', 'openrouter_model': 'google/gemini-2.5-flash', 'openrouter_api_key': 'mock-key',
    'claude_api_key': '', 'key_is_set': False, 'fallback': 'google/gemini-2.5-flash-lite',
    'max_tokens': 700, 'rate_limit': 60, 'kb_max_results': 5, 'log_limit': 5000,
}
s['bot'] = {
    'bot_name': 'Nadia - Nusa EV',
    'persona_company': 'Nusa EV Motor Listrik',
    'greeting': 'Halo Kak! Saya Nadia dari Nusa EV 👋 Mau tanya harga, test ride, atau cicilan motor listrik?',
    'birthday_greeting': '',
    'quick_replies': ['Harga & tipe motor', 'Simulasi cicilan', 'Jadwalkan test ride'],
    'system_prompt': ("Anda adalah Nadia, asisten penjualan Nusa EV, dealer motor listrik di Jakarta.\n"
                      "- Jawab hanya berdasarkan Knowledge Base dan Daftar Harga. Bila tidak yakin, tawarkan disambungkan ke tim sales.\n"
                      "- Ramah, singkat, sapa pelanggan dengan \"Kak\".\n"
                      "- Ajak pelanggan menjadwalkan test ride atau datang ke showroom, dan tanyakan nama serta domisili untuk ditindaklanjuti sales."),
}
s['appearance'] = dict(s.get('appearance', {}), primary_color='#0E7C66', avatar_type='emoji', avatar_emoji='⚡')
s['widget'] = dict(s.get('widget', {}), chatbot_enabled=True, whatsapp_enabled=True, whatsapp_number='6281100000001',
                   whatsapp_message='Halo Nusa EV, saya mau tanya motor listrik.', lead_form={'enabled': False})
s['whatsapp_api'] = {
    'enabled': True, 'provider': 'waha', 'waha_url': 'http://127.0.0.1:9100', 'waha_api_key': 'mock',
    'waha_session': 'dei-demo', 'waha_webhook_key': 'seedkey', 'waha_number': '6281100000001', 'keep_context': True,
}
s['handoff'] = {'enabled': True, 'keywords': ['admin', 'manusia', 'sales', 'komplain', 'cs']}
s['central_server'] = dict(s.get('central_server', {}), url='http://127.0.0.1:9100', tenant_id='demo', license_key='mock-license')
s['onboarding'] = {'enabled': False}
wj('settings.json', s)

ph = subprocess.run(['php', '-r', 'echo password_hash("seed-Only-123", PASSWORD_DEFAULT);'], capture_output=True, text=True).stdout
wj('users.json', [{'username': 'seed', 'password': ph, 'role': 'super_admin', 'name': 'Seeder', 'migrated_3role': True}])
wj('version.json', {'version': 'v1.2.220', 'updated_at': '', 'source': 'demo-seed'})

set_time(at(20, 9, 0))
r = call('login', 'POST', body={'username': 'seed', 'password': 'seed-Only-123'})
print('login', r.get('ok'), list(r.keys()))
open(os.path.expanduser('~/demo/seed/token'), 'w').write(r['token'])
print(call('cap_status', token=r['token']))
print(call('plan_info', token=r['token']))
