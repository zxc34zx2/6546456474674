#!/bin/bash
# 🔄 Восстановление из бекапа

if [ -z "$1" ]; then
    echo "❌ Укажите файл бекапа для восстановления"
    echo "Использование: ./restore-docker.sh secure_data/backups/backup_20240101_120000.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Файл бекапа не найден: $BACKUP_FILE"
    exit 1
fi

echo "=========================================="
echo "🔄 ВОССТАНОВЛЕНИЕ ИЗ БЕКАПА"
echo "=========================================="
echo "📦 Файл: $BACKUP_FILE"

# Остановка контейнера
echo "🛑 Остановка контейнера..."
docker-compose stop telegram-bot

# Создание бекапа текущего состояния
CURRENT_BACKUP="secure_data/backups/pre_restore_$(date +%Y%m%d_%H%M%S).tar.gz"
echo "💾 Создание бекапа текущего состояния: $CURRENT_BACKUP"
tar -czf "$CURRENT_BACKUP" secure_data/secure_bot.db secure_config.json 2>/dev/null || true

# Восстановление
echo "🔧 Восстановление данных..."
tar -xzf "$BACKUP_FILE"

# Установка прав
chmod 600 secure_config.json 2>/dev/null || true
chmod 700 secure_data/secure_bot.db 2>/dev/null || true

# Запуск контейнера
echo "🚀 Запуск контейнера..."
docker-compose start telegram-bot

echo "✅ Восстановление завершено"