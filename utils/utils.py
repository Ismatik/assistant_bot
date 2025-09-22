from aiogram.fsm.state import State, StatesGroup


class AIConversation(StatesGroup):
    chatting = State()
    
class UserSettings(StatesGroup):
    model = State()