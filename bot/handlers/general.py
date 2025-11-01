from asyncio import sleep

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, \
    KeyboardButton

# noinspection PyUnresolvedReferences
from config import config
# noinspection PyUnresolvedReferences
from generator import create_response, create_spread, card_to_sticker
# noinspection PyUnresolvedReferences
from database.requests import set_user, get_count_requests_user, set_count_requests_user, get_count_referral_user, \
    get_referral_code_user, get_referral_id_user
# noinspection PyUnresolvedReferences
from handlers.utils import universal_close_message_kb, process_referrer, get_referral_link_user, delete_messages_up_to

router = Router()


class FsmReading(StatesGroup):
    get_context = State()


@router.message(Command('start'))
async def start(message: Message, state: FSMContext):
    referrer_id = None
    # Извлекаем код из команды, если таковой есть
    if len(message.text.split()) > 1:
        referrer_code = message.text.split()[1]  # код после /start
        referrer_id = await process_referrer(referrer_code)

    await set_user(user_data=message.from_user, referrer_id=referrer_id)  # Добавление пользователя в БД

    await message.answer('Здравствуйте, тут можно получить расклад таро бесплатно.\n'
                         '\n'
                         'Чтобы сделать расклад опиши свою ситуацию и я обращусь к высшим силам за помощью тебе!',
                         reply_markup=start_reply_kb())

    await state.update_data(message_id=message.message_id)
    await state.set_state(FsmReading.get_context)


def start_reply_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text='👤 Личный кабинет')]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)


@router.message(F.text == '👤 Личный кабинет')
async def private_account(message: Message):
    await message.delete()
    user_id = message.from_user.id

    count_requests = await get_count_requests_user(user_id)
    count_referral = await get_count_referral_user(user_id)
    referral_link = await get_referral_link_user(user_id)

    await message.answer('✨ <b><i>Ваш личный кабинет</i></b> ✨\n'
                         '\n'
                         'Здесь вы можете отслеживать свою активность и приглашать друзей.\n'
                         '\n'
                         f'🔮 <b>Доступные запросы:</b> {count_requests}\n'
                         f'👥 <b>Приглашено друзей:</b> {count_referral}\n'
                         '\n'
                         '<b>----------</b>\n'
                         '🕊️ Распространите мудрость Карт 🕊️\n'
                         '\n'
                         'Подарите друзьям ключ к тайнам. Ваша личная вибрационная ссылка:\n'
                         '\n'
                         f'<i><code>{referral_link}</code></i>\n'
                         '\n'
                         'За каждую приведенную душу, Вселенная наделит вас <b>дополнительной энергией</b> для 5 новых раскладов.',
                         reply_markup=universal_close_message_kb('Скрыть личный кабинет 👁'),
                         parse_mode='HTML')


@router.message(FsmReading.get_context)
async def send_reading(message: Message, state: FSMContext):
    user_tg_id = message.from_user.id
    data = await state.get_data()
    await state.clear()

    user_count_requests = await get_count_requests_user(user_tg_id)
    if user_count_requests <= 0:  # Если нет доступных запросов
        await message.answer('❌ У вас нет доступных запросов! ❌\n\n'
                             'Чтобы получить дополнительные запросы приведите друзей к нам!\n',
                             reply_markup=not_enough_requests_kb(data['message_id']))
        return None

    await message.answer('Отлично, я получила твою ситуацию, уже связываюсь с высшими силами, чтобы помочь тебе!')

    spread = await create_spread()
    gifs = []  # Список для хранения GIF-анимаций карт
    for i in range(0, 3):  # Для каждой карты в раскладе получаем соответствующую GIF-анимацию
        gif = await card_to_sticker(spread[i])
        gifs.append(gif)

    try:  # Получаем текстовую интерпретацию расклада от ИИ или сообщение об ошибке
        response_ai = await create_response(text=message.text, spread=spread)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    # Разделяем ответ ИИ на части по разделителю '~!'
    response_ai = response_ai.split('~!')  # Ожидается, что будет 4 части: по одной на каждую карту + итог

    if len(response_ai) < 4:  # Если частей ответа меньше, чем ожидается, отправляем сообщение об ошибке
        await message.answer(response_ai[0], reply_markup=restart_reading_kb(data['message_id']))
        return None

    user_count_requests -= 1
    await set_count_requests_user(user_tg_id, user_count_requests)  # Запись в бд, использования одного запроса

    for i in range(0, 3):
        await message.answer_sticker(sticker=f'{gifs[i]}')
        await message.answer(response_ai[i])
        await sleep(2)
    await message.answer(f'{response_ai[3]}')

    await message.answer('Это всё, что мне сказали карты.\n'
                         'Если хочешь ещё один расклад, закрой этот и начни новый расклад!',
                         # Добавляем кнопку для удаления сообщений расклада
                         reply_markup=restart_reading_kb(data['message_id']))


def not_enough_requests_kb(message_id) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text='Получить реферальную ссылку 💌', callback_data=f'user_referral_link_{message_id}')]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def restart_reading_kb(message_id) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text='Скрыть этот расклад 👁', callback_data=f'restart_reading_{message_id}')]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith('user_referral_link_'))
async def user_referral_link(callback: CallbackQuery):
    # Извлекаем айди сообщения из калбэка для закрытия всего диалога
    message_id = callback.data.split('_')[-1]
    # Получаем из БД реф код и создаем на его основе реф ссылку
    referral_link = await get_referral_link_user(callback.from_user.id)

    await callback.answer()
    await callback.message.edit_text('🔮 Вот ваша реферальная ссылка!\n'
                                     f'💌   <i><code>{referral_link}</code></i>   💌\n'
                                     'Скорее поделитесь ею с <b>друзьями</b>, чтобы получить <b>бонусные запросы</b> к нашим магам!',
                                     reply_markup=user_referral_link_kb(message_id),
                                     parse_mode='HTML')


@router.callback_query(F.data.startswith('restart_reading_'))
async def restart_reading(callback: CallbackQuery, state: FSMContext):
    # Удаляем прошлый расклад
    target_message_id = int(callback.data.split('_')[-1])
    current_message_id = callback.message.message_id
    await delete_messages_up_to(target_message_id, current_message_id, callback.bot, callback.message.chat.id)

    await callback.answer()
    await callback.message.answer('Здравствуйте, тут можно получить расклад таро бесплатно.\n'
                                  '\n'
                                  'Чтобы сделать расклад опиши свою ситуацию и я обращусь к высшим силам за помощью тебе!',
                                  reply_markup=start_reply_kb())

    await state.update_data(message_id=callback.message.message_id + 1)
    await state.set_state(FsmReading.get_context)


def user_referral_link_kb(message_id) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text='Назад ⬅', callback_data=f'restart_reading_{message_id}')]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
