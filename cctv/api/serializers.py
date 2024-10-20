from rest_framework import serializers
from .models import Camera, CameraPermission
from .models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes,smart_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .models import User
from .utils import Util





class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'password', 'password_confirm']
        read_only_fields = ['id']

    def validate(self, data):
        # Check if passwords match
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')  # No need to pass password_confirm to create_user

        user = User.objects.create_user(
            email=validated_data['email'],
            role=validated_data.get('role', 'USER')
        )
        user.set_password(password)  # Use set_password to properly hash the password
        user.save()

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('password_confirm', None)

        if password:
            instance.set_password(password)  # Update password if it's provided
        return super().update(instance, validated_data)
    
class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = ['id', 'name',  'is_public', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class CameraPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraPermission
        fields = ['id', 'user', 'camera', 'can_view', 'can_edit']

    def validate(self, data):
        # Ensure that the user assigning permissions has the right to do so
        request_user = self.context['request'].user
        if request_user.role not in [User.role.SUPER_ADMIN, User.Role.ADMIN]:
            raise serializers.ValidationError("You don't have permission to assign camera permissions.")
        
        # If the user is an Admin, ensure they're only assigning permissions for cameras they created
        if request_user.role == User.role.ADMIN and data['camera'].created_by != request_user:
            raise serializers.ValidationError("You can only assign permissions for cameras you've created.")

        return data
    
    
class ChangeUserPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=255,style={"input_type": "password"}, write_only=True)
    password2 = serializers.CharField(max_length=255,style={"input_type": "password"}, write_only=True)
    class Meta:
        fields = ["password", "password2"]
        
    def validate(self, attrs):
        password = attrs.get("password")
        password2 = attrs.pop("password2")
        user=self.context.get("user")
        if password != password2:
            raise serializers.ValidationError("Password and confirm password must match")
        user.set_password(password)
        user.save()
        return attrs
    
class SendPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        email = attrs.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist")

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)
        reset_url = f'http://localhost:8000/api/user/reset-password/{uid}/{token}/'
        
        Util.send_email({
            'email_subject': 'Password Reset email from django',
            'email_body': f'Click the link below to reset your password\n {reset_url}',
            'recipient_email': email
        })
        return attrs


class UserPasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=255, style={"input_type": "password"}, write_only=True)
    password2 = serializers.CharField(max_length=255, style={"input_type": "password"}, write_only=True)

    class Meta:
        fields = ["password", "password2"]

    def validate(self, attrs):
        password = attrs.get("password")
        password2 = attrs.pop("password2")
        uid = self.context.get("uid")
        token = self.context.get("token")

        # Check if passwords match
        if password != password2:
            raise serializers.ValidationError("Password and confirm password must match")

        # Validate user ID and token
        try:
            id = smart_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid user or UID")

        if not PasswordResetTokenGenerator().check_token(user, token):
            raise serializers.ValidationError("Token is not valid or has expired")

        # Set the new password
        user.set_password(password)
        user.save()

        return attrs