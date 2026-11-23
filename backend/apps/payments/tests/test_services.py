"""
Tests for payment services (submit_payment, approve_payment, reject_payment, get_payment_stats).
"""
from datetime import timedelta
from decimal import Decimal
import pytest
from django.utils import timezone

from apps.accounts.tests.factories import PaymentOfficerFactory, SuperAdminFactory
from apps.audit_logs.models import AuditLog
from apps.lotteries.models import CustomerStatus, LotteryStatus
from apps.lotteries.services import generate_tickets_for_lottery
from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory
from apps.payments.models import Payment, PaymentMethod, PaymentStatus
from apps.payments.services import (
    approve_payment,
    get_payment_stats,
    reject_payment,
    submit_payment,
)
from apps.payments.tests.factories import PaymentFactory
from apps.reservations.models import Reservation, ReservationStatus
from apps.reservations.services import reserve_tickets
from apps.tickets.models import Ticket, TicketStatus


@pytest.fixture
def open_lottery():
    lottery = LotteryFactory(
        status=LotteryStatus.OPEN,
        ticket_price=Decimal('50.00'),
        total_numbers=100,
    )
    generate_tickets_for_lottery(lottery)
    return lottery


@pytest.fixture
def customer():
    return CustomerFactory(status=CustomerStatus.ACTIVE)


@pytest.fixture
def payment_officer():
    return PaymentOfficerFactory()


@pytest.mark.django_db
class TestSubmitPayment:
    """Tests for submit_payment service."""

    def test_submit_payment_success(self, open_lottery, customer):
        reservations = reserve_tickets(customer, open_lottery, ['001'])

        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(r.id) for r in reservations],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='TXN-TELEBIRR-001',
            amount=Decimal('50.00'),
        )

        assert payment.status == PaymentStatus.PENDING
        assert payment.transaction_reference == 'TXN-TELEBIRR-001'
        assert payment.reservations.count() == 1
        assert payment.reservations.first().id == reservations[0].id

        # Verify audit log
        assert AuditLog.objects.filter(
            action='PAYMENT_SUBMITTED',
            entity_id=str(payment.id),
        ).exists()

    def test_submit_payment_multiple_reservations(self, open_lottery, customer):
        reservations = reserve_tickets(customer, open_lottery, ['002', '003', '004'])

        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(r.id) for r in reservations],
            payment_method=PaymentMethod.CBE,
            transaction_reference='CBE-REF-998877',
            amount=Decimal('150.00'),  # 3 * 50
        )

        assert payment.status == PaymentStatus.PENDING
        assert payment.reservations.count() == 3

    def test_submit_payment_blocked_customer_fails(self, open_lottery):
        blocked = CustomerFactory(status=CustomerStatus.BLOCKED)
        ticket = Ticket.objects.filter(lottery=open_lottery, status=TicketStatus.AVAILABLE).first()
        res = Reservation.objects.create(
            customer=blocked,
            lottery=open_lottery,
            ticket=ticket,
            expires_at=timezone.now() + timedelta(hours=48),
        )

        with pytest.raises(ValueError, match='blocked'):
            submit_payment(
                customer=blocked,
                lottery=open_lottery,
                reservation_ids=[str(res.id)],
                payment_method=PaymentMethod.TELEBIRR,
                transaction_reference='TXN-FAIL-01',
                amount=Decimal('50.00'),
            )

    def test_submit_payment_non_open_lottery_fails(self, customer):
        draft_lottery = LotteryFactory(status=LotteryStatus.DRAFT, ticket_price=Decimal('50.00'), total_numbers=50)
        generate_tickets_for_lottery(draft_lottery)
        ticket = Ticket.objects.filter(lottery=draft_lottery).first()
        res = Reservation.objects.create(
            customer=customer,
            lottery=draft_lottery,
            ticket=ticket,
            expires_at=timezone.now() + timedelta(hours=48),
        )

        with pytest.raises(ValueError, match='not open'):
            submit_payment(
                customer=customer,
                lottery=draft_lottery,
                reservation_ids=[str(res.id)],
                payment_method=PaymentMethod.TELEBIRR,
                transaction_reference='TXN-FAIL-02',
                amount=Decimal('50.00'),
            )

    def test_submit_payment_duplicate_reference_fails(self, open_lottery, customer):
        PaymentFactory(transaction_reference='DUPLICATE-REF-100')

        res = reserve_tickets(customer, open_lottery, ['005'])

        with pytest.raises(ValueError, match='already been submitted'):
            submit_payment(
                customer=customer,
                lottery=open_lottery,
                reservation_ids=[str(r.id) for r in res],
                payment_method=PaymentMethod.TELEBIRR,
                transaction_reference='duplicate-ref-100',  # case-insensitive check
                amount=Decimal('50.00'),
            )

    def test_submit_payment_empty_reservations_fails(self, open_lottery, customer):
        with pytest.raises(ValueError, match='At least one reservation'):
            submit_payment(
                customer=customer,
                lottery=open_lottery,
                reservation_ids=[],
                payment_method=PaymentMethod.TELEBIRR,
                transaction_reference='REF-EMPTY',
                amount=Decimal('50.00'),
            )

    def test_submit_payment_other_customer_reservation_fails(self, open_lottery, customer):
        other_customer = CustomerFactory()
        res = reserve_tickets(other_customer, open_lottery, ['006'])

        with pytest.raises(ValueError, match='invalid, expired, cancelled'):
            submit_payment(
                customer=customer,
                lottery=open_lottery,
                reservation_ids=[str(r.id) for r in res],
                payment_method=PaymentMethod.TELEBIRR,
                transaction_reference='REF-STEAL',
                amount=Decimal('50.00'),
            )

    def test_submit_payment_already_pending_fails(self, open_lottery, customer):
        res = reserve_tickets(customer, open_lottery, ['007'])

        # First payment
        submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='FIRST-PAY-1',
            amount=Decimal('50.00'),
        )

        # Second payment for the same reservation
        with pytest.raises(ValueError, match='already has a pending payment'):
            submit_payment(
                customer=customer,
                lottery=open_lottery,
                reservation_ids=[str(res[0].id)],
                payment_method=PaymentMethod.CBE,
                transaction_reference='SECOND-PAY-2',
                amount=Decimal('50.00'),
            )

    def test_submit_payment_insufficient_amount_fails(self, open_lottery, customer):
        res = reserve_tickets(customer, open_lottery, ['008', '009'])

        # 2 tickets * 50 = 100, submitting 50
        with pytest.raises(ValueError, match='less than the required total'):
            submit_payment(
                customer=customer,
                lottery=open_lottery,
                reservation_ids=[str(r.id) for r in res],
                payment_method=PaymentMethod.TELEBIRR,
                transaction_reference='LOW-AMOUNT-REF',
                amount=Decimal('50.00'),
            )


@pytest.mark.django_db
class TestApprovePayment:
    """Tests for approve_payment service."""

    def test_approve_payment_success(self, open_lottery, customer, payment_officer):
        reservations = reserve_tickets(customer, open_lottery, ['010', '011'])

        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(r.id) for r in reservations],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='APPROVE-TXN-101',
            amount=Decimal('100.00'),
        )

        approved = approve_payment(
            payment=payment,
            staff_user=payment_officer,
            admin_notes='Verified with Telebirr portal.',
        )

        # Verify Payment state
        assert approved.status == PaymentStatus.APPROVED
        assert approved.reviewed_by == payment_officer
        assert approved.reviewed_at is not None
        assert approved.admin_notes == 'Verified with Telebirr portal.'

        # Verify Reservations state -> CONFIRMED
        for r in reservations:
            r.refresh_from_db()
            assert r.status == ReservationStatus.CONFIRMED

        # Verify Tickets state -> SOLD
        for r in reservations:
            ticket = Ticket.objects.get(id=r.ticket_id)
            assert ticket.status == TicketStatus.SOLD
            assert ticket.customer == customer

        # Verify Audit Log
        assert AuditLog.objects.filter(
            action='PAYMENT_APPROVED',
            entity_id=str(approved.id),
        ).exists()

    def test_approve_already_approved_fails(self, open_lottery, customer, payment_officer):
        res = reserve_tickets(customer, open_lottery, ['012'])
        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='DOUBLE-APPROVE',
            amount=Decimal('50.00'),
        )

        approve_payment(payment, staff_user=payment_officer)

        with pytest.raises(ValueError, match='Only pending payments can be approved'):
            approve_payment(payment, staff_user=payment_officer)

    def test_approve_payment_reservation_expired_fails(self, open_lottery, customer, payment_officer):
        res = reserve_tickets(customer, open_lottery, ['013'])
        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='STALE-RES-APPROVE',
            amount=Decimal('50.00'),
        )

        # Stale reservation becomes cancelled/expired
        res[0].status = ReservationStatus.EXPIRED
        res[0].save()

        with pytest.raises(ValueError, match='no longer active'):
            approve_payment(payment, staff_user=payment_officer)


@pytest.mark.django_db
class TestRejectPayment:
    """Tests for reject_payment service."""

    def test_reject_payment_success(self, open_lottery, customer, payment_officer):
        reservations = reserve_tickets(customer, open_lottery, ['014', '015'])

        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(r.id) for r in reservations],
            payment_method=PaymentMethod.CBE,
            transaction_reference='REJECT-TXN-202',
            amount=Decimal('100.00'),
        )

        rejected = reject_payment(
            payment=payment,
            staff_user=payment_officer,
            rejection_reason='Transaction reference was not found in bank statement.',
            admin_notes='Checked statement at 10:00 AM.',
        )

        # Verify Payment state
        assert rejected.status == PaymentStatus.REJECTED
        assert rejected.rejection_reason == 'Transaction reference was not found in bank statement.'
        assert rejected.reviewed_by == payment_officer
        assert rejected.reviewed_at is not None

        # Verify Reservations state -> CANCELLED
        for r in reservations:
            r.refresh_from_db()
            assert r.status == ReservationStatus.CANCELLED

        # Verify Tickets state -> AVAILABLE (released for others)
        for r in reservations:
            ticket = Ticket.objects.get(id=r.ticket_id)
            assert ticket.status == TicketStatus.AVAILABLE
            assert ticket.customer is None

        # Verify Audit Log
        assert AuditLog.objects.filter(
            action='PAYMENT_REJECTED',
            entity_id=str(rejected.id),
        ).exists()

    def test_reject_empty_reason_fails(self, open_lottery, customer, payment_officer):
        res = reserve_tickets(customer, open_lottery, ['016'])
        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='EMPTY-REASON-REF',
            amount=Decimal('50.00'),
        )

        with pytest.raises(ValueError, match='rejection reason must be provided'):
            reject_payment(payment, staff_user=payment_officer, rejection_reason='   ')

    def test_reject_already_finalized_fails(self, open_lottery, customer, payment_officer):
        res = reserve_tickets(customer, open_lottery, ['017'])
        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='ALREADY-DONE',
            amount=Decimal('50.00'),
        )

        reject_payment(payment, staff_user=payment_officer, rejection_reason='Initial rejection')

        with pytest.raises(ValueError, match='Only pending payments can be rejected'):
            reject_payment(payment, staff_user=payment_officer, rejection_reason='Second attempt')


@pytest.mark.django_db
class TestPaymentStats:
    """Tests for get_payment_stats service."""

    def test_stats_aggregation(self, open_lottery, customer, payment_officer):
        PaymentFactory(lottery=open_lottery, status=PaymentStatus.PENDING, amount=Decimal('100.00'))
        PaymentFactory(lottery=open_lottery, status=PaymentStatus.PENDING, amount=Decimal('200.00'))
        PaymentFactory(lottery=open_lottery, status=PaymentStatus.APPROVED, amount=Decimal('500.00'))
        PaymentFactory(lottery=open_lottery, status=PaymentStatus.REJECTED, amount=Decimal('50.00'))

        stats = get_payment_stats(lottery=open_lottery)

        assert stats['total_payments'] == 4
        assert stats['pending_count'] == 2
        assert stats['approved_count'] == 1
        assert stats['rejected_count'] == 1
        assert Decimal(stats['approved_revenue']) == Decimal('500.00')
        assert Decimal(stats['pending_amount']) == Decimal('300.00')
