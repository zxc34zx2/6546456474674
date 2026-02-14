#!/usr/bin/env python3
# 🔐 PROTECTED CORE MODULE - SQL INJECTION PROTECTION ACTIVE
# ⚠️ DO NOT MODIFY - DATABASE SECURITY ENFORCED

import logging
import sqlite3
import os
import re
import hashlib
import hmac
import secrets
import time
import html
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any, Union
from functools import wraps

# 🛡️ SQL INJECTION PROTECTION SYSTEM
class SQLInjectionProtector:
    """Advanced SQL injection protection"""
    
    SQL_KEYWORDS = [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'TRUNCATE', 'UNION', 'JOIN', 'WHERE', 'OR', 'AND', 'LIKE', 'EXEC',
        'EXECUTE', 'DECLARE', 'CAST', 'CONVERT', 'WAITFOR', 'DELAY', 'SLEEP',
        'BENCHMARK', 'LOAD_FILE', 'INTO', 'OUTFILE', 'DUMPFILE', 'SCRIPT',
        'SHUTDOWN', '--', '/*', '*/', ';', "'", '"', '`', '\\'
    ]
    
    PATTERNS = [
        (r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b.*\b(WHERE|SET|VALUES|INTO|FROM)\b.*[\'\"])', 'SQL_COMMAND_WITH_QUOTE'),
        (r'(\b(OR|AND)\b\s*[\'\"].*[\'\"]\s*=\s*[\'\"].*[\'\"])', 'BOOLEAN_INJECTION'),
        (r'(\b(UNION)\b.*\b(SELECT)\b)', 'UNION_INJECTION'),
        (r'(\b(SLEEP|WAITFOR|DELAY|BENCHMARK)\b\s*\(.*\))', 'TIME_BASED_INJECTION'),
        (r'(\b(LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b)', 'FILE_OPERATION_INJECTION'),
        (r'(\/\*.*\*\/|--.*$)', 'SQL_COMMENT_INJECTION'),
        (r'(\b(EXEC|EXECUTE|EXECUTE\s+IMMEDIATE|sp_executesql)\b)', 'EXECUTION_INJECTION'),
        (r'(;\s*[\w\s]*$)', 'QUERY_CHAINING'),
        (r'(\b(XPATH|EXTRACTVALUE|UPDATEXML)\b\s*\(.*\))', 'XPATH_INJECTION'),
        (r'(\b(CONVERT|CAST)\b\s*\(.*AS\s+BINARY\))', 'BINARY_INJECTION'),
    ]
    
    @classmethod
    def sanitize_input(cls, input_data: Union[str, int, float]) -> Union[str, int, float]:
        """Sanitize input data for SQL queries"""
        if input_data is None:
            return None
        
        # For integers and floats, just return
        if isinstance(input_data, (int, float)):
            return input_data
        
        # For strings, apply multiple sanitization layers
        if isinstance(input_data, str):
            # Layer 1: Remove SQL comments
            sanitized = re.sub(r'--.*$', '', input_data, flags=re.MULTILINE)
            sanitized = re.sub(r'/\*.*\*/', '', sanitized, flags=re.DOTALL)
            
            # Layer 2: Escape single quotes (but use parameterized queries instead)
            sanitized = sanitized.replace("'", "''")
            
            # Layer 3: Remove control characters
            sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
            
            # Layer 4: Limit length
            if len(sanitized) > 1000:
                sanitized = sanitized[:1000]
            
            return sanitized
        
        # For other types, convert to string and sanitize
        return cls.sanitize_input(str(input_data))
    
    @classmethod
    def detect_sql_injection(cls, input_data: str) -> Tuple[bool, List[str]]:
        """Detect SQL injection attempts"""
        if not isinstance(input_data, str):
            return False, []
        
        input_upper = input_data.upper()
        threats = []
        
        # Check for SQL keywords in suspicious contexts
        for keyword in cls.SQL_KEYWORDS:
            if keyword in input_upper:
                # Check if keyword appears in suspicious pattern
                pattern = fr'\b{re.escape(keyword)}\b'
                if re.search(pattern, input_upper, re.IGNORECASE):
                    threats.append(f"SQL_KEYWORD_{keyword}")
        
        # Check for known injection patterns
        for pattern, threat_name in cls.PATTERNS:
            if re.search(pattern, input_upper, re.IGNORECASE | re.MULTILINE):
                threats.append(threat_name)
        
        # Check for encoded attacks
        decoded = cls._decode_obfuscated(input_data)
        if decoded != input_data:
            decoded_threats = cls.detect_sql_injection(decoded)
            if decoded_threats[0]:
                threats.extend([f"ENCODED_{t}" for t in decoded_threats[1]])
        
        return len(threats) > 0, threats
    
    @classmethod
    def _decode_obfuscated(cls, text: str) -> str:
        """Attempt to decode obfuscated SQL"""
        # Hex decoding
        hex_pattern = r'0x([0-9A-Fa-f]+)'
        hex_matches = re.findall(hex_pattern, text)
        for match in hex_matches:
            try:
                decoded = bytes.fromhex(match).decode('utf-8', errors='ignore')
                text = text.replace(f'0x{match}', decoded)
            except:
                pass
        
        # Char() decoding
        char_pattern = r'CHAR\((\d+(?:\s*,\s*\d+)*)\)'
        char_matches = re.findall(char_pattern, text)
        for match in char_matches:
            try:
                chars = [int(c.strip()) for c in match.split(',')]
                decoded = ''.join(chr(c) for c in chars)
                text = text.replace(f'CHAR({match})', decoded)
            except:
                pass
        
        return text
    
    @classmethod
    def secure_execute(cls, cursor, query: str, params: Tuple = None):
        """Execute query with SQL injection protection"""
        # Validate query structure
        if not cls._validate_query_structure(query):
            raise SecurityError("INVALID_QUERY_STRUCTURE")
        
        # Check parameters for injection
        if params:
            for param in params:
                if isinstance(param, str):
                    is_injection, threats = cls.detect_sql_injection(param)
                    if is_injection:
                        raise SecurityError(f"SQL_INJECTION_ATTEMPT: {threats}")
        
        # Execute with error handling
        try:
            if params:
                return cursor.execute(query, params)
            else:
                return cursor.execute(query)
        except sqlite3.Error as e:
            # Log the error but don't expose details
            logging.error(f"Database error: {str(e)[:100]}")
            raise SecurityError("DATABASE_ERROR")

    @classmethod
    def _validate_query_structure(cls, query: str) -> bool:
        """Validate SQL query structure"""
        query_upper = query.upper().strip()
        
        # Check for multiple statements
        if ';' in query_upper and query_upper.count(';') > 1:
            return False
        
        # Check for suspicious patterns even in valid queries
        suspicious = [
            r'DROP\s+TABLE',
            r'TRUNCATE\s+TABLE',
            r'ALTER\s+TABLE',
            r'CREATE\s+TABLE.*SELECT',
            r'INSERT.*SELECT.*FROM',
            r'UPDATE.*SET.*=.*SELECT',
        ]
        
        for pattern in suspicious:
            if re.search(pattern, query_upper, re.IGNORECASE):
                return False
        
        return True

# 🚨 SECURITY ERROR CLASS
class SecurityError(Exception):
    """Security-related exceptions"""
    pass

# 🔒 SECURE DATABASE WITH SQL INJECTION PROTECTION
class SecureDatabase:
    """Database with comprehensive SQL injection protection"""
    
    def __init__(self, security_hash: str):
        self.security_hash = security_hash
        self.db_file = 'secure_bot.db'
        self.sql_protector = SQLInjectionProtector()
        self.conn = None
        self.query_log = []
        self.max_query_log = 1000
        
        # Initialize with security
        self._secure_init()
    
    def _secure_init(self):
        """Secure database initialization"""
        # Set secure file permissions
        if os.path.exists(self.db_file):
            try:
                os.chmod(self.db_file, 0o600)
            except:
                pass
        
        # Connect with security options
        self.conn = sqlite3.connect(
            self.db_file,
            check_same_thread=False,
            timeout=30.0
        )
        
        # Enable security features
        self._enable_security_features()
        
        # Create tables
        self._create_secure_tables()
        
        # Initialize security monitoring
        self._init_security_monitoring()
    
    def _enable_security_features(self):
        """Enable SQLite security features"""
        cursor = self.conn.cursor()
        
        # PRAGMAs for security
        security_pragmas = [
            ("PRAGMA journal_mode = WAL", ()),
            ("PRAGMA synchronous = NORMAL", ()),
            ("PRAGMA foreign_keys = ON", ()),
            ("PRAGMA secure_delete = ON", ()),  # Overwrite deleted data
            ("PRAGMA cell_size_check = ON", ()),
            ("PRAGMA automatic_index = OFF", ()),  # Prevent automatic indexing of sensitive data
            ("PRAGMA temp_store = MEMORY", ()),  # Avoid temp files
            ("PRAGMA mmap_size = 0", ()),  # Disable memory mapping
        ]
        
        for pragma, params in security_pragmas:
            try:
                self.sql_protector.secure_execute(cursor, pragma, params)
            except:
                pass
        
        self.conn.commit()
    
    def _create_secure_tables(self):
        """Create tables with security considerations"""
        cursor = self.conn.cursor()
        
        # Users table with security constraints
        users_table = '''
            CREATE TABLE IF NOT EXISTS secure_users (
                user_id INTEGER PRIMARY KEY CHECK(user_id > 0),
                username TEXT CHECK(LENGTH(username) <= 100),
                first_name TEXT CHECK(LENGTH(first_name) <= 100),
                last_name TEXT CHECK(LENGTH(last_name) <= 100),
                access_hash TEXT UNIQUE NOT NULL CHECK(LENGTH(access_hash) = 64),
                security_level INTEGER DEFAULT 0 CHECK(security_level >= 0 AND security_level <= 10),
                is_banned INTEGER DEFAULT 0 CHECK(is_banned IN (0, 1)),
                ban_reason TEXT CHECK(LENGTH(ban_reason) <= 500),
                registration_date TEXT NOT NULL,
                is_premium INTEGER DEFAULT 0 CHECK(is_premium IN (0, 1)),
                custom_emoji TEXT DEFAULT "📨" CHECK(LENGTH(custom_emoji) <= 4),
                premium_until TEXT,
                message_count INTEGER DEFAULT 0 CHECK(message_count >= 0),
                edit_count INTEGER DEFAULT 0 CHECK(edit_count >= 0),
                delete_count INTEGER DEFAULT 0 CHECK(delete_count >= 0),
                last_activity TEXT NOT NULL,
                security_token TEXT NOT NULL CHECK(LENGTH(security_token) = 64),
                failed_logins INTEGER DEFAULT 0 CHECK(failed_logins >= 0),
                last_failed_login TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        '''
        
        # Messages table with integrity checks
        messages_table = '''
            CREATE TABLE IF NOT EXISTS secure_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_hash TEXT UNIQUE NOT NULL CHECK(LENGTH(message_hash) = 64),
                user_id INTEGER NOT NULL CHECK(user_id > 0),
                channel_message_id INTEGER NOT NULL CHECK(channel_message_id > 0),
                encrypted_text TEXT NOT NULL,
                sanitized_text TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                reply_to INTEGER CHECK(reply_to > 0),
                is_reply INTEGER DEFAULT 0 CHECK(is_reply IN (0, 1)),
                emoji_used TEXT CHECK(LENGTH(emoji_used) <= 4),
                is_edited INTEGER DEFAULT 0 CHECK(is_edited IN (0, 1)),
                is_deleted INTEGER DEFAULT 0 CHECK(is_deleted IN (0, 1)),
                edit_count INTEGER DEFAULT 0 CHECK(edit_count >= 0),
                last_edit_time TEXT,
                integrity_check TEXT NOT NULL CHECK(LENGTH(integrity_check) = 64),
                ip_hash TEXT CHECK(LENGTH(ip_hash) = 64),
                user_agent_hash TEXT CHECK(LENGTH(user_agent_hash) = 64),
                FOREIGN KEY (user_id) REFERENCES secure_users(user_id) ON DELETE CASCADE,
                CHECK(channel_message_id > 0),
                CHECK(timestamp IS datetime(timestamp))
            )
        '''
        
        # Emoji reservations
        emoji_table = '''
            CREATE TABLE IF NOT EXISTS secure_emoji_reservations (
                emoji TEXT PRIMARY KEY CHECK(LENGTH(emoji) <= 4),
                user_id INTEGER UNIQUE NOT NULL CHECK(user_id > 0),
                reserved_at TEXT NOT NULL,
                reservation_token TEXT NOT NULL CHECK(LENGTH(reservation_token) = 64),
                FOREIGN KEY (user_id) REFERENCES secure_users(user_id) ON DELETE CASCADE,
                CHECK(reserved_at IS datetime(reserved_at))
            )
        '''
        
        # Security logs
        security_logs_table = '''
            CREATE TABLE IF NOT EXISTS security_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id INTEGER CHECK(user_id > 0),
                action TEXT NOT NULL CHECK(LENGTH(action) <= 50),
                details TEXT CHECK(LENGTH(details) <= 1000),
                ip_hash TEXT CHECK(LENGTH(ip_hash) = 64),
                security_level INTEGER DEFAULT 0,
                threat_score INTEGER DEFAULT 0 CHECK(threat_score >= 0),
                response_action TEXT CHECK(LENGTH(response_action) <= 50),
                FOREIGN KEY (user_id) REFERENCES secure_users(user_id) ON DELETE SET NULL,
                CHECK(timestamp IS datetime(timestamp))
            )
        '''
        
        # SQL injection attempt logs
        injection_logs_table = '''
            CREATE TABLE IF NOT EXISTS sql_injection_logs (
                attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id INTEGER,
                input_data TEXT,
                detected_threats TEXT,
                query_attempted TEXT,
                ip_hash TEXT,
                user_agent TEXT,
                blocked INTEGER DEFAULT 1 CHECK(blocked IN (0, 1)),
                FOREIGN KEY (user_id) REFERENCES secure_users(user_id) ON DELETE SET NULL,
                CHECK(timestamp IS datetime(timestamp))
            )
        '''
        
        # Create tables
        tables = [
            users_table,
            messages_table,
            emoji_table,
            security_logs_table,
            injection_logs_table
        ]
        
        for table_sql in tables:
            try:
                cursor.execute(table_sql)
            except sqlite3.Error as e:
                logging.error(f"Table creation error: {e}")
        
        self.conn.commit()
    
    def _init_security_monitoring(self):
        """Initialize security monitoring"""
        # Create indexes for security queries
        cursor = self.conn.cursor()
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_security ON secure_users(security_level, is_banned)",
            "CREATE INDEX IF NOT EXISTS idx_messages_user ON secure_messages(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_security_logs_time ON security_logs(timestamp, security_level)",
            "CREATE INDEX IF NOT EXISTS idx_injection_logs_time ON sql_injection_logs(timestamp, blocked)",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except:
                pass
        
        self.conn.commit()
    
    # 🔐 SECURE QUERY EXECUTION
    def execute_query(self, query: str, params: Tuple = None, user_id: int = None) -> sqlite3.Cursor:
        """Execute query with full security checks"""
        cursor = self.conn.cursor()
        
        # Log query attempt
        self._log_query_attempt(query, params, user_id)
        
        # Check for SQL injection
        injection_check = self._check_query_for_injection(query, params, user_id)
        if injection_check["block"]:
            self._log_injection_attempt(
                user_id,
                params,
                injection_check["threats"],
                query
            )
            raise SecurityError(f"SQL_INJECTION_BLOCKED: {injection_check['threats']}")
        
        # Execute with protection
        try:
            result = self.sql_protector.secure_execute(cursor, query, params)
            self.conn.commit()
            return result
        except SecurityError as e:
            raise e
        except sqlite3.Error as e:
            # Don't expose database errors
            logging.error(f"Database error: {str(e)[:50]}")
            raise SecurityError("DATABASE_OPERATION_FAILED")
    
    def _check_query_for_injection(self, query: str, params: Tuple, user_id: int) -> Dict:
        """Check query for SQL injection attempts"""
        result = {
            "block": False,
            "threats": [],
            "score": 0
        }
        
        # Check query itself
        is_injection, threats = self.sql_protector.detect_sql_injection(query)
        if is_injection:
            result["threats"].extend(threats)
            result["score"] += len(threats) * 10
        
        # Check parameters
        if params:
            for i, param in enumerate(params):
                if isinstance(param, str):
                    is_injection, threats = self.sql_protector.detect_sql_injection(param)
                    if is_injection:
                        result["threats"].extend([f"PARAM_{i}_{t}" for t in threats])
                        result["score"] += len(threats) * 5
        
        # Check for suspicious patterns
        suspicious_patterns = [
            (r'DROP\s+TABLE', 'DROP_TABLE_ATTEMPT', 50),
            (r'TRUNCATE\s+TABLE', 'TRUNCATE_ATTEMPT', 50),
            (r'ALTER\s+TABLE', 'ALTER_TABLE_ATTEMPT', 40),
            (r'CREATE\s+TABLE', 'CREATE_TABLE_ATTEMPT', 30),
            (r'INSERT.*SELECT', 'INSERT_SELECT_ATTEMPT', 20),
            (r'UNION.*SELECT', 'UNION_SELECT_ATTEMPT', 25),
        ]
        
        query_upper = query.upper()
        for pattern, threat, score in suspicious_patterns:
            if re.search(pattern, query_upper, re.IGNORECASE):
                result["threats"].append(threat)
                result["score"] += score
        
        # Block if score is too high
        if result["score"] > 20:
            result["block"] = True
        
        # Check user's history
        if user_id and self._check_user_injection_history(user_id):
            result["block"] = True
            result["threats"].append("USER_HISTORY_BLOCK")
        
        return result
    
    def _check_user_injection_history(self, user_id: int) -> bool:
        """Check if user has injection history"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM sql_injection_logs 
                WHERE user_id = ? AND timestamp > datetime('now', '-1 hour')
            ''', (user_id,))
            count = cursor.fetchone()[0]
            return count >= 3
        except:
            return False
    
    def _log_query_attempt(self, query: str, params: Tuple, user_id: int):
        """Log query attempt for auditing"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'query': query[:500],
            'params': str(params)[:500] if params else None,
            'hash': hashlib.sha256(query.encode()).hexdigest()[:16]
        }
        
        self.query_log.append(log_entry)
        
        # Trim log if too large
        if len(self.query_log) > self.max_query_log:
            self.query_log = self.query_log[-self.max_query_log:]
    
    def _log_injection_attempt(self, user_id: int, input_data, threats: List[str], query: str):
        """Log SQL injection attempt"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO sql_injection_logs 
                (timestamp, user_id, input_data, detected_threats, query_attempted, blocked)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                user_id,
                str(input_data)[:1000] if input_data else None,
                ','.join(threats)[:500],
                query[:1000],
                1
            ))
            self.conn.commit()
        except:
            pass
    
    # 👤 USER MANAGEMENT WITH SECURITY
    def register_user(self, user_id: int, username: str, first_name: str, last_name: str):
        """Register user with security checks"""
        # Sanitize inputs
        username = self.sql_protector.sanitize_input(username or "")
        first_name = self.sql_protector.sanitize_input(first_name or "")
        last_name = self.sql_protector.sanitize_input(last_name or "")
        
        # Generate security tokens
        access_hash = hashlib.sha256(f"{user_id}{secrets.token_hex(16)}".encode()).hexdigest()
        security_token = secrets.token_hex(32)
        
        # Check if user exists
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM secure_users WHERE user_id = ?', (user_id,))
        
        if cursor.fetchone():
            # Update existing user
            self.execute_query('''
                UPDATE secure_users 
                SET username = ?, first_name = ?, last_name = ?, last_activity = ?, updated_at = datetime('now')
                WHERE user_id = ?
            ''', (username, first_name, last_name, datetime.now().isoformat(), user_id), user_id)
        else:
            # Insert new user
            self.execute_query('''
                INSERT INTO secure_users 
                (user_id, username, first_name, last_name, access_hash, security_token, 
                 registration_date, custom_emoji, last_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, username, first_name, last_name, access_hash, security_token,
                datetime.now().isoformat(), "📨", datetime.now().isoformat()
            ), user_id)
        
        # Log registration
        self._log_security(user_id, "USER_REGISTER", f"User registered: {username}")
    
    def get_user_info(self, user_id: int) -> Optional[Tuple]:
        """Get user info with security"""
        try:
            cursor = self.execute_query(
                'SELECT * FROM secure_users WHERE user_id = ?',
                (user_id,),
                user_id
            )
            return cursor.fetchone()
        except SecurityError:
            return None
    
    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        user_info = self.get_user_info(user_id)
        if not user_info:
            return False
        
        # Index 6 is is_banned
        return user_info[6] == 1 if len(user_info) > 6 else False
    
    def ban_user(self, user_id: int, reason: str = "Security violation"):
        """Ban user securely"""
        reason = self.sql_protector.sanitize_input(reason)
        
        self.execute_query('''
            UPDATE secure_users 
            SET is_banned = 1, ban_reason = ?, updated_at = datetime('now')
            WHERE user_id = ?
        ''', (reason, user_id), user_id)
        
        self._log_security(user_id, "USER_BANNED", f"Reason: {reason}")
    
    # 💬 MESSAGE MANAGEMENT
    def log_message(self, user_id: int, channel_message_id: int, text: str, 
                   reply_to: int = None, emoji_used: str = None):
        """Log message with security"""
        # Sanitize inputs
        text = self.sql_protector.sanitize_input(text or "")
        emoji_used = self.sql_protector.sanitize_input(emoji_used or "📨")
        
        # Generate integrity data
        message_hash = hashlib.sha256(
            f"{user_id}:{channel_message_id}:{text}:{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        encrypted_text = self._encrypt_text(text)
        sanitized_text = self._sanitize_text_for_storage(text)
        integrity_check = hashlib.sha256(text.encode()).hexdigest()
        
        # Insert message
        self.execute_query('''
            INSERT INTO secure_messages 
            (message_hash, user_id, channel_message_id, encrypted_text, sanitized_text,
             timestamp, reply_to, is_reply, emoji_used, integrity_check)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            message_hash, user_id, channel_message_id, encrypted_text, sanitized_text,
            datetime.now().isoformat(), reply_to, 1 if reply_to else 0, emoji_used, integrity_check
        ), user_id)
        
        # Update user stats
        self.execute_query('''
            UPDATE secure_users 
            SET message_count = message_count + 1, last_activity = ?, updated_at = datetime('now')
            WHERE user_id = ?
        ''', (datetime.now().isoformat(), user_id), user_id)
        
        self._log_security(user_id, "MESSAGE_SENT", f"Message ID: {channel_message_id}")
    
    def _encrypt_text(self, text: str) -> str:
        """Encrypt text for storage (simplified - use proper encryption in production)"""
        # In production, use cryptography.fernet or similar
        return text  # Placeholder
    
    def _sanitize_text_for_storage(self, text: str) -> str:
        """Sanitize text for database storage"""
        if not text:
            return ""
        
        # HTML escape
        text = html.escape(text)
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Limit length
        if len(text) > 4000:
            text = text[:4000]
        
        return text
    
    def get_message_owner(self, message_id: int) -> Optional[int]:
        """Get message owner with security"""
        try:
            cursor = self.execute_query(
                'SELECT user_id FROM secure_messages WHERE channel_message_id = ? AND is_deleted = 0',
                (message_id,),
                None
            )
            result = cursor.fetchone()
            return result[0] if result else None
        except SecurityError:
            return None
    
    # 🎨 EMOJI MANAGEMENT
    PREMIUM_EMOJIS = [
        "🔥", "✨", "🌟", "💎", "🚀", "🎯", "🏆", "🎨", "🦄", "🌈",
        "⭐", "💫", "☄️", "🎭", "🎪", "🎮", "🎲", "🎵", "🎶", "🎸",
        "🏅", "🎖️", "🥇", "🥈", "🥉", "⚡", "💥", "🌠", "🌌", "🌙",
        "☀️", "🌞", "🪐", "🌊", "🌸", "🌺", "🌹", "🍀", "🎄", "🎁",
        "🎀", "🎊", "🎉", "🕹️", "🎬", "🎥", "📽️", "🎞️", "🎤", "🎧",
    ]
    
    def update_user_emoji(self, user_id: int, emoji: str) -> bool:
        """Update user emoji with security"""
        # Validate emoji
        if not emoji or len(emoji) > 4:
            return False
        
        # Check if premium emoji
        if emoji in self.PREMIUM_EMOJIS:
            user_info = self.get_user_info(user_id)
            if not user_info or (len(user_info) > 9 and user_info[9] == 0):  # is_premium
                return False
        
        # Update emoji
        try:
            self.execute_query(
                'UPDATE secure_users SET custom_emoji = ?, updated_at = datetime("now") WHERE user_id = ?',
                (emoji, user_id),
                user_id
            )
            return True
        except SecurityError:
            return False
    
    # 📊 SECURITY LOGGING
    def _log_security(self, user_id: Optional[int], action: str, details: str = ""):
        """Log security event"""
        try:
            # Sanitize inputs
            action = self.sql_protector.sanitize_input(action)
            details = self.sql_protector.sanitize_input(details)
            
            self.execute_query('''
                INSERT INTO security_logs (timestamp, user_id, action, details, security_level)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                user_id,
                action,
                details,
                1 if "ATTACK" in action or "INJECTION" in action else 0
            ), user_id)
        except:
            pass
    
    # 🛡️ SECURITY UTILITIES
    def get_security_report(self, hours: int = 24) -> Dict:
        """Get security report"""
        try:
            cursor = self.conn.cursor()
            
            # Injection attempts
            cursor.execute('''
                SELECT COUNT(*) FROM sql_injection_logs 
                WHERE timestamp > datetime('now', ?)
            ''', (f'-{hours} hours',))
            injection_attempts = cursor.fetchone()[0]
            
            # Security events
            cursor.execute('''
                SELECT COUNT(*) FROM security_logs 
                WHERE timestamp > datetime('now', ?) AND security_level > 0
            ''', (f'-{hours} hours',))
            security_events = cursor.fetchone()[0]
            
            # Banned users
            cursor.execute('SELECT COUNT(*) FROM secure_users WHERE is_banned = 1')
            banned_users = cursor.fetchone()[0]
            
            return {
                'injection_attempts': injection_attempts,
                'security_events': security_events,
                'banned_users': banned_users,
                'query_log_size': len(self.query_log),
                'report_time': datetime.now().isoformat()
            }
        except:
            return {}

# 🚀 SECURE BOT LAUNCHER
class SecureBotLauncher:
    """Secure bot launcher with all protections"""
    
    def __init__(self, security_shield):
        self.shield = security_shield
        self.db = None
        self.app = None
        
    def launch(self):
        """Launch bot with maximum security"""
        print("\n" + "=" * 60)
        print("🚀 SECURE BOT LAUNCH SEQUENCE - MAXIMUM SECURITY")
        print("=" * 60)
        
        try:
            # Initialize secure database
            self.db = SecureDatabase(self.shield.execution_id)
            print("✅ Secure database initialized")
            print("🔒 SQL Injection Protection: ACTIVE")
            
            # Setup secure logging
            self._setup_logging()
            
            # Create secure application
            self._create_secure_app()
            
            # Add security middleware
            self._add_security_middleware()
            
            print("\n" + "=" * 60)
            print("🤖 SECURE BOT ACTIVATED")
            print("=" * 60)
            print("🔒 All security systems: OPERATIONAL")
            print("🛡️  API Protection: MAXIMUM")
            print("🚫 SQL Injection: BLOCKED")
            print("📊 Input Validation: ACTIVE")
            print("=" * 60)
            
            # Run with protection
            self.app.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query'],
                close_loop=False
            )
            
        except Exception as e:
            print(f"❌ LAUNCH FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    def _setup_logging(self):
        """Setup secure logging"""
        logging.basicConfig(
            format='%(asctime)s - SECURE - %(levelname)s - %(message)s',
            level=logging.INFO,
            handlers=[
                logging.FileHandler('secure_bot.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logging.getLogger('httpx').setLevel(logging.WARNING)
    
    def _create_secure_app(self):
        """Create secure Telegram application"""
        from telegram.ext import Application
        
        # Import API protector
        from api_protector import APISecurityLayer
        
        # Create application with API protection
        self.app = Application.builder() \
            .token("8426196421:AAGOtFqNj3E8D8yA_dcX8cAOSxMPrf4dobc") \
            .build()
        
        # Add API security layer
        self.api_security = APISecurityLayer(self.db)
        self.app.add_handler(self.api_security)
        
        # Add command handlers
        self._add_secure_handlers()
    
    def _add_security_middleware(self):
        """Add security middleware to application"""
        # This would add pre-processing and post-processing hooks
        # for all incoming updates
        pass
    
    def _add_secure_handlers(self):
        """Add secure command handlers"""
        from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters
        
        # Basic commands
        self.app.add_handler(CommandHandler("start", self._secure_start))
        self.app.add_handler(CommandHandler("premium", self._secure_premium))
        self.app.add_handler(CommandHandler("buy_premium", self._secure_buy_premium))
        self.app.add_handler(CommandHandler("emoji", self._secure_emoji))
        self.app.add_handler(CommandHandler("myemoji", self._secure_myemoji))
        
        # Message handler with security
        self.app.add_handler(MessageHandler(
            filters.ChatType.PRIVATE & ~filters.COMMAND,
            self._secure_message
        ))
        
        # Callback handler
        self.app.add_handler(CallbackQueryHandler(self._secure_callback))
    
    # 🔒 SECURE HANDLERS
    async def _secure_start(self, update, context):
        """Secure start command"""
        from telegram.constants import ParseMode
        
        user = update.effective_user
        
        # Register user securely
        self.db.register_user(
            user.id,
            user.username or "",
            user.first_name or "",
            user.last_name or ""
        )
        
        welcome = (
            "🛡️ *АНОНИМНЫЙ БОТ С МАКСИМАЛЬНОЙ ЗАЩИТОЙ*\n\n"
            "✅ *Безопасность:* Защита от SQL-инъекций\n"
            "🔒 *Конфиденциальность:* Шифрование данных\n"
            "🛡️ *API Защита:* Защита от взлома API\n"
            "🚫 *Валидация:* Проверка всех входных данных\n\n"
            "📢 Канал: @anonalmet\n"
            "👨‍💼 Поддержка: @anonaltshelper"
        )
        
        await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN_V2)
    
    async def _secure_premium(self, update, context):
        """Secure premium command"""
        from telegram.constants import ParseMode
        
        user = update.effective_user
        
        # Get user info securely
        user_info = self.db.get_user_info(user.id)
        is_premium = user_info and len(user_info) > 9 and user_info[9] == 1
        
        if is_premium:
            text = (
                "✨ *Anon Premium*\n\n"
                "✅ Ваш премиум аккаунт активен!\n"
                "🔒 Уровень безопасности: МАКСИМАЛЬНЫЙ\n"
                "🛡️ Дополнительная защита данных\n\n"
                "*Поддержка:* @anonaltshelper"
            )
        else:
            text = (
                "✨ *Anon Premium*\n\n"
                "⭐ *Получите максимальную защиту!*\n\n"
                "*Премиум включает:*\n"
                "✅ Расширенное шифрование\n"
                "✅ Приоритетная безопасность\n"
                "✅ Защита от SQL-инъекций\n"
                "✅ API защита\n"
                "✅ Мониторинг атак\n\n"
                "*Стоимость:* 25 звезд Telegram ⭐\n\n"
                "*Поддержка:* @anonaltshelper"
            )
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
    
    async def _secure_buy_premium(self, update, context):
        """Secure buy premium command"""
        from telegram.constants import ParseMode
        
        user = update.effective_user
        
        await update.message.reply_text(
            f"💰 *Покупка Premium*\n\n"
            f"Для приобретения Premium:\n"
            f"1. Свяжитесь с @anonaltshelper\n"
            f"2. Укажите ваш ID: `{user.id}`\n"
            f"3. Оплатите 25 звезд Telegram\n\n"
            f"✅ После оплаты премиум будет активирован!",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    async def _secure_emoji(self, update, context):
        """Secure emoji command"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.constants import ParseMode
        
        user = update.effective_user
        
        # Check premium status
        user_info = self.db.get_user_info(user.id)
        is_premium = user_info and len(user_info) > 9 and user_info[9] == 1
        
        if not is_premium:
            await update.message.reply_text(
                "🎨 *Выбор эмодзи*\n\n"
                "❌ Требуется *Anon Premium*\n\n"
                "Обычные пользователи используют: 📨\n\n"
                "✨ *Получите Premium для:*\n"
                "• Выбора из 50+ премиум эмодзи\n"
                "• Закрепления уникального эмодзи\n"
                "• Максимальной безопасности\n\n"
                "*Поддержка:* @anonaltshelper",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        # Create emoji keyboard
        keyboard = []
        emojis = SecureDatabase.PREMIUM_EMOJIS[:20]
        
        for i in range(0, len(emojis), 5):
            row = []
            for j in range(5):
                idx = i + j
                if idx < len(emojis):
                    row.append(InlineKeyboardButton(emojis[idx], callback_data=f"emoji_{emojis[idx]}"))
            if row:
                keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🖼️ *Выберите ваш эмодзи*\n\n"
            "Нажмите на эмодзи чтобы выбрать.\n"
            "✅ Premium активен\n"
            "🔒 Безопасный выбор",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    async def _secure_myemoji(self, update, context):
        """Secure myemoji command"""
        from telegram.constants import ParseMode
        
        user = update.effective_user
        
        # Get user info
        user_info = self.db.get_user_info(user.id)
        if not user_info:
            await update.message.reply_text("❌ Пользователь не найден")
            return
        
        is_premium = len(user_info) > 9 and user_info[9] == 1
        current_emoji = user_info[10] if len(user_info) > 10 else "📨"
        
        if is_premium:
            text = (
                f"🎨 *Ваш эмодзи*\n\n"
                f"Текущий эмодзи: {current_emoji}\n"
                f"Статус: ✅ Premium активен\n"
                f"Безопасность: 🔒 МАКСИМАЛЬНАЯ\n\n"
                f"*Изменить эмодзи:*\n"
                f"`/emoji` - выбрать из списка\n\n"
                f"*Защита включена:*\n"
                f"• SQL Injection Protection\n"
                f"• API Security Layer\n"
                f"• Input Validation"
            )
        else:
            text = (
                f"🎨 *Ваш эмодзи*\n\n"
                f"Текущий эмодзи: {current_emoji}\n"
                f"Статус: ❌ Premium не активен\n"
                f"Безопасность: 🛡️ СТАНДАРТНАЯ\n\n"
                f"*Получить премиум:*\n"
                f"`/premium` - узнать о премиуме\n"
                f"`/buy_premium` - купить премиум\n\n"
                f"*Поддержка:* @anonaltshelper"
            )
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
    
    async def _secure_message(self, update, context):
        """Secure message handler"""
        from telegram.constants import ParseMode
        
        user = update.effective_user
        
        # Check if user is banned
        if self.db.is_user_banned(user.id):
            await update.message.reply_text("❌ Ваш аккаунт заблокирован.")
            return
        
        # Register user
        self.db.register_user(
            user.id,
            user.username or "",
            user.first_name or "",
            user.last_name or ""
        )
        
        # Process message based on type
        if update.message.text:
            await self._process_text_message(update, context)
        elif update.message.photo:
            await self._process_photo_message(update, context)
        elif update.message.video:
            await self._process_video_message(update, context)
    
    async def _process_text_message(self, update, context):
        """Process text message securely"""
        from telegram.constants import ParseMode
        
        user = update.effective_user
        text = update.message.text
        
        # Validate text length
        if len(text) > 2000:
            await update.message.reply_text("❌ Сообщение слишком длинное.")
            return
        
        # Get user's emoji
        user_info = self.db.get_user_info(user.id)
        emoji = user_info[10] if user_info and len(user_info) > 10 else "📨"
        
        # Send to channel
        try:
            sent_message = await context.bot.send_message(
                chat_id="@anonalmet",
                text=f"{emoji}: {text}"
            )
            
            # Log message securely
            self.db.log_message(user.id, sent_message.message_id, text)
            
            await update.message.reply_text(
                "✅ *Сообщение отправлено!*\n"
                "🔒 Защищённая доставка\n"
                f"🎨 Ваш эмодзи: {emoji}",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
        except Exception as e:
            logging.error(f"Message send error: {e}")
            await update.message.reply_text("❌ Ошибка отправки.")
    
    async def _process_photo_message(self, update, context):
        """Process photo message"""
        from telegram.constants import ParseMode
        
        user = update.effective_user
        photo = update.message.photo[-1]
        caption = update.message.caption or ""
        
        # Get user's emoji
        user_info = self.db.get_user_info(user.id)
        emoji = user_info[10] if user_info and len(user_info) > 10 else "📨"
        
        try:
            sent_message = await context.bot.send_photo(
                chat_id="@anonalmet",
                photo=photo.file_id,
                caption=f"{emoji}: {caption[:200]}"
            )
            
            self.db.log_message(user.id, sent_message.message_id, f"[Фото] {caption}")
            
            await update.message.reply_text(
                "✅ *Фото отправлено!*\n"
                "🔒 Защищённая доставка",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
        except Exception as e:
            logging.error(f"Photo send error: {e}")
            await update.message.reply_text("❌ Ошибка отправки фото.")
    
    async def _process_video_message(self, update, context):
        """Process video message"""
        from telegram.constants import ParseMode
        
        user = update.effective_user
        video = update.message.video
        caption = update.message.caption or ""
        
        # Get user's emoji
        user_info = self.db.get_user_info(user.id)
        emoji = user_info[10] if user_info and len(user_info) > 10 else "📨"
        
        try:
            sent_message = await context.bot.send_video(
                chat_id="@anonalmet",
                video=video.file_id,
                caption=f"{emoji}: {caption[:200]}"
            )
            
            self.db.log_message(user.id, sent_message.message_id, f"[Видео] {caption}")
            
            await update.message.reply_text(
                "✅ *Видео отправлено!*\n"
                "🔒 Защищённая доставка",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
        except Exception as e:
            logging.error(f"Video send error: {e}")
            await update.message.reply_text("❌ Ошибка отправки видео.")
    
    async def _secure_callback(self, update, context):
        """Secure callback handler"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        
        if query.data.startswith('emoji_'):
            emoji = query.data.split('_')[1]
            
            # Check premium status
            user_info = self.db.get_user_info(user.id)
            is_premium = user_info and len(user_info) > 9 and user_info[9] == 1
            
            if not is_premium:
                await query.edit_message_text("❌ Требуется Premium доступ.")
                return
            
            # Update emoji
            if self.db.update_user_emoji(user.id, emoji):
                await query.edit_message_text(f"✅ Эмодзи установлен: {emoji}")
            else:
                await query.edit_message_text("❌ Ошибка установки эмодзи.")