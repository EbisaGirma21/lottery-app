"""
Serializers for payment submission, staff queue listing, detail view, approval, and rejection.
"""
from decimal import Decimal
from rest_framework import serializers

from apps.lotteries.models import Customer, Lottery
from apps.payments.models import Payment, PaymentMethod, PaymentStatus
from apps.payments.services import submit_payment
from apps.reservations.models import Reservation


class PaymentSubmitSerializer(serializers.Serializer):
    """
    Serializer for submitting a manual payment for reserved lottery tickets.
    Can be called by the Telegram bot or web/mobile clients.
    """
    lottery_id = serializers.UUIDField(required=True)
    reservation_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        required=True,
    )
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices, required=True)
    transaction_reference = serializers.CharField(max_length=100, required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'), required=True)
    payment_proof = serializers.FileField(required=False, allow_null=True)
    telegram_user_id = serializers.IntegerField(required=False, allow_null=True)
    customer_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        # 1. Identify Customer
        customer = None
        telegram_id = attrs.get('telegram_user_id')
        cust_id = attrs.get('customer_id')

        if telegram_id:
            try:
                customer = Customer.objects.get(telegram_user_id=telegram_id)
            except Customer.DoesNotExist:
                raise serializers.ValidationError({'telegram_user_id': 'Customer with this Telegram ID was not found.'})
        elif cust_id:
            try:
                customer = Customer.objects.get(id=cust_id)
            except Customer.DoesNotExist:
                raise serializers.ValidationError({'customer_id': 'Customer not found.'})
        else:
            raise serializers.ValidationError(
                'Either telegram_user_id or customer_id must be provided to identify the customer.'
            )

        attrs['customer'] = customer

        # 2. Identify Lottery
        try:
            lottery = Lottery.objects.get(id=attrs['lottery_id'])
        except Lottery.DoesNotExist:
            raise serializers.ValidationError({'lottery_id': 'Lottery not found.'})

        attrs['lottery'] = lottery
        return attrs

    def create(self, validated_data):
        customer = validated_data['customer']
        lottery = validated_data['lottery']
        reservation_ids = [str(rid) for rid in validated_data['reservation_ids']]
        payment_method = validated_data['payment_method']
        ref = validated_data['transaction_reference']
        amount = validated_data['amount']
        proof = validated_data.get('payment_proof')

        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        ip_address = None
        if request:
            from apps.accounts.views import LoginView
            ip_address = LoginView._get_client_ip(request)

        try:
            return submit_payment(
                customer=customer,
                lottery=lottery,
                reservation_ids=reservation_ids,
                payment_method=payment_method,
                transaction_reference=ref,
                amount=amount,
                payment_proof=proof,
                user=user,
                ip_address=ip_address,
            )
        except ValueError as e:
            raise serializers.ValidationError({'detail': str(e)})


class PaymentReservationInlineSerializer(serializers.ModelSerializer):
    """Inline view of reservations and ticket numbers in a payment."""
    ticket_number = serializers.CharField(source='ticket.ticket_number', read_only=True)

    class Meta:
        model = Reservation
        fields = ['id', 'ticket_id', 'ticket_number', 'status', 'reserved_at', 'expires_at']


class PaymentListSerializer(serializers.ModelSerializer):
    """Compact serializer for staff payment queue list."""
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone_number', read_only=True)
    customer_telegram = serializers.CharField(source='customer.telegram_username', read_only=True)
    lottery_name = serializers.CharField(source='lottery.name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    ticket_numbers = serializers.SerializerMethodField()
    ticket_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_reference', 'payment_method', 'payment_method_display',
            'amount', 'status', 'status_display',
            'is_auto_verified', 'auto_verification_status', 'verification_error',
            'receipt_reference_match',
            'customer', 'customer_name', 'customer_phone', 'customer_telegram',
            'lottery', 'lottery_name',
            'ticket_count', 'ticket_numbers',
            'payment_proof', 'submitted_at',
        ]

    def get_ticket_numbers(self, obj) -> list:
        return list(
            obj.reservations.select_related('ticket')
            .values_list('ticket__ticket_number', flat=True)
        )


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for staff payment review and detail page."""
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone_number', read_only=True)
    customer_telegram = serializers.CharField(source='customer.telegram_username', read_only=True)
    customer_telegram_id = serializers.IntegerField(source='customer.telegram_user_id', read_only=True)
    lottery_name = serializers.CharField(source='lottery.name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.full_name', read_only=True)
    reservations = PaymentReservationInlineSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_reference', 'payment_method', 'payment_method_display',
            'amount', 'status', 'status_display',
            'is_auto_verified', 'auto_verification_status', 'verification_data', 'verification_error',
            'customer', 'customer_name', 'customer_phone', 'customer_telegram', 'customer_telegram_id',
            'lottery', 'lottery_name',
            'reservations',
            'payment_proof',
            'rejection_reason', 'admin_notes',
            'receipt_extraction_data', 'receipt_reference_match',
            'reviewed_by', 'reviewed_by_name', 'reviewed_at',
            'submitted_at', 'updated_at',
        ]


class PaymentApproveSerializer(serializers.Serializer):
    """Staff action to approve a payment."""
    admin_notes = serializers.CharField(required=False, allow_blank=True, default='')


class PaymentRejectSerializer(serializers.Serializer):
    """Staff action to reject a payment."""
    rejection_reason = serializers.CharField(required=True, min_length=3)
    admin_notes = serializers.CharField(required=False, allow_blank=True, default='')
