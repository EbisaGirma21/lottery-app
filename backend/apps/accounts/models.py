"""
Custom User model with role-based access control.

Uses UUID primary keys and email-based authentication.
"""
import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserRole(models.TextChoices):
    """Available user roles in the system."""
    SUPER_ADMIN = 'super_admin', 'Super Admin'
    LOTTERY_MANAGER = 'lottery_manager', 'Lottery Manager'
    PAYMENT_OFFICER = 'payment_officer', 'Payment Officer'
    DRAW_OFFICER = 'draw_officer', 'Draw Officer'
    VIEWER = 'viewer', 'Viewer'


class UserManager(BaseUserManager):
    """Custom manager for the User model using email as the unique identifier."""

    def create_user(self, email: str, password: str = None, **extra_fields) -> 'User':
        """Create and return a regular user with the given email and password."""
        if not email:
            raise ValueError('Users must have an email address.')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields) -> 'User':
        """Create and return a superuser with the given email and password."""
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.SUPER_ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for the Lottery Management System.

    Uses email as the login identifier and UUID as the primary key.
    Each user is assigned a role that controls their permissions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        max_length=255,
        db_index=True,
        help_text='Used as the login identifier.',
    )
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='Contact phone number.',
    )
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.VIEWER,
        db_index=True,
        help_text='Determines the permissions available to this user.',
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        default=False,
        help_text='Designates whether the user can log into the Django admin site.',
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['role'], name='idx_user_role'),
            models.Index(fields=['is_active'], name='idx_user_active'),
        ]

    def __str__(self) -> str:
        return f'{self.full_name} ({self.email})'

    @property
    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN

    @property
    def is_lottery_manager(self) -> bool:
        return self.role == UserRole.LOTTERY_MANAGER

    @property
    def is_payment_officer(self) -> bool:
        return self.role == UserRole.PAYMENT_OFFICER

    @property
    def is_draw_officer(self) -> bool:
        return self.role == UserRole.DRAW_OFFICER

    @property
    def is_viewer(self) -> bool:
        return self.role == UserRole.VIEWER
