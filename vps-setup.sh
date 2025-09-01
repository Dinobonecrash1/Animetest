#!/bin/bash
# VPS Initial Setup Script for Telegram Anime Bot
# Run this script first on a fresh Ubuntu/Debian VPS

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🔧 Setting up VPS for Telegram Anime Bot deployment..."

# Update system
log_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
log_info "Installing essential packages..."
sudo apt install -y python3 python3-pip python3-venv git curl wget                    nginx ufw fail2ban htop nano vim unzip

# Install Python packages globally needed
log_info "Installing Python build tools..."
sudo apt install -y python3-dev build-essential

# Configure firewall
log_info "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 8443/tcp  # For Telegram webhook
sudo ufw --force enable

# Setup fail2ban for SSH protection
log_info "Configuring fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create swap if not exists (for low memory VPS)
if [ ! -f /swapfile ]; then
    log_info "Creating swap file..."
    sudo fallocate -l 1G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# Setup automatic security updates
log_info "Setting up automatic security updates..."
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Create bot user and directory structure
log_info "Creating bot user and directories..."
sudo useradd -m -s /bin/bash telegram-bot || true
sudo mkdir -p /home/telegram-bot/anime-bot
sudo chown telegram-bot:telegram-bot /home/telegram-bot/anime-bot

# Install Node.js (if needed for other tools)
log_info "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Setup nginx basic configuration
log_info "Setting up nginx..."
sudo systemctl enable nginx
sudo systemctl start nginx

# Create nginx configuration for bot (optional webhook support)
sudo tee /etc/nginx/sites-available/telegram-bot > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location /webhook {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        return 404;
    }
}
EOF

# Setup log rotation for bot logs
log_info "Setting up log rotation..."
sudo tee /etc/logrotate.d/telegram-bot > /dev/null << 'EOF'
/home/telegram-bot/anime-bot/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 telegram-bot telegram-bot
    postrotate
        systemctl reload telegram-anime-bot > /dev/null 2>&1 || true
    endscript
}
EOF

# Setup monitoring script
log_info "Creating monitoring script..."
sudo tee /usr/local/bin/bot-monitor.sh > /dev/null << 'EOF'
#!/bin/bash
# Simple monitoring script for the bot

SERVICE_NAME="telegram-anime-bot"
LOG_FILE="/var/log/bot-monitor.log"

if ! systemctl is-active --quiet $SERVICE_NAME; then
    echo "$(date): $SERVICE_NAME is not running, attempting to restart..." >> $LOG_FILE
    systemctl restart $SERVICE_NAME
    sleep 10
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "$(date): $SERVICE_NAME restarted successfully" >> $LOG_FILE
    else
        echo "$(date): Failed to restart $SERVICE_NAME" >> $LOG_FILE
    fi
fi
EOF

sudo chmod +x /usr/local/bin/bot-monitor.sh

# Add monitoring to crontab
log_info "Setting up monitoring cron job..."
(crontab -l 2>/dev/null | grep -v bot-monitor; echo "*/5 * * * * /usr/local/bin/bot-monitor.sh") | sudo crontab -

# Setup system limits
log_info "Configuring system limits..."
sudo tee -a /etc/security/limits.conf > /dev/null << 'EOF'
telegram-bot soft nofile 4096
telegram-bot hard nofile 4096
telegram-bot soft nproc 2048
telegram-bot hard nproc 2048
EOF

# Create deployment directory
log_info "Creating deployment directory..."
sudo mkdir -p /opt/deployment
sudo chown $USER:$USER /opt/deployment

echo ""
log_success "🎉 VPS setup completed!"
echo ""
log_info "Next steps:"
echo "1. Clone your bot repository: git clone https://github.com/yourusername/telegram-anime-bot.git"
echo "2. Run the deployment script: ./deploy.sh"
echo "3. Configure your bot token in .env file"
echo "4. Start the bot service"
echo ""
log_info "System info:"
echo "• Python version: $(python3 --version)"
echo "• Available memory: $(free -h | grep Mem | awk '{print $2}')"
echo "• Disk space: $(df -h / | tail -1 | awk '{print $4}' | tr -d '\n') available"
echo "• IP address: $(curl -s ifconfig.me)"
echo ""
log_warning "Remember to:"
echo "• Change default SSH port (edit /etc/ssh/sshd_config)"
echo "• Set up SSH key authentication"
echo "• Configure a domain name (optional)"
echo "• Set up SSL certificate if using webhooks"
