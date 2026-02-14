#!/usr/bin/env python3
# Быстрое исправление MarkdownV2 ошибок

import re

def fix_telegram_bot():
    with open('telegram_bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Исправить восклицательные знаки в MarkdownV2
    content = content.replace("*!*", "*\\!*")
    content = content.replace("!*", "\\!*")
    content = re.sub(r'(\*.*?)!(\s)', r'\1\\!\2', content)
    
    # 2. Исправить точки в MarkdownV2
    content = re.sub(r'(\*.*?)\.(\s|$)', r'\1\\.\2', content)
    
    # 3. Исправить дефисы после звездочек
    content = re.sub(r'(\*.*?)-', r'\1\\-', content)
    
    # 4. Исправить квадратные скобки
    content = content.replace("[команда]", "\\[команда\\]")
    content = content.replace("[параметры]", "\\[параметры\\]")
    content = content.replace("[ID]", "\\[ID\\]")
    content = content.replace("[текст]", "\\[текст\\]")
    
    # 5. Исправить круглые скобки с ID
    content = re.sub(r'\(ID:(\d+)\)', r'\\(ID:\1\\)', content)
    
    with open('telegram_bot_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Создан исправленный файл: telegram_bot_fixed.py")
    print("✅ Переименуйте его обратно: mv telegram_bot_fixed.py telegram_bot.py")

if __name__ == "__main__":
    fix_telegram_bot()