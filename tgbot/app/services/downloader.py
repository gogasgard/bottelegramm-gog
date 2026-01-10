"""Сервис загрузки видео с использованием yt-dlp"""
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
import uuid

import yt_dlp

from app.config import Config
from app.utils.helpers import sanitize_filename


@dataclass
class VideoInfo:
    """Информация о видео"""
    title: str
    uploader: str
    duration: int  # секунды
    thumbnail: Optional[str]
    formats: list[dict]
    url: str
    platform: str
    description: Optional[str] = None


@dataclass
class DownloadResult:
    """Результат загрузки"""
    success: bool
    file_path: Optional[Path]
    file_size: int  # байты
    error: Optional[str] = None


class VideoDownloader:
    """Класс для загрузки видео"""
    
    def __init__(self, config: Config):
        self.config = config
        self.downloads_path = config.downloads_path
    
    async def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """
        Получить информацию о видео
        
        Args:
            url: URL видео
            
        Returns:
            VideoInfo или None при ошибке
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            def _extract():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            # Выполнение в отдельном потоке
            info = await asyncio.to_thread(_extract)
            
            if not info:
                return None
            
            # Определение платформы
            platform = info.get('extractor_key', 'unknown').lower()
            if 'youtube' in platform:
                platform = 'youtube'
            elif 'vk' in platform:
                platform = 'vk'
            elif 'rutube' in platform:
                platform = 'rutube'
            elif 'tiktok' in platform:
                platform = 'tiktok'
            
            return VideoInfo(
                title=info.get('title', 'Unknown'),
                uploader=info.get('uploader', 'Unknown'),
                duration=info.get('duration', 0),
                thumbnail=info.get('thumbnail'),
                formats=info.get('formats', []),
                url=url,
                platform=platform,
                description=info.get('description'),
            )
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def get_available_qualities(self, video_info: VideoInfo) -> list[dict]:
        """
        Получить доступные качества видео
        
        Args:
            video_info: Информация о видео
            
        Returns:
            Список словарей с качеством и размером
        """
        qualities = {}
        
        for fmt in video_info.formats:
            # Пропускаем форматы без видео (только аудио)
            if fmt.get('vcodec') == 'none':
                continue
            
            height = fmt.get('height')
            if not height:
                continue
            
            # Определение качества
            quality_label = f"{height}p"
            
            # Размер файла
            filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0
            
            # Сохраняем только лучший формат для каждого качества
            if quality_label not in qualities or (filesize or 0) > qualities[quality_label].get('filesize', 0):
                qualities[quality_label] = {
                    'quality': quality_label,
                    'height': height,
                    'filesize': filesize,
                    'format_id': fmt.get('format_id'),
                }
        
        # Сортировка по качеству (от высокого к низкому)
        sorted_qualities = sorted(
            qualities.values(),
            key=lambda x: x['height'],
            reverse=True
        )
        
        return sorted_qualities
    
    async def download_video(
        self,
        url: str,
        quality: str,
        progress_callback: Optional[Callable] = None,
        download_subtitles: bool = False,
    ) -> DownloadResult:
        """
        Загрузить видео
        
        Args:
            url: URL видео
            quality: Качество (например, "1080p" или "best")
            progress_callback: Функция для отслеживания прогресса
            download_subtitles: Загружать ли субтитры
            
        Returns:
            DownloadResult
        """
        try:
            # Уникальное имя файла
            unique_id = str(uuid.uuid4())[:8]
            output_template = str(self.downloads_path / f"{unique_id}_%(title)s.%(ext)s")
            
            # КРИТИЧНО: YouTube форматы которые ГАРАНТИРОВАННО работают в Telegram
            # Формат 18 (360p) - ВСЕГДА есть, H.264+AAC в MP4
            # Формат 22 (720p) - обычно есть, H.264+AAC в MP4
            # Формат 37 (1080p) - иногда есть, H.264+AAC в MP4
            
            # Маппинг качества на конкретные форматы
            height = quality.replace('p', '') if quality != "best" else "9999"
            height_num = int(height)
            
            # Выбор формата на основе качества
            if height_num >= 1080 or quality == "best":
                # 1080p и выше: пробуем 37 (1080p), 22 (720p), 18 (360p)
                format_string = "37/22/18/best"
            elif height_num >= 720:
                # 720p: пробуем 22 (720p), 18 (360p)
                format_string = "22/18/best"
            elif height_num >= 480:
                # 480p: пробуем 18 (360p) - ближайший доступный
                format_string = "18/best"
            else:
                # 360p и ниже: используем 18 (360p)
                format_string = "18/best"
            
            ydl_opts = {
                'format': format_string,
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
            }
            
            # Субтитры пока отключены (требуется ffmpeg для встраивания)
            # Можно скачивать отдельными файлами, но это усложняет логику
            if download_subtitles:
                ydl_opts.update({
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': ['ru', 'en'],
                    'skip_download': False,
                })
            
            # Добавление callback для прогресса
            if progress_callback:
                ydl_opts['progress_hooks'] = [progress_callback]
            
            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    return filename
            
            # Выполнение загрузки в отдельном потоке
            filename = await asyncio.to_thread(_download)
            file_path = Path(filename)
            
            # Проверка файла
            if not file_path.exists():
                # Попытка найти файл с другим расширением
                possible_files = list(self.downloads_path.glob(f"{unique_id}_*"))
                if possible_files:
                    file_path = possible_files[0]
                else:
                    return DownloadResult(
                        success=False,
                        file_path=None,
                        file_size=0,
                        error="Файл не найден после загрузки"
                    )
            
            file_size = file_path.stat().st_size
            
            return DownloadResult(
                success=True,
                file_path=file_path,
                file_size=file_size,
            )
            
        except Exception as e:
            return DownloadResult(
                success=False,
                file_path=None,
                file_size=0,
                error=str(e)
            )
    
    async def download_audio(
        self,
        url: str,
        progress_callback: Optional[Callable] = None,
    ) -> DownloadResult:
        """
        Загрузить только аудио в формате MP3
        
        Args:
            url: URL видео
            progress_callback: Функция для отслеживания прогресса
            
        Returns:
            DownloadResult
        """
        try:
            # Уникальное имя файла
            unique_id = str(uuid.uuid4())[:8]
            output_template = str(self.downloads_path / f"{unique_id}_%(title)s.%(ext)s")
            
            # Скачиваем аудио без конвертации (не требуется ffmpeg)
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio',
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
            }
            
            # Добавление callback для прогресса
            if progress_callback:
                ydl_opts['progress_hooks'] = [progress_callback]
            
            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    return Path(filename)
            
            # Выполнение загрузки в отдельном потоке
            file_path = await asyncio.to_thread(_download)
            
            # Проверка файла
            if not file_path.exists():
                # Попытка найти файл с любым расширением
                possible_files = list(self.downloads_path.glob(f"{unique_id}_*"))
                if possible_files:
                    file_path = possible_files[0]
                else:
                    return DownloadResult(
                        success=False,
                        file_path=None,
                        file_size=0,
                        error="Аудио файл не найден после загрузки"
                    )
            
            file_size = file_path.stat().st_size
            
            return DownloadResult(
                success=True,
                file_path=file_path,
                file_size=file_size,
            )
            
        except Exception as e:
            return DownloadResult(
                success=False,
                file_path=None,
                file_size=0,
                error=str(e)
            )
