"""Конфигурация приложения"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()


@dataclass
class Config:
    """Конфигурация бота"""
    
    # Telegram Bot
    bot_token: str
    admin_password: str
    channel_id: int  # ID канала для пересылки видео
    
    # Пути
    database_path: Path
    downloads_path: Path
    logs_path: Path
    
    # Настройки
    log_level: str
    
    # Ограничения
    max_file_size: int = 50_000_000  # 50 МБ (лимит Telegram Bot API)
    split_part_size: int = 40_000_000  # 40 МБ для каждой части (с запасом)
    
    # Прогресс
    progress_update_interval: int = 3  # секунды между обновлениями прогресса
    
    def __post_init__(self):
        """Создание директорий после инициализации"""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.downloads_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    """Загрузка конфигурации из переменных окружения"""
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN не установлен в .env файле")
    
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise ValueError("ADMIN_PASSWORD не установлен в .env файле")
    
    channel_id_str = os.getenv("CHANNEL_ID")
    if not channel_id_str:
        raise ValueError("CHANNEL_ID не установлен в .env файле")
    
    try:
        channel_id = int(channel_id_str)
    except ValueError:
        raise ValueError("CHANNEL_ID должен быть числом")
    
    database_path = Path(os.getenv("DATABASE_PATH", "data/database.db"))
    downloads_path = Path(os.getenv("DOWNLOADS_PATH", "data/downloads"))
    logs_path = Path(os.getenv("LOGS_PATH", "logs"))
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    return Config(
        bot_token=bot_token,
        admin_password=admin_password,
        channel_id=channel_id,
        database_path=database_path,
        downloads_path=downloads_path,
        logs_path=logs_path,
        log_level=log_level,
    )
