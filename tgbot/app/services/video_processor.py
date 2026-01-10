"""Обработка видео: сжатие и разбивка"""
import asyncio
import math
from pathlib import Path
from typing import Optional

import ffmpeg

from app.config import Config


class VideoProcessor:
    """Класс для обработки видео"""
    
    def __init__(self, config: Config):
        self.config = config
        self.max_file_size = config.max_file_size
        self.split_part_size = config.split_part_size
    
    async def compress_video(
        self,
        input_path: Path,
        target_size_mb: Optional[int] = None,
    ) -> tuple[bool, Optional[Path], Optional[str]]:
        """
        Сжать видео
        
        Args:
            input_path: Путь к исходному видео
            target_size_mb: Целевой размер в МБ (по умолчанию 1900 МБ)
            
        Returns:
            (успех, путь к сжатому видео, ошибка)
        """
        try:
            if not target_size_mb:
                target_size_mb = 1900  # Чуть меньше 2 ГБ
            
            # Выходной файл
            output_path = input_path.with_stem(f"{input_path.stem}_compressed")
            
            # Получение информации о видео
            probe = await asyncio.to_thread(
                ffmpeg.probe, str(input_path)
            )
            
            # Длительность видео
            duration = float(probe['format']['duration'])
            
            # Вычисление целевого битрейта
            target_size_bits = target_size_mb * 8 * 1024 * 1024
            target_bitrate = int(target_size_bits / duration)
            
            # Ограничение битрейта (не меньше 500k)
            if target_bitrate < 500000:
                target_bitrate = 500000
            
            # Сжатие видео
            def _compress():
                stream = ffmpeg.input(str(input_path))
                stream = ffmpeg.output(
                    stream,
                    str(output_path),
                    video_bitrate=target_bitrate,
                    audio_bitrate='128k',
                    **{'c:v': 'libx264', 'c:a': 'aac', 'preset': 'medium'}
                )
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            await asyncio.to_thread(_compress)
            
            if output_path.exists():
                return True, output_path, None
            else:
                return False, None, "Файл не создан после сжатия"
            
        except Exception as e:
            return False, None, f"Ошибка сжатия: {str(e)}"
    
    async def split_video(
        self,
        input_path: Path,
    ) -> tuple[bool, list[Path], Optional[str]]:
        """
        Разбить видео на части
        
        Args:
            input_path: Путь к исходному видео
            
        Returns:
            (успех, список путей к частям, ошибка)
        """
        try:
            # Получение информации о видео
            probe = await asyncio.to_thread(
                ffmpeg.probe, str(input_path)
            )
            
            # Размер и длительность
            file_size = input_path.stat().st_size
            duration = float(probe['format']['duration'])
            
            # Вычисление количества частей
            num_parts = math.ceil(file_size / self.split_part_size)
            
            # Длительность каждой части
            part_duration = duration / num_parts
            
            parts = []
            
            for i in range(num_parts):
                # Выходной файл
                output_path = input_path.with_stem(f"{input_path.stem}_part{i+1}")
                
                # Время начала
                start_time = i * part_duration
                
                # Разбивка
                def _split(start, dur, output):
                    stream = ffmpeg.input(str(input_path), ss=start, t=dur)
                    stream = ffmpeg.output(
                        stream,
                        str(output),
                        **{'c': 'copy'}  # Копирование без перекодирования
                    )
                    ffmpeg.run(stream, overwrite_output=True, quiet=True)
                
                await asyncio.to_thread(_split, start_time, part_duration, output_path)
                
                if output_path.exists():
                    parts.append(output_path)
                else:
                    return False, [], f"Не удалось создать часть {i+1}"
            
            return True, parts, None
            
        except Exception as e:
            return False, [], f"Ошибка разбивки: {str(e)}"
    
    async def get_video_duration(self, input_path: Path) -> Optional[float]:
        """
        Получить длительность видео
        
        Args:
            input_path: Путь к видео
            
        Returns:
            Длительность в секундах или None
        """
        try:
            probe = await asyncio.to_thread(
                ffmpeg.probe, str(input_path)
            )
            return float(probe['format']['duration'])
        except Exception:
            return None
    
    async def check_if_needs_processing(self, file_path: Path) -> tuple[bool, str]:
        """
        Проверить, нужна ли обработка файла
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            (нужна обработка, причина)
        """
        file_size = file_path.stat().st_size
        
        if file_size > self.max_file_size:
            return True, "file_too_large"
        
        return False, "ok"
