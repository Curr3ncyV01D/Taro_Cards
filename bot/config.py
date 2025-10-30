import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class BotConfig:
    """
    Конфигурация бота.
    Загружает токен из переменных окружения.
    """
    token_bot: str = os.getenv("BOT_TOKEN", "")
    token_api: str = os.getenv('API_TOKEN', '')

# Создаем экземпляр конфигурации
config = BotConfig()