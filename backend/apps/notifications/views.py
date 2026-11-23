"""
Views for viewing and managing notifications.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


@extend_schema_view(
    list=extend_schema(tags=['Notifications'], summary='List notifications (filtered by customer or staff)'),
    retrieve=extend_schema(tags=['Notifications'], summary='Get notification details'),
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoints for listing and acknowledging notifications.

    - Telegram Bot / Customer: Can query notifications for a specific `telegram_user_id`.
    - Authenticated Staff: Can browse all system notifications.
    """
    queryset = Notification.objects.select_related('customer', 'user').all()
    serializer_class = NotificationSerializer
    filterset_fields = ['notification_type', 'channel', 'status', 'is_read']
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']

    def get_permissions(self):
        # Allow bot / customers to view their notifications
        if self.action in ('list', 'retrieve', 'mark_read', 'my_notifications'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ('mark_read', 'retrieve'):
            return qs

        telegram_id = self.request.query_params.get('telegram_user_id')
        customer_id = self.request.query_params.get('customer_id')

        if telegram_id:
            qs = qs.filter(customer__telegram_user_id=telegram_id)
        elif customer_id:
            qs = qs.filter(customer_id=customer_id)
        elif not (self.request.user and self.request.user.is_authenticated):
            # Unauthenticated requests without customer identifier see none
            return qs.none()

        return qs

    @extend_schema(
        tags=['Notifications'],
        summary='Mark notification as read',
        responses={200: NotificationSerializer},
    )
    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)
