import asyncio
import logging
from aiogram import Bot, Dispatcher

from database.models import async_main, engine
from config import config
from handlers import routers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция инициализации и запуска бота."""
    if not config.token_bot:
        logger.error("Не найден BOT_TOKEN в переменных окружения")
        return

    await async_main()

    bot = Bot(token=config.token_bot)
    dp = Dispatcher()

    for router in routers:
        dp.include_router(router)

    try:
        logger.info("Starting bot")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('[LOG] БОТ ОТКЛЮЧЕН')