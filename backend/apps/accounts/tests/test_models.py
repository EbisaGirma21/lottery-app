"""
Tests for the custom User model.
"""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.accounts.models import UserRole

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Tests for User model creation and properties."""

    def test_create_user(self):
        """Regular user creation with email and password."""
        user = User.objects.create_user(
            email='test@example.com',
            password='SecurePass123!',
            full_name='Test User',
        )
        assert user.email == 'test@example.com'
        assert user.full_name == 'Test User'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.role == UserRole.VIEWER  # default role
        assert user.check_password('SecurePass123!')

    def test_create_user_without_email_raises(self):
        """Creating a user without an email should raise ValueError."""
        with pytest.raises(ValueError, match='email'):
            User.objects.create_user(email='', password='SecurePass123!')

    def test_create_superuser(self):
        """Superuser gets super_admin role and elevated flags."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='SecurePass123!',
            full_name='Admin User',
        )
        assert user.role == UserRole.SUPER_ADMIN
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True

    def test_create_superuser_without_is_staff_raises(self):
        with pytest.raises(ValueError, match='is_staff'):
            User.objects.create_superuser(
                email='admin@example.com',
                password='pass',
                full_name='Admin',
                is_staff=False,
            )

    def test_create_superuser_without_is_superuser_raises(self):
        with pytest.raises(ValueError, match='is_superuser'):
            User.objects.create_superuser(
                email='admin@example.com',
                password='pass',
                full_name='Admin',
                is_superuser=False,
            )

    def test_email_uniqueness(self):
        """Two users with the same email should raise IntegrityError."""
        User.objects.create_user(
            email='dup@example.com',
            password='SecurePass123!',
            full_name='First',
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='dup@example.com',
                password='SecurePass123!',
                full_name='Second',
            )

    def test_email_normalization(self):
        """Email addresses should be normalized (domain lowercased)."""
        user = User.objects.create_user(
            email='test@EXAMPLE.COM',
            password='SecurePass123!',
            full_name='Test',
        )
        assert user.email == 'test@example.com'

    def test_uuid_primary_key(self):
        """User ID should be a UUID."""
        user = User.objects.create_user(
            email='uuid@example.com',
            password='SecurePass123!',
            full_name='UUID Test',
        )
        assert user.id is not None
        assert len(str(user.id)) == 36  # UUID format

    def test_role_properties(self):
        """Role property shortcuts should work correctly."""
        user = User.objects.create_user(
            email='roles@example.com',
            password='SecurePass123!',
            full_name='Role Test',
            role=UserRole.PAYMENT_OFFICER,
        )
        assert user.is_payment_officer is True
        assert user.is_super_admin is False
        assert user.is_lottery_manager is False
        assert user.is_draw_officer is False
        assert user.is_viewer is False

    def test_str_representation(self):
        """String representation should show name and email."""
        user = User.objects.create_user(
            email='str@example.com',
            password='SecurePass123!',
            full_name='John Doe',
        )
        assert str(user) == 'John Doe (str@example.com)'

    def test_all_roles_valid(self):
        """Every defined role should be a valid choice."""
        for role_value, role_label in UserRole.choices:
            user = User.objects.create_user(
                email=f'{role_value}@example.com',
                password='SecurePass123!',
                full_name=f'{role_label} User',
                role=role_value,
            )
            assert user.role == role_value
