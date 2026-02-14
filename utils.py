#!/usr/bin/env python3
# 🛠️ Утилиты для бота

import re
import hashlib
import hmac
import secrets
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from config import ADMIN_IDS, DEFAULT_SPAM_COOLDOWN, PREMIUM_SPAM_COOLDOWN

def escape_markdown_v2(text: str) -> str:
    """Экранировать специальные символы MarkdownV2"""
    if not text:
        return text
    
    # Все символы, которые нужно экранировать в MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Экранируем каждый символ
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def escape_markdown(text: str) -> str:
    """Совместимая функция экранирования (алиас для обратной совместимости)"""
    return escape_markdown_v2(text)

def safe_markdown_text(text: str) -> str:
    """Безопасный текст для MarkdownV2 с проверкой экранирования"""
    escaped = escape_markdown_v2(text)
    
    # Дополнительная проверка на неэкранированные символы
    dangerous_chars = r'[_*\[\]()~`>#+\-=|{}.!]'
    matches = re.findall(dangerous_chars, escaped)
    
    for match in matches:
        if not escaped.startswith(f'\\{match}'):
            escaped = escaped.replace(match, f'\\{match}')
    
    return escaped

def validate_emoji(emoji: str) -> bool:
    """Валидация эмодзи"""
    if not emoji or len(emoji.strip()) == 0:
        return False
    
    if len(emoji) > 4:
        return False
    
    return True

def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь админом"""
    return user_id in ADMIN_IDS

def sanitize_text(text: str, max_length: int = 4096) -> str:
    """Очистка текста"""
    if not text:
        return ""
    
    # Удаляем лишние пробелы
    text = ' '.join(text.split())
    
    # Обрезаем до максимальной длины
    if len(text) > max_length:
        text = text[:max_length]
    
    return text

def validate_message_text(text: str) -> tuple[bool, str]:
    """Валидация текста сообщения"""
    if not text or len(text.strip()) == 0:
        return False, "❌ Текст сообщения не может быть пустым"
    
    if len(text) > 4096:
        return False, "❌ Текст сообщения слишком длинный"
    
    return True, ""

# Шифрование функций
SECRET_KEY = "anon_bot_secure_key_2024_v2"

def encrypt_admin_command(command: str, data: Dict[str, Any]) -> str:
    """Шифрование админ команды"""
    try:
        data['timestamp'] = datetime.now().isoformat()
        data['command'] = command
        
        json_data = json.dumps(data, separators=(',', ':'))
        salt = secrets.token_hex(8)
        data_to_encrypt = f"{salt}:{json_data}"
        
        encoded = base64.b64encode(data_to_encrypt.encode()).decode()
        
        hmac_digest = hmac.new(
            SECRET_KEY.encode(),
            encoded.encode(),
            hashlib.sha256
        ).hexdigest()[:8]
        
        return f"{encoded}:{hmac_digest}"
        
    except Exception:
        return ""

def decrypt_admin_command(encrypted_data: str) -> Optional[Dict[str, Any]]:
    """Дешифрование админ команды"""
    try:
        if ':' not in encrypted_data:
            return None
        
        encoded, received_hmac = encrypted_data.rsplit(':', 1)
        
        expected_hmac = hmac.new(
            SECRET_KEY.encode(),
            encoded.encode(),
            hashlib.sha256
        ).hexdigest()[:8]
        
        if received_hmac != expected_hmac:
            return None
        
        decoded = base64.b64decode(encoded.encode()).decode()
        salt, json_data = decoded.split(':', 1)
        data = json.loads(json_data)
        
        timestamp = datetime.fromisoformat(data['timestamp'])
        if datetime.now() - timestamp > timedelta(minutes=5):
            return None
        
        return data
        
    except Exception:
        return None

def generate_admin_token(user_id: int) -> str:
    """Генерация токена для админа"""
    if user_id not in ADMIN_IDS:
        return ""
    
    data = {
        'user_id': user_id,
        'timestamp': datetime.now().isoformat(),
        'random': secrets.token_hex(16)
    }
    
    json_data = json.dumps(data, separators=(',', ':'))
    encrypted = base64.b64encode(json_data.encode()).decode()
    
    return f"admin_{user_id}_{encrypted[:16]}"