"""Менеджер очереди загрузок"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class DownloadTask:
    """Задача загрузки"""
    user_id: int
    url: str
    quality: str
    audio_only: bool
    subtitles: bool
    callback: Callable
    message_id: int


class QueueManager:
    """Менеджер очереди загрузок"""
    
    def __init__(self):
        # Очереди для каждого пользователя
        self.user_queues: dict[int, asyncio.Queue] = defaultdict(asyncio.Queue)
        # Активные задачи
        self.active_tasks: dict[int, asyncio.Task] = {}
        # Блокировки для каждого пользователя
        self.locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
    
    async def add_task(
        self,
        user_id: int,
        url: str,
        quality: str,
        audio_only: bool,
        subtitles: bool,
        callback: Callable,
        message_id: int,
    ) -> int:
        """
        Добавить задачу в очередь
        
        Args:
            user_id: ID пользователя
            url: URL видео
            quality: Качество
            audio_only: Только аудио
            subtitles: С субтитрами
            callback: Функция обработки
            message_id: ID сообщения для обновления
            
        Returns:
            Позиция в очереди
        """
        task = DownloadTask(
            user_id=user_id,
            url=url,
            quality=quality,
            audio_only=audio_only,
            subtitles=subtitles,
            callback=callback,
            message_id=message_id,
        )
        
        # Добавление в очередь
        await self.user_queues[user_id].put(task)
        
        # Получение позиции в очереди
        position = self.user_queues[user_id].qsize()
        
        # Запуск обработчика очереди, если он не запущен
        if user_id not in self.active_tasks or self.active_tasks[user_id].done():
            self.active_tasks[user_id] = asyncio.create_task(
                self._process_queue(user_id)
            )
        
        return position
    
    async def _process_queue(self, user_id: int):
        """
        Обработка очереди пользователя
        
        Args:
            user_id: ID пользователя
        """
        queue = self.user_queues[user_id]
        
        while not queue.empty():
            # Получение задачи
            task: DownloadTask = await queue.get()
            
            try:
                # Выполнение задачи
                await task.callback(task)
            except Exception as e:
                print(f"Error processing task for user {user_id}: {e}")
            finally:
                # Отметка задачи как выполненной
                queue.task_done()
    
    def get_queue_size(self, user_id: int) -> int:
        """
        Получить размер очереди пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Количество задач в очереди
        """
        return self.user_queues[user_id].qsize()
    
    def is_processing(self, user_id: int) -> bool:
        """
        Проверить, обрабатывается ли очередь пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если очередь обрабатывается
        """
        return (
            user_id in self.active_tasks
            and not self.active_tasks[user_id].done()
        )
    
    async def cancel_queue(self, user_id: int) -> int:
        """
        Отменить все задачи пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Количество отмененных задач
        """
        queue = self.user_queues[user_id]
        cancelled_count = queue.qsize()
        
        # Очистка очереди
        while not queue.empty():
            try:
                queue.get_nowait()
                queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        # Отмена активной задачи
        if user_id in self.active_tasks and not self.active_tasks[user_id].done():
            self.active_tasks[user_id].cancel()
        
        return cancelled_count
