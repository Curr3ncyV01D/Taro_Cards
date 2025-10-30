from asyncio import sleep

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from generator import create_response, create_spread, card_to_sticker

router = Router()


class FsmReading(StatesGroup):
    get_context = State()


@router.callback_query(F.data.startswith('delete_up_to_'))
async def delete_messages_up_to(callback: CallbackQuery, bot: Bot):
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


@router.message(Command('start'))
async def start(message: Message, state: FSMContext):
    await message.answer('Здравствуйте, тут можно получить расклад таро бесплатно.\n'
                         '\n'
                         'Чтобы сделать расклад опиши свою ситуацию и я обращусь к высшим силам за помощью тебе!')
    await state.update_data(message_id=message.message_id)
    await state.set_state(FsmReading.get_context)


@router.message(FsmReading.get_context)
async def send_reading(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    await message.answer('Отлично, я получила твою ситуацию, уже связываюсь с высшими силами, чтобы помочь тебе!')

    spread = await create_spread()
    gifs = []  # Список для хранения GIF-анимаций карт
    for i in range(0, 3):  # Для каждой карты в раскладе получаем соответствующую GIF-анимацию
        gif = await card_to_sticker(spread[i])
        gifs.append(gif)

    try:  # Получаем текстовую интерпретацию расклада от ИИ
        response_ai = await create_response(text=message.text, spread=spread)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    # Разделяем ответ ИИ на части по разделителю '~!'
    response_ai = response_ai.split('~!')  # Ожидается, что будет 4 части: по одной на каждую карту + итог

    if len(response_ai) < 4:
        await message.answer(response_ai[0], reply_markup=send_reading_kb(data['message_id']))
        return None

    for i in range(0, 3):
        await message.answer_sticker(sticker=f'{gifs[i]}')
        await message.answer(response_ai[i])
        await sleep(2)
    await message.answer(f'{response_ai[3]}')

    await message.answer('Это всё, что мне сказали карты.\n'
                         'Если хочешь ещё один расклад, закрой этот и начни новый расклад!',
                         # Добавляем кнопку для удаления сообщений расклада
                         reply_markup=send_reading_kb(data['message_id']))


def send_reading_kb(message_id) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text='Скрыть этот расклад 👁', callback_data=f'delete_up_to_{message_id}')]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
