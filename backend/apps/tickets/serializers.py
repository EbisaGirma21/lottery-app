"""
Serializers for the tickets app.
"""
from rest_framework import serializers

from apps.tickets.models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    """Full ticket representation."""
    lottery_name = serializers.CharField(source='lottery.name', read_only=True)
    customer_name = serializers.CharField(
        source='customer.full_name', read_only=True, default=None,
    )
    customer_phone = serializers.CharField(
        source='customer.phone_number', read_only=True, default=None,
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True,
    )

    class Meta:
        model = Ticket
        fields = [
            'id', 'lottery', 'lottery_name',
            'ticket_number', 'status', 'status_display',
            'customer', 'customer_name', 'customer_phone',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class TicketCompactSerializer(serializers.ModelSerializer):
    """Minimal ticket representation for availability lists."""
    status_display = serializers.CharField(
        source='get_status_display', read_only=True,
    )

    class Meta:
        model = Ticket
        fields = ['id', 'ticket_number', 'status', 'status_display']
        read_only_fields = fields
