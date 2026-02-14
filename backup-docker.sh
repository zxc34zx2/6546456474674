#!/bin/bash
# 💾 Бекап данных Docker контейнера

set -e

BACKUP_DIR="secure_data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"

echo "=========================================="
echo "💾 СОЗДАНИЕ БЕКАПА"
echo "=========================================="

# Создание директории для бекапов
mkdir -p "$BACKUP_DIR"

# Остановка контейнера для консистентности данных
echo "🛑 Остановка контейнера..."
docker-compose stop telegram-bot

# Создание бекапа
echo "📦 Создание архива..."
tar -czf "$BACKUP_FILE" \
    secure_data/secure_bot.db \
    secure_config.json \
    logs/bot.log \
    2>/dev/null || true

# Запуск контейнера
echo "🚀 Запуск контейнера..."
docker-compose start telegram-bot

# Проверка бекапа
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "✅ Бекап создан: ${BACKUP_FILE}"
    echo -e "📊 Размер: ${SIZE}"
    
    # Оставляем только последние 10 бекапов
    ls -t ${BACKUP_DIR}/backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
    echo "🧹 Очистка старых бекапов выполнена"
else
    echo "❌ Ошибка создания бекапа!"
    exit 1
fi