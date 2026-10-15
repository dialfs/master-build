#!/bin/bash
# mkapp.sh <nama> [db]  — salinan app uji dari ../work dengan URL eksternal diarahkan ke mock
set -e; cd "$(dirname "$0")"; A=$1
rm -rf $A && mkdir $A && cp -r ../../dei-chatbot-ai/{api,assets,dashboard,vendor} $A/ && mkdir -p $A/data
sed -i "s#https://openrouter.ai/api/v1/chat/completions#http://127.0.0.1:9900/api/v1/chat/completions#; s#https://graph.facebook.com/#http://127.0.0.1:9900/#; s#https://api.telegram.org/bot#http://127.0.0.1:9900/bot#" $A/api/index.php
cat > $A/data/settings.json <<'J'
{"api":{"provider":"openrouter","openrouter_api_key":"x","openrouter_model":"google/gemini-2.5-flash","model":"claude-haiku-4-5-20251001","max_tokens":400,"rate_limit":1000,"log_limit":5000},
 "bot":{"name":"Tes","system_prompt":"Kamu CS."},
 "whatsapp_api":{"enabled":true,"provider":"meta","access_token":"tok","phone_number_id":"123","app_secret":"sec","keep_context":true,"rate_limit_per_number":1000},
 "handoff":{"enabled":true,"keywords":["admin"]}}
J
echo '[]' > $A/data/knowledge-base.json; echo '[]' > $A/data/users.json
if [ "$2" = db ]; then
cat > $A/data/server.php <<'J'
<?php return ['storage'=>'mysql','queue'=>'redis','db'=>['host'=>'127.0.0.1','name'=>'sj_chat','user'=>'sj','pass'=>'sjpass'],'redis'=>['host'=>'127.0.0.1','port'=>6379,'prefix'=>'sj:']];
J
mysql -uroot -e "DROP DATABASE IF EXISTS sj_chat; CREATE DATABASE sj_chat CHARACTER SET utf8mb4;"
redis-cli flushall >/dev/null
(cd $A && php api/index.php action=db_init)
fi
