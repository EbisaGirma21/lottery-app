"""
Factory classes for creating test instances.
"""
import factory
from django.contrib.auth import get_user_model

from apps.accounts.models import UserRole

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances in tests."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f'user{n}@test.com')
    full_name = factory.Faker('name')
    phone_number = factory.Sequence(lambda n: f'+25191234{n:04d}')
    role = UserRole.VIEWER
    is_active = True
    is_staff = True

    @factory.lazy_attribute
    def password(self):
        return 'TestPass123!'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', 'TestPass123!')
        user = model_class(**kwargs)
        user.set_password(password)
        user.save()
        return user


class SuperAdminFactory(UserFactory):
    role = UserRole.SUPER_ADMIN
    is_superuser = True


class LotteryManagerFactory(UserFactory):
    role = UserRole.LOTTERY_MANAGER


class PaymentOfficerFactory(UserFactory):
    role = UserRole.PAYMENT_OFFICER


class DrawOfficerFactory(UserFactory):
    role = UserRole.DRAW_OFFICER


class ViewerFactory(UserFactory):
    role = UserRole.VIEWER
