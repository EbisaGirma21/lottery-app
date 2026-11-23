"""
Serializers for Draw models and execution.
"""
from rest_framework import serializers

from apps.draws.models import Draw
from apps.draws.services import execute_draw
from apps.lotteries.models import Lottery, LotteryStatus
from apps.winners.models import Winner


class DrawWinnerInlineSerializer(serializers.ModelSerializer):
    """Inline winner information for a draw."""
    ticket_number = serializers.CharField(source='ticket.ticket_number', read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone_number', read_only=True)
    customer_telegram = serializers.CharField(source='customer.telegram_username', read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    ticket = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()

    class Meta:
        model = Winner
        fields = [
            'id', 'position', 'position_display', 'ticket', 'ticket_number',
            'customer', 'customer_name', 'customer_phone', 'customer_telegram',
            'prize_name', 'prize_description', 'prize_value', 'claim_status',
        ]

    def get_ticket(self, obj):
        if obj.ticket:
            return {'id': str(obj.ticket.id), 'ticket_number': obj.ticket.ticket_number}
        return None

    def get_customer(self, obj):
        if obj.customer:
            return {
                'id': str(obj.customer.id),
                'full_name': obj.customer.full_name,
                'phone_number': obj.customer.phone_number,
                'telegram_username': obj.customer.telegram_username,
            }
        return None


class DrawDetailSerializer(serializers.ModelSerializer):
    """Detailed view of an executed lottery draw."""
    lottery_name = serializers.CharField(source='lottery.name', read_only=True)
    executed_by_name = serializers.CharField(source='executed_by.full_name', read_only=True)
    winners = DrawWinnerInlineSerializer(many=True, read_only=True)
    sold_tickets_pool_count = serializers.IntegerField(source='total_eligible_tickets', read_only=True)

    class Meta:
        model = Draw
        fields = [
            'id', 'lottery', 'lottery_name',
            'executed_by', 'executed_by_name',
            'total_eligible_tickets', 'sold_tickets_pool_count',
            'randomness_hash', 'notes', 'executed_at', 'winners',
        ]


class DrawExecuteSerializer(serializers.Serializer):
    """Request serializer to initiate and execute a lottery draw."""
    lottery_id = serializers.UUIDField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_lottery_id(self, value):
        try:
            lottery = Lottery.objects.get(id=value)
        except Lottery.DoesNotExist:
            raise serializers.ValidationError('Lottery not found.')

        if Draw.objects.filter(lottery=lottery).exists():
            raise serializers.ValidationError('A draw has already been conducted for this lottery.')

        if lottery.status != LotteryStatus.CLOSED:
            raise serializers.ValidationError(
                f'Lottery status is "{lottery.get_status_display()}". It must be Closed before conducting a draw.'
            )

        self.context['lottery'] = lottery
        return value

    def create(self, validated_data):
        lottery = self.context['lottery']
        user = self.context['request'].user
        notes = validated_data.get('notes', '')

        from apps.accounts.views import LoginView
        ip_address = LoginView._get_client_ip(self.context['request'])

        try:
            return execute_draw(
                lottery=lottery,
                executed_by=user,
                notes=notes,
                ip_address=ip_address,
            )
        except ValueError as e:
            raise serializers.ValidationError({'detail': str(e)})
