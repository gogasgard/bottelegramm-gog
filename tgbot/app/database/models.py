"""Модели базы данных"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для моделей"""
    pass


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    total_downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_size_mb: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Связь с загрузками
    downloads: Mapped[list["Download"]] = relationship("Download", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, username={self.username})>"


class Download(Base):
    """Модель загрузки видео"""
    __tablename__ = "downloads"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)  # Индекс для быстрого поиска
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # youtube, vk, rutube, tiktok
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    quality: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 1080p, 720p, audio, etc
    file_size_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    download_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    forwarded_to_channel: Mapped[bool] = mapped_column(Integer, default=0, nullable=False)  # SQLite не поддерживает bool
    telegram_file_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON массив file_id для всех частей
    parts_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Количество частей
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Связь с пользователем
    user: Mapped["User"] = relationship("User", back_populates="downloads")
    
    def __repr__(self) -> str:
        return f"<Download(id={self.id}, platform={self.platform}, title={self.title})>"
