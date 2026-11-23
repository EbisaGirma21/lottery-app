"""
Ticket model — represents individual lottery numbers.
"""
import uuid

from django.db import models

from apps.lotteries.models import Customer, Lottery


class TicketStatus(models.TextChoices):
    """Lifecycle status of a lottery ticket."""
    AVAILABLE = 'available', 'Available'
    RESERVED = 'reserved', 'Reserved'
    SOLD = 'sold', 'Sold'
    WINNER = 'winner', 'Winner'


class Ticket(models.Model):
    """
    A single lottery number belonging to a specific lottery.

    Ticket numbers are zero-padded strings whose width adapts to
    the lottery's total_numbers (e.g., 001 for 100 tickets, 0001 for 10000).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lottery = models.ForeignKey(
        Lottery,
        on_delete=models.CASCADE,
        related_name='tickets',
    )
    ticket_number = models.CharField(
        max_length=20,
        db_index=True,
        help_text='Zero-padded ticket number string (e.g., "0042").',
    )
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.AVAILABLE,
        db_index=True,
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        help_text='The customer who owns this ticket (set after payment approval).',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tickets'
        ordering = ['ticket_number']
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        constraints = [
            models.UniqueConstraint(
                fields=['lottery', 'ticket_number'],
                name='uq_lottery_ticket_number',
            ),
        ]
        indexes = [
            models.Index(
                fields=['lottery', 'status'],
                name='idx_ticket_lottery_status',
            ),
            models.Index(
                fields=['customer'],
                name='idx_ticket_customer',
            ),
        ]

    def __str__(self) -> str:
        return f'#{self.ticket_number} ({self.lottery.name}) — {self.get_status_display()}'
