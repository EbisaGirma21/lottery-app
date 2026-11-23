"""
Tests for execute_draw service.
"""
from decimal import Decimal
import pytest

from apps.accounts.tests.factories import DrawOfficerFactory
from apps.audit_logs.models import AuditLog
from apps.draws.models import Draw
from apps.draws.services import execute_draw
from apps.lotteries.models import CustomerStatus, LotteryStatus
from apps.lotteries.services import generate_tickets_for_lottery
from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory
from apps.tickets.models import Ticket, TicketStatus
from apps.winners.models import Winner, WinningPosition


@pytest.fixture
def draw_officer():
    return DrawOfficerFactory()


@pytest.fixture
def closed_lottery():
    lottery = LotteryFactory(
        status=LotteryStatus.CLOSED,
        total_numbers=100,
        ticket_price=Decimal('50.00'),
        first_prize_name='Car',
        first_prize_description='Brand new Toyota',
        first_prize_value=Decimal('2000000.00'),
        second_prize_name='Motorcycle',
        second_prize_description='Bajaj Pulsar',
        second_prize_value=Decimal('300000.00'),
        third_prize_name='Smartphone',
        third_prize_description='Samsung Galaxy',
        third_prize_value=Decimal('50000.00'),
    )
    generate_tickets_for_lottery(lottery)
    return lottery


@pytest.fixture
def customer():
    return CustomerFactory(status=CustomerStatus.ACTIVE)


@pytest.mark.django_db
class TestExecuteDraw:
    """Tests for execute_draw business logic."""

    def test_execute_draw_success(self, closed_lottery, draw_officer, customer):
        # Mark 10 tickets as SOLD
        sold_tickets = Ticket.objects.filter(lottery=closed_lottery)[:10]
        for t in sold_tickets:
            t.status = TicketStatus.SOLD
            t.customer = customer
            t.save()

        draw = execute_draw(
            lottery=closed_lottery,
            executed_by=draw_officer,
            notes='Audited by National Lottery Board observer.',
        )

        # 1. Draw record verification
        assert draw.id is not None
        assert draw.lottery == closed_lottery
        assert draw.executed_by == draw_officer
        assert draw.total_eligible_tickets == 10
        assert len(draw.randomness_hash) == 64
        assert draw.notes == 'Audited by National Lottery Board observer.'

        # 2. Winners verification (exactly 3)
        winners = list(Winner.objects.filter(draw=draw).order_by('position'))
        assert len(winners) == 3

        w1, w2, w3 = winners[0], winners[1], winners[2]
        assert w1.position == WinningPosition.FIRST
        assert w1.prize_name == 'Car'
        assert w1.prize_value == Decimal('2000000.00')
        assert w1.ticket.status == TicketStatus.WINNER

        assert w2.position == WinningPosition.SECOND
        assert w2.prize_name == 'Motorcycle'
        assert w2.prize_value == Decimal('300000.00')
        assert w2.ticket.status == TicketStatus.WINNER

        assert w3.position == WinningPosition.THIRD
        assert w3.prize_name == 'Smartphone'
        assert w3.prize_value == Decimal('50000.00')
        assert w3.ticket.status == TicketStatus.WINNER

        # 3. Winning tickets must be distinct
        winner_ticket_ids = {w1.ticket_id, w2.ticket_id, w3.ticket_id}
        assert len(winner_ticket_ids) == 3

        # 4. Remaining sold tickets stay SOLD
        remaining_sold = Ticket.objects.filter(lottery=closed_lottery, status=TicketStatus.SOLD).count()
        assert remaining_sold == 7

        # 5. Lottery status transitioned to DRAWN
        closed_lottery.refresh_from_db()
        assert closed_lottery.status == LotteryStatus.DRAWN

        # 6. Audit Log verification
        assert AuditLog.objects.filter(
            action='DRAW_EXECUTED',
            entity_id=str(draw.id),
        ).exists()

    def test_execute_draw_non_closed_lottery_fails(self, draw_officer, customer):
        open_lottery = LotteryFactory(status=LotteryStatus.OPEN, total_numbers=50)
        generate_tickets_for_lottery(open_lottery)
        for t in Ticket.objects.filter(lottery=open_lottery)[:5]:
            t.status = TicketStatus.SOLD
            t.customer = customer
            t.save()

        with pytest.raises(ValueError, match='must be Closed before conducting a draw'):
            execute_draw(lottery=open_lottery, executed_by=draw_officer)

    def test_execute_draw_fewer_than_3_tickets_fails(self, closed_lottery, draw_officer, customer):
        # Only 2 tickets sold
        for t in Ticket.objects.filter(lottery=closed_lottery)[:2]:
            t.status = TicketStatus.SOLD
            t.customer = customer
            t.save()

        with pytest.raises(ValueError, match='At least 3 sold tickets are required'):
            execute_draw(lottery=closed_lottery, executed_by=draw_officer)

    def test_cannot_execute_draw_twice(self, closed_lottery, draw_officer, customer):
        for t in Ticket.objects.filter(lottery=closed_lottery)[:5]:
            t.status = TicketStatus.SOLD
            t.customer = customer
            t.save()

        execute_draw(lottery=closed_lottery, executed_by=draw_officer)

        with pytest.raises(ValueError, match='already been executed'):
            execute_draw(lottery=closed_lottery, executed_by=draw_officer)
