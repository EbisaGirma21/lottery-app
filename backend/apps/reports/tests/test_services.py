"""
Tests for reports generation services (Excel, PDF, dashboard metrics).
"""
from decimal import Decimal
import io
import pytest
import openpyxl

from apps.lotteries.models import LotteryStatus
from apps.lotteries.services import generate_tickets_for_lottery
from apps.lotteries.tests.factories import CustomerFactory, LotteryFactory
from apps.payments.models import PaymentMethod, PaymentStatus
from apps.payments.tests.factories import PaymentFactory
from apps.reports.services import (
    generate_financial_revenue_excel,
    generate_lottery_sales_excel,
    generate_lottery_summary_pdf,
    get_dashboard_analytics,
)
from apps.tickets.models import Ticket, TicketStatus


@pytest.fixture
def lottery():
    lottery = LotteryFactory(
        name='Big Year Lottery',
        status=LotteryStatus.OPEN,
        total_numbers=50,
        ticket_price=Decimal('100.00'),
    )
    generate_tickets_for_lottery(lottery)
    customer = CustomerFactory(full_name='Test Buyer', phone_number='+251911223344')
    # Mark 5 tickets as sold
    for t in Ticket.objects.filter(lottery=lottery)[:5]:
        t.status = TicketStatus.SOLD
        t.customer = customer
        t.save()
    return lottery


@pytest.mark.django_db
class TestReportServices:
    """Tests for report generation logic."""

    def test_generate_lottery_sales_excel(self, lottery):
        buffer = generate_lottery_sales_excel(lottery)
        assert isinstance(buffer, io.BytesIO)
        assert buffer.getbuffer().nbytes > 0

        # Parse generated workbook
        wb = openpyxl.load_workbook(buffer)
        assert 'Lottery Overview' in wb.sheetnames
        assert 'Ticket Inventory' in wb.sheetnames

        ws_overview = wb['Lottery Overview']
        assert 'Big Year Lottery' in str(ws_overview['A1'].value)

        ws_tickets = wb['Ticket Inventory']
        headers = [cell.value for cell in ws_tickets[1]]
        assert 'Ticket #' in headers
        assert 'Status' in headers
        assert 'Customer Name' in headers

    def test_generate_financial_revenue_excel(self, lottery):
        PaymentFactory(payment_method=PaymentMethod.TELEBIRR, status=PaymentStatus.APPROVED, amount=Decimal('500.00'))
        PaymentFactory(payment_method=PaymentMethod.CBE, status=PaymentStatus.APPROVED, amount=Decimal('1500.00'))

        buffer = generate_financial_revenue_excel()
        assert isinstance(buffer, io.BytesIO)
        assert buffer.getbuffer().nbytes > 0

        wb = openpyxl.load_workbook(buffer)
        assert 'Revenue by Channel' in wb.sheetnames
        assert 'Transactions Ledger' in wb.sheetnames

        ws_summary = wb['Revenue by Channel']
        assert 'FINANCIAL RECONCILIATION REPORT' in str(ws_summary['A1'].value)

    def test_generate_lottery_summary_pdf(self, lottery):
        buffer = generate_lottery_summary_pdf(lottery)
        assert isinstance(buffer, io.BytesIO)
        pdf_bytes = buffer.getvalue()
        assert len(pdf_bytes) > 0
        # Valid PDF files begin with %PDF
        assert pdf_bytes.startswith(b'%PDF')

    def test_get_dashboard_analytics(self, lottery):
        PaymentFactory(payment_method=PaymentMethod.TELEBIRR, status=PaymentStatus.APPROVED, amount=Decimal('250.00'))
        PaymentFactory(status=PaymentStatus.PENDING, amount=Decimal('100.00'))

        data = get_dashboard_analytics()

        assert 'lotteries' in data
        assert data['lotteries']['total'] >= 1
        assert data['lotteries']['active'] >= 1

        assert 'tickets' in data
        assert data['tickets']['sold'] >= 5

        assert 'financials' in data
        assert Decimal(data['financials']['total_revenue']) >= Decimal('250.00')
        assert data['financials']['pending_verifications_count'] >= 1
        assert len(data['financials']['revenue_by_channel']) == len(PaymentMethod.choices)

        assert 'recent_payments' in data
        assert 'recent_winners' in data
