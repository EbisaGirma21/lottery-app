"""
Django management command to run the Telegram customer bot in polling mode.
Usage:
    python manage.py run_telegram_bot
    python manage.py run_telegram_bot --dry-run
"""
import logging
from django.core.management.base import BaseCommand

from apps.telegram_bot.bot import build_bot_application
from apps.telegram_bot.config import get_bot_token

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Runs the Telegram Customer Bot for lottery browsing, reservations, and payment submissions.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate bot setup, handlers, and configuration without starting network polling.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        token = get_bot_token()

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Validating Telegram Bot configuration..."))
            test_token = token or "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
            try:
                app = build_bot_application(test_token)
                self.stdout.write(self.style.SUCCESS(f"[OK] Bot initialized successfully with {len(app.handlers[0])} handler groups."))
                return
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"[FAIL] Dry run failed: {str(e)}"))
                return

        if not token:
            self.stderr.write(
                self.style.ERROR(
                    "[ERROR] TELEGRAM_BOT_TOKEN is not configured. "
                    "Please set TELEGRAM_BOT_TOKEN in your .env or settings."
                )
            )
            return

        self.stdout.write(self.style.SUCCESS("Starting Telegram Customer Bot worker (polling mode)..."))
        app = build_bot_application(token)
        app.run_polling()
