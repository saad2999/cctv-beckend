# jwtMiddleware.py
import jwt
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from .models import User
import logging
from channels.middleware import BaseMiddleware

logger = logging.getLogger(__name__)

@database_sync_to_async
def get_user_from_jwt(token):
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        
        # Validate the token and extract user information
        access_token = AccessToken(token)
        user = User.objects.get(id=access_token['user_id'])
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
        return None

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope['query_string'].decode())
        token = query_string.get('token', [None])[0]

        if token:
            user = await get_user_from_jwt(token)
            if user is not None:
                scope['user'] = user
            else:
                logger.warning("Invalid JWT token")
                return await send({
                    "type": "websocket.close",
                    "code": 4001,
                    "reason": "Invalid or expired token"
                })
        else:
            logger.warning("JWT token missing")
            return await send({
                "type": "websocket.close",
                "code": 4002,
                "reason": "Authentication token required"
            })

        return await super().__call__(scope, receive, send)