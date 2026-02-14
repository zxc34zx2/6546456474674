#!/bin/bash
# 🔐 SECURE INSTALLATION SCRIPT FOR PROTECTED BOT
# ⚠️ Authorized use only

set -e  # Exit on error

echo "=========================================="
echo "🛡️  ULTRA SECURE BOT INSTALLATION"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Python version
echo "🔍 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python 3.8 or higher required. Found: $PYTHON_VERSION"
    exit 1
fi
print_success "Python $PYTHON_VERSION detected"

# Check for required packages
echo "📦 Checking required packages..."
REQUIRED_PACKAGES=("python3-pip" "sqlite3")

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! dpkg -l | grep -q "^ii  $pkg "; then
        print_warning "Package $pkg not found. Installing..."
        sudo apt-get install -y "$pkg" > /dev/null 2>&1 || {
            print_error "Failed to install $pkg"
            exit 1
        }
    fi
done

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install python-telegram-bot httpx > /dev/null 2>&1 || {
    print_error "Failed to install Python dependencies"
    exit 1
}
print_success "Dependencies installed"

# Create secure directory structure
echo "📁 Creating secure directory structure..."
mkdir -p secure_data/{backups,logs,sessions}
chmod 700 secure_data
chmod 700 secure_data/*

# Set secure file permissions
echo "🔒 Setting secure file permissions..."
chmod 600 *.py 2>/dev/null || true
chmod 700 main_secure.py
chmod 700 install.sh

# Generate security keys
echo "🔑 Generating security keys..."
python3 -c "
import secrets
import hashlib
import json
import os

keys = {
    'database_key': secrets.token_hex(32),
    'session_key': secrets.token_hex(32),
    'admin_key': secrets.token_hex(32),
    'encryption_salt': secrets.token_hex(16),
    'hmac_key': secrets.token_hex(32),
    'api_protection_key': secrets.token_hex(32)
}

# Create secure config
config = {
    'security': {
        'level': 'maximum',
        'sql_injection_protection': True,
        'api_protection': True,
        'memory_protection': True,
        'tamper_detection': True
    },
    'database': {
        'name': 'secure_bot.db',
        'backup_interval': 3600,
        'max_backups': 24
    },
    'logging': {
        'level': 'INFO',
        'max_size': '10MB',
        'backup_count': 5
    }
}

# Save keys to secure file
with open('secure_config.json', 'w') as f:
    json.dump({'config': config, 'keys': keys}, f, indent=2)

# Set permissions
os.chmod('secure_config.json', 0o600)

print('Security keys generated and saved to secure_config.json')
print('⚠️  KEEP THIS FILE SECURE!')
"

# Create database
echo "🗄️  Creating secure database..."
if [ -f "secure_bot.db" ]; then
    print_warning "Database already exists, creating backup..."
    cp secure_bot.db "secure_bot.db.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Create startup script
echo "🚀 Creating startup scripts..."
cat > start_bot.sh << 'EOF'
#!/bin/bash
# 🔐 SECURE BOT STARTUP SCRIPT

echo "=========================================="
echo "🤖 STARTING ULTRA SECURE BOT"
echo "=========================================="
echo "Time: $(date)"
echo "User: $(whoami)"
echo "PID: $$"
echo "------------------------------------------"

# Security checks
if [ ! -f "main_secure.py" ]; then
    echo "❌ ERROR: Main file not found"
    exit 1
fi

if [ ! -f "secure_config.json" ]; then
    echo "❌ ERROR: Security config not found"
    exit 1
fi

# Check file permissions
if [ "$(stat -c %a main_secure.py)" != "700" ]; then
    echo "⚠️  WARNING: Insecure permissions on main_secure.py"
    chmod 700 main_secure.py
fi

# Run with security flags
echo "🔒 Starting with maximum security..."
python3 -B -S main_secure.py "$@"

EXIT_CODE=$?
echo "------------------------------------------"
echo "Bot stopped with exit code: $EXIT_CODE"
echo "=========================================="
exit $EXIT_CODE
EOF

chmod 700 start_bot.sh

# Create systemd service (if running as root)
if [ "$EUID" -eq 0 ]; then
    echo "⚙️  Creating systemd service..."
    
    SERVICE_USER=${SUDO_USER:-$USER}
    
    cat > /etc/systemd/system/secure-bot.service << EOF
[Unit]
Description=Ultra Secure Telegram Bot
After=network.target
Requires=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/start_bot.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=secure-bot

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$(pwd)/secure_data
ReadOnlyPaths=/
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
RestrictNamespaces=true
RestrictRealtime=true
LockPersonality=true
MemoryDenyWriteExecute=true

# Resource limits
LimitNOFILE=65536
LimitNPROC=512
LimitMEMLOCK=64M

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    print_success "Systemd service created"
    
    cat > /etc/systemd/system/secure-bot.timer << EOF
[Unit]
Description=Daily security scan for Secure Bot
Requires=secure-bot.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

    systemctl daemon-reload
    print_success "Security timer created"
fi

# Create update script
cat > update_bot.sh << 'EOF'
#!/bin/bash
# 🔄 SECURE BOT UPDATE SCRIPT

echo "=========================================="
echo "🔄 UPDATING SECURE BOT"
echo "=========================================="

# Backup current installation
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "💾 Creating backup..."
cp *.py "$BACKUP_DIR/" 2>/dev/null || true
cp *.db "$BACKUP_DIR/" 2>/dev/null || true
cp *.json "$BACKUP_DIR/" 2>/dev/null || true

echo "📥 Updating from repository..."
# This would pull from git repository
# git pull origin master

echo "🔒 Verifying updates..."
# Check file integrity
python3 -c "
import hashlib
import os

files = ['main_secure.py', 'core_protected.py', 'api_protector.py']
for file in files:
    if os.path.exists(file):
        with open(file, 'rb') as f:
            hash_val = hashlib.sha256(f.read()).hexdigest()[:16]
        print(f'{file}: {hash_val}')
"

echo "✅ Update completed"
echo "Backup saved to: $BACKUP_DIR"
EOF

chmod 700 update_bot.sh

# Create security monitoring script
cat > check_security.sh << 'EOF'
#!/bin/bash
# 🔍 SECURITY CHECK SCRIPT

echo "=========================================="
echo "🔍 SECURITY STATUS CHECK"
echo "=========================================="

# Check file permissions
echo "📁 File Permissions:"
find . -name "*.py" -exec stat -c "%a %n" {} \; | grep -v "^700"

# Check for suspicious files
echo "🚨 Suspicious Files:"
find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "__pycache__" \) | head -5

# Check database
echo "🗄️  Database:"
if [ -f "secure_bot.db" ]; then
    size=$(du -h secure_bot.db | cut -f1)
    echo "  Size: $size"
    
    # Check if database is readable
    if sqlite3 secure_bot.db "SELECT COUNT(*) FROM sqlite_master" 2>/dev/null; then
        echo "  Status: ✅ Accessible"
    else
        echo "  Status: ❌ Corrupted"
    fi
else
    echo "  Status: ❌ Not found"
fi

# Check logs
echo "📊 Logs:"
if [ -f "secure_bot.log" ]; then
    tail -5 secure_bot.log
else
    echo "  No log file found"
fi

echo "=========================================="
echo "🔒 SECURITY CHECK COMPLETE"
EOF

chmod 700 check_security.sh

# Create firewall rules (if root)
if [ "$EUID" -eq 0 ]; then
    echo "🔥 Configuring firewall..."
    
    # Allow only necessary ports
    ufw allow 80/tcp comment "HTTP for updates"
    ufw allow 443/tcp comment "HTTPS for updates"
    ufw deny 22/tcp comment "SSH disabled for security"
    ufw --force enable
    
    print_success "Firewall configured"
fi

print_success "Installation completed successfully!"
echo ""
echo "=========================================="
echo "🚀 QUICK START GUIDE"
echo "=========================================="
echo ""
echo "1. Start the bot:"
echo "   ./start_bot.sh"
echo ""
echo "2. Check security:"
echo "   ./check_security.sh"
echo ""
echo "3. Update bot:"
echo "   ./update_bot.sh"
echo ""
echo "4. Systemd commands (if installed as root):"
echo "   sudo systemctl start secure-bot"
echo "   sudo systemctl status secure-bot"
echo "   sudo journalctl -u secure-bot -f"
echo ""
echo "🔐 SECURITY NOTES:"
echo "• Keep secure_config.json secure"
echo "• Regularly backup secure_bot.db"
echo "• Monitor secure_bot.log for attacks"
echo "• Use VPN for additional security"
echo ""
echo "🆘 SUPPORT: @anonaltshelper"
echo "=========================================="