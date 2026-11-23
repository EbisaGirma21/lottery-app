"""
Handler for /my_tickets and ticket portfolio viewing.
"""
from datetime import timedelta
from asgiref.sync import sync_to_async
from django.db.models import Q
from django.utils import timezone
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from apps.lotteries.models import Customer, LotteryStatus
from apps.payments.models import Payment, PaymentStatus
from apps.reservations.models import Reservation, ReservationStatus
from apps.tickets.models import Ticket, TicketStatus
from apps.telegram_bot.formatters import format_my_tickets
from apps.telegram_bot.keyboards import main_menu_reply_keyboard


def sync_get_customer_portfolio(telegram_user_id: int):
    """
    Retrieve active reservations, pending reviews, and confirmed tickets for active lotteries.
    Once a lottery is drawn and the winners are known, tickets remain visible for 48 hours.
    After 48 hours, already drawn lottery tickets are excluded from My Tickets.
    """
    customer = Customer.objects.filter(telegram_user_id=telegram_user_id).first()
    if not customer:
        return [], [], []

    now = timezone.now()
    draw_visible_cutoff = now - timedelta(hours=48)

    # Active lotteries:
    # 1. Not drawn yet (OPEN, PAUSED, CLOSED, DRAFT)
    # 2. Drawn within the last 48 hours (DRAWN or COMPLETED with executed_at >= cutoff)
    active_or_recent_draw_q = (
        Q(lottery__status__in=[LotteryStatus.OPEN, LotteryStatus.PAUSED, LotteryStatus.CLOSED, LotteryStatus.DRAFT])
        | (
            Q(lottery__status__in=[LotteryStatus.DRAWN, LotteryStatus.COMPLETED])
            & (
                Q(lottery__draw__executed_at__gte=draw_visible_cutoff)
                | (Q(lottery__draw__isnull=True) & Q(lottery__updated_at__gte=draw_visible_cutoff))
            )
        )
    )

    active_res = list(
        Reservation.objects.filter(
            customer=customer,
            status=ReservationStatus.ACTIVE,
            lottery__status__in=[LotteryStatus.OPEN, LotteryStatus.PAUSED],
        )
        .select_related('lottery', 'ticket')
        .order_by('-reserved_at')
    )

    pending_payments = list(
        Payment.objects.filter(
            customer=customer,
            status=PaymentStatus.PENDING,
            lottery__status__in=[LotteryStatus.OPEN, LotteryStatus.PAUSED, LotteryStatus.CLOSED],
        )
        .order_by('-submitted_at')
    )

    sold_tickets = list(
        Ticket.objects.filter(
            customer=customer,
            status__in=[TicketStatus.SOLD, TicketStatus.WINNER],
        )
        .filter(active_or_recent_draw_q)
        .select_related('lottery', 'lottery__draw')
        .order_by('-updated_at')
    )

    return active_res, pending_payments, sold_tickets


async def my_tickets_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /my_tickets or text menu click."""
    user = update.effective_user
    active_res, pending_payments, sold_tickets = await sync_to_async(
        sync_get_customer_portfolio
    )(user.id)

    msg = await sync_to_async(format_my_tickets)(active_res, pending_payments, sold_tickets)

    await update.effective_message.reply_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_reply_keyboard(),
    )
