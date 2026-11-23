"""
Serializers for the audit logs app.
"""
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.audit_logs.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for audit log entries."""
    user_email = serializers.CharField(source='user.email', read_only=True, default=None)
    user_name = serializers.CharField(source='user.full_name', read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'action', 'entity_type', 'entity_id',
            'old_value', 'new_value',
            'ip_address', 'created_at',
        ]
        read_only_fields = fields
