#!/usr/bin/env python3
# 🗄️ Работа с базой данных SQLite

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from config import PREMIUM_EMOJIS

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self):
        self.db_file = 'anonymous_bot.db'
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Создание таблиц с правильной структурой"""
        cursor = self.conn.cursor()
        
        # Таблица users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_banned INTEGER DEFAULT 0,
                registration_date TEXT,
                is_premium INTEGER DEFAULT 0,
                custom_emoji TEXT DEFAULT "📨",
                premium_until TEXT DEFAULT NULL,
                emoji_type TEXT DEFAULT "standard",
                payment_history TEXT DEFAULT NULL,
                emoji_unique INTEGER DEFAULT 1,
                emoji_lock INTEGER DEFAULT 0,
                nickname TEXT DEFAULT NULL,
                message_count INTEGER DEFAULT 0,
                edit_count INTEGER DEFAULT 0,
                delete_count INTEGER DEFAULT 0,
                last_activity TEXT DEFAULT NULL
            )
        ''')
        
        # Таблица emoji_reservations (для уникальных эмодзи)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emoji_reservations (
                emoji TEXT PRIMARY KEY,
                user_id INTEGER UNIQUE,
                reserved_at TEXT,
                is_premium INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица messages с ВСЕМИ нужными колонками
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_message_id INTEGER NOT NULL,
                text TEXT,
                timestamp TEXT NOT NULL,
                reply_to INTEGER DEFAULT NULL,
                is_reply INTEGER DEFAULT 0,
                emoji_used TEXT,
                is_edited INTEGER DEFAULT 0,
                is_deleted INTEGER DEFAULT 0,
                edit_count INTEGER DEFAULT 0,
                last_edit_time TEXT
            )
        ''')
        
        # Таблица replies
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS replies (
                reply_id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_message_id INTEGER,
                reply_message_id INTEGER,
                user_id INTEGER,
                timestamp TEXT
            )
        ''')
        
        # Таблица payments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                currency TEXT DEFAULT "XTR",
                status TEXT DEFAULT "pending",
                timestamp TEXT NOT NULL,
                product TEXT,
                payload TEXT
            )
        ''')
        
        # Таблица used_emojis (история использованных эмодзи)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS used_emojis (
                emoji TEXT PRIMARY KEY,
                user_id INTEGER,
                last_used TEXT,
                use_count INTEGER DEFAULT 1
            )
        ''')
        
        # Таблица message_edits (история редактирований)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_edits (
                edit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                old_text TEXT,
                new_text TEXT,
                user_id INTEGER,
                edit_time TEXT,
                FOREIGN KEY (message_id) REFERENCES messages(channel_message_id)
            )
        ''')
        
        self.conn.commit()
        logger.info("✅ База данных создана/проверена")
    
    def reset_database(self):
        """Пересоздать базу данных"""
        cursor = self.conn.cursor()
        
        tables = ['users', 'emoji_reservations', 'messages', 'replies', 'payments', 'used_emojis', 'message_edits']
        for table in tables:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table}')
            except:
                pass
        
        self.conn.commit()
        self.create_tables()
        logger.info("🔄 База данных пересоздана")
    
    # ===================== USER MANAGEMENT =====================
    
    def register_user(self, user_id: int, username: str, first_name: str, last_name: str):
        """Регистрация нового пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        
        if cursor.fetchone():
            cursor.execute('''
                UPDATE users 
                SET username = ?, first_name = ?, last_name = ?, last_activity = ?
                WHERE user_id = ?
            ''', (username, first_name, last_name, datetime.now().isoformat(), user_id))
        else:
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, first_name, last_name, registration_date, custom_emoji, emoji_type, last_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, datetime.now().isoformat(), "📨", "standard", datetime.now().isoformat()))
        
        self.conn.commit()
    
    def get_user_info(self, user_id: int) -> Optional[tuple]:
        """Получить информацию о пользователе"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    
    def is_user_premium(self, user_id: int) -> bool:
        """Проверить премиум статус"""
        user = self.get_user_info(user_id)
        if not user:
            return False
        
        # Проверка срока действия премиума
        if user[8]:  # premium_until
            try:
                premium_until = datetime.fromisoformat(user[8])
                if datetime.now() > premium_until:
                    cursor = self.conn.cursor()
                    cursor.execute('''
                        UPDATE users 
                        SET is_premium = 0, premium_until = NULL 
                        WHERE user_id = ?
                    ''', (user_id,))
                    self.conn.commit()
                    
                    # Освобождаем зарезервированный эмодзи
                    cursor.execute('DELETE FROM emoji_reservations WHERE user_id = ?', (user_id,))
                    self.conn.commit()
                    return False
            except:
                pass
        
        return user[6] == 1  # is_premium поле
    
    def get_user_emoji(self, user_id: int) -> str:
        """Получить эмодзи пользователя"""
        user = self.get_user_info(user_id)
        if not user:
            return "📨"
        
        return user[7] if user[7] else "📨"
    
    def is_user_banned(self, user_id: int) -> bool:
        """Проверить, забанен ли пользователь"""
        user = self.get_user_info(user_id)
        if not user:
            return False
        return user[4] == 1
    
    # ===================== MESSAGE MANAGEMENT =====================
    
    def log_message(self, user_id: int, channel_message_id: int, text: str, reply_to: int = None, emoji_used: str = None):
        """Сохранить сообщение в базе"""
        cursor = self.conn.cursor()
        is_reply = 1 if reply_to is not None else 0
        timestamp = datetime.now().isoformat()
        
        try:
            cursor.execute('''
                INSERT INTO messages 
                (user_id, channel_message_id, text, timestamp, reply_to, is_reply, emoji_used, is_edited, is_deleted, edit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0)
            ''', (user_id, channel_message_id, text or '', timestamp, reply_to, is_reply, emoji_used))
            
            cursor.execute('UPDATE users SET message_count = message_count + 1, last_activity = ? WHERE user_id = ?', 
                          (timestamp, user_id))
            
            self.conn.commit()
            
            if reply_to is not None:
                cursor.execute('''
                    INSERT INTO replies (original_message_id, reply_message_id, user_id, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (reply_to, channel_message_id, user_id, timestamp))
                self.conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения сообщения: {e}")
            self.conn.rollback()
            raise
    
    def get_message_owner(self, message_id: int) -> Optional[int]:
        """Получить ID владельца сообщения"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM messages WHERE channel_message_id = ?', (message_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def is_message_owner(self, user_id: int, message_id: int) -> bool:
        """Проверить владельца сообщения"""
        owner_id = self.get_message_owner(message_id)
        return owner_id == user_id
    
    def get_message_info(self, message_id: int) -> Optional[tuple]:
        """Получить информацию о сообщении"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM messages WHERE channel_message_id = ?', (message_id,))
        return cursor.fetchone()
    
    def edit_message(self, user_id: int, message_id: int, new_text: str) -> bool:
        """Редактировать сообщение"""
        cursor = self.conn.cursor()
        
        try:
            if not self.is_message_owner(user_id, message_id):
                return False
            
            cursor.execute('SELECT text FROM messages WHERE channel_message_id = ?', (message_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            old_text = result[0]
            if old_text == new_text:
                return True
            
            # Сохраняем историю редактирования
            cursor.execute('''
                INSERT INTO message_edits (message_id, old_text, new_text, user_id, edit_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (message_id, old_text, new_text, user_id, datetime.now().isoformat()))
            
            # Обновляем сообщение
            cursor.execute('''
                UPDATE messages 
                SET text = ?, is_edited = 1, edit_count = edit_count + 1, last_edit_time = ?
                WHERE channel_message_id = ?
            ''', (new_text, datetime.now().isoformat(), message_id))
            
            cursor.execute('UPDATE users SET edit_count = edit_count + 1, last_activity = ? WHERE user_id = ?', 
                          (datetime.now().isoformat(), user_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка редактирования: {e}")
            self.conn.rollback()
            return False
    
    def delete_message(self, user_id: int, message_id: int) -> bool:
        """Удалить сообщение"""
        cursor = self.conn.cursor()
        
        try:
            if not self.is_message_owner(user_id, message_id):
                return False
            
            cursor.execute('''
                UPDATE messages 
                SET is_deleted = 1 
                WHERE channel_message_id = ?
            ''', (message_id,))
            
            cursor.execute('UPDATE users SET delete_count = delete_count + 1, last_activity = ? WHERE user_id = ?', 
                          (datetime.now().isoformat(), user_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления: {e}")
            self.conn.rollback()
            return False
    
    # ===================== PREMIUM MANAGEMENT =====================
    
    def set_user_premium(self, user_id: int, months: int = 1, emoji_type: str = "premium"):
        """Активировать премиум"""
        cursor = self.conn.cursor()
        premium_until = datetime.now() + timedelta(days=30 * months)
        cursor.execute('''
            UPDATE users 
            SET is_premium = 1, premium_until = ?, emoji_type = ?, emoji_unique = 1
            WHERE user_id = ?
        ''', (premium_until.isoformat(), emoji_type, user_id))
        self.conn.commit()
    
    def add_premium_days(self, user_id: int, days: int):
        """Добавить дни премиума"""
        cursor = self.conn.cursor()
        user = self.get_user_info(user_id)
        
        if user and user[8]:
            try:
                current_until = datetime.fromisoformat(user[8])
                new_until = current_until + timedelta(days=days)
            except:
                new_until = datetime.now() + timedelta(days=days)
        else:
            new_until = datetime.now() + timedelta(days=days)
        
        cursor.execute('''
            UPDATE users 
            SET is_premium = 1, premium_until = ?, emoji_type = "premium"
            WHERE user_id = ?
        ''', (new_until.isoformat(), user_id))
        self.conn.commit()
    
    # ===================== EMOJI MANAGEMENT =====================
    
    def get_reserved_emoji_for_user(self, user_id: int) -> Optional[str]:
        """Получить зарезервированный эмодзи пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT emoji FROM emoji_reservations WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def get_reserved_emoji_owner(self, emoji: str) -> Optional[int]:
        """Получить владельца зарезервированного эмодзи"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM emoji_reservations WHERE emoji = ?', (emoji,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def set_user_emoji_with_reservation(self, user_id: int, emoji: str, emoji_type: str = None) -> bool:
        """Установить эмодзи с закреплением"""
        cursor = self.conn.cursor()
        
        if emoji_type is None:
            emoji_type = "premium" if emoji in PREMIUM_EMOJIS else "standard"
        
        # Для не-премиум просто устанавливаем эмодзи
        if not self.is_user_premium(user_id):
            cursor.execute('UPDATE users SET custom_emoji = ?, emoji_type = ? WHERE user_id = ?', 
                          (emoji, emoji_type, user_id))
            self.conn.commit()
            return True
        
        # Для премиум пользователей - закрепляем эмодзи
        cursor.execute('DELETE FROM emoji_reservations WHERE user_id = ?', (user_id,))
        
        # Проверяем, занят ли новый эмодзи
        cursor.execute('SELECT user_id FROM emoji_reservations WHERE emoji = ?', (emoji,))
        if cursor.fetchone():
            return False
        
        # Резервируем новый эмодзи
        cursor.execute('''
            INSERT OR REPLACE INTO emoji_reservations (emoji, user_id, reserved_at, is_premium)
            VALUES (?, ?, ?, 1)
        ''', (emoji, user_id, datetime.now().isoformat()))
        
        cursor.execute('UPDATE users SET custom_emoji = ?, emoji_type = ? WHERE user_id = ?', 
                      (emoji, emoji_type, user_id))
        
        self.conn.commit()
        return True
    
    def get_available_emojis(self) -> List[str]:
        """Получить список доступных эмодзи"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT emoji FROM emoji_reservations')
        reserved_emojis = {row[0] for row in cursor.fetchall()}
        
        available_emojis = [emoji for emoji in PREMIUM_EMOJIS if emoji not in reserved_emojis]
        return available_emojis
    
    def get_all_reserved_emojis(self) -> List[tuple]:
        """Получить все зарезервированные эмодзи"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT e.emoji, u.user_id, u.username, u.first_name, e.reserved_at
            FROM emoji_reservations e
            JOIN users u ON e.user_id = u.user_id
            ORDER BY e.reserved_at DESC
        ''')
        return cursor.fetchall()
    
    def free_emoji(self, emoji: str) -> bool:
        """Освободить эмодзи"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM emoji_reservations WHERE emoji = ?', (emoji,))
        affected = cursor.rowcount
        self.conn.commit()
        return affected > 0
    
    # ===================== ADMIN FUNCTIONS =====================
    
    def get_all_users(self, limit: int = 100) -> List[tuple]:
        """Получить всех пользователей"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, is_premium, registration_date, 
                   message_count, edit_count, delete_count, last_activity
            FROM users 
            ORDER BY registration_date DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def get_user_count(self) -> int:
        """Получить количество пользователей"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        return cursor.fetchone()[0]
    
    def get_premium_users_count(self) -> int:
        """Получить количество премиум пользователей"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_premium = 1')
        return cursor.fetchone()[0]
    
    def get_message_count(self) -> int:
        """Получить количество сообщений"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM messages')
        return cursor.fetchone()[0]
    
    def ban_user(self, user_id: int):
        """Забанить пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def unban_user(self, user_id: int):
        """Разбанить пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    # ===================== VALIDATION =====================
    
    def validate_emoji(self, emoji: str) -> bool:
        """Валидация эмодзи"""
        if not emoji or len(emoji.strip()) == 0:
            return False
        
        if len(emoji) > 4:
            return False
        
        return True