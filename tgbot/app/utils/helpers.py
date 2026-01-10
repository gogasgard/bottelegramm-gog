"""Вспомогательные функции"""
import os
from pathlib import Path
from typing import Optional


def format_size(size_bytes: int) -> str:
    """
    Форматирование размера файла
    
    Args:
        size_bytes: Размер в байтах
        
    Returns:
        Строка с размером (например, "1.5 ГБ")
    """
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} ТБ"


def format_duration(seconds: int) -> str:
    """
    Форматирование длительности
    
    Args:
        seconds: Длительность в секундах
        
    Returns:
        Строка с длительностью (например, "1:23:45")
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_speed(bytes_per_second: float) -> str:
    """
    Форматирование скорости загрузки
    
    Args:
        bytes_per_second: Скорость в байтах/сек
        
    Returns:
        Строка со скоростью (например, "2.5 МБ/с")
    """
    return f"{format_size(int(bytes_per_second))}/с"


def format_eta(seconds: int) -> str:
    """
    Форматирование оставшегося времени
    
    Args:
        seconds: Секунды до завершения
        
    Returns:
        Строка с временем (например, "~2 мин 15 сек")
    """
    if seconds < 60:
        return f"~{seconds} сек"
    
    minutes = seconds // 60
    secs = seconds % 60
    
    if minutes < 60:
        if secs > 0:
            return f"~{minutes} мин {secs} сек"
        return f"~{minutes} мин"
    
    hours = minutes // 60
    mins = minutes % 60
    return f"~{hours} ч {mins} мин"


def create_progress_bar(percent: float, length: int = 20) -> str:
    """
    Создание прогресс-бара
    
    Args:
        percent: Процент выполнения (0-100)
        length: Длина прогресс-бара в символах
        
    Returns:
        Строка с прогресс-баром
    """
    filled = int(length * percent / 100)
    bar = '━' * filled + '━' * (length - filled)
    return bar


def sanitize_filename(filename: str) -> str:
    """
    Очистка имени файла от недопустимых символов
    
    Args:
        filename: Исходное имя файла
        
    Returns:
        Очищенное имя файла
    """
    # Удаление недопустимых символов для Windows
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Ограничение длины
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename


def get_file_size(file_path: Path) -> int:
    """
    Получить размер файла
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Размер файла в байтах
    """
    return file_path.stat().st_size if file_path.exists() else 0


def cleanup_file(file_path: Path) -> bool:
    """
    Удалить файл
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        True если файл успешно удален
    """
    try:
        if file_path.exists():
            file_path.unlink()
            return True
    except Exception:
        pass
    return False


def bytes_to_mb(size_bytes: int) -> float:
    """
    Конвертация байтов в мегабайты
    
    Args:
        size_bytes: Размер в байтах
        
    Returns:
        Размер в МБ
    """
    return size_bytes / (1024 * 1024)
