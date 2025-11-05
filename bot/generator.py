import logging
import time
import random
import hashlib
import re

from openai import AsyncOpenAI, APIError, RateLimitError

from config import config

client = AsyncOpenAI(api_key=config.token_api)


class TarotAI:
    def __init__(self):
        self.cache = {}
        self.system_prompt = """
        Ты — мудрый таро-оракул. Сделай расклад на 3 Старших Аркана. 

        ВАЖНЫЕ ПРАВИЛА:
        1. Если вопрос пользователя бессмысленный, состоит из случайных символов, повторяющихся слов - вежливо откажись делать расклад
        2. Если вопрос слишком короткий или непонятный - попроси уточнить
        3. Не отвечай на оскорбительные, провокационные или личные вопросы
        4. Фокусируйся только на духовных и жизненных аспектах

        Структура для КАЖДОЙ карты: 
        🔮 Карта: [Название]
        📖 Значение: [Интерпретация].
        Обязательно ставь разделитель ~! после КАЖДОЙ карты и ПЕРЕД заголовком "Итог".

        Будь добрым, честным и вдохновляющим. Ответ до 600 символов.

        Если вопрос не подходит для таро-расклада, ответь: 
        "К сожалению, я не могу сделать расклад на этот вопрос. Пожалуйста, задайте вопрос о вашей жизненной ситуации, отношениях или духовном пути."
        """

        self.flood_patterns = [
            r'(.)\1{5,}',  # повторяющиеся символы (6+ раз)
        ]

        self.nonsense_indicators = [
            'asdfghjkl', 'фывапрол', 'qwerty', 'йцукен',
            'test', 'тест', 'проверка', 'привет', 'hello', 'hi'
        ]

        self.major_arcana = ["Шут", "Маг", "Верховная Жрица", "Императрица",
                             "Император", "Иерофант", "Влюбленные", "Колесница",
                             "Сила", "Отшельник", "Колесо Фортуны", "Справедливость",
                             "Повешенный", "Смерть", "Умеренность", "Дьявол",
                             "Башня", "Звезда", "Луна", "Солнце", "Суд", "Мир"]

        self.gifs_cards = {"Шут": 'CAACAgIAAxkBAAEPqyhpA7thdUEmcIyHf1CgRPVdAe06IwACx30AAmY2IEgbbKC7x_hshDYE',
                           "Маг": 'CAACAgIAAxkBAAEPqyppA7tmtOyfZgxvzeOp_wABWsH_NhsAAkaKAALHNSFIPPIgmX2zOps2BA',
                           "Верховная Жрица": 'CAACAgIAAxkBAAEPqyxpA7tudJbY40XTyb_HCyuwzsgWRAACEY4AAmc8GEiGnxiZKUo6-zYE',
                           "Императрица": 'CAACAgIAAxkBAAEPqy5pA7t4Q334UPB0RUXdnQABBAvT0fsAAkSDAAIKSyFI7wsy72Md1oA2BA',
                           "Император": 'CAACAgIAAxkBAAEPqzBpA7t90iOO21XUK-o-8mPB1JAX6gAC7pEAAvCMIEj1VH7xrrmgSDYE',
                           "Иерофант": 'CAACAgIAAxkBAAEPqzJpA7uMpm7Ql51ACHVcKb2oq7DqfAAC84AAAlSXIUgU-UlzrcoSHDYE',
                           "Влюбленные": 'CAACAgIAAxkBAAEPqzRpA7uUpTyk8VZkJhQiRl8q-tnFFgACnYgAAv_XIEhTjo_v23RvpTYE',
                           "Колесница": 'CAACAgIAAxkBAAEPqzZpA7uhV9qAGf-w4O_VOOWBMW44HwACJXcAAsqCIUgd6yihG_tw8DYE',
                           "Сила": 'CAACAgIAAxkBAAEPqyJpA7tQnjQ9UjwQi5d0SW_avCNSkQACl4sAArCLGUjbl_RTT0aQTjYE',
                           "Отшельник": 'CAACAgIAAxkBAAEPqzppA7uu1JUUB5sL5r1UsFgL0YrinAACLYMAAmcaIUgE9gMEBiouCTYE',
                           "Колесо Фортуны": 'CAACAgIAAxkBAAEPqzxpA7u52PONeiFJ6I2XW8v5gSp_6wACzJAAAmsmGUgLX_Wd8Dj8DTYE',
                           "Справедливость": 'CAACAgIAAxkBAAEPqz5pA7vbbQPg8sJO42iT--_tC3Sp2AACdJIAApFEIEgjLQnmzQGL4zYE',
                           "Повешенный": 'CAACAgIAAxkBAAEPq0JpA7vvQZDKORRWthkS9lXd1RVkiAACOpwAAghSIEiVnDjm84lDiTYE',
                           "Смерть": 'CAACAgIAAxkBAAEPq0BpA7vhUpAPH4KDcwpm1L8Tk8_XlAAC144AAsDGGUjJw7S63c_b7jYE',
                           "Умеренность": 'CAACAgIAAxkBAAEPqyRpA7tR5lMZ_HS7o1_RECLLwPKiIAACS4oAAoC8IEgY6oCJU3qb2zYE',
                           "Дьявол": 'CAACAgIAAxkBAAEPq0hpA7wbCaJpVg6EaYdghYL0sQJd4QACp5gAAmUTIUi1DTLeMM-jpjYE',
                           "Башня": 'CAACAgIAAxkBAAEPqyVpA7tR4pLSfyex-igf3pLU9VUzTQACiIkAAgnuIEj9Rt9GHVF1NzYE',
                           "Звезда": 'CAACAgIAAxkBAAEPq0xpA7wpoOMAAbVxxJywjF9d3lXFXsMAAqeMAAIzUSFI2PAz2KbjBEQ2BA',
                           "Луна": 'CAACAgIAAxkBAAEPq05pA7wtkiSuOilgZEgCYz7ZvKYvOwAChokAAifJIEgvFt4Xx_YKfTYE',
                           "Солнце": 'CAACAgIAAxkBAAEPqyBpA7tNUb5FYLHveg5sTVCuTWxrQAACv5AAAvntGUjwq0bNlC8iIjYE',
                           "Суд": 'CAACAgIAAxkBAAEPq1JpA7w4yBicF5jpVDnxMJVNFEDnRwAC9ZAAAhF1GEiTihrniJCA7TYE',
                           "Мир": 'CAACAgIAAxkBAAEPq1RpA7w7UXOuiRotZmxyBM1W9JKo0gACzpMAAo8jGUiZuMjLdwVd2zYE'}

    async def create_reading(self, question: str, spread) -> str:
        """Создает таро-расклад с помощью ИИ"""
        start_time = time.time()

        try:
            # Валидация вопроса
            validation_result = self._validate_question(question)
            if not validation_result["valid"]:
                return validation_result["message"]

            cleaned_question = self._clean_question(question)
            spread_str = ', '.join(spread)

            # Проверка кэша
            question_hash = self._get_question_hash(cleaned_question)
            if question_hash in self.cache:
                return self.cache[question_hash]

            # Запрос к ИИ
            response = await client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Вопрос: {cleaned_question} Карты: {spread_str}"}
                ],
                max_completion_tokens=600
            )

            result = response.choices[0].message.content

            # Дополнительная проверка ответа от ИИ
            if self._is_rejected_response(result):
                return "К сожалению, я не могу сделать расклад на этот вопрос. Пожалуйста, задайте вопрос о вашей жизненной ситуации, отношениях или духовном пути."

            # Кэширование
            self.cache[question_hash] = result

            duration = time.time() - start_time
            logging.info(f"Таро-расклад создан за {duration:.2f}с")

            return result

        except (APIError, RateLimitError) as e:
            logging.warning(f"Ошибка OpenAI: {e}, используем fallback")
            return self._get_fallback_reading()
        except Exception as e:
            logging.error(f"Неожиданная ошибка: {e}")
            return "🔮 В настоящий момент я не могу сделать расклад. Пожалуйста, попробуйте позже."

    def _validate_question(self, question: str) -> dict:
        """Проверяет вопрос на флуд и бессмысленность"""
        question_lower = question.lower().strip()

        # Проверка длины
        if len(question) < 5:
            return {
                "valid": False,
                "message": "Пожалуйста, задайте более развернутый вопрос (минимум 5 символов)."
            }

        if len(question) > 500:
            return {
                "valid": False,
                "message": "Вопрос слишком длинный. Пожалуйста, сформулируйте его короче (до 500 символов)."
            }

        # Проверка на флуд (повторяющиеся символы) с обработкой ошибок
        try:
            for pattern in self.flood_patterns:
                if re.search(pattern, question):
                    return {
                        "valid": False,
                        "message": "Пожалуйста, задайте осмысленный вопрос для таро-расклада."
                    }
        except re.error as e:
            logging.warning(f"Ошибка в regex паттерне: {e}")  # Продолжаем без проверки regex в случае ошибки

        # Проверка на бессмысленные фразы
        for nonsense in self.nonsense_indicators:
            if nonsense in question_lower:
                return {
                    "valid": False,
                    "message": "Пожалуйста, задайте настоящий вопрос для таро-расклада."
                }

        # Проверка на слишком много одинаковых слов
        words = question_lower.split()
        if len(words) > 3:
            # Проверяем, есть ли много повторяющихся слов
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1

            # Если какое-то слово встречается слишком часто
            max_count = max(word_counts.values())
            if max_count > len(words) * 0.5:  # если одно слово занимает >50%
                return {
                    "valid": False,
                    "message": "Пожалуйста, сформулируйте вопрос более разнообразно."
                }

        # Проверка на минимальное количество уникальных слов
        unique_words = set(words)
        if len(unique_words) < 2:
            return {
                "valid": False,
                "message": "Пожалуйста, задайте более осмысленный вопрос."
            }

        return {"valid": True, "message": ""}

    def _clean_question(self, question: str) -> str:
        """Очищает и валидирует вопрос"""
        question = question.strip()
        # Удаляем лишние пробелы - просто цикл на наличие 2 пробелов в тексте
        while '  ' in question:
            question = question.replace('  ', ' ')
        return question[:500]

    def _is_rejected_response(self, response: str) -> bool:
        """Проверяет, является ли ответ отказом от ИИ"""
        if not response:
            return True

        rejection_phrases = [
            "не могу сделать расклад",
            "не могу ответить",
            "не подходит для таро",
            "отказаться",
            "не могу помочь",
            "к сожалению"
        ]
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in rejection_phrases)

    def _get_question_hash(self, question: str) -> str:
        """Создает хэш вопроса для кэширования"""
        return hashlib.md5(question.encode()).hexdigest()

    def _get_fallback_reading(self) -> str:
        """Запасной вариант когда ИИ недоступен"""
        cards = [
            {"name": "🃏 Шут", "meaning": "Начало нового пути, невинность, спонтанность"},
            {"name": "👑 Император", "meaning": "Власть, структура, контроль, стабильность"},
            {"name": "💞 Влюбленные", "meaning": "Любовь, гармония, отношения, выбор"},
            {"name": "⚖️ Правосудие", "meaning": "Справедливость, правда, карма, решение"},
            {"name": "🔄 Колесо Фортуны", "meaning": "Судьба, поворот событий, циклы жизни"},
            {"name": "💪 Сила", "meaning": "Сила воли, страсть, мужество, влияние"},
            {"name": "🏰 Башня", "meaning": "Внезапные изменения, пробуждение, откровение"},
            {"name": "🌟 Звезда", "meaning": "Надежда, вдохновение, духовность, исцеление"}]
        card = random.choice(cards)
        return f"🔮 {card['name']}\n📖 {card['meaning']}\n💫 Прислушайтесь к знакам судьбы сегодня."


# Использование
tarot_ai = TarotAI()


async def create_spread() -> list:
    """Выбирает рандомно 3 карты"""
    return random.sample(tarot_ai.major_arcana, 3)


async def card_to_sticker(card_name) -> str | None:
    """Возвращает стикер по карте таро с обработкой ошибок"""
    return tarot_ai.gifs_cards.get(card_name)


async def create_response(text: str, spread: list) -> str:
    """Создание запроса к ИИ"""
    return await tarot_ai.create_reading(text, spread)
