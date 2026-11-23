"""
Views for lottery and customer management.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrManager, IsSuperAdmin
from apps.accounts.views import LoginView
from apps.lotteries.models import Customer, Lottery, PaymentInstruction
from apps.lotteries.serializers import (
    CustomerCreateSerializer,
    CustomerSerializer,
    LotteryCreateSerializer,
    LotteryDetailSerializer,
    LotteryListSerializer,
    LotteryStatusSerializer,
    LotteryUpdateSerializer,
    PaymentInstructionSerializer,
)
from apps.lotteries.services import get_lottery_stats, transition_lottery_status


@extend_schema_view(
    list=extend_schema(tags=['Lotteries'], summary='List all lotteries'),
    retrieve=extend_schema(tags=['Lotteries'], summary='Get lottery details'),
    create=extend_schema(tags=['Lotteries'], summary='Create a new lottery'),
    update=extend_schema(tags=['Lotteries'], summary='Update a lottery'),
    partial_update=extend_schema(tags=['Lotteries'], summary='Partially update a lottery'),
)
class LotteryViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for lottery management.

    - Super Admin / Lottery Manager: Full CRUD access.
    - Other roles: Read-only access.

    Tickets are generated automatically when a lottery is created.
    """
    queryset = Lottery.objects.select_related('created_by').all()
    filterset_fields = ['status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'closing_date', 'draw_date', 'name']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy',
                           'change_status', 'update_payment_instructions'):
            return [IsAdminOrManager()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return LotteryCreateSerializer
        if self.action in ('update', 'partial_update'):
            return LotteryUpdateSerializer
        if self.action == 'retrieve':
            return LotteryDetailSerializer
        if self.action == 'change_status':
            return LotteryStatusSerializer
        return LotteryListSerializer

    def perform_create(self, serializer):
        lottery = serializer.save()

        from apps.audit_logs.services import log_action
        log_action(
            user=self.request.user,
            action='LOTTERY_CREATED',
            entity_type='Lottery',
            entity_id=str(lottery.id),
            new_value={'name': lottery.name, 'total_numbers': lottery.total_numbers},
            ip_address=LoginView._get_client_ip(self.request),
        )

    @extend_schema(
        tags=['Lotteries'],
        summary='Change lottery status',
        request=LotteryStatusSerializer,
        responses={200: LotteryDetailSerializer},
    )
    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        """Transition a lottery to a new status."""
        lottery = self.get_object()
        serializer = LotteryStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']

        try:
            lottery = transition_lottery_status(lottery, new_status, user=request.user)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            LotteryDetailSerializer(lottery).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=['Lotteries'],
        summary='Get lottery statistics',
        responses={200: dict},
    )
    @action(detail=True, methods=['get'], url_path='stats')
    def stats(self, request, pk=None):
        """Get real-time ticket statistics for a lottery."""
        lottery = self.get_object()
        return Response(get_lottery_stats(lottery))

    @extend_schema(
        tags=['Lotteries'],
        summary='Update payment instructions',
        request=PaymentInstructionSerializer(many=True),
        responses={200: PaymentInstructionSerializer(many=True)},
    )
    @action(detail=True, methods=['put'], url_path='payment-instructions')
    def update_payment_instructions(self, request, pk=None):
        """Replace all payment instructions for a lottery."""
        lottery = self.get_object()

        # Validate incoming data
        serializer = PaymentInstructionSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # Replace all instructions
        PaymentInstruction.objects.filter(lottery=lottery).delete()
        for pi_data in serializer.validated_data:
            PaymentInstruction.objects.create(lottery=lottery, **pi_data)

        instructions = PaymentInstruction.objects.filter(lottery=lottery)
        return Response(
            PaymentInstructionSerializer(instructions, many=True).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=['Lotteries'],
        summary='Get all user applications / participants for a lottery',
        responses={200: dict},
    )
    @action(detail=True, methods=['get'], url_path='participants')
    def participants(self, request, pk=None):
        """
        Return the list of users/customers who have applied (reserved, purchased,
        or submitted payments) for this lottery, along with ticket allocations,
        payment method (Telebirr/CBE), receipt screenshot proof, and status.
        """
        from apps.tickets.models import Ticket
        from apps.reservations.models import Reservation
        from apps.payments.models import Payment

        lottery = self.get_object()

        # Gather all tickets for this lottery that belong to a customer
        tickets = (
            Ticket.objects
            .filter(lottery=lottery, customer__isnull=False)
            .select_related('customer')
            .order_by('ticket_number')
        )

        # Gather active/recent reservations for this lottery
        reservations = (
            Reservation.objects
            .filter(lottery=lottery)
            .select_related('customer', 'ticket')
            .order_by('-reserved_at')
        )

        # Gather all payments submitted for this lottery
        payments = (
            Payment.objects
            .filter(lottery=lottery)
            .select_related('customer')
            .prefetch_related('reservations__ticket')
            .order_by('-submitted_at')
        )

        # Build participant dictionary keyed by customer ID
        participants_map = {}

        for t in tickets:
            c = t.customer
            cid = str(c.id)
            if cid not in participants_map:
                participants_map[cid] = {
                    'customer_id': cid,
                    'full_name': c.full_name,
                    'phone_number': c.phone_number,
                    'telegram_username': c.telegram_username,
                    'telegram_user_id': c.telegram_user_id,
                    'tickets_sold': [],
                    'tickets_reserved': [],
                    'payments': [],
                }
            if t.status in ('sold', 'winner'):
                participants_map[cid]['tickets_sold'].append(t.ticket_number)
            elif t.status == 'reserved':
                participants_map[cid]['tickets_reserved'].append(t.ticket_number)

        for r in reservations:
            c = r.customer
            cid = str(c.id)
            if cid not in participants_map:
                participants_map[cid] = {
                    'customer_id': cid,
                    'full_name': c.full_name,
                    'phone_number': c.phone_number,
                    'telegram_username': c.telegram_username,
                    'telegram_user_id': c.telegram_user_id,
                    'tickets_sold': [],
                    'tickets_reserved': [],
                    'payments': [],
                }
            if r.status == 'active' and r.ticket and r.ticket.ticket_number not in participants_map[cid]['tickets_reserved']:
                participants_map[cid]['tickets_reserved'].append(r.ticket.ticket_number)

        for p in payments:
            c = p.customer
            cid = str(c.id)
            if cid not in participants_map:
                participants_map[cid] = {
                    'customer_id': cid,
                    'full_name': c.full_name,
                    'phone_number': c.phone_number,
                    'telegram_username': c.telegram_username,
                    'telegram_user_id': c.telegram_user_id,
                    'tickets_sold': [],
                    'tickets_reserved': [],
                    'payments': [],
                }

            payment_data = {
                'id': str(p.id),
                'payment_method': p.payment_method,
                'payment_method_display': p.get_payment_method_display(),
                'transaction_reference': p.transaction_reference,
                'amount': str(p.amount),
                'status': p.status,
                'status_display': p.get_status_display(),
                'payment_proof': request.build_absolute_uri(p.payment_proof.url) if p.payment_proof else None,
                'submitted_at': p.submitted_at.isoformat() if p.submitted_at else None,
                'tickets': [r.ticket.ticket_number for r in p.reservations.all() if r.ticket],
            }
            participants_map[cid]['payments'].append(payment_data)

        # Convert to list and compute summary state for each participant
        result = []
        for pdata in participants_map.values():
            has_pending = any(p['status'] == 'pending' for p in pdata['payments'])
            has_approved = any(p['status'] == 'approved' for p in pdata['payments'])
            has_rejected = any(p['status'] == 'rejected' for p in pdata['payments'])

            if has_pending:
                pdata['application_status'] = 'pending_verification'
            elif has_approved or pdata['tickets_sold']:
                pdata['application_status'] = 'approved_paid'
            elif pdata['tickets_reserved']:
                pdata['application_status'] = 'reserved_unpaid'
            elif has_rejected:
                pdata['application_status'] = 'rejected'
            else:
                pdata['application_status'] = 'in_progress'

            pdata['total_tickets_count'] = len(pdata['tickets_sold']) + len(pdata['tickets_reserved'])
            result.append(pdata)

        # Sort: pending verifications first, then by total tickets
        result.sort(key=lambda x: (x['application_status'] != 'pending_verification', -x['total_tickets_count']))

        return Response({
            'lottery_id': str(lottery.id),
            'lottery_name': lottery.name,
            'total_participants': len(result),
            'participants': result,
        })

    def destroy(self, request, *args, **kwargs):
        """Only allow deletion of DRAFT lotteries."""
        lottery = self.get_object()
        if lottery.status != 'draft':
            return Response(
                {'detail': 'Only draft lotteries can be deleted. Consider cancelling instead.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(tags=['Customers'], summary='List all customers'),
    retrieve=extend_schema(tags=['Customers'], summary='Get customer details'),
    create=extend_schema(tags=['Customers'], summary='Register a new customer'),
    update=extend_schema(tags=['Customers'], summary='Update a customer'),
    partial_update=extend_schema(tags=['Customers'], summary='Partially update a customer'),
)
class CustomerViewSet(viewsets.ModelViewSet):
    """
    CRUD for customer management.

    Customers are primarily created through the Telegram bot.
    """
    queryset = Customer.objects.all()
    filterset_fields = ['status']
    search_fields = ['full_name', 'phone_number', 'telegram_username']
    ordering_fields = ['created_at', 'full_name']

    def get_permissions(self):
        if self.action in ('create',):
            # Allow unauthenticated creation (for Telegram bot registration)
            return []
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomerCreateSerializer
        return CustomerSerializer

    @extend_schema(
        tags=['Customers'],
        summary='Block a customer',
    )
    @action(detail=True, methods=['post'], url_path='block')
    def block(self, request, pk=None):
        """Block a customer."""
        customer = self.get_object()
        customer.status = 'blocked'
        customer.save(update_fields=['status', 'updated_at'])

        from apps.audit_logs.services import log_action
        log_action(
            user=request.user,
            action='CUSTOMER_BLOCKED',
            entity_type='Customer',
            entity_id=str(customer.id),
            new_value={'status': 'blocked'},
            ip_address=LoginView._get_client_ip(request),
        )

        return Response(CustomerSerializer(customer).data)

    @extend_schema(
        tags=['Customers'],
        summary='Unblock a customer',
    )
    @action(detail=True, methods=['post'], url_path='unblock')
    def unblock(self, request, pk=None):
        """Unblock a customer."""
        customer = self.get_object()
        customer.status = 'active'
        customer.save(update_fields=['status', 'updated_at'])

        from apps.audit_logs.services import log_action
        log_action(
            user=request.user,
            action='CUSTOMER_UNBLOCKED',
            entity_type='Customer',
            entity_id=str(customer.id),
            new_value={'status': 'active'},
            ip_address=LoginView._get_client_ip(request),
        )

        return Response(CustomerSerializer(customer).data)
