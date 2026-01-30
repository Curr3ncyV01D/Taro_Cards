from sqlalchemy import select, update


from bot.database.db_function import generate_unique_referral_code

from bot.database.models import async_session, User


async def set_user(user_data, referrer_id) -> None:
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
                    referral_code=referral_code,
                    referrer_id=referrer_id
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
        await session.commit()


async def get_count_referral_user(tg_id):
    """Возвращает количество рефералов пользователя по айди пользователя"""
    async with async_session() as session:
        return await session.scalar(select(User.referral_count).where(User.tg_id == tg_id))


async def set_count_referral_user(tg_id, referral_count):
    """Изменяет количество рефералов пользователя по айди пользователя"""
    async with async_session() as session:
        await session.execute(update(User).where(User.tg_id == tg_id).values(referral_count=referral_count))
        await session.commit()


async def get_referral_code_user(tg_id):
    """Возвращает реферальный код для ссылки по айди пользователя"""
    async with async_session() as session:
        return await session.scalar(select(User.referral_code).where(User.tg_id == tg_id))


async def get_referral_id_user(referral_code):
    """Возвращает айди владельца реферального кода по реферальному коду"""
    async with async_session() as session:
        return await session.scalar(select(User.tg_id).where(User.referral_code == referral_code))
