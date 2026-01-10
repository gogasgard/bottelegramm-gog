FROM python:3.11-slim

# Установка ffmpeg и необходимых системных пакетов
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание необходимых директорий
RUN mkdir -p data/downloads logs

# Запуск приложения
CMD ["python", "-m", "app.main"]
