"""
Reports and analytics generation services (Excel, PDF, and dashboard metrics).
"""
from decimal import Decimal
import io
from typing import Optional

from django.db.models import Count, Sum
from django.utils import timezone
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.lotteries.models import Lottery, LotteryStatus
from apps.payments.models import Payment, PaymentMethod, PaymentStatus
from apps.tickets.models import Ticket, TicketStatus
from apps.winners.models import Winner


def generate_lottery_sales_excel(lottery: Lottery) -> io.BytesIO:
    """
    Generate a styled Excel (.xlsx) workbook for a specific lottery:
    Sheet 1: Executive KPI overview & configuration.
    Sheet 2: Complete ticket inventory and sales ledger.
    """
    wb = openpyxl.Workbook()

    # Style presets
    header_fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    title_font = Font(name='Calibri', size=16, bold=True, color='1E3A8A')
    bold_font = Font(name='Calibri', size=11, bold=True)
    regular_font = Font(name='Calibri', size=11)
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1'),
    )

    # -------------------------------------------------------------
    # Sheet 1: Overview
    # -------------------------------------------------------------
    ws_summary = wb.active
    ws_summary.title = 'Lottery Overview'

    ws_summary['A1'] = f'LOTTERY SALES REPORT: {lottery.name}'
    ws_summary['A1'].font = title_font
    ws_summary['A2'] = f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")}'
    ws_summary['A2'].font = Font(italic=True, color='64748B')

    # Metrics calculation
    total_tickets = lottery.total_numbers
    sold_count = lottery.tickets.filter(status__in=[TicketStatus.SOLD, TicketStatus.WINNER]).count()
    reserved_count = lottery.tickets.filter(status=TicketStatus.RESERVED).count()
    available_count = lottery.tickets.filter(status=TicketStatus.AVAILABLE).count()
    sell_through = (sold_count / total_tickets * 100) if total_tickets > 0 else 0
    total_revenue = Decimal(str(lottery.ticket_price)) * sold_count

    overview_data = [
        ('Configuration', ''),
        ('Lottery Status', lottery.get_status_display()),
        ('Ticket Price (ETB)', f'{lottery.ticket_price:,.2f}'),
        ('Total Ticket Capacity', f'{total_tickets:,}'),
        ('Start Date', lottery.start_date.strftime('%Y-%m-%d %H:%M')),
        ('Closing Date', lottery.closing_date.strftime('%Y-%m-%d %H:%M')),
        ('Draw Date', lottery.draw_date.strftime('%Y-%m-%d %H:%M')),
        ('', ''),
        ('Sales Performance', ''),
        ('Tickets Sold', f'{sold_count:,}'),
        ('Tickets Reserved', f'{reserved_count:,}'),
        ('Tickets Available', f'{available_count:,}'),
        ('Sell-Through Rate', f'{sell_through:.1f}%'),
        ('Total Sales Revenue (ETB)', f'{total_revenue:,.2f}'),
    ]

    row_idx = 4
    for label, val in overview_data:
        cell_a = ws_summary.cell(row=row_idx, column=1, value=label)
        cell_b = ws_summary.cell(row=row_idx, column=2, value=val)
        if label in ('Configuration', 'Sales Performance'):
            cell_a.font = Font(name='Calibri', size=13, bold=True, color='1E3A8A')
        else:
            cell_a.font = bold_font
            cell_b.font = regular_font
            if label != '':
                cell_a.border = thin_border
                cell_b.border = thin_border
        row_idx += 1

    ws_summary.column_dimensions['A'].width = 30
    ws_summary.column_dimensions['B'].width = 35

    # -------------------------------------------------------------
    # Sheet 2: Ticket Ledger
    # -------------------------------------------------------------
    ws_ledger = wb.create_sheet(title='Ticket Inventory')

    headers = [
        'Ticket #', 'Status', 'Customer Name', 'Phone Number',
        'Telegram Username', 'Telegram ID', 'Payment Ref', 'Updated At',
    ]

    for col_num, header in enumerate(headers, 1):
        cell = ws_ledger.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    tickets = (
        lottery.tickets
        .select_related('customer')
        .prefetch_related('reservations__payments')
        .order_by('ticket_number')
    )

    for row_num, ticket in enumerate(tickets, 2):
        cust = ticket.customer
        name = cust.full_name if cust else '—'
        phone = cust.phone_number if cust else '—'
        username = cust.telegram_username if cust else '—'
        tg_id = cust.telegram_user_id if cust else '—'

        # Payment ref
        payment_ref = '—'
        if cust and ticket.status in (TicketStatus.SOLD, TicketStatus.WINNER):
            # Check for approved payment
            p = Payment.objects.filter(customer=cust, lottery=lottery, status=PaymentStatus.APPROVED).first()
            if p:
                payment_ref = p.transaction_reference

        row_values = [
            ticket.ticket_number,
            ticket.get_status_display(),
            name,
            phone,
            username,
            str(tg_id),
            payment_ref,
            ticket.updated_at.strftime('%Y-%m-%d %H:%M'),
        ]

        for col_num, val in enumerate(row_values, 1):
            cell = ws_ledger.cell(row=row_num, column=col_num, value=val)
            cell.font = regular_font
            cell.border = thin_border
            if col_num in (1, 2, 6, 8):
                cell.alignment = Alignment(horizontal='center')

    # Auto-fit columns
    for col in ws_ledger.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_ledger.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def generate_financial_revenue_excel(start_date=None, end_date=None) -> io.BytesIO:
    """
    Generate an Excel (.xlsx) financial reconciliation report:
    Sheet 1: Revenue breakdown by payment method.
    Sheet 2: Ledger of all approved payment transactions.
    """
    wb = openpyxl.Workbook()

    header_fill = PatternFill(start_color='0F766E', end_color='0F766E', fill_type='solid')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    title_font = Font(name='Calibri', size=16, bold=True, color='0F766E')
    bold_font = Font(name='Calibri', size=11, bold=True)
    regular_font = Font(name='Calibri', size=11)
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1'),
    )

    # Base query for approved payments
    payments_qs = Payment.objects.filter(status=PaymentStatus.APPROVED).select_related('customer', 'lottery', 'reviewed_by')
    if start_date:
        payments_qs = payments_qs.filter(submitted_at__gte=start_date)
    if end_date:
        payments_qs = payments_qs.filter(submitted_at__lte=end_date)

    total_revenue = payments_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # -------------------------------------------------------------
    # Sheet 1: Payment Method Summary
    # -------------------------------------------------------------
    ws_summary = wb.active
    ws_summary.title = 'Revenue by Channel'

    ws_summary['A1'] = 'FINANCIAL RECONCILIATION REPORT'
    ws_summary['A1'].font = title_font
    ws_summary['A2'] = f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")} | Total Revenue: ETB {total_revenue:,.2f}'
    ws_summary['A2'].font = Font(italic=True, color='64748B')

    headers_s1 = ['Payment Method', 'Transactions', 'Revenue (ETB)', 'Revenue Share']
    for col_num, h in enumerate(headers_s1, 1):
        c = ws_summary.cell(row=4, column=col_num, value=h)
        c.fill = header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal='center')

    row_idx = 5
    for method_code, method_label in PaymentMethod.choices:
        qs_method = payments_qs.filter(payment_method=method_code)
        count = qs_method.count()
        rev = qs_method.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        pct = (rev / total_revenue * 100) if total_revenue > 0 else 0

        row = [method_label, count, f'{rev:,.2f}', f'{pct:.1f}%']
        for col_num, val in enumerate(row, 1):
            cell = ws_summary.cell(row=row_idx, column=col_num, value=val)
            cell.font = regular_font
            cell.border = thin_border
            if col_num in (2, 3, 4):
                cell.alignment = Alignment(horizontal='right')
        row_idx += 1

    # Total row
    total_row = ['Total', payments_qs.count(), f'{total_revenue:,.2f}', '100.0%']
    for col_num, val in enumerate(total_row, 1):
        cell = ws_summary.cell(row=row_idx, column=col_num, value=val)
        cell.font = bold_font
        cell.border = thin_border
        if col_num in (2, 3, 4):
            cell.alignment = Alignment(horizontal='right')

    for col in ws_summary.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_summary.column_dimensions[col_letter].width = max(max_len + 4, 15)

    # -------------------------------------------------------------
    # Sheet 2: Transactions Ledger
    # -------------------------------------------------------------
    ws_txns = wb.create_sheet(title='Transactions Ledger')
    headers_s2 = [
        'Transaction Ref', 'Payment Method', 'Customer Name', 'Phone Number',
        'Lottery', 'Amount (ETB)', 'Reviewed By', 'Reviewed At',
    ]

    for col_num, h in enumerate(headers_s2, 1):
        c = ws_txns.cell(row=1, column=col_num, value=h)
        c.fill = header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal='center')

    for row_num, p in enumerate(payments_qs.order_by('-reviewed_at'), 2):
        reviewer = p.reviewed_by.full_name if p.reviewed_by else '—'
        rev_at = p.reviewed_at.strftime('%Y-%m-%d %H:%M') if p.reviewed_at else '—'

        row = [
            p.transaction_reference,
            p.get_payment_method_display(),
            p.customer.full_name,
            p.customer.phone_number,
            p.lottery.name,
            f'{p.amount:,.2f}',
            reviewer,
            rev_at,
        ]
        for col_num, val in enumerate(row, 1):
            cell = ws_txns.cell(row=row_num, column=col_num, value=val)
            cell.font = regular_font
            cell.border = thin_border
            if col_num in (1, 2, 6, 8):
                cell.alignment = Alignment(horizontal='center')

    for col in ws_txns.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_txns.column_dimensions[col_letter].width = max(max_len + 3, 14)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def generate_lottery_summary_pdf(lottery: Lottery) -> io.BytesIO:
    """
    Generate an executive PDF summary report using ReportLab.
    Includes KPI summary, sales rates, and prize winners table.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15,
    )
    section_style = ParagraphStyle(
        'DocSection',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=12,
        spaceAfter=8,
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        fontName='Helvetica-Bold',
    )

    elements = []

    # Title & Header
    elements.append(Paragraph(f'Lottery Performance Report: {lottery.name}', title_style))
    elements.append(Paragraph(
        f'Generated on {timezone.now().strftime("%B %d, %Y at %H:%M UTC")} | Status: <b>{lottery.get_status_display()}</b>',
        subtitle_style,
    ))

    # Metrics computation
    total_tickets = lottery.total_numbers
    sold_count = lottery.tickets.filter(status__in=[TicketStatus.SOLD, TicketStatus.WINNER]).count()
    sell_through = (sold_count / total_tickets * 100) if total_tickets > 0 else 0
    total_revenue = Decimal(str(lottery.ticket_price)) * sold_count

    # KPI Table
    kpi_data = [
        [
            Paragraph('<b>Ticket Price</b>', cell_bold),
            Paragraph(f'ETB {lottery.ticket_price:,.2f}', cell_style),
            Paragraph('<b>Total Capacity</b>', cell_bold),
            Paragraph(f'{total_tickets:,} tickets', cell_style),
        ],
        [
            Paragraph('<b>Tickets Sold</b>', cell_bold),
            Paragraph(f'{sold_count:,} ({sell_through:.1f}%)', cell_style),
            Paragraph('<b>Total Revenue</b>', cell_bold),
            Paragraph(f'ETB {total_revenue:,.2f}', cell_style),
        ],
        [
            Paragraph('<b>Closing Date</b>', cell_bold),
            Paragraph(lottery.closing_date.strftime('%Y-%m-%d %H:%M'), cell_style),
            Paragraph('<b>Draw Date</b>', cell_bold),
            Paragraph(lottery.draw_date.strftime('%Y-%m-%d %H:%M'), cell_style),
        ],
    ]

    t_kpi = Table(kpi_data, colWidths=[110, 160, 110, 160])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_kpi)
    elements.append(Spacer(1, 15))

    # Prizes & Winners Section
    elements.append(Paragraph('Prizes & Draw Winners', section_style))

    winners = list(Winner.objects.filter(lottery=lottery).select_related('ticket', 'customer').order_by('position'))

    prize_headers = [
        Paragraph('<b>Position</b>', cell_bold),
        Paragraph('<b>Prize Name</b>', cell_bold),
        Paragraph('<b>Value (ETB)</b>', cell_bold),
        Paragraph('<b>Winning Ticket</b>', cell_bold),
        Paragraph('<b>Winner Name</b>', cell_bold),
        Paragraph('<b>Claim Status</b>', cell_bold),
    ]
    prize_rows = [prize_headers]

    prizes_info = [
        (1, '1st Prize', lottery.first_prize_name, lottery.first_prize_value),
        (2, '2nd Prize', lottery.second_prize_name, lottery.second_prize_value),
        (3, '3rd Prize', lottery.third_prize_name, lottery.third_prize_value),
    ]

    for pos, pos_name, p_name, p_val in prizes_info:
        w = next((x for x in winners if x.position == pos), None)
        ticket_str = f'#{w.ticket.ticket_number}' if w else 'Pending Draw'
        winner_name = w.masked_customer_name if w else '—'
        claim_str = w.get_claim_status_display() if w else '—'

        prize_rows.append([
            Paragraph(pos_name, cell_bold),
            Paragraph(p_name, cell_style),
            Paragraph(f'{p_val:,.2f}', cell_style),
            Paragraph(ticket_str, cell_style),
            Paragraph(winner_name, cell_style),
            Paragraph(claim_str, cell_style),
        ])

    t_prizes = Table(prize_rows, colWidths=[65, 120, 85, 80, 105, 85])
    t_prizes.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))
    elements.append(t_prizes)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def get_dashboard_analytics() -> dict:
    """
    Compute real-time dashboard analytics and executive summaries.
    """
    total_lotteries = Lottery.objects.count()
    active_lotteries = Lottery.objects.filter(status=LotteryStatus.OPEN).count()
    closed_lotteries = Lottery.objects.filter(status=LotteryStatus.CLOSED).count()
    drawn_lotteries = Lottery.objects.filter(status__in=[LotteryStatus.DRAWN, LotteryStatus.COMPLETED]).count()

    total_tickets = Ticket.objects.count()
    sold_tickets = Ticket.objects.filter(status__in=[TicketStatus.SOLD, TicketStatus.WINNER]).count()
    reserved_tickets = Ticket.objects.filter(status=TicketStatus.RESERVED).count()

    approved_payments = Payment.objects.filter(status=PaymentStatus.APPROVED)
    total_revenue = approved_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    pending_payments = Payment.objects.filter(status=PaymentStatus.PENDING)
    pending_count = pending_payments.count()
    pending_amount = pending_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Breakdown by payment method
    by_channel = []
    for code, label in PaymentMethod.choices:
        qs = approved_payments.filter(payment_method=code)
        cnt = qs.count()
        amt = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        by_channel.append({
            'code': code,
            'label': label,
            'count': cnt,
            'amount': str(amt),
        })

    # Recent activity
    recent_payments = []
    for p in Payment.objects.select_related('customer', 'lottery').order_by('-submitted_at')[:6]:
        c = p.customer
        l = p.lottery
        recent_payments.append({
            'id': str(p.id),
            'transaction_reference': p.transaction_reference,
            'amount': str(p.amount),
            'payment_method': p.payment_method,
            'status': p.status,
            'submitted_at': p.submitted_at.isoformat() if p.submitted_at else (p.created_at.isoformat() if p.created_at else None),
            'reviewed_at': p.reviewed_at.isoformat() if p.reviewed_at else None,
            'customer': {
                'id': str(c.id) if c else '',
                'full_name': c.full_name if c else 'Anonymous',
                'phone_number': c.phone_number if c else '—',
                'telegram_username': c.telegram_username if c else '',
            } if c else None,
            'customer__full_name': c.full_name if c else 'Anonymous',
            'lottery': {
                'id': str(l.id) if l else '',
                'name': l.name if l else 'Lottery',
            } if l else None,
            'lottery__name': l.name if l else 'Lottery',
        })

    recent_winners = []
    for w in Winner.objects.select_related('lottery', 'ticket', 'customer').order_by('-created_at')[:5]:
        c = w.customer
        l = w.lottery
        t = w.ticket
        recent_winners.append({
            'id': str(w.id),
            'position': w.position,
            'prize_name': w.prize_name,
            'prize_value': str(w.prize_value),
            'ticket': {
                'ticket_number': t.ticket_number if t else '—',
            } if t else None,
            'ticket__ticket_number': t.ticket_number if t else '—',
            'customer': {
                'full_name': c.full_name if c else 'Anonymous',
            } if c else None,
            'customer__full_name': c.full_name if c else 'Anonymous',
            'lottery': {
                'name': l.name if l else 'Lottery',
            } if l else None,
            'lottery__name': l.name if l else 'Lottery',
            'created_at': w.created_at.isoformat() if w.created_at else None,
        })

    return {
        'lotteries': {
            'total': total_lotteries,
            'active': active_lotteries,
            'closed': closed_lotteries,
            'drawn': drawn_lotteries,
        },
        'tickets': {
            'total': total_tickets,
            'sold': sold_tickets,
            'reserved': reserved_tickets,
            'sell_through_rate': f'{(sold_tickets / total_tickets * 100):.1f}%' if total_tickets > 0 else '0.0%',
        },
        'financials': {
            'total_revenue': str(total_revenue),
            'pending_verifications_count': pending_count,
            'pending_verifications_amount': str(pending_amount),
            'revenue_by_channel': by_channel,
        },
        'recent_payments': recent_payments,
        'recent_winners': recent_winners,
    }
