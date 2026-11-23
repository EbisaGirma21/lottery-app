"""
Tests for Draw API endpoints: list, detail, execute.
"""
from decimal import Decimal
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
from apps.draws.models import Draw
from apps.draws.tests.factories import DrawFactory
from apps.lotteries.models import LotteryStatus
from apps.lotteries.services import generate_tickets_for_lottery
from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory
from apps.tickets.models import Ticket, TicketStatus


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def draw_officer():
    return DrawOfficerFactory()


@pytest.fixture
def super_admin():
    return SuperAdminFactory()


@pytest.fixture
def lottery_manager():
    return LotteryManagerFactory()


@pytest.fixture
def payment_officer():
    return PaymentOfficerFactory()


@pytest.fixture
def viewer():
    return ViewerFactory()


@pytest.fixture
def closed_lottery():
    lottery = LotteryFactory(status=LotteryStatus.CLOSED, total_numbers=50, ticket_price=Decimal('50.00'))
    generate_tickets_for_lottery(lottery)
    customer = CustomerFactory()
    for t in Ticket.objects.filter(lottery=lottery)[:5]:
        t.status = TicketStatus.SOLD
        t.customer = customer
        t.save()
    return lottery


@pytest.mark.django_db
class TestDrawAPI:
    """Tests for /api/draws/ endpoints."""

    list_url = '/api/draws/'
    execute_url = '/api/draws/execute/'

    def test_unauthenticated_cannot_access_draws(self, api_client):
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_draws_authenticated(self, api_client, viewer):
        DrawFactory()
        api_client.force_authenticate(user=viewer)
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] >= 1

    def test_execute_draw_as_draw_officer(self, api_client, draw_officer, closed_lottery):
        api_client.force_authenticate(user=draw_officer)
        payload = {'lottery_id': str(closed_lottery.id), 'notes': 'Official Draw Session 1'}
        response = api_client.post(self.execute_url, payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['lottery'] == str(closed_lottery.id)
        assert len(data['winners']) == 3
        assert data['total_eligible_tickets'] == 5

    def test_execute_draw_as_super_admin(self, api_client, super_admin, closed_lottery):
        api_client.force_authenticate(user=super_admin)
        payload = {'lottery_id': str(closed_lottery.id)}
        response = api_client.post(self.execute_url, payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_execute_draw_as_lottery_manager_forbidden(self, api_client, lottery_manager, closed_lottery):
        api_client.force_authenticate(user=lottery_manager)
        payload = {'lottery_id': str(closed_lottery.id)}
        response = api_client.post(self.execute_url, payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_execute_draw_as_payment_officer_forbidden(self, api_client, payment_officer, closed_lottery):
        api_client.force_authenticate(user=payment_officer)
        payload = {'lottery_id': str(closed_lottery.id)}
        response = api_client.post(self.execute_url, payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_execute_draw_as_viewer_forbidden(self, api_client, viewer, closed_lottery):
        api_client.force_authenticate(user=viewer)
        payload = {'lottery_id': str(closed_lottery.id)}
        response = api_client.post(self.execute_url, payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_execute_draw_open_lottery_fails(self, api_client, draw_officer):
        open_lottery = LotteryFactory(status=LotteryStatus.OPEN, total_numbers=50)
        api_client.force_authenticate(user=draw_officer)
        payload = {'lottery_id': str(open_lottery.id)}
        response = api_client.post(self.execute_url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_execute_draw_duplicate_fails(self, api_client, draw_officer, closed_lottery):
        api_client.force_authenticate(user=draw_officer)
        payload = {'lottery_id': str(closed_lottery.id)}

        # First execution succeeds
        r1 = api_client.post(self.execute_url, payload, format='json')
        assert r1.status_code == status.HTTP_201_CREATED

        # Second execution fails
        r2 = api_client.post(self.execute_url, payload, format='json')
        assert r2.status_code == status.HTTP_400_BAD_REQUEST
