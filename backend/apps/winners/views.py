"""
Views for viewing winners and recording prize claims.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrManager
from apps.accounts.views import LoginView
from apps.winners.models import Winner
from apps.winners.serializers import (
    PublicWinnerSerializer,
    StaffWinnerSerializer,
    WinnerClaimSerializer,
)
from apps.winners.services import claim_prize


@extend_schema_view(
    list=extend_schema(tags=['Winners'], summary='List winners (publicly masked or full for staff)'),
    retrieve=extend_schema(tags=['Winners'], summary='Get winner details'),
)
class WinnerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public and staff endpoints for viewing lottery winners and recording claims.

    - Public / Telegram bot: Views winning tickets with masked customer identities.
    - Authorized Staff: Full view and capability to record prize claims.
    """
    queryset = (
        Winner.objects
        .select_related('lottery', 'ticket', 'customer', 'verified_by')
        .all()
    )
    filterset_fields = ['lottery', 'position', 'claim_status']
    ordering_fields = ['position', 'created_at', 'prize_value']
    ordering = ['position']

    def get_permissions(self):
        if self.action == 'claim':
            return [IsAdminOrManager()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action == 'claim':
            return WinnerClaimSerializer
        if self.request.user and self.request.user.is_authenticated:
            return StaffWinnerSerializer
        return PublicWinnerSerializer

    @extend_schema(
        tags=['Winners'],
        summary='Record prize claim and handover',
        request=WinnerClaimSerializer,
        responses={200: StaffWinnerSerializer},
    )
    @action(detail=True, methods=['post'], url_path='claim')
    def claim(self, request, pk=None):
        """
        Record that a winning customer has claimed their prize.
        Stores verification proof and payout transaction reference.
        """
        winner = self.get_object()
        serializer = WinnerClaimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ref = serializer.validated_data['payout_reference']
        notes = serializer.validated_data.get('admin_notes', '')
        ip_address = LoginView._get_client_ip(request)

        try:
            winner = claim_prize(
                winner=winner,
                staff_user=request.user,
                payout_reference=ref,
                admin_notes=notes,
                ip_address=ip_address,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            StaffWinnerSerializer(winner, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )
