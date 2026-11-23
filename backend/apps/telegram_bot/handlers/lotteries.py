"""
Handlers for browsing lotteries and dynamic tickets.
"""
import logging
import math
from asgiref.sync import sync_to_async
from django.core.paginator import Paginator
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from apps.lotteries.models import Customer, Lottery, LotteryStatus
from apps.reservations.services import reserve_tickets, ReservationError
from apps.tickets.models import Ticket, TicketStatus
from apps.telegram_bot.config import TICKETS_PER_PAGE
from apps.telegram_bot.formatters import format_lottery_card, format_reservation_confirmed
from apps.telegram_bot.keyboards import (
    lotteries_inline_keyboard,
    lottery_detail_keyboard,
    reservation_confirmed_keyboard,
    ticket_grid_keyboard,
)

logger = logging.getLogger(__name__)


def sync_get_open_lotteries():
    """Retrieve list of currently open lotteries."""
    return list(Lottery.objects.filter(status=LotteryStatus.OPEN).order_by('-created_at'))


def sync_get_lottery(lottery_id):
    """Retrieve a single lottery by ID."""
    return Lottery.objects.filter(pk=lottery_id).first()


def sync_get_all_available_tickets(lottery_id: str, limit: int = 96):
    """
    Retrieve all available tickets for a lottery (shown in 4 columns down).
    Excludes any ticket that is reserved, sold, or in an active unexpired reservation.
    Capped at 96 to adhere to Telegram's 100-button limit per inline keyboard.
    """
    from django.utils import timezone
    from apps.reservations.models import Reservation, ReservationStatus

    active_reserved_ids = Reservation.objects.filter(
        lottery_id=lottery_id,
        status=ReservationStatus.ACTIVE,
        expires_at__gt=timezone.now(),
    ).values_list('ticket_id', flat=True)

    qs = (
        Ticket.objects
        .filter(lottery_id=lottery_id, status=TicketStatus.AVAILABLE)
        .exclude(id__in=active_reserved_ids)
        .order_by('ticket_number')
    )
    return list(qs[:limit])


def sync_get_available_tickets_page(lottery_id: str, page_number: int = 1, page_size: int = 8):
    """Retrieve a paginated page of available tickets."""
    qs = Ticket.objects.filter(
        lottery_id=lottery_id,
        status=TicketStatus.AVAILABLE,
    ).order_by('ticket_number')

    paginator = Paginator(qs, page_size)
    page_number = max(1, min(page_number, paginator.num_pages or 1))
    page_obj = paginator.get_page(page_number)
    return list(page_obj.object_list), page_obj.number, paginator.num_pages or 1


def sync_quick_pick_tickets(lottery_id: str, count: int):
    """Pick up to `count` available ticket numbers."""
    return list(
        Ticket.objects.filter(
            lottery_id=lottery_id,
            status=TicketStatus.AVAILABLE,
        )
        .values_list('ticket_number', flat=True)[:count]
    )


def sync_execute_reservation(telegram_user_id: int, lottery_id: str, ticket_numbers: list):
    """Execute atomic reservation using reservations service."""
    customer = Customer.objects.filter(telegram_user_id=telegram_user_id).first()
    if not customer:
        raise ReservationError("Customer profile not found. Please type /start first.")

    lottery = Lottery.objects.filter(pk=lottery_id).first()
    if not lottery:
        raise ReservationError("Selected lottery does not exist.")

    reservations = reserve_tickets(customer, lottery, ticket_numbers)
    instructions = list(lottery.payment_instructions.filter(is_active=True))
    return reservations, instructions


async def list_lotteries_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /lotteries or text menu click."""
    lotteries = await sync_to_async(sync_get_open_lotteries)()

    if not lotteries:
        msg = (
            "🎟️ <b>Active Lotteries</b>\n\n"
            "There are currently no open lotteries accepting ticket purchases.\n"
            "Please check back soon!"
        )
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    msg = (
        "🎟️ <b>Active Lotteries</b>\n\n"
        "Select a lottery below to view prize details, available tickets, "
        "and pick your lucky numbers:"
    )
    reply_markup = lotteries_inline_keyboard(lotteries)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            msg,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )
    else:
        await update.effective_message.reply_text(
            msg,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )


async def lottery_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles inline callbacks for lotteries, tickets, and quick pick."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'list_lotteries':
        await list_lotteries_handler(update, context)
        return

    if data == 'noop':
        return

    if data.startswith('lottery:'):
        lottery_id = data.split(':', 1)[1]
        lottery = await sync_to_async(sync_get_lottery)(lottery_id)
        if not lottery:
            await query.edit_message_text("Lottery not found.")
            return

        text = await sync_to_async(format_lottery_card)(lottery)
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=lottery_detail_keyboard(str(lottery.id)),
        )
        return

    if data.startswith('tickets:'):
        parts = data.split(':')
        lottery_id = parts[1]
        context.user_data['current_lottery_id'] = lottery_id

        # Retrieve selection from user_data
        key = f'selected_{lottery_id}'
        selected_ids = context.user_data.setdefault(key, set())

        tickets = await sync_to_async(sync_get_all_available_tickets)(lottery_id)

        if not tickets:
            await query.edit_message_text(
                "⚠️ There are currently no available tickets for this lottery (all tickets may be reserved or sold).",
                reply_markup=lottery_detail_keyboard(lottery_id),
            )
            return

        markup = ticket_grid_keyboard(
            lottery_id,
            tickets,
            selected_ids=selected_ids,
        )
        header = (
            f"🎫 <b>Pick Your Numbers</b> ({len(tickets)} available)\n"
            "All available numbers are shown below in 4 columns. "
            "Reserved numbers are hidden.\n"
            "Tap any number to select or deselect, then tap <b>'Confirm Reservation'</b> below:\n"
        )
        await query.edit_message_text(
            header,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )
        return

    if data.startswith('pick:'):
        parts = data.split(':')
        # Format can be pick:ticket_id, pick:ticket_id:page, or pick:lottery_id:ticket_id:page
        if len(parts) == 2:
            ticket_id = parts[1]
        elif len(parts) == 3:
            ticket_id = parts[1]
        else:
            ticket_id = parts[2]

        lottery_id = context.user_data.get('current_lottery_id')
        if not lottery_id:
            lottery_id = await sync_to_async(
                lambda: str(Ticket.objects.filter(id=ticket_id).values_list('lottery_id', flat=True).first())
            )()

        context.user_data['current_lottery_id'] = lottery_id
        key = f'selected_{lottery_id}'
        selected_ids = context.user_data.setdefault(key, set())

        if ticket_id in selected_ids:
            selected_ids.remove(ticket_id)
        else:
            selected_ids.add(ticket_id)

        tickets = await sync_to_async(sync_get_all_available_tickets)(lottery_id)

        markup = ticket_grid_keyboard(
            lottery_id,
            tickets,
            selected_ids=selected_ids,
        )
        header = (
            f"🎫 <b>Pick Your Numbers</b> ({len(selected_ids)} selected)\n"
            "All available numbers in 4 columns. Reserved numbers are hidden.\n"
            "Tap any number to select or deselect. When ready, tap <b>'Confirm Reservation'</b>:"
        )
        try:
            await query.edit_message_text(
                header,
                parse_mode=ParseMode.HTML,
                reply_markup=markup,
            )
        except Exception:
            pass
        return

    if data.startswith('quick_pick:'):
        _, lottery_id, count_str = data.split(':')
        count = int(count_str)
        user = update.effective_user

        ticket_numbers = await sync_to_async(sync_quick_pick_tickets)(lottery_id, count)
        if not ticket_numbers:
            await query.edit_message_text(
                "⚠️ Not enough tickets available for quick pick.",
                reply_markup=lottery_detail_keyboard(lottery_id),
            )
            return

        try:
            reservations, instructions = await sync_to_async(sync_execute_reservation)(
                user.id, lottery_id, ticket_numbers
            )
            receipt_msg = await sync_to_async(format_reservation_confirmed)(reservations, instructions)
            await query.edit_message_text(
                receipt_msg,
                parse_mode=ParseMode.HTML,
                reply_markup=reservation_confirmed_keyboard(lottery_id),
            )
        except ReservationError as err:
            await query.edit_message_text(f"❌ Could not reserve: {str(err)}")
        return

    if data.startswith('confirm_reserve:'):
        lottery_id = data.split(':', 1)[1]
        user = update.effective_user
        key = f'selected_{lottery_id}'
        selected_ids = context.user_data.get(key, set())

        if not selected_ids:
            await query.answer("Please select at least one ticket number first!", show_alert=True)
            return

        # Fetch ticket numbers for selected IDs
        ticket_numbers = await sync_to_async(
            lambda: list(
                Ticket.objects.filter(id__in=selected_ids).values_list('ticket_number', flat=True)
            )
        )()

        try:
            reservations, instructions = await sync_to_async(sync_execute_reservation)(
                user.id, lottery_id, ticket_numbers
            )
            # Clear selection
            context.user_data.pop(key, None)
            receipt_msg = await sync_to_async(format_reservation_confirmed)(reservations, instructions)
            await query.edit_message_text(
                receipt_msg,
                parse_mode=ParseMode.HTML,
                reply_markup=reservation_confirmed_keyboard(lottery_id),
            )
        except ReservationError as err:
            await query.edit_message_text(
                f"❌ <b>Reservation Failed:</b> {str(err)}\n\n"
                "Please go back and select available tickets.",
                parse_mode=ParseMode.HTML,
                reply_markup=lottery_detail_keyboard(lottery_id),
            )
        return
