#!/usr/bin/env python3
# 🤖 Анонимный бот с уникальными эмодзи
# 🚀 Основной файл запуска

import logging
import sys
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Импорт модулей
from config import BOT_TOKEN, CHANNEL_ID, ADMIN_IDS
from database import Database
from telegram_bot import TelegramBot

def main():
    """Основная функция запуска бота"""
    try:
        print("=" * 60)
        print("🤖 АНОНИМНЫЙ БОТ")
        print("=" * 60)
        print("📢 Канал: @anonalmet")
        print("💰 Стоимость премиума: 25 Stars")
        print("=" * 60)
        print("🔄 Инициализация...")
        
        # Инициализация базы данных
        db = Database()
        
        print("✅ Система готова")
        print("🚀 Запуск бота...")
        print("=" * 60)
        
        # Запуск бота
        bot = TelegramBot(db)
        bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске: {e}")
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()