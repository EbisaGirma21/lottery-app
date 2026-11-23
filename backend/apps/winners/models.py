"""
Models for winners, winning positions, and prize claims.
"""
from decimal import Decimal
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class WinningPosition(models.IntegerChoices):
    """The 3 winning positions in every lottery."""
    FIRST = 1, '1st Prize'
    SECOND = 2, '2nd Prize'
    THIRD = 3, '3rd Prize'


class ClaimStatus(models.TextChoices):
    """Lifecycle of prize disbursement."""
    PENDING = 'pending', 'Pending Claim'
    CLAIMED = 'claimed', 'Claimed'
    EXPIRED = 'expired', 'Expired'


class Winner(models.Model):
    """
    Record of a winning ticket in a lottery draw.

    Stores a snapshot of the prize details at the time of the draw
    and tracks verification and prize handover.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    draw = models.ForeignKey(
        'draws.Draw',
        on_delete=models.CASCADE,
        related_name='winners',
        help_text='Draw in which this winner was selected.',
    )
    lottery = models.ForeignKey(
        'lotteries.Lottery',
        on_delete=models.CASCADE,
        related_name='winners',
        help_text='Lottery this winning belongs to.',
    )
    ticket = models.OneToOneField(
        'tickets.Ticket',
        on_delete=models.PROTECT,
        related_name='winner_record',
        help_text='Winning ticket.',
    )
    customer = models.ForeignKey(
        'lotteries.Customer',
        on_delete=models.PROTECT,
        related_name='winnings',
        help_text='Customer who owns the winning ticket.',
    )
    position = models.PositiveSmallIntegerField(
        choices=WinningPosition.choices,
        help_text='Winning position: 1 (1st), 2 (2nd), or 3 (3rd).',
    )
    prize_name = models.CharField(max_length=255)
    prize_description = models.TextField(blank=True, default='')
    prize_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Cash value or equivalent value of the prize.',
    )
    claim_status = models.CharField(
        max_length=20,
        choices=ClaimStatus.choices,
        default=ClaimStatus.PENDING,
        db_index=True,
    )
    claimed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when the prize was claimed.',
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_claims',
        help_text='Staff member who confirmed the claimant identity and disbursed the prize.',
    )
    payout_reference = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Bank check number, transfer reference, or handover receipt number.',
    )
    admin_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']
        verbose_name = 'Winner'
        verbose_name_plural = 'Winners'
        constraints = [
            models.UniqueConstraint(
                fields=['lottery', 'position'],
                name='unique_lottery_winning_position',
            ),
            models.UniqueConstraint(
                fields=['draw', 'position'],
                name='unique_draw_winning_position',
            ),
        ]

    def __str__(self):
        return f'{self.get_position_display()}: Ticket #{self.ticket.ticket_number} — {self.prize_name} ({self.customer})'

    @property
    def masked_customer_name(self) -> str:
        """Masked customer name for public display (privacy protection)."""
        name = self.customer.full_name or 'Anonymous'
        parts = name.split()
        masked_parts = []
        for part in parts:
            if len(part) <= 2:
                masked_parts.append(part[0] + '*')
            else:
                masked_parts.append(part[0] + '*' * (len(part) - 2) + part[-1])
        return ' '.join(masked_parts)

    @property
    def masked_phone_number(self) -> str:
        """Masked customer phone number for public display."""
        phone = self.customer.phone_number or ''
        if len(phone) >= 9:
            return phone[:5] + '****' + phone[-4:]
        return phone
