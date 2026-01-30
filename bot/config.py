import os
from dotenv import load_dotenv

load_dotenv()


class BotConfig:
    """
    Конфигурация бота.
    Загружает данные из переменных окружения.
    """
    name_bot: str = os.getenv('BOT_NAME', '')
    token_bot = os.getenv('BOT_TOKEN')
    token_api: str = os.getenv('API_TOKEN', '')

    # ЛОГИКА:
    # Если мы в Докере, мы хотим сохранять базу в папку /app/data
    # Если мы запускаем локально, сохраняем просто рядом в файл db.sqlite3

    # Получаем путь из переменной окружения или берем стандартный
    DB_NAME = os.getenv('DB_NAME', 'db.sqlite3')

    # Если есть специальная папка для данных (в докере), кладем туда
    DB_FOLDER = os.getenv('DB_FOLDER', '')

    if DB_FOLDER:
        # Получится: sqlite+aiosqlite:////app/data/db.sqlite3
        DB_URL = f"sqlite+aiosqlite:///{os.path.join(DB_FOLDER, DB_NAME)}"
    else:
        # Локально: sqlite+aiosqlite:///db.sqlite3
        DB_URL = f"sqlite+aiosqlite:///{DB_NAME}"


config = BotConfig()