"""
Configuration and constants for Telegram Customer Bot.
"""
from django.conf import settings


def get_bot_token() -> str:
    """Retrieve the configured bot token."""
    return getattr(settings, 'TELEGRAM_BOT_TOKEN', '') or ''


# Conversation states for Payment Submission
(
    PAY_SELECT_RESERVATION,
    PAY_SELECT_METHOD,
    PAY_ENTER_REFERENCE,
    PAY_ENTER_AMOUNT,
    PAY_UPLOAD_PROOF,
) = range(5)

# Ticket browser pagination
TICKETS_PER_PAGE = 8

# Bot Commands registered with Telegram
BOT_COMMANDS = [
    ('start', 'Start bot & show main menu'),
    ('lotteries', 'Browse active lotteries & prize pools'),
    ('my_tickets', 'View your reservations, reviews & confirmed tickets'),
    ('pay', 'Submit transaction reference for verification'),
    ('winners', 'View recent winning lottery draws'),
    ('help', 'How to play, payment guide & support'),
    ('cancel', 'Cancel the current operation'),
]
