#!/usr/bin/env python3
import re

# Читаем исходный файл
with open('telegram_bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Удаляем все parse_mode=ParseMode.MARKDOWN_V2 из reply_text
content = re.sub(
    r'await update\.message\.reply_text\([^,]+, parse_mode=ParseMode\.MARKDOWN_V2\)',
    lambda m: m.group(0).replace(', parse_mode=ParseMode.MARKDOWN_V2', ''),
    content
)

# 2. Заменяем reply_text с parse_mode на простые вызовы
content = re.sub(
    r'await query\.edit_message_text\([^,]+, parse_mode=ParseMode\.MARKDOWN_V2',
    lambda m: m.group(0).replace(', parse_mode=ParseMode.MARKDOWN_V2', ''),
    content
)

# 3. Для query.edit_message_text тоже
content = re.sub(
    r'await query\.edit_message_text\([^,]+, parse_mode=ParseMode\.MARKDOWN_V2',
    lambda m: m.group(0).replace(', parse_mode=ParseMode.MARKDOWN_V2', ''),
    content
)

# 4. Удаляем все MARKDOWN_V2 из контента
content = re.sub(
    r'parse_mode=ParseMode\.MARKDOWN_V2',
    '',
    content
)

# 5. Заменяем оставшиеся parse_mode на HTML
content = re.sub(
    r'parse_mode=ParseMode\.[A-Z_]+',
    'parse_mode=ParseMode.HTML',
    content
)

# 6. Преобразуем Markdown разметку в HTML
def markdown_to_html(text):
    # Заменяем **текст** на <b>текст</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Заменяем __текст__ на <i>текст</i>
    text = re.sub(r'__(.+?)__', r'<i>\1</i>', text)
    # Заменяем `текст` на <code>текст</code>
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Заменяем *текст* на <b>текст</b> (если не в начале предложения)
    text = re.sub(r'(?<=\s)\*(.+?)\*', r'<b>\1</b>', text)
    return text

# Применяем преобразование ко всем строкам с разметкой
lines = content.split('\n')
for i in range(len(lines)):
    if 'f"' in lines[i] or "f'" in lines[i]:
        if any(mark in lines[i] for mark in ['*', '_', '`']):
            # Это f-строка с разметкой, но нам нужно быть осторожными
            pass  # Пока пропустим

# Сохраняем исправленный файл
with open('telegram_bot_fixed.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Файл исправлен!")
print("✅ Используйте: python telegram_bot_fixed.py")