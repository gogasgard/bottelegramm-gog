"""Валидация URL"""
import re
from typing import Optional
from urllib.parse import urlparse


class URLValidator:
    """Валидатор URL для поддерживаемых платформ"""
    
    # Поддерживаемые платформы и их домены
    PLATFORMS = {
        'youtube': [
            'youtube.com',
            'youtu.be',
            'www.youtube.com',
            'm.youtube.com',
        ],
        'vk': [
            'vk.com',
            'vk.ru',
            'www.vk.com',
            'www.vk.ru',
            'm.vk.com',
            'vkvideo.ru',
            'www.vkvideo.ru',
        ],
        'rutube': [
            'rutube.ru',
            'www.rutube.ru',
        ],
        'tiktok': [
            'tiktok.com',
            'www.tiktok.com',
            'vm.tiktok.com',
            'm.tiktok.com',
        ],
    }
    
    @classmethod
    def validate_url(cls, url: str) -> tuple[bool, Optional[str]]:
        """
        Валидация URL
        
        Args:
            url: URL для проверки
            
        Returns:
            Tuple (валидный, платформа)
        """
        if not url or not isinstance(url, str):
            return False, None
        
        # Базовая проверка URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Проверка каждой платформы
            for platform, domains in cls.PLATFORMS.items():
                if any(domain == d or domain.endswith('.' + d) for d in domains):
                    return True, platform
            
            return False, None
            
        except Exception:
            return False, None
    
    @classmethod
    def get_platform(cls, url: str) -> Optional[str]:
        """
        Получить платформу из URL
        
        Args:
            url: URL видео
            
        Returns:
            Название платформы или None
        """
        is_valid, platform = cls.validate_url(url)
        return platform if is_valid else None
    
    @classmethod
    def is_supported(cls, url: str) -> bool:
        """
        Проверить, поддерживается ли URL
        
        Args:
            url: URL для проверки
            
        Returns:
            True если URL поддерживается
        """
        is_valid, _ = cls.validate_url(url)
        return is_valid
    
    @classmethod
    def get_supported_platforms(cls) -> list[str]:
        """Получить список поддерживаемых платформ"""
        return list(cls.PLATFORMS.keys())
    
    @classmethod
    def get_platform_emoji(cls, platform: str) -> str:
        """Получить эмодзи для платформы"""
        emojis = {
            'youtube': '▶️',
            'vk': '🎵',
            'rutube': '📺',
            'tiktok': '🎬',
        }
        return emojis.get(platform, '🎥')
