# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from api.consumer import VideoStreamConsumer, CameraStreamConsumer 
from  api.jwtMiddleware import JWTAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cctv.settings')


django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(AuthMiddlewareStack(
        URLRouter([
            path("ws/stream/<int:camera_id>/", VideoStreamConsumer.as_asgi()),
            path('ws/camera_stream/', CameraStreamConsumer.as_asgi()),

        ])
    ),)
})

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path('ws/camera_stream/', CameraStreamConsumer.as_asgi()),

        ])
    ),
})