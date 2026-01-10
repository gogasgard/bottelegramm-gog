"""Inline клавиатуры"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_quality_keyboard(qualities: list[dict], with_audio: bool = True) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для выбора качества
    
    Args:
        qualities: Список доступных качеств
        with_audio: Показать кнопку "Только аудио"
        
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопки качества
    for quality in qualities:
        quality_label = quality['quality']
        filesize = quality.get('filesize', 0)
        
        # Форматирование размера
        if filesize > 0:
            size_mb = filesize / (1024 * 1024)
            if size_mb >= 1024:
                size_str = f"{size_mb / 1024:.1f} ГБ"
            else:
                size_str = f"{size_mb:.0f} МБ"
            button_text = f"{quality_label} ({size_str})"
        else:
            button_text = quality_label
        
        builder.button(
            text=button_text,
            callback_data=f"quality:{quality_label}"
        )
    
    # 2 кнопки в ряд для качества
    builder.adjust(2)
    
    # Кнопка "Только аудио"
    if with_audio:
        builder.row(
            InlineKeyboardButton(
                text="🎵 Только аудио (MP3)",
                callback_data="quality:audio"
            )
        )
    
    # Кнопка отмены
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def create_subtitles_keyboard(quality: str) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для выбора субтитров
    
    Args:
        quality: Выбранное качество
        
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ С субтитрами",
            callback_data=f"download:{quality}:subs"
        ),
        InlineKeyboardButton(
            text="❌ Без субтитров",
            callback_data=f"download:{quality}:nosubs"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_quality"
        )
    )
    
    return builder.as_markup()


def create_large_file_keyboard(quality: str, subtitles: bool) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для обработки большого файла
    
    Args:
        quality: Выбранное качество
        subtitles: С субтитрами или нет
        
    Returns:
        InlineKeyboardMarkup
    """
    subs_str = "subs" if subtitles else "nosubs"
    
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🗜️ Сжать видео",
            callback_data=f"process:{quality}:{subs_str}:compress"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="✂️ Разбить на части",
            callback_data=f"process:{quality}:{subs_str}:split"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def create_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Создать клавиатуру с кнопкой отмены
    
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить загрузку",
            callback_data="cancel_download"
        )
    )
    
    return builder.as_markup()
