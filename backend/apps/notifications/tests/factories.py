"""
Test factories for Notification models.
"""
import factory

from apps.lotteries.tests.factories import CustomerFactory
from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)


class NotificationFactory(factory.django.DjangoModelFactory):
    """Factory for Notification instances."""

    class Meta:
        model = Notification

    customer = factory.SubFactory(CustomerFactory)
    channel = NotificationChannel.TELEGRAM
    notification_type = NotificationType.RESERVATION_CREATED
    title = 'Test Notification'
    message = 'This is a test notification message.'
    status = NotificationStatus.SENT
    is_read = False
