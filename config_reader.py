from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

# Paths to files
USER_ACTIVITY_LOG_FILE = "/home/ikki/Desktop/Practice/Assistant_bot/assistant_bot/files/user_activity.log"


class Settings(BaseSettings):
    
    bot_token: SecretStr
    gemini_api_key: SecretStr
    model_config = SettingsConfigDict(env_file = ".env", env_file_encoding = "utf-8")
    
config = Settings()