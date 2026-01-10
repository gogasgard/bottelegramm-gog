"""Подключение к базе данных"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from app.config import Config
from app.database.models import Base, User, Download


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, config: Config):
        self.config = config
        # Создание асинхронного движка
        database_url = f"sqlite+aiosqlite:///{config.database_path}"
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Отключить логирование SQL запросов
        )
        # Фабрика сессий
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def init_db(self):
        """Инициализация базы данных (создание таблиц)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получение сессии для работы с БД"""
        async with self.async_session() as session:
            yield session
    
    async def close(self):
        """Закрытие подключения к БД"""
        await self.engine.dispose()
    
    # Методы для работы с пользователями
    
    async def get_user(self, user_id: int) -> User | None:
        """Получить пользователя по Telegram ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def create_user(self, user_id: int, username: str | None = None) -> User:
        """Создать нового пользователя"""
        async with self.async_session() as session:
            user = User(user_id=user_id, username=username)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
    
    async def update_user_stats(self, user_id: int, size_mb: float):
        """Обновить статистику пользователя"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.total_downloads += 1
                user.total_size_mb += size_mb
                await session.commit()
    
    # Методы для работы с загрузками
    
    async def create_download(
        self,
        user_id: int,
        url: str,
        platform: str,
        title: str | None = None,
        quality: str | None = None,
        file_size_mb: float | None = None,
        duration_seconds: int | None = None,
        download_time_seconds: float | None = None,
        forwarded_to_channel: bool = False,
        telegram_file_ids: str | None = None,  # JSON массив
        parts_count: int = 1,
    ) -> Download:
        """Создать запись о загрузке"""
        async with self.async_session() as session:
            download = Download(
                user_id=user_id,
                url=url,
                platform=platform,
                title=title,
                quality=quality,
                file_size_mb=file_size_mb,
                duration_seconds=duration_seconds,
                download_time_seconds=download_time_seconds,
                forwarded_to_channel=1 if forwarded_to_channel else 0,
                telegram_file_ids=telegram_file_ids,
                parts_count=parts_count,
            )
            session.add(download)
            await session.commit()
            await session.refresh(download)
            return download
    
    async def find_cached_video(self, url: str, quality: str) -> Download | None:
        """Найти видео в кэше по URL и качеству"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Download)
                .where(
                    Download.url == url,
                    Download.quality == quality,
                    Download.forwarded_to_channel == 1,
                    Download.telegram_file_ids.isnot(None)
                )
                .order_by(Download.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
    
    async def get_user_downloads(self, user_id: int, limit: int = 10) -> list[Download]:
        """Получить историю загрузок пользователя"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Download)
                .where(Download.user_id == user_id)
                .order_by(Download.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
