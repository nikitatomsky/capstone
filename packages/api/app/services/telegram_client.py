"""Telegram Bot API client for sending messages."""

import logging
import os

from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramClient:
    """Client for sending messages via Telegram Bot API."""

    def __init__(self, bot_token: str | None = None):
        """
        Initialize Telegram bot client.

        Args:
            bot_token: Telegram bot token. If None, reads from TELEGRAM_BOT_TOKEN env var.
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.bot = Bot(token=self.bot_token) if self.bot_token else None

        if self.bot:
            logger.info("Telegram bot initialized")
        else:
            logger.warning("TELEGRAM_BOT_TOKEN not set - responses will not be sent")

    async def send_message(self, chat_id: int, text: str) -> bool:
        """
        Send message to Telegram chat.

        Args:
            chat_id: Telegram chat ID
            text: Message text to send

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.bot:
            logger.warning("Cannot send message - bot not initialized")
            return False

        try:
            await self.bot.send_message(chat_id=chat_id, text=text)
            logger.info(f"Sent message to chat_id={chat_id}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message to chat_id={chat_id}: {e}")
            return False
