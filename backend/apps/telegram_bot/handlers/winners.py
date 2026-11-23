"""
Handler for /winners command to browse winning draws.
"""
from asgiref.sync import sync_to_async
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from apps.draws.models import Draw
from apps.telegram_bot.formatters import format_winners
from apps.telegram_bot.keyboards import main_menu_reply_keyboard


def sync_get_recent_draws():
    """Fetch recent completed draws with winners."""
    return list(
        Draw.objects.select_related('lottery')
        .prefetch_related('winners', 'winners__ticket', 'winners__customer')
        .order_by('-executed_at')[:10]
    )


async def winners_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /winners or text menu click."""
    draws = await sync_to_async(sync_get_recent_draws)()
    msg = await sync_to_async(format_winners)(draws)

    await update.effective_message.reply_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_reply_keyboard(),
    )
