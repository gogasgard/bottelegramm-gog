"""Главный модуль приложения"""
import asyncio
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from app.config import load_config
from app.database.database import Database
from app.bot.middlewares.auth import AuthMiddleware
from app.bot.handlers import start, download, callbacks


async def main():
    """Главная функция"""
    
    # Загрузка конфигурации
    try:
        config = load_config()
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}")
        print("Убедитесь, что файл .env настроен правильно")
        sys.exit(1)
    
    # Настройка логирования
    logger.remove()  # Удаление стандартного обработчика
    
    # Логирование в консоль
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=config.log_level,
        colorize=True,
    )
    
    # Логирование в файл
    log_file = config.logs_path / "bot.log"
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=config.log_level,
        rotation="10 MB",  # Ротация при достижении 10 МБ
        retention="7 days",  # Хранение 7 дней
        compression="zip",  # Сжатие старых логов
    )
    
    logger.info("Запуск бота...")
    
    # Инициализация базы данных
    database = Database(config)
    await database.init_db()
    logger.info("База данных инициализирована")
    
    # Создание бота и диспетчера
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация middleware
    dp.message.middleware(AuthMiddleware(database))
    dp.callback_query.middleware(AuthMiddleware(database))
    logger.info("Middleware зарегистрированы")
    
    # Передача зависимостей через workflow_data
    dp.workflow_data.update({
        "config": config,
        "database": database,
        "bot": bot,
    })
    
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(download.router)
    dp.include_router(callbacks.router)
    logger.info("Обработчики зарегистрированы")
    
    # Получение информации о боте
    try:
        bot_info = await bot.get_me()
        logger.info(f"Бот запущен: @{bot_info.username}")
    except Exception as e:
        logger.error(f"Ошибка получения информации о боте: {e}")
        sys.exit(1)
    
    # Проверка доступа к каналу
    try:
        chat = await bot.get_chat(config.channel_id)
        logger.info(f"Канал для пересылки: {chat.title or chat.username or config.channel_id}")
    except Exception as e:
        logger.warning(f"Не удалось получить информацию о канале: {e}")
        logger.warning("Убедитесь, что бот добавлен в канал как администратор")
    
    try:
        # Запуск polling
        logger.info("Начало polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
    finally:
        # Закрытие соединений
        await bot.session.close()
        await database.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)
