from aiogram import Bot, Dispatcher
from config_reader import config
from config_reader import USER_ACTIVITY_LOG_FILE
import asyncio

import logging


bot = Bot(token = config.bot_token.get_secret_value())
dp = Dispatcher()




async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers={
            logging.FileHandler(USER_ACTIVITY_LOG_FILE , mode = "a"),
            logging.StreamHandler()
        }
    )
    # dp.include_router()
    await dp.start_polling(bot)
    
    if __name__ == "__main__":
        try:
            
            asyncio.run(main())
            
        except (KeyboardInterrupt, SystemExit):
            logging.error("Bot stopped!")