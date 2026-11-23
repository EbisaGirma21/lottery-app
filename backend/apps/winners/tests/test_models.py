"""
Tests for Winner model.
"""
from decimal import Decimal
import pytest
from django.db import IntegrityError

from apps.draws.tests.factories import DrawFactory
from apps.lotteries.tests.factories import CustomerFactory, TicketFactory
from apps.winners.models import ClaimStatus, Winner, WinningPosition
from apps.winners.tests.factories import WinnerFactory


@pytest.mark.django_db
class TestWinnerModel:
    """Tests for Winner model fields, constraints, and privacy helpers."""

    def test_create_winner(self):
        winner = WinnerFactory()
        assert winner.id is not None
        assert winner.claim_status == ClaimStatus.PENDING
        assert winner.claimed_at is None
        assert winner.verified_by is None
        assert winner.created_at is not None

    def test_unique_position_per_lottery(self):
        draw = DrawFactory()
        lottery = draw.lottery
        WinnerFactory(draw=draw, lottery=lottery, position=WinningPosition.FIRST)

        with pytest.raises(IntegrityError):
            WinnerFactory(draw=draw, lottery=lottery, position=WinningPosition.FIRST)

    def test_masked_customer_name(self):
        customer = CustomerFactory(full_name='Abebe Kebede')
        winner = WinnerFactory(customer=customer)
        # Should mask middle characters
        assert 'A' in winner.masked_customer_name
        assert 'Abebe Kebede' != winner.masked_customer_name
        assert '*' in winner.masked_customer_name

    def test_masked_phone_number(self):
        customer = CustomerFactory(phone_number='+251912345678')
        winner = WinnerFactory(customer=customer)
        assert winner.masked_phone_number == '+2519****5678'

    def test_str_representation(self):
        winner = WinnerFactory(position=WinningPosition.FIRST, prize_name='Gold Bar')
        assert '1st Prize' in str(winner)
        assert 'Gold Bar' in str(winner)
