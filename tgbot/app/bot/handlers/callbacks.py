"""Обработчик callback-кнопок"""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from app.config import Config
from app.database.database import Database
from app.bot.keyboards.inline import create_subtitles_keyboard, create_large_file_keyboard
from app.bot.handlers.download import process_download


router = Router()


@router.callback_query(F.data.startswith("quality:"))
async def callback_quality(
    callback: CallbackQuery,
    config: Config,
    database: Database,
    bot: Bot,
):
    """
    Обработчик выбора качества
    
    Args:
        callback: Callback query
        config: Конфигурация
        database: База данных
        bot: Bot instance
    """
    await callback.answer()
    
    # Получение выбранного качества
    quality = callback.data.split(":")[1]
    
    # Получение информации о видео из кеша
    from app.bot.video_cache import get_video_info
    
    video_data = None
    if callback.message:
        video_data = get_video_info(callback.message.message_id)
    
    if not video_data:
        await callback.message.edit_text(
            "❌ Информация о видео устарела. Отправьте ссылку еще раз."
        )
        return
    
    url = video_data['url']
    video_info = video_data['video_info']
    
    # Если выбрано аудио
    if quality == "audio":
        await callback.message.edit_caption(
            caption="🎵 Загрузка аудио начинается..."
        ) if callback.message.photo else await callback.message.edit_text(
            "🎵 Загрузка аудио начинается..."
        )
        
        # Запуск загрузки аудио
        await process_download(
            bot=bot,
            user_id=callback.from_user.id,
            chat_id=callback.message.chat.id,
            url=url,
            quality="audio",
            audio_only=True,
            subtitles=False,
            config=config,
            database=database,
            video_info=video_info,
        )
        
        # Очистка кеша
        from app.bot.video_cache import remove_video_info
        remove_video_info(callback.message.message_id)
        
        return
    
    # Для видео - спросить про субтитры
    keyboard = create_subtitles_keyboard(quality)
    
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=f"Качество {quality} выбрано.\n\nЗагрузить с субтитрами?",
                reply_markup=keyboard,
            )
        else:
            await callback.message.edit_text(
                text=f"Качество {quality} выбрано.\n\nЗагрузить с субтитрами?",
                reply_markup=keyboard,
            )
    except Exception as e:
        print(f"Error editing message: {e}")


@router.callback_query(F.data.startswith("download:"))
async def callback_download(
    callback: CallbackQuery,
    config: Config,
    database: Database,
    bot: Bot,
):
    """
    Обработчик начала загрузки
    
    Args:
        callback: Callback query
        config: Конфигурация
        database: База данных
        bot: Bot instance
    """
    await callback.answer()
    
    # Парсинг данных: download:quality:subs/nosubs
    parts = callback.data.split(":")
    quality = parts[1]
    subtitles = parts[2] == "subs"
    
    # Получение информации о видео из кеша
    from app.bot.video_cache import get_video_info
    
    video_data = None
    if callback.message:
        video_data = get_video_info(callback.message.message_id)
    
    if not video_data:
        await callback.message.edit_text(
            "❌ Информация о видео устарела. Отправьте ссылку еще раз."
        )
        return
    
    url = video_data['url']
    video_info = video_data['video_info']
    
    # Обновление сообщения
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=f"🎬 Загрузка видео {quality} начинается..."
            )
        else:
            await callback.message.edit_text(
                f"🎬 Загрузка видео {quality} начинается..."
            )
    except Exception:
        pass
    
    # Запуск загрузки
    await process_download(
        bot=bot,
        user_id=callback.from_user.id,
        chat_id=callback.message.chat.id,
        url=url,
        quality=quality,
        audio_only=False,
        subtitles=subtitles,
        config=config,
        database=database,
        video_info=video_info,
    )
    
    # Очистка кеша
    from app.bot.video_cache import remove_video_info
    remove_video_info(callback.message.message_id)


@router.callback_query(F.data == "back_to_quality")
async def callback_back(callback: CallbackQuery):
    """Обработчик кнопки "Назад" """
    await callback.answer()
    
    # Получение информации о видео из кеша
    from app.bot.video_cache import get_video_info
    
    video_data = None
    if callback.message:
        video_data = get_video_info(callback.message.message_id)
    
    if not video_data:
        await callback.message.edit_text(
            "❌ Информация о видео устарела. Отправьте ссылку еще раз."
        )
        return
    
    # Восстановление клавиатуры с качествами
    from app.bot.keyboards.inline import create_quality_keyboard
    from app.utils.validators import URLValidator
    from app.utils.helpers import format_duration
    
    video_info = video_data['video_info']
    qualities = video_data['qualities']
    
    emoji = URLValidator.get_platform_emoji(video_info.platform)
    duration_str = format_duration(video_info.duration) if video_info.duration else "неизвестно"
    
    info_text = (
        f"{emoji} Видео найдено!\n\n"
        f"🎬 Название: {video_info.title}\n"
        f"👤 Автор: {video_info.uploader}\n"
        f"⏱️ Длительность: {duration_str}\n\n"
        f"Выберите качество:"
    )
    
    keyboard = create_quality_keyboard(qualities)
    
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=info_text,
                reply_markup=keyboard,
            )
        else:
            await callback.message.edit_text(
                text=info_text,
                reply_markup=keyboard,
            )
    except Exception as e:
        print(f"Error editing message: {e}")


@router.callback_query(F.data == "cancel")
async def callback_cancel(callback: CallbackQuery):
    """Обработчик кнопки отмены"""
    await callback.answer("Отменено")
    
    # Удаление из кеша
    from app.bot.video_cache import remove_video_info
    if callback.message:
        remove_video_info(callback.message.message_id)
    
    try:
        await callback.message.delete()
    except Exception:
        try:
            await callback.message.edit_text("❌ Отменено")
        except Exception:
            pass


@router.callback_query(F.data == "cancel_download")
async def callback_cancel_download(callback: CallbackQuery):
    """Обработчик отмены загрузки"""
    await callback.answer("Загрузка отменена", show_alert=True)
    
    try:
        await callback.message.edit_text("❌ Загрузка отменена пользователем")
    except Exception:
        pass
