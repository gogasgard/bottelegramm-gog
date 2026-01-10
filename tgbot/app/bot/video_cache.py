"""Общий кеш для информации о видео"""

# Глобальный кеш для хранения информации о видео
# Ключ: message_id, Значение: dict с url, video_info, qualities
video_info_cache = {}


def set_video_info(message_id: int, url: str, video_info, qualities: list):
    """
    Сохранить информацию о видео в кеш
    
    Args:
        message_id: ID сообщения
        url: URL видео
        video_info: Информация о видео
        qualities: Список доступных качеств
    """
    video_info_cache[message_id] = {
        'url': url,
        'video_info': video_info,
        'qualities': qualities,
    }


def get_video_info(message_id: int):
    """
    Получить информацию о видео из кеша
    
    Args:
        message_id: ID сообщения
        
    Returns:
        dict с информацией или None
    """
    return video_info_cache.get(message_id)


def remove_video_info(message_id: int):
    """
    Удалить информацию о видео из кеша
    
    Args:
        message_id: ID сообщения
    """
    if message_id in video_info_cache:
        del video_info_cache[message_id]
