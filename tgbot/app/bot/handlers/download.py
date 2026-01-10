"""Обработчик загрузки видео"""
import json
import time
from pathlib import Path

from aiogram import Router, Bot, F
from aiogram.types import Message, FSInputFile, URLInputFile
from aiogram.exceptions import TelegramBadRequest

from app.config import Config
from app.database.database import Database
from app.services.downloader import VideoDownloader, VideoInfo
from app.services.video_processor import VideoProcessor
from app.services.progress import ProgressTracker
from app.bot.keyboards.inline import create_quality_keyboard
from app.utils.validators import URLValidator
from app.utils.helpers import format_size, format_duration, cleanup_file, bytes_to_mb


router = Router()


@router.message(F.text.regexp(r'https?://'))
async def handle_url(
    message: Message,
    config: Config,
    database: Database,
):
    """
    Обработчик URL
    
    Args:
        message: Сообщение с URL
        config: Конфигурация
        database: База данных
    """
    url = message.text.strip()
    
    # Валидация URL
    is_valid, platform = URLValidator.validate_url(url)
    
    if not is_valid:
        await message.answer(
            "❌ Ссылка не поддерживается.\n\n"
            "Поддерживаемые платформы:\n"
            "▶️ YouTube\n"
            "🎵 VK Видео\n"
            "📺 Rutube\n"
            "🎬 TikTok"
        )
        return
    
    # Отправка сообщения о загрузке информации
    status_msg = await message.answer("⏳ Получение информации о видео...")
    
    # Создание downloader
    downloader = VideoDownloader(config)
    
    # Получение информации о видео
    video_info = await downloader.get_video_info(url)
    
    if not video_info:
        await status_msg.edit_text(
            "❌ Не удалось получить информацию о видео.\n"
            "Проверьте ссылку и попробуйте еще раз."
        )
        return
    
    # Получение доступных качеств
    qualities = downloader.get_available_qualities(video_info)
    
    if not qualities:
        await status_msg.edit_text(
            "❌ Не удалось получить доступные качества для этого видео."
        )
        return
    
    # Формирование текста с информацией
    emoji = URLValidator.get_platform_emoji(platform)
    duration_str = format_duration(video_info.duration) if video_info.duration else "неизвестно"
    
    info_text = (
        f"{emoji} Видео найдено!\n\n"
        f"🎬 Название: {video_info.title}\n"
        f"👤 Автор: {video_info.uploader}\n"
        f"⏱️ Длительность: {duration_str}\n\n"
        f"Выберите качество:"
    )
    
    # Создание клавиатуры с качествами
    keyboard = create_quality_keyboard(qualities)
    
    # Отправка превью и информации
    try:
        if video_info.thumbnail:
            await status_msg.delete()
            sent_msg = await message.answer_photo(
                photo=video_info.thumbnail,
                caption=info_text,
                reply_markup=keyboard,
            )
        else:
            await status_msg.edit_text(
                text=info_text,
                reply_markup=keyboard,
            )
            sent_msg = status_msg
        
        # Сохранение информации о видео в кеш
        from app.bot.video_cache import set_video_info
        set_video_info(sent_msg.message_id, url, video_info, qualities)
        
    except Exception as e:
        await status_msg.edit_text(
            f"❌ Ошибка при отправке информации: {str(e)}"
        )


async def process_download(
    bot: Bot,
    user_id: int,
    chat_id: int,
    url: str,
    quality: str,
    audio_only: bool,
    subtitles: bool,
    config: Config,
    database: Database,
    video_info: VideoInfo,
):
    """
    Процесс загрузки и отправки видео
    
    Args:
        bot: Bot instance
        user_id: ID пользователя
        chat_id: ID чата
        url: URL видео
        quality: Качество
        audio_only: Только аудио
        subtitles: С субтитрами
        config: Конфигурация
        database: База данных
        video_info: Информация о видео
    """
    start_time = time.time()
    
    # Отправка сообщения о начале загрузки
    progress_msg = await bot.send_message(
        chat_id=chat_id,
        text="📥 Проверка кэша..."
    )
    
    # Проверка кэша: есть ли уже это видео в канале?
    quality_str = "audio" if audio_only else quality
    cached_video = await database.find_cached_video(url, quality_str)
    
    if cached_video and cached_video.telegram_file_ids:
        # Видео найдено в кэше - копируем из канала!
        try:
            # Парсим JSON с file_ids
            file_ids = json.loads(cached_video.telegram_file_ids)
            parts_count = cached_video.parts_count
            
            await progress_msg.edit_text(
                f"✨ Видео найдено в кэше канала!\n"
                f"📦 Частей: {parts_count}\n"
                f"📤 Отправка..."
            )
            
            # Отправляем все части
            for i, file_id in enumerate(file_ids):
                caption = f"📹 {cached_video.title}"
                
                if parts_count > 1:
                    caption += f"\n📦 Часть {i+1} из {parts_count}"
                
                caption += f"\n💾 Размер: {format_size(int(cached_video.file_size_mb * 1024 * 1024))}\n⚡ Из кэша канала"
                
                # Копируем файл из канала пользователю
                if audio_only:
                    await bot.send_audio(
                        chat_id=chat_id,
                        audio=file_id,
                        caption=caption,
                    )
                else:
                    await bot.send_video(
                        chat_id=chat_id,
                        video=file_id,
                        caption=caption,
                        supports_streaming=True,
                    )
            
            # Обновляем статистику
            await database.update_user_stats(user_id, cached_video.file_size_mb)
            
            # Сохраняем запись о загрузке
            await database.create_download(
                user_id=user_id,
                url=url,
                platform=video_info.platform,
                title=cached_video.title,
                quality=quality_str,
                file_size_mb=cached_video.file_size_mb,
                duration_seconds=cached_video.duration_seconds,
                download_time_seconds=time.time() - start_time,
                forwarded_to_channel=True,
                telegram_file_ids=cached_video.telegram_file_ids,
                parts_count=parts_count,
            )
            
            await progress_msg.edit_text(
                f"✅ Готово (из кэша)!\n\n"
                f"📦 Отправлено частей: {parts_count}\n"
                f"💾 Общий размер: {format_size(int(cached_video.file_size_mb * 1024 * 1024))}\n"
                f"⏱️ Время: {(time.time() - start_time):.1f} сек\n"
                f"⚡ Из кэша канала"
            )
            return
            
        except Exception as e:
            # Если не удалось отправить из кэша - загружаем заново
            await progress_msg.edit_text(
                f"⚠️ Ошибка отправки из кэша: {str(e)}\n📥 Загрузка нового файла..."
            )
    else:
        await progress_msg.edit_text("📥 Загрузка начинается...")
    
    # Создание downloader и processor
    downloader = VideoDownloader(config)
    processor = VideoProcessor(config)
    
    # Создание progress tracker
    progress_tracker = ProgressTracker(bot, chat_id, progress_msg.message_id)
    
    try:
        # Загрузка видео или аудио
        if audio_only:
            result = await downloader.download_audio(
                url=url,
                progress_callback=progress_tracker.create_hook(),
            )
            quality_str = "audio"
        else:
            result = await downloader.download_video(
                url=url,
                quality=quality,
                progress_callback=progress_tracker.create_hook(),
                download_subtitles=subtitles,
            )
            quality_str = quality
        
        if not result.success or not result.file_path:
            await progress_tracker.update_status(
                "error",
                f"❌ Ошибка загрузки: {result.error}"
            )
            return
        
        # Проверка размера файла
        needs_processing, reason = await processor.check_if_needs_processing(result.file_path)
        
        files_to_send = []
        
        if needs_processing and reason == "file_too_large" and not audio_only:
            # Файл слишком большой - разбиваем на части
            file_size_mb = result.file_size / (1024 * 1024)
            
            await progress_tracker.update_status(
                "processing",
                f"⚠️ Файл большой: {file_size_mb:.1f} МБ\n"
                f"✂️ Разбивка на части (по ~40 МБ)..."
            )
            
            # Разбивка видео
            success_split, parts, error_split = await processor.split_video(result.file_path)
            
            if success_split and parts:
                files_to_send = parts
                cleanup_file(result.file_path)
                
                await progress_tracker.update_status(
                    "processing",
                    f"✅ Разбито на {len(parts)} частей\n"
                    f"📤 Отправка..."
                )
            else:
                await progress_tracker.update_status(
                    "error",
                    f"❌ Ошибка разбивки: {error_split}\n\n"
                    f"💡 Попробуйте более низкое качество"
                )
                cleanup_file(result.file_path)
                return
                
        elif needs_processing and reason == "file_too_large" and audio_only:
            # Аудио файл слишком большой (аудио нельзя разбить)
            file_size_mb = result.file_size / (1024 * 1024)
            await progress_tracker.update_status(
                "error",
                f"❌ Аудио файл слишком большой: {file_size_mb:.1f} МБ\n"
                f"📊 Лимит: 50 МБ\n\n"
                f"💡 Решение: выберите более короткое видео"
            )
            cleanup_file(result.file_path)
            return
        else:
            files_to_send = [result.file_path]
        
        # Отправка файлов пользователю
        await progress_tracker.update_status(
            "uploading",
            "📤 Отправка файла..."
        )
        
        sent_messages = []
        total_size = sum(f.stat().st_size for f in files_to_send)
        
        for i, file_path in enumerate(files_to_send):
            try:
                file_size = file_path.stat().st_size
                caption = f"📹 {video_info.title}"
                
                if len(files_to_send) > 1:
                    caption += f"\n\n📦 Часть {i+1} из {len(files_to_send)}"
                
                caption += f"\n💾 Размер: {format_size(file_size)}"
                
                # Отправка файла
                if audio_only:
                    sent = await bot.send_audio(
                        chat_id=chat_id,
                        audio=FSInputFile(file_path),
                        caption=caption,
                        title=video_info.title,
                        performer=video_info.uploader,
                    )
                else:
                    sent = await bot.send_video(
                        chat_id=chat_id,
                        video=FSInputFile(file_path),
                        caption=caption,
                        supports_streaming=True,
                    )
                
                sent_messages.append(sent)
                
            except Exception as e:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Ошибка отправки файла {i+1}: {str(e)}"
                )
        
        # Пересылка в канал и получение file_ids для всех частей
        forwarded_to_channel = False
        telegram_file_ids = []
        
        try:
            for msg in sent_messages:
                await bot.forward_message(
                    chat_id=config.channel_id,
                    from_chat_id=chat_id,
                    message_id=msg.message_id,
                )
            forwarded_to_channel = True
            
            # Получаем file_id из ВСЕХ сообщений для кэширования
            for msg in sent_messages:
                if audio_only and msg.audio:
                    telegram_file_ids.append(msg.audio.file_id)
                elif not audio_only and msg.video:
                    telegram_file_ids.append(msg.video.file_id)
                    
        except Exception as e:
            # Уведомление пользователя об ошибке пересылки
            await bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Не удалось переслать видео в канал: {str(e)}"
            )
        
        # Удаление файлов
        for file_path in files_to_send:
            cleanup_file(file_path)
        
        # Сохранение в БД с file_ids для кэширования (JSON массив)
        download_time = time.time() - start_time
        telegram_file_ids_json = json.dumps(telegram_file_ids) if telegram_file_ids else None
        
        await database.create_download(
            user_id=user_id,
            url=url,
            platform=video_info.platform,
            title=video_info.title,
            quality=quality_str,
            file_size_mb=bytes_to_mb(total_size),
            duration_seconds=video_info.duration,
            download_time_seconds=download_time,
            forwarded_to_channel=forwarded_to_channel,
            telegram_file_ids=telegram_file_ids_json if forwarded_to_channel else None,
            parts_count=len(telegram_file_ids) if telegram_file_ids else 1,
        )
        
        # Обновление статистики пользователя
        await database.update_user_stats(user_id, bytes_to_mb(total_size))
        
        # Финальное сообщение
        await progress_tracker.update_status(
            "done",
            f"✅ Готово!\n\n"
            f"💾 Общий размер: {format_size(total_size)}\n"
            f"⏱️ Время: {download_time:.1f} сек\n"
            f"🗑️ Файлы удалены с сервера"
        )
        
    except Exception as e:
        await progress_tracker.update_status(
            "error",
            f"❌ Ошибка: {str(e)}"
        )
        
        # Очистка файлов при ошибке
        if 'result' in locals() and result.file_path:
            cleanup_file(result.file_path)
        
        if 'files_to_send' in locals():
            for file_path in files_to_send:
                cleanup_file(file_path)
