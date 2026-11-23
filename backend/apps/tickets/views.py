"""
Views for ticket management.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tickets.models import Ticket, TicketStatus
from apps.tickets.serializers import TicketCompactSerializer, TicketSerializer


@extend_schema_view(
    list=extend_schema(tags=['Tickets'], summary='List tickets (with filters)'),
    retrieve=extend_schema(tags=['Tickets'], summary='Get ticket details'),
)
class TicketViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ticket management.

    Tickets are created automatically when a lottery is created.
    Use filters to search by lottery, status, customer, or ticket number.
    """
    queryset = (
        Ticket.objects
        .select_related('lottery', 'customer')
        .all()
    )
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['lottery', 'status', 'customer']
    search_fields = ['ticket_number', 'customer__full_name', 'customer__phone_number']
    ordering_fields = ['ticket_number', 'status', 'created_at']


@extend_schema(tags=['Tickets'], summary='List available tickets for a lottery')
class AvailableTicketsView(viewsets.GenericViewSet):
    """
    Lists only AVAILABLE tickets for a specific lottery.
    Supports pagination for large lotteries.
    """
    queryset = Ticket.objects.none()
    serializer_class = TicketCompactSerializer
    permission_classes = []  # Public — Telegram bot needs access

    def list(self, request, lottery_id=None):
        tickets = Ticket.objects.filter(
            lottery_id=lottery_id,
            status=TicketStatus.AVAILABLE,
        ).order_by('ticket_number')

        page = self.paginate_queryset(tickets)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tickets, many=True)
        return Response(serializer.data)
