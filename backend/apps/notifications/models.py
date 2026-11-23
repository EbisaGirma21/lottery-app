"""
Models for multi-channel notification dispatching and history.
"""
import uuid

from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    """Event triggers that generate customer or staff notifications."""
    RESERVATION_CREATED = 'reservation_created', 'Reservation Created'
    PAYMENT_SUBMITTED = 'payment_submitted', 'Payment Submitted'
    PAYMENT_APPROVED = 'payment_approved', 'Payment Approved'
    PAYMENT_REJECTED = 'payment_rejected', 'Payment Rejected'
    RESERVATION_EXPIRED = 'reservation_expired', 'Reservation Expired'
    DRAW_EXECUTED = 'draw_executed', 'Draw Executed'
    WINNER_ANNOUNCED = 'winner_announced', 'Winner Announced'


class NotificationChannel(models.TextChoices):
    """Delivery mechanisms for notifications."""
    IN_APP = 'in_app', 'In-App'
    TELEGRAM = 'telegram', 'Telegram'


class NotificationStatus(models.TextChoices):
    """Delivery status of a notification."""
    PENDING = 'pending', 'Pending'
    SENT = 'sent', 'Sent'
    FAILED = 'failed', 'Failed'


class Notification(models.Model):
    """
    Log and queue of notifications dispatched to customers (via Telegram)
    or administrative staff members.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        'lotteries.Customer',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text='Customer recipient (e.g. for Telegram bot delivery).',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text='Staff member recipient.',
    )
    channel = models.CharField(
        max_length=20,
        choices=NotificationChannel.choices,
        default=NotificationChannel.TELEGRAM,
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        db_index=True,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
        db_index=True,
    )
    is_read = models.BooleanField(default=False, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'is_read']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        recipient = self.customer or self.user or 'Broadcast'
        return f'[{self.get_notification_type_display()}] -> {recipient}: {self.title}'
