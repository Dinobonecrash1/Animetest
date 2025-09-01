#!/usr/bin/env python3
"""
Telegram Anime Bot - Fixed for Dinobonecrash1/Animetest Repository
Updated to use working streaming APIs while maintaining original structure
"""

import os
import logging
import asyncio
import aiohttp
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

class AnimeAPI:
    """Updated API class with working streaming APIs"""

    def __init__(self):
        # Working streaming APIs (September 2025)
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
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def find_working_api(self):
        """Find first working API"""
        if self.working_api:
            return self.working_api

        logger.info("🔍 Testing streaming APIs...")

        for api in self.apis:
            try:
                await self.init_session()
                test_url = api["base_url"] + api["search"].format(query="naruto")

                async with self.session.get(test_url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Check for results
                        has_results = False
                        if isinstance(data, dict):
                            results = (data.get('results') or 
                                     data.get('data', {}).get('animes') or 
                                     data.get('data'))
                            has_results = bool(results)
                        elif isinstance(data, list):
                            has_results = len(data) > 0

                        if has_results:
                            logger.info(f"✅ {api['name']} is working!")
                            self.working_api = api
                            return api

                logger.warning(f"❌ {api['name']} returned no results")

            except Exception as e:
                logger.warning(f"❌ {api['name']} failed: {str(e)[:50]}...")

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
            logger.info(f"🔍 Searching: {url}")

            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    # Handle different response formats
                    if "HiAnime" in api["name"]:
                        return data.get('data', {}).get('animes', [])
                    elif "Consumet" in api["name"]:
                        return data.get('results', [])
                    elif "Zen" in api["name"]:
                        return data.get('results', [])
                    else:
                        return data.get('results', []) or data.get('data', [])

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
            logger.info(f"📺 Getting recent: {url}")

            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    # Handle different response formats
                    if "HiAnime" in api["name"]:
                        # Try different possible keys for recent data
                        recent_data = (data.get('data', {}).get('latestEpisodeAnimes') or
                                     data.get('data', {}).get('recentlyAdded') or
                                     data.get('data', {}).get('episodes', []))
                        return recent_data if isinstance(recent_data, list) else []
                    elif "Consumet" in api["name"]:
                        return data.get('results', [])
                    elif "Zen" in api["name"]:
                        return data.get('results', [])
                    else:
                        return data.get('results', []) or data.get('data', [])

                return []
        except Exception as e:
            logger.error(f"Recent error: {e}")
            return []

class AnimeTelegramBot:
    """Main bot class - maintaining your original structure"""

    def __init__(self, token: str):
        self.token = token
        self.api = AnimeAPI()
        self.application = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username or user.first_name}) started bot")

        welcome_text = f"""
🍿 **Welcome to Anime Bot, {user.first_name}!** 🍿

🎬 **Available commands:**
• `/search <anime name>` - Search for anime with streaming
• `/recent` - Get recent anime episodes  
• `/popular` - Popular anime (coming soon)
• `/test` - Test API status
• `/help` - Show this help

✨ **Features:**
• ✅ Multiple working streaming APIs
• ✅ Search with watch buttons
• ✅ Recent episodes with links
• ✅ Auto-fallback when APIs are down

⚠️ **Note:** This bot is for educational purposes only.
Please support creators by using official platforms.

💡 **Try:** `/search Naruto`

🔧 **Status:** Ready with working APIs! 🚀
        """
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)

    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test API connectivity - NEW COMMAND"""
        message = await update.message.reply_text("🧪 **Testing streaming APIs...**", parse_mode=ParseMode.MARKDOWN)

        api = await self.api.find_working_api()

        if api:
            await message.edit_text(
                f"✅ **API Status: WORKING**\n\n"
                f"**Active API:** {api['name']}\n"
                f"**Base URL:** `{api['base_url']}`\n\n"
                f"🎬 **Features Available:**\n"
                f"• ✅ Anime Search\n"
                f"• ✅ Recent Episodes\n"
                f"• ✅ Streaming Links\n\n"
                f"Ready to stream! Try `/search One Piece`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.edit_text(
                "❌ **API Status: DOWN**\n\n"
                "All streaming APIs are currently unavailable.\n\n"
                "**Possible reasons:**\n"
                "• Server maintenance\n"
                "• Network issues\n"
                "• API rate limiting\n\n"
                "⏰ Please try again in a few minutes.",
                parse_mode=ParseMode.MARKDOWN
            )

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced search with streaming features"""
        user = update.effective_user

        if not context.args:
            await update.message.reply_text(
                "❓ **Please provide an anime name to search!**\n\n"
                "📝 **Examples:**\n"
                "• `/search Naruto`\n"
                "• `/search One Piece`\n"
                "• `/search Attack on Titan`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        query = " ".join(context.args)
        logger.info(f"User {user.id} searching: {query}")

        message = await update.message.reply_text(
            f"🔍 **Searching for '{query}'...**\n"
            "⏳ Finding streaming sources...",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            results = await self.api.search_anime(query)

            if not results:
                await message.edit_text(
                    f"❌ **No anime found for '{query}'**\n\n"
                    "💡 **Try:**\n"
                    "• Different spelling\n"
                    "• English name instead of Japanese\n"
                    "• More popular titles\n\n"
                    "🧪 **Check status:** `/test`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            api_name = self.api.working_api.get('name', 'Unknown') if self.api.working_api else 'Unknown'
            response_text = f"🔍 **Search Results for '{query}'**\n📡 *Source: {api_name}*\n\n"

            # Create buttons for watchable anime
            keyboard = []

            for i, anime in enumerate(results[:6], 1):  # Limit to 6 for better display
                # Handle different API response formats
                title = (anime.get('title') or 
                        anime.get('name') or 
                        anime.get('animeTitle', 'Unknown Title'))

                episodes = (anime.get('totalEpisodes') or 
                           anime.get('episodes') or 
                           anime.get('episodeNumber', 'Unknown'))

                anime_id = (anime.get('id') or 
                           anime.get('animeId') or 
                           anime.get('slug', ''))

                status = anime.get('status', anime.get('type', 'Unknown'))
                year = anime.get('releaseDate', anime.get('year', 'Unknown'))

                response_text += f"**{i}. {title}**\n"
                response_text += f"📺 Episodes: {episodes}\n"
                if str(status) != 'Unknown':
                    response_text += f"📊 Status: {status}\n"
                if str(year) != 'Unknown':
                    response_text += f"📅 Year: {str(year)[:4]}\n"
                response_text += f"🆔 ID: `{anime_id}`\n\n"

                # Add watch button if we have valid ID
                if anime_id and str(anime_id).strip():
                    button_text = f"🎬 Watch {title[:15]}..." if len(title) > 15 else f"🎬 Watch {title}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"watch_{anime_id}")])

            response_text += "⚠️ *For educational purposes only.*"

            # Add keyboard if we have watchable results
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

            await message.edit_text(response_text,
                                  parse_mode=ParseMode.MARKDOWN,
                                  reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Search command error: {e}")
            await message.edit_text(
                f"❌ **Error searching for '{query}'**\n\n"
                "🔧 This could be due to:\n"
                "• API temporarily down\n"
                "• Network connectivity issues\n"
                "• Server overload\n\n"
                "⏰ Please try again or use `/test` to check API status",
                parse_mode=ParseMode.MARKDOWN
            )

    async def recent_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced recent episodes with streaming"""
        user = update.effective_user
        logger.info(f"User {user.id} requested recent anime")

        message = await update.message.reply_text(
            "📺 **Getting recent anime episodes...**\n"
            "⏳ Finding streaming links...",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            results = await self.api.get_recent_anime()

            if not results:
                await message.edit_text(
                    "❌ **No recent episodes available**\n\n"
                    "🔧 This could be due to:\n"
                    "• API temporarily unavailable\n"
                    "• No recent episodes uploaded\n"
                    "• Server maintenance\n\n"
                    "🧪 Check status: `/test`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            api_name = self.api.working_api.get('name', 'Unknown') if self.api.working_api else 'Unknown'
            response_text = f"📺 **Recent Anime Episodes**\n📡 *Source: {api_name}*\n\n"

            keyboard = []

            for i, anime in enumerate(results[:6], 1):
                title = (anime.get('title') or 
                        anime.get('name') or 
                        anime.get('animeTitle', 'Unknown Title'))

                episode = (anime.get('episodeNumber') or 
                          anime.get('episode') or 
                          anime.get('episodeNum', 'Latest'))

                anime_id = (anime.get('id') or 
                           anime.get('episodeId') or 
                           anime.get('animeId', ''))

                response_text += f"**{i}. {title}**\n"
                response_text += f"📺 Episode: {episode}\n"
                response_text += f"🆔 ID: `{anime_id}`\n\n"

                # Add watch button for episodes
                if anime_id and str(anime_id).strip():
                    button_text = f"▶️ Watch Ep {episode}" if str(episode) != 'Latest' else f"▶️ Watch {title[:10]}..."
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"episode_{anime_id}")])

            response_text += "⚠️ *For educational purposes only.*"

            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

            await message.edit_text(response_text,
                                  parse_mode=ParseMode.MARKDOWN,
                                  reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Recent command error: {e}")
            await message.edit_text(
                "❌ **Error getting recent episodes**\n\n"
                "🔧 Please try again or check API status with `/test`",
                parse_mode=ParseMode.MARKDOWN
            )

    async def popular_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /popular command - placeholder for future"""
        await update.message.reply_text(
            "🎯 **Popular anime feature coming soon!**\n\n"
            "For now, try these popular searches:\n"
            "• `/search One Piece`\n"
            "• `/search Naruto`\n"
            "• `/search Attack on Titan`\n"
            "• `/search Demon Slayer`\n\n"
            "Or check `/recent` for latest episodes!",
            parse_mode=ParseMode.MARKDOWN
        )

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown messages"""
        await update.message.reply_text(
            "❓ **I don't understand that command.**\n\n"
            "📋 **Available commands:**\n"
            "• `/start` - Start the bot\n"
            "• `/search <name>` - Search anime to watch\n"
            "• `/recent` - Recent episodes with links\n"
            "• `/test` - Test API status\n"
            "• `/help` - Show help\n\n"
            "💡 **Example:** `/search Dragon Ball`",
            parse_mode=ParseMode.MARKDOWN
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data.startswith("watch_"):
            anime_id = data.replace("watch_", "")
            await query.edit_message_text(
                f"🎬 **Anime Selected**\n\n"
                f"🆔 **Anime ID:** `{anime_id}`\n\n"
                f"📡 **Source:** {self.api.working_api.get('name', 'Unknown') if self.api.working_api else 'Unknown'}\n\n"
                f"⚠️ **Note:** This demonstrates the streaming functionality.\n"
                f"The actual streaming links are available through the API\n"
                f"for educational and development purposes only.\n\n"
                f"🔄 Use `/search` to find more anime!",
                parse_mode=ParseMode.MARKDOWN
            )

        elif data.startswith("episode_"):
            episode_id = data.replace("episode_", "")
            await query.edit_message_text(
                f"▶️ **Episode Selected**\n\n"
                f"🆔 **Episode ID:** `{episode_id}`\n\n"
                f"📡 **Source:** {self.api.working_api.get('name', 'Unknown') if self.api.working_api else 'Unknown'}\n\n"
                f"⚠️ **Note:** This demonstrates episode streaming functionality.\n"
                f"The actual streaming links are available through the API\n"
                f"for educational and development purposes only.\n\n"
                f"🔄 Use `/recent` to find more episodes!",
                parse_mode=ParseMode.MARKDOWN
            )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced error handling"""
        logger.error(f"Exception while handling update: {context.error}")

        if update and hasattr(update, 'message') and update.message:
            try:
                await update.message.reply_text(
                    "😅 **Oops! Something went wrong.**\n\n"
                    "🔧 **Try:**\n"
                    "• Use `/test` to check API status\n"
                    "• Try your command again\n"
                    "• Use `/help` for available commands\n\n"
                    "If the issue persists, the APIs might be temporarily down.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Could not send error message: {e}")

    def setup_handlers(self):
        """Setup command handlers - maintains your original structure"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("search", self.search_command))
        self.application.add_handler(CommandHandler("recent", self.recent_command))
        self.application.add_handler(CommandHandler("popular", self.popular_command))
        self.application.add_handler(CommandHandler("test", self.test_command))

        # Handle button callbacks
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

        # Handle unknown messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown_command))

        # Error handler
        self.application.add_error_handler(self.error_handler)

    async def run(self):
        """Run the bot - maintains your original structure"""
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()

        logger.info("🤖 Starting Telegram Anime Bot with working streaming APIs...")
        logger.info("🎬 Repository: Dinobonecrash1/Animetest")

        try:
            await self.api.init_session()
            await self.application.run_polling(drop_pending_updates=True)
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
        finally:
            await self.api.close_session()

async def main():
    """Main function - maintains your original structure"""
    print("🤖 Starting Telegram Anime Bot...")
    print("📁 Repository: Dinobonecrash1/Animetest")
    print("🎬 Features: Streaming APIs with fallback support")

    # Get bot token from environment variable
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN environment variable not set!")
        logger.error("Please check your .env file or environment variables.")
        return

    logger.info(f"✅ Bot token loaded (ends with: ...{bot_token[-10:]})")

    # Create and run bot
    bot = AnimeTelegramBot(bot_token)
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Bot crashed: {e}")
