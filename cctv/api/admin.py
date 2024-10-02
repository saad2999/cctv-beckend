from django.contrib import admin
from .models import User, Camera, CameraPermission

# Register your models here.

admin.site.register(User)
admin.site.register(Camera)
admin.site.register(CameraPermission)
