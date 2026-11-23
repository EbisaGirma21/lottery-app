"""
Tests for Notification API endpoints.
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import ViewerFactory
from apps.lotteries.tests.factories import CustomerFactory
from apps.notifications.tests.factories import NotificationFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def staff_user():
    return ViewerFactory()


@pytest.fixture
def customer():
    return CustomerFactory(telegram_user_id=777777)


@pytest.mark.django_db
class TestNotificationAPI:
    """Tests for /api/notifications/ endpoints."""

    list_url = '/api/notifications/'

    def test_list_notifications_by_telegram_id(self, api_client, customer):
        NotificationFactory(customer=customer, title='Customer Alert')
        NotificationFactory()  # Other customer

        response = api_client.get(f'{self.list_url}?telegram_user_id={customer.telegram_user_id}')
        assert response.status_code == status.HTTP_200_OK
        results = response.json().get('results', response.json())
        assert len(results) == 1
        assert results[0]['title'] == 'Customer Alert'

    def test_list_notifications_staff(self, api_client, staff_user):
        NotificationFactory()
        NotificationFactory()
        api_client.force_authenticate(user=staff_user)

        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] >= 2

    def test_mark_as_read(self, api_client, customer):
        n = NotificationFactory(customer=customer, is_read=False)

        response = api_client.post(f'{self.list_url}{n.id}/read/')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['is_read'] is True

        n.refresh_from_db()
        assert n.is_read is True
