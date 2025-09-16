import logging
from aiogram import Router, F, types, Bot
from aiogram.filters import Command 
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from google import genai
from config_reader import config 

client = genai.Client(api_key=config.gemini_api_key.get_secret_value())
model = 'gemini-2.5-pro'

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_command(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot.")
    await message.answer("Hello! I'm Ismat's AI assistant. How can I help you today?")

    

@router.message(Command("help"))
async def help_command(message: types.Message):
    help_text = (
        "I can assist you with various tasks using AI. "
        "Just send me a message with your request, and I'll do my best to help!\n\n"
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message"
    )

    logger.info(f"User {message.from_user.id} requested help.")
    await message.answer(help_text)

async def set_default_commands(bot: Bot):
    commands = [
        types.BotCommand(command="/start", description="Start the bot"),
        types.BotCommand(command="/help", description="Show help message"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Default commands set.")
