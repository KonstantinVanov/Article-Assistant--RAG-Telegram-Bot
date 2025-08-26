FROM python:3.11-slim-buster

WORKDIR /app

# Копируем зависимости сначала для лучшего кэширования
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только нужные файлы (более безопасно)
COPY RAG_bot/ ./RAG_bot/
COPY *.py *.md .env.example ./

# Устанавливаем рабочую директорию для приложения
WORKDIR /app/RAG_bot

# Запускаем бота
CMD ["python", "RAG_bot/main.py"]