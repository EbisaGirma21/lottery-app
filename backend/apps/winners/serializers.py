"""
Serializers for Winner models, public display, staff detail, and prize claim.
"""
from rest_framework import serializers

from apps.winners.models import Winner


class PublicWinnerSerializer(serializers.ModelSerializer):
    """Public serializer with masked customer identities for Telegram bot and website."""
    ticket_number = serializers.CharField(source='ticket.ticket_number', read_only=True)
    lottery_name = serializers.CharField(source='lottery.name', read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    claim_status_display = serializers.CharField(source='get_claim_status_display', read_only=True)
    masked_name = serializers.CharField(source='masked_customer_name', read_only=True)
    masked_phone = serializers.CharField(source='masked_phone_number', read_only=True)

    class Meta:
        model = Winner
        fields = [
            'id', 'lottery', 'lottery_name',
            'position', 'position_display',
            'ticket_number',
            'masked_name', 'masked_phone',
            'prize_name', 'prize_description', 'prize_value',
            'claim_status', 'claim_status_display',
            'created_at',
        ]


class StaffWinnerSerializer(serializers.ModelSerializer):
    """Complete serializer with full customer identification for authorized staff."""
    ticket_number = serializers.CharField(source='ticket.ticket_number', read_only=True)
    lottery_name = serializers.CharField(source='lottery.name', read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone_number', read_only=True)
    customer_telegram_id = serializers.IntegerField(source='customer.telegram_user_id', read_only=True)
    customer_telegram = serializers.CharField(source='customer.telegram_username', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.full_name', read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    claim_status_display = serializers.CharField(source='get_claim_status_display', read_only=True)

    class Meta:
        model = Winner
        fields = [
            'id', 'lottery', 'lottery_name',
            'position', 'position_display',
            'ticket', 'ticket_number',
            'customer', 'customer_name', 'customer_phone',
            'customer_telegram_id', 'customer_telegram',
            'prize_name', 'prize_description', 'prize_value',
            'claim_status', 'claim_status_display',
            'claimed_at', 'verified_by', 'verified_by_name',
            'payout_reference', 'admin_notes',
            'created_at', 'updated_at',
        ]


class WinnerClaimSerializer(serializers.Serializer):
    """Serializer for staff recording prize claim and disbursement."""
    payout_reference = serializers.CharField(max_length=100, required=True)
    admin_notes = serializers.CharField(required=False, allow_blank=True, default='')
