FROM python:3.10-slim

WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код бота
COPY bot /app/bot

# Переменная, чтобы Python не буферизировал вывод (логи видны сразу)
ENV PYTHONUNBUFFERED=1

# Запуск
CMD ["python", "-m", "bot.main"]
