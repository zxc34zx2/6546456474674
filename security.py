#!/usr/bin/env python3
# 🔒 Модуль безопасности

from config import ADMIN_IDS, DEFAULT_SPAM_COOLDOWN, PREMIUM_SPAM_COOLDOWN
from datetime import datetime
from typing import Dict, Optional

def check_spam_cooldown(user_id: int, db, user_cooldowns: Dict[int, datetime]) -> Optional[str]:
    """Проверить спам-режим"""
    now = datetime.now()
    
    if user_id in user_cooldowns:
        last_time = user_cooldowns[user_id]
        
        # Определяем время ожидания
        if db.is_user_premium(user_id) or is_admin(user_id):
            cooldown = PREMIUM_SPAM_COOLDOWN
        else:
            cooldown = DEFAULT_SPAM_COOLDOWN
        
        time_diff = (now - last_time).total_seconds()
        
        if time_diff < cooldown:
            wait_time = int(cooldown - time_diff)
            return f"⏳ Подождите {wait_time} секунд перед отправкой следующего сообщения."
    
    user_cooldowns[user_id] = now
    return None

def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь админом"""
    return user_id in ADMIN_IDS

# Для обратной совместимости
def validate_admin_session(user_id: int, session_token: str) -> bool:
    """Валидация админ сессии"""
    return user_id in ADMIN_IDS and session_token.startswith(f"admin_{user_id}_")