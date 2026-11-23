"""
Tests for Telegram Bot Keyboard builders.
"""
from decimal import Decimal
import pytest
from apps.lotteries.tests.factories import LotteryFactory, TicketFactory
from apps.reservations.tests.factories import ReservationFactory
from apps.telegram_bot.keyboards import (
    cancel_inline_keyboard,
    contact_request_keyboard,
    lotteries_inline_keyboard,
    lottery_detail_keyboard,
    main_menu_reply_keyboard,
    payment_methods_keyboard,
    reservations_selection_keyboard,
    skip_receipt_keyboard,
    ticket_grid_keyboard,
)


@pytest.mark.django_db
class TestTelegramKeyboards:
    """Tests for keyboard builders."""

    def test_main_menu_reply_keyboard(self):
        kb = main_menu_reply_keyboard()
        buttons = [btn.text if hasattr(btn, 'text') else str(btn) for row in kb.keyboard for btn in row]
        assert '🎟️ Active Lotteries' in buttons
        assert '🎫 My Tickets' in buttons
        assert '💳 Submit Payment' in buttons
        assert '🏆 Draw Results' in buttons
        assert 'ℹ️ Help & Info' in buttons

    def test_contact_request_keyboard(self):
        kb = contact_request_keyboard()
        assert kb.keyboard[0][0].request_contact is True
        skip_btn = kb.keyboard[1][0]
        assert (skip_btn.text if hasattr(skip_btn, 'text') else str(skip_btn)) == 'Skip for now'

    def test_lotteries_inline_keyboard(self):
        l1 = LotteryFactory(name="L1", ticket_price=Decimal("10.00"))
        l2 = LotteryFactory(name="L2", ticket_price=Decimal("20.00"))
        kb = lotteries_inline_keyboard([l1, l2])
        assert len(kb.inline_keyboard) == 2
        assert kb.inline_keyboard[0][0].callback_data == f"lottery:{l1.id}"
        assert kb.inline_keyboard[1][0].callback_data == f"lottery:{l2.id}"

    def test_lottery_detail_keyboard(self):
        kb = lottery_detail_keyboard("some-uuid")
        data = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "tickets:some-uuid:1" in data
        assert "quick_pick:some-uuid:1" in data
        assert "quick_pick:some-uuid:5" in data
        assert "list_lotteries" in data

    def test_ticket_grid_keyboard(self):
        lottery = LotteryFactory()
        tickets = [TicketFactory(lottery=lottery, ticket_number=str(i).zfill(3)) for i in range(1, 9)]
        kb = ticket_grid_keyboard(
            str(lottery.id),
            tickets,
            page=1,
            total_pages=3,
            selected_ids={str(tickets[0].id)},
        )
        # Check first ticket has checkmark
        first_btn = kb.inline_keyboard[0][0]
        assert "✅" in first_btn.text
        assert str(tickets[0].id) in first_btn.callback_data

        # Check action row has confirm reserve button
        all_buttons = [btn for row in kb.inline_keyboard for btn in row]
        assert any("Confirm Reservation" in b.text for b in all_buttons)

    def test_payment_methods_keyboard(self):
        kb = payment_methods_keyboard()
        callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "pay_channel:telebirr" in callbacks
        assert "pay_channel:cbe" in callbacks
        assert "pay_channel:awash" in callbacks
        assert "pay_channel:boa" in callbacks
        assert "cancel_flow" in callbacks

    def test_reservations_selection_keyboard(self):
        r1 = ReservationFactory()
        kb = reservations_selection_keyboard([r1])
        assert kb.inline_keyboard[0][0].callback_data == f"pay_res:{r1.id}"
        assert kb.inline_keyboard[1][0].callback_data == "cancel_flow"

    def test_utility_keyboards(self):
        skip_kb = skip_receipt_keyboard()
        assert skip_kb.inline_keyboard[0][0].callback_data == "skip_receipt"

        cancel_kb = cancel_inline_keyboard()
        assert cancel_kb.inline_keyboard[0][0].callback_data == "cancel_flow"
