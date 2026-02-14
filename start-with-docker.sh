#!/bin/bash
# 🐳 Docker запуск для VDSina

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}🐳 ЗАПУСК БОТА В DOCKER НА VDSINA${NC}"
echo -e "${GREEN}==========================================${NC}"

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен. Устанавливаем...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✅ Docker установлен. Перезайдите в сессию или выполните: newgrp docker${NC}"
    exit 0
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker Compose не установлен. Устанавливаем...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Создание необходимых директорий
echo -e "${YELLOW}📁 Создание директорий...${NC}"
mkdir -p secure_data/backups secure_data/logs secure_data/sessions logs
chmod 700 secure_data secure_data/* logs

# Проверка наличия конфигурации
if [ ! -f "secure_config.json" ]; then
    echo -e "${YELLOW}⚠️  Файл secure_config.json не найден. Создаем...${NC}"
    python3 -c "
import secrets
import json
import os

config = {
    'security': {
        'level': 'maximum',
        'sql_injection_protection': True,
        'api_protection': True,
        'memory_protection': True
    },
    'database': {
        'name': 'secure_data/secure_bot.db',
        'backup_interval': 3600
    },
    'logging': {
        'level': 'INFO',
        'max_size': '10MB'
    }
}

keys = {
    'database_key': secrets.token_hex(32),
    'session_key': secrets.token_hex(32),
    'admin_key': secrets.token_hex(32),
    'encryption_salt': secrets.token_hex(16),
    'api_protection_key': secrets.token_hex(32)
}

with open('secure_config.json', 'w') as f:
    json.dump({'config': config, 'keys': keys}, f, indent=2)

os.chmod('secure_config.json', 0o600)
print('✅ secure_config.json создан')
"
fi

# Остановка и удаление старых контейнеров
echo -e "${YELLOW}🛑 Остановка старых контейнеров...${NC}"
docker-compose down --remove-orphans 2>/dev/null || true

# Сборка образа
echo -e "${YELLOW}🔨 Сборка Docker образа...${NC}"
docker-compose build --no-cache

# Запуск контейнеров
echo -e "${YELLOW}🚀 Запуск контейнеров...${NC}"
docker-compose up -d

# Проверка статуса
echo -e "${YELLOW}⏳ Ожидание запуска...${NC}"
sleep 5

if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Бот успешно запущен в Docker!${NC}"
    echo -e "${GREEN}📊 Статус:${NC}"
    docker-compose ps
    
    echo -e "\n${GREEN}📋 Логи (последние 10 строк):${NC}"
    docker-compose logs --tail=10
    
    echo -e "\n${GREEN}🔍 Полезные команды:${NC}"
    echo -e "  • Просмотр логов: ${YELLOW}docker-compose logs -f${NC}"
    echo -e "  • Остановка бота: ${YELLOW}docker-compose down${NC}"
    echo -e "  • Перезапуск: ${YELLOW}docker-compose restart${NC}"
    echo -e "  • Вход в контейнер: ${YELLOW}docker exec -it ultra-secure-bot /bin/bash${NC}"
    
    echo -e "\n${GREEN}📁 Данные сохраняются в:${NC}"
    echo -e "  • База данных: ${YELLOW}./secure_data/secure_bot.db${NC}"
    echo -e "  • Логи: ${YELLOW}./logs/${NC}"
    echo -e "  • Бекапы: ${YELLOW}./secure_data/backups/${NC}"
else
    echo -e "${RED}❌ Ошибка запуска!${NC}"
    docker-compose logs
    exit 1
fi