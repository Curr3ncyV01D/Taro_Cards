from sqlalchemy import select

from database.db_function import generate_unique_referral_code
from database.models import async_session, User


async def set_user(user_data) -> None:
    """Запись в базу данных при старте, если пользователя там нет"""
    async with async_session() as session:
        async with session.begin():  # Контекстный менеджер для транзакции
            user = await session.scalar(select(User).where(User.tg_id == user_data.id))

            if not user:
                # Генерируем реферал код ДО создания пользователя
                referral_code = await generate_unique_referral_code(session)

                new_user = User(
                    tg_id=user_data.id,
                    username=user_data.username if user_data.username else None,
                    first_name=user_data.first_name,
                    referral_code=referral_code
                )
                session.add(new_user)