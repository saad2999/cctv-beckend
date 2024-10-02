from rest_framework import permissions
from .models import User

class CanViewCamera(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Super Admin or Admin can view any camera
        if request.user.role in ['SUPER_ADMIN', 'ADMIN']:
            return True
        # Check specific camera permission for the user
        return obj.camerapermission_set.filter(user=request.user, can_view=True).exists()

class CanEditCamera(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Only Super Admin can edit any camera
        if request.user.role == 'SUPER_ADMIN':
            return True
        # Admin can edit only their own cameras
        if request.user.role == 'ADMIN':
            return obj.created_by == request.user
        return False
    
class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'SUPER_ADMIN'

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'ADMIN'
