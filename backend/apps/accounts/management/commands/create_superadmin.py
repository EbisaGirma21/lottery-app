"""
Management command to create the initial super admin user.

Usage:
    python manage.py create_superadmin

Credentials are read from environment variables:
    SUPERADMIN_EMAIL
    SUPERADMIN_PASSWORD
    SUPERADMIN_FULL_NAME
"""
from decouple import config
from django.core.management.base import BaseCommand

from apps.accounts.models import User, UserRole


class Command(BaseCommand):
    help = 'Create the initial super admin user from environment variables.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Override the email from environment variable.',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Override the password from environment variable.',
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Override the full name from environment variable.',
        )

    def handle(self, *args, **options):
        email = (
            options.get('email')
            or config('SUPERADMIN_EMAIL', default='admin@lottery.com')
        ).lower().strip()

        password = (
            options.get('password')
            or config('SUPERADMIN_PASSWORD', default='admin123456')
        )

        full_name = (
            options.get('name')
            or config('SUPERADMIN_FULL_NAME', default='System Administrator')
        )

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{email}" already exists. Skipping.')
            )
            return

        user = User.objects.create_superuser(
            email=email,
            password=password,
            full_name=full_name,
            role=UserRole.SUPER_ADMIN,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Super admin created successfully:\n'
                f'  Email: {user.email}\n'
                f'  Name:  {user.full_name}\n'
                f'  Role:  {user.get_role_display()}'
            )
        )
