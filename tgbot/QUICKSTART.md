# 🚀 Быстрый старт

Минимальное руководство для запуска бота за 5 минут.

## 1. Создайте Telegram бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен

## 2. Создайте канал

1. Создайте новый канал в Telegram
2. Добавьте бота как администратора с правами публикации
3. Получите ID канала через [@userinfobot](https://t.me/userinfobot):
   - Перешлите сообщение из канала боту
   - Скопируйте ID (например: `-1001234567890`)

## 3. Настройте проект

```bash
# Клонируйте и перейдите в директорию
cd tgbot

# Создайте .env файл
cp .env.example .env
```

Отредактируйте `.env`:
```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_PASSWORD=ваш_пароль
CHANNEL_ID=-1001234567890
```

## 4. Запустите бота

### Вариант A: Docker (рекомендуется)

```bash
docker-compose up -d
```

Просмотр логов:
```bash
docker-compose logs -f
```

### Вариант B: Локально

```bash
# Создайте виртуальное окружение
python -m venv venv

# Активируйте (Windows)
venv\Scripts\activate

# Или (Linux/Mac)
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt

# Запустите бота
python -m app.main
```

## 5. Используйте бота

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Введите пароль из `.env`
4. Отправьте ссылку на видео!

## Поддерживаемые платформы

- ▶️ YouTube: `https://youtube.com/watch?v=...`
- 🎵 VK Видео: `https://vk.com/video...`
- 📺 Rutube: `https://rutube.ru/video/...`
- 🎬 TikTok: `https://tiktok.com/@user/video/...`

## Команды

- `/start` - Начать работу
- `/help` - Справка
- `/stats` - Статистика

## Готово! 🎉

Теперь бот готов к использованию. Для подробной информации см. [README.md](README.md)
