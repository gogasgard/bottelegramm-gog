"""Отслеживание и отображение прогресса загрузки"""
import asyncio
import time
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from app.utils.helpers import format_size, format_speed, format_eta, create_progress_bar


class ProgressTracker:
    """Отслеживание прогресса загрузки"""
    
    def __init__(self, bot: Bot, chat_id: int, message_id: int):
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = message_id
        
        # Данные прогресса
        self.total_bytes: Optional[int] = None
        self.downloaded_bytes: int = 0
        self.speed: float = 0
        self.eta: int = 0
        self.status: str = "downloading"
        
        # Время последнего обновления
        self.last_update_time: float = 0
        self.update_interval: float = 3.0  # секунды
        
        # Флаг для остановки
        self.stopped: bool = False
        
        # Сохраняем event loop для вызова из других потоков
        self.loop = asyncio.get_event_loop()
    
    def create_hook(self):
        """
        Создать hook для yt-dlp
        
        Returns:
            Функция hook
        """
        def progress_hook(d):
            if self.stopped:
                return
            
            if d['status'] == 'downloading':
                self.total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                self.downloaded_bytes = d.get('downloaded_bytes', 0)
                
                # Скорость
                speed = d.get('speed')
                if speed:
                    self.speed = speed
                
                # Оставшееся время
                eta = d.get('eta')
                if eta:
                    self.eta = eta
                
                # Обновление сообщения через event loop (безопасно из другого потока)
                asyncio.run_coroutine_threadsafe(self._update_message(), self.loop)
            
            elif d['status'] == 'finished':
                self.status = 'finished'
                self.downloaded_bytes = self.total_bytes or 0
        
        return progress_hook
    
    async def _update_message(self):
        """Обновить сообщение с прогрессом"""
        current_time = time.time()
        
        # Проверка интервала обновления
        if current_time - self.last_update_time < self.update_interval:
            return
        
        self.last_update_time = current_time
        
        # Формирование текста
        text = self._format_progress()
        
        try:
            await self.bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self.message_id,
                text=text,
            )
        except TelegramBadRequest:
            # Игнорируем ошибки (например, если текст не изменился)
            pass
        except Exception as e:
            print(f"Error updating progress message: {e}")
    
    def _format_progress(self) -> str:
        """
        Форматировать текст прогресса
        
        Returns:
            Текст с прогрессом
        """
        if not self.total_bytes:
            return "📥 Загрузка видео...\n\nПодготовка..."
        
        # Процент
        percent = (self.downloaded_bytes / self.total_bytes) * 100 if self.total_bytes > 0 else 0
        
        # Прогресс-бар
        progress_bar = create_progress_bar(percent)
        
        # Размеры
        downloaded = format_size(self.downloaded_bytes)
        total = format_size(self.total_bytes)
        
        # Скорость
        speed_str = format_speed(self.speed) if self.speed > 0 else "вычисление..."
        
        # Оставшееся время
        eta_str = format_eta(self.eta) if self.eta > 0 else "вычисление..."
        
        text = (
            f"📥 Загрузка видео...\n"
            f"{progress_bar} {percent:.0f}%\n\n"
            f"⚡ Скорость: {speed_str}\n"
            f"⏳ Осталось: {eta_str}\n"
            f"💾 Загружено: {downloaded} из {total}"
        )
        
        return text
    
    async def update_status(self, status: str, text: Optional[str] = None):
        """
        Обновить статус
        
        Args:
            status: Новый статус
            text: Текст для отображения
        """
        self.status = status
        
        if text:
            try:
                await self.bot.edit_message_text(
                    chat_id=self.chat_id,
                    message_id=self.message_id,
                    text=text,
                )
            except Exception as e:
                print(f"Error updating status message: {e}")
    
    def stop(self):
        """Остановить отслеживание прогресса"""
        self.stopped = True
