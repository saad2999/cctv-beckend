from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone



class UserManager(BaseUserManager):
    def create_user(self, email, password=None, password_confirm=None, **extra_fields):
        if password and password_confirm and password != password_confirm:
            raise ValueError('Passwords do not match')
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, password_confirm=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SUPER_ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, password_confirm, **extra_fields)
class User(AbstractUser):
    ROLES = (
        ('SUPER_ADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),
        ('USER', 'User'),
    )

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLES, default='USER')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
    
    
class Camera(models.Model):
    name = models.CharField(max_length=100)
   
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class CameraPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'camera')

    def __str__(self):
        return f"{self.user.username} - {self.camera.name}"


class DetectedFrame(models.Model):
    camera = models.ForeignKey('Camera', on_delete=models.CASCADE)
    frame_image = models.ImageField(upload_to='media/detected/')
    timestamp = models.DateTimeField(default=timezone.now)
    detection_result = models.TextField()  # Store detection information (optional)
    
    def __str__(self):
        return f"Detected Frame at {self.timestamp} for Camera {self.camera.id}"