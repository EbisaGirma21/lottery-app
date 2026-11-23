"""
Lottery service layer — ticket generation and status management.
"""
import logging
from typing import Optional

from django.db import transaction

from apps.lotteries.models import LOTTERY_STATUS_TRANSITIONS, Lottery, LotteryStatus
from apps.tickets.models import Ticket, TicketStatus

logger = logging.getLogger(__name__)


def generate_tickets_for_lottery(lottery: Lottery) -> int:
    """
    Generate all ticket numbers for a lottery using bulk_create.

    Ticket numbers are zero-padded strings that automatically adapt
    to the total number count:
        100 tickets  →  001, 002, ..., 100
        10000 tickets → 0001, 0002, ..., 10000

    Args:
        lottery: The Lottery instance to generate tickets for.

    Returns:
        The number of tickets created.

    Raises:
        ValueError: If tickets already exist for this lottery.
    """
    existing_count = Ticket.objects.filter(lottery=lottery).count()
    if existing_count > 0:
        raise ValueError(
            f'Lottery "{lottery.name}" already has {existing_count} tickets. '
            f'Cannot regenerate.'
        )

    width = lottery.ticket_number_width
    batch_size = 5000  # Bulk create in batches for large lotteries

    tickets = []
    for num in range(1, lottery.total_numbers + 1):
        tickets.append(
            Ticket(
                lottery=lottery,
                ticket_number=str(num).zfill(width),
                status=TicketStatus.AVAILABLE,
            )
        )

        if len(tickets) >= batch_size:
            Ticket.objects.bulk_create(tickets)
            tickets = []

    # Insert remaining tickets
    if tickets:
        Ticket.objects.bulk_create(tickets)

    total_created = Ticket.objects.filter(lottery=lottery).count()
    logger.info(
        'Generated %d tickets for lottery "%s" (width=%d)',
        total_created, lottery.name, width,
    )
    return total_created


def transition_lottery_status(
    lottery: Lottery,
    new_status: str,
    user=None,
) -> Lottery:
    """
    Transition a lottery to a new status with validation.

    Args:
        lottery: The Lottery to transition.
        new_status: The target status.
        user: The staff user performing the transition (for audit).

    Returns:
        The updated Lottery instance.

    Raises:
        ValueError: If the transition is not allowed.
    """
    old_status = lottery.status

    if not lottery.can_transition_to(new_status):
        allowed = LOTTERY_STATUS_TRANSITIONS.get(old_status, [])
        allowed_display = ', '.join(allowed) if allowed else 'none'
        raise ValueError(
            f'Cannot transition lottery from "{old_status}" to "{new_status}". '
            f'Allowed transitions: {allowed_display}.'
        )

    lottery.status = new_status
    lottery.save(update_fields=['status', 'updated_at'])

    # Audit log
    from apps.audit_logs.services import log_action
    log_action(
        user=user,
        action='LOTTERY_STATUS_CHANGED',
        entity_type='Lottery',
        entity_id=str(lottery.id),
        old_value={'status': old_status},
        new_value={'status': new_status},
    )

    logger.info(
        'Lottery "%s" transitioned: %s → %s (by %s)',
        lottery.name, old_status, new_status,
        user.email if user else 'System',
    )
    return lottery


def get_lottery_stats(lottery: Lottery) -> dict:
    """
    Calculate real-time ticket statistics for a lottery.

    All counts are computed from the database — never cached or
    trusted from the frontend.
    """
    from django.db.models import Count, Q

    stats = Ticket.objects.filter(lottery=lottery).aggregate(
        total=Count('id'),
        available=Count('id', filter=Q(status=TicketStatus.AVAILABLE)),
        reserved=Count('id', filter=Q(status=TicketStatus.RESERVED)),
        sold=Count('id', filter=Q(status=TicketStatus.SOLD)),
        winner=Count('id', filter=Q(status=TicketStatus.WINNER)),
    )

    total = stats['total'] or 0
    sold = (stats['sold'] or 0) + (stats['winner'] or 0)

    stats['sold_percentage'] = round((sold / total * 100), 2) if total > 0 else 0
    stats['revenue'] = sold * lottery.ticket_price

    return stats
