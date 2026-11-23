"""
Django admin configuration for audit logs.
"""
from django.contrib import admin

from apps.audit_logs.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'entity_type', 'entity_id', 'ip_address')
    list_filter = ('action', 'entity_type', 'created_at')
    search_fields = ('action', 'entity_type', 'entity_id', 'user__email')
    readonly_fields = (
        'id', 'user', 'action', 'entity_type', 'entity_id',
        'old_value', 'new_value', 'ip_address', 'created_at',
    )
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
