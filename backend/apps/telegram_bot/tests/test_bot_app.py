"""
Tests for Telegram Bot application initialization.
"""
import pytest
from apps.telegram_bot.bot import build_bot_application


class TestBotApplication:
    """Tests for Telegram bot application builder."""

    def test_build_bot_application_with_token(self):
        token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        app = build_bot_application(token)
        assert app is not None
        assert app.bot.token == token
        # Handlers are registered
        assert len(app.handlers) > 0
        assert len(app.error_handlers) > 0

    def test_build_bot_application_missing_token_raises(self):
        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN is not configured"):
            build_bot_application(token="")
