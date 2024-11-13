import logging
import pprint

logger = logging.getLogger('user_activity')

def log_function_call(func):
    def wrapper(*args, **kwargs):
        # Используем pprint для форматирования аргументов
        formatted_args = pprint.pformat(args, indent=2)
        formatted_kwargs = pprint.pformat(kwargs, indent=2)
        
        # Логируем более структурированную информацию
        logger.info(f"Вызвана функция: {func.__name__}\nАргументы: {formatted_args}\nКлючевые аргументы: {formatted_kwargs}")
        
        # Выполняем функцию
        return func(*args, **kwargs)
    return wrapper
