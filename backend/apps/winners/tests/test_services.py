"""
Tests for winner services (claim_prize).
"""
import pytest

from apps.accounts.tests.factories import LotteryManagerFactory
from apps.audit_logs.models import AuditLog
from apps.winners.models import ClaimStatus
from apps.winners.services import claim_prize
from apps.winners.tests.factories import WinnerFactory


@pytest.fixture
def lottery_manager():
    return LotteryManagerFactory()


@pytest.mark.django_db
class TestClaimPrize:
    """Tests for claim_prize service."""

    def test_claim_prize_success(self, lottery_manager):
        winner = WinnerFactory(claim_status=ClaimStatus.PENDING)

        claimed = claim_prize(
            winner=winner,
            staff_user=lottery_manager,
            payout_reference='CHECK-998877',
            admin_notes='Verified government ID and physical ticket.',
        )

        assert claimed.claim_status == ClaimStatus.CLAIMED
        assert claimed.claimed_at is not None
        assert claimed.verified_by == lottery_manager
        assert claimed.payout_reference == 'CHECK-998877'
        assert claimed.admin_notes == 'Verified government ID and physical ticket.'

        # Verify audit log
        assert AuditLog.objects.filter(
            action='PRIZE_CLAIMED',
            entity_id=str(claimed.id),
        ).exists()

    def test_claim_prize_empty_reference_fails(self, lottery_manager):
        winner = WinnerFactory(claim_status=ClaimStatus.PENDING)

        with pytest.raises(ValueError, match='Payout reference'):
            claim_prize(
                winner=winner,
                staff_user=lottery_manager,
                payout_reference='   ',
            )

    def test_claim_already_claimed_fails(self, lottery_manager):
        winner = WinnerFactory(claim_status=ClaimStatus.CLAIMED)

        with pytest.raises(ValueError, match='already been claimed'):
            claim_prize(
                winner=winner,
                staff_user=lottery_manager,
                payout_reference='CHECK-001',
            )

    def test_claim_expired_fails(self, lottery_manager):
        winner = WinnerFactory(claim_status=ClaimStatus.EXPIRED)

        with pytest.raises(ValueError, match='expired'):
            claim_prize(
                winner=winner,
                staff_user=lottery_manager,
                payout_reference='CHECK-002',
            )
