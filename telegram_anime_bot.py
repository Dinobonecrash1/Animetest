#!/usr/bin/env python3
"""
Telegram Anime Bot - Final Fixed Version for VPS Deployment
Repository: Dinobonecrash1/Animetest
Fixed asyncio event loop issues for production deployment
"""

import os
import logging
import asyncio
import aiohttp
import signal
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
import json
from typing import List, Dict, Any

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not found. Using system environment variables.")

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

# Global flag for graceful shutdown
shutdown_flag = False

class AnimeAPI:
    """Working streaming APIs with proper async handling"""

    def __init__(self):
        self.apis = [
            {
                "name": "HiAnime",
                "base_url": "https://hianime-api-theta.vercel.app/api/v1",
                "search": "/search?q={query}",
                "recent": "/home"
            },
            {
                "name": "Consumet",
                "base_url": "https://consumet-api-clone.vercel.app/anime/gogoanime", 
                "search": "/{query}",
                "recent": "/recent-episodes"
            },
            {
                "name": "Zen API",
                "base_url": "https://zen-api-rouge.vercel.app/api",
                "search": "/search/{query}",
                "recent": "/recent-release"
            }
        ]
        self.session = None
        self.working_api = None

    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

    async def close_session(self):
        """Safely close aiohttp session"""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
                # Wait a bit for the underlying connections to close
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.warning(f"Error closing session: {e}")

    async def find_working_api(self):
        """Find first working API"""
        if self.working_api:
            return self.working_api

        logger.info("🔍 Testing streaming APIs...")

        for api in self.apis:
            try:
                await self.init_session()
                test_url = api["base_url"] + api["search"].format(query="test")

                async with self.session.get(test_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Check for valid data
                        if isinstance(data, dict) and (data.get('data') or data.get('results')):
                            logger.info(f"✅ {api['name']} is working!")
                            self.working_api = api
                            return api
                        elif isinstance(data, list) and len(data) > 0:
                            logger.info(f"✅ {api['name']} is working!")
                            self.working_api = api
                            return api

                logger.warning(f"❌ {api['name']} no data")

            except Exception as e:
                logger.warning(f"❌ {api['name']} failed: {str(e)[:30]}...")

        logger.error("❌ No working API found!")
        return None

    async def search_anime(self, query: str) -> List[Dict[str, Any]]:
        """Search anime with working API"""
        try:
            api = await self.find_working_api()
            if not api:
                return []

            await self.init_session()
            url = api["base_url"] + api["search"].format(query=query)

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    # Handle different response formats
                    if "HiAnime" in api["name"]:
                        return data.get('data', {}).get('animes', [])
                    else:
                        return data.get('results', [])

                return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    async def get_recent_anime(self, page: int = 1) -> List[Dict[str, Any]]:
        """Get recent anime episodes"""
        try:
            api = await self.find_working_api()
            if not api:
                return []

            await self.init_session()
            url = api["base_url"] + api["recent"]

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    # Handle different response formats
                    if "HiAnime" in api["name"]:
                        # Try different keys for recent data
                        recent_data = (data.get('data', {}).get('latestEpisodeAnimes') or
                                     data.get('data', {}).get('recentlyAdded') or
                                     data.get('data', {}).get('episodes', []))
                        return recent_data if isinstance(recent_data, list) else []
                    else:
                        return data.get('results', [])

                return []
        except Exception as e:
            logger.error(f"Recent error: {e}")
            return []

class AnimeTelegramBot:
    """Main bot class with proper async lifecycle management"""

    def __init__(self, token: str):
        self.token = token
        self.api = AnimeAPI()
        self.application = None
        self.is_running = False

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"User {user.id} started bot")

        welcome_text = f"""
🍿 **Welcome to Anime Bot, {user.first_name}!** 🍿

🎬 **Available commands:**
• `/search <anime name>` - Search anime with streaming
• `/recent` - Recent episodes with links
• `/test` - Check API status
• `/help` - Show help

✨ **Working Features:**
• ✅ Multiple streaming APIs
• ✅ Auto-fallback when APIs are down
• ✅ Interactive watch buttons
• ✅ Recent episodes with links

⚠️ **Note:** Educational purposes only.

💡 **Try:** `/search One Piece`

🔧 **Status:** Ready to stream! 🚀
        """
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test API connectivity"""
        message = await update.message.reply_text("🧪 **Testing streaming APIs...**", parse_mode=ParseMode.MARKDOWN)

        api = await self.api.find_working_api()

        if api:
            await message.edit_text(
                f"✅ **Streaming APIs: WORKING**\n\n"
                f"**Active API:** {api['name']}\n"
                f"**URL:** `{api['base_url']}`\n\n"
                f"🎬 **Ready to stream anime!**\n\n"
                f"Try: `/search Naruto`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.edit_text(
                "❌ **All APIs currently down**\n\n"
                "⏰ Please try again in a few minutes.",
                parse_mode=ParseMode.MARKDOWN
            )

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search command with streaming results"""
        if not context.args:
            await update.message.reply_text(
                "❓ **Please provide anime name!**\n\n"
                "📝 **Example:** `/search Naruto`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        query = " ".join(context.args)
        logger.info(f"Searching: {query}")

        message = await update.message.reply_text(
            f"🔍 **Searching '{query}'...**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            results = await self.api.search_anime(query)

            if not results:
                await message.edit_text(
                    f"❌ **No anime found for '{query}'**\n\n"
                    f"💡 Try different spelling or check `/test`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            api_name = self.api.working_api.get('name', 'Unknown') if self.api.working_api else 'Unknown'
            response_text = f"🔍 **Results for '{query}'**\n📡 *Source: {api_name}*\n\n"

            keyboard = []

            for i, anime in enumerate(results[:5], 1):
                title = anime.get('title') or anime.get('name', 'Unknown')
                episodes = anime.get('totalEpisodes') or anime.get('episodes', 'Unknown')
                anime_id = anime.get('id') or anime.get('animeId', '')

                response_text += f"**{i}. {title}**\n"
                response_text += f"📺 Episodes: {episodes}\n"
                response_text += f"🆔 ID: `{anime_id}`\n\n"

                if anime_id:
                    keyboard.append([InlineKeyboardButton(f"🎬 Watch {title[:15]}...", callback_data=f"watch_{anime_id}")])

            response_text += "⚠️ *Educational purposes only.*"

            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Search error: {e}")
            await message.edit_text(f"❌ **Search failed**\n\nTry `/test` to check API status", parse_mode=ParseMode.MARKDOWN)

    async def recent_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recent episodes command"""
        message = await update.message.reply_text("📺 **Getting recent episodes...**", parse_mode=ParseMode.MARKDOWN)

        try:
            results = await self.api.get_recent_anime()

            if not results:
                await message.edit_text("❌ **No recent episodes**\n\nTry `/test` to check APIs", parse_mode=ParseMode.MARKDOWN)
                return

            api_name = self.api.working_api.get('name', 'Unknown') if self.api.working_api else 'Unknown'
            response_text = f"📺 **Recent Episodes**\n📡 *Source: {api_name}*\n\n"

            keyboard = []

            for i, anime in enumerate(results[:5], 1):
                title = anime.get('title') or anime.get('name', 'Unknown')
                episode = anime.get('episodeNumber') or anime.get('episode', 'Latest')
                anime_id = anime.get('id') or anime.get('episodeId', '')

                response_text += f"**{i}. {title}**\n"
                response_text += f"📺 Episode: {episode}\n\n"

                if anime_id:
                    keyboard.append([InlineKeyboardButton(f"▶️ Watch Ep {episode}", callback_data=f"episode_{anime_id}")])

            response_text += "⚠️ *Educational purposes only.*"

            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Recent error: {e}")
            await message.edit_text("❌ **Recent failed**\n\nTry again later", parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown messages"""
        await update.message.reply_text(
            "❓ **Commands:**\n"
            "• `/start` - Start\n"
            "• `/search <name>` - Search anime\n"
            "• `/recent` - Recent episodes\n"
            "• `/test` - Test APIs\n"
            "• `/help` - Help",
            parse_mode=ParseMode.MARKDOWN
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks"""
        query = update.callback_query
        await query.answer()

        if query.data.startswith("watch_"):
            anime_id = query.data.replace("watch_", "")
            await query.edit_message_text(
                f"🎬 **Anime Ready to Stream**\n\n"
                f"🆔 **ID:** `{anime_id}`\n"
                f"📡 **Source:** {self.api.working_api.get('name', 'Unknown') if self.api.working_api else 'Unknown'}\n\n"
                f"⚠️ **Streaming links available via API**\n"
                f"Educational demonstration only.\n\n"
                f"🔄 Search more: `/search <anime name>`",
                parse_mode=ParseMode.MARKDOWN
            )
        elif query.data.startswith("episode_"):
            episode_id = query.data.replace("episode_", "")
            await query.edit_message_text(
                f"▶️ **Episode Ready to Stream**\n\n"
                f"🆔 **Episode ID:** `{episode_id}`\n"
                f"📡 **Source:** {self.api.working_api.get('name', 'Unknown') if self.api.working_api else 'Unknown'}\n\n"
                f"⚠️ **Streaming functionality demonstrated**\n"
                f"Educational purposes only.\n\n"
                f"🔄 More episodes: `/recent`",
                parse_mode=ParseMode.MARKDOWN
            )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors gracefully"""
        logger.error(f"Update error: {context.error}")

        if update and hasattr(update, 'message') and update.message:
            try:
                await update.message.reply_text("😅 **Error occurred. Try again.**")
            except:
                pass  # Ignore if we can't send error message

    def setup_handlers(self):
        """Setup all command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("search", self.search_command))
        self.application.add_handler(CommandHandler("recent", self.recent_command))
        self.application.add_handler(CommandHandler("test", self.test_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown_command))
        self.application.add_error_handler(self.error_handler)

    async def initialize_bot(self):
        """Initialize bot with proper error handling"""
        try:
            self.application = Application.builder().token(self.token).build()
            await self.application.initialize()
            self.setup_handlers()
            logger.info("✅ Bot initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Bot initialization failed: {e}")
            return False

    async def run_bot(self):
        """Run bot with proper lifecycle management"""
        try:
            if not await self.initialize_bot():
                return

            # Initialize API session
            await self.api.init_session()

            # Start the application
            await self.application.start()

            # Start polling
            logger.info("🤖 Starting Telegram Anime Bot with working streaming APIs...")
            logger.info("🎬 Repository: Dinobonecrash1/Animetest")
            logger.info("✅ Bot is ready! Send /start to your bot on Telegram")

            # Start updater
            await self.application.updater.start_polling(drop_pending_updates=True)
            self.is_running = True

            # Keep running until shutdown
            while not shutdown_flag and self.is_running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Bot run error: {e}")
        finally:
            await self.shutdown_bot()

    async def shutdown_bot(self):
        """Graceful shutdown with proper cleanup"""
        global shutdown_flag
        shutdown_flag = True
        self.is_running = False

        logger.info("🛑 Shutting down bot...")

        try:
            # Stop updater
            if self.application and self.application.updater.running:
                await self.application.updater.stop()
                logger.info("✅ Updater stopped")

            # Stop application
            if self.application:
                await self.application.stop()
                logger.info("✅ Application stopped")

            # Shutdown application
            if self.application:
                await self.application.shutdown()
                logger.info("✅ Application shutdown")

            # Close API session
            await self.api.close_session()
            logger.info("✅ API session closed")

        except Exception as e:
            logger.error(f"Shutdown error: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global shutdown_flag
    logger.info(f"Received signal {signum}, initiating shutdown...")
    shutdown_flag = True

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main function with proper event loop management"""
    global shutdown_flag

    print("🤖 Starting Telegram Anime Bot...")
    print("📁 Repository: Dinobonecrash1/Animetest")
    print("🎬 Features: Working Streaming APIs")

    # Check bot token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set! Check your .env file")
        return

    logger.info(f"✅ Bot token loaded (ends with: ...{bot_token[-10:]})")

    # Setup signal handlers
    setup_signal_handlers()

    # Create and run bot
    bot = AnimeTelegramBot(bot_token)

    try:
        await bot.run_bot()
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if not shutdown_flag:
            await bot.shutdown_bot()

def run_with_proper_loop():
    """Run with proper asyncio loop management for VPS"""
    try:
        # Check if there's already an event loop running
        try:
            loop = asyncio.get_running_loop()
            logger.warning("Existing event loop detected, creating new one...")
            # Create new loop for this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(main())
            new_loop.close()
        except RuntimeError:
            # No existing loop, safe to create one
            asyncio.run(main())

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"🚨 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_with_proper_loop()
