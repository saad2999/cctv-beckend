from django.contrib import admin
from .models import User, Camera, CameraPermission ,DetectedFrame

# Register your models here.

admin.site.register(User)
admin.site.register(DetectedFrame)

admin.site.register(CameraPermission)
@admin.register(Camera)
class cameraAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "is_public","created_by","created_at","updated_at"]
    
