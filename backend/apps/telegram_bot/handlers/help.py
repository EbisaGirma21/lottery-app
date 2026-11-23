"""
Handler for /help command and general user guide.
"""
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from apps.telegram_bot.formatters import format_help
from apps.telegram_bot.keyboards import main_menu_reply_keyboard


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /help or text menu click."""
    msg = format_help()
    await update.effective_message.reply_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_reply_keyboard(),
    )
