# Telegram Anime Bot

A Telegram bot for searching and streaming anime using the GogoAnime API.

## ⚠️ Disclaimer

This bot is for **educational purposes only**. Please support anime creators by using official streaming platforms like:
- Crunchyroll
- Funimation
- Netflix
- Hulu

## Features

- 🔍 Search anime by name
- 📺 Get recent anime updates
- 🎯 Browse popular anime
- 🤖 Simple command interface

## Commands

- `/start` - Start the bot
- `/search <anime name>` - Search for anime
- `/recent` - Get recent anime updates
- `/help` - Show help message

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/telegram-anime-bot.git
cd telegram-anime-bot
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment file:
```bash
cp .env.example .env
```

5. Edit `.env` and add your bot token:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

6. Run the bot:
```bash
python telegram_anime_bot.py
```

### VPS Deployment

1. Upload files to your VPS:
```bash
scp -r * user@your-vps-ip:/home/user/anime-bot/
```

2. SSH into your VPS:
```bash
ssh user@your-vps-ip
```

3. Run the deployment script:
```bash
cd anime-bot
chmod +x deploy.sh
./deploy.sh
```

4. Configure the environment:
```bash
sudo -u telegram-bot nano /home/telegram-bot/anime-bot/.env
```

5. Start the service:
```bash
sudo systemctl start telegram-anime-bot
```

## GitHub Repository Setup

1. Create a new repository on GitHub
2. Add files to repository:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/telegram-anime-bot.git
git push -u origin main
```

3. Set up GitHub Secrets (for auto-deployment):
   - `VPS_HOST` - Your VPS IP address
   - `VPS_USERNAME` - Your VPS username
   - `VPS_SSH_KEY` - Your private SSH key
   - `VPS_PORT` - SSH port (usually 22)

## VPS Management Commands

```bash
# Check bot status
sudo systemctl status telegram-anime-bot

# Start/stop/restart bot
sudo systemctl start telegram-anime-bot
sudo systemctl stop telegram-anime-bot
sudo systemctl restart telegram-anime-bot

# View logs
sudo journalctl -u telegram-anime-bot -f
tail -f /home/telegram-bot/anime-bot/telegram_anime_bot.log

# Update bot
cd /home/telegram-bot/anime-bot
git pull
sudo systemctl restart telegram-anime-bot
```

## Security Considerations

- Never commit your `.env` file with real tokens
- Use GitHub Secrets for sensitive data
- Keep your VPS updated
- Use firewall rules
- Run bot with limited user privileges
- Monitor logs regularly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes only. Please respect copyright laws and use official streaming platforms.

## Support

If you encounter issues:
1. Check the logs: `sudo journalctl -u telegram-anime-bot -f`
2. Verify your environment configuration
3. Ensure your bot token is valid
4. Check network connectivity
