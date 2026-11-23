"""
Cryptographically secure draw execution engine.
"""
import hashlib
import logging
import secrets
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.audit_logs.services import log_action
from apps.draws.models import Draw
from apps.lotteries.models import Lottery, LotteryStatus
from apps.tickets.models import Ticket, TicketStatus
from apps.winners.models import Winner, WinningPosition

logger = logging.getLogger(__name__)


def execute_draw(
    lottery: Lottery,
    executed_by,
    notes: str = '',
    ip_address: Optional[str] = None,
) -> Draw:
    """
    Execute a lottery draw with cryptographically secure random selection.

    Validates:
    - Draw has not already been conducted for this lottery.
    - Lottery status is CLOSED.
    - At least 3 tickets have been sold (to award 1st, 2nd, and 3rd prizes).

    Actions:
    1. Selects 3 distinct winning tickets from SOLD tickets using `secrets.SystemRandom`.
    2. Computes an audit SHA-256 randomness hash.
    3. Creates Draw record.
    4. Creates 3 Winner records with prize snapshots.
    5. Updates winning tickets status -> WINNER.
    6. Transitions lottery status -> DRAWN.
    7. Records audit log.

    Returns the created Draw instance.
    """
    with transaction.atomic():
        locked_lottery = Lottery.objects.select_for_update().get(id=lottery.id)

        # 1. Prevent duplicate draw
        if Draw.objects.filter(lottery=locked_lottery).exists():
            raise ValueError(
                f'A draw has already been executed for lottery "{locked_lottery.name}".'
            )

        # 2. Check lottery status
        if locked_lottery.status != LotteryStatus.CLOSED:
            raise ValueError(
                f'Cannot execute draw: lottery status is "{locked_lottery.get_status_display()}". '
                'The lottery must be Closed before conducting a draw.'
            )

        # 3. Retrieve eligible SOLD tickets with row-level locks
        sold_tickets = list(
            Ticket.objects.select_for_update()
            .filter(lottery=locked_lottery, status=TicketStatus.SOLD)
        )

        if len(sold_tickets) < 3:
            raise ValueError(
                f'Cannot execute draw: only {len(sold_tickets)} ticket(s) have been sold. '
                'At least 3 sold tickets are required to award 1st, 2nd, and 3rd prizes.'
            )

        # 4. Cryptographically secure selection without replacement
        rng = secrets.SystemRandom()
        winning_tickets = rng.sample(sold_tickets, 3)
        t1, t2, t3 = winning_tickets[0], winning_tickets[1], winning_tickets[2]

        # 5. Generate cryptographic entropy hash
        entropy_proof = (
            f'{locked_lottery.id}:{timezone.now().isoformat()}:'
            f'{secrets.token_hex(32)}:{t1.id}:{t2.id}:{t3.id}'
        )
        randomness_hash = hashlib.sha256(entropy_proof.encode('utf-8')).hexdigest()

        # 6. Create Draw record
        draw = Draw.objects.create(
            lottery=locked_lottery,
            executed_by=executed_by,
            total_eligible_tickets=len(sold_tickets),
            randomness_hash=randomness_hash,
            notes=notes,
        )

        # 7. Create Winner records (snapshotting prize attributes)
        prizes = [
            (
                WinningPosition.FIRST,
                t1,
                locked_lottery.first_prize_name,
                locked_lottery.first_prize_description,
                locked_lottery.first_prize_value,
            ),
            (
                WinningPosition.SECOND,
                t2,
                locked_lottery.second_prize_name,
                locked_lottery.second_prize_description,
                locked_lottery.second_prize_value,
            ),
            (
                WinningPosition.THIRD,
                t3,
                locked_lottery.third_prize_name,
                locked_lottery.third_prize_description,
                locked_lottery.third_prize_value,
            ),
        ]

        for position, ticket, prize_name, prize_desc, prize_val in prizes:
            Winner.objects.create(
                draw=draw,
                lottery=locked_lottery,
                ticket=ticket,
                customer_id=ticket.customer_id,
                position=position,
                prize_name=prize_name,
                prize_description=prize_desc,
                prize_value=prize_val,
            )

        # 8. Update winning tickets -> WINNER
        for ticket in [t1, t2, t3]:
            ticket.status = TicketStatus.WINNER
            ticket.save(update_fields=['status', 'updated_at'])

        # 9. Transition lottery status -> DRAWN
        locked_lottery.status = LotteryStatus.DRAWN
        locked_lottery.save(update_fields=['status', 'updated_at'])

    log_action(
        user=executed_by,
        action='DRAW_EXECUTED',
        entity_type='Draw',
        entity_id=str(draw.id),
        new_value={
            'lottery': locked_lottery.name,
            'eligible_tickets': len(sold_tickets),
            '1st_prize_ticket': t1.ticket_number,
            '2nd_prize_ticket': t2.ticket_number,
            '3rd_prize_ticket': t3.ticket_number,
            'randomness_hash': randomness_hash,
        },
        ip_address=ip_address,
    )

    logger.info(
        'Draw executed for %s by %s. Winners: 1st=#%s, 2nd=#%s, 3rd=#%s',
        locked_lottery.name, executed_by.email,
        t1.ticket_number, t2.ticket_number, t3.ticket_number,
    )

    try:
        from apps.notifications.services import notify_winner_announced
        for winner in draw.winners.select_related('customer', 'lottery', 'ticket'):
            notify_winner_announced(winner)
    except Exception as e:
        logger.warning('Failed to dispatch winner notifications: %s', e)

    return draw
