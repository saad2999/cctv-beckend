from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, consumer
from django.conf.urls.static import static 
from django.conf import settings


router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'cameras', views.CameraViewSet)
from .views import (
    
    UserLoginView,
    
    ChangeUserPasswordView,
    SendPasswordResetEmailView,
    UserPasswordResetView,
    
)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('home/', views.home, name='home'),  # Correct mapping for the home view
    path('login/', UserLoginView.as_view(), name='login'),
    path('changepassword/', ChangeUserPasswordView.as_view(), name='changepassword'),
    path('send-password-reset-email/', SendPasswordResetEmailView.as_view(), name='send-password-reset-email'),
    path('user/reset-password/<str:uidb64>/<str:token>/', UserPasswordResetView.as_view(), name='password_reset'),
    


]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

