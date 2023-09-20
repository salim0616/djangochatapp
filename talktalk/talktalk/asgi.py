import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import chatapp.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "talktalk.settings")

# As per the best practices creating a routing.py and include that in websocket is correct.
application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                chatapp.routing.websocket_urlpatterns,
            )
        ),
    }
)
