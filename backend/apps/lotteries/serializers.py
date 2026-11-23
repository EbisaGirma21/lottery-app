"""
Serializers for lottery, customer, and payment instruction models.
"""
from rest_framework import serializers

from apps.lotteries.models import Customer, Lottery, LotteryStatus, PaymentInstruction


class PaymentInstructionSerializer(serializers.ModelSerializer):
    """Inline serializer for payment instructions within a lottery."""
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True,
    )

    class Meta:
        model = PaymentInstruction
        fields = [
            'id', 'payment_method', 'payment_method_display',
            'account_name', 'account_number', 'additional_info',
            'is_active', 'display_order',
        ]


class LotteryListSerializer(serializers.ModelSerializer):
    """Compact lottery representation for list views."""
    created_by_name = serializers.CharField(
        source='created_by.full_name', read_only=True,
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True,
    )
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Lottery
        fields = [
            'id', 'name', 'slug', 'ticket_price', 'total_numbers',
            'start_date', 'closing_date', 'draw_date',
            'status', 'status_display',
            'created_by', 'created_by_name', 'created_at',
            'stats',
        ]

    def get_stats(self, obj) -> dict:
        from apps.lotteries.services import get_lottery_stats
        return get_lottery_stats(obj)


class LotteryDetailSerializer(serializers.ModelSerializer):
    """Full lottery representation with prizes and payment instructions."""
    created_by_name = serializers.CharField(
        source='created_by.full_name', read_only=True,
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True,
    )
    payment_instructions = PaymentInstructionSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Lottery
        fields = [
            'id', 'name', 'slug', 'description',
            'ticket_price', 'total_numbers',
            'start_date', 'closing_date', 'draw_date',
            'first_prize_name', 'first_prize_description', 'first_prize_value',
            'second_prize_name', 'second_prize_description', 'second_prize_value',
            'third_prize_name', 'third_prize_description', 'third_prize_value',
            'reservation_hours', 'max_tickets_per_customer',
            'status', 'status_display',
            'payment_instructions',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
            'stats',
        ]
        read_only_fields = ['id', 'slug', 'created_by', 'created_at', 'updated_at']

    def get_stats(self, obj) -> dict:
        from apps.lotteries.services import get_lottery_stats
        return get_lottery_stats(obj)


class LotteryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new lottery."""
    payment_instructions = PaymentInstructionSerializer(many=True, required=False)

    class Meta:
        model = Lottery
        fields = [
            'id', 'slug', 'status',
            'name', 'description',
            'ticket_price', 'total_numbers',
            'start_date', 'closing_date', 'draw_date',
            'first_prize_name', 'first_prize_description', 'first_prize_value',
            'second_prize_name', 'second_prize_description', 'second_prize_value',
            'third_prize_name', 'third_prize_description', 'third_prize_value',
            'reservation_hours', 'max_tickets_per_customer',
            'payment_instructions',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'status', 'created_at']

    def to_representation(self, instance):
        return LotteryDetailSerializer(instance, context=self.context).data

    def validate(self, attrs):
        start = attrs.get('start_date')
        closing = attrs.get('closing_date')
        draw = attrs.get('draw_date')

        if start and closing and start >= closing:
            raise serializers.ValidationError(
                {'closing_date': 'Closing date must be after start date.'}
            )
        if closing and draw and closing > draw:
            raise serializers.ValidationError(
                {'draw_date': 'Draw date must be on or after closing date.'}
            )
        if attrs.get('total_numbers', 0) < 3:
            raise serializers.ValidationError(
                {'total_numbers': 'A lottery must have at least 3 tickets for a draw.'}
            )
        return attrs

    def create(self, validated_data):
        payment_instructions_data = validated_data.pop('payment_instructions', [])
        validated_data['created_by'] = self.context['request'].user
        validated_data['status'] = LotteryStatus.DRAFT

        lottery = Lottery.objects.create(**validated_data)

        for pi_data in payment_instructions_data:
            PaymentInstruction.objects.create(lottery=lottery, **pi_data)

        # Generate tickets
        from apps.lotteries.services import generate_tickets_for_lottery
        generate_tickets_for_lottery(lottery)

        return lottery


class LotteryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an existing lottery."""

    class Meta:
        model = Lottery
        fields = [
            'name', 'description',
            'ticket_price', 'total_numbers',
            'start_date', 'closing_date', 'draw_date',
            'first_prize_name', 'first_prize_description', 'first_prize_value',
            'second_prize_name', 'second_prize_description', 'second_prize_value',
            'third_prize_name', 'third_prize_description', 'third_prize_value',
            'reservation_hours', 'max_tickets_per_customer',
        ]

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.status not in (LotteryStatus.DRAFT, LotteryStatus.PAUSED):
            # Restrict editable fields for non-draft lotteries
            restricted = {'ticket_price', 'total_numbers'}
            attempted = set(attrs.keys()) & restricted
            if attempted:
                raise serializers.ValidationError(
                    f'Cannot modify {", ".join(attempted)} when lottery is '
                    f'{instance.get_status_display()}.'
                )
        return attrs


class LotteryStatusSerializer(serializers.Serializer):
    """Serializer for changing lottery status."""
    status = serializers.ChoiceField(choices=LotteryStatus.choices)


# ── Customer Serializers ────────────────────────────────────────────

class CustomerSerializer(serializers.ModelSerializer):
    """Full customer representation."""
    status_display = serializers.CharField(
        source='get_status_display', read_only=True,
    )

    class Meta:
        model = Customer
        fields = [
            'id', 'full_name', 'phone_number',
            'telegram_user_id', 'telegram_username',
            'status', 'status_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerCreateSerializer(serializers.ModelSerializer):
    """Serializer for registering a new customer (via Telegram or admin)."""

    class Meta:
        model = Customer
        fields = [
            'full_name', 'phone_number',
            'telegram_user_id', 'telegram_username',
        ]

    def validate_phone_number(self, value):
        return Customer.normalize_phone(value)

    def validate_telegram_user_id(self, value):
        if Customer.objects.filter(telegram_user_id=value).exists():
            raise serializers.ValidationError(
                'A customer with this Telegram user ID already exists.'
            )
        return value
