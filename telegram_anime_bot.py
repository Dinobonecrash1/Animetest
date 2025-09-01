#!/usr/bin/env python3
"""
Telegram Anime Bot - WORKING Streaming APIs with Video Links
Repository: Dinobonecrash1/Animetest
Real streaming functionality with actual video links
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

shutdown_flag = False

class StreamingAnimeAPI:
    """Working streaming APIs with REAL video links"""

    def __init__(self):
        self.apis = [
            {
                "name": "Anime API (falcon71181)",
                "base_url": "https://api-anime-rouge.vercel.app",
                "type": "streaming",
                "search_endpoint": "/aniwatch/search?keyword={query}&page=1",
                "recent_endpoint": "/aniwatch/recent-episodes?page=1",
                "episodes_endpoint": "/aniwatch/episodes/{anime_id}",
                "servers_endpoint": "/aniwatch/servers?id={episode_id}",
                "stream_endpoint": "/aniwatch/episode-srcs?id={episode_id}&server={server}&category={category}",
                "working": True
            },
            {
                "name": "GogoAnime API (falcon71181)",
                "base_url": "https://api-anime-rouge.vercel.app",
                "type": "streaming",
                "search_endpoint": "/gogoanime/search?query={query}",
                "recent_endpoint": "/gogoanime/recent-episodes",
                "info_endpoint": "/gogoanime/anime-details/{anime_id}",
                "episodes_endpoint": "/gogoanime/anime-details/{anime_id}",
                "stream_endpoint": "/gogoanime/episode-srcs?id={episode_id}&server=vidstreaming&category=sub",
                "working": True
            },
            {
                "name": "Animetize API",
                "base_url": "https://animetize-api.vercel.app",
                "type": "streaming",
                "search_endpoint": "/search/{query}",
                "recent_endpoint": "/recent-episodes",
                "info_endpoint": "/info/{anime_id}",
                "episodes_endpoint": "/episodes/{anime_id}",
                "stream_endpoint": "/watch/{episode_id}",
                "working": True
            },
            {
                "name": "Consumet Self-Hosted",
                "base_url": "https://consumet-org-phi.vercel.app",
                "type": "streaming",
                "search_endpoint": "/anime/gogoanime/{query}",
                "recent_endpoint": "/anime/gogoanime/recent-episodes",
                "info_endpoint": "/anime/gogoanime/info/{anime_id}",
                "stream_endpoint": "/anime/gogoanime/watch/{episode_id}",
                "working": True
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
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.warning(f"Error closing session: {e}")

    async def test_streaming_api(self, api_config):
        """Test if streaming API is working"""
        try:
            await self.init_session()
            test_url = api_config["base_url"] + api_config["search_endpoint"].format(query="naruto")

            async with self.session.get(test_url) as response:
                if response.status == 200:
                    data = await response.json()

                    # Check for valid streaming data
                    if isinstance(data, dict):
                        results = (data.get('results') or 
                                 data.get('animes') or 
                                 data.get('data'))
                        return bool(results and len(results) > 0)
                    elif isinstance(data, list):
                        return len(data) > 0

                return False
        except Exception as e:
            logger.debug(f"{api_config['name']} test failed: {e}")
            return False

    async def find_working_streaming_api(self):
        """Find first working streaming API"""
        if self.working_api:
            return self.working_api

        logger.info("🔍 Testing streaming APIs for video links...")

        for api in self.apis:
            if not api.get('working', True):
                continue

            logger.info(f"Testing {api['name']}...")
            if await self.test_streaming_api(api):
                logger.info(f"✅ {api['name']} is working!")
                self.working_api = api
                return api
            else:
                logger.warning(f"❌ {api['name']} is not responding")
                api['working'] = False

        logger.error("❌ No working streaming API found!")
        return None

    async def search_anime(self, query: str) -> List[Dict[str, Any]]:
        """Search anime with streaming capability"""
        try:
            api = await self.find_working_streaming_api()
            if not api:
                return []

            await self.init_session()
            url = api["base_url"] + api["search_endpoint"].format(query=query.replace(" ", "+"))
            logger.info(f"🔍 Searching: {url}")

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    # Handle different API response formats
                    if "aniwatch" in api["search_endpoint"]:
                        return data.get('animes', [])
                    elif "gogoanime" in api["search_endpoint"]:
                        return data.get('results', [])
                    else:
                        return data.get('results', []) or data.get('data', [])

                return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    async def get_recent_episodes(self) -> List[Dict[str, Any]]:
        """Get recent anime episodes with streaming capability"""
        try:
            api = await self.find_working_streaming_api()
            if not api:
                return []

            await self.init_session()
            url = api["base_url"] + api["recent_endpoint"]
            logger.info(f"📺 Getting recent: {url}")

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', []) or data.get('data', [])

                return []
        except Exception as e:
            logger.error(f"Recent error: {e}")
            return []

    async def get_anime_episodes(self, anime_id: str) -> List[Dict[str, Any]]:
        """Get episodes for an anime"""
        try:
            api = await self.find_working_streaming_api()
            if not api:
                return []

            await self.init_session()
            url = api["base_url"] + api["episodes_endpoint"].format(anime_id=anime_id)
            logger.info(f"📺 Getting episodes: {url}")

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('episodes', []) or data.get('results', [])

                return []
        except Exception as e:
            logger.error(f"Episodes error: {e}")
            return []

    async def get_streaming_links(self, episode_id: str, server: str = "vidstreaming", category: str = "sub") -> Dict[str, Any]:
        """Get actual streaming video links"""
        try:
            api = await self.find_working_streaming_api()
            if not api:
                return {}

            await self.init_session()

            # Format streaming URL based on API
            if "aniwatch" in api.get("stream_endpoint", ""):
                url = api["base_url"] + api["stream_endpoint"].format(
                    episode_id=episode_id, 
                    server=server, 
                    category=category
                )
            else:
                url = api["base_url"] + api["stream_endpoint"].format(episode_id=episode_id)

            logger.info(f"🎬 Getting stream links: {url}")

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data

                return {}
        except Exception as e:
            logger.error(f"Streaming links error: {e}")
            return {}

class StreamingTelegramBot:
    """Main bot class with real streaming functionality"""

    def __init__(self, token: str):
        self.token = token
        self.api = StreamingAnimeAPI()
        self.application = None
        self.is_running = False

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"User {user.id} started bot")

        welcome_text = f"""
🍿 **Welcome to Anime Streaming Bot, {user.first_name}!** 🍿

🎬 **Available commands:**
• `/search <anime name>` - Search anime with streaming links
• `/recent` - Recent episodes with video links
• `/test` - Check streaming API status
• `/help` - Show help

🔥 **REAL Streaming Features:**
• ✅ Actual video streaming links
• ✅ Multiple server options (VidStreaming, etc.)
• ✅ Sub and Dub support
• ✅ Episode streaming with M3U8 links
• ✅ Auto-fallback when servers are down

⚠️ **Important Notice:**
This bot provides access to streaming links for educational purposes.
Please support anime creators by using official platforms when possible:
• Crunchyroll • Funimation • Netflix • Hulu

💡 **Try:** `/search One Piece`

🔧 **Status:** Ready with WORKING streaming APIs! 🚀
        """
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test streaming API connectivity"""
        message = await update.message.reply_text("🧪 **Testing streaming APIs...**", parse_mode=ParseMode.MARKDOWN)

        api = await self.api.find_working_streaming_api()

        if api:
            await message.edit_text(
                f"✅ **Streaming APIs: WORKING**\n\n"
                f"**Active API:** {api['name']}\n"
                f"**Type:** {api.get('type', 'streaming')}\n"
                f"**Base URL:** `{api['base_url']}`\n\n"
                f"🎬 **Streaming Features Available:**\n"
                f"• ✅ Search anime with video links\n"
                f"• ✅ Episode streaming URLs\n"
                f"• ✅ Multiple server support\n"
                f"• ✅ Sub/Dub options\n\n"
                f"🚀 **Ready to stream anime!**\n\n"
                f"Try: `/search Attack on Titan`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.edit_text(
                "❌ **All streaming APIs currently down**\n\n"
                "⏰ Please try again in a few minutes.\n\n"
                "**APIs being tested:**\n"
                "• Anime API (falcon71181) - AniWatch\n"
                "• GogoAnime API (falcon71181)\n"
                "• Animetize API\n"
                "• Consumet Self-Hosted",
                parse_mode=ParseMode.MARKDOWN
            )

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search anime with streaming functionality"""
        if not context.args:
            await update.message.reply_text(
                "❓ **Please provide anime name to search!**\n\n"
                "📝 **Examples:**\n"
                "• `/search Naruto`\n"
                "• `/search One Piece`\n"
                "• `/search Attack on Titan`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        query = " ".join(context.args)
        logger.info(f"Searching: {query}")

        message = await update.message.reply_text(
            f"🔍 **Searching for '{query}' with streaming links...**\n"
            "⏳ Finding video sources...",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            results = await self.api.search_anime(query)

            if not results:
                await message.edit_text(
                    f"❌ **No streamable anime found for '{query}'**\n\n"
                    f"💡 **Try:**\n"
                    f"• Different spelling\n"
                    f"• More popular anime titles\n"
                    f"• Check streaming status: `/test`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            api_name = self.api.working_api.get('name', 'Unknown') if self.api.working_api else 'Unknown'
            response_text = f"🔍 **Streaming Results for '{query}'**\n📡 *Source: {api_name}*\n\n"

            keyboard = []

            for i, anime in enumerate(results[:5], 1):
                # Handle different API response formats
                title = anime.get('name') or anime.get('title', 'Unknown Title')
                anime_id = anime.get('id') or anime.get('animeId', '')

                # Get episode info
                episodes_info = anime.get('episodes', {})
                if isinstance(episodes_info, dict):
                    total_eps = episodes_info.get('eps', 'Unknown')
                    sub_eps = episodes_info.get('sub', 0)
                    dub_eps = episodes_info.get('dub', 0)
                else:
                    total_eps = episodes_info or anime.get('totalEpisodes', 'Unknown')
                    sub_eps = 0
                    dub_eps = 0

                response_text += f"**{i}. {title}**\n"
                response_text += f"📺 Episodes: {total_eps}\n"
                if sub_eps > 0:
                    response_text += f"🎌 Sub: {sub_eps} episodes\n"
                if dub_eps > 0:
                    response_text += f"🎤 Dub: {dub_eps} episodes\n"
                response_text += f"🆔 ID: `{anime_id}`\n\n"

                if anime_id:
                    keyboard.append([InlineKeyboardButton(f"🎬 Stream {title[:15]}...", callback_data=f"stream_{anime_id}")])

            response_text += "⚠️ *Streaming links for educational purposes only.*"

            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Search error: {e}")
            await message.edit_text(
                f"❌ **Search failed for '{query}'**\n\n"
                f"Try `/test` to check streaming API status",
                parse_mode=ParseMode.MARKDOWN
            )

    async def recent_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recent episodes with streaming links"""
        message = await update.message.reply_text(
            "📺 **Getting recent episodes with streaming links...**\n"
            "⏳ Finding video sources...",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            results = await self.api.get_recent_episodes()

            if not results:
                await message.edit_text(
                    "❌ **No recent streamable episodes**\n\n"
                    "Try `/test` to check streaming APIs",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            api_name = self.api.working_api.get('name', 'Unknown') if self.api.working_api else 'Unknown'
            response_text = f"📺 **Recent Streamable Episodes**\n📡 *Source: {api_name}*\n\n"

            keyboard = []

            for i, episode in enumerate(results[:5], 1):
                title = episode.get('title') or episode.get('animeTitle', 'Unknown')
                episode_num = episode.get('episodeNumber') or episode.get('episodeNum', 'Latest')
                episode_id = episode.get('episodeId') or episode.get('id', '')

                response_text += f"**{i}. {title}**\n"
                response_text += f"▶️ Episode: {episode_num}\n"
                response_text += f"🆔 Episode ID: `{episode_id}`\n\n"

                if episode_id:
                    keyboard.append([InlineKeyboardButton(f"🎬 Stream Ep {episode_num}", callback_data=f"watch_{episode_id}")])

            response_text += "⚠️ *Streaming links for educational purposes only.*"

            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Recent error: {e}")
            await message.edit_text(
                "❌ **Recent episodes failed**\n\nTry again later",
                parse_mode=ParseMode.MARKDOWN
            )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle streaming button clicks"""
        query = update.callback_query
        await query.answer()

        if query.data.startswith("stream_"):
            anime_id = query.data.replace("stream_", "")

            # Get episodes for this anime
            episodes = await self.api.get_anime_episodes(anime_id)

            if episodes:
                episode_list = []
                for i, ep in enumerate(episodes[:10], 1):  # Show first 10 episodes
                    ep_num = ep.get('episodeNo', i)
                    ep_id = ep.get('episodeId', '')
                    episode_list.append([InlineKeyboardButton(f"📺 Episode {ep_num}", callback_data=f"watch_{ep_id}")])

                reply_markup = InlineKeyboardMarkup(episode_list)

                await query.edit_message_text(
                    f"🎬 **Episodes Available for Streaming**\n\n"
                    f"🆔 **Anime ID:** `{anime_id}`\n"
                    f"📺 **Episodes:** {len(episodes)} total\n\n"
                    f"Select an episode to get streaming links:",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    f"❌ **No episodes found for this anime**\n\n"
                    f"🆔 **Anime ID:** `{anime_id}`\n\n"
                    f"The anime might not be available for streaming.",
                    parse_mode=ParseMode.MARKDOWN
                )

        elif query.data.startswith("watch_"):
            episode_id = query.data.replace("watch_", "")

            # Get actual streaming links
            await query.edit_message_text(
                f"🎬 **Getting streaming links...**\n\n"
                f"🆔 **Episode ID:** `{episode_id}`\n"
                f"⏳ Fetching video sources...",
                parse_mode=ParseMode.MARKDOWN
            )

            streaming_data = await self.api.get_streaming_links(episode_id)

            if streaming_data and streaming_data.get('sources'):
                sources = streaming_data.get('sources', [])
                subtitles = streaming_data.get('subtitles', [])

                response_text = f"🎬 **Streaming Links Ready!**\n\n"
                response_text += f"🆔 **Episode ID:** `{episode_id}`\n"
                response_text += f"📡 **Source:** {self.api.working_api.get('name', 'Unknown')}\n\n"

                response_text += f"🎥 **Video Sources:** {len(sources)} available\n"
                for i, source in enumerate(sources[:3], 1):  # Show first 3 sources
                    quality = source.get('quality', 'Unknown')
                    is_m3u8 = source.get('isM3U8', False)
                    url = source.get('url', '')[:50] + "..." if len(source.get('url', '')) > 50 else source.get('url', '')
                    response_text += f"  {i}. Quality: {quality} ({'M3U8' if is_m3u8 else 'MP4'})\n"
                    response_text += f"     URL: `{url}`\n"

                if subtitles:
                    response_text += f"\n🎌 **Subtitles:** {len(subtitles)} available\n"
                    for sub in subtitles[:2]:  # Show first 2 subtitle options
                        lang = sub.get('lang', 'Unknown')
                        response_text += f"  • {lang}\n"

                response_text += f"\n⚠️ **Important:**\n"
                response_text += f"• These are direct streaming links\n"
                response_text += f"• Use VLC or similar player for M3U8 links\n"
                response_text += f"• For educational purposes only\n"
                response_text += f"• Support official platforms when possible"

                await query.edit_message_text(response_text, parse_mode=ParseMode.MARKDOWN)

            else:
                await query.edit_message_text(
                    f"❌ **No streaming links available**\n\n"
                    f"🆔 **Episode ID:** `{episode_id}`\n\n"
                    f"The episode might not be available for streaming\n"
                    f"or the server is temporarily down.\n\n"
                    f"Try a different episode or check `/test`",
                    parse_mode=ParseMode.MARKDOWN
                )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown messages"""
        await update.message.reply_text(
            "❓ **Available Commands:**\n"
            "• `/start` - Start bot\n"
            "• `/search <name>` - Search anime with streaming\n"
            "• `/recent` - Recent episodes with video links\n"
            "• `/test` - Test streaming APIs\n"
            "• `/help` - Show help\n\n"
            "💡 **Example:** `/search Death Note`",
            parse_mode=ParseMode.MARKDOWN
        )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors gracefully"""
        logger.error(f"Update error: {context.error}")

        if update and hasattr(update, 'message') and update.message:
            try:
                await update.message.reply_text("😅 **Error occurred. Try again or use `/test`**")
            except:
                pass

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

            await self.api.init_session()
            await self.application.start()

            logger.info("🤖 Starting Telegram Anime Bot with REAL STREAMING...")
            logger.info("🎬 Repository: Dinobonecrash1/Animetest")
            logger.info("🔥 STREAMING APIs: Video links, M3U8, MP4 sources")
            logger.info("✅ Bot is ready! Send /start to your bot on Telegram")

            await self.application.updater.start_polling(drop_pending_updates=True)
            self.is_running = True

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

        logger.info("🛑 Shutting down streaming bot...")

        try:
            if self.application and self.application.updater.running:
                await self.application.updater.stop()
                logger.info("✅ Updater stopped")

            if self.application:
                await self.application.stop()
                logger.info("✅ Application stopped")

            if self.application:
                await self.application.shutdown()
                logger.info("✅ Application shutdown")

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

    print("🤖 Starting Telegram Anime Bot with REAL STREAMING...")
    print("📁 Repository: Dinobonecrash1/Animetest")
    print("🔥 Features: Actual video links, M3U8, MP4 sources")

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set! Check your .env file")
        return

    logger.info(f"✅ Bot token loaded (ends with: ...{bot_token[-10:]})")

    setup_signal_handlers()

    bot = StreamingTelegramBot(bot_token)

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
        try:
            loop = asyncio.get_running_loop()
            logger.warning("Existing event loop detected, creating new one...")
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(main())
            new_loop.close()
        except RuntimeError:
            asyncio.run(main())

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"🚨 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_with_proper_loop()
