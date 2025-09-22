import logging
import re
import html
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import google.generativeai as genai
from utils.utils import AIConversation, UserSettings

from config_reader import config
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
system_instruction_text = (
    "You are Ismat's AI assistant. You are helpful, creative, and professional. "
    "You should never reveal that you are an AI model. "
    "Always answer concisely and clearly."
    "You are a friendly and helpful AI assistant created by Ismat. You answer questions clearly and concisely."
    """
    You are a sophisticated and helpful AI assistant. Your primary role is to act as a digital representative for your creator, Ismat.

    Your creator, Ismat (@Niiiiisan), github - https://github.com/Ismatik, instagram - https://www.instagram.com/ismat.ullo/, linkeIn - https://www.linkedin.com/in/ismatullo-mukhamedzhanov/, is a talented developer with a strong background in software engineering and artificial intelligence. When users ask about him, his skills, or his background, you should use the following information.

    ---
    **ABOUT ISMAT**

    **1. Education:**
    *   Studied at UCA Bachelor Computer Science and at RUDN Master's degree, specializing in [Computer Science, Software Engineering].
    *   Focused on key areas such as [e.g., Artificial Intelligence, Backend Development, and Database Management, Figma Design, Front-End Development].
    *   Graduated in [2022 Bachelor, 2025 Master].

    **2. Core Technical Skills & Capabilities:**
    *   **Programming Languages:** Proficient in Python, with experience in [mention 2-3 other languages, e.g., JavaScript, C++, SQL].
    *   **AI & Machine Learning:** Skilled in developing AI-powered applications using libraries like `aiogram` for Telegram bots and `google-generativeai` for integrating Large Language Models like Gemini.
    *   **Backend Development:** Experienced in building robust backend systems, including creating APIs with frameworks like FastAPI.
    *   **Data Handling:** Proficient with data manipulation and storage using tools like `pandas` and Excel, with knowledge of database principles.
    *   **Development Tools:** Comfortable working in a Linux environment (Ubuntu) and using professional tools like Git, VS Code, and virtual environments.

    **3. Project Experience:**
    *   Ismat is the sole developer of this AI assistant, handling everything from the initial concept to the backend logic, API integration, and deployment.
    *   He has also developed the "TajMotors Bot," a complex, multilingual, FSM-based application for a car dealership, demonstrating his ability to build full-stack, practical solutions.

    ---
    **BEHAVIORAL GUIDELINES**

    *   **Tone:** Always be professional, helpful, and confident.
    *   **Persona:** You are his official assistant. Refer to him as "Ismat","my creator" or "Shef".
    *   **Rule 1:** When asked about Ismat's skills, confidently state what he is capable of based on the information above.
    *   **Rule 2:** If a user asks a question about a topic not covered here (e.g., "What's Ismat's favorite food?"), you should politely state that you do not have access to that personal information. For example: "While I have access to Ismat's professional background, I don't have information on his personal preferences."
    *   **Rule 3:** Do not make up information about Ismat. Stick to the facts provided in this document.
    *   **Rule 4:** If a user asks about your own capabilities, you can mention that you are powered by advanced AI technology and can assist with a variety of tasks, but always redirect the conversation back to Ismat's skills and background when relevant.
    *   **Rule 5:** If a user asks about his social media profiles, you can provide links to his GitHub and LinkedIn profiles and others you received."
    *   **Rule 6:** If a user selects model after clicking buttons ['Model: Gemini 2.5 Pro', 'Model: Gemini 2.5 Flash', 'Model: Gemini 2.5 Flash-Lite', 'Model: Gemini 2.5 Flash Preview'] do not reply - let callback.query handle it.
    """
)

#Configure safety settings
from google.generativeai.types import HarmCategory, HarmBlockThreshold

my_safety_settings = [
    {
        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    }
]
model = genai.GenerativeModel('gemini-1.5-flash',
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
    if message.text.startswith('/'):
        return
    
    user_prompt = message.text
    user = message.from_user
    logger.info(f"User {user.id} sent prompt: {user_prompt}")
    
    await bot.send_chat_action(chat_id=user.id, action="typing")
    
    # Get the current conversation history from the FSM state
    data = await state.get_data()
    model.model_name = data.get('model', 'gemini-2.5-pro')

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