"""
Models for lottery draw execution.
"""
import uuid

from django.conf import settings
from django.db import models


class Draw(models.Model):
    """
    Permanent audit record of a lottery draw execution.
    Only one draw can ever be executed for a single lottery.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lottery = models.OneToOneField(
        'lotteries.Lottery',
        on_delete=models.PROTECT,
        related_name='draw',
        help_text='Lottery for which this draw was conducted.',
    )
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='executed_draws',
        help_text='Staff member (Draw Officer or Super Admin) who executed the draw.',
    )
    total_eligible_tickets = models.PositiveIntegerField(
        help_text='Total number of sold tickets eligible during this draw.',
    )
    randomness_hash = models.CharField(
        max_length=64,
        help_text='SHA-256 cryptographic proof of entropy/randomness for audit verification.',
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text='Operational remarks or external auditor witness notes.',
    )
    executed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-executed_at']
        verbose_name = 'Draw'
        verbose_name_plural = 'Draws'

    def __str__(self):
        return f'Draw for {self.lottery.name} ({self.executed_at.strftime("%Y-%m-%d %H:%M")})'
