"""
Tests for Winner API endpoints: public listing, staff detail, claim action.
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import (
    DrawOfficerFactory,
    LotteryManagerFactory,
    PaymentOfficerFactory,
    SuperAdminFactory,
    ViewerFactory,
)
from apps.lotteries.tests.factories import CustomerFactory
from apps.winners.models import ClaimStatus, WinningPosition
from apps.winners.tests.factories import WinnerFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def lottery_manager():
    return LotteryManagerFactory()


@pytest.fixture
def super_admin():
    return SuperAdminFactory()


@pytest.fixture
def draw_officer():
    return DrawOfficerFactory()


@pytest.fixture
def viewer():
    return ViewerFactory()


@pytest.fixture
def customer():
    return CustomerFactory(full_name='Dawit Bekele', phone_number='+251911223344')


@pytest.mark.django_db
class TestWinnerAPI:
    """Tests for /api/winners/ endpoints."""

    list_url = '/api/winners/'

    def test_list_winners_public_masked(self, api_client, customer):
        winner = WinnerFactory(customer=customer, position=WinningPosition.FIRST)

        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        results = data.get('results', data)
        assert len(results) >= 1

        first = results[0]
        # Must have masked name and masked phone, NOT full customer profile
        assert 'masked_name' in first
        assert 'masked_phone' in first
        assert first['masked_phone'] == '+2519****3344'
        assert 'customer_phone' not in first

    def test_list_winners_staff_full(self, api_client, lottery_manager, customer):
        winner = WinnerFactory(customer=customer, position=WinningPosition.FIRST)
        api_client.force_authenticate(user=lottery_manager)

        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        results = data.get('results', data)
        assert len(results) >= 1

        first = results[0]
        # Staff sees full customer phone number
        assert first['customer_phone'] == '+251911223344'

    def test_filter_winners_by_lottery(self, api_client):
        w1 = WinnerFactory()
        w2 = WinnerFactory()

        response = api_client.get(f'{self.list_url}?lottery={w1.lottery_id}')
        assert response.status_code == status.HTTP_200_OK
        results = response.json().get('results', response.json())
        assert len(results) == 1
        assert results[0]['id'] == str(w1.id)

    def test_claim_prize_as_lottery_manager(self, api_client, lottery_manager):
        winner = WinnerFactory(claim_status=ClaimStatus.PENDING)
        api_client.force_authenticate(user=lottery_manager)

        response = api_client.post(
            f'{self.list_url}{winner.id}/claim/',
            {'payout_reference': 'CBE-TXN-7788', 'admin_notes': 'Transferred via CBE Birr.'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['claim_status'] == 'claimed'
        assert response.json()['payout_reference'] == 'CBE-TXN-7788'

    def test_claim_prize_as_super_admin(self, api_client, super_admin):
        winner = WinnerFactory(claim_status=ClaimStatus.PENDING)
        api_client.force_authenticate(user=super_admin)

        response = api_client.post(
            f'{self.list_url}{winner.id}/claim/',
            {'payout_reference': 'BANK-CHECK-1122'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['claim_status'] == 'claimed'

    def test_claim_prize_as_viewer_forbidden(self, api_client, viewer):
        winner = WinnerFactory(claim_status=ClaimStatus.PENDING)
        api_client.force_authenticate(user=viewer)

        response = api_client.post(
            f'{self.list_url}{winner.id}/claim/',
            {'payout_reference': 'ATTEMPT-REF'},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_claim_prize_as_draw_officer_forbidden(self, api_client, draw_officer):
        winner = WinnerFactory(claim_status=ClaimStatus.PENDING)
        api_client.force_authenticate(user=draw_officer)

        response = api_client.post(
            f'{self.list_url}{winner.id}/claim/',
            {'payout_reference': 'ATTEMPT-REF'},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_claim_prize_unauthenticated_forbidden(self, api_client):
        winner = WinnerFactory(claim_status=ClaimStatus.PENDING)
        response = api_client.post(
            f'{self.list_url}{winner.id}/claim/',
            {'payout_reference': 'ATTEMPT-REF'},
            format='json',
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_claim_prize_missing_reference_fails(self, api_client, lottery_manager):
        winner = WinnerFactory(claim_status=ClaimStatus.PENDING)
        api_client.force_authenticate(user=lottery_manager)

        response = api_client.post(
            f'{self.list_url}{winner.id}/claim/',
            {},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
