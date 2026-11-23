"""
Test factories for Payment models.
"""
from decimal import Decimal
import factory

from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory
from apps.payments.models import Payment, PaymentMethod, PaymentStatus


class PaymentFactory(factory.django.DjangoModelFactory):
    """Factory for Payment instances."""

    class Meta:
        model = Payment
        skip_postgeneration_save = True

    customer = factory.SubFactory(CustomerFactory)
    lottery = factory.SubFactory(LotteryFactory)
    payment_method = PaymentMethod.TELEBIRR
    transaction_reference = factory.Sequence(lambda n: f'TXNREF{n:06d}')
    amount = Decimal('100.00')
    status = PaymentStatus.PENDING

    @factory.post_generation
    def reservations(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.reservations.add(*extracted)
