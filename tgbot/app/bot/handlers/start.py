"""Обработчик команды /start и регистрации"""
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.config import Config
from app.database.database import Database
from app.database.models import User


router = Router()


class RegistrationStates(StatesGroup):
    """Состояния регистрации"""
    waiting_for_password = State()


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    config: Config,
    database: Database,
    is_authorized: bool,
):
    """
    Обработчик команды /start
    
    Args:
        message: Сообщение
        state: FSM состояние
        config: Конфигурация
        database: База данных
        is_authorized: Авторизован ли пользователь
    """
    if is_authorized:
        # Пользователь уже зарегистрирован
        await message.answer(
            "👋 Добро пожаловать!\n\n"
            "Я помогу вам скачать видео с популярных платформ:\n"
            "▶️ YouTube\n"
            "🎵 VK Видео\n"
            "📺 Rutube\n"
            "🎬 TikTok\n\n"
            "Просто отправьте мне ссылку на видео, и я предложу варианты качества для загрузки.\n\n"
            "Команды:\n"
            "/help - Справка\n"
            "/stats - Статистика\n"
            "/cancel - Отменить текущую загрузку\n"
            "/queue - Показать очередь"
        )
    else:
        # Запрос пароля
        await message.answer(
            "🔐 Добро пожаловать в Video Downloader Bot!\n\n"
            "Для доступа к боту необходимо ввести пароль:"
        )
        await state.set_state(RegistrationStates.waiting_for_password)


@router.message(RegistrationStates.waiting_for_password)
async def process_password(
    message: Message,
    state: FSMContext,
    config: Config,
    database: Database,
):
    """
    Обработка ввода пароля
    
    Args:
        message: Сообщение с паролем
        state: FSM состояние
        config: Конфигурация
        database: База данных
    """
    password = message.text.strip()
    
    if password == config.admin_password:
        # Правильный пароль - регистрация пользователя
        try:
            await database.create_user(
                user_id=message.from_user.id,
                username=message.from_user.username,
            )
            
            await message.answer(
                "✅ Регистрация успешно завершена!\n\n"
                "Теперь вы можете использовать бота.\n"
                "Отправьте мне ссылку на видео с поддерживаемой платформы:\n\n"
                "▶️ YouTube\n"
                "🎵 VK Видео\n"
                "📺 Rutube\n"
                "🎬 TikTok\n\n"
                "Команды:\n"
                "/help - Справка\n"
                "/stats - Статистика"
            )
            
            # Удаление сообщения с паролем для безопасности
            try:
                await message.delete()
            except:
                pass
            
            await state.clear()
            
        except Exception as e:
            await message.answer(
                f"❌ Ошибка при регистрации: {str(e)}\n"
                "Попробуйте еще раз с помощью команды /start"
            )
            await state.clear()
    else:
        # Неправильный пароль
        await message.answer(
            "❌ Неверный пароль. Попробуйте еще раз.\n\n"
            "Если вы не знаете пароль, обратитесь к администратору бота."
        )
        
        # Удаление сообщения с неверным паролем
        try:
            await message.delete()
        except:
            pass


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "📖 Справка по использованию бота\n\n"
        "🎥 Как скачать видео:\n"
        "1. Отправьте ссылку на видео\n"
        "2. Выберите качество из предложенных вариантов\n"
        "3. Дождитесь загрузки\n\n"
        "🎵 Загрузка аудио:\n"
        "При выборе качества нажмите кнопку 'Только аудио (MP3)'\n\n"
        "📝 Субтитры:\n"
        "После выбора качества вам будет предложено загрузить видео с субтитрами\n\n"
        "💾 Большие файлы (>2 ГБ):\n"
        "Для больших файлов бот предложит:\n"
        "• Сжать видео до размера <2 ГБ\n"
        "• Разбить на несколько частей\n\n"
        "📺 Поддерживаемые платформы:\n"
        "▶️ YouTube (youtube.com, youtu.be)\n"
        "🎵 VK Видео (vk.com, vk.ru)\n"
        "📺 Rutube (rutube.ru)\n"
        "🎬 TikTok (tiktok.com)\n\n"
        "⚙️ Команды:\n"
        "/start - Начать работу\n"
        "/help - Эта справка\n"
        "/stats - Ваша статистика\n"
        "/cancel - Отменить загрузку\n"
        "/queue - Показать очередь"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message, database: Database, db_user: User):
    """Обработчик команды /stats"""
    if not db_user:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
    
    await message.answer(
        f"📊 Ваша статистика\n\n"
        f"👤 Пользователь: {db_user.username or 'Не указано'}\n"
        f"📥 Всего загрузок: {db_user.total_downloads}\n"
        f"💾 Общий объем: {db_user.total_size_mb:.2f} МБ\n"
        f"📅 Дата регистрации: {db_user.registered_at.strftime('%d.%m.%Y %H:%M')}"
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message):
    """Обработчик команды /cancel"""
    # TODO: Реализовать отмену текущей загрузки
    await message.answer(
        "ℹ️ Для отмены загрузки нажмите кнопку 'Отменить загрузку' под сообщением о прогрессе."
    )


@router.message(Command("queue"))
async def cmd_queue(message: Message):
    """Обработчик команды /queue"""
    # TODO: Реализовать показ очереди
    await message.answer(
        "📋 Очередь загрузок пуста"
    )
