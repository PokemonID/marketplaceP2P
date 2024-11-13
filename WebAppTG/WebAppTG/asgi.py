"""
ASGI config for WebAppTG project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import testsite.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebAppTG.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # "https": get_asgi_application(),
    "websocket": AuthMiddlewareStack(URLRouter(testsite.routing.websocket_urlpatterns)),
    # Just HTTP for now. (We can add other protocols later.)
})
