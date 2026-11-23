"""
Reservation model — temporary ticket holds with automatic expiration.
"""
import uuid

from django.db import models

from apps.lotteries.models import Customer, Lottery
from apps.tickets.models import Ticket


class ReservationStatus(models.TextChoices):
    """Lifecycle status of a ticket reservation."""
    ACTIVE = 'active', 'Active'
    EXPIRED = 'expired', 'Expired'
    CONFIRMED = 'confirmed', 'Confirmed'
    CANCELLED = 'cancelled', 'Cancelled'


class Reservation(models.Model):
    """
    A temporary hold on a ticket for a customer.

    Reservations automatically expire after the lottery's configured
    reservation_hours if payment is not submitted and approved.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='reservations',
    )
    lottery = models.ForeignKey(
        Lottery,
        on_delete=models.CASCADE,
        related_name='reservations',
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='reservations',
    )
    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        db_index=True,
        help_text='When this reservation expires if not confirmed.',
    )
    status = models.CharField(
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        db_table = 'reservations'
        ordering = ['-reserved_at']
        verbose_name = 'Reservation'
        verbose_name_plural = 'Reservations'
        indexes = [
            models.Index(
                fields=['status', 'expires_at'],
                name='idx_resv_status_expires',
            ),
            models.Index(
                fields=['customer', 'lottery'],
                name='idx_resv_cust_lottery',
            ),
        ]

    def __str__(self) -> str:
        return (
            f'Reservation #{self.ticket.ticket_number} '
            f'by {self.customer.full_name} '
            f'({self.get_status_display()})'
        )
