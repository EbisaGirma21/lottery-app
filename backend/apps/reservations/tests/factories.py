"""
Test factories for Reservation models.
"""
from datetime import timedelta
import factory
from django.utils import timezone

from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory, TicketFactory
from apps.reservations.models import Reservation, ReservationStatus


class ReservationFactory(factory.django.DjangoModelFactory):
    """Factory for Reservation instances."""

    class Meta:
        model = Reservation

    customer = factory.SubFactory(CustomerFactory)
    lottery = factory.SubFactory(LotteryFactory)
    ticket = factory.LazyAttribute(lambda o: TicketFactory(lottery=o.lottery))
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=48))
    status = ReservationStatus.ACTIVE
