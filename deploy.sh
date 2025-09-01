#!/bin/bash
# Telegram Anime Bot Deployment Script

set -e  # Exit on any error

echo "🚀 Starting deployment of Telegram Anime Bot..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BOT_USER="telegram-bot"
BOT_HOME="/home/$BOT_USER"
BOT_DIR="$BOT_HOME/anime-bot"
SERVICE_NAME="telegram-anime-bot"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    log_error "This script should not be run as root for security reasons"
    exit 1
fi

# Check if bot user exists, create if not
if ! id "$BOT_USER" &>/dev/null; then
    log_info "Creating user $BOT_USER..."
    sudo useradd -m -s /bin/bash "$BOT_USER"
    log_success "User $BOT_USER created"
else
    log_info "User $BOT_USER already exists"
fi

# Create bot directory
log_info "Setting up bot directory..."
sudo mkdir -p "$BOT_DIR"
sudo chown "$BOT_USER:$BOT_USER" "$BOT_DIR"

# Copy files to bot directory
log_info "Copying bot files..."
sudo cp telegram_anime_bot.py "$BOT_DIR/"
sudo cp requirements.txt "$BOT_DIR/"
sudo cp .env.example "$BOT_DIR/"
sudo chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR"

# Switch to bot user for Python environment setup
log_info "Setting up Python virtual environment..."
sudo -u "$BOT_USER" bash << EOF
cd "$BOT_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF

log_success "Python environment setup complete"

# Install systemd service
log_info "Installing systemd service..."
sudo cp telegram-anime-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

log_success "Systemd service installed and enabled"

# Setup environment file
if [ ! -f "$BOT_DIR/.env" ]; then
    log_info "Creating environment file..."
    sudo cp "$BOT_DIR/.env.example" "$BOT_DIR/.env"
    sudo chown "$BOT_USER:$BOT_USER" "$BOT_DIR/.env"
    log_warning "Please edit $BOT_DIR/.env and add your bot token before starting the service"
else
    log_info "Environment file already exists"
fi

# Setup log rotation
log_info "Setting up log rotation..."
sudo tee /etc/logrotate.d/telegram-anime-bot > /dev/null << EOF
$BOT_DIR/telegram_anime_bot.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $BOT_USER $BOT_USER
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF

log_success "Log rotation configured"

# Setup firewall (if ufw is available)
if command -v ufw >/dev/null 2>&1; then
    log_info "Configuring firewall..."
    sudo ufw allow ssh
    sudo ufw allow 8443/tcp  # For webhook if needed
    log_info "Firewall rules added (SSH and port 8443)"
fi

echo ""
log_success "🎉 Deployment completed successfully!"
echo ""
log_info "Next steps:"
echo "1. Edit the environment file: sudo -u $BOT_USER nano $BOT_DIR/.env"
echo "2. Add your Telegram bot token to the TELEGRAM_BOT_TOKEN variable"
echo "3. Start the bot: sudo systemctl start $SERVICE_NAME"
echo "4. Check status: sudo systemctl status $SERVICE_NAME"
echo "5. View logs: sudo journalctl -u $SERVICE_NAME -f"
echo ""
log_info "Useful commands:"
echo "• Start bot: sudo systemctl start $SERVICE_NAME"
echo "• Stop bot: sudo systemctl stop $SERVICE_NAME"
echo "• Restart bot: sudo systemctl restart $SERVICE_NAME"
echo "• View logs: sudo journalctl -u $SERVICE_NAME -f"
echo "• View bot logs: sudo tail -f $BOT_DIR/telegram_anime_bot.log"
