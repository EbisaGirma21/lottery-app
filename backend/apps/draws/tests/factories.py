"""
Test factories for Draw models.
"""
import factory

from apps.accounts.tests.factories import DrawOfficerFactory
from apps.draws.models import Draw
from apps.lotteries.tests.factories import LotteryFactory


class DrawFactory(factory.django.DjangoModelFactory):
    """Factory for Draw instances."""

    class Meta:
        model = Draw

    lottery = factory.SubFactory(LotteryFactory)
    executed_by = factory.SubFactory(DrawOfficerFactory)
    total_eligible_tickets = 50
    randomness_hash = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    notes = 'Official draw execution'
