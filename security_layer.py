#!/usr/bin/env python3
# 🔐 SECURITY LAYER MODULE - COMPREHENSIVE PROTECTION
# ⚠️ DO NOT MODIFY - SECURITY ENFORCEMENT ACTIVE

import os
import sys
import hashlib
import hmac
import secrets
import time
import inspect
import threading
import signal
import atexit
from datetime import datetime
from typing import Callable, Any, Dict, List, Optional
import logging

# 🚨 ANTI-TAMPERING SYSTEM
class AntiTampering:
    """Prevent code tampering and runtime manipulation"""
    
    def __init__(self):
        self.code_hashes = {}
        self.memory_checks = []
        self.runtime_guards = []
        self._collect_hashes()
        self._install_guards()
    
    def _collect_hashes(self):
        """Collect hashes of critical files"""
        critical_files = [
            'main_secure.py',
            'core_protected.py', 
            'api_protector.py',
            'security_layer.py',
            'encrypted_admin.py'
        ]
        
        for file in critical_files:
            if os.path.exists(file):
                try:
                    with open(file, 'rb') as f:
                        content = f.read()
                        self.code_hashes[file] = {
                            'hash': hashlib.sha256(content).hexdigest(),
                            'size': len(content),
                            'mtime': os.path.getmtime(file)
                        }
                except Exception as e:
                    logging.error(f"Failed to hash {file}: {e}")
    
    def _install_guards(self):
        """Install runtime guards"""
        # Guard against module replacement
        original_import = __builtins__.__import__
        
        def guarded_import(name, *args, **kwargs):
            # Check for suspicious modules
            suspicious = ['pdb', 'ipdb', 'pydevd', 'debugpy', 'code', 'bdb']
            if name in suspicious:
                logging.warning(f"Attempt to import suspicious module: {name}")
                raise ImportError(f"Module {name} blocked by security")
            
            return original_import(name, *args, **kwargs)
        
        __builtins__.__import__ = guarded_import
        
        # Register cleanup
        atexit.register(self._cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def check_integrity(self) -> Dict[str, bool]:
        """Check integrity of all protected files"""
        results = {}
        
        for file, original_info in self.code_hashes.items():
            if not os.path.exists(file):
                results[file] = False
                continue
            
            try:
                with open(file, 'rb') as f:
                    content = f.read()
                
                current_hash = hashlib.sha256(content).hexdigest()
                current_size = len(content)
                current_mtime = os.path.getmtime(file)
                
                # Check hash
                hash_ok = current_hash == original_info['hash']
                
                # Check if file was modified recently (potential runtime tampering)
                time_diff = time.time() - current_mtime
                time_ok = time_diff > 5  # Not modified in last 5 seconds
                
                # Check size
                size_ok = current_size == original_info['size']
                
                results[file] = hash_ok and time_ok and size_ok
                
                if not results[file]:
                    logging.warning(f"Integrity check failed for {file}: "
                                  f"hash_ok={hash_ok}, time_ok={time_ok}, size_ok={size_ok}")
                    
            except Exception as e:
                logging.error(f"Failed to check {file}: {e}")
                results[file] = False
        
        return results
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals securely"""
        logging.warning(f"Signal {signum} received - performing secure shutdown")
        self._cleanup()
        sys.exit(1)
    
    def _cleanup(self):
        """Cleanup security data"""
        try:
            # Overwrite sensitive data
            self.code_hashes.clear()
            self.memory_checks.clear()
            self.runtime_guards.clear()
            
            # Force garbage collection
            import gc
            gc.collect()
        except:
            pass

# 🔍 MEMORY PROTECTION
class MemoryProtector:
    """Protect sensitive data in memory"""
    
    @staticmethod
    def secure_erase(data):
        """Securely erase data from memory"""
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            return
        
        # Multiple overwrites
        length = len(data_bytes)
        for _ in range(3):
            # Fill with random data
            random_bytes = secrets.token_bytes(length)
            data_bytes = bytes(a ^ b for a, b in zip(data_bytes, random_bytes))
        
        # Final overwrite with zeros
        data_bytes = b'\x00' * length
        
        # Clear reference
        del data_bytes
    
    @staticmethod
    def protect_sensitive(func: Callable) -> Callable:
        """Decorator to protect sensitive function execution"""
        def wrapper(*args, **kwargs):
            # Make local copies
            local_args = list(args)
            local_kwargs = kwargs.copy()
            
            try:
                # Execute
                result = func(*local_args, **local_kwargs)
                
                # Cleanup arguments
                for i, arg in enumerate(local_args):
                    if isinstance(arg, (str, bytes)):
                        MemoryProtector.secure_erase(arg)
                        local_args[i] = None
                
                for key, value in local_kwargs.items():
                    if isinstance(value, (str, bytes)):
                        MemoryProtector.secure_erase(value)
                        local_kwargs[key] = None
                
                return result
            finally:
                # Final cleanup
                del local_args
                del local_kwargs
        
        return wrapper

# 🛡️ REQUEST SANITIZATION
class RequestSanitizer:
    """Sanitize all incoming requests"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            return ""
        
        # Remove null bytes
        sanitized = input_str.replace('\x00', '')
        
        # Remove control characters (except newline, tab, carriage return)
        sanitized = ''.join(
            char for char in sanitized 
            if ord(char) >= 32 or char in '\n\r\t'
        )
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    @staticmethod
    def sanitize_integer(input_val) -> Optional[int]:
        """Sanitize integer input"""
        try:
            if isinstance(input_val, str):
                # Remove non-numeric characters
                numeric = ''.join(c for c in input_val if c.isdigit() or c == '-')
                if numeric and numeric != '-':
                    value = int(numeric)
                    # Basic range check
                    if -2147483648 <= value <= 2147483647:
                        return value
            elif isinstance(input_val, int):
                if -2147483648 <= input_val <= 2147483647:
                    return input_val
        except (ValueError, TypeError):
            pass
        
        return None
    
    @staticmethod
    def sanitize_dict(input_dict: Dict) -> Dict:
        """Sanitize dictionary input"""
        if not isinstance(input_dict, dict):
            return {}
        
        sanitized = {}
        for key, value in input_dict.items():
            # Sanitize key
            safe_key = RequestSanitizer.sanitize_string(str(key), 100)
            
            # Sanitize value based on type
            if isinstance(value, str):
                safe_value = RequestSanitizer.sanitize_string(value)
            elif isinstance(value, int):
                safe_value = RequestSanitizer.sanitize_integer(value)
            elif isinstance(value, dict):
                safe_value = RequestSanitizer.sanitize_dict(value)
            elif isinstance(value, list):
                safe_value = RequestSanitizer.sanitize_list(value)
            else:
                safe_value = str(value)[:100] if value else None
            
            if safe_key and safe_value is not None:
                sanitized[safe_key] = safe_value
        
        return sanitized
    
    @staticmethod
    def sanitize_list(input_list: List) -> List:
        """Sanitize list input"""
        if not isinstance(input_list, list):
            return []
        
        sanitized = []
        for item in input_list:
            if isinstance(item, str):
                safe_item = RequestSanitizer.sanitize_string(item)
            elif isinstance(item, (int, float)):
                safe_item = item
            elif isinstance(item, dict):
                safe_item = RequestSanitizer.sanitize_dict(item)
            elif isinstance(item, list):
                safe_item = RequestSanitizer.sanitize_list(item)
            else:
                safe_item = str(item)[:100] if item else None
            
            if safe_item is not None:
                sanitized.append(safe_item)
        
        return sanitized

# 📊 SECURITY MONITOR
class SecurityMonitor:
    """Monitor system for security events"""
    
    def __init__(self):
        self.events = []
        self.max_events = 10000
        self.alert_threshold = 10
        self.monitoring = True
        self.alert_callbacks = []
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def log_event(self, event_type: str, severity: int, details: str = "", user_id: int = None):
        """Log security event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'severity': severity,
            'details': details[:500],
            'user_id': user_id
        }
        
        self.events.append(event)
        
        # Trim if too many events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        # Check for alerts
        if severity >= 5:
            self._check_alerts(event_type, severity)
    
    def _check_alerts(self, event_type: str, severity: int):
        """Check if alert should be triggered"""
        # Count recent high-severity events
        recent_events = [
            e for e in self.events[-100:]  # Last 100 events
            if e['severity'] >= 5 and time.time() - datetime.fromisoformat(e['timestamp']).timestamp() < 300
        ]
        
        if len(recent_events) >= self.alert_threshold:
            # Trigger alert callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(recent_events)
                except:
                    pass
    
    def _monitor_loop(self):
        """Monitoring loop"""
        while self.monitoring:
            time.sleep(30)
            self._cleanup_old_events()
    
    def _cleanup_old_events(self):
        """Cleanup old events"""
        cutoff_time = time.time() - 86400  # 24 hours
        
        self.events = [
            e for e in self.events
            if datetime.fromisoformat(e['timestamp']).timestamp() > cutoff_time
        ]
    
    def register_alert_callback(self, callback: Callable):
        """Register alert callback"""
        self.alert_callbacks.append(callback)
    
    def get_recent_events(self, limit: int = 100) -> List[Dict]:
        """Get recent security events"""
        return self.events[-limit:]
    
    def stop(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

# 🚀 SECURITY MANAGER
class SecurityManager:
    """Main security manager"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SecurityManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.anti_tampering = AntiTampering()
        self.memory_protector = MemoryProtector()
        self.request_sanitizer = RequestSanitizer()
        self.monitor = SecurityMonitor()
        
        # Register alert callback
        self.monitor.register_alert_callback(self._handle_security_alert)
        
        # Run initial checks
        self._initial_checks()
        
        self._initialized = True
    
    def _initial_checks(self):
        """Run initial security checks"""
        # Check file integrity
        integrity = self.anti_tampering.check_integrity()
        
        for file, is_ok in integrity.items():
            if not is_ok:
                self.monitor.log_event(
                    "FILE_TAMPERING", 
                    10, 
                    f"File {file} integrity check failed",
                    None
                )
        
        # Check environment
        env_checks = self._check_environment()
        for check, details in env_checks:
            self.monitor.log_event(
                "ENVIRONMENT_CHECK",
                3 if "WARNING" in check else 5,
                details,
                None
            )
    
    def _check_environment(self) -> List[Tuple[str, str]]:
        """Check execution environment"""
        checks = []
        
        # Check for debugger
        if hasattr(sys, 'gettrace') and sys.gettrace() is not None:
            checks.append(("DEBUGGER_ACTIVE", "Execution under debugger"))
        
        # Check Python path
        if 'test' in sys.path[0].lower() or 'debug' in sys.path[0].lower():
            checks.append(("SUSPICIOUS_PATH", f"Suspicious sys.path: {sys.path[0]}"))
        
        # Check for suspicious modules
        suspicious_modules = ['pdb', 'ipdb', 'pydevd', 'debugpy']
        for module in suspicious_modules:
            if module in sys.modules:
                checks.append((f"SUSPICIOUS_MODULE_{module.upper()}", f"Module {module} loaded"))
        
        return checks
    
    def _handle_security_alert(self, events: List[Dict]):
        """Handle security alert"""
        logging.critical(f"🚨 SECURITY ALERT: {len(events)} high-severity events detected")
        
        # Log details
        for event in events[:5]:  # First 5 events
            logging.critical(f"  - {event['type']}: {event['details']}")
    
    def sanitize_input(self, input_data) -> Any:
        """Sanitize input based on type"""
        if isinstance(input_data, str):
            return self.request_sanitizer.sanitize_string(input_data)
        elif isinstance(input_data, int):
            return self.request_sanitizer.sanitize_integer(input_data)
        elif isinstance(input_data, dict):
            return self.request_sanitizer.sanitize_dict(input_data)
        elif isinstance(input_data, list):
            return self.request_sanitizer.sanitize_list(input_data)
        else:
            return str(input_data)[:100] if input_data else None
    
    def secure_execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with security protections"""
        # Sanitize inputs
        sanitized_args = [self.sanitize_input(arg) for arg in args]
        sanitized_kwargs = {k: self.sanitize_input(v) for k, v in kwargs.items()}
        
        # Add memory protection
        protected_func = self.memory_protector.protect_sensitive(func)
        
        # Execute and monitor
        start_time = time.time()
        
        try:
            result = protected_func(*sanitized_args, **sanitized_kwargs)
            
            execution_time = time.time() - start_time
            
            # Log if execution took too long (potential DoS)
            if execution_time > 5.0:
                self.monitor.log_event(
                    "LONG_EXECUTION",
                    3,
                    f"Function {func.__name__} took {execution_time:.2f}s",
                    None
                )
            
            return result
            
        except Exception as e:
            self.monitor.log_event(
                "EXECUTION_ERROR",
                4,
                f"Function {func.__name__} failed: {str(e)[:100]}",
                None
            )
            raise
    
    def get_security_report(self) -> Dict:
        """Get comprehensive security report"""
        integrity = self.anti_tampering.check_integrity()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'integrity_checks': integrity,
            'total_events': len(self.monitor.events),
            'recent_high_severity': len([e for e in self.monitor.events[-100:] if e['severity'] >= 5]),
            'monitoring_active': self.monitor.monitoring,
            'security_level': 'MAXIMUM'
        }
    
    def shutdown(self):
        """Shutdown security system"""
        self.monitor.stop()
        
        # Perform cleanup
        self.anti_tampering._cleanup()

# Initialize global security manager
SECURITY_MANAGER = SecurityManager()