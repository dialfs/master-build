#!/usr/bin/env bash
# Push dei-pusat + master-build ke GitHub lewat HTTPS (v1.2.140 sudah live sejak 17:36 WIB 4 Nov). Log: push-github.log
exec > >(tee "$HOME/Herd/master-build/tools/patch-v1.2.140/push-github.log") 2>&1
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0="url.https://github.com/.insteadOf" GIT_CONFIG_VALUE_0="git@github.com:"
for r in dei-pusat master-build; do
  echo "== $r =="; cd "$HOME/Herd/$r"
  git add -A tools/patch-v1.2.140 2>/dev/null; git commit -qm "tools: v1.2.140 deploy-tanpa-github + push" 2>/dev/null
  git push origin HEAD:main && echo "$r PUSH OK" || echo "$r PUSH GAGAL"
  git status -sb | head -1
done
echo; echo "SSH GitHub:"; ssh -o BatchMode=yes -T git@github.com 2>&1 | head -1
echo; read -r -p "Tekan Enter untuk menutup..." _
