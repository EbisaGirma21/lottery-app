"""
Tests for the reservation system.

Covers:
- Atomic ticket reservation with locking
- Multiple ticket reservation
- Max ticket enforcement
- Status-based rejection
- Reservation cancellation
- Reservation expiration
- API endpoints
"""
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import SuperAdminFactory
from apps.lotteries.models import LotteryStatus
from apps.lotteries.services import generate_tickets_for_lottery
from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory
from apps.reservations.models import Reservation, ReservationStatus
from apps.reservations.services import (
    ReservationError,
    cancel_reservation,
    expire_stale_reservations,
    reserve_tickets,
)
from apps.tickets.models import Ticket, TicketStatus


@pytest.mark.django_db
class TestReserveTickets:
    """Tests for the reserve_tickets service."""

    def _create_open_lottery(self, total_numbers=100, **kwargs):
        lottery = LotteryFactory(
            total_numbers=total_numbers,
            status=LotteryStatus.OPEN,
            **kwargs,
        )
        generate_tickets_for_lottery(lottery)
        return lottery

    def test_reserve_single_ticket(self):
        lottery = self._create_open_lottery()
        customer = CustomerFactory()

        reservations = reserve_tickets(customer, lottery, ['001'])

        assert len(reservations) == 1
        assert reservations[0].status == ReservationStatus.ACTIVE
        assert reservations[0].ticket.ticket_number == '001'

        ticket = Ticket.objects.get(lottery=lottery, ticket_number='001')
        assert ticket.status == TicketStatus.RESERVED

    def test_reserve_multiple_tickets(self):
        """Scenario 6: Customer selects 3 tickets."""
        lottery = self._create_open_lottery()
        customer = CustomerFactory()

        reservations = reserve_tickets(customer, lottery, ['001', '002', '003'])

        assert len(reservations) == 3
        for r in reservations:
            assert r.status == ReservationStatus.ACTIVE

        # All tickets should be RESERVED
        for num in ['001', '002', '003']:
            ticket = Ticket.objects.get(lottery=lottery, ticket_number=num)
            assert ticket.status == TicketStatus.RESERVED

    def test_reserve_already_reserved_ticket_fails(self):
        """Scenario 7: Second customer cannot reserve same ticket."""
        lottery = self._create_open_lottery()
        customer_a = CustomerFactory()
        customer_b = CustomerFactory()

        # Customer A reserves first
        reserve_tickets(customer_a, lottery, ['001'])

        # Customer B should be rejected
        with pytest.raises(ReservationError, match='not available'):
            reserve_tickets(customer_b, lottery, ['001'])

        # Ticket should still belong to customer A's reservation
        ticket = Ticket.objects.get(lottery=lottery, ticket_number='001')
        assert ticket.status == TicketStatus.RESERVED

    def test_reserve_sold_ticket_fails(self):
        lottery = self._create_open_lottery()
        customer = CustomerFactory()

        # Mark ticket as SOLD
        ticket = Ticket.objects.get(lottery=lottery, ticket_number='001')
        ticket.status = TicketStatus.SOLD
        ticket.save()

        with pytest.raises(ReservationError, match='not available'):
            reserve_tickets(customer, lottery, ['001'])

    def test_reserve_nonexistent_ticket_fails(self):
        lottery = self._create_open_lottery(total_numbers=10)
        customer = CustomerFactory()

        with pytest.raises(ReservationError, match='does not exist'):
            reserve_tickets(customer, lottery, ['999'])

    def test_reserve_in_non_open_lottery_fails(self):
        """Only OPEN lotteries accept reservations."""
        for lottery_status in [LotteryStatus.DRAFT, LotteryStatus.PAUSED,
                               LotteryStatus.CLOSED, LotteryStatus.DRAWN]:
            lottery = LotteryFactory(status=lottery_status)
            generate_tickets_for_lottery(lottery)
            customer = CustomerFactory()

            with pytest.raises(ReservationError, match='not accepting'):
                reserve_tickets(customer, lottery, ['001'])

    def test_reserve_blocked_customer_fails(self):
        lottery = self._create_open_lottery()
        customer = CustomerFactory(status='blocked')

        with pytest.raises(ReservationError, match='blocked'):
            reserve_tickets(customer, lottery, ['001'])

    def test_max_tickets_per_customer_enforced(self):
        lottery = self._create_open_lottery(max_tickets_per_customer=2)
        customer = CustomerFactory()

        reserve_tickets(customer, lottery, ['001', '002'])

        with pytest.raises(ReservationError, match='only reserve 0 more'):
            reserve_tickets(customer, lottery, ['003'])

    def test_max_tickets_exceeded_in_single_request(self):
        lottery = self._create_open_lottery(max_tickets_per_customer=2)
        customer = CustomerFactory()

        with pytest.raises(ReservationError, match='only reserve 2 more'):
            reserve_tickets(customer, lottery, ['001', '002', '003'])

    def test_expiration_time_uses_lottery_config(self):
        lottery = self._create_open_lottery(reservation_hours=24)
        customer = CustomerFactory()

        reservations = reserve_tickets(customer, lottery, ['001'])
        r = reservations[0]

        expected = timezone.now() + timedelta(hours=24)
        # Allow 5 seconds tolerance
        assert abs((r.expires_at - expected).total_seconds()) < 5

    def test_atomic_rollback_on_partial_failure(self):
        """If one ticket in a multi-ticket request fails, ALL should be rolled back."""
        lottery = self._create_open_lottery()
        customer_a = CustomerFactory()
        customer_b = CustomerFactory()

        # Customer A reserves ticket 002
        reserve_tickets(customer_a, lottery, ['002'])

        # Customer B tries to reserve 001, 002, 003 — should fail on 002
        with pytest.raises(ReservationError):
            reserve_tickets(customer_b, lottery, ['001', '002', '003'])

        # Verify 001 was rolled back to AVAILABLE
        ticket_001 = Ticket.objects.get(lottery=lottery, ticket_number='001')
        assert ticket_001.status == TicketStatus.AVAILABLE

        # Verify 003 was also not reserved
        ticket_003 = Ticket.objects.get(lottery=lottery, ticket_number='003')
        assert ticket_003.status == TicketStatus.AVAILABLE


@pytest.mark.django_db
class TestCancelReservation:
    """Tests for reservation cancellation."""

    def test_cancel_active_reservation(self):
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        generate_tickets_for_lottery(lottery)
        customer = CustomerFactory()

        reservations = reserve_tickets(customer, lottery, ['001'])
        r = reservations[0]

        result = cancel_reservation(r)
        assert result.status == ReservationStatus.CANCELLED

        ticket = Ticket.objects.get(lottery=lottery, ticket_number='001')
        assert ticket.status == TicketStatus.AVAILABLE

    def test_cannot_cancel_non_active_reservation(self):
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        generate_tickets_for_lottery(lottery)
        customer = CustomerFactory()

        reservations = reserve_tickets(customer, lottery, ['001'])
        r = reservations[0]
        r.status = ReservationStatus.CONFIRMED
        r.save()

        with pytest.raises(ReservationError, match='Cannot cancel'):
            cancel_reservation(r)


@pytest.mark.django_db
class TestReservationExpiration:
    """Tests for automatic reservation expiration (Scenario 4 & 5)."""

    def test_expire_stale_reservations(self):
        """Scenario 4: Customer doesn't pay for 48 hours → ticket released."""
        lottery = LotteryFactory(status=LotteryStatus.OPEN, reservation_hours=48)
        generate_tickets_for_lottery(lottery)
        customer = CustomerFactory()

        reservations = reserve_tickets(customer, lottery, ['001'])
        r = reservations[0]

        # Simulate expiration by moving expires_at into the past
        r.expires_at = timezone.now() - timedelta(hours=1)
        r.save()

        count = expire_stale_reservations()
        assert count == 1

        r.refresh_from_db()
        assert r.status == ReservationStatus.EXPIRED

        ticket = Ticket.objects.get(lottery=lottery, ticket_number='001')
        assert ticket.status == TicketStatus.AVAILABLE

    def test_confirmed_reservation_not_expired(self):
        """Confirmed reservations must NOT be expired."""
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        generate_tickets_for_lottery(lottery)
        customer = CustomerFactory()

        reservations = reserve_tickets(customer, lottery, ['001'])
        r = reservations[0]
        r.status = ReservationStatus.CONFIRMED
        r.expires_at = timezone.now() - timedelta(hours=1)
        r.save()

        count = expire_stale_reservations()
        assert count == 0

        r.refresh_from_db()
        assert r.status == ReservationStatus.CONFIRMED

    def test_released_ticket_can_be_reserved_again(self):
        """Scenario 5: After expiration, another customer can reserve the ticket."""
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        generate_tickets_for_lottery(lottery)
        customer_a = CustomerFactory()
        customer_b = CustomerFactory()

        # Customer A reserves
        reservations = reserve_tickets(customer_a, lottery, ['001'])
        r = reservations[0]
        r.expires_at = timezone.now() - timedelta(hours=1)
        r.save()

        # Expire
        expire_stale_reservations()

        # Customer B can now reserve the same ticket
        new_reservations = reserve_tickets(customer_b, lottery, ['001'])
        assert len(new_reservations) == 1
        assert new_reservations[0].customer == customer_b

    def test_non_expired_reservation_not_touched(self):
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        generate_tickets_for_lottery(lottery)
        customer = CustomerFactory()

        reservations = reserve_tickets(customer, lottery, ['001'])
        # Default expiration is in the future

        count = expire_stale_reservations()
        assert count == 0

        reservations[0].refresh_from_db()
        assert reservations[0].status == ReservationStatus.ACTIVE


@pytest.mark.django_db
class TestReservationAPI:
    """Tests for reservation API endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.admin = SuperAdminFactory()

    def test_reserve_via_api(self):
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        generate_tickets_for_lottery(lottery)
        customer = CustomerFactory()

        url = reverse('reservation-reserve')
        response = self.client.post(url, {
            'lottery_id': str(lottery.id),
            'customer_id': str(customer.id),
            'ticket_numbers': ['001', '002'],
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.json()) == 2

    def test_reserve_unavailable_via_api(self):
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        generate_tickets_for_lottery(lottery)
        customer_a = CustomerFactory()
        customer_b = CustomerFactory()

        # Reserve ticket 001
        reserve_tickets(customer_a, lottery, ['001'])

        url = reverse('reservation-reserve')
        response = self.client.post(url, {
            'lottery_id': str(lottery.id),
            'customer_id': str(customer_b.id),
            'ticket_numbers': ['001'],
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_reservations_requires_auth(self):
        url = reverse('reservation-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_reservations_authenticated(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('reservation-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_cancel_via_api(self):
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        generate_tickets_for_lottery(lottery)
        customer = CustomerFactory()

        reservations = reserve_tickets(customer, lottery, ['001'])
        r = reservations[0]

        url = reverse('reservation-cancel', kwargs={'pk': r.id})
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'cancelled'
