"""
Tests for Notification model.
"""
import pytest

from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from apps.notifications.tests.factories import NotificationFactory


@pytest.mark.django_db
class TestNotificationModel:
    """Tests for Notification model fields and choices."""

    def test_create_notification(self):
        n = NotificationFactory(title='Welcome', message='Hello!')
        assert n.id is not None
        assert n.status == NotificationStatus.SENT
        assert n.is_read is False
        assert n.created_at is not None

    def test_channels_and_types(self):
        assert 'telegram' in NotificationChannel.values
        assert 'in_app' in NotificationChannel.values
        assert 'payment_approved' in NotificationType.values
        assert 'payment_rejected' in NotificationType.values
        assert 'winner_announced' in NotificationType.values

    def test_str_representation(self):
        n = NotificationFactory(title='Prize Won')
        assert 'Prize Won' in str(n)
