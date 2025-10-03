import asyncio
import contextlib
import logging
import shutil

from aiogram import Bot, Dispatcher

from config_reader import USER_ACTIVITY_LOG_FILE, config
from handlers.messages_ai_handler import router as ai_router
from handlers.song_handler import router as song_router
from handlers.task_handler import router as task_router
from handlers.weather_handler import router as weather_router

from buttons.buttons import router as buttons_router
from buttons.buttons import set_default_commands

from utils.weather_broadcast import broadcast_daily_weather


bot = Bot(token = config.bot_token.get_secret_value())
dp = Dispatcher()


def verify_external_tools() -> None:
    """Log a warning if required external tools are missing."""

    missing_tools = [tool for tool in ("ffmpeg", "yt-dlp") if shutil.which(tool) is None]
    if missing_tools:
        logging.warning(
            "Missing external dependencies: %s. Please install them before deploying the bot.",
            ", ".join(missing_tools),
        )
    else:
        logging.info(
            "External tools ffmpeg and yt-dlp detected. Ensure downloads comply with YouTube's Terms of Service."
        )


async def main():
    """
    Start the bot.

    1. Set up logging with level INFO and format '%(asctime)s - %(levelname)s - %(name)s - %(message)s'.
    2. Include the router for buttons.
    3. Include the router for ai.
    4. Set default commands for the bot.
    5. Start polling for the bot.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(USER_ACTIVITY_LOG_FILE , mode = "a"),
            logging.StreamHandler()
        ]
    )

    verify_external_tools()

    dp.include_router(buttons_router)
    dp.include_router(task_router)
    dp.include_router(song_router)
    dp.include_router(ai_router)
    dp.include_router(weather_router)
    await set_default_commands(bot)

    broadcast_task = None
    if (
        config.weather_broadcast_time
        and config.weather_broadcast_cities
        and config.weather_broadcast_chat_ids
    ):
        logging.info(
            "Scheduling daily weather broadcast at %s for %d chat(s).",
            config.weather_broadcast_time.strftime("%H:%M"),
            len(config.weather_broadcast_chat_ids),
        )
        broadcast_task = asyncio.create_task(
            broadcast_daily_weather(
                bot,
                config.weather_broadcast_chat_ids,
                config.weather_broadcast_cities,
                send_at=config.weather_broadcast_time,
            )
        )
    else:
        logging.info(
            "Weather broadcast disabled. Provide WEATHER_BROADCAST_CHAT_IDS, "
            "WEATHER_BROADCAST_CITIES and WEATHER_BROADCAST_TIME to enable it."
        )

    try:
        await dp.start_polling(bot)
    finally:
        if broadcast_task:
            broadcast_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await broadcast_task
    
    
if __name__ == "__main__":
    try:
        
        asyncio.run(main())
        
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
        