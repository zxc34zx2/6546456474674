#!/usr/bin/env python3
# 🔐 API PROTECTOR MODULE - PROTECTION AGAINST API HACKING
# ⚠️ DO NOT MODIFY - API SECURITY ENFORCED

import re
import time
import hashlib
import hmac
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from functools import wraps
import logging

# 🚨 API ATTACK PATTERNS
class APIAttackPatterns:
    """Patterns for detecting API attacks"""
    
    # Injection patterns
    INJECTION_PATTERNS = [
        (r'(union.*select)', 'SQL_INJECTION_UNION'),
        (r'(select.*from)', 'SQL_INJECTION_SELECT'),
        (r'(insert.*into)', 'SQL_INJECTION_INSERT'),
        (r'(update.*set)', 'SQL_INJECTION_UPDATE'),
        (r'(delete.*from)', 'SQL_INJECTION_DELETE'),
        (r'(drop.*table)', 'SQL_INJECTION_DROP'),
        (r'(exec.*\(.*\))', 'COMMAND_INJECTION'),
        (r'(system\(.*\))', 'SYSTEM_COMMAND_INJECTION'),
        (r'(eval\(.*\))', 'EVAL_INJECTION'),
        (r'(<script.*>)', 'XSS_ATTEMPT'),
        (r'(javascript:)', 'XSS_JAVASCRIPT'),
        (r'(onload=)', 'XSS_ONLOAD'),
        (r'(onerror=)', 'XSS_ONERROR'),
        (r'(alert\(.*\))', 'XSS_ALERT'),
        (r'(document\.cookie)', 'XSS_COOKIE_THEFT'),
    ]
    
    # Rate limiting patterns
    RATE_LIMIT_PATTERNS = [
        (r'(\d+ requests in \d+ seconds)', 'RATE_LIMIT_DETECTED'),
    ]
    
    # Bot detection patterns
    BOT_PATTERNS = [
        (r'(python-requests)', 'PYTHON_BOT'),
        (r'(curl)', 'CURL_BOT'),
        (r'(wget)', 'WGET_BOT'),
        (r'(scrapy)', 'SCRAPY_BOT'),
        (r'(sellenium)', 'SELENIUM_BOT'),
        (r'(phantomjs)', 'PHANTOMJS_BOT'),
        (r'(headless)', 'HEADLESS_BROWSER'),
        (r'(bot|crawler|spider)', 'GENERIC_BOT'),
    ]
    
    # API abuse patterns
    ABUSE_PATTERNS = [
        (r'(\.\./)', 'DIRECTORY_TRAVERSAL'),
        (r'(etc/passwd)', 'FILE_DISCLOSURE'),
        (r'(\.env)', 'ENV_FILE_ACCESS'),
        (r'(config\.)', 'CONFIG_ACCESS'),
        (r'(admin)', 'ADMIN_ACCESS_ATTEMPT'),
        (r'(login)', 'LOGIN_BRUTEFORCE'),
        (r'(password)', 'PASSWORD_ATTEMPT'),
        (r'(token)', 'TOKEN_THEFT_ATTEMPT'),
        (r'(key)', 'KEY_THEFT_ATTEMPT'),
        (r'(secret)', 'SECRET_ACCESS_ATTEMPT'),
    ]
    
    # Telegram API specific attacks
    TELEGRAM_PATTERNS = [
        (r'(getMe.*abuse)', 'TELEGRAM_API_ABUSE'),
        (r'(sendMessage.*spam)', 'TELEGRAM_SPAM_ATTEMPT'),
        (r'(forwardMessage.*mass)', 'TELEGRAM_MASS_FORWARD'),
        (r'(editMessage.*flood)', 'TELEGRAM_EDIT_FLOOD'),
        (r'(deleteMessage.*mass)', 'TELEGRAM_MASS_DELETE'),
        (r'(getChat.*harvest)', 'TELEGRAM_DATA_HARVEST'),
        (r'(getUser.*harvest)', 'TELEGRAM_USER_HARVEST'),
    ]

# 🔐 API REQUEST VALIDATOR
class APIRequestValidator:
    """Validate and sanitize API requests"""
    
    def __init__(self, database):
        self.db = database
        self.rate_limit_store = {}
        self.request_history = {}
        self.blocked_ips = set()
        self.suspicious_users = {}
        
    def validate_request(self, update_data: Dict, user_id: int) -> Tuple[bool, str, Dict]:
        """Validate API request with multiple security checks"""
        
        validation_results = {
            'checks_passed': [],
            'checks_failed': [],
            'threats_detected': [],
            'risk_score': 0
        }
        
        # Check 1: Rate limiting
        rate_ok, rate_msg = self._check_rate_limit(user_id)
        if not rate_ok:
            validation_results['checks_failed'].append(('RATE_LIMIT', rate_msg))
            validation_results['risk_score'] += 30
            self._log_attack(user_id, 'RATE_LIMIT_VIOLATION', rate_msg)
        
        # Check 2: Content validation
        content_ok, content_msg, content_threats = self._validate_content(update_data)
        if not content_ok:
            validation_results['checks_failed'].append(('CONTENT_VALIDATION', content_msg))
            validation_results['threats_detected'].extend(content_threats)
            validation_results['risk_score'] += len(content_threats) * 10
        
        # Check 3: User agent validation
        ua_ok, ua_msg = self._validate_user_agent(update_data)
        if not ua_ok:
            validation_results['checks_failed'].append(('USER_AGENT', ua_msg))
            validation_results['risk_score'] += 20
        
        # Check 4: Request structure
        structure_ok, structure_msg = self._validate_structure(update_data)
        if not structure_ok:
            validation_results['checks_failed'].append(('STRUCTURE', structure_msg))
            validation_results['risk_score'] += 15
        
        # Check 5: Bot detection
        bot_ok, bot_msg = self._detect_bot_behavior(user_id, update_data)
        if not bot_ok:
            validation_results['checks_failed'].append(('BOT_DETECTION', bot_msg))
            validation_results['risk_score'] += 25
        
        # Determine if request should be blocked
        should_block = validation_results['risk_score'] > 50 or \
                      any('INJECTION' in threat for threat in validation_results['threats_detected'])
        
        if should_block:
            block_reason = f"Risk score: {validation_results['risk_score']}, Threats: {validation_results['threats_detected']}"
            self._log_attack(user_id, 'REQUEST_BLOCKED', block_reason)
            return False, "REQUEST_BLOCKED", validation_results
        
        # All checks passed
        validation_results['checks_passed'] = [
            'RATE_LIMIT', 'CONTENT_VALIDATION', 'USER_AGENT', 
            'STRUCTURE', 'BOT_DETECTION'
        ]
        
        return True, "REQUEST_VALID", validation_results
    
    def _check_rate_limit(self, user_id: int) -> Tuple[bool, str]:
        """Check rate limiting for user"""
        current_time = time.time()
        
        if user_id not in self.request_history:
            self.request_history[user_id] = []
        
        # Clean old requests
        self.request_history[user_id] = [
            t for t in self.request_history[user_id] 
            if current_time - t < 60  # Last 60 seconds
        ]
        
        # Check limits
        if len(self.request_history[user_id]) >= 30:  # 30 requests per minute
            return False, "Rate limit exceeded (30/min)"
        
        if len(self.request_history[user_id]) >= 5 and \
           current_time - self.request_history[user_id][0] < 5:  # 5 requests in 5 seconds
            return False, "Burst rate limit exceeded"
        
        # Add current request
        self.request_history[user_id].append(current_time)
        
        return True, "Rate limit OK"
    
    def _validate_content(self, update_data: Dict) -> Tuple[bool, str, List[str]]:
        """Validate content for injection attempts"""
        threats = []
        
        # Convert update to string for pattern matching
        update_str = json.dumps(update_data, ensure_ascii=False).lower()
        
        # Check all patterns
        all_patterns = (
            APIAttackPatterns.INJECTION_PATTERNS +
            APIAttackPatterns.ABUSE_PATTERNS +
            APIAttackPatterns.TELEGRAM_PATTERNS
        )
        
        for pattern, threat_name in all_patterns:
            if re.search(pattern, update_str, re.IGNORECASE):
                threats.append(threat_name)
        
        # Check for encoded attacks
        encoded_threats = self._check_encoded_attacks(update_str)
        threats.extend(encoded_threats)
        
        if threats:
            return False, f"Injection attempts detected: {threats[:3]}", threats
        
        return True, "Content validation passed", []
    
    def _check_encoded_attacks(self, text: str) -> List[str]:
        """Check for encoded/obfuscated attacks"""
        threats = []
        
        # Hex encoding
        hex_pattern = r'(?:\\x|%|0x)[0-9a-f]{2}'
        if re.search(hex_pattern, text, re.IGNORECASE):
            threats.append('HEX_ENCODED_ATTACK')
        
        # Base64 encoding
        base64_pattern = r'[A-Za-z0-9+/]{20,}=*'
        if re.search(base64_pattern, text):
            # Check if it decodes to something suspicious
            import base64
            try:
                for match in re.findall(base64_pattern, text):
                    if len(match) > 30:
                        decoded = base64.b64decode(match + '==').decode('utf-8', errors='ignore')
                        if any(keyword in decoded.lower() for keyword in ['script', 'alert', 'onload']):
                            threats.append('BASE64_XSS_ATTACK')
                            break
            except:
                pass
        
        # URL encoding
        url_encoded_pattern = r'%[0-9a-f]{2}'
        if len(re.findall(url_encoded_pattern, text)) > 10:
            threats.append('URL_ENCODED_ATTACK')
        
        # Unicode encoding
        unicode_pattern = r'\\u[0-9a-f]{4}'
        if re.search(unicode_pattern, text, re.IGNORECASE):
            threats.append('UNICODE_ENCODED_ATTACK')
        
        return threats
    
    def _validate_user_agent(self, update_data: Dict) -> Tuple[bool, str]:
        """Validate user agent"""
        # Extract user agent from update if available
        # Telegram Bot API doesn't provide user agent directly
        # This would be implemented for webhook endpoints
        
        # Check for known bot/malicious user agents
        if 'message' in update_data and 'from' in update_data['message']:
            user = update_data['message']['from']
            
            # Check for suspicious usernames
            suspicious_usernames = ['bot', 'crawler', 'spider', 'scraper', 'hack']
            username = user.get('username', '').lower()
            if any(sus in username for sus in suspicious_usernames):
                return False, f"Suspicious username: {username}"
            
            # Check for suspicious first names
            first_name = user.get('first_name', '').lower()
            if any(sus in first_name for sus in ['bot', 'test', 'admin']):
                return False, f"Suspicious first name: {first_name}"
        
        return True, "User agent validation passed"
    
    def _validate_structure(self, update_data: Dict) -> Tuple[bool, str]:
        """Validate request structure"""
        # Check for required fields
        required_fields = ['update_id']
        
        for field in required_fields:
            if field not in update_data:
                return False, f"Missing required field: {field}"
        
        # Check message structure if present
        if 'message' in update_data:
            message = update_data['message']
            
            # Check for from field
            if 'from' not in message:
                return False, "Message missing 'from' field"
            
            # Check for valid user ID
            if 'id' not in message['from']:
                return False, "Message missing user ID"
            
            # Check for valid chat
            if 'chat' not in message:
                return False, "Message missing chat info"
            
            # Validate text length if present
            if 'text' in message:
                text = message['text']
                if len(text) > 4096:  # Telegram limit
                    return False, f"Text too long: {len(text)} chars"
                
                # Check for null bytes
                if '\x00' in text:
                    return False, "Text contains null bytes"
        
        return True, "Structure validation passed"
    
    def _detect_bot_behavior(self, user_id: int, update_data: Dict) -> Tuple[bool, str]:
        """Detect automated/bot behavior"""
        current_time = time.time()
        
        # Initialize user tracking
        if user_id not in self.suspicious_users:
            self.suspicious_users[user_id] = {
                'request_times': [],
                'similar_requests': [],
                'last_request': 0
            }
        
        user_data = self.suspicious_users[user_id]
        
        # Check request timing
        if user_data['last_request'] > 0:
            time_diff = current_time - user_data['last_request']
            
            # Too fast (less than 100ms between requests)
            if time_diff < 0.1:
                user_data['request_times'].append(current_time)
                
                # Check for pattern of fast requests
                if len(user_data['request_times']) > 10:
                    time_diffs = [
                        user_data['request_times'][i] - user_data['request_times'][i-1]
                        for i in range(1, len(user_data['request_times']))
                    ]
                    
                    # If all diffs are very similar, likely a bot
                    if all(0.09 < diff < 0.11 for diff in time_diffs):
                        return False, "Bot-like timing pattern detected"
            else:
                # Reset if not fast
                user_data['request_times'] = []
        
        user_data['last_request'] = current_time
        
        # Check for similar requests (message flooding)
        if 'message' in update_data and 'text' in update_data['message']:
            text = update_data['message']['text']
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            user_data['similar_requests'].append((current_time, text_hash))
            
            # Clean old entries
            user_data['similar_requests'] = [
                (t, h) for t, h in user_data['similar_requests']
                if current_time - t < 10  # Last 10 seconds
            ]
            
            # Check for duplicate messages
            hashes = [h for _, h in user_data['similar_requests']]
            if len(set(hashes)) < len(hashes) * 0.5:  # More than 50% duplicates
                return False, "Message flooding detected"
        
        return True, "No bot behavior detected"
    
    def _log_attack(self, user_id: int, attack_type: str, details: str):
        """Log API attack attempt"""
        try:
            self.db._log_security(user_id, f"API_ATTACK_{attack_type}", details)
        except:
            pass
        
        # Also log to console for monitoring
        logging.warning(f"API Attack detected: User {user_id}, Type: {attack_type}, Details: {details}")

# 🛡️ API SECURITY MIDDLEWARE
class APISecurityMiddleware:
    """Middleware for API security"""
    
    def __init__(self, validator: APIRequestValidator):
        self.validator = validator
        self.request_counter = 0
        self.attack_counter = 0
        
    async def process_update(self, update_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """Process and validate update"""
        self.request_counter += 1
        
        # Extract user ID
        user_id = self._extract_user_id(update_data)
        if not user_id:
            return False, {"error": "Invalid user ID"}
        
        # Validate request
        is_valid, message, validation_results = self.validator.validate_request(
            update_data, user_id
        )
        
        if not is_valid:
            self.attack_counter += 1
            
            # Log attack details
            attack_details = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'attack_type': message,
                'validation_results': validation_results,
                'update_id': update_data.get('update_id'),
                'blocked': True
            }
            
            # Log to database
            self.validator._log_attack(
                user_id, 
                f"BLOCKED_{message}", 
                json.dumps(validation_results, ensure_ascii=False)
            )
            
            return False, attack_details
        
        return True, None
    
    def _extract_user_id(self, update_data: Dict) -> Optional[int]:
        """Extract user ID from update"""
        try:
            if 'message' in update_data:
                return update_data['message']['from']['id']
            elif 'callback_query' in update_data:
                return update_data['callback_query']['from']['id']
            elif 'edited_message' in update_data:
                return update_data['edited_message']['from']['id']
            elif 'channel_post' in update_data:
                return update_data['channel_post']['sender_chat']['id']
            elif 'edited_channel_post' in update_data:
                return update_data['edited_channel_post']['sender_chat']['id']
        except (KeyError, TypeError):
            return None
        
        return None
    
    def get_security_stats(self) -> Dict:
        """Get security statistics"""
        return {
            'total_requests': self.request_counter,
            'blocked_attacks': self.attack_counter,
            'block_rate': (self.attack_counter / self.request_counter * 100) if self.request_counter > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }

# 🔐 TELEGRAM API SPECIFIC PROTECTION
class TelegramAPIProtector:
    """Telegram Bot API specific protections"""
    
    COMMAND_WHITELIST = [
        'start', 'help', 'premium', 'buy_premium', 'emoji', 'myemoji',
        'edit', 'delete', 'settings', 'info', 'stats'
    ]
    
    def __init__(self, database):
        self.db = database
        self.command_history = {}
        
    def validate_command(self, command: str, user_id: int) -> Tuple[bool, str]:
        """Validate bot command"""
        
        # Clean command
        command = command.lstrip('/').split('@')[0].lower()
        
        # Check if command is in whitelist
        if command not in self.COMMAND_WHITELIST:
            return False, f"Command not allowed: {command}"
        
        # Check for command flooding
        current_time = time.time()
        
        if user_id not in self.command_history:
            self.command_history[user_id] = []
        
        # Clean old commands
        self.command_history[user_id] = [
            t for t in self.command_history[user_id]
            if current_time - t < 30  # Last 30 seconds
        ]
        
        # Check rate
        if len(self.command_history[user_id]) >= 10:  # 10 commands in 30 seconds
            return False, "Command rate limit exceeded"
        
        # Add command
        self.command_history[user_id].append(current_time)
        
        return True, "Command valid"
    
    def validate_message_content(self, message_text: str, user_id: int) -> Tuple[bool, str, List[str]]:
        """Validate message content"""
        threats = []
        
        # Check length
        if len(message_text) > 4096:
            return False, "Message too long", ['MESSAGE_TOO_LONG']
        
        # Check for spam patterns
        spam_patterns = [
            (r'(http[s]?://)', 'URL_IN_MESSAGE'),
            (r'(@\w+)', 'MENTION_IN_MESSAGE'),
            (r'(#\w+)', 'HASHTAG_IN_MESSAGE'),
            (r'(\d{10,})', 'LONG_NUMBER_SEQUENCE'),  # Phone numbers, etc.
            (r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', 'EMAIL_IN_MESSAGE'),
            (r'(\b(win|free|money|cash|prize|lottery)\b)', 'SPAM_KEYWORDS'),
        ]
        
        for pattern, threat in spam_patterns:
            if re.search(pattern, message_text, re.IGNORECASE):
                threats.append(threat)
        
        # Check for repetition (spam detection)
        words = message_text.lower().split()
        if len(words) > 5:
            # Check for repeated words
            word_counts = {}
            for word in words:
                if len(word) > 3:  # Ignore short words
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            # If any word appears more than 3 times
            for word, count in word_counts.items():
                if count > 3:
                    threats.append('REPETITIVE_CONTENT')
                    break
        
        if threats:
            return False, f"Content validation failed: {threats[:3]}", threats
        
        return True, "Content valid", []
    
    def validate_callback_data(self, callback_data: str, user_id: int) -> Tuple[bool, str]:
        """Validate callback query data"""
        
        # Check length
        if len(callback_data) > 64:
            return False, "Callback data too long"
        
        # Check for allowed patterns
        allowed_patterns = [
            r'^emoji_[🔥✨🌟💎🚀🎯🏆🎨🦄🌈⭐💫☄️🎭🎪🎮🎲🎵🎶🎸]+$',
            r'^action_[a-z_]+$',
            r'^page_\d+$',
            r'^confirm_[a-z_]+$',
            r'^cancel_[a-z_]+$',
        ]
        
        for pattern in allowed_patterns:
            if re.match(pattern, callback_data):
                return True, "Callback data valid"
        
        # Check for injection attempts
        injection_patterns = [
            r'([<>\"\'&])',
            r'(javascript:)',
            r'(data:)',
            r'(vbscript:)',
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, callback_data, re.IGNORECASE):
                return False, f"Injection attempt in callback: {pattern}"
        
        return False, "Invalid callback data format"

# 🚀 MAIN API PROTECTION LAYER
class APISecurityLayer:
    """Main API security layer for Telegram Bot"""
    
    def __init__(self, database):
        self.db = database
        self.validator = APIRequestValidator(database)
        self.middleware = APISecurityMiddleware(self.validator)
        self.telegram_protector = TelegramAPIProtector(database)
        
    async def __call__(self, update, context):
        """Process update with security checks"""
        
        # Convert update to dict for validation
        update_dict = update.to_dict()
        
        # Validate with middleware
        is_valid, attack_details = await self.middleware.process_update(update_dict)
        
        if not is_valid:
            # Block the update
            logging.warning(f"Blocked update: {attack_details}")
            
            # Notify admin if it's a serious attack
            if attack_details.get('validation_results', {}).get('risk_score', 0) > 70:
                await self._notify_admin(attack_details)
            
            return  # Stop processing
        
        # Additional Telegram-specific validations
        if update.message and update.message.text:
            user_id = update.effective_user.id
            
            # Check if it's a command
            if update.message.text.startswith('/'):
                command_valid, command_msg = self.telegram_protector.validate_command(
                    update.message.text, user_id
                )
                
                if not command_valid:
                    logging.warning(f"Blocked command: User {user_id}, Command: {update.message.text}, Reason: {command_msg}")
                    
                    # Send error to user
                    await update.message.reply_text(
                        f"❌ Command blocked: {command_msg}\n"
                        f"Please contact @anonaltshelper if this is an error."
                    )
                    return
            
            # Validate message content
            content_valid, content_msg, content_threats = self.telegram_protector.validate_message_content(
                update.message.text, user_id
            )
            
            if not content_valid:
                logging.warning(f"Blocked message content: User {user_id}, Threats: {content_threats}")
                
                # Log to security database
                self.db._log_security(
                    user_id, 
                    "CONTENT_BLOCKED", 
                    f"Threats: {content_threats}, Message: {update.message.text[:100]}"
                )
                
                await update.message.reply_text(
                    "❌ Сообщение содержит подозрительный контент и было заблокировано."
                )
                return
        
        # Validate callback queries
        if update.callback_query:
            user_id = update.effective_user.id
            callback_data = update.callback_query.data
            
            callback_valid, callback_msg = self.telegram_protector.validate_callback_data(
                callback_data, user_id
            )
            
            if not callback_valid:
                logging.warning(f"Blocked callback: User {user_id}, Data: {callback_data}, Reason: {callback_msg}")
                
                await update.callback_query.answer(
                    "❌ This action has been blocked for security reasons.",
                    show_alert=True
                )
                return
        
        # If all checks pass, continue with normal processing
        # The update will be passed to other handlers
        
    async def _notify_admin(self, attack_details: Dict):
        """Notify admin about serious attack"""
        # In production, this would send a message to admin
        # For now, just log it
        logging.critical(f"🚨 SERIOUS ATTACK DETECTED: {json.dumps(attack_details, indent=2)}")
    
    def get_security_report(self) -> Dict:
        """Get security report"""
        stats = self.middleware.get_security_stats()
        
        # Add database security stats
        db_stats = self.db.get_security_report(1)  # Last hour
        
        report = {
            'api_security': stats,
            'database_security': db_stats,
            'timestamp': datetime.now().isoformat(),
            'protection_level': 'MAXIMUM',
            'status': 'OPERATIONAL'
        }
        
        return report
    
    def reset_security_counters(self):
        """Reset security counters (admin only)"""
        self.middleware.request_counter = 0
        self.middleware.attack_counter = 0
        self.validator.request_history = {}
        self.validator.suspicious_users = {}
        self.telegram_protector.command_history = {}
        
        logging.info("Security counters reset by admin")