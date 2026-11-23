"""
Tests for Payment API endpoints: submit, queue listing, approve, reject, stats, my-payments.
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
from apps.lotteries.models import CustomerStatus, LotteryStatus
from apps.lotteries.services import generate_tickets_for_lottery
from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory
from apps.payments.models import PaymentMethod, PaymentStatus
from apps.payments.services import submit_payment
from apps.payments.tests.factories import PaymentFactory
from apps.reservations.services import reserve_tickets
from apps.tickets.models import Ticket, TicketStatus


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def open_lottery():
    lottery = LotteryFactory(status=LotteryStatus.OPEN, ticket_price=Decimal('50.00'), total_numbers=100)
    generate_tickets_for_lottery(lottery)
    return lottery


@pytest.fixture
def customer():
    return CustomerFactory(status=CustomerStatus.ACTIVE, telegram_user_id=888888)


@pytest.fixture
def payment_officer():
    return PaymentOfficerFactory()


@pytest.fixture
def super_admin():
    return SuperAdminFactory()


@pytest.fixture
def lottery_manager():
    return LotteryManagerFactory()


@pytest.fixture
def viewer():
    return ViewerFactory()


@pytest.fixture
def draw_officer():
    return DrawOfficerFactory()


@pytest.mark.django_db
class TestPaymentSubmissionAPI:
    """Tests for POST /api/payments/submit/"""

    submit_url = '/api/payments/submit/'

    def test_submit_payment_with_telegram_id(self, api_client, open_lottery, customer):
        res = reserve_tickets(customer, open_lottery, ['001'])

        payload = {
            'lottery_id': str(open_lottery.id),
            'reservation_ids': [str(r.id) for r in res],
            'payment_method': PaymentMethod.TELEBIRR,
            'transaction_reference': 'API-TXN-001',
            'amount': '50.00',
            'telegram_user_id': customer.telegram_user_id,
        }

        response = api_client.post(self.submit_url, payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['transaction_reference'] == 'API-TXN-001'
        assert data['status'] == PaymentStatus.PENDING
        assert len(data['reservations']) == 1

    def test_submit_payment_with_customer_id(self, api_client, open_lottery, customer):
        res = reserve_tickets(customer, open_lottery, ['002'])

        payload = {
            'lottery_id': str(open_lottery.id),
            'reservation_ids': [str(r.id) for r in res],
            'payment_method': PaymentMethod.CBE,
            'transaction_reference': 'API-CBE-002',
            'amount': '50.00',
            'customer_id': str(customer.id),
        }

        response = api_client.post(self.submit_url, payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['payment_method'] == 'cbe'

    def test_submit_payment_missing_customer_identifier_fails(self, api_client, open_lottery):
        payload = {
            'lottery_id': str(open_lottery.id),
            'reservation_ids': [],
            'payment_method': PaymentMethod.TELEBIRR,
            'transaction_reference': 'API-FAIL-003',
            'amount': '50.00',
        }
        response = api_client.post(self.submit_url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_submit_duplicate_reference_fails(self, api_client, open_lottery, customer):
        PaymentFactory(transaction_reference='EXISTING-REF-99')

        res = reserve_tickets(customer, open_lottery, ['003'])

        payload = {
            'lottery_id': str(open_lottery.id),
            'reservation_ids': [str(r.id) for r in res],
            'payment_method': PaymentMethod.TELEBIRR,
            'transaction_reference': 'EXISTING-REF-99',
            'amount': '50.00',
            'customer_id': str(customer.id),
        }
        response = api_client.post(self.submit_url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPaymentQueueAPI:
    """Tests for staff payment queue listing and retrieval."""

    list_url = '/api/payments/'

    def test_unauthenticated_cannot_access_queue(self, api_client):
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_payment_officer_can_view_queue(self, api_client, payment_officer):
        PaymentFactory()
        PaymentFactory()
        api_client.force_authenticate(user=payment_officer)

        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] >= 2

    def test_filter_by_status(self, api_client, payment_officer):
        PaymentFactory(status=PaymentStatus.PENDING)
        PaymentFactory(status=PaymentStatus.APPROVED)
        api_client.force_authenticate(user=payment_officer)

        response = api_client.get(f'{self.list_url}?status=pending')
        assert response.status_code == status.HTTP_200_OK
        for item in response.json()['results']:
            assert item['status'] == 'pending'

    def test_retrieve_payment_detail(self, api_client, payment_officer, open_lottery, customer):
        res = reserve_tickets(customer, open_lottery, ['004'])
        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='DETAIL-TXN-01',
            amount=Decimal('50.00'),
        )

        api_client.force_authenticate(user=payment_officer)
        response = api_client.get(f'{self.list_url}{payment.id}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['id'] == str(payment.id)
        assert data['customer_name'] == customer.full_name
        assert len(data['reservations']) == 1


@pytest.mark.django_db
class TestPaymentApprovalAPI:
    """Tests for POST /api/payments/{id}/approve/"""

    def test_approve_as_payment_officer(self, api_client, payment_officer, open_lottery, customer):
        res = reserve_tickets(customer, open_lottery, ['005'])
        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='OFFICER-APPROVE',
            amount=Decimal('50.00'),
        )

        api_client.force_authenticate(user=payment_officer)
        response = api_client.post(
            f'/api/payments/{payment.id}/approve/',
            {'admin_notes': 'Checked SMS notification.'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'approved'

        # Ticket must now be SOLD
        ticket = Ticket.objects.get(lottery=open_lottery, ticket_number='005')
        assert ticket.status == TicketStatus.SOLD

    def test_approve_as_super_admin(self, api_client, super_admin, open_lottery, customer):
        res = reserve_tickets(customer, open_lottery, ['006'])
        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.CBE,
            transaction_reference='ADMIN-APPROVE',
            amount=Decimal('50.00'),
        )

        api_client.force_authenticate(user=super_admin)
        response = api_client.post(f'/api/payments/{payment.id}/approve/', {}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'approved'

    def test_approve_as_lottery_manager(self, api_client, lottery_manager, open_lottery, customer):
        res = reserve_tickets(customer, open_lottery, ['007'])
        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.AWASH,
            transaction_reference='MGR-APPROVE',
            amount=Decimal('50.00'),
        )

        api_client.force_authenticate(user=lottery_manager)
        response = api_client.post(f'/api/payments/{payment.id}/approve/', {}, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_viewer_cannot_approve(self, api_client, viewer, open_lottery, customer):
        res = reserve_tickets(customer, open_lottery, ['008'])
        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='VIEWER-FAIL',
            amount=Decimal('50.00'),
        )

        api_client.force_authenticate(user=viewer)
        response = api_client.post(f'/api/payments/{payment.id}/approve/', {}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_draw_officer_cannot_approve(self, api_client, draw_officer, open_lottery, customer):
        res = reserve_tickets(customer, open_lottery, ['009'])
        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='DRAW-FAIL',
            amount=Decimal('50.00'),
        )

        api_client.force_authenticate(user=draw_officer)
        response = api_client.post(f'/api/payments/{payment.id}/approve/', {}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestPaymentRejectionAPI:
    """Tests for POST /api/payments/{id}/reject/"""

    def test_reject_as_payment_officer(self, api_client, payment_officer, open_lottery, customer):
        res = reserve_tickets(customer, open_lottery, ['010'])
        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='OFFICER-REJECT',
            amount=Decimal('50.00'),
        )

        api_client.force_authenticate(user=payment_officer)
        response = api_client.post(
            f'/api/payments/{payment.id}/reject/',
            {'rejection_reason': 'Invalid transaction reference code.'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'rejected'

        # Ticket must now be AVAILABLE again
        ticket = Ticket.objects.get(lottery=open_lottery, ticket_number='010')
        assert ticket.status == TicketStatus.AVAILABLE

    def test_reject_without_reason_fails(self, api_client, payment_officer, open_lottery, customer):
        res = reserve_tickets(customer, open_lottery, ['011'])
        payment = submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='NO-REASON-FAIL',
            amount=Decimal('50.00'),
        )

        api_client.force_authenticate(user=payment_officer)
        response = api_client.post(f'/api/payments/{payment.id}/reject/', {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPaymentAuxiliaryAPI:
    """Tests for stats and my-payments endpoints."""

    def test_get_stats_authenticated(self, api_client, payment_officer):
        PaymentFactory(status=PaymentStatus.PENDING)
        PaymentFactory(status=PaymentStatus.APPROVED)
        api_client.force_authenticate(user=payment_officer)

        response = api_client.get('/api/payments/stats/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_payments'] >= 2
        assert 'approved_revenue' in data

    def test_my_payments_by_telegram_id(self, api_client, customer, open_lottery):
        res = reserve_tickets(customer, open_lottery, ['012'])
        submit_payment(
            customer=customer,
            lottery=open_lottery,
            reservation_ids=[str(res[0].id)],
            payment_method=PaymentMethod.TELEBIRR,
            transaction_reference='MY-PAY-01',
            amount=Decimal('50.00'),
        )

        response = api_client.get(f'/api/payments/my-payments/?telegram_user_id={customer.telegram_user_id}')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        results = data.get('results', data)
        assert len(results) >= 1
        assert results[0]['transaction_reference'] == 'MY-PAY-01'
