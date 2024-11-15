import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cctv.settings')

# Initialize Django ASGI application first
django_asgi_app = get_asgi_application()

# Import all other components after Django initialization
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from api.consumer import VideoStreamConsumer
from api.jwtMiddleware import JWTAuthMiddleware

# Define the application
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter([
            path("ws/stream/<int:camera_id>/", VideoStreamConsumer.as_asgi()),
        ])
    ),
})