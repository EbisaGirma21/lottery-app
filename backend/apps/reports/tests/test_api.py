"""
Tests for Reports API endpoints: dashboard, excel downloads, pdf downloads.
"""
from decimal import Decimal
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import ViewerFactory
from apps.lotteries.models import LotteryStatus
from apps.lotteries.services import generate_tickets_for_lottery
from apps.lotteries.tests.factories import LotteryFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def staff_user():
    return ViewerFactory()


@pytest.fixture
def lottery():
    lottery = LotteryFactory(status=LotteryStatus.OPEN, total_numbers=30, ticket_price=Decimal('50.00'))
    generate_tickets_for_lottery(lottery)
    return lottery


@pytest.mark.django_db
class TestReportsAPI:
    """Tests for reports endpoints."""

    def test_dashboard_unauthenticated_forbidden(self, api_client):
        response = api_client.get('/api/reports/dashboard/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_dashboard_authenticated(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        response = api_client.get('/api/reports/dashboard/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'financials' in data
        assert 'lotteries' in data

    def test_export_lottery_sales_excel(self, api_client, staff_user, lottery):
        api_client.force_authenticate(user=staff_user)
        response = api_client.get(f'/api/reports/lotteries/{lottery.id}/export-excel/')
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert f'attachment; filename="lottery_{lottery.slug}_sales.xlsx"' in response['Content-Disposition']

    def test_export_financial_excel(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        response = api_client.get('/api/reports/financial/export-excel/')
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert 'attachment; filename="financial_revenue_report.xlsx"' in response['Content-Disposition']

    def test_export_lottery_summary_pdf(self, api_client, staff_user, lottery):
        api_client.force_authenticate(user=staff_user)
        response = api_client.get(f'/api/reports/lotteries/{lottery.id}/export-pdf/')
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/pdf'
        assert f'attachment; filename="lottery_{lottery.slug}_summary.pdf"' in response['Content-Disposition']
        assert response.content.startswith(b'%PDF')
