"""
Telegram Customer Bot Application Factory.
Configures and registers all conversation handlers and commands.
"""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from apps.telegram_bot.config import get_bot_token
from apps.telegram_bot.handlers.help import help_handler
from apps.telegram_bot.handlers.lotteries import list_lotteries_handler, lottery_callback_handler
from apps.telegram_bot.handlers.my_tickets import my_tickets_handler
from apps.telegram_bot.handlers.payments import get_payment_conversation_handler
from apps.telegram_bot.handlers.start import (
    contact_handler,
    skip_contact_handler,
    start_handler,
)
from apps.telegram_bot.handlers.winners import winners_handler

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and notify the user gracefully."""
    logger.error("Exception while handling an update: %s", context.error, exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An unexpected error occurred while processing your request. "
                "Our engineers have been alerted. Please try again in a moment."
            )
        except Exception:
            pass


def build_bot_application(token: str = None) -> Application:
    """
    Constructs and configures the python-telegram-bot Application.
    """
    bot_token = token if token is not None else get_bot_token()
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is not configured in settings or environment.")

    application = ApplicationBuilder().token(bot_token).build()

    # 1. Start & Registration
    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    application.add_handler(MessageHandler(filters.Regex('^Skip for now$'), skip_contact_handler))

    # 2. Lotteries & Dynamic Tickets Browser
    application.add_handler(CommandHandler('lotteries', list_lotteries_handler))
    application.add_handler(MessageHandler(filters.Regex('^🎟️ Active Lotteries$'), list_lotteries_handler))
    application.add_handler(
        CallbackQueryHandler(
            lottery_callback_handler,
            pattern=r'^(list_lotteries|lottery:|tickets:|pick:|quick_pick:|confirm_reserve:|noop)',
        )
    )

    # 3. Manual Payment Submission (ConversationHandler)
    application.add_handler(get_payment_conversation_handler())

    # 4. My Tickets Portfolio
    application.add_handler(CommandHandler('my_tickets', my_tickets_handler))
    application.add_handler(MessageHandler(filters.Regex('^🎫 My Tickets$'), my_tickets_handler))

    # 5. Winners
    application.add_handler(CommandHandler('winners', winners_handler))
    application.add_handler(MessageHandler(filters.Regex('^🏆 (Draw Results|Draw Winners|View Winners)$'), winners_handler))

    # 6. Help & Info
    application.add_handler(CommandHandler('help', help_handler))
    application.add_handler(MessageHandler(filters.Regex('^ℹ️ Help & Info$'), help_handler))

    # 7. Global Error Handler
    application.add_error_handler(error_handler)

    return application
