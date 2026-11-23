"""
Serializers for Notification models.
"""
from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Full representation of a notification."""
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone_number', read_only=True)
    customer_telegram_id = serializers.IntegerField(source='customer.telegram_user_id', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'customer', 'customer_name', 'customer_phone', 'customer_telegram_id',
            'user',
            'channel',
            'notification_type', 'notification_type_display',
            'title', 'message',
            'status', 'status_display',
            'is_read',
            'metadata',
            'created_at', 'sent_at',
        ]
        read_only_fields = fields
