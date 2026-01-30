from sqlalchemy import BigInteger, String, Integer, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from bot.config import config

engine = create_async_engine(url=config.DB_URL)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(32), nullable=True)
    first_name: Mapped[str] = mapped_column(String(64))
    requests: Mapped[int] = mapped_column(BigInteger, default=10)
    is_admin: Mapped[bool] = mapped_column(default=False)
    referral_code: Mapped[str] = mapped_column(String)
    referral_count: Mapped[int] = mapped_column(Integer, default=0)
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.tg_id'), nullable=True)

    referrals: Mapped[list['User']] = relationship('User', backref='referrer', remote_side=[tg_id])


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
