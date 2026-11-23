"""
Test factories for Winner models.
"""
from decimal import Decimal
import factory

from apps.draws.tests.factories import DrawFactory
from apps.lotteries.tests.factories import CustomerFactory, TicketFactory
from apps.winners.models import ClaimStatus, Winner, WinningPosition


class WinnerFactory(factory.django.DjangoModelFactory):
    """Factory for Winner instances."""

    class Meta:
        model = Winner

    draw = factory.SubFactory(DrawFactory)
    lottery = factory.LazyAttribute(lambda o: o.draw.lottery)
    ticket = factory.SubFactory(TicketFactory)
    customer = factory.SubFactory(CustomerFactory)
    position = WinningPosition.FIRST
    prize_name = 'First Prize'
    prize_description = 'Grand Prize'
    prize_value = Decimal('500000.00')
    claim_status = ClaimStatus.PENDING
