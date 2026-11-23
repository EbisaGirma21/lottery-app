"""
Services for winner management and prize claims.
"""
import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.audit_logs.services import log_action
from apps.winners.models import ClaimStatus, Winner

logger = logging.getLogger(__name__)


def claim_prize(
    winner: Winner,
    staff_user,
    payout_reference: str,
    admin_notes: str = '',
    ip_address: Optional[str] = None,
) -> Winner:
    """
    Process and record a winner's prize claim.

    Validates:
    - Winner has not already claimed the prize.
    - Payout reference is provided.

    Updates:
    - claim_status -> CLAIMED
    - claimed_at -> now
    - verified_by -> staff_user
    - payout_reference, admin_notes
    - Records audit log.

    Returns the updated Winner instance.
    """
    ref = payout_reference.strip()
    if not ref:
        raise ValueError('Payout reference or transaction number is required to confirm claim.')

    with transaction.atomic():
        locked_winner = Winner.objects.select_for_update().get(id=winner.id)

        if locked_winner.claim_status == ClaimStatus.CLAIMED:
            raise ValueError('This prize has already been claimed.')

        if locked_winner.claim_status == ClaimStatus.EXPIRED:
            raise ValueError('The claim window for this prize has expired.')

        locked_winner.claim_status = ClaimStatus.CLAIMED
        locked_winner.claimed_at = timezone.now()
        locked_winner.verified_by = staff_user
        locked_winner.payout_reference = ref
        if admin_notes:
            locked_winner.admin_notes = admin_notes
        locked_winner.save()

    log_action(
        user=staff_user,
        action='PRIZE_CLAIMED',
        entity_type='Winner',
        entity_id=str(locked_winner.id),
        old_value={'claim_status': ClaimStatus.PENDING},
        new_value={
            'claim_status': ClaimStatus.CLAIMED,
            'payout_reference': ref,
            'verified_by': staff_user.email,
        },
        ip_address=ip_address,
    )

    logger.info(
        'Prize claimed for %s position %d by %s (Verified by %s, Ref: %s)',
        locked_winner.lottery.name, locked_winner.position,
        locked_winner.customer.full_name, staff_user.email, ref,
    )
    return locked_winner
