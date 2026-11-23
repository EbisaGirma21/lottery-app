"""
Tests for ticket generation and lottery services.
"""
import pytest

from apps.lotteries.models import LotteryStatus
from apps.lotteries.services import (
    generate_tickets_for_lottery,
    get_lottery_stats,
    transition_lottery_status,
)
from apps.lotteries.tests.factories import LotteryFactory
from apps.tickets.models import Ticket, TicketStatus


@pytest.mark.django_db
class TestTicketGeneration:
    """Tests for the ticket generation service."""

    def test_generate_100_tickets(self):
        lottery = LotteryFactory(total_numbers=100)
        count = generate_tickets_for_lottery(lottery)
        assert count == 100

        tickets = Ticket.objects.filter(lottery=lottery).order_by('ticket_number')
        assert tickets.first().ticket_number == '001'
        assert tickets.last().ticket_number == '100'

    def test_generate_1000_tickets(self):
        lottery = LotteryFactory(total_numbers=1000)
        count = generate_tickets_for_lottery(lottery)
        assert count == 1000

        first = Ticket.objects.filter(lottery=lottery).order_by('ticket_number').first()
        assert first.ticket_number == '0001'

    def test_all_tickets_start_available(self):
        lottery = LotteryFactory(total_numbers=50)
        generate_tickets_for_lottery(lottery)

        statuses = set(
            Ticket.objects.filter(lottery=lottery).values_list('status', flat=True)
        )
        assert statuses == {TicketStatus.AVAILABLE}

    def test_cannot_regenerate_tickets(self):
        lottery = LotteryFactory(total_numbers=10)
        generate_tickets_for_lottery(lottery)

        with pytest.raises(ValueError, match='already has'):
            generate_tickets_for_lottery(lottery)

    def test_ticket_numbers_are_unique_within_lottery(self):
        lottery = LotteryFactory(total_numbers=100)
        generate_tickets_for_lottery(lottery)

        numbers = list(
            Ticket.objects.filter(lottery=lottery).values_list('ticket_number', flat=True)
        )
        assert len(numbers) == len(set(numbers))

    def test_large_lottery_generation(self):
        """Test that large lotteries generate correctly (batched)."""
        lottery = LotteryFactory(total_numbers=6000)
        count = generate_tickets_for_lottery(lottery)
        assert count == 6000

        # Check width is 4 digits
        first = Ticket.objects.filter(lottery=lottery).order_by('ticket_number').first()
        assert first.ticket_number == '0001'


@pytest.mark.django_db
class TestLotteryStatusTransitions:
    """Tests for lottery status transition service."""

    def test_draft_to_open(self):
        lottery = LotteryFactory(status=LotteryStatus.DRAFT)
        result = transition_lottery_status(lottery, LotteryStatus.OPEN)
        assert result.status == LotteryStatus.OPEN

    def test_open_to_paused(self):
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        result = transition_lottery_status(lottery, LotteryStatus.PAUSED)
        assert result.status == LotteryStatus.PAUSED

    def test_paused_to_open(self):
        lottery = LotteryFactory(status=LotteryStatus.PAUSED)
        result = transition_lottery_status(lottery, LotteryStatus.OPEN)
        assert result.status == LotteryStatus.OPEN

    def test_open_to_closed(self):
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        result = transition_lottery_status(lottery, LotteryStatus.CLOSED)
        assert result.status == LotteryStatus.CLOSED

    def test_closed_to_drawn(self):
        lottery = LotteryFactory(status=LotteryStatus.CLOSED)
        result = transition_lottery_status(lottery, LotteryStatus.DRAWN)
        assert result.status == LotteryStatus.DRAWN

    def test_drawn_to_completed(self):
        lottery = LotteryFactory(status=LotteryStatus.DRAWN)
        result = transition_lottery_status(lottery, LotteryStatus.COMPLETED)
        assert result.status == LotteryStatus.COMPLETED

    def test_invalid_transition_raises(self):
        lottery = LotteryFactory(status=LotteryStatus.DRAFT)
        with pytest.raises(ValueError, match='Cannot transition'):
            transition_lottery_status(lottery, LotteryStatus.DRAWN)

    def test_completed_cannot_transition(self):
        lottery = LotteryFactory(status=LotteryStatus.COMPLETED)
        with pytest.raises(ValueError):
            transition_lottery_status(lottery, LotteryStatus.OPEN)


@pytest.mark.django_db
class TestLotteryStats:
    """Tests for the lottery statistics service."""

    def test_stats_for_empty_lottery(self):
        lottery = LotteryFactory(total_numbers=100)
        generate_tickets_for_lottery(lottery)

        stats = get_lottery_stats(lottery)
        assert stats['total'] == 100
        assert stats['available'] == 100
        assert stats['reserved'] == 0
        assert stats['sold'] == 0
        assert stats['sold_percentage'] == 0

    def test_stats_with_mixed_statuses(self):
        lottery = LotteryFactory(total_numbers=10)
        generate_tickets_for_lottery(lottery)

        tickets = list(Ticket.objects.filter(lottery=lottery).order_by('ticket_number'))
        tickets[0].status = TicketStatus.RESERVED
        tickets[0].save()
        tickets[1].status = TicketStatus.SOLD
        tickets[1].save()
        tickets[2].status = TicketStatus.SOLD
        tickets[2].save()

        stats = get_lottery_stats(lottery)
        assert stats['total'] == 10
        assert stats['available'] == 7
        assert stats['reserved'] == 1
        assert stats['sold'] == 2
        assert stats['sold_percentage'] == 20.0
