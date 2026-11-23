"""
Views for reservation management.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.lotteries.models import Customer, Lottery
from apps.reservations.models import Reservation
from apps.reservations.serializers import ReservationSerializer, ReserveTicketsSerializer
from apps.reservations.services import ReservationError, cancel_reservation, reserve_tickets


@extend_schema_view(
    list=extend_schema(tags=['Reservations'], summary='List reservations'),
    retrieve=extend_schema(tags=['Reservations'], summary='Get reservation details'),
)
class ReservationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only reservation listing with filters.

    Reservations are created via the reserve action.
    """
    queryset = (
        Reservation.objects
        .select_related('customer', 'lottery', 'ticket')
        .all()
    )
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['lottery', 'customer', 'status']
    search_fields = ['ticket__ticket_number', 'customer__full_name', 'customer__phone_number']
    ordering_fields = ['reserved_at', 'expires_at', 'status']

    @extend_schema(
        tags=['Reservations'],
        summary='Reserve tickets',
        request=ReserveTicketsSerializer,
        responses={201: ReservationSerializer(many=True)},
    )
    @action(detail=False, methods=['post'], url_path='reserve', permission_classes=[])
    def reserve(self, request):
        """
        Atomically reserve one or more tickets.

        Uses row-level locking to prevent duplicate reservations.
        """
        serializer = ReserveTicketsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            lottery = Lottery.objects.get(id=serializer.validated_data['lottery_id'])
        except Lottery.DoesNotExist:
            return Response(
                {'detail': 'Lottery not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            customer = Customer.objects.get(id=serializer.validated_data['customer_id'])
        except Customer.DoesNotExist:
            return Response(
                {'detail': 'Customer not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            reservations = reserve_tickets(
                customer=customer,
                lottery=lottery,
                ticket_numbers=serializer.validated_data['ticket_numbers'],
            )
        except ReservationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ReservationSerializer(reservations, many=True).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=['Reservations'],
        summary='Cancel a reservation',
    )
    @action(detail=True, methods=['post'], url_path='cancel', permission_classes=[])
    def cancel(self, request, pk=None):
        """Cancel an active reservation and release the ticket."""
        reservation = self.get_object()

        try:
            reservation = cancel_reservation(reservation)
        except ReservationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ReservationSerializer(reservation).data,
            status=status.HTTP_200_OK,
        )
