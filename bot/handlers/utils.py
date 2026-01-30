from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.database.requests import (get_referral_id_user, get_count_referral_user, set_count_referral_user,
                               get_count_requests_user, set_count_requests_user)

from bot.config import config

from bot.database.requests import get_referral_code_user

router = Router()


@router.callback_query(F.data.startswith('delete_up_to_'))
async def callback_delete_messages_up_to(callback: CallbackQuery, bot: Bot):
    """Удаляет все сообщения в диапазоне от айди в калбэк дате до айди из калбэк айди"""
    # Извлекаем target_message_id из callback данных
    try:
        target_message_id = int(callback.data.split('_')[-1])
    except (IndexError, ValueError):
        await callback.answer("Ошибка в формате данных")
        return

    chat_id = callback.message.chat.id
    current_message_id = callback.message.message_id

    if target_message_id > current_message_id:
        await callback.answer("Некорректный диапазон удаления")
        return

    # Генерируем список всех message_id от target_message_id до current_message_id включительно
    all_message_ids = list(range(target_message_id, current_message_id + 1))
    for message_id in all_message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение: {message_id}: {e}")

    await callback.answer("Сообщения удалены")


async def delete_messages_up_to(target_message_id: int, current_message_id: int, bot: Bot, chat_id: int):
    """Удаляет все сообщения и переданного диапазона"""
    if target_message_id > current_message_id:
        print("Некорректный диапазон удаления")
        return

    # Генерируем список всех message_id от target_message_id до current_message_id включительно
    all_message_ids = list(range(target_message_id, current_message_id + 1))
    for message_id in all_message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение: {message_id}: {e}")


@router.callback_query(F.data == 'close_message')
async def close_message(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.delete()


def universal_close_message_kb(text) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=f'{text}', callback_data=f'close_message')]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def process_referrer(referrer_code):
    referrer_id = await get_referral_id_user(referrer_code)  # айди владельца реферального кода
    # Засчитываем нового реферала
    referral_count = await get_count_referral_user(referrer_id)
    await set_count_referral_user(referrer_id, referral_count + 1)
    # Добавляем бонус(5 новых запросов) реферу за нового реферала
    user_count_requests = await get_count_requests_user(referrer_id)
    await set_count_requests_user(referrer_id, user_count_requests + 5)
    return referrer_id


async def get_referral_link_user(tg_id: int) -> str:
    referral_code = await get_referral_code_user(tg_id)
    referral_link = f'https://t.me/{config.name_bot}?start={referral_code}'
    return referral_link
