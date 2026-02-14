#!/usr/bin/env python3
import os

def fix_missing_methods():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    telegram_bot_path = os.path.join(current_dir, 'telegram_bot.py')
    
    with open(telegram_bot_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, какие методы определены
    methods_defined = []
    for line in content.split('\n'):
        if 'async def _admin_' in line:
            method_name = line.split('async def ')[1].split('(')[0]
            methods_defined.append(method_name)
    
    print(f"✅ Найдено методов _admin_*: {len(methods_defined)}")
    for method in methods_defined:
        print(f"  - {method}")
    
    # Ищем словарь encrypted_commands
    import re
    pattern = r'self\.encrypted_commands = \{([^}]+)\}'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        commands_dict = match.group(1)
        print(f"\n📋 Команды в словаре:")
        
        # Извлекаем команды и их обработчики
        command_pattern = r'\"([a-z0-9]+)\"\s*:\s*self\.(\w+)'
        commands = re.findall(command_pattern, commands_dict)
        
        for cmd, handler in commands:
            print(f"  - {cmd} -> {handler}")
            
            # Проверяем, определен ли метод
            if handler not in methods_defined:
                print(f"    ❌ Метод {handler} НЕ НАЙДЕН!")
    
    # Проверяем, есть ли все методы
    required_methods = [
        '_admin_stats_encrypted',
        '_admin_users_encrypted', 
        '_admin_messages_encrypted',
        '_admin_ban_encrypted',
        '_admin_unban_encrypted',
        '_admin_premium_encrypted',
        '_admin_emoji_list_encrypted',
        '_admin_free_emoji_encrypted',
        '_admin_broadcast_encrypted',
        '_admin_reset_encrypted',
        '_admin_restart_encrypted',
        '_admin_debug_encrypted',
        '_admin_logs_encrypted'
    ]
    
    print(f"\n🔍 Проверка необходимых методов:")
    missing_methods = []
    for method in required_methods:
        if method not in methods_defined:
            print(f"  ❌ {method} - отсутствует")
            missing_methods.append(method)
        else:
            print(f"  ✅ {method} - найден")
    
    if missing_methods:
        print(f"\n⚠️ Отсутствуют методы: {len(missing_methods)}")
        
        # Создаем заглушки для отсутствующих методов
        stubs = "\n\n"
        for method in missing_methods:
            stubs += f"""    async def {method}(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        \"\"\"Заглушка для {method}\"\"\"
        return f"Метод {method} еще не реализован"
    
"""
        
        # Вставляем заглушки перед концом класса
        if '    # ===================== ОБРАБОТКА КНОПОК =====================' in content:
            insert_point = content.find('    # ===================== ОБРАБОТКА КНОПОК =====================')
            new_content = content[:insert_point] + stubs + content[insert_point:]
            
            output_path = os.path.join(current_dir, 'telegram_bot_with_stubs.py')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"\n✅ Создан файл с заглушками: {output_path}")
            print("✅ Запустите: python telegram_bot_with_stubs.py")
    else:
        print("\n✅ Все методы найдены!")

if __name__ == "__main__":
    fix_missing_methods()