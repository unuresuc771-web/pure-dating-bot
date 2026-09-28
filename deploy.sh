#!/usr/bin/env bash
set -e

echo "=== Развертывание Pure Match Bot 24/7 ==="

# 1. Обновление пакетов и установка зависимостей
apt-get update -y
apt-get install -y python3 python3-pip python3-venv curl

# 2. Создание каталога приложения
APP_DIR="/opt/pure_match_bot"
mkdir -p "$APP_DIR"

# 3. Настройка виртуального окружения
if [ ! -d "$APP_DIR/.venv" ]; then
    python3 -m venv "$APP_DIR/.venv"
fi

# 4. Установка Python библиотек
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# 5. Установка и запуск системной службы systemd
cp "$APP_DIR/pure_bot.service" /etc/systemd/system/pure_bot.service
systemctl daemon-reload
systemctl enable pure_bot.service
systemctl restart pure_bot.service

echo "=== Бот успешно развернут и запущен 24/7! ==="
systemctl status pure_bot.service --no-pager
