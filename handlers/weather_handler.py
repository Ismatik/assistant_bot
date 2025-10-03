import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# --- Import the functions you've already written! ---
from utils.weather import fetch_weather_by_city, LocationNotFoundError, WeatherServiceError
from utils.weather_broadcast import format_weather_info # We can reuse the formatter!
from config_reader import config

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("weather"))
async def get_weather_command(message: Message, bot: Bot, command: Command):
    city = command.args.strip()
    
    if not city:
        await message.answer("Please provide a city name after the command.\nExample: `/weather Dushanbe`", parse_mode="MarkdownV2")
        return
    
    logger.info(f"User {message.from_user.id} requested weather for city: {city}")
    
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        weather_data = fetch_weather_by_city(
            city=city,
            api_key=config.weather_api_key.get_secret_value()
        )
        report = format_weather_info(weather_data, requested_city=city)
        await message.answer(
            report,
            parse_mode="HTML"
            )
        
    except LocationNotFoundError:
        logger.warning(f"Could not find location for city: {city}")
        await message.answer(f"Sorry, I couldn't find the location for '{city}'. Please check the spelling.")
    except WeatherServiceError as e:
        logger.error(f"Weather service error for city {city}: {e}")
        await message.answer("Sorry, there was an error fetching the weather data. Please try again later.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred in get_weather_command for city {city}: {e}")
        await message.answer("An unexpected error occurred. Please try again.")