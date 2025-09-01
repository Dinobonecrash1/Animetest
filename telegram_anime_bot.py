#!/usr/bin/env python3
"""
Telegram Anime Bot - Main Application
A bot for searching and streaming anime using GogoAnime API
"""

import os
import logging
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import json
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('telegram_anime_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AnimeAPI:
    """GogoAnime API wrapper"""

    def __init__(self):
        self.base_url = "https://api.anispace.workers.dev"
        self.session = None

    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

    async def search_anime(self, query: str) -> List[Dict[str, Any]]:
        """Search for anime"""
        try:
            await self.init_session()
            async with self.session.get(f"{self.base_url}/search/{query}") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                return []
        except Exception as e:
            logger.error(f"Error searching anime: {e}")
            return []

    async def get_recent_anime(self, page: int = 1) -> List[Dict[str, Any]]:
        """Get recent anime updates"""
        try:
            await self.init_session()
            async with self.session.get(f"{self.base_url}/recent/{page}") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                return []
        except Exception as e:
            logger.error(f"Error getting recent anime: {e}")
            return []

class AnimeTelegramBot:
    """Main bot class"""

    def __init__(self, token: str):
        self.token = token
        self.api = AnimeAPI()
        self.application = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_text = """
🍿 Welcome to Anime Bot! 🍿

Available commands:
/search <anime name> - Search for anime
/recent - Get recent anime updates
/popular - Get popular anime
/help - Show this help message

⚠️ Note: This bot is for educational purposes only.
Please support anime creators by using official streaming platforms.
        """
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        if not context.args:
            await update.message.reply_text("Please provide an anime name to search!\n\nExample: /search Naruto")
            return

        query = " ".join(context.args)
        await update.message.reply_text(f"🔍 Searching for '{query}'...")

        results = await self.api.search_anime(query)

        if not results:
            await update.message.reply_text("No anime found with that name. Try a different search term.")
            return

        response_text = f"🔍 Search results for '{query}':\n\n"

        for i, anime in enumerate(results[:10], 1):  # Limit to 10 results
            title = anime.get('title', 'Unknown Title')
            episodes = anime.get('totalEpisodes', 'Unknown')
            response_text += f"{i}. **{title}**\n"
            response_text += f"   Episodes: {episodes}\n\n"

        response_text += "\n⚠️ For educational purposes only. Please use official streaming platforms."

        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

    async def recent_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /recent command"""
        await update.message.reply_text("📺 Getting recent anime updates...")

        results = await self.api.get_recent_anime()

        if not results:
            await update.message.reply_text("Unable to fetch recent anime updates at the moment.")
            return

        response_text = "📺 **Recent Anime Updates:**\n\n"

        for i, anime in enumerate(results[:10], 1):
            title = anime.get('title', 'Unknown Title')
            episode = anime.get('episodeNumber', 'Unknown')
            response_text += f"{i}. **{title}**\n"
            response_text += f"   Episode: {episode}\n\n"

        response_text += "\n⚠️ For educational purposes only."

        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown messages"""
        await update.message.reply_text(
            "I don't understand that command. Use /help to see available commands."
        )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Log errors"""
        logger.error(f"Exception while handling an update: {context.error}")

    def setup_handlers(self):
        """Setup command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("search", self.search_command))
        self.application.add_handler(CommandHandler("recent", self.recent_command))

        # Handle unknown messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown_command))

        # Error handler
        self.application.add_error_handler(self.error_handler)

    async def run(self):
        """Run the bot"""
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()

        logger.info("Starting Telegram Anime Bot...")

        try:
            # Initialize API session
            await self.api.init_session()

            # Start the bot
            await self.application.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Error running bot: {e}")
        finally:
            # Clean up
            await self.api.close_session()

async def main():
    """Main function"""
    # Get bot token from environment variable
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return

    # Create and run bot
    bot = AnimeTelegramBot(bot_token)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
