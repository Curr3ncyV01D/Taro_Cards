import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class BotConfig:
    """
    Конфигурация бота.
    Загружает данные из переменных окружения.
    """
    name_bot: str = os.getenv('BOT_NAME', '')
    token_bot: str = os.getenv("BOT_TOKEN", "")
    token_api: str = os.getenv('API_TOKEN', '')

# Создаем экземпляр конфигурации
config = BotConfig()