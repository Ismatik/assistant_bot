import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from google import genai
from ismat_assistant_bot import bot

# client = genai.Client(api_key="AIzaSyAzVi8VhQRsmw3Cixl7TW18IBjKOHToGhs")
# response = client.models.generate_content(
#     model="gemini-2.5-pro",
#     contents="Write a short poem about the sea in English",
#     config={
#         "temperature": 0.3,
#         "max_output_tokens": 256
#     }
# )

# print(response.text)


genai.configure(api_key="AIzaSyAzVi8VhQRsmw3Cixl7TW18IBjKOHToGhs")

model = genai.GenerativeModel('gemini-2.5-pro')

logger = logging.getLogger(__name__)
router = Router()

class AIConversation(StatesGroup):
    waiting_for_prompt = State()
    
async def ai_handles(prompt:str, history: list = None):
    try:
        #Start a chat with provided history
        chat = model.start_chat(
            history=history or []
        )
        #Send user's prompt to the model and get response
        response = await chat.send_message_async(prompt)
        
        return response.text
    
    except Exception as e:
        logger.error(f"Error in ai_handles: {e}")
        return "Sorry, I couldn't process your request at the moment."

@router.message(F.text)
async def ai_handler_message(message: types.Message, state: FSMContext):
    await state.set_state(AIConversation.waiting_for_prompt)
    user_prompt = message.text
    logger.info(f"User prompt: {user_prompt}")
    
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    