import asyncio
import sys
import types as pytypes
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.append(str(Path(__file__).resolve().parents[2]))

if "google" not in sys.modules:
    google_module = pytypes.ModuleType("google")
    generativeai_module = pytypes.ModuleType("google.generativeai")
    generativeai_types_module = pytypes.ModuleType("google.generativeai.types")

    class DummyGenerationConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyHarmCategory:
        HARM_CATEGORY_HARASSMENT = "harassment"

    class DummyHarmBlockThreshold:
        BLOCK_NONE = "none"

    class DummyChat:
        def __init__(self, history=None):
            self.history = history or []

        async def send_message_async(self, prompt: str):
            response_text = "stub-response"
            self.history = [
                *self.history,
                {"role": "user", "parts": [prompt]},
                {"role": "model", "parts": [response_text]},
            ]
            return SimpleNamespace(text=response_text)

    class DummyGenerativeModel:
        def __init__(self, **kwargs):  # noqa: D401
            self.kwargs = kwargs

        def start_chat(self, history=None):
            return DummyChat(history)

    generativeai_module.configure = lambda **kwargs: None
    generativeai_module.types = SimpleNamespace(GenerationConfig=DummyGenerationConfig)
    generativeai_module.GenerativeModel = DummyGenerativeModel

    generativeai_types_module.HarmCategory = DummyHarmCategory
    generativeai_types_module.HarmBlockThreshold = DummyHarmBlockThreshold

    sys.modules["google"] = google_module
    sys.modules["google.generativeai"] = generativeai_module
    sys.modules["google.generativeai.types"] = generativeai_types_module

if "utils" not in sys.modules:
    utils_module = pytypes.ModuleType("utils")
    utils_module.__path__ = []  # Mark as namespace package
    utils_utils_module = pytypes.ModuleType("utils.utils")

    class DummyAIConversation:  # noqa: D401 - placeholder FSM state
        chatting = "chatting"

    class DummyUserSettings:
        pass

    utils_utils_module.AIConversation = DummyAIConversation
    utils_utils_module.UserSettings = DummyUserSettings

    sys.modules["utils"] = utils_module
    sys.modules["utils.utils"] = utils_utils_module

if "config_reader" not in sys.modules:
    config_reader_module = pytypes.ModuleType("config_reader")

    class _Secret:
        def __init__(self, value: str):
            self._value = value

        def get_secret_value(self) -> str:
            return self._value

    config_reader_module.config = SimpleNamespace(
        gemini_api_key=_Secret("dummy-key"),
        bot_token=_Secret("dummy-token"),
    )
    config_reader_module.CONFIG_SYSTEM_INSTRUCTION_TEXT = ""

    sys.modules["config_reader"] = config_reader_module

if "requests" not in sys.modules:
    requests_module = SimpleNamespace()

    class _RequestException(Exception):
        pass

    requests_module.RequestException = _RequestException
    requests_module.exceptions = SimpleNamespace(RequestException=_RequestException)

    sys.modules["requests"] = requests_module

from assistant_bot.handlers.messages_ai_handler import ai_handler_message


class DummyState:
    def __init__(self, data: dict | None = None):
        self._data = data or {}

    async def get_data(self) -> dict:
        return self._data

    async def update_data(self, **kwargs):
        self._data.update(kwargs)

    async def set_state(self, state):  # noqa: ARG002 - part of FSMContext API
        self._state = state

    async def clear(self):
        self._data.clear()


def test_ai_handler_ignores_commands():
    message = SimpleNamespace(
        text="/song never gonna give you up",
        from_user=SimpleNamespace(id=42),
        answer=AsyncMock(),
    )

    bot = AsyncMock()
    state = DummyState({"history": [], "model": "gemini-2.5-pro"})

    asyncio.run(ai_handler_message(message, state, bot))

    bot.send_chat_action.assert_not_awaited()
    message.answer.assert_not_awaited()
