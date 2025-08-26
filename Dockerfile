FROM python:3.11-slim-buster

WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВЕСЬ проект
COPY . .

# Запускаем конкретный файл из папки RAG_bot
CMD ["python", "bot_main.py"]