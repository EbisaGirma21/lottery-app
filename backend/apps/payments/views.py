"""
Views for payment submission, staff review queue, approval, and rejection.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsPaymentVerifier
from apps.accounts.views import LoginView
from apps.lotteries.models import Lottery
from apps.payments.models import Payment
from apps.payments.serializers import (
    PaymentApproveSerializer,
    PaymentDetailSerializer,
    PaymentListSerializer,
    PaymentRejectSerializer,
    PaymentSubmitSerializer,
)
from apps.payments.services import approve_payment, get_payment_stats, reject_payment, verify_payment_now


@extend_schema_view(
    list=extend_schema(tags=['Payments'], summary='List payments in verification queue'),
    retrieve=extend_schema(tags=['Payments'], summary='Get payment details'),
)
class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Staff review queue for manual payments and submission endpoint for customers/bots.

    - Staff (Payment Officer, Manager, Admin): View queue, approve, reject payments, verify with bank API.
    - Public / Bot: Submit payments via POST /api/payments/submit/
    """
    queryset = (
        Payment.objects
        .select_related('customer', 'lottery', 'reviewed_by')
        .prefetch_related('reservations__ticket')
        .all()
    )
    filterset_fields = ['status', 'payment_method', 'lottery', 'is_auto_verified']
    search_fields = [
        'transaction_reference',
        'customer__full_name',
        'customer__phone_number',
        'customer__telegram_username',
    ]
    ordering_fields = ['submitted_at', 'amount', 'status']
    ordering = ['-submitted_at']

    def get_permissions(self):
        if self.action in ('submit', 'my_payments'):
            return [AllowAny()]
        if self.action in ('approve', 'reject', 'verify_now'):
            return [IsPaymentVerifier()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaymentDetailSerializer
        if self.action == 'submit':
            return PaymentSubmitSerializer
        if self.action == 'approve':
            return PaymentApproveSerializer
        if self.action == 'reject':
            return PaymentRejectSerializer
        return PaymentListSerializer

    @extend_schema(
        tags=['Payments'],
        summary='Submit manual payment',
        request=PaymentSubmitSerializer,
        responses={201: PaymentDetailSerializer},
    )
    @action(detail=False, methods=['post'], url_path='submit')
    def submit(self, request):
        """
        Submit a manual payment transaction reference (and optional screenshot proof)
        for one or more active reservations.
        """
        serializer = PaymentSubmitSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response(
            PaymentDetailSerializer(payment, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=['Payments'],
        summary='Approve pending payment',
        request=PaymentApproveSerializer,
        responses={200: PaymentDetailSerializer},
    )
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        Approve a pending payment after staff manual verification.
        Atomically converts reserved tickets to SOLD and confirms reservations.
        """
        payment = self.get_object()
        serializer = PaymentApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        admin_notes = serializer.validated_data.get('admin_notes', '')
        ip_address = LoginView._get_client_ip(request)

        try:
            payment = approve_payment(
                payment=payment,
                staff_user=request.user,
                admin_notes=admin_notes,
                ip_address=ip_address,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            PaymentDetailSerializer(payment, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=['Payments'],
        summary='Reject pending payment',
        request=PaymentRejectSerializer,
        responses={200: PaymentDetailSerializer},
    )
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """
        Reject a pending payment with an explanation reason.
        Atomically releases reserved tickets back to AVAILABLE and cancels reservations.
        """
        payment = self.get_object()
        serializer = PaymentRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rejection_reason = serializer.validated_data['rejection_reason']
        admin_notes = serializer.validated_data.get('admin_notes', '')
        ip_address = LoginView._get_client_ip(request)

        try:
            payment = reject_payment(
                payment=payment,
                staff_user=request.user,
                rejection_reason=rejection_reason,
                admin_notes=admin_notes,
                ip_address=ip_address,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            PaymentDetailSerializer(payment, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=['Payments'],
        summary='Trigger real-time bank ledger verification',
        responses={200: PaymentDetailSerializer},
    )
    @action(detail=True, methods=['post'], url_path='verify-now')
    def verify_now(self, request, pk=None):
        """
        Query official bank/wallet ledger via REST API for this pending payment.
        If confirmed, automatically marks payment as approved and confirms tickets.
        """
        payment = self.get_object()
        ip_address = LoginView._get_client_ip(request)

        try:
            payment = verify_payment_now(
                payment=payment,
                staff_user=request.user,
                ip_address=ip_address,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            PaymentDetailSerializer(payment, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=['Payments'],
        summary='Get payment statistics',
        responses={200: dict},
    )
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Get aggregate payment statistics (pending, approved, rejected counts and amounts)."""
        lottery_id = request.query_params.get('lottery')
        lottery = None
        if lottery_id:
            try:
                lottery = Lottery.objects.get(id=lottery_id)
            except Lottery.DoesNotExist:
                return Response({'detail': 'Lottery not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(get_payment_stats(lottery=lottery))

    @extend_schema(
        tags=['Payments'],
        summary='Customer payment history',
        responses={200: PaymentListSerializer(many=True)},
    )
    @action(detail=False, methods=['get'], url_path='my-payments')
    def my_payments(self, request):
        """
        Retrieve payments for a customer by telegram_user_id or customer UUID.
        Useful for Telegram bot status checks.
        """
        telegram_id = request.query_params.get('telegram_user_id')
        customer_id = request.query_params.get('customer_id')

        if not telegram_id and not customer_id:
            return Response(
                {'detail': 'Provide either telegram_user_id or customer_id query parameter.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset()
        if telegram_id:
            qs = qs.filter(customer__telegram_user_id=telegram_id)
        elif customer_id:
            qs = qs.filter(customer_id=customer_id)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = PaymentListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = PaymentListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)
