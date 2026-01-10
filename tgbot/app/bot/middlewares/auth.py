"""Middleware для проверки авторизации"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.database.database import Database


class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки авторизации пользователя"""
    
    def __init__(self, database: Database):
        super().__init__()
        self.database = database
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        """
        Обработка события
        
        Args:
            handler: Следующий обработчик
            event: Событие (сообщение или callback)
            data: Данные
            
        Returns:
            Результат обработчика
        """
        # Получение пользователя
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        else:
            return await handler(event, data)
        
        if not user:
            return
        
        # Проверка, зарегистрирован ли пользователь
        db_user = await self.database.get_user(user.id)
        
        # Добавление информации о пользователе в данные
        data['db_user'] = db_user
        data['is_authorized'] = db_user is not None
        
        # Получение FSM состояния
        state: FSMContext = data.get("state")
        current_state = None
        if state:
            current_state = await state.get_state()
        
        # Пропуск команды /start для незарегистрированных пользователей
        if isinstance(event, Message):
            if event.text and event.text.startswith('/start'):
                return await handler(event, data)
            
            # Пропуск сообщений во время процесса регистрации (FSM состояние)
            if current_state is not None:
                return await handler(event, data)
        
        # Блокировка доступа для незарегистрированных пользователей
        if not db_user:
            if isinstance(event, Message):
                await event.answer(
                    "🔐 Для использования бота необходимо пройти регистрацию.\n"
                    "Используйте команду /start"
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "🔐 Для использования бота необходимо пройти регистрацию.",
                    show_alert=True
                )
            return
        
        # Продолжение обработки
        return await handler(event, data)
