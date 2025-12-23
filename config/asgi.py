import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import chat.routing  # استدعاء ملف routing الخاص بالتطبيق

# تحديد إعدادات Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# تكوين تطبيق ASGI
application = ProtocolTypeRouter({
    # إعداد الاتصال عبر HTTP
    'http': get_asgi_application(),

    # إعداد الاتصال عبر WebSocket
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                chat.routing.websocket_urlpatterns  # جميع روابط WebSocket للتطبيق
            )
        )
    ),
})
