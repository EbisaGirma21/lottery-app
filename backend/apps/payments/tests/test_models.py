"""
Tests for Payment models.
"""
from datetime import timedelta
from decimal import Decimal
import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.lotteries.models import LotteryStatus
from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory, TicketFactory
from apps.payments.models import Payment, PaymentMethod, PaymentStatus
from apps.payments.tests.factories import PaymentFactory
from apps.reservations.models import Reservation, ReservationStatus


@pytest.mark.django_db
class TestPaymentModel:
    """Tests for Payment model fields, constraints, and methods."""

    def test_create_payment(self):
        payment = PaymentFactory()
        assert payment.id is not None
        assert payment.status == PaymentStatus.PENDING
        assert payment.submitted_at is not None
        assert payment.reviewed_by is None
        assert payment.reviewed_at is None
        assert payment.rejection_reason == ''
        assert payment.admin_notes == ''

    def test_transaction_reference_uniqueness(self):
        PaymentFactory(transaction_reference='REF-UNIQUE-123')
        with pytest.raises(IntegrityError):
            PaymentFactory(transaction_reference='REF-UNIQUE-123')

    def test_transaction_reference_whitespace_stripped(self):
        payment = PaymentFactory(transaction_reference='  REF-SPACES-999  ')
        assert payment.transaction_reference == 'REF-SPACES-999'

    def test_payment_methods(self):
        expected_methods = {'telebirr', 'cbe', 'cbe_birr', 'awash', 'boa', 'other'}
        actual_methods = {choice[0] for choice in PaymentMethod.choices}
        assert expected_methods == actual_methods

    def test_payment_statuses(self):
        expected_statuses = {'pending', 'approved', 'rejected'}
        actual_statuses = {choice[0] for choice in PaymentStatus.choices}
        assert expected_statuses == actual_statuses

    def test_ticket_count_property(self):
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        customer = CustomerFactory()
        ticket1 = TicketFactory(lottery=lottery)
        ticket2 = TicketFactory(lottery=lottery)
        expires = timezone.now() + timedelta(hours=48)

        r1 = Reservation.objects.create(customer=customer, lottery=lottery, ticket=ticket1, expires_at=expires)
        r2 = Reservation.objects.create(customer=customer, lottery=lottery, ticket=ticket2, expires_at=expires)

        payment = PaymentFactory(customer=customer, lottery=lottery, reservations=[r1, r2])
        assert payment.ticket_count == 2

    def test_str_representation(self):
        payment = PaymentFactory(transaction_reference='TXN123456')
        str_val = str(payment)
        assert 'TXN123456' in str_val
        assert 'Pending Verification' in str_val
