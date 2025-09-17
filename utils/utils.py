from aiogram.fsm.state import State, StatesGroup


class ChatHistory(StatesGroup):
    history = State()