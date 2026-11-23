"""
Tests for Telegram Bot HTML message formatters.
"""
from decimal import Decimal
from django.utils import timezone
import pytest

from apps.draws.tests.factories import DrawFactory
from apps.lotteries.tests.factories import (
    CustomerFactory,
    LotteryFactory,
    PaymentInstructionFactory,
    TicketFactory,
)
from apps.payments.models import PaymentMethod
from apps.payments.tests.factories import PaymentFactory
from apps.reservations.tests.factories import ReservationFactory
from apps.telegram_bot.formatters import (
    format_help,
    format_lottery_card,
    format_my_tickets,
    format_payment_submitted,
    format_reservation_confirmed,
    format_welcome,
    format_winners,
)
from apps.winners.tests.factories import WinnerFactory


@pytest.mark.django_db
class TestTelegramFormatters:
    """Tests for message formatting utilities."""

    def test_format_welcome(self):
        msg = format_welcome("Abebe", has_phone=False)
        assert "Welcome to the National Lottery Platform, Abebe!" in msg
        assert "share your phone number" in msg.lower()

        msg_with_phone = format_welcome("Kebede", has_phone=True)
        assert "Welcome to the National Lottery Platform, Kebede!" in msg_with_phone
        assert "share your phone number" not in msg_with_phone.lower()

    def test_format_help(self):
        msg = format_help()
        assert "/lotteries" in msg
        assert "/pay" in msg
        assert "Telebirr" in msg
        assert "Commercial Bank of Ethiopia" in msg
        assert "Manual Payment & Verification Security" in msg

    def test_format_lottery_card(self):
        lottery = LotteryFactory(
            name="Grand Holiday Draw",
            ticket_price=Decimal("100.00"),
            total_numbers=1000,
            first_prize_name="Luxury Car",
            first_prize_value=Decimal("2500000.00"),
        )
        msg = format_lottery_card(lottery)
        assert "Grand Holiday Draw" in msg
        assert "100.00 ETB" in msg
        assert "Luxury Car" in msg
        assert "2,500,000.00 ETB" in msg
        assert "1,000" in msg

    def test_format_reservation_confirmed(self):
        lottery = LotteryFactory(name="Mega Jackpot", ticket_price=Decimal("50.00"))
        pi = PaymentInstructionFactory(
            lottery=lottery,
            payment_method=PaymentMethod.TELEBIRR,
            account_name="Lottery Admin",
            account_number="0911000000",
        )
        res = ReservationFactory(lottery=lottery)
        msg = format_reservation_confirmed([res], payment_instructions=[pi])
        assert "Tickets Reserved Successfully!" in msg
        assert "Mega Jackpot" in msg
        assert "50.00 ETB" in msg
        assert "0911000000" in msg
        assert "/pay" in msg

    def test_format_payment_submitted(self):
        payment = PaymentFactory(
            transaction_reference="FT2409998877",
            amount=Decimal("150.00"),
            payment_method=PaymentMethod.TELEBIRR,
        )
        msg = format_payment_submitted(payment)
        assert "FT2409998877" in msg
        assert "150.00 ETB" in msg
        assert "Telebirr" in msg
        assert "Verification in Progress" in msg

    def test_format_my_tickets_empty(self):
        msg = format_my_tickets([], [], [])
        assert "You don't have any tickets or reservations yet" in msg

    def test_format_my_tickets_populated(self):
        customer = CustomerFactory()
        lottery = LotteryFactory(name="Addis Fortune")
        ticket = TicketFactory(lottery=lottery, customer=customer, ticket_number="042")
        payment = PaymentFactory(customer=customer, transaction_reference="REF123")
        res = ReservationFactory(customer=customer, lottery=lottery)

        msg = format_my_tickets([res], [payment], [ticket])
        assert "#042" in msg
        assert "REF123" in msg
        assert "Active Reservations" in msg
        assert "Confirmed Tickets" in msg

    def test_format_winners_empty(self):
        msg = format_winners([])
        assert "No lottery draws have been completed yet" in msg

    def test_format_winners_populated(self):
        draw = DrawFactory()
        w1 = WinnerFactory(draw=draw, lottery=draw.lottery, position=1, prize_value=Decimal("500000.00"))
        w2 = WinnerFactory(draw=draw, lottery=draw.lottery, position=2, prize_value=Decimal("250000.00"))
        w3 = WinnerFactory(draw=draw, lottery=draw.lottery, position=3, prize_value=Decimal("100000.00"))

        msg = format_winners([draw])
        assert draw.lottery.name in msg
        assert "1st Prize" in msg
        assert "500,000.00 ETB" in msg
