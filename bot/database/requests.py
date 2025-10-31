from sqlalchemy import select, update

# noinspection PyUnresolvedReferences
from database.db_function import generate_unique_referral_code
# noinspection PyUnresolvedReferences
from database.models import async_session, User
from sqlalchemy.util import await_only


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


async def get_count_requests_user(tg_id):
    """Возвращает количество доступных запросов по айди пользователя"""
    async with async_session() as session:
        return await session.scalar(select(User.requests).where(User.tg_id == tg_id))


async def set_count_requests_user(tg_id, requests_count):
    """Изменяет количество доступных запросов по айди пользователя"""
    async with async_session() as session:
        await session.execute(update(User).where(User.tg_id == tg_id).values(requests=requests_count))


async def get_referral_code_user(tg_id):
    async with async_session() as session:
        return await session.scalar(select(User.referral_code).where(User.tg_id == tg_id))