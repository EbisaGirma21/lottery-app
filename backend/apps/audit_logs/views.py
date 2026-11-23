"""
Views for the audit logs app.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsSuperAdmin, IsViewer, ReadOnly
from apps.audit_logs.models import AuditLog
from apps.audit_logs.serializers import AuditLogSerializer


@extend_schema_view(
    list=extend_schema(tags=['Audit Logs'], summary='List audit log entries'),
    retrieve=extend_schema(tags=['Audit Logs'], summary='Get audit log details'),
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to the system audit trail.

    - Super Admin: Full read access.
    - Viewer: Read access.
    - Other roles: No access.
    """
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin | (IsViewer & ReadOnly)]
    filterset_fields = ['action', 'entity_type', 'user']
    search_fields = ['action', 'entity_type', 'entity_id']
    ordering_fields = ['created_at', 'action']
