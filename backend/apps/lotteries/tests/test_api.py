"""
Tests for the lottery and customer API endpoints.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import LotteryManagerFactory, SuperAdminFactory, ViewerFactory
from apps.lotteries.models import LotteryStatus
from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory


@pytest.mark.django_db
class TestLotteryAPI:
    """Tests for lottery CRUD endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.admin = SuperAdminFactory()
        self.list_url = reverse('lottery-list')

    def _lottery_data(self):
        now = timezone.now()
        return {
            'name': 'API Test Lottery',
            'description': 'Test',
            'ticket_price': '100.00',
            'total_numbers': 50,
            'start_date': now.isoformat(),
            'closing_date': (now + timedelta(days=7)).isoformat(),
            'draw_date': (now + timedelta(days=8)).isoformat(),
            'first_prize_name': '1st',
            'first_prize_description': 'Grand',
            'first_prize_value': '50000.00',
            'second_prize_name': '2nd',
            'second_prize_description': 'Runner',
            'second_prize_value': '25000.00',
            'third_prize_name': '3rd',
            'third_prize_description': 'Third',
            'third_prize_value': '10000.00',
        }

    def test_create_lottery(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.list_url, self._lottery_data(), format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['name'] == 'API Test Lottery'

    def test_create_lottery_generates_tickets(self):
        """Creating a lottery should auto-generate all ticket numbers."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.list_url, self._lottery_data(), format='json')
        assert response.status_code == status.HTTP_201_CREATED

        from apps.tickets.models import Ticket
        lottery_id = response.json()['id']
        ticket_count = Ticket.objects.filter(lottery_id=lottery_id).count()
        assert ticket_count == 50

    def test_lottery_manager_can_create(self):
        manager = LotteryManagerFactory()
        self.client.force_authenticate(user=manager)
        response = self.client.post(self.list_url, self._lottery_data(), format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_viewer_cannot_create(self):
        viewer = ViewerFactory()
        self.client.force_authenticate(user=viewer)
        response = self.client.post(self.list_url, self._lottery_data(), format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_lotteries(self):
        LotteryFactory()
        LotteryFactory()
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] >= 2

    def test_change_status_draft_to_open(self):
        lottery = LotteryFactory(status=LotteryStatus.DRAFT)
        self.client.force_authenticate(user=self.admin)
        url = reverse('lottery-change-status', kwargs={'pk': lottery.id})
        response = self.client.post(url, {'status': 'open'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'open'

    def test_invalid_status_transition(self):
        lottery = LotteryFactory(status=LotteryStatus.DRAFT)
        self.client.force_authenticate(user=self.admin)
        url = reverse('lottery-change-status', kwargs={'pk': lottery.id})
        response = self.client.post(url, {'status': 'drawn'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_delete_non_draft_lottery(self):
        lottery = LotteryFactory(status=LotteryStatus.OPEN)
        self.client.force_authenticate(user=self.admin)
        url = reverse('lottery-detail', kwargs={'pk': lottery.id})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_validation_closing_before_start(self):
        self.client.force_authenticate(user=self.admin)
        data = self._lottery_data()
        data['closing_date'] = (timezone.now() - timedelta(days=1)).isoformat()
        response = self.client.post(self.list_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCustomerAPI:
    """Tests for customer management endpoints."""

    def setup_method(self):
        self.client = APIClient()
        self.admin = SuperAdminFactory()

    def test_create_customer(self):
        """Customer creation should work without auth (for Telegram bot)."""
        url = reverse('customer-list')
        response = self.client.post(url, {
            'full_name': 'Abebe Kebede',
            'phone_number': '0912345678',
            'telegram_user_id': 999999,
            'telegram_username': 'abebe',
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        # Phone should be normalized
        assert response.json()['phone_number'] == '+251912345678'

    def test_list_customers_requires_auth(self):
        url = reverse('customer-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_block_customer(self):
        customer = CustomerFactory()
        self.client.force_authenticate(user=self.admin)
        url = reverse('customer-block', kwargs={'pk': customer.id})
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'blocked'

    def test_unblock_customer(self):
        customer = CustomerFactory(status='blocked')
        self.client.force_authenticate(user=self.admin)
        url = reverse('customer-unblock', kwargs={'pk': customer.id})
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'active'

    def test_duplicate_telegram_id_rejected(self):
        CustomerFactory(telegram_user_id=12345)
        url = reverse('customer-list')
        response = self.client.post(url, {
            'full_name': 'Duplicate',
            'phone_number': '0912000000',
            'telegram_user_id': 12345,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
