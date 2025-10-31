import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from database.models import User


async def generate_unique_referral_code(session: AsyncSession, length=8, max_attempts=10):
    """Генерации уникального реферального кода"""
    for _ in range(max_attempts):
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                       for _ in range(length))
        # Проверка уникальности
        existing_user = await session.scalar(
            select(User).where(User.referral_code == code)
        )
        if not existing_user:
            return code

    raise Exception("Не удалось сгенерировать уникальный реферальный код")