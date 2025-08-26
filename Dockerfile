FROM python:3.11-slim-buster

WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY RAG_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВЕСЬ проект
COPY . .

# Запускаем конкретный файл из папки RAG_bot
CMD ["python", "RAG_bot/bot_main.py"]