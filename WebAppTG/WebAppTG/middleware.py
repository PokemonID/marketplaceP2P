# middleware.py
import logging
from django.utils.timezone import now

logger = logging.getLogger('user_activity')

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user if request.user.is_authenticated else 'Анонимный пользователь'
        logger.info(f"{now()} - {user} посетил {request.path} с методом {request.method}")

        # Обработка запроса
        response = self.get_response(request)

        # Логирование дополнительной информации
        if request.method in ['POST', 'PUT', 'PATCH']:  # Проверяем, если это метод, где пользователь вводит данные
            logger.info(f"Данные, введенные пользователем: {request.POST.dict()}")

        # Логирование информации о полученном ответе
        logger.info(f"Ответ статус: {response.status_code}, содержимое: {response.content.decode()}")

        return response
