"""
Django admin configuration for notifications app.
"""
from django.contrib import admin
from django.utils.html import format_html

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'notification_type',
        'customer',
        'user',
        'channel',
        'status_badge',
        'is_read',
        'created_at',
    )
    list_filter = ('notification_type', 'channel', 'status', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'customer__full_name', 'customer__phone_number')
    readonly_fields = ('id', 'created_at', 'sent_at')

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'sent': '#10b981',
            'failed': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = 'Status'
