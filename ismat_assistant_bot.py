from aiogram import Bot, Dispatcher
from config_reader import config
from config_reader import USER_ACTIVITY_LOG_FILE
import asyncio
from handlers.messages_ai_handler import router as ai_router

from buttons.buttons import router as buttons_router
from buttons.buttons import set_default_commands

import logging


bot = Bot(token = config.bot_token.get_secret_value())
dp = Dispatcher()


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
        handlers={
            logging.FileHandler(USER_ACTIVITY_LOG_FILE , mode = "a"),
            logging.StreamHandler()
        }
    )
    
    dp.include_router(buttons_router)
    dp.include_router(ai_router)
    await set_default_commands(bot)
    await dp.start_polling(bot)
    
    
if __name__ == "__main__":
    try:
        
        asyncio.run(main())
        
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
        
