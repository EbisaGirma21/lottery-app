"""
Handler for /start command and customer contact registration.
"""
import logging
from asgiref.sync import sync_to_async
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from apps.lotteries.models import Customer
from apps.telegram_bot.formatters import format_welcome
from apps.telegram_bot.keyboards import contact_request_keyboard, main_menu_reply_keyboard

logger = logging.getLogger(__name__)


def sync_get_or_create_customer(tg_user, phone_number: str = None) -> Customer:
    """Get or create Customer record for Telegram user (sync helper)."""
    customer = Customer.objects.filter(telegram_user_id=tg_user.id).first()
    full_name = f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip()
    if not full_name:
        full_name = tg_user.username or f"Telegram User {tg_user.id}"

    if not customer:
        customer = Customer.objects.create(
            telegram_user_id=tg_user.id,
            telegram_username=tg_user.username or '',
            full_name=full_name,
            phone_number=phone_number or '',
        )
        logger.info("Registered new customer telegram_id=%s, name=%s", tg_user.id, full_name)
    else:
        changed = False
        if full_name and customer.full_name != full_name:
            customer.full_name = full_name
            changed = True
        if tg_user.username and customer.telegram_username != tg_user.username:
            customer.telegram_username = tg_user.username
            changed = True
        if phone_number and not customer.phone_number:
            customer.phone_number = phone_number
            changed = True
        if changed:
            customer.save()

    return customer


def sync_save_customer_phone(telegram_id: int, phone_number: str) -> bool:
    """Update customer phone number."""
    customer = Customer.objects.filter(telegram_user_id=telegram_id).first()
    if customer:
        customer.phone_number = phone_number
        customer.save(update_fields=['phone_number'])
        return True
    return False


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    user = update.effective_user
    if not user:
        return

    customer = await sync_to_async(sync_get_or_create_customer)(user)
    has_phone = bool(customer.phone_number)

    welcome_text = format_welcome(user.first_name or "Friend", has_phone=has_phone)

    # If customer doesn't have phone registered, present contact sharing keyboard
    if not has_phone:
        await update.effective_message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=contact_request_keyboard(),
        )
    else:
        await update.effective_message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_reply_keyboard(),
        )


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles phone contact shared by customer."""
    contact = update.effective_message.contact
    user = update.effective_user

    if contact and user:
        phone = contact.phone_number
        if not phone.startswith('+'):
            phone = f'+{phone}'

        await sync_to_async(sync_save_customer_phone)(user.id, phone)

        await update.effective_message.reply_text(
            f"✅ Thank you! Your phone number <b>{phone}</b> has been linked to your account.",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_reply_keyboard(),
        )


async def skip_contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles customer skipping phone sharing."""
    await update.effective_message.reply_text(
        "No problem! You can still browse lotteries and reserve tickets.",
        reply_markup=main_menu_reply_keyboard(),
    )
