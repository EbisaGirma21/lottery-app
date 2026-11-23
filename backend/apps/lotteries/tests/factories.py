"""
Test factories for Phase 2 models.
"""
from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone

from apps.accounts.tests.factories import SuperAdminFactory
from apps.lotteries.models import Customer, CustomerStatus, Lottery, LotteryStatus, PaymentInstruction
from apps.tickets.models import Ticket, TicketStatus


class LotteryFactory(factory.django.DjangoModelFactory):
    """Factory for Lottery instances."""

    class Meta:
        model = Lottery

    name = factory.Sequence(lambda n: f'Test Lottery {n}')
    slug = factory.Sequence(lambda n: f'test-lottery-{n}')
    description = 'A test lottery'
    ticket_price = Decimal('100.00')
    total_numbers = 100
    start_date = factory.LazyFunction(lambda: timezone.now())
    closing_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    draw_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=8))
    first_prize_name = 'First Prize'
    first_prize_description = 'Grand Prize'
    first_prize_value = Decimal('50000.00')
    second_prize_name = 'Second Prize'
    second_prize_description = 'Runner Up'
    second_prize_value = Decimal('25000.00')
    third_prize_name = 'Third Prize'
    third_prize_description = 'Third Place'
    third_prize_value = Decimal('10000.00')
    reservation_hours = 48
    status = LotteryStatus.DRAFT
    created_by = factory.SubFactory(SuperAdminFactory)


class CustomerFactory(factory.django.DjangoModelFactory):
    """Factory for Customer instances."""

    class Meta:
        model = Customer

    full_name = factory.Faker('name')
    phone_number = factory.Sequence(lambda n: f'+25191234{n:04d}')
    telegram_user_id = factory.Sequence(lambda n: 100000 + n)
    telegram_username = factory.Sequence(lambda n: f'user{n}')
    status = CustomerStatus.ACTIVE


class TicketFactory(factory.django.DjangoModelFactory):
    """Factory for Ticket instances."""

    class Meta:
        model = Ticket

    lottery = factory.SubFactory(LotteryFactory)
    ticket_number = factory.Sequence(lambda n: f'{n:03d}')
    status = TicketStatus.AVAILABLE


class PaymentInstructionFactory(factory.django.DjangoModelFactory):
    """Factory for PaymentInstruction instances."""

    class Meta:
        model = PaymentInstruction

    lottery = factory.SubFactory(LotteryFactory)
    payment_method = 'telebirr'
    account_name = 'Test Account'
    account_number = '0911223344'
    is_active = True

