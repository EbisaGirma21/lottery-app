"""
Tests for Draw model.
"""
import pytest
from django.db import IntegrityError

from apps.draws.models import Draw
from apps.draws.tests.factories import DrawFactory
from apps.lotteries.tests.factories import LotteryFactory


@pytest.mark.django_db
class TestDrawModel:
    """Tests for Draw model fields, constraints, and methods."""

    def test_create_draw(self):
        draw = DrawFactory()
        assert draw.id is not None
        assert draw.executed_at is not None
        assert draw.total_eligible_tickets == 50
        assert len(draw.randomness_hash) == 64

    def test_one_draw_per_lottery_constraint(self):
        lottery = LotteryFactory()
        DrawFactory(lottery=lottery)

        with pytest.raises(IntegrityError):
            DrawFactory(lottery=lottery)

    def test_str_representation(self):
        lottery = LotteryFactory(name='Christmas Mega Lottery')
        draw = DrawFactory(lottery=lottery)
        assert 'Christmas Mega Lottery' in str(draw)
