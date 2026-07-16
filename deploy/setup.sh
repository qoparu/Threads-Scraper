#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# JasPulse — установка парсера на сервер (Ubuntu/Debian).
# Делает: системные зависимости, venv, Playwright+Chromium, systemd-таймер (раз в час).
#
# ПОРЯДОК:
#   1) git clone git@github.com:qoparu/Threads-Scraper.git && cd Threads-Scraper
#   2) СКОПИРУЙ секреты и данные (см. DEPLOY_SERVER.md): .env, auth_state.json, data/
#   3) bash deploy/setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
RUN_USER="$(whoami)"
PY="$REPO/venv/bin/python"
cd "$REPO"

echo "==> Репозиторий: $REPO   пользователь: $RUN_USER"

# 1. Системные зависимости
echo "==> Устанавливаю системные пакеты…"
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip curl ca-certificates

# 1b. Swap для маломощных серверов (Chromium прожорлив; 2ГБ swap если RAM < 3ГБ)
MEM_MB="$(free -m | awk '/^Mem:/{print $2}')"
if [ "${MEM_MB:-9999}" -lt 3000 ] && [ -z "$(swapon --show)" ]; then
  echo "==> RAM ${MEM_MB} МБ — создаю 2 ГБ swap (иначе Chromium может упасть по памяти)…"
  sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

# 2. Node.js (нужен для деплоя на Vercel через npx)
if ! command -v node >/dev/null 2>&1; then
  echo "==> Ставлю Node.js 20…"
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

# 3. Python-окружение
echo "==> Создаю venv и ставлю зависимости…"
python3 -m venv venv
"$REPO/venv/bin/pip" install --upgrade pip
"$REPO/venv/bin/pip" install -r requirements.txt

# 4. Браузер для Playwright + его системные библиотеки
echo "==> Ставлю Chromium для Playwright…"
"$PY" -m playwright install --with-deps chromium

# 5. Проверка секретов/данных (их нужно скопировать ВРУЧНУЮ, не через git)
echo "==> Проверяю секреты и данные…"
MISSING=0
for f in .env auth_state.json; do
  [ -f "$REPO/$f" ] || { echo "   ⚠ НЕТ $f — скопируй его на сервер (scp), см. DEPLOY_SERVER.md"; MISSING=1; }
done
[ -f "$REPO/data/meta_clean.json" ] || echo "   ⚠ нет data/meta_clean.json — без базовых FB/IG дашборд будет только по Threads"
if [ "$MISSING" = "1" ]; then
  echo "==> Останавливаюсь: сначала скопируй .env и auth_state.json, потом запусти скрипт снова."
  exit 1
fi
chmod 600 "$REPO/.env" "$REPO/auth_state.json" 2>/dev/null || true

# 6. systemd: сервис (один прогон) + таймер (раз в час)
echo "==> Настраиваю systemd-таймер (раз в час)…"
sudo tee /etc/systemd/system/jaspulse.service >/dev/null <<UNIT
[Unit]
Description=JasPulse — сбор Threads + пересборка и деплой дашборда
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$RUN_USER
WorkingDirectory=$REPO
ExecStart=$PY $REPO/run_hourly.py
TimeoutStartSec=1800
UNIT

sudo tee /etc/systemd/system/jaspulse.timer >/dev/null <<UNIT
[Unit]
Description=Запуск JasPulse раз в час

[Timer]
OnCalendar=hourly
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now jaspulse.timer

echo ""
echo "✅ Готово. Таймер активен:"
systemctl list-timers jaspulse.timer --no-pager || true
echo ""
echo "Проверить один прогон прямо сейчас:   sudo systemctl start jaspulse.service"
echo "Смотреть логи:                        journalctl -u jaspulse.service -f"
