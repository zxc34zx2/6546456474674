#!/usr/bin/env python3
# 🤖 Основной класс Telegram бота с шифрованными админ командами

import logging
import asyncio
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple, Any
from functools import wraps

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, PreCheckoutQueryHandler
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError

from config import (
    BOT_TOKEN, CHANNEL_ID, ADMIN_IDS, PREMIUM_PRICE,
    DEFAULT_SPAM_COOLDOWN, PREMIUM_SPAM_COOLDOWN,
    PREMIUM_EMOJIS, MAX_MESSAGE_LENGTH
)
from database import Database

from utils import (
    escape_markdown, 
    validate_emoji,
    encrypt_admin_command, 
    decrypt_admin_command,
    generate_admin_token
)
from security import (
    check_spam_cooldown, 
    is_admin, 
    validate_admin_session
)

logger = logging.getLogger(<i>name</i>)

class TelegramBot:
    """Основной класс Telegram бота с шифрованными админ командами"""
    
    def <i>init</i>(self, db: Database):
        self.db = db
        self.app = None
        
        # Временные хранилища
        self.user_cooldowns: Dict[int, datetime] = {}
        self.pending_replies: Dict[int, tuple] = {}
        self.pending_edits: Dict[int, tuple] = {}
        
        # Хранилище сессий
        self.admin_sessions: Dict[int, dict] = {}
        
        # Шифрованные команды админа
        self.encrypted_commands = {
            # Статистика
            "a1b2c3d4": self._admin_stats_encrypted,
            "e5f6g7h8": self._admin_users_encrypted,
            "i9j0k1l2": self._admin_messages_encrypted,
            
            # Управление пользователями
            "m3n4o5p6": self._admin_ban_encrypted,
            "q7r8s9t0": self._admin_unban_encrypted,
            "u1v2w3x4": self._admin_premium_encrypted,
            
            # Управление эмодзи
            "y5z6a7b8": self._admin_emoji_list_encrypted,
            "c9d0e1f2": self._admin_free_emoji_encrypted,
            
            # Системные команды
            "g3h4i5j6": self._admin_broadcast_encrypted,
            "k7l8m9n0": self._admin_reset_encrypted,
            "o1p2q3r4": self._admin_restart_encrypted,
            
            # Отладочные команды
            "s5t6u7v8": self._admin_debug_encrypted,
            "w9x0y1z2": self._admin_logs_encrypted,
        }
    
    def run(self):
        """Запуск бота"""
        try:
            self.app = Application.builder().token(BOT_TOKEN).build()
            self._setup_handlers()
            
            print("✅ Бот запущен")
            print("🔐 Шифрованные админ команды активированы")
            print("🎨 Уникальные эмодзи доступны для премиума")
            print("💳 Оплата через Telegram Stars: /buy_premium")
            print("=" * 60)
            
            self.app.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            raise
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        
        # Основные команды
        self.app.add_handler(CommandHandler("start", self._start_command))
        
        # Команды пользователей
        self.app.add_handler(CommandHandler("help", self._help_command))
        self.app.add_handler(CommandHandler("premium", self._premium_command))
        self.app.add_handler(CommandHandler("myemoji", self._myemoji_command))
        self.app.add_handler(CommandHandler("availableemojis", self._availableemojis_command))
        
        # Эмодзи команды (только для премиум)
        self.app.add_handler(CommandHandler("emoji", self._emoji_command))
        self.app.add_handler(CommandHandler("myreservations", self._myreservations_command))
        
        # Команды редактирования/удаления (только для премиум)
        self.app.add_handler(CommandHandler("edit", self._edit_message_command))
        self.app.add_handler(CommandHandler("delete", self._delete_message_command))
        
        # Платежные команды
        self.app.add_handler(CommandHandler("buy_premium", self._buy_premium_command))
        
        # Шифрованные админ команды (пример: /as22f2ffj8)
        self.app.add_handler(CommandHandler("as22f2ffj8", self._encrypted_admin_command))
        self.app.add_handler(CommandHandler("b3g5h7j9k1", self._encrypted_admin_session))
        self.app.add_handler(CommandHandler("c4d6f8h0j2", self._encrypted_admin_status))
        
        # Обработчики платежей
        self.app.add_handler(PreCheckoutQueryHandler(self._pre_checkout_handler))
        self.app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self._successful_payment_handler))
        
        # Обработчики кнопок
        self.app.add_handler(CallbackQueryHandler(self._button_handler))
        
        # Обработчик всех сообщений
        self.app.add_handler(MessageHandler(
            filters.ChatType.PRIVATE & ~filters.COMMAND,
            self._handle_all_messages
        ))
    
    # ===================== ОСНОВНЫЕ КОМАНДЫ =====================
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        
        self.db.register_user(
            user.id, 
            user.username or "", 
            user.first_name or "", 
            user.last_name or ""
        )
        
        # ЛУЧШЕЕ РЕШЕНИЕ: используйте обычный текст без Markdown
        welcome_text = (
            "👋 Анонимный бот\n\n"
            "📢 Канал: @anonalmet\n"
            "💎 Премиум: /premium\n"
            "🛠️ Поддержка: @anonaltshelper\n\n"
            "Как использовать:\n"
            "1. Просто отправьте сообщение\n"
            "2. Все сообщения анонимны\n\n"
        )
        
        await update.message.reply_text(welcome_text)  # Без parse_mode
        
        # Для админов показываем секретную информацию
        if is_admin(user.id):
            admin_token = generate_admin_token(user.id)
            encrypted_help = encrypt_admin_command("help", {"user_id": user.id})
            
            # ИСПРАВЛЕНИЕ: обычный текст без разметки
            admin_text = (
                f"🔐 Админ доступ обнаружен\n\n"
                f"Ваш токен: {admin_token[:16]}...\n"
                f"Сессия: {encrypted_help[:20]}...\n\n"
                f"Шифрованные команды:\n"
                f"• /as22f2ffj8 [команда] - выполнить команду\n"
                f"• /b3g5h7j9k1 - создать сессию\n"
                f"• /c4d6f8h0j2 - статус системы\n\n"
                f"Доступно команд: {len(self.encrypted_commands)}"
            )
            
            await update.message.reply_text(admin_text)  # Без parse_mode!
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        # ИСПРАВЛЕНИЕ: используйте HTML или обычный текст
        help_text = (
            "<b>🤖 Помощь по командам</b>\n\n"
            "<b>Основные команды:</b>\n"
            "• /start - начать работу\n"
            "• /premium - информация о премиуме\n"
            "• /myemoji - мой текущий эмодзи\n\n"
            "<b>Для премиум пользователей:</b>\n"
            "• /emoji [эмодзи] - установить эмодзи\n"
            "• /availableemojis - доступные эмодзи\n"
            "• /edit [ID] - редактировать сообщение\n"
            "• /delete [ID] - удалить сообщение\n\n"
            "<b>Покупка премиума:</b>\n"
            "• /buy_premium - купить премиум\n\n"
            "📢 Канал: @anonalmet\n"
            "🛠️ Поддержка: @anonaltshelper"
        )
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    # ===================== PREMIUM КОМАНДЫ =====================
    
    async def _premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /premium"""
        user = update.effective_user
        
        is_premium = self.db.is_user_premium(user.id)
        
        if is_premium:
            user_emoji = self.db.get_user_emoji(user.id)
            reserved_emoji = self.db.get_reserved_emoji_for_user(user.id)
            
            # ИСПРАВЛЕНИЕ: используйте HTML
            text = (
                f"<b>✨ Anon Premium</b>\n\n"
                f"✅ Ваш премиум активен!\n"
                f"🎨 Текущий эмодзи: {user_emoji}\n"
                f"⏱️ Спам-режим: 🔓 ОТКЛЮЧЕН\n"
            )
            
            if reserved_emoji and reserved_emoji == user_emoji:
                text += f"🔒 Уникальный закрепленный эмодзи\n\n"
            elif reserved_emoji:
                text += f"\n⚠️ Внимание: Закреплен {reserved_emoji}, но используется {user_emoji}\n\n"
            else:
                text += f"\n⚠️ Эмодзи не закреплен\n\n"
            
            text += (
                f"<b>Преимущества:</b>\n"
                f"• Редактирование сообщений ✏️\n"
                f"• Удаление сообщений 🗑️\n"
                f"• Уникальный эмодзи 🔒\n"
                f"• {len(PREMIUM_EMOJIS)} премиум эмодзи ⭐\n"
                f"• 🔓 Отключение спам-режима\n\n"
                f"<b>Команды:</b>\n"
                f"<code>/emoji</code> - закрепить новый эмодзи\n"
                f"<code>/availableemojis</code> - доступные эмодзи\n"
                f"<code>/edit ID</code> - редактировать сообщение\n"
                f"<code>/delete ID</code> - удалить сообщение"
            )
            
        else:
            text = (
                f"<b>✨ Anon Premium</b>\n\n"
                f"<b>⭐ Получите расширенные функции!</b>\n\n"
                f"<b>Что входит в премиум:</b>\n"
                f"✅ Редактирование сообщений ✏️\n"
                f"✅ Удаление сообщений 🗑️\n"
                f"✅ Уникальный закрепленный эмодзи 🔒\n"
                f"✅ {len(PREMIUM_EMOJIS)} премиум эмодзи ⭐\n"
                f"✅ 🔓 Отключение спам-режима\n\n"
                f"<b>Отличие от обычных:</b>\n"
                f"👤 <b>Обычный:</b> ⏳ {DEFAULT_SPAM_COOLDOWN} сек ожидания\n"
                f"⭐ <b>Премиум:</b> 🔓 {PREMIUM_SPAM_COOLDOWN} сек\n\n"
                f"<b>Стоимость:</b>\n"
                f"1 месяц - {PREMIUM_PRICE} звезд Telegram ⭐\n\n"
                f"<b>Поддержка:</b> @anonaltshelper"
            )
            
            keyboard = [
                [InlineKeyboardButton(f"💰 Купить Premium ({PREMIUM_PRICE}⭐)", callback_data="buy_premium_stars")],
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text, 
                parse_mode=ParseMode.HTML, 
                reply_markup=reply_markup
            )
            return
        
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    async def _myemoji_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /myemoji"""
        user = update.effective_user
        
        current_emoji = self.db.get_user_emoji(user.id)
        is_premium = self.db.is_user_premium(user.id)
        reserved_emoji = self.db.get_reserved_emoji_for_user(user.id)
        
        if is_premium:
            text = (
                f"🎨 *Ваш эмодзи*\n\n"
                f"Текущий эмодзи: {current_emoji}\n"
                f"Статус: ✅ Premium активен\n"
                f"Спам-режим: 🔓 ОТКЛЮЧЕН\n"
            )
            
            if reserved_emoji:
                if reserved_emoji == current_emoji:
                    text += f"🔒 Эмодзи закреплен за вами\n\n"
                else:
                    text += f"⚠️ Закреплен другой эмодзи: {reserved_emoji}\n\n"
            else:
                text += f"⚠️ Эмодзи не закреплен\n\n"
            
            text += (
                f"*Изменить эмодзи:*\n"
                f"<code>/emoji [новый_эмодзи]</code>\n"
                f"*Пример:* <code>/emoji ✨</code>\n\n"
                f"*Посмотреть доступные:*\n"
                f"<code>/availableemojis</code>\n\n"
                f"*Редактирование/Удаление:*\n"
                f"<code>/edit ID</code> - редактировать\n"
                f"<code>/delete ID</code> - удалить"
            )
        else:
            text = (
                f"🎨 *Ваш эмодзи*\n\n"
                f"Текущий эмодзи: {current_emoji}\n"
                f"Статус: ❌ Premium не активен\n"
                f"Спам-режим: ⏳ {DEFAULT_SPAM_COOLDOWN} секунд\n\n"
                f"*Получить премиум:*\n"
                f"<code>/premium</code> - узнать о премиуме\n"
                f"<code>/buy_premium</code> - купить премиум за {PREMIUM_PRICE}⭐\n\n"
                f"*С премиумом вы сможете:*\n"
                f"• Редактировать и удалять сообщения ✏️\n"
                f"• Закрепить уникальный эмодзи 🔒\n"
                f"• Использовать премиум эмодзи ⭐\n"
                f"• 🔓 ОТКЛЮЧИТЬ спам-режим\n\n"
                f"*Поддержка:* @anonaltshelper"
            )
        
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    async def _availableemojis_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать доступные эмодзи"""
        user = update.effective_user
        
        if not self.db.is_user_premium(user.id):
            await update.message.reply_text(
                "❌ Эта функция доступна только для премиум пользователей.",
                parse_mode=ParseMode.HTML
            )
            return
        
        available_emojis = self.db.get_available_emojis()
        reserved_emojis = self.db.get_all_reserved_emojis()
        
        text = "📋 *Доступные эмодзи для закрепления*\n\n"
        
        if available_emojis:
            text += f"✅ *Свободно: {len(available_emojis)} эмодзи*\n\n"
            
            # Показываем доступные эмодзи группами
            for i in range(0, min(len(available_emojis), 50), 10):
                group = available_emojis[i:i+10]
                text += " ".join(group) + "\n"
            
            if len(available_emojis) > 50:
                text += f"\n... и еще {len(available_emojis) - 50} эмодзи\n"
            
            text += f"\nИспользуйте <code>/emoji [эмодзи]</code> чтобы закрепить\n"
            text += f"*Пример:* <code>/emoji {available_emojis[0] if available_emojis else '🔥'}</code>\n"
        else:
            text += "😔 *Все эмодзи заняты*\n\n"
            text += "Попробуйте позже или свяжитесь с поддержкой @anonaltshelper\n"
        
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    async def _emoji_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Установить эмодзи"""
        user = update.effective_user
        
        if not self.db.is_user_premium(user.id):
            await update.message.reply_text(
                "❌ Эта функция доступна только для премиум пользователей.\n\n"
                "Используйте /premium чтобы узнать больше.",
                parse_mode=ParseMode.HTML
            )
            return
        
        if not context.args:
            current_emoji = self.db.get_user_emoji(user.id)
            reserved_emoji = self.db.get_reserved_emoji_for_user(user.id)
            
            text = (
                f"🎨 *Смена эмодзи*\n\n"
                f"Текущий эмодзи: {current_emoji}\n"
            )
            
            if reserved_emoji:
                if reserved_emoji == current_emoji:
                    text += f"🔒 Зарезервирован за вами\n\n"
                else:
                    text += f"⚠️ Закреплен другой эмодзи: {reserved_emoji}\n\n"
            else:
                text += f"⚠️ Не зарезервирован\n\n"
            
            text += (
                f"*Использование:*\n"
                f"<code>/emoji [эмодзи]</code> - выбрать и закрепить эмодзи\n\n"
                f"*Примеры:*\n"
                f"<code>/emoji 🔥</code> - закрепить огонь\n"
                f"<code>/emoji ✨</code> - закрепить искры\n\n"
                f"*Посмотреть доступные:*\n"
                f"<code>/availableemojis</code>"
            )
            
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            return
        
        emoji = context.args[0]
        
        if not validate_emoji(emoji):
            await update.message.reply_text(
                "❌ Пожалуйста, используйте валидный эмодзи.\n"
                "*Например:* <code>/emoji 🔥</code> или <code>/emoji ✨</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Проверяем, не занят ли эмодзи
        reserved_owner = self.db.get_reserved_emoji_owner(emoji)
        if reserved_owner and reserved_owner != user.id:
            if is_admin(user.id):
                owner_info = self.db.get_user_info(reserved_owner)
                owner_name = f"@{owner_info[1]}" if owner_info and owner_info[1] else f"ID: {reserved_owner}"
                
                await update.message.reply_text(
                    f"🔒 *Только для админа:*\n\n"
                    f"❌ Эмодзи {emoji} уже закреплен за {escape_markdown(owner_name)}\n\n"
                    f"Если нужно, освободите его командой:\n"
                    f"<code>/freeemoji {emoji}</code>",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text(
                    f"❌ Этот эмодзи уже занят.\n\n"
                    f"Используйте <code>/availableemojis</code> чтобы увидеть свободные.",
                    parse_mode=ParseMode.HTML
                )
            return
        
        # Устанавливаем эмодзи
        success = self.db.set_user_emoji_with_reservation(user.id, emoji)
        
        if not success:
            await update.message.reply_text(
                "❌ Не удалось закрепить эмодзи. Попробуйте другой.",
                parse_mode=ParseMode.HTML
            )
            return
        
        type_text = "⭐ Премиум эмодзи" if emoji in PREMIUM_EMOJIS else "📱 Стандартный эмодзи"
        
        await update.message.reply_text(
            f"✅ Эмодзи успешно закреплен!\n\n"
            f"Новый эмодзи: {emoji}\n"
            f"Тип: {type_text}\n"
            f"Статус: 🔒 Уникальный закрепленный эмодзи\n\n"
            f"Теперь этот эмодзи закреплен только за вами!\n"
            f"Другие пользователи не смогут его использовать.",
            parse_mode=ParseMode.HTML
        )
    
    async def _myreservations_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Мои зарезервированные эмодзи"""
        user = update.effective_user
        
        if not self.db.is_user_premium(user.id):
            await update.message.reply_text(
                "❌ Эта функция доступна только для премиум пользователей.",
                parse_mode=ParseMode.HTML
            )
            return
        
        current_emoji = self.db.get_user_emoji(user.id)
        reserved_emoji = self.db.get_reserved_emoji_for_user(user.id)
        
        text = "🔒 *Мои зарезервированные эмодзи*\n\n"
        
        if reserved_emoji:
            text += f"✅ Текущий закрепленный эмодзи: {reserved_emoji}\n"
            
            if current_emoji == reserved_emoji:
                text += f"📝 Используется в сообщениях: Да\n"
            else:
                text += f"⚠️ Внимание: В настройках установлен другой эмодзи\n"
                text += f"📝 Текущий эмодзи: {current_emoji}\n"
            
            # Информация о статусе премиума
            user_info = self.db.get_user_info(user.id)
            if user_info and user_info[8]:
                try:
                    until_date = datetime.fromisoformat(user_info[8])
                    days_left = (until_date - datetime.now()).days
                    text += f"📅 Эмодзи закреплен до окончания премиума ({days_left} дней)\n"
                except:
                    pass
            
            text += f"\n*Для смены эмодзи:*\n"
            text += f"Используйте <code>/emoji [новый_эмодзи]</code>\n"
            text += f"Старый эмодзи будет освобожден автоматически.\n"
        else:
            text += f"⚠️ У вас нет закрепленных эмодзи\n\n"
            text += f"*Как закрепить:*\n"
            text += f"1. Используйте <code>/availableemojis</code>\n"
            text += f"2. Выберите понравившийся эмодзи\n"
            text += f"3. Используйте <code>/emoji [эмодзи]</code>\n\n"
            text += f"*Текущий эмодзи:* {current_emoji}\n"
            text += f"⚠️ Этот эмодзи не закреплен и могут использовать другие"
        
        text += f"\n*Преимущества закрепления:*\n"
        text += f"• Уникальность - эмодзи только ваш\n"
        text += f"• Узнаваемость - другие видят ваш уникальный стиль\n"
        text += f"• Эксклюзивность - доступно только премиум пользователям"
        
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    # ===================== РЕДАКТИРОВАНИЕ И УДАЛЕНИЕ =====================
    
    async def _edit_message_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Редактировать сообщение"""
        user = update.effective_user
        
        if not self.db.is_user_premium(user.id) and not is_admin(user.id):
            await update.message.reply_text(
                "❌ Эта функция доступна только для премиум пользователей.\n"
                "Используйте /premium для получения премиума.",
                parse_mode=ParseMode.HTML
            )
            return
        
        if not context.args:
            await update.message.reply_text(
                "✏️ *Редактирование сообщения*\n\n"
                "*Использование:*\n"
                "<code>/edit ID_сообщения</code> - начать редактирование\n\n"
                "*Для редактирования:*\n"
                "1. Найдите ID сообщения (отображается при отправке)\n"
                "2. Используйте /edit ID\n"
                "3. Отправьте новый текст\n\n"
                "*Пример:* <code>/edit 123</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        try:
            message_id = int(context.args[0])
            
            message_info = self.db.get_message_info(message_id)
            if not message_info:
                await update.message.reply_text("❌ Сообщение не найдено.")
                return
            
            if not self.db.is_message_owner(user.id, message_id) and not is_admin(user.id):
                await update.message.reply_text(
                    "❌ Вы не являетесь владельцем этого сообщения.\n"
                    "Можно редактировать только свои сообщения."
                )
                return
            
            if len(message_info) > 9 and message_info[9] == 1:
                await update.message.reply_text("❌ Сообщение было удалено.")
                return
            
            self.pending_edits[user.id] = (message_id, message_info[3])
            
            old_text_escaped = escape_markdown(message_info[3] or "")
            
            await update.message.reply_text(
                f"✏️ *Редактирование сообщения #{message_id}*\n\n"
                f"*Текущий текст:*\n"
                f"<code>`</code>\n{old_text_escaped}\n<code>`</code>\n\n"
                f"*Теперь отправьте новый текст:*",
                parse_mode=ParseMode.HTML
            )
            
        except ValueError:
            await update.message.reply_text("❌ Неверный формат ID сообщения.")
    
    async def _delete_message_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить сообщение"""
        user = update.effective_user
        
        if not self.db.is_user_premium(user.id) and not is_admin(user.id):
            await update.message.reply_text(
                "❌ Эта функция доступна только для премиум пользователей.\n"
                "Используйте /premium для получения премиума.",
                parse_mode=ParseMode.HTML
            )
            return
        
        if not context.args:
            await update.message.reply_text(
                "🗑️ *Удаление сообщения*\n\n"
                "*Использование:*\n"
                "<code>/delete ID_сообщения</code> - удалить сообщение\n\n"
                "*Для удаления:*\n"
                "1. Найдите ID сообщения (отображается при отправке)\n"
                "2. Используйте /delete ID\n"
                "3. Подтвердите удаление\n\n"
                "*Пример:* <code>/delete 123</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        try:
            message_id = int(context.args[0])
            
            message_info = self.db.get_message_info(message_id)
            if not message_info:
                await update.message.reply_text("❌ Сообщение не найдено.")
                return
            
            if not self.db.is_message_owner(user.id, message_id) and not is_admin(user.id):
                await update.message.reply_text(
                    "❌ Вы не являетесь владельцем этого сообщения.\n"
                    "Можно удалять только свои сообщения."
                )
                return
            
            if len(message_info) > 9 and message_info[9] == 1:
                await update.message.reply_text("❌ Сообщение уже удалено.")
                return
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Да, удалить", callback_data=f'delete_confirm_{message_id}'),
                    InlineKeyboardButton("❌ Отмена", callback_data=f'delete_cancel_{message_id}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_text = message_info[3] or ""
            message_preview = escape_markdown(message_text[:200])
            
            await update.message.reply_text(
                f"🗑️ *Подтверждение удаления*\n\n"
                f"Вы действительно хотите удалить сообщение #{message_id}\\?\n\n"
                f"*Текст сообщения:*\n"
                f"<code>`</code>\n{message_preview}{'...' if len(message_text) > 200 else ''}\n<code>`</code>\n\n"
                f"\\❗ *Внимание:* Это действие нельзя отменить!",
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            
        except ValueError:
            await update.message.reply_text("❌ Неверный формат ID сообщения.")
    
    # ===================== ПЛАТЕЖИ И ПРЕМИУМ =====================
    
    async def _buy_premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Купить премиум"""
        user = update.effective_user
        
        if self.db.is_user_premium(user.id):
            await update.message.reply_text(
                "✅ У вас уже есть активная премиум подписка!\n"
                "Используйте /myemoji чтобы посмотреть ваш текущий эмодзи.",
                parse_mode=ParseMode.HTML
            )
            return
        
        text = (
            f"✨ *Anon Premium - 1 месяц*\n\n"
            f"*Стоимость:* {PREMIUM_PRICE} звезд Telegram ⭐\n\n"
            f"*Включает:*\n"
            f"✅ Редактирование и удаление сообщений ✏️\n"
            f"✅ Уникальный закрепленный эмодзи 🔒\n"
            f"✅ Премиум эмодзи Telegram ⭐\n"
            f"✅ 🔓 Отключение спам-режима\n\n"
            f"*Особенности:*\n"
            f"• Редактируйте отправленные сообщения\n"
            f"• Удаляйте свои сообщения\n"
            f"• Закрепите уникальный эмодзи за собой\n"
            f"• Используйте премиум эмодзи\n"
            f"• Отправляйте сообщения без ожидания\n\n"
            f"*Поддержка:* @anonaltshelper"
        )
        
        keyboard = [
            [InlineKeyboardButton(f"💰 Купить за {PREMIUM_PRICE}⭐", callback_data="buy_premium_stars")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error in buy_premium: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже.",
                parse_mode=ParseMode.HTML
            )
    
    async def _pre_checkout_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик предварительной проверки платежа"""
        query = update.pre_checkout_query
        
        payload = query.invoice_payload
        if not payload.startswith("premium_1month_"):
            await query.answer(ok=False, error_message="Неверный тип товара")
            return
        
        try:
            user_id = int(payload.split("_")[-1])
            user = self.db.get_user_info(user_id)
            
            if not user:
                await query.answer(ok=False, error_message="Пользователь не найден")
                return
            
            if self.db.is_user_premium(user_id):
                await query.answer(ok=False, error_message="У вас уже есть активная подписка")
                return
            
            await query.answer(ok=True)
        except Exception as e:
            logger.error(f"Error in pre_checkout: {e}")
            await query.answer(ok=False, error_message="Произошла ошибка")
    
    async def _successful_payment_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик успешной оплаты"""
        user = update.effective_user
        payment = update.message.successful_payment
        
        try:
            self.db.set_user_premium(user.id, months=1, emoji_type="premium")
            
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO payments (payment_id, user_id, amount, currency, status, timestamp, product, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                payment.telegram_payment_charge_id,
                user.id,
                payment.total_amount,
                payment.currency,
                "completed",
                datetime.now().isoformat(),
                "premium_1month",
                payment.invoice_payload
            ))
            self.db.conn.commit()
            
            text = (
                f"🎉 *Поздравляем!*\n\n"
                f"✅ Премиум подписка активирована на 1 месяц!\n\n"
                f"✨ *Теперь вам доступно:*\n"
                f"• Редактирование и удаление сообщений ✏️\n"
                f"• Уникальный закрепленный эмодзи 🔒\n"
                f"• Выбор из {len(PREMIUM_EMOJIS)} премиум эмодзи ⭐\n"
                f"• 🔓 ОТКЛЮЧЕНИЕ спам-режима\n\n"
                f"*Как редактировать сообщения:*\n"
                f"1. Используйте <code>/edit ID</code> для редактирования\n"
                f"2. Используйте <code>/delete ID</code> для удаления\n\n"
                f"*Как закрепить эмодзи:*\n"
                f"1. Используйте <code>/availableemojis</code>\n"
                f"2. Выберите свободный эмодзи\n"
                f"3. Используйте <code>/emoji [эмодзи]</code>\n\n"
                f"Спасибо за покупку! 💫"
            )
            
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при активации премиума. Свяжитесь с администратором @anonaltshelper.",
                parse_mode=ParseMode.HTML
            )
    
    # ===================== ШИФРОВАННЫЕ АДМИН КОМАНДЫ =====================
    
    async def _encrypted_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Шифрованная админ команда: /as22f2ffj8"""
        user = update.effective_user
        
        if not is_admin(user.id):
            await update.message.reply_text("❌ Доступ запрещен.")
            return
        
        if not context.args:
            # Показываем доступные команды
            available_cmds = "\n".join([f"• <code>{cmd}</code>" for cmd in self.encrypted_commands.keys()][:10])
            
            text = (
                f"🔐 *Шифрованные админ команды*\n\n"
                f"*Использование:*\n"
                f"<code>/as22f2ffj8 [команда] [параметры]</code>\n\n"
                f"*Пример:*\n"
                f"<code>/as22f2ffj8 a1b2c3d4</code> - статистика\n"
                f"<code>/as22f2ffj8 m3n4o5p6 123456789</code> - забанить пользователя\n\n"
                f"*Доступные команды:*\n"
                f"{available_cmds}\n\n"
                f"*Для сессии:*\n"
                f"<code>/b3g5h7j9k1</code> - создать сессию\n"
                f"<code>/c4d6f8h0j2</code> - статус системы"
            )
            
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            return
        
        command = context.args[0]
        params = context.args[1:] if len(context.args) > 1 else []
        
        if command not in self.encrypted_commands:
            await update.message.reply_text(
                f"❌ Неизвестная команда: <code>{command}</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        try:
            # Выполняем шифрованную команду
            handler = self.encrypted_commands[command]
            result = await handler(update, context, user.id, params)
            
            if result:
                await update.message.reply_text(
                    f"✅ Команда выполнена:\n<code>`</code>\n{result}\n<code>`</code>",
                    parse_mode=ParseMode.HTML
                )
            
        except Exception as e:
            logger.error(f"Error executing encrypted command {command}: {e}")
            await update.message.reply_text(
                f"❌ Ошибка выполнения команды: {str(e)}",
                parse_mode=ParseMode.HTML
            )
    
    async def _encrypted_admin_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создание админ сессии: /b3g5h7j9k1"""
        user = update.effective_user
        
        if not is_admin(user.id):
            await update.message.reply_text("❌ Доступ запрещен.")
            return
        
        # Генерируем новую сессию
        session_token = secrets.token_hex(32)
        self.admin_sessions[user.id] = {
            'token': session_token,
            'created': datetime.now(),
            'expires': datetime.now() + timedelta(hours=24),
            'commands_used': 0
        }
        
        # Шифруем сессию
        encrypted_session = encrypt_admin_command("session", {
            'user_id': user.id,
            'token': session_token,
            'expires': self.admin_sessions[user.id]['expires'].isoformat()
        })
        
        text = (
            f"🔐 *Админ сессия создана*\n\n"
            f"*Токен:* <code>{session_token[:16]}...</code>\n"
            f"*Действует до:* {self.admin_sessions[user.id]['expires'].strftime('%d.%m.%Y %H:%M')}\n"
            f"*Команд использовано:* 0\n\n"
            f"*Шифрованная сессия:*\n"
            f"<code>{encrypted_session[:50]}...</code>\n\n"
            f"*Использование:*\n"
            f"Добавьте токен к командам:\n"
            f"<code>/as22f2ffj8 [команда] [параметры] #{session_token[:8]}</code>"
        )
        
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    async def _encrypted_admin_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статус системы: /c4d6f8h0j2"""
        user = update.effective_user
        
        if not is_admin(user.id):
            await update.message.reply_text("❌ Доступ запрещен.")
            return
        
        # Получаем статистику
        total_users = self.db.get_user_count()
        premium_users = self.db.get_premium_users_count()
        total_messages = self.db.get_message_count()
        
        # Статус сессий
        active_sessions = len(self.admin_sessions)
        user_session = self.admin_sessions.get(user.id)
        
        text = (
            f"📊 *Статус системы*\n\n"
            f"*Статистика:*\n"
            f"• Пользователи: {total_users}\n"
            f"• Премиум: {premium_users}\n"
            f"• Сообщений: {total_messages}\n\n"
            f"*Админ сессии:*\n"
            f"• Активных: {active_sessions}\n"
        )
        
        if user_session:
            expires = user_session['expires']
            time_left = expires - datetime.now()
            hours_left = int(time_left.total_seconds() / 3600)
            
            text += (
                f"• Ваша сессия: ✅ Активна\n"
                f"• Осталось: {hours_left} часов\n"
                f"• Команд использовано: {user_session['commands_used']}\n"
            )
        else:
            text += f"• Ваша сессия: ❌ Не активна\n"
        
        text += (
            f"\n*Шифрованные команды:*\n"
            f"• Доступно: {len(self.encrypted_commands)}\n"
            f"• Использовано: {user_session['commands_used'] if user_session else 0}\n\n"
            f"*Для создания сессии:*\n"
            f"<code>/b3g5h7j9k1</code>"
        )
        
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    # ===================== ШИФРОВАННЫЕ АДМИН ФУНКЦИИ =====================
    
    async def _admin_stats_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованная статистика: a1b2c3d4"""
        total_users = self.db.get_user_count()
        premium_users = self.db.get_premium_users_count()
        total_messages = self.db.get_message_count()
        
        recent_users = self.db.get_all_users(5)
        
        result = f"📊 СТАТИСТИКА\n"
        result += f"Пользователи: {total_users}\n"
        result += f"Премиум: {premium_users}\n"
        result += f"Сообщений: {total_messages}\n\n"
        result += f"ПОСЛЕДНИЕ ПОЛЬЗОВАТЕЛИ:\n"
        
        for i, (user_id, username, first_name, last_name, is_premium, reg_date, msg_count, edit_count, delete_count, last_activity) in enumerate(recent_users, 1):
            name = f"@{username}" if username else f"{first_name or ''}".strip() or f"ID:{user_id}"
            result += f"{i}. {name} ({'⭐' if is_premium else '👤'}) - {msg_count} сообщ.\n"
        
        return result
    
    async def _admin_users_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованный список пользователей: e5f6g7h8"""
        limit = 10
        if params and params[0].isdigit():
            limit = min(int(params[0]), 50)
        
        users = self.db.get_all_users(limit)
        
        result = f"👥 ПОЛЬЗОВАТЕЛИ ({len(users)} из {self.db.get_user_count()})\n\n"
        
        for i, (user_id, username, first_name, last_name, is_premium, reg_date, msg_count, edit_count, delete_count, last_activity) in enumerate(users, 1):
            name = f"@{username}" if username else f"{first_name or ''}".strip() or f"ID:{user_id}"
            status = "⭐" if is_premium else "👤"
            result += f"{i}. {status} {name} (ID:{user_id})\n"
            result += f"   📅 {msg_count}💬 {edit_count}✏️ {delete_count}🗑️\n"
        
        return result
    
    async def _admin_messages_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованная статистика сообщений: i9j0k1l2"""
        total_messages = self.db.get_message_count()
        
        # Получаем последние сообщения
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT m.channel_message_id, m.user_id, u.username, u.first_name, 
                   m.text, m.timestamp, m.is_edited, m.is_deleted
            FROM messages m
            JOIN users u ON m.user_id = u.user_id
            ORDER BY m.timestamp DESC
            LIMIT 5
        ''')
        recent_messages = cursor.fetchall()
        
        result = f"💬 СООБЩЕНИЯ: {total_messages}\n\n"
        
        for msg_id, user_id, username, first_name, text, timestamp, is_edited, is_deleted in recent_messages:
            name = f"@{username}" if username else f"{first_name or ''}".strip() or f"ID:{user_id}"
            status = "🗑️" if is_deleted else "✏️" if is_edited else "✅"
            
            try:
                time_obj = datetime.fromisoformat(timestamp)
                time_str = time_obj.strftime("%H:%M")
            except:
                time_str = "\\?\\?:\\?\\?"
            
            text_preview = (text or "")[:30].replace('\n', ' ')
            if len(text or "") > 30:
                text_preview += "..."
            
            result += f"#{msg_id} {status} {name} ({time_str})\n"
            result += f"   {text_preview}\n"
        
        return result
    
    async def _admin_ban_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованный бан пользователя: m3n4o5p6"""
        if not params:
            return "❌ Укажите ID пользователя\nИспользование: m3n4o5p6 [ID]"
        
        try:
            user_id = int(params[0])
            
            if user_id == admin_id:
                return "❌ Нельзя забанить самого себя"
            
            if user_id in ADMIN_IDS:
                return "❌ Нельзя забанить администратора"
            
            user_info = self.db.get_user_info(user_id)
            if not user_info:
                return f"❌ Пользователь {user_id} не найден"
            
            self.db.ban_user(user_id)
            
            username = f"@{user_info[1]}" if user_info[1] else f"{user_info[2] or ''}".strip() or f"ID:{user_id}"
            
            return f"✅ Пользователь {username} (ID:{user_id}) забанен"
            
        except ValueError:
            return "❌ Неверный формат ID"
    
    async def _admin_unban_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованный разбан пользователя: q7r8s9t0"""
        if not params:
            return "❌ Укажите ID пользователя\nИспользование: q7r8s9t0 [ID]"
        
        try:
            user_id = int(params[0])
            
            user_info = self.db.get_user_info(user_id)
            if not user_info:
                return f"❌ Пользователь {user_id} не найден"
            
            self.db.unban_user(user_id)
            
            username = f"@{user_info[1]}" if user_info[1] else f"{user_info[2] or ''}".strip() or f"ID:{user_id}"
            
            return f"✅ Пользователь {username} (ID:{user_id}) разбанен"
            
        except ValueError:
            return "❌ Неверный формат ID"
    
    async def _admin_premium_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованная выдача премиума: u1v2w3x4"""
        if len(params) < 2:
            return "❌ Укажите ID и дни\nИспользование: u1v2w3x4 [ID] [дни]"
        
        try:
            user_id = int(params[0])
            days = int(params[1])
            
            user_info = self.db.get_user_info(user_id)
            if not user_info:
                return f"❌ Пользователь {user_id} не найден"
            
            username = f"@{user_info[1]}" if user_info[1] else f"{user_info[2] or ''}".strip() or f"ID:{user_id}"
            
            if days <= 0:
                # Отобрать премиум
                cursor = self.db.conn.cursor()
                cursor.execute('UPDATE users SET is_premium = 0, premium_until = NULL WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM emoji_reservations WHERE user_id = ?', (user_id,))
                self.db.conn.commit()
                
                return f"✅ Премиум отобран у {username} (ID:{user_id})"
            else:
                # Выдать премиум
                self.db.add_premium_days(user_id, days)
                
                return f"✅ {username} (ID:{user_id}) получил премиум на {days} дней"
            
        except ValueError:
            return "❌ Неверный формат параметров"
    
    async def _admin_emoji_list_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованный список эмодзи: y5z6a7b8"""
        reserved_emojis = self.db.get_all_reserved_emojis()
        available_emojis = self.db.get_available_emojis()
        
        result = f"🎨 ЭМОДЗИ\n"
        result += f"Всего премиум: {len(PREMIUM_EMOJIS)}\n"
        result += f"Занято: {len(reserved_emojis)}\n"
        result += f"Свободно: {len(available_emojis)}\n\n"
        
        if reserved_emojis:
            result += f"ЗАНЯТЫЕ ЭМОДЗИ:\n"
            for i, (emoji, user_id, username, first_name, reserved_at) in enumerate(reserved_emojis[:5], 1):
                name = f"@{username}" if username else f"{first_name or f'ID{user_id}'}"
                result += f"{i}. {emoji} - {name} (ID:{user_id})\n"
            
            if len(reserved_emojis) > 5:
                result += f"... и еще {len(reserved_emojis) - 5}\n"
        
        return result
    
    async def _admin_free_emoji_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованное освобождение эмодзи: c9d0e1f2"""
        if not params:
            return "❌ Укажите эмодзи\nИспользование: c9d0e1f2 [эмодзи]"
        
        emoji = params[0]
        
        success = self.db.free_emoji(emoji)
        
        if success:
            return f"✅ Эмодзи {emoji} освобожден"
        else:
            return f"❌ Эмодзи {emoji} не был занят"
    
    async def _admin_broadcast_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованная рассылка: g3h4i5j6"""
        if not params:
            return "❌ Укажите сообщение\nИспользование: g3h4i5j6 [текст]"
        
        message_text = " ".join(params)
        
        users = self.db.get_all_users(1000)
        
        if not users:
            return "❌ Нет пользователей для рассылки"
        
        result = f"📢 РАССЫЛКА\n"
        result += f"Пользователей: {len(users)}\n"
        result += f"Текст: {message_text[:50]}...\n\n"
        result += f"⚠️ Используйте с осторожностью!"
        
        return result
    
    async def _admin_reset_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованный сброс БД: k7l8m9n0"""
        result = "🗑️ СБРОС БАЗЫ ДАННЫХ\n\n"
        result += "⚠️ ОПАСНАЯ КОМАНДА!\n"
        result += "Это удалит:\n"
        result += "- Всех пользователей\n"
        result += "- Все сообщения\n"
        result += "- Все платежи\n"
        result += "- Все резервации\n\n"
        result += "Для подтверждения:\n"
        result += "k7l8m9n0 CONFIRM"
        
        if params and params[0] == "CONFIRM":
            self.db.reset_database()
            return "✅ База данных сброшена"
        
        return result
    
    async def _admin_restart_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованная перезагрузка: o1p2q3r4"""
        result = "🔄 ПЕРЕЗАГРУЗКА\n\n"
        result += "Для перезагрузки бота отправьте:\n"
        result += "o1p2q3r4 RESTART"
        
        if params and params[0] == "RESTART":
            # В реальном боте здесь был бы перезапуск
            return "✅ Бот будет перезагружен"
        
        return result
    
    async def _admin_debug_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованная отладка: s5t6u7v8"""
        result = "🐛 ОТЛАДКА\n\n"
        
        # Статус бота
        result += f"Бот работает: ✅\n"
        result += f"Пользователей в памяти: {len(self.user_cooldowns)}\n"
        result += f"Ожидают редактирования: {len(self.pending_edits)}\n"
        result += f"Ожидают ответа: {len(self.pending_replies)}\n"
        result += f"Активных сессий: {len(self.admin_sessions)}\n\n"
        
        # Проверка канала
        try:
            chat = await context.bot.get_chat(CHANNEL_ID)
            result += f"Канал доступен: ✅ {chat.title}\n"
        except Exception as e:
            result += f"Канал недоступен: ❌ {str(e)}\n"
        
        return result
    
    async def _admin_logs_encrypted(self, update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id: int, params: List[str]):
        """Шифрованные логи: w9x0y1z2"""
        result = "📋 ЛОГИ\n\n"
        
        try:
            with open('bot.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()[-20:]  # Последние 20 строк
                log_content = "".join(lines)
                
                if len(log_content) > 1000:
                    result += log_content[-1000:] + "\n... (обрезано)"
                else:
                    result += log_content
        except FileNotFoundError:
            result += "Файл логов не найден"
        except Exception as e:
            result += f"Ошибка чтения логов: {str(e)}"
        
        return result
    
    # ===================== ОБРАБОТКА СООБЩЕНИЙ =====================
    
    async def _handle_all_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка всех сообщений"""
        user = update.effective_user
        
        if update.message and update.message.text and update.message.text.startswith('/'):
            return
        
        # Проверяем, является ли пользователь в процессе редактирования
        if user.id in self.pending_edits:
            await self._process_edit_text(update, context, user.id)
            return
        
        # Проверяем, является ли пользователь в процессе ответа
        if user.id in self.pending_replies:
            await self._process_reply_text(update, context, user.id)
            return
        
        # Проверяем, является ли сообщение пересланным (ответом)
        if hasattr(update.message, 'forward_from_chat') and update.message.forward_from_chat:
            if update.message.forward_from_chat.username == CHANNEL_ID.replace('@', ''):
                await self._handle_reply_message(update, context)
                return
        
        # Если не пересланное сообщение или не из нашего канала - обычное сообщение
        await self._handle_new_message(update, context)
    
    async def _process_edit_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Обработка текста для редактирования"""
        if user_id not in self.pending_edits:
            await update.message.reply_text("❌ Сессия редактирования истекла. Пожалуйста, начните заново.")
            return
        
        message_id, old_text = self.pending_edits[user_id]
        new_text = update.message.text or update.message.caption or ""
        
        if not new_text.strip():
            await update.message.reply_text("❌ Текст не может быть пустым.")
            return
        
        # Если текст не изменился
        if old_text == new_text:
            await update.message.reply_text(
                "⚠️ *Текст не изменился*\n\n"
                "Новый текст совпадает со старым, редактирование не требуется.",
                parse_mode=ParseMode.HTML
            )
            del self.pending_edits[user_id]
            return
        
        try:
            message_info = self.db.get_message_info(message_id)
            if not message_info:
                await update.message.reply_text("❌ Сообщение не найдено.")
                del self.pending_edits[user_id]
                return
            
            if not self.db.is_message_owner(user_id, message_id) and not is_admin(user_id):
                await update.message.reply_text("❌ Вы не являетесь владельцем этого сообщения.")
                del self.pending_edits[user_id]
                return
            
            success = self.db.edit_message(user_id, message_id, new_text)
            
            if not success:
                await update.message.reply_text("❌ Не удалось отредактировать сообщение.")
                del self.pending_edits[user_id]
                return
            
            # Получаем эмодзи пользователя
            user_emoji = self.db.get_user_emoji(user_id)
            
            # Форматируем новое сообщение
            message_prefix = f"{user_emoji}: "
            formatted_message = f"{message_prefix}{new_text}"
            
            # Редактируем сообщение в канале
            try:
                await context.bot.edit_message_text(
                    chat_id=CHANNEL_ID,
                    message_id=message_id,
                    text=formatted_message,
                    parse_mode=ParseMode.HTML if any(mark in new_text for mark in ['*', '_', '`']) else None
                )
                
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Ошибка редактирования в канале: {e}")
            except Exception as e:
                logger.error(f"Ошибка редактирования в канале: {e}")
            
            # Удаляем из pending_edits
            del self.pending_edits[user_id]
            
            await update.message.reply_text(
                f"✅ *Сообщение отредактировано!*\n\n"
                f"Сообщение #{message_id} успешно обновлено.",
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ошибка редактирования: {error_msg}")
            await update.message.reply_text(f"❌ Ошибка при редактировании: {error_msg}")
            if user_id in self.pending_edits:
                del self.pending_edits[user_id]
    
    async def _process_reply_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Обработка текста ответа"""
        if user_id not in self.pending_replies:
            await update.message.reply_text("❌ Сессия ответа истекла. Пожалуйста, начните заново.")
            return
        
        original_message_id, _ = self.pending_replies[user_id]
        
        # Получаем текст ответа
        reply_text = update.message.text or update.message.caption or ""
        if not reply_text.strip():
            await update.message.reply_text("❌ Ответ не может быть пустым.")
            return
        
        # Получаем данные пользователя
        user_emoji = self.db.get_user_emoji(user_id)
        
        # Форматируем ответ
        message_prefix = f"{user_emoji}: "
        formatted_reply = f"{message_prefix}{reply_text}"
        
        try:
            # Отправляем ответ в канал
            sent_message = await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=formatted_reply,
                parse_mode=ParseMode.HTML if any(mark in reply_text for mark in ['*', '_', '`']) else None
            )
            
            # Логируем ответ в базе данных
            self.db.log_message(user_id, sent_message.message_id, reply_text, 
                              reply_to=original_message_id, emoji_used=user_emoji)
            
            # Удаляем из pending_replies
            del self.pending_replies[user_id]
            
            # Создаем клавиатуру с кнопками управления для премиум пользователей
            keyboard = []
            if self.db.is_user_premium(user_id) or is_admin(user_id):
                keyboard = [
                    [
                        InlineKeyboardButton("✏️ Редактировать", callback_data=f'edit_select'),
                        InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_select')
                    ]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            
            response_text = (
                f"✅ *Ответ отправлен!*\n\n"
                f"Ваш ответ был отправлен как ответ на сообщение #{original_message_id}"
            )
            
            if not self.db.is_user_premium(user_id):
                response_text += f"\n\n✨ *Получите Premium, чтобы редактировать и удалять сообщения!*\nИспользуйте /premium"
            
            await update.message.reply_text(
                response_text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ошибка отправки ответа: {error_msg}")
            
            await update.message.reply_text(f"❌ Ошибка при отправке: {error_msg}")
    
    async def _handle_reply_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ответа на сообщение"""
        user = update.effective_user
        
        spam_check = check_spam_cooldown(user.id, self.db, self.user_cooldowns)
        if spam_check:
            await update.message.reply_text(spam_check)
            return
        
        self.db.register_user(
            user.id, 
            user.username or "", 
            user.first_name or "", 
            user.last_name or ""
        )
        
        # Получаем ID оригинального сообщения
        if not update.message.forward_from_message_id:
            await update.message.reply_text(
                "❌ Не удалось определить сообщение для ответа.\n"
                "Пожалуйста, перешлите сообщение из канала корректно.",
                parse_mode=ParseMode.HTML
            )
            return
        
        original_message_id = update.message.forward_from_message_id
        
        # Проверяем, существует ли оригинальное сообщение
        message_info = self.db.get_message_info(original_message_id)
        if not message_info:
            await update.message.reply_text(
                "❌ Оригинальное сообщение не найдено.\n"
                "Возможно, оно было удалено или слишком старое.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Сохраняем информацию об ответе
        self.pending_replies[user.id] = (original_message_id, None)
        
        # Всегда запрашиваем текст ответа
        await update.message.reply_text(
            "✏️ *Ответ на сообщение*\n\n"
            f"Вы отвечаете на сообщение #{original_message_id}\n\n"
            f"*Теперь отправьте текст вашего ответа:*",
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_new_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нового сообщения (не ответа)"""
        user = update.effective_user
        
        spam_check = check_spam_cooldown(user.id, self.db, self.user_cooldowns)
        if spam_check:
            await update.message.reply_text(spam_check)
            return
        
        self.db.register_user(
            user.id, 
            user.username or "", 
            user.first_name or "", 
            user.last_name or ""
        )
        
        # Проверяем, не является ли это текстом ответа на пересланное сообщение
        if user.id in self.pending_replies:
            return
        
        try:
            message = update.message
            
            # Получаем эмодзи пользователя
            user_emoji = self.db.get_user_emoji(user.id)
            
            # Форматируем префикс сообщения
            message_prefix = f"{user_emoji}: "
            
            if message.text:
                formatted_message = f"{message_prefix}{message.text}"
                
                # Отправляем сообщение в канал
                sent_message = await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=formatted_message,
                    parse_mode=ParseMode.HTML if any(mark in message.text for mark in ['*', '_', '`']) else None
                )
                
                # Логируем сообщение
                self.db.log_message(user.id, sent_message.message_id, message.text, emoji_used=user_emoji)
                
                # Создаем клавиатуру с кнопками управления
                keyboard = []
                if self.db.is_user_premium(user.id) or is_admin(user.id):
                    keyboard = [
                        [
                            InlineKeyboardButton("✏️ Редактировать", callback_data=f'edit_select'),
                            InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_select')
                        ]
                    ]
                
                reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                
                response_text = (
                    f"✅ *Сообщение отправлено!*\n\n"
                    f"ID сообщения: <code>{sent_message.message_id}</code>"
                )
                
                if not self.db.is_user_premium(user.id):
                    response_text += f"\n\n✨ *Получите Premium, чтобы редактировать и удалять сообщения!*\nИспользуйте /premium"
                
                await update.message.reply_text(
                    response_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
                
            elif message.photo:
                photo = message.photo[-1]
                caption = f"{message_prefix}Анонимное фото"
                if message.caption:
                    caption = f"{message_prefix}{message.caption}"
                
                sent_message = await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=photo.file_id,
                    caption=caption,
                    parse_mode=ParseMode.HTML if message.caption and any(mark in message.caption for mark in ['*', '_', '`']) else None
                )
                
                if message.caption:
                    self.db.log_message(user.id, sent_message.message_id, message.caption, emoji_used=user_emoji)
                else:
                    self.db.log_message(user.id, sent_message.message_id, "Анонимное фото", emoji_used=user_emoji)
                
                keyboard = []
                if self.db.is_user_premium(user.id) or is_admin(user.id):
                    keyboard = [
                        [
                            InlineKeyboardButton("✏️ Редактировать", callback_data=f'edit_select'),
                            InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_select')
                        ]
                    ]
                
                reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                
                response_text = (
                    f"✅ *Фото отправлено!*\n\n"
                    f"ID сообщения: <code>{sent_message.message_id}</code>\n"
                    f"(Редактирование фото недоступно)"
                )
                
                if not self.db.is_user_premium(user.id):
                    response_text += f"\n\n✨ *Получите Premium, чтобы удалять сообщения!*\nИспользуйте /premium"
                
                await update.message.reply_text(
                    response_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
                
            elif message.video:
                video = message.video
                caption = f"{message_prefix}Анонимное видео"
                if message.caption:
                    caption = f"{message_prefix}{message.caption}"
                
                sent_message = await context.bot.send_video(
                    chat_id=CHANNEL_ID,
                    video=video.file_id,
                    caption=caption,
                    parse_mode=ParseMode.HTML if message.caption and any(mark in message.caption for mark in ['*', '_', '`']) else None
                )
                
                if message.caption:
                    self.db.log_message(user.id, sent_message.message_id, message.caption, emoji_used=user_emoji)
                else:
                    self.db.log_message(user.id, sent_message.message_id, "Анонимное видео", emoji_used=user_emoji)
                
                keyboard = []
                if self.db.is_user_premium(user.id) or is_admin(user.id):
                    keyboard = [
                        [
                            InlineKeyboardButton("✏️ Редактировать", callback_data=f'edit_select'),
                            InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_select')
                        ]
                    ]
                
                reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                
                response_text = (
                    f"✅ *Видео отправлено!*\n\n"
                    f"ID сообщения: <code>{sent_message.message_id}</code>\n"
                    f"(Редактирование видео недоступно)"
                )
                
                if not self.db.is_user_premium(user.id):
                    response_text += f"\n\n✨ *Получите Premium, чтобы удалять сообщения!*\nИспользуйте /premium"
                
                await update.message.reply_text(
                    response_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            
            elif message.voice:
                voice = message.voice
                caption = f"{message_prefix}Анонимное голосовое сообщение"
                
                sent_message = await context.bot.send_voice(
                    chat_id=CHANNEL_ID,
                    voice=voice.file_id,
                    caption=caption
                )
                
                self.db.log_message(user.id, sent_message.message_id, "Анонимное голосовое сообщение", emoji_used=user_emoji)
                
                keyboard = []
                if self.db.is_user_premium(user.id) or is_admin(user.id):
                    keyboard = [
                        [InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_select')]
                    ]
                
                reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                
                response_text = "✅ Голосовое сообщение отправлено в канал!"
                
                if not self.db.is_user_premium(user.id):
                    response_text += f"\n\n✨ *Получите Premium, чтобы удалять сообщения!*\nИспользуйте /premium"
                
                await update.message.reply_text(
                    response_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            
            elif message.document:
                document = message.document
                caption = f"{message_prefix}Анонимный документ"
                if message.caption:
                    caption = f"{message_prefix}{message.caption}"
                
                sent_message = await context.bot.send_document(
                    chat_id=CHANNEL_ID,
                    document=document.file_id,
                    caption=caption,
                    parse_mode=ParseMode.HTML if message.caption and any(mark in message.caption for mark in ['*', '_', '`']) else None
                )
                
                if message.caption:
                    self.db.log_message(user.id, sent_message.message_id, message.caption, emoji_used=user_emoji)
                else:
                    self.db.log_message(user.id, sent_message.message_id, "Анонимный документ", emoji_used=user_emoji)
                
                keyboard = []
                if self.db.is_user_premium(user.id) or is_admin(user.id):
                    keyboard = [
                        [
                            InlineKeyboardButton("✏️ Редактировать", callback_data=f'edit_select'),
                            InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_select')
                        ]
                    ]
                
                reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                
                response_text = "✅ Документ отправлен в канал!"
                
                if not self.db.is_user_premium(user.id):
                    response_text += f"\n\n✨ *Получите Premium, чтобы редактировать и удалять сообщения!*\nИспользуйте /premium"
                
                await update.message.reply_text(
                    response_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ошибка отправки: {error_msg}")
            await update.message.reply_text(f"❌ Ошибка: {error_msg}")
    
    # ===================== ОБРАБОТКА КНОПОК =====================
    
    async def _button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик кнопок"""
        query = update.callback_query
        
        try:
            await query.answer()
        except Exception as e:
            logger.error(f"Ошибка при ответе на callback_query: {e}")
        
        user = query.from_user
        data = query.data
        
        # Обработка удаления сообщений
        if data.startswith('delete_confirm_'):
            await self._delete_confirm_callback(update, context)
            return
        
        elif data.startswith('delete_cancel_'):
            await self._delete_cancel_callback(update, context)
            return
        
        # Обработка покупки премиума
        elif data == "buy_premium_stars":
            await self._buy_premium_stars_callback(update, context)
            return
        
        # Обработка редактирования/удаления через кнопки
        elif data == "edit_select":
            await self._edit_select_callback(update, context)
            return
        
        elif data == "delete_select":
            await self._delete_select_callback(update, context)
            return
        
        # Обработка админ панели
        elif data == "admin_panel":
            if not is_admin(user.id):
                await query.edit_message_text("❌ У вас нет доступа к админ меню.")
                return
            
            keyboard = [
                [InlineKeyboardButton("📊 Статистика", callback_data='admin_stats')],
                [InlineKeyboardButton("👥 Пользователи", callback_data='admin_users')],
                [InlineKeyboardButton("🎨 Эмодзи", callback_data='admin_emoji')],
                [InlineKeyboardButton("⚙️ Настройки", callback_data='admin_settings')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "👑 *Админ панель*\n\n"
                "Выберите раздел для управления ботом:",
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            return
        
        # Обработка других кнопок админ панели
        elif data in ['admin_stats', 'admin_users', 'admin_emoji', 'admin_settings']:
            if not is_admin(user.id):
                await query.edit_message_text("❌ У вас нет доступа.")
                return
            
            if data == 'admin_stats':
                await self._admin_stats_button(update, context)
            elif data == 'admin_users':
                await self._admin_users_button(update, context)
            elif data == 'admin_emoji':
                await self._admin_emoji_button(update, context)
            elif data == 'admin_settings':
                await self._admin_settings_button(update, context)
            
            return
        
        # Неизвестная команда
        else:
            await query.edit_message_text("❌ Неизвестная команда.")
    
    async def _delete_confirm_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Подтверждение удаления сообщения"""
        query = update.callback_query
        
        user = query.from_user
        message_id = int(query.data.replace('delete_confirm_', ''))
        
        try:
            # Проверяем, является ли пользователь владельцем сообщения
            if not self.db.is_message_owner(user.id, message_id) and not is_admin(user.id):
                await query.edit_message_text("❌ Вы не являетесь владельцем этого сообщения.")
                return
            
            # Удаляем сообщение в базе данных
            success = self.db.delete_message(user.id, message_id)
            
            if not success:
                await query.edit_message_text("❌ Не удалось удалить сообщение.")
                return
            
            # Пытаемся удалить сообщение из канала
            try:
                await context.bot.delete_message(
                    chat_id=CHANNEL_ID,
                    message_id=message_id
                )
            except Exception as e:
                logger.error(f"Ошибка удаления из канала: {e}")
            
            await query.edit_message_text(
                f"✅ *Сообщение удалено!*\n\n"
                f"Сообщение #{message_id} было успешно удалено.",
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Ошибка удаления: {e}")
            await query.edit_message_text(f"❌ Ошибка при удалении: {str(e)}")
    
    async def _delete_cancel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена удаления сообщения"""
        query = update.callback_query
        
        await query.edit_message_text(
            "❌ Удаление отменено.",
            parse_mode=ParseMode.HTML
        )
    
    async def _buy_premium_stars_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Колбэк для оплаты через Stars"""
        query = update.callback_query
        
        user = query.from_user
        
        if self.db.is_user_premium(user.id):
            await query.edit_message_text(
                "✅ У вас уже есть активная премиум подписка!\n"
                "Используйте /myemoji чтобы посмотреть ваш текущий эмодзи.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Создаем инвойс для оплаты через Stars
        try:
            payload = f"premium_1month_{user.id}"
            
            await context.bot.send_invoice(
                chat_id=user.id,
                title="Anon Premium - 1 месяц",
                description="Премиум подписка на 1 месяц\n✅ Редактирование сообщений\n✅ Уникальный эмодзи\n✅ Без спам-режима",
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label="Premium (1 месяц)", amount=PREMIUM_PRICE)],
                start_parameter="anon_premium",
                need_email=False,
                need_phone_number=False,
                need_shipping_address=False,
                is_flexible=False,
                protect_content=True
            )
            
        except Exception as e:
            logger.error(f"Ошибка при создании инвойса: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при создании платежа. Попробуйте позже.",
                parse_mode=ParseMode.HTML
            )
    
    async def _edit_select_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выбор сообщения для редактирования"""
        query = update.callback_query
        
        await query.edit_message_text(
            "✏️ *Редактирование сообщения*\n\n"
            "Введите ID сообщения для редактирования:\n"
            "*Пример:* <code>/edit 123</code>",
            parse_mode=ParseMode.HTML
        )
    
    async def _delete_select_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выбор сообщения для удаления"""
        query = update.callback_query
        
        await query.edit_message_text(
            "🗑️ *Удаление сообщения*\n\n"
            "Введите ID сообщения для удаления:\n"
            "*Пример:* <code>/delete 123</code>",
            parse_mode=ParseMode.HTML
        )
    
    async def _admin_stats_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Кнопка статистики админ панели"""
        query = update.callback_query
        
        total_users = self.db.get_user_count()
        premium_users = self.db.get_premium_users_count()
        total_messages = self.db.get_message_count()
        
        recent_users = self.db.get_all_users(5)
        
        text = (
            f"📊 *Статистика бота*\n\n"
            f"👥 *Пользователи:*\n"
            f"• Всего: {total_users}\n"
            f"• Премиум: {premium_users}\n"
            f"• Обычные: {total_users - premium_users}\n\n"
            f"💬 *Сообщения:*\n"
            f"• Всего: {total_messages}\n\n"
            f"🆕 *Последние пользователи:*\n"
        )
        
        for i, (user_id, username, first_name, last_name, is_premium, reg_date, msg_count, edit_count, delete_count, last_activity) in enumerate(recent_users, 1):
            name = f"@{username}" if username else f"{first_name or ''}".strip() or f"ID:{user_id}"
            premium_status = "⭐" if is_premium else "👤"
            text += f"{i}. {premium_status} {escape_markdown(name)}\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='admin_stats')],
            [InlineKeyboardButton("🔙 Назад", callback_data='admin_panel')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text, 
            parse_mode=ParseMode.HTML, 
            reply_markup=reply_markup
        )
    
    async def _admin_users_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Кнопка пользователей админ панели"""
        query = update.callback_query
        
        text = (
            f"👥 *Управление пользователями*\n\n"
            f"*Шифрованные команды:*\n"
            f"<code>/as22f2ffj8 e5f6g7h8</code> - список пользователей\n"
            f"<code>/as22f2ffj8 m3n4o5p6 [ID]</code> - забанить\n"
            f"<code>/as22f2ffj8 q7r8s9t0 [ID]</code> - разбанить\n"
            f"<code>/as22f2ffj8 u1v2w3x4 [ID] [дни]</code> - выдать премиум\n\n"
            f"*Статистика:*\n"
            f"Всего пользователей: {self.db.get_user_count()}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data='admin_panel')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text, 
            parse_mode=ParseMode.HTML, 
            reply_markup=reply_markup
        )
    
    async def _admin_emoji_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Кнопка эмодзи админ панели"""
        query = update.callback_query
        
        reserved_emojis = self.db.get_all_reserved_emojis()
        
        text = (
            f"🎨 *Управление эмодзи*\n\n"
            f"*Шифрованные команды:*\n"
            f"<code>/as22f2ffj8 y5z6a7b8</code> - список эмодзи\n"
            f"<code>/as22f2ffj8 c9d0e1f2 [эмодзи]</code> - освободить эмодзи\n\n"
            f"*Статистика:*\n"
            f"• Занято эмодзи: {len(reserved_emojis)}\n"
            f"• Свободно эмодзи: {len(PREMIUM_EMOJIS) - len(reserved_emojis)}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='admin_emoji')],
            [InlineKeyboardButton("🔙 Назад", callback_data='admin_panel')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text, 
            parse_mode=ParseMode.HTML, 
            reply_markup=reply_markup
        )
    
    async def _admin_settings_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Кнопка настроек админ панели"""
        query = update.callback_query
        
        text = (
            f"⚙️ *Настройки системы*\n\n"
            f"*Шифрованные команды:*\n"
            f"<code>/as22f2ffj8 g3h4i5j6 [текст]</code> - рассылка\n"
            f"<code>/as22f2ffj8 k7l8m9n0</code> - сброс БД\n"
            f"<code>/as22f2ffj8 s5t6u7v8</code> - отладка\n"
            f"<code>/as22f2ffj8 w9x0y1z2</code> - логи\n\n"
            f"*Системные команды:*\n"
            f"<code>/b3g5h7j9k1</code> - создать сессию\n"
            f"<code>/c4d6f8h0j2</code> - статус системы"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data='admin_panel')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text, 
            parse_mode=ParseMode.HTML, 
            reply_markup=reply_markup
        )