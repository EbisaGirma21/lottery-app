"""
Tests for Lottery and Customer models.
"""
import pytest
from django.utils import timezone

from apps.lotteries.models import Customer, Lottery, LotteryStatus, LOTTERY_STATUS_TRANSITIONS
from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory


@pytest.mark.django_db
class TestLotteryModel:
    """Tests for the Lottery model."""

    def test_create_lottery(self):
        lottery = LotteryFactory(name='New Year Lottery', total_numbers=500)
        assert lottery.name == 'New Year Lottery'
        assert lottery.total_numbers == 500
        assert lottery.status == LotteryStatus.DRAFT

    def test_slug_auto_generated(self):
        lottery = LotteryFactory(name='Grand Lottery 2026', slug='')
        assert lottery.slug == 'grand-lottery-2026'

    def test_slug_uniqueness(self):
        LotteryFactory(name='Duplicate', slug='duplicate')
        lottery2 = LotteryFactory(name='Duplicate', slug='')
        assert lottery2.slug == 'duplicate-1'

    def test_ticket_number_width(self):
        """Width should adapt to total_numbers."""
        assert LotteryFactory(total_numbers=100).ticket_number_width == 3
        assert LotteryFactory(total_numbers=1000).ticket_number_width == 4
        assert LotteryFactory(total_numbers=10000).ticket_number_width == 5
        assert LotteryFactory(total_numbers=100000).ticket_number_width == 6

    def test_format_ticket_number(self):
        lottery = LotteryFactory(total_numbers=10000)
        assert lottery.format_ticket_number(1) == '00001'
        assert lottery.format_ticket_number(42) == '00042'
        assert lottery.format_ticket_number(10000) == '10000'

    def test_status_transitions(self):
        lottery = LotteryFactory(status=LotteryStatus.DRAFT)
        assert lottery.can_transition_to(LotteryStatus.OPEN) is True
        assert lottery.can_transition_to(LotteryStatus.CANCELLED) is True
        assert lottery.can_transition_to(LotteryStatus.CLOSED) is False
        assert lottery.can_transition_to(LotteryStatus.DRAWN) is False

    def test_all_status_transitions_defined(self):
        """Every status should have defined transitions."""
        for status_val, _ in LotteryStatus.choices:
            assert status_val in LOTTERY_STATUS_TRANSITIONS

    def test_completed_lottery_cannot_transition(self):
        lottery = LotteryFactory(status=LotteryStatus.COMPLETED)
        for target, _ in LotteryStatus.choices:
            assert lottery.can_transition_to(target) is False

    def test_cancelled_lottery_cannot_transition(self):
        lottery = LotteryFactory(status=LotteryStatus.CANCELLED)
        for target, _ in LotteryStatus.choices:
            assert lottery.can_transition_to(target) is False

    def test_str_representation(self):
        lottery = LotteryFactory(name='Test Lottery')
        assert str(lottery) == 'Test Lottery'


@pytest.mark.django_db
class TestCustomerModel:
    """Tests for the Customer model."""

    def test_create_customer(self):
        customer = CustomerFactory(
            full_name='Abebe Kebede',
            phone_number='+251912345678',
            telegram_user_id=123456789,
        )
        assert customer.full_name == 'Abebe Kebede'
        assert customer.status == 'active'

    def test_telegram_user_id_uniqueness(self):
        CustomerFactory(telegram_user_id=111)
        with pytest.raises(Exception):
            CustomerFactory(telegram_user_id=111)

    def test_phone_normalization(self):
        """Phone normalization handles Ethiopian formats."""
        assert Customer.normalize_phone('0912345678') == '+251912345678'
        assert Customer.normalize_phone('+251912345678') == '+251912345678'
        assert Customer.normalize_phone('251912345678') == '+251912345678'
        assert Customer.normalize_phone('912345678') == '+251912345678'
        assert Customer.normalize_phone('  0912 345 678  ') == '+251912345678'

    def test_str_representation(self):
        customer = CustomerFactory(full_name='Test User', phone_number='+251911111111')
        assert 'Test User' in str(customer)
        assert '+251911111111' in str(customer)
