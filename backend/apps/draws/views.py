"""
Views for lottery draw management and execution.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrDrawOfficer
from apps.draws.models import Draw
from apps.draws.serializers import DrawDetailSerializer, DrawExecuteSerializer


@extend_schema_view(
    list=extend_schema(tags=['Draws'], summary='List all executed lottery draws'),
    retrieve=extend_schema(tags=['Draws'], summary='Get draw details and winning tickets'),
)
class DrawViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing and executing lottery draws.

    - Draw Officer / Super Admin: Can execute a draw for a closed lottery.
    - Authenticated Staff: Can view draw results and randomness proofs.
    """
    queryset = (
        Draw.objects
        .select_related('lottery', 'executed_by')
        .prefetch_related('winners__ticket', 'winners__customer')
        .all()
    )
    serializer_class = DrawDetailSerializer
    filterset_fields = ['lottery']
    ordering_fields = ['executed_at', 'total_eligible_tickets']
    ordering = ['-executed_at']

    def get_permissions(self):
        if self.action == 'execute':
            return [IsAdminOrDrawOfficer()]
        return [IsAuthenticated()]

    @extend_schema(
        tags=['Draws'],
        summary='Execute draw for a closed lottery',
        request=DrawExecuteSerializer,
        responses={201: DrawDetailSerializer},
    )
    @action(detail=False, methods=['post'], url_path='execute')
    def execute(self, request):
        """
        Execute the cryptographic draw for a closed lottery.
        Selects 1st, 2nd, and 3rd winning tickets from all sold tickets.
        """
        serializer = DrawExecuteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        draw = serializer.save()
        return Response(
            DrawDetailSerializer(draw, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )
