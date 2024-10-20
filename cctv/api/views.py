from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import render
from django.contrib.auth import authenticate
import logging
from .models import User, Camera, CameraPermission
from .serializers import (
    UserSerializer, CameraSerializer, 
    CameraPermissionSerializer, UserLoginSerializer, 
    ChangeUserPasswordSerializer, SendPasswordResetEmailSerializer, 
    UserPasswordResetSerializer
)
from .premissions import IsSuperAdmin, IsAdmin, CanViewCamera, CanEditCamera
from rest_framework_simplejwt.tokens import RefreshToken

# Setup logging
logger = logging.getLogger(__name__)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        logger.debug(f"Fetching users for user role: {user.role}")
        
        if user.role == 'SUPER_ADMIN':
            return User.objects.all()
        elif user.role == 'ADMIN':
            return User.objects.filter(role='USER')
        logger.info(f"No users available for user: {user.username}")
        return User.objects.none()

    @action(detail=True, methods=['post'])
    def set_password(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if serializer.validated_data['password'] != serializer.validated_data['password_confirm']:
                return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['password'])
            user.save()
            logger.info(f"Password updated successfully for user: {user.username}")
            token = get_tokens_for_user(user)
            return Response({'token': token, 'status': 'password set'}, status=status.HTTP_200_OK)
        else:
            logger.warning(f"Password update failed for user: {user.username}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            logger.info(f"Admin permission required for action: {self.action}")
            return [permissions.IsAuthenticated(), IsAdmin()]
        elif self.action in ['retrieve', 'list']:
            logger.info(f"View camera permission required for action: {self.action}")
            return [permissions.IsAuthenticated(), CanViewCamera()]
        logger.debug(f"Permission authenticated for action: {self.action}")
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        logger.debug(f"Fetching cameras for user role: {user.role}")

        if user.role == 'SUPER_ADMIN':
            return Camera.objects.all()
        elif user.role == 'ADMIN':
            return Camera.objects.filter(created_by=user)
        else:
            return Camera.objects.filter(camerapermission__user=user, camerapermission__can_view=True)

    @action(detail=True, methods=['post'])
    def set_permissions(self, request, pk=None):
        camera = self.get_object()
        serializer = CameraPermissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(camera=camera)
            logger.info(f"Camera permissions set successfully for camera ID: {camera.id}")
            return Response(serializer.data)
        else:
            logger.warning(f"Failed to set camera permissions for camera ID: {camera.id}")
            return Response(serializer.errors, status=400)

from asgiref.sync import sync_to_async

class UserLoginView(generics.CreateAPIView):
    serializer_class = UserLoginSerializer

    @sync_to_async
    def authenticate_user(self, email, password):
        return authenticate(email=email, password=password)

    async def create(self, request, *args, **kwargs):
        logger.info("UserLoginView.post method called")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        user = await self.authenticate_user(email, password)
        if user:
            token = get_tokens_for_user(user)
            return Response({"token": token, "message": "Login successful"}, status=status.HTTP_200_OK)

        raise ValidationError({"non_field_errors": ['Email or password is not valid']})

class ChangeUserPasswordView(generics.GenericAPIView):
    serializer_class = ChangeUserPasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"user": request.user})
        if serializer.is_valid(raise_exception=True):
            request.user.set_password(serializer.validated_data['new_password'])  # Ensure the password is updated
            request.user.save()
            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SendPasswordResetEmailView(generics.CreateAPIView):
    serializer_class = SendPasswordResetEmailSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Logic to send the password reset email should go here
            return Response({"msg": "Password reset email has been sent"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserPasswordResetView(generics.CreateAPIView):
    serializer_class = UserPasswordResetSerializer

    def post(self, request, uidb64, token):
        serializer = self.get_serializer(data=request.data, context={'uid': uidb64, 'token': token})
        if serializer.is_valid():
            # Logic to reset the user's password should go here
            return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def home(request):
    logger.info("Home page accessed.")
    logger.warning("Potential issue: ensure streaming resources are available.")
    logger.error("Simulated error: This is an error message for testing purposes.")
    return render(request, 'stream.html')
