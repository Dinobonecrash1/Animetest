#!/usr/bin/env python3
"""
Telegram Anime Bot - Main Application (Asyncio Fixed)
A bot for searching and streaming anime using GogoAnime API
"""

import os
import logging
import asyncio
import aiohttp
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import json
from typing import List, Dict, Any

# Try to load dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ dotenv loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not installed. Using system environment variables only.")

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
        if self.session and not self.session.closed:
            await self.session.close()

    async def search_anime(self, query: str) -> List[Dict[str, Any]]:
        """Search for anime"""
        try:
            await self.init_session()
            async with self.session.get(f"{self.base_url}/search/{query}") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                else:
                    logger.warning(f"API returned status {response.status}")
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
                else:
                    logger.warning(f"API returned status {response.status}")
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
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")

        welcome_text = f"""
🍿 Welcome to Anime Bot, {user.first_name}! 🍿

Available commands:
/search <anime name> - Search for anime
/recent - Get recent anime updates
/popular - Get popular anime (coming soon)
/help - Show this help message

⚠️ Note: This bot is for educational purposes only.
Please support anime creators by using official streaming platforms.

Example: /search Naruto
        """
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        user = update.effective_user

        if not context.args:
            await update.message.reply_text(
                "Please provide an anime name to search!\n\nExample: /search Naruto"
            )
            return

        query = " ".join(context.args)
        logger.info(f"User {user.id} searching for: {query}")

        # Send initial message
        message = await update.message.reply_text(f"🔍 Searching for '{query}'...")

        try:
            results = await self.api.search_anime(query)

            if not results:
                await message.edit_text("No anime found with that name. Try a different search term.")
                return

            response_text = f"🔍 **Search results for '{query}':**\n\n"

            for i, anime in enumerate(results[:8], 1):  # Limit to 8 results to avoid message length issues
                title = anime.get('title', 'Unknown Title')
                episodes = anime.get('totalEpisodes', 'Unknown')
                year = anime.get('releaseDate', 'Unknown')
                response_text += f"{i}. **{title}**\n"
                response_text += f"   📺 Episodes: {episodes}\n"
                response_text += f"   📅 Year: {year}\n\n"

            response_text += "⚠️ For educational purposes only. Please use official streaming platforms."

            await message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Error in search command: {e}")
            await message.edit_text("Sorry, there was an error searching for anime. Please try again.")

    async def recent_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /recent command"""
        user = update.effective_user
        logger.info(f"User {user.id} requested recent anime")

        message = await update.message.reply_text("📺 Getting recent anime updates...")

        try:
            results = await self.api.get_recent_anime()

            if not results:
                await message.edit_text("Unable to fetch recent anime updates at the moment. Please try again later.")
                return

            response_text = "📺 **Recent Anime Updates:**\n\n"

            for i, anime in enumerate(results[:8], 1):  # Limit to 8 results
                title = anime.get('title', 'Unknown Title')
                episode = anime.get('episodeNumber', 'Unknown')
                response_text += f"{i}. **{title}**\n"
                response_text += f"   📺 Episode: {episode}\n\n"

            response_text += "⚠️ For educational purposes only."

            await message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Error in recent command: {e}")
            await message.edit_text("Sorry, there was an error getting recent anime. Please try again.")

    async def popular_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /popular command"""
        await update.message.reply_text(
            "🎯 **Popular anime feature is coming soon!**\n\n"
            "For now, try:\n"
            "• /search One Piece\n"
            "• /search Attack on Titan\n"
            "• /search Demon Slayer\n"
            "• /recent - for latest updates",
            parse_mode=ParseMode.MARKDOWN
        )

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown messages"""
        await update.message.reply_text(
            "I don't understand that command. Use /help to see available commands.\n\n"
            "📋 **Available commands:**\n"
            "• /start - Start the bot\n"
            "• /search <anime name> - Search anime\n"
            "• /recent - Recent updates\n"
            "• /popular - Popular anime\n"
            "• /help - Show help",
            parse_mode=ParseMode.MARKDOWN
        )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Log errors and inform user"""
        logger.error(f"Exception while handling an update: {context.error}")

        # Try to send error message to user if possible
        if update and hasattr(update, 'message') and update.message:
            try:
                await update.message.reply_text(
                    "😅 Sorry, something went wrong processing your request. Please try again."
                )
            except Exception as e:
                logger.error(f"Could not send error message to user: {e}")

    def setup_handlers(self):
        """Setup command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("search", self.search_command))
        self.application.add_handler(CommandHandler("recent", self.recent_command))
        self.application.add_handler(CommandHandler("popular", self.popular_command))

        # Handle unknown messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown_command))

        # Error handler
        self.application.add_error_handler(self.error_handler)

    async def initialize(self):
        """Initialize the bot application"""
        try:
            self.application = Application.builder().token(self.token).build()
            await self.application.initialize()
            self.setup_handlers()
            logger.info("Bot application initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing bot: {e}")
            raise

    async def start_polling(self):
        """Start the bot with polling"""
        try:
            logger.info("Starting bot polling...")
            await self.api.init_session()
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)

            logger.info("🤖 Bot is now running and ready to receive messages!")
            logger.info("Press Ctrl+C to stop the bot")

            # Keep the bot running
            await asyncio.Event().wait()

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping bot...")
        except Exception as e:
            logger.error(f"Error during polling: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("Cleaning up resources...")

            if self.application:
                if self.application.updater.running:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()

            if self.api:
                await self.api.close_session()

            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def check_event_loop():
    """Check if there's already a running event loop"""
    try:
        loop = asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False

async def main():
    """Main function"""
    print("🤖 Starting Telegram Anime Bot...")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")

    # Get bot token from environment variable
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN environment variable not set!")
        logger.error("Please create a .env file with your bot token:")
        logger.error("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        return

    logger.info(f"✅ Bot token loaded successfully (ends with: ...{bot_token[-10:]})")

    # Create and run bot
    bot = AnimeTelegramBot(bot_token)

    try:
        await bot.initialize()
        await bot.start_polling()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await bot.cleanup()

def run_bot():
    """Run the bot with proper event loop handling"""
    if check_event_loop():
        # If there's already a running event loop, create a new one in a thread
        logger.warning("Detected existing event loop, creating new one...")
        import threading
        import concurrent.futures

        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                new_loop.run_until_complete(main())
            finally:
                new_loop.close()

        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()
        thread.join()
    else:
        # Normal execution
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"🚨 Fatal error: {e}")

if __name__ == "__main__":
    run_bot()
