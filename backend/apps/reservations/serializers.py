"""
Serializers for the reservations app.
"""
from rest_framework import serializers

from apps.reservations.models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    """Full reservation representation."""
    customer_name = serializers.CharField(
        source='customer.full_name', read_only=True,
    )
    customer_phone = serializers.CharField(
        source='customer.phone_number', read_only=True,
    )
    lottery_name = serializers.CharField(
        source='lottery.name', read_only=True,
    )
    ticket_number = serializers.CharField(
        source='ticket.ticket_number', read_only=True,
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True,
    )

    class Meta:
        model = Reservation
        fields = [
            'id',
            'customer', 'customer_name', 'customer_phone',
            'lottery', 'lottery_name',
            'ticket', 'ticket_number',
            'reserved_at', 'expires_at',
            'status', 'status_display',
        ]
        read_only_fields = fields


class ReserveTicketsSerializer(serializers.Serializer):
    """Serializer for the ticket reservation request."""
    lottery_id = serializers.UUIDField()
    customer_id = serializers.UUIDField()
    ticket_numbers = serializers.ListField(
        child=serializers.CharField(max_length=20),
        min_length=1,
        help_text='List of ticket number strings to reserve.',
    )
