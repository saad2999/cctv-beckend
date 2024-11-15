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
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
        
        access_token = AccessToken(token)
        user = User.objects.get(id=access_token['user_id'])
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
        return None

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope.get('query_string', b'').decode())
        token = query_string.get('token', [None])[0]

        if not token:
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode()
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            logger.warning("No authentication token provided")
            await self.close_connection(send, 4002, "Authentication token required")
            return
        
        user = await get_user_from_jwt(token)
        if user is None:
            logger.warning("Invalid or expired token")
            await self.close_connection(send, 4001, "Invalid or expired token")
            return

        scope['user'] = user
        return await super().__call__(scope, receive, send)

    async def close_connection(self, send, code, reason):
        await send({
            'type': 'websocket.close',
            'code': code
        })
        await send({
            'type': 'websocket.send',
            'text': reason
        })
