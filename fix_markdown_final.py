#!/usr/bin/env python3
import re
import os
import sys

def fix_all_markdown():
    print("🔧 Исправление всех проблем с MarkdownV2 в файле telegram_bot.py")
    
    # Получаем текущую директорию
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"📁 Текущая папка: {current_dir}")
    
    # Проверяем, существует ли файл telegram_bot.py
    telegram_bot_path = os.path.join(current_dir, 'telegram_bot.py')
    if not os.path.exists(telegram_bot_path):
        print(f"❌ Файл не найден: {telegram_bot_path}")
        
        # Показываем файлы в текущей директории
        print("\n📂 Содержимое текущей папки:")
        for file in os.listdir(current_dir):
            print(f"  - {file}")
        
        # Ищем файл с похожим именем
        for file in os.listdir(current_dir):
            if 'telegram' in file.lower() and file.endswith('.py'):
                print(f"\n✅ Возможно, ваш файл называется: {file}")
                telegram_bot_path = os.path.join(current_dir, file)
                break
        
        if not os.path.exists(telegram_bot_path):
            print("\n❌ Не могу найти файл telegram_bot.py")
            print("✅ Убедитесь, что скрипт находится в той же папке, что и файл бота")
            return
    
    print(f"✅ Найден файл: {telegram_bot_path}")
    
    with open(telegram_bot_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📏 Размер файла: {len(content)} символов")
    
    # 1. Заменяем ВСЕ MarkdownV2 на HTML
    count_md = content.count('parse_mode=ParseMode.MARKDOWN_V2')
    content = content.replace('parse_mode=ParseMode.MARKDOWN_V2', 'parse_mode=ParseMode.HTML')
    print(f"✅ Заменено MarkdownV2: {count_md}")
    
    # 2. Также заменяем обычный Markdown
    count_md_simple = content.count('parse_mode=ParseMode.MARKDOWN')
    content = content.replace('parse_mode=ParseMode.MARKDOWN', 'parse_mode=ParseMode.HTML')
    print(f"✅ Заменено Markdown: {count_md_simple}")
    
    # 3. Преобразуем разметку в HTML
    # **текст** → <b>текст</b>
    content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
    print(f"✅ Преобразовано **жирный** тегов")
    
    # __текст__ → <i>текст</i>
    content = re.sub(r'__(.+?)__', r'<i>\1</i>', content)
    print(f"✅ Преобразовано __курсив__ тегов")
    
    # `текст` → <code>текст</code>
    content = re.sub(r'`(.+?)`', r'<code>\1</code>', content)
    print(f"✅ Преобразовано `код` тегов")
    
    # 4. Убираем экранирование (в HTML оно не нужно)
    escape_pairs = [
        ('\\\\-', '-'),
        ('\\\\.', '.'),
        ('\\\\!', '!'),
        ('\\\\:', ':'),
        ('\\\\(', '('),
        ('\\\\)', ')'),
        ('\\\\[', '['),
        ('\\\\]', ']'),
        ('\\\\`', '`'),
        ('\\\\*', '*'),
        ('\\\\_', '_'),
        ('\\\\~', '~'),
        ('\\\\>', '>'),
        ('\\\\#', '#'),
        ('\\\\+', '+'),
        ('\\\\=', '='),
        ('\\\\|', '|'),
        ('\\\\{', '{'),
        ('\\\\}', '}'),
    ]
    
    for escaped, normal in escape_pairs:
        count = content.count(escaped)
        if count > 0:
            content = content.replace(escaped, normal)
            print(f"✅ Убрано экранирование {escaped}: {count}")
    
    # 5. Сохраняем исправленный файл
    output_path = os.path.join(current_dir, 'telegram_bot_fixed.py')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Размер нового файла: {len(content)} символов")
    print(f"✅ Исправленный файл сохранен как: {output_path}")
    
    # 6. Проверяем, есть ли еще проблемы
    if 'parse_mode=ParseMode.MARKDOWN_V2' in content:
        print("⚠️ ВНИМАНИЕ: В файле все еще есть MARKDOWN_V2!")
    
    print("\n" + "="*50)
    print("✅ Файл успешно исправлен!")
    print("\n📋 Что делать дальше:")
    print("1. Остановите бота (Ctrl+C в терминале)")
    print(f"2. Переименуйте файлы командой:")
    print(f"   rename telegram_bot.py telegram_bot_backup.py")
    print(f"   rename telegram_bot_fixed.py telegram_bot.py")
    print("3. Запустите бота:")
    print(f"   python telegram_bot.py")
    print("="*50)

if __name__ == "__main__":
    fix_all_markdown()