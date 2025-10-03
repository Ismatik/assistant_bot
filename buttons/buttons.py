import logging
from aiogram import Router, F, types, Bot
from aiogram.filters import Command 
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from google import genai
from config_reader import config
from utils.utils import UserSettings
client = genai.Client(api_key=config.gemini_api_key.get_secret_value())
# model = 'gemini-2.5-pro'

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_command(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot.")
    message_text = (
        "Hello! I'm your AI assistant, powered by Google Gemini. "
        "Feel free to ask me anything or request assistance with various tasks. "
        "Type /help to see what I can do."
    )
    await message.answer(message_text)
    
    
@router.message(Command("select_model"))
async def select_model_command(message: types.Message, model: str = "gemini-2.5-pro"):
    model_info = (
        "Please select a model from the options below:\n"
        "1. Gemini 2.5 Pro\n"
        "2. Gemini 2.5 Flash\n"
        "3. Gemini 2.5 Flash-Lite\n"
        "4. Gemini 2.5 Flash Preview\n\n"
        "Please choose a model by clicking one of the buttons below."
    )
    
    model_options = {"🚀 Gemini 2.5 Pro" : "model_gemini-2.5-pro|🚀 Gemini 2.5 Pro", "⚡ Gemini 2.5 Flash": "model_gemini-2.5-flash|⚡ Gemini 2.5 Flash", "🌟 Gemini 2.5 Flash-Lite" : "model_gemini-2.5-flash-lite|🌟 Gemini 2.5 Flash-Lite", "🔍 Gemini 2.5 Flash Preview" : "model_gemini-2.5-flash-preview|🔍 Gemini 2.5 Flash Preview"}
    
    buttons = [
        types.InlineKeyboardButton(
            text=display_name,
            callback_data=f"{model_name}"
        ) for display_name, model_name in model_options.items()
    ]
    
    # kb = [[types.InlineKeyboardButton(text="Model: Gemini 2.5 Pro" , callback_data="model_gemini_2.5_pro") , types.InlineKeyboardButton(text="Model: Gemini 2.5 Flash" , callback_data="model_gemini_2.5_flash")],
    #       [types.InlineKeyboardButton(text="Model: Gemini 2.5 Flash-Lite" , callback_data="model_gemini_2.5_flash-lite"), types.InlineKeyboardButton(text="Model: Gemini 2.5 Flash Preview" , callback_data="model_gemini_2.5_flash_preview")],
    #       ]
    kb = [[button] for button in buttons]
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)

    await message.answer(model_info,
                         reply_markup=keyboard)
    
    logger.info(f"User {message.from_user.id} requested model selection info.")

@router.callback_query(F.data.startswith("model_"))
async def model_selection_callback(callback_query: types.CallbackQuery, state: FSMContext, mdel: str = "gemini-2.5-pro"):
    """
    Handles callback query for model selection.

    Args:
        callback_query (types.CallbackQuery): Contains information about the callback query.
        state (FSMContext): Contains information about the current state of the user.

    Returns:
        None
    """
    await callback_query.answer()
    selected_model = callback_query.data.split("|")[0].split("_")[1]
    for_user = callback_query.data.split("|")[1]
    await state.update_data(model=selected_model)
    await state.set_state(UserSettings.model)
    
    # await callback_query.answer(callback_query.id, text=f"Selected model: {selected_model}")
    await callback_query.message.edit_text(f"✅ Model set to: {for_user}")
    
    await callback_query.answer()
    
    logger.info(f"User {callback_query.from_user.id} selected model: {selected_model}")
    
    return selected_model


@router.message(Command("help"))
async def help_command(message: types.Message):
    """
    Responds to the "/help" command with a help message.
    
    The help message includes information about the bot's capabilities and available commands.
    """
    
    help_text = (
        "I can assist you with various tasks using AI. "
        "Just send me a message with your request, and I'll do my best to help!\n\n"
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/song <name of the song> - Search YouTube and send back audio.(e.g. /song Name of song)\n"
        "/tasks - Manage your personal to-do list\n"
        "/select_model - Select AI model\n"
        "/weather <city> - Get the current weather for any city (e.g. /weather Dushanbe)\n"
    )

    logger.info(f"User {message.from_user.id} requested help.")
    await message.answer(help_text)

async def set_default_commands(bot: Bot):
    commands = [
        types.BotCommand(command="/start", description="Start the bot"),
        types.BotCommand(command="/help", description="Show help message"),
        types.BotCommand(command="/tasks", description="Manage your to-do list"),
        types.BotCommand(command="/song", description="Download a song from YouTube"),
        types.BotCommand(command="/clear", description="Clear conversation history"),
        types.BotCommand(command="/select_model", description="Select AI model"),
        types.BotCommand(command="/weather", description="Weather for city you ask")
    ]
    await bot.set_my_commands(commands)
    logger.info("Default commands set.")


