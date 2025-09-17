# import logging
# from aiogram import Router, F, types, Bot
# from aiogram.filters import Command 
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup
# from google import genai
# from config_reader import config 
# from utils.utils import ChatHistory

# import re
# import html

# client = genai.Client(api_key=config.gemini_api_key.get_secret_value())
# model = 'gemini-2.5-pro'

# logger = logging.getLogger(__name__)
# router = Router()

# @router.message(Command("start"))
# async def start_command(message: types.Message):
#     """_summary_

#     Args:
#         message (types.Message): _Start command implementation_
#     """
#     logger.info(f"User {message.from_user.id} started the bot.")
#     await message.answer("Hello! I'm Ismat's AI assistant. How can I help you today?")
    
    
# @router.message(Command("help"))
# async def help_command(message: types.Message):
#     help_text = (
#         "I can assist you with various tasks using AI. "
#         "Just send me a message with your request, and I'll do my best to help!\n\n"
#         "Available commands:\n"
#         "/start - Start the bot\n"
#         "/help - Show this help message"
#     )

#     logger.info(f"User {message.from_user.id} requested help.")
#     await message.answer(help_text)

# async def set_default_commands(bot: Bot):
#     commands = [
#         types.BotCommand(command="/start", description="Start the bot"),
#         types.BotCommand(command="/help", description="Show help message"),
#     ]
#     await bot.set_my_commands(commands)
#     logger.info("Default commands set.")


# async def ai_handles(prompt:str, history: list = None) -> str:
#     """_summary_

#     Args:
#         prompt (str): _description_
#         history (list, optional): _description_. Defaults to None.

#     Returns:
#         _type_: _description_
#     """
#     try:
#         #Start a chat with provided history
#         response = client.models.generate_content(
#             model=model,
#             contents=prompt,
#             )
        
#         return response.text
    
#     except Exception as e:
#         logger.error(f"Error in ai_handles: {e}")
#         return "Sorry, I couldn't process your request at the moment."

# def format_ai_response(text: str) -> str:
#     """
#     Converts a wide range of Markdown from an AI response into Telegram-safe HTML.
#     This function handles bold, italic, strikethrough, underline, code blocks,
#     and bullet points, while ensuring the text is safe for HTML parsing.

#     Args:
#         text (str): The raw text from the AI model.

#     Returns:
#         str: A Telegram-safe HTML formatted string.
#     """
#     # --- Basic Text Formatting ---
#     # **bold** -> <b>bold</b>
#     text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
#     # *italic* -> <i>italic</i> (be careful not to match **)
#     text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
#     # __underline__ -> <u>underline</u>
#     text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)
#     # ~strikethrough~ -> <s>strikethrough</s>
#     text = re.sub(r'~(.*?)~', r'<s>\1</s>', text)

#     # --- Code Blocks ---
#     # ```language\ncode\n``` -> <pre><code class="language-...">code</code></pre>
#     # This regex handles multi-line code blocks with optional language hints.
#     text = re.sub(
#         r'```(\w*)\n(.*?)```', 
#         lambda m: f'<pre><code class="language-{m.group(1)}">{html.escape(m.group(2))}</code></pre>',
#         text, 
#         flags=re.DOTALL
#     )
#     # `inline code` -> <code>inline code</code>
#     text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)

#     # --- Lists (Bullet Points) ---
#     # This is a bit more complex. We need to wrap the whole list in <ul> and each item in <li>.
#     # We find all list blocks and process them.
#     def replace_list(match):
#         items = match.group(0).strip().split('\n')
#         li_items = [f'<li>{item.strip()[2:]}</li>' for item in items]
#         return f"<ul>\n{''.join(li_items)}\n</ul>"

#     # This regex finds consecutive lines starting with * or - (common for lists)
#     text = re.sub(r'(?:^\s*[-*]\s+.*\n?)+', replace_list, text, flags=re.MULTILINE)

#     # --- Links ---
#     # [text](url) -> <a href="url">text</a>
#     text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
#     print(text)
#     return text

# @router.message(F.text)
# async def ai_handler_message(message: types.Message, bot:Bot):
#     if message.text.startswith('/'):
#         return
    
#     user_prompt = message.text
#     logger.info(f"User {message.from_user.id} sent prompt: {user_prompt}")
    
#     # Now you can use the 'bot' object that was passed in.
#     await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
#     # Get the AI response
#     ai_response = await ai_handles(user_prompt)
    
#     # Send the response
#     # await message.answer(
#     #     text=ai_response
#     #     )
    
#     formatted_response = format_ai_response(ai_response)
#     raw_ai_response = ai_response  # Keep the raw response as a fallback
#     try:
#         await message.answer(
#             formatted_response,
#             parse_mode="HTML"
#         )
#     except Exception as e:
#         # If formatting fails for some reason, send the raw text as a fallback
#         logger.error(f"Failed to send formatted message, sending raw. Error: {e}")
#         await message.answer(raw_ai_response)




# File: handlers/messages_ai_handler.py

import logging
import re
import html
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import google.generativeai as genai

from config_reader import config
import requests


# --- 1. Use the modern, async-friendly setup ---
genai.configure(api_key=config.gemini_api_key.get_secret_value())
model = genai.GenerativeModel('gemini-1.5-flash') # Use a modern, available model

logger = logging.getLogger(__name__)
router = Router()

# --- 2. Define an FSM State to manage the conversation ---
class AIConversation(StatesGroup):
    chatting = State()

# --- 3. Refactor the AI handler to use the chat model ---
async def ai_handles_chat(prompt: str, history: list = None):
    """
    Manages a multi-turn conversation with Gemini.
    """
    try:
        # Start a chat session with the provided history
        chat = model.start_chat(history=history or [])
        
        # Send the user's message and get the response
        response = await chat.send_message_async(prompt)
        
        # Return the response text AND the updated history
        return response.text, chat.history
    
    except Exception as e:
        logger.error(f"Error in ai_handles_chat: {e}", exc_info=True)
        return "Sorry, I couldn't process your request at the moment.", history

# --- 4. Modify the main handler to use FSM ---
@router.message(F.text)
async def ai_handler_message(message: types.Message, state: FSMContext, bot: Bot):
    # Ignore commands
    if message.text.startswith('/'):
        return
    
    user_prompt = message.text
    user = message.from_user
    logger.info(f"User {user.id} sent prompt: {user_prompt}")
    
    await bot.send_chat_action(chat_id=user.id, action="typing")
    
    # Get the current conversation history from the FSM state
    data = await state.get_data()
    history = data.get('history', [])
    
    # Get the AI's response AND the new, updated history
    ai_response_text, new_history = await ai_handles_chat(user_prompt, history)
    
    # Save the updated history back to the FSM state for the next message
    await state.update_data(history=new_history)
    
    # Set the state to indicate an ongoing conversation
    await state.set_state(AIConversation.chatting)
    
    # Format and send the response
    formatted_response = format_ai_response(ai_response_text)
    try:
        await message.answer(formatted_response, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send formatted message, sending raw. Error: {e}")
        await message.answer(ai_response_text)

# --- 5. Add a /clear command to reset the history ---
@router.message(Command("clear"))
async def clear_history(message: types.Message, state: FSMContext):
    """Clears the conversation history for the user."""
    await state.clear()
    await message.answer("My memory of our conversation has been cleared. Let's start fresh!")
    logger.info(f"User {message.from_user.id} cleared their conversation history.")



def format_ai_response(text: str) -> str:
    """
    Converts a wide range of Markdown from an AI response into Telegram-safe HTML.
    This function handles bold, italic, strikethrough, underline, code blocks,
    and bullet points, while ensuring the text is safe for HTML parsing.

    Args:
        text (str): The raw text from the AI model.

    Returns:
        str: A Telegram-safe HTML formatted string.
    """
    # --- Code Blocks ---
    text = re.sub(r'```(\w*)\n(.*?)```', lambda m: f'<pre><code class="language-{m.group(1)}">{html.escape(m.group(2))}</code></pre>', text, flags=re.DOTALL)

    # --- Inline Code ---
    text = re.sub(r'`(.*?)`', lambda m: f'<code>{html.escape(m.group(1))}</code>', text)

    # --- Lists ---
    text = re.sub(r'(?:^\s*[-*]\s+.*\n?)+', lambda m: "<ul>" + "".join([f"<li>{html.escape(item.strip())}</li>" for item in m.group(0).strip().splitlines() if item.strip()]) + "</ul>", text, flags=re.MULTILINE)


    # --- Links ---
    text = re.sub(r'\[(.*?)\]\((.*?)\)', lambda m: f'<a href="{html.escape(m.group(2))}">{html.escape(m.group(1))}</a>', text, flags=re.DOTALL)
    