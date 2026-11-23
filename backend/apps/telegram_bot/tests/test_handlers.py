"""
Tests for Telegram Bot business sync services and handler helpers.
"""
from decimal import Decimal
import pytest
from unittest.mock import MagicMock

from apps.draws.models import Draw
from apps.draws.tests.factories import DrawFactory
from apps.lotteries.models import Customer, CustomerStatus, LotteryStatus
from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory, TicketFactory
from apps.payments.models import PaymentMethod, PaymentStatus
from apps.payments.tests.factories import PaymentFactory
from apps.reservations.models import ReservationStatus
from apps.reservations.services import ReservationError
from apps.reservations.tests.factories import ReservationFactory
from apps.telegram_bot.handlers.lotteries import (
    sync_execute_reservation,
    sync_get_available_tickets_page,
    sync_get_lottery,
    sync_get_open_lotteries,
    sync_quick_pick_tickets,
)
from apps.telegram_bot.handlers.my_tickets import sync_get_customer_portfolio
from apps.telegram_bot.handlers.payments import (
    sync_get_unpaid_reservations,
    sync_is_reference_duplicate,
    sync_process_payment_submission,
)
from apps.telegram_bot.handlers.start import (
    sync_get_or_create_customer,
    sync_save_customer_phone,
)
from apps.telegram_bot.handlers.winners import sync_get_recent_draws
from apps.tickets.models import TicketStatus
from apps.winners.tests.factories import WinnerFactory


@pytest.mark.django_db
class TestTelegramHandlerHelpers:
    """Tests for Telegram bot database sync helpers."""

    def test_get_or_create_customer_new(self):
        tg_user = MagicMock()
        tg_user.id = 12345678
        tg_user.first_name = "Solomon"
        tg_user.last_name = "Tekle"
        tg_user.username = "solomon_t"

        customer = sync_get_or_create_customer(tg_user)
        assert customer.telegram_user_id == 12345678
        assert customer.full_name == "Solomon Tekle"
        assert customer.telegram_username == "solomon_t"

    def test_get_or_create_customer_update_existing(self):
        customer = CustomerFactory(
            telegram_user_id=888888,
            full_name="Old Name",
            telegram_username="old_user",
        )
        tg_user = MagicMock()
        tg_user.id = 888888
        tg_user.first_name = "New"
        tg_user.last_name = "Name"
        tg_user.username = "new_user"

        updated_customer = sync_get_or_create_customer(tg_user)
        assert updated_customer.id == customer.id
        assert updated_customer.full_name == "New Name"
        assert updated_customer.telegram_username == "new_user"

    def test_save_customer_phone(self):
        customer = CustomerFactory(telegram_user_id=999999, phone_number="")
        success = sync_save_customer_phone(999999, "+251911223344")
        assert success is True
        customer.refresh_from_db()
        assert customer.phone_number == "+251911223344"

    def test_get_open_lotteries(self):
        LotteryFactory(name="Open 1", status=LotteryStatus.OPEN)
        LotteryFactory(name="Draft 1", status=LotteryStatus.DRAFT)
        LotteryFactory(name="Closed 1", status=LotteryStatus.CLOSED)

        open_list = sync_get_open_lotteries()
        assert len(open_list) == 1
        assert open_list[0].name == "Open 1"

    def test_get_lottery_by_id(self):
        lottery = LotteryFactory()
        found = sync_get_lottery(str(lottery.id))
        assert found.id == lottery.id

    def test_get_available_tickets_page(self):
        lottery = LotteryFactory(total_numbers=20)
        tickets = [TicketFactory(lottery=lottery, ticket_number=str(i).zfill(2)) for i in range(1, 15)]
        # Mark one as sold
        tickets[0].status = TicketStatus.SOLD
        tickets[0].save()

        page_tickets, current_page, total_pages = sync_get_available_tickets_page(
            str(lottery.id), page_number=1, page_size=5
        )
        assert len(page_tickets) == 5
        assert current_page == 1
        assert total_pages == 3

    def test_quick_pick_tickets(self):
        lottery = LotteryFactory()
        for i in range(10):
            TicketFactory(lottery=lottery, ticket_number=str(i).zfill(3), status=TicketStatus.AVAILABLE)

        picked = sync_quick_pick_tickets(str(lottery.id), count=3)
        assert len(picked) == 3

    def test_execute_reservation_success(self):
        customer = CustomerFactory(telegram_user_id=112233, status=CustomerStatus.ACTIVE)
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        t1 = TicketFactory(lottery=lottery, ticket_number="001", status=TicketStatus.AVAILABLE)
        t2 = TicketFactory(lottery=lottery, ticket_number="002", status=TicketStatus.AVAILABLE)

        reservations, instructions = sync_execute_reservation(
            telegram_user_id=customer.telegram_user_id,
            lottery_id=str(lottery.id),
            ticket_numbers=["001", "002"],
        )
        assert len(reservations) == 2
        t1.refresh_from_db()
        t2.refresh_from_db()
        assert t1.status == TicketStatus.RESERVED
        assert t2.status == TicketStatus.RESERVED

    def test_execute_reservation_blocked_customer(self):
        customer = CustomerFactory(telegram_user_id=445566, status=CustomerStatus.BLOCKED)
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        TicketFactory(lottery=lottery, ticket_number="001", status=TicketStatus.AVAILABLE)

        with pytest.raises(ReservationError):
            sync_execute_reservation(
                telegram_user_id=customer.telegram_user_id,
                lottery_id=str(lottery.id),
                ticket_numbers=["001"],
            )

    def test_get_unpaid_reservations(self):
        customer = CustomerFactory(telegram_user_id=556677)
        lottery = LotteryFactory()
        r1 = ReservationFactory(customer=customer, lottery=lottery, status=ReservationStatus.ACTIVE)
        r2 = ReservationFactory(customer=customer, lottery=lottery, status=ReservationStatus.EXPIRED)

        cust, active_res = sync_get_unpaid_reservations(customer.telegram_user_id)
        assert cust.id == customer.id
        assert len(active_res) == 1
        assert active_res[0].id == r1.id

    def test_is_reference_duplicate(self):
        PaymentFactory(transaction_reference="REF_UNIQUE_123")
        assert sync_is_reference_duplicate("REF_UNIQUE_123") is True
        assert sync_is_reference_duplicate("ref_unique_123") is True
        assert sync_is_reference_duplicate("SOME_OTHER_REF") is False

    def test_process_payment_submission(self):
        customer = CustomerFactory(telegram_user_id=778899, status=CustomerStatus.ACTIVE)
        lottery = LotteryFactory(status=LotteryStatus.OPEN, ticket_price=Decimal("100.00"))
        ticket = TicketFactory(lottery=lottery, status=TicketStatus.RESERVED)
        reservation = ReservationFactory(customer=customer, lottery=lottery, ticket=ticket, status=ReservationStatus.ACTIVE)

        payment = sync_process_payment_submission(
            telegram_user_id=customer.telegram_user_id,
            lottery_id=str(lottery.id),
            reservation_ids=[str(reservation.id)],
            payment_method=PaymentMethod.TELEBIRR,
            reference="TX_TG_TEST_999",
            amount=Decimal("100.00"),
        )
        assert payment.status == PaymentStatus.PENDING
        assert payment.transaction_reference == "TX_TG_TEST_999"
        assert payment.customer.id == customer.id

    def test_get_customer_portfolio(self):
        customer = CustomerFactory(telegram_user_id=334455)
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        TicketFactory(customer=customer, lottery=lottery, status=TicketStatus.SOLD)
        ReservationFactory(customer=customer, lottery=lottery, status=ReservationStatus.ACTIVE)
        PaymentFactory(customer=customer, lottery=lottery, status=PaymentStatus.PENDING)

        res, pends, solds = sync_get_customer_portfolio(customer.telegram_user_id)
        assert len(res) == 1
        assert len(pends) == 1
        assert len(solds) == 1

    def test_get_customer_portfolio_excludes_drawn_older_than_48_hours(self):
        from datetime import timedelta
        from django.utils import timezone
        customer = CustomerFactory(telegram_user_id=445566)
        old_drawn_lottery = LotteryFactory(status=LotteryStatus.DRAWN)
        # Simulate draw conducted 50 hours ago
        draw = DrawFactory(lottery=old_drawn_lottery)
        Draw.objects.filter(id=draw.id).update(executed_at=timezone.now() - timedelta(hours=50))

        TicketFactory(customer=customer, lottery=old_drawn_lottery, status=TicketStatus.SOLD)

        _, _, solds = sync_get_customer_portfolio(customer.telegram_user_id)
        assert len(solds) == 0

    def test_get_customer_portfolio_includes_drawn_within_48_hours(self):
        from datetime import timedelta
        from django.utils import timezone
        customer = CustomerFactory(telegram_user_id=556677)
        recent_drawn_lottery = LotteryFactory(status=LotteryStatus.DRAWN)
        # Simulate draw conducted 2 hours ago
        draw = DrawFactory(lottery=recent_drawn_lottery)
        Draw.objects.filter(id=draw.id).update(executed_at=timezone.now() - timedelta(hours=2))

        TicketFactory(customer=customer, lottery=recent_drawn_lottery, status=TicketStatus.SOLD)

        _, _, solds = sync_get_customer_portfolio(customer.telegram_user_id)
        assert len(solds) == 1

    def test_get_recent_draws(self):
        draw = DrawFactory()
        WinnerFactory(draw=draw, lottery=draw.lottery, position=1)
        draws = sync_get_recent_draws()
        assert len(draws) >= 1
