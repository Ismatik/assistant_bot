import logging
import re
import html
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import google.generativeai as genai
from utils.utils import AIConversation, UserSettings

from buttons.buttons import select_model_command
from config_reader import config, CONFIG_SYSTEM_INSTRUCTION_TEXT
import requests


# --- 1. Use the modern, async-friendly setup ---
genai.configure(api_key=config.gemini_api_key.get_secret_value())

#Configure model itself and its correctness
my_configs = genai.types.GenerationConfig(
    temperature=0.3,
    max_output_tokens=1024,
    top_p=0.95,  # Nucleus filtering
    top_k=40,  # Frequency filtering
)

#Configuer instructions for the model, as its personality for the user
system_instruction_text = CONFIG_SYSTEM_INSTRUCTION_TEXT

#Configure safety settings
from google.generativeai.types import HarmCategory, HarmBlockThreshold

my_safety_settings = [
    {
        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    }
]

model_name = select_model_command()
model = genai.GenerativeModel(model_name=model_name,
                              generation_config=my_configs,
                              safety_settings=my_safety_settings,
                              system_instruction=system_instruction_text) # Use a modern, available model


logger = logging.getLogger(__name__)
router = Router()

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
    print(model)

    history = data.get('history', [])
    
    # Get the AI's response AND the new, updated history
    ai_response_text, new_history = await ai_handles_chat(user_prompt, history)
    

    await state.update_data(history=new_history)
    
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
    lists, and links, while ensuring the text is safe for HTML parsing.
    """
    # --- Structural Elements First ---

    # 1. Code Blocks (Multi-line)
    # This should run first to protect the code inside from further formatting.
    text = re.sub(
        r'```(\w*)\n(.*?)```', 
        lambda m: f'<pre><code class="language-{m.group(1)}">{html.escape(m.group(2))}</code></pre>',
        text, 
        flags=re.DOTALL
    )

    # 2. Lists (Bullet Points)
    # This finds blocks of list items and wraps them correctly.
    
    def replace_list(match):
        item_text = match.group(0).lstrip('*- ').strip()
        # Return it as a new line starting with a bullet character.
        return f"• {item_text}"
    
    text = re.sub(r'(?:^\s*[-*]\s+.*\n?)+', replace_list, text, flags=re.MULTILINE)

    # --- Inline Formatting (Applied after structural changes) ---

    # 3. Bold (**text**)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # 4. Italic (*text*)
    # The regex here is designed to not conflict with the bold markers.
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    
    # 5. Underline (__text__)
    text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)
    
    # 6. Strikethrough (~text~)
    text = re.sub(r'~(.*?)~', r'<s>\1</s>', text)

    # 7. Inline Code (`code`)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)

    # 8. Links ([text](url))
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)

    return text