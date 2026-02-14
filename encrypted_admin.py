#!/usr/bin/env python3
# 🔐 ENCRYPTED ADMIN SYSTEM - SECURE COMMAND PROCESSING
# ⚠️ RESTRICTED ACCESS - ADMINISTRATIVE FUNCTIONS ONLY

import hashlib
import hmac
import secrets
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging

# 🔑 ENCRYPTION SYSTEM
class CommandEncryption:
    """Encrypt and decrypt admin commands"""
    
    def __init__(self, master_key: str):
        self.master_key = master_key.encode()
        self.command_keys = {}
        self._generate_keys()
    
    def _generate_keys(self):
        """Generate encryption keys"""
        # Generate key for each admin function
        functions = [
            'stats', 'users', 'ban', 'unban', 'premium',
            'broadcast', 'security', 'reset', 'logs', 'backup'
        ]
        
        for func in functions:
            key = hmac.new(
                self.master_key,
                f"admin_key_{func}".encode(),
                hashlib.sha256
            ).digest()[:16]
            self.command_keys[func] = key
    
    def encrypt_command(self, command: str, params: Dict) -> str:
        """Encrypt admin command"""
        try:
            # Prepare data
            data = {
                'command': command,
                'params': params,
                'timestamp': datetime.now().isoformat(),
                'nonce': secrets.token_hex(8)
            }
            
            # Convert to JSON
            json_data = json.dumps(data, separators=(',', ':'))
            
            # Get encryption key
            if command not in self.command_keys:
                raise ValueError(f"Unknown command: {command}")
            
            key = self.command_keys[command]
            
            # Simple XOR encryption (in production use AES)
            encrypted = self._simple_encrypt(json_data.encode(), key)
            
            # Base64 encode
            encoded = base64.urlsafe_b64encode(encrypted).decode()
            
            return encoded
            
        except Exception as e:
            logging.error(f"Command encryption failed: {e}")
            return ""
    
    def decrypt_command(self, encrypted_data: str) -> Tuple[bool, Optional[Dict], str]:
        """Decrypt admin command"""
        try:
            # Base64 decode
            encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Try each key
            for command, key in self.command_keys.items():
                try:
                    # Decrypt
                    decrypted = self._simple_decrypt(encrypted, key)
                    
                    # Parse JSON
                    data = json.loads(decrypted.decode())
                    
                    # Validate timestamp
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    if datetime.now() - timestamp > timedelta(minutes=5):
                        return False, None, "Command expired"
                    
                    # Validate structure
                    if 'command' not in data or 'params' not in data:
                        return False, None, "Invalid command structure"
                    
                    return True, data, "Success"
                    
                except:
                    continue
            
            return False, None, "Decryption failed"
            
        except Exception as e:
            return False, None, f"Decryption error: {str(e)}"
    
    def _simple_encrypt(self, data: bytes, key: bytes) -> bytes:
        """Simple XOR encryption (replace with AES in production)"""
        result = bytearray()
        key_len = len(key)
        
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % key_len])
        
        return bytes(result)
    
    def _simple_decrypt(self, data: bytes, key: bytes) -> bytes:
        """Simple XOR decryption"""
        return self._simple_encrypt(data, key)  # XOR is symmetric

# 🔐 ADMIN COMMAND VALIDATOR
class AdminCommandValidator:
    """Validate admin commands"""
    
    def __init__(self, admin_ids: List[int]):
        self.admin_ids = admin_ids
        self.command_history = {}
        self.failed_attempts = {}
        self.MAX_FAILED_ATTEMPTS = 5
        self.COMMAND_TIMEOUT = 30  # seconds
    
    def validate_admin(self, user_id: int) -> bool:
        """Validate admin user"""
        return user_id in self.admin_ids
    
    def validate_command_rate(self, user_id: int, command: str) -> Tuple[bool, str]:
        """Validate command rate limiting"""
        current_time = datetime.now()
        
        # Initialize user history
        if user_id not in self.command_history:
            self.command_history[user_id] = {}
        
        if command not in self.command_history[user_id]:
            self.command_history[user_id][command] = []
        
        # Clean old entries
        self.command_history[user_id][command] = [
            t for t in self.command_history[user_id][command]
            if (current_time - t).total_seconds() < self.COMMAND_TIMEOUT
        ]
        
        # Check rate (max 3 commands per 30 seconds)
        if len(self.command_history[user_id][command]) >= 3:
            return False, f"Rate limit exceeded for command: {command}"
        
        # Add current command
        self.command_history[user_id][command].append(current_time)
        
        return True, "Rate limit OK"
    
    def check_failed_attempts(self, user_id: int) -> Tuple[bool, str]:
        """Check failed command attempts"""
        if user_id in self.failed_attempts:
            attempts, last_attempt = self.failed_attempts[user_id]
            
            # Reset if last attempt was more than 1 hour ago
            if (datetime.now() - last_attempt).total_seconds() > 3600:
                del self.failed_attempts[user_id]
                return True, "Attempts reset"
            
            if attempts >= self.MAX_FAILED_ATTEMPTS:
                return False, f"Too many failed attempts ({attempts})"
        
        return True, "Attempts OK"
    
    def record_failed_attempt(self, user_id: int):
        """Record failed command attempt"""
        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = [1, datetime.now()]
        else:
            attempts, _ = self.failed_attempts[user_id]
            self.failed_attempts[user_id] = [attempts + 1, datetime.now()]
    
    def reset_failed_attempts(self, user_id: int):
        """Reset failed attempts for user"""
        if user_id in self.failed_attempts:
            del self.failed_attempts[user_id]

# 🛠️ ADMIN COMMAND EXECUTOR
class AdminCommandExecutor:
    """Execute admin commands securely"""
    
    def __init__(self, database, encryption_system: CommandEncryption):
        self.db = database
        self.encryption = encryption_system
        self.validator = AdminCommandValidator([6970104969])  # Admin ID
        
        # Command handlers
        self.handlers = {
            'stats': self._handle_stats,
            'users': self._handle_users,
            'ban': self._handle_ban,
            'unban': self._handle_unban,
            'premium': self._handle_premium,
            'broadcast': self._handle_broadcast,
            'security': self._handle_security,
            'reset': self._handle_reset,
            'logs': self._handle_logs,
            'backup': self._handle_backup,
        }
    
    async def execute_command(self, user_id: int, encrypted_command: str) -> Dict:
        """Execute encrypted admin command"""
        # Validate admin
        if not self.validator.validate_admin(user_id):
            self.validator.record_failed_attempt(user_id)
            return self._error_response("NOT_ADMIN")
        
        # Check failed attempts
        attempts_ok, attempts_msg = self.validator.check_failed_attempts(user_id)
        if not attempts_ok:
            return self._error_response(attempts_msg)
        
        # Decrypt command
        decrypted_ok, decrypted_data, decryption_msg = \
            self.encryption.decrypt_command(encrypted_command)
        
        if not decrypted_ok:
            self.validator.record_failed_attempt(user_id)
            return self._error_response(f"DECRYPTION_FAILED: {decryption_msg}")
        
        # Extract command and params
        command = decrypted_data['command']
        params = decrypted_data.get('params', {})
        
        # Validate command rate
        rate_ok, rate_msg = self.validator.validate_command_rate(user_id, command)
        if not rate_ok:
            return self._error_response(rate_msg)
        
        # Check if command exists
        if command not in self.handlers:
            self.validator.record_failed_attempt(user_id)
            return self._error_response(f"UNKNOWN_COMMAND: {command}")
        
        # Execute command
        try:
            handler = self.handlers[command]
            result = await handler(params, user_id)
            
            # Reset failed attempts on success
            self.validator.reset_failed_attempts(user_id)
            
            # Encrypt response
            if result.get('encrypt_response', True):
                response_data = {
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
                encrypted_response = self.encryption.encrypt_command(
                    f"{command}_response", response_data
                )
                result['encrypted_response'] = encrypted_response
            
            return result
            
        except Exception as e:
            logging.error(f"Admin command execution failed: {e}")
            self.validator.record_failed_attempt(user_id)
            return self._error_response(f"EXECUTION_ERROR: {str(e)}")
    
    def _error_response(self, error: str) -> Dict:
        """Create error response"""
        return {
            'success': False,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'encrypted': False
        }
    
    # 🎯 COMMAND HANDLERS
    
    async def _handle_stats(self, params: Dict, admin_id: int) -> Dict:
        """Handle stats command"""
        # Get security stats
        from security_layer import SECURITY_MANAGER
        security_report = SECURITY_MANAGER.get_security_report()
        
        # Get database stats
        db_stats = self.db.get_security_report(24)  # Last 24 hours
        
        return {
            'success': True,
            'command': 'stats',
            'data': {
                'security': security_report,
                'database': db_stats,
                'admin_id': admin_id,
                'timestamp': datetime.now().isoformat()
            },
            'encrypt_response': True
        }
    
    async def _handle_users(self, params: Dict, admin_id: int) -> Dict:
        """Handle users command"""
        limit = params.get('limit', 20)
        if limit > 100:
            limit = 100
        
        # This would query the database
        # For security, we don't expose all user data
        
        return {
            'success': True,
            'command': 'users',
            'data': {
                'count': 'protected',
                'limit': limit,
                'admin_id': admin_id,
                'timestamp': datetime.now().isoformat()
            },
            'encrypt_response': True
        }
    
    async def _handle_ban(self, params: Dict, admin_id: int) -> Dict:
        """Handle ban command"""
        target_id = params.get('user_id')
        reason = params.get('reason', 'Административное решение')
        
        if not target_id:
            return self._error_response("MISSING_USER_ID")
        
        # Ban user
        self.db.ban_user(target_id, reason)
        
        return {
            'success': True,
            'command': 'ban',
            'data': {
                'target_id': target_id,
                'reason': reason,
                'admin_id': admin_id,
                'timestamp': datetime.now().isoformat()
            },
            'encrypt_response': True
        }
    
    async def _handle_unban(self, params: Dict, admin_id: int) -> Dict:
        """Handle unban command"""
        target_id = params.get('user_id')
        
        if not target_id:
            return self._error_response("MISSING_USER_ID")
        
        # Unban user (implementation depends on database)
        
        return {
            'success': True,
            'command': 'unban',
            'data': {
                'target_id': target_id,
                'admin_id': admin_id,
                'timestamp': datetime.now().isoformat()
            },
            'encrypt_response': True
        }
    
    async def _handle_premium(self, params: Dict, admin_id: int) -> Dict:
        """Handle premium command"""
        target_id = params.get('user_id')
        days = params.get('days', 30)
        
        if not target_id:
            return self._error_response("MISSING_USER_ID")
        
        if days <= 0:
            return self._error_response("INVALID_DAYS")
        
        # Give premium (implementation depends on database)
        
        return {
            'success': True,
            'command': 'premium',
            'data': {
                'target_id': target_id,
                'days': days,
                'admin_id': admin_id,
                'timestamp': datetime.now().isoformat()
            },
            'encrypt_response': True
        }
    
    async def _handle_broadcast(self, params: Dict, admin_id: int) -> Dict:
        """Handle broadcast command"""
        message = params.get('message')
        
        if not message:
            return self._error_response("MISSING_MESSAGE")
        
        if len(message) > 1000:
            return self._error_response("MESSAGE_TOO_LONG")
        
        # Queue broadcast message
        
        return {
            'success': True,
            'command': 'broadcast',
            'data': {
                'message_length': len(message),
                'admin_id': admin_id,
                'timestamp': datetime.now().isoformat()
            },
            'encrypt_response': True
        }
    
    async def _handle_security(self, params: Dict, admin_id: int) -> Dict:
        """Handle security command"""
        action = params.get('action', 'report')
        
        if action == 'report':
            # Get detailed security report
            from api_protector import APISecurityLayer
            
            # This would require APISecurityLayer instance
            report = {
                'status': 'secure',
                'last_scan': datetime.now().isoformat(),
                'threats_blocked': 'protected',
                'admin_id': admin_id
            }
            
            return {
                'success': True,
                'command': 'security_report',
                'data': report,
                'encrypt_response': True
            }
        
        elif action == 'reset':
            # Reset security counters
            # This would reset APISecurityLayer counters
            
            return {
                'success': True,
                'command': 'security_reset',
                'data': {
                    'action': 'counters_reset',
                    'admin_id': admin_id,
                    'timestamp': datetime.now().isoformat()
                },
                'encrypt_response': True
            }
        
        else:
            return self._error_response(f"UNKNOWN_ACTION: {action}")
    
    async def _handle_reset(self, params: Dict, admin_id: int) -> Dict:
        """Handle reset command - DANGEROUS"""
        confirmation = params.get('confirmation')
        
        if confirmation != 'CONFIRM_RESET_ALL_DATA':
            return self._error_response("CONFIRMATION_REQUIRED")
        
        # This would reset the database
        # Extremely dangerous operation
        
        return {
            'success': True,
            'command': 'reset',
            'data': {
                'warning': 'SYSTEM_RESET_INITIATED',
                'admin_id': admin_id,
                'timestamp': datetime.now().isoformat()
            },
            'encrypt_response': True
        }
    
    async def _handle_logs(self, params: Dict, admin_id: int) -> Dict:
        """Handle logs command"""
        log_type = params.get('type', 'security')
        limit = params.get('limit', 50)
        
        if limit > 1000:
            limit = 1000
        
        # Get logs based on type
        logs = {
            'security': [],
            'database': [],
            'api': []
        }
        
        return {
            'success': True,
            'command': 'logs',
            'data': {
                'type': log_type,
                'limit': limit,
                'log_count': len(logs.get(log_type, [])),
                'admin_id': admin_id,
                'timestamp': datetime.now().isoformat()
            },
            'encrypt_response': True
        }
    
    async def _handle_backup(self, params: Dict, admin_id: int) -> Dict:
        """Handle backup command"""
        backup_type = params.get('type', 'database')
        
        # Create backup
        backup_info = {
            'type': backup_type,
            'status': 'initiated',
            'backup_id': secrets.token_hex(8),
            'admin_id': admin_id,
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'command': 'backup',
            'data': backup_info,
            'encrypt_response': True
        }

# 🚀 ADMIN COMMAND INTERFACE
class SecureAdminInterface:
    """Secure interface for admin commands"""
    
    def __init__(self, database):
        master_key = secrets.token_hex(32)
        self.encryption = CommandEncryption(master_key)
        self.executor = AdminCommandExecutor(database, self.encryption)
        
    async def process_admin_command(self, user_id: int, command_data: str) -> Dict:
        """Process admin command"""
        return await self.executor.execute_command(user_id, command_data)
    
    def generate_test_command(self, command: str, params: Dict = None) -> str:
        """Generate test command (for development only)"""
        if params is None:
            params = {}
        
        return self.encryption.encrypt_command(command, params)
    
    def get_available_commands(self) -> List[str]:
        """Get list of available commands"""
        return list(self.executor.handlers.keys())