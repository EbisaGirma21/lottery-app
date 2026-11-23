"""
Serializers for user management and authentication.
"""
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import User, UserRole


class UserSerializer(serializers.ModelSerializer):
    """Full representation of a user (read operations)."""
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'phone_number',
            'role', 'role_display', 'is_active',
            'date_joined', 'updated_at',
        ]
        read_only_fields = ['id', 'date_joined', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users (Super Admin only)."""
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Minimum 8 characters.',
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'phone_number',
            'role', 'password', 'confirm_password', 'is_active',
        ]
        read_only_fields = ['id']

    def validate_email(self, value: str) -> str:
        """Normalize email to lowercase."""
        return value.lower().strip()

    def validate(self, attrs: dict) -> dict:
        """Ensure passwords match and pass Django validation."""
        password = attrs.get('password')
        confirm_password = attrs.pop('confirm_password', None)

        if password != confirm_password:
            raise serializers.ValidationError(
                {'confirm_password': 'Passwords do not match.'}
            )

        validate_password(password)
        return attrs

    def create(self, validated_data: dict) -> User:
        """Create a new user with a properly hashed password."""
        password = validated_data.pop('password')
        # Set is_staff=True so staff users can access admin if needed
        if validated_data.get('role') == UserRole.SUPER_ADMIN:
            validated_data['is_staff'] = True
            validated_data['is_superuser'] = True
        else:
            validated_data['is_staff'] = True

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing users."""

    class Meta:
        model = User
        fields = ['full_name', 'phone_number', 'role', 'is_active']

    def validate_role(self, value: str) -> str:
        """Prevent non-super-admins from escalating to super_admin."""
        request = self.context.get('request')
        if value == UserRole.SUPER_ADMIN and not request.user.is_super_admin:
            raise serializers.ValidationError(
                'Only super administrators can assign the super admin role.'
            )
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs: dict) -> dict:
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('Both email and password are required.')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError('Invalid email or password.')

        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.')

        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing the current user's password."""
    current_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
    )
    confirm_new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_current_password(self, value: str) -> str:
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(
                {'confirm_new_password': 'New passwords do not match.'}
            )
        validate_password(attrs['new_password'])
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing/updating the current user's profile."""
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'phone_number',
            'role', 'role_display', 'date_joined', 'updated_at',
        ]
        read_only_fields = ['id', 'email', 'role', 'role_display', 'date_joined', 'updated_at']
