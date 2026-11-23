"""
Tests for notification dispatching services.
"""
from datetime import timedelta
from decimal import Decimal
import pytest
from django.utils import timezone

from apps.draws.tests.factories import DrawFactory
from apps.lotteries.models import LotteryStatus
from apps.lotteries.services import generate_tickets_for_lottery
from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory, TicketFactory
from apps.notifications.models import NotificationStatus, NotificationType
from apps.notifications.services import (
    dispatch_notification,
    notify_payment_approved,
    notify_payment_rejected,
    notify_reservation_created,
    notify_winner_announced,
)
from apps.payments.models import PaymentMethod, PaymentStatus
from apps.payments.tests.factories import PaymentFactory
from apps.reservations.models import Reservation
from apps.winners.models import WinningPosition
from apps.winners.tests.factories import WinnerFactory


@pytest.fixture
def customer():
    return CustomerFactory(full_name='Almaz Ayana', phone_number='+251911998877')


@pytest.fixture
def lottery():
    lottery = LotteryFactory(name='Holiday Special', status=LotteryStatus.OPEN, total_numbers=50)
    generate_tickets_for_lottery(lottery)
    return lottery


@pytest.mark.django_db
class TestNotificationServices:
    """Tests for notification service helper functions."""

    def test_dispatch_notification(self, customer):
        n = dispatch_notification(
            customer=customer,
            notification_type=NotificationType.RESERVATION_CREATED,
            title='Test Title',
            message='Test Content',
            metadata={'key': 'val'},
        )
        assert n.status == NotificationStatus.SENT
        assert n.customer == customer
        assert n.metadata['key'] == 'val'

    def test_notify_reservation_created(self, customer, lottery):
        expires = timezone.now() + timedelta(hours=48)
        n = notify_reservation_created(
            customer=customer,
            lottery=lottery,
            ticket_numbers=['001', '002'],
            expires_at=expires,
        )
        assert n.notification_type == NotificationType.RESERVATION_CREATED
        assert 'Holiday Special' in n.title
        assert '#001, #002' in n.message
        assert 'Almaz Ayana' in n.message

    def test_notify_payment_approved(self, customer, lottery):
        ticket = TicketFactory(lottery=lottery)
        res = Reservation.objects.create(
            customer=customer,
            lottery=lottery,
            ticket=ticket,
            expires_at=timezone.now() + timedelta(hours=48),
        )
        payment = PaymentFactory(
            customer=customer,
            lottery=lottery,
            status=PaymentStatus.APPROVED,
            transaction_reference='REF-APPROVED-100',
            reservations=[res],
        )

        n = notify_payment_approved(payment)
        assert n.notification_type == NotificationType.PAYMENT_APPROVED
        assert 'Payment Approved' in n.title
        assert 'REF-APPROVED-100' in n.message

    def test_notify_payment_rejected(self, customer, lottery):
        payment = PaymentFactory(
            customer=customer,
            lottery=lottery,
            status=PaymentStatus.REJECTED,
            transaction_reference='REF-REJECTED-200',
        )

        n = notify_payment_rejected(payment, reason='Invalid confirmation code.')
        assert n.notification_type == NotificationType.PAYMENT_REJECTED
        assert 'Payment Verification Failed' in n.title
        assert 'Invalid confirmation code.' in n.message

    def test_notify_winner_announced(self, customer, lottery):
        draw = DrawFactory(lottery=lottery)
        ticket = TicketFactory(lottery=lottery, ticket_number='042')
        winner = WinnerFactory(
            draw=draw,
            lottery=lottery,
            ticket=ticket,
            customer=customer,
            position=WinningPosition.FIRST,
            prize_name='Luxury Car',
            prize_value=Decimal('3500000.00'),
        )

        n = notify_winner_announced(winner)
        assert n.notification_type == NotificationType.WINNER_ANNOUNCED
        assert '1st Prize' in n.title
        assert 'Luxury Car' in n.message
        assert '#042' in n.message
