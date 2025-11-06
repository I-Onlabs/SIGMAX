"""
Telegram Bot - Natural Language Control Interface
"""

from typing import Optional, Dict, Any
from loguru import logger
import os


class TelegramBot:
    """
    Telegram Bot - Natural language interface for SIGMAX

    Commands:
    - /status - Current status
    - /start [profile] - Start trading
    - /pause [duration] - Pause trading
    - /resume - Resume trading
    - /panic - Emergency stop
    - /why [symbol] - Explain last decision
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.bot = None
        self.enabled = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

        logger.info(f"✓ Telegram bot created (enabled: {self.enabled})")

    async def initialize(self):
        """Initialize Telegram bot"""
        if not self.enabled:
            logger.info("Telegram bot disabled")
            return

        if not self.token:
            logger.warning("No Telegram token provided")
            return

        try:
            from telegram import Bot
            from telegram.ext import Application, CommandHandler, MessageHandler, filters

            # Create bot
            self.bot = Application.builder().token(self.token).build()

            # Register handlers
            self.bot.add_handler(CommandHandler("start", self._handle_start))
            self.bot.add_handler(CommandHandler("status", self._handle_status))
            self.bot.add_handler(CommandHandler("pause", self._handle_pause))
            self.bot.add_handler(CommandHandler("resume", self._handle_resume))
            self.bot.add_handler(CommandHandler("panic", self._handle_panic))
            self.bot.add_handler(CommandHandler("why", self._handle_why))

            # Natural language handler
            self.bot.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
            )

            logger.info("✓ Telegram bot initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            self.enabled = False

    async def start(self):
        """Start the bot"""
        if self.enabled and self.bot:
            await self.bot.initialize()
            await self.bot.start()
            await self.send_message("🤖 SIGMAX bot is online!")

    async def stop(self):
        """Stop the bot"""
        if self.enabled and self.bot:
            await self.send_message("👋 SIGMAX bot is going offline")
            await self.bot.stop()

    async def send_message(self, text: str):
        """Send message to user"""
        if self.enabled and self.bot and self.chat_id:
            try:
                await self.bot.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to send Telegram message: {e}")

    async def _handle_start(self, update, context):
        """Handle /start command"""
        profile = context.args[0] if context.args else "conservative"

        await update.message.reply_text(
            f"🚀 Starting SIGMAX with {profile} profile..."
        )

        await self.orchestrator.start()

    async def _handle_status(self, update, context):
        """Handle /status command"""
        status = await self.orchestrator.get_status()

        message = f"""
📊 *SIGMAX Status*

Running: {'✅' if status.get('running') else '❌'}
Paused: {'⏸️' if status.get('paused') else '▶️'}
Risk Profile: {status.get('risk_profile')}

Agents: {len(status.get('agents', {}))} active
"""

        await update.message.reply_text(message, parse_mode='Markdown')

    async def _handle_pause(self, update, context):
        """Handle /pause command"""
        duration = context.args[0] if context.args else None

        await self.orchestrator.pause()
        await update.message.reply_text(f"⏸️ Trading paused{f' for {duration}' if duration else ''}")

    async def _handle_resume(self, update, context):
        """Handle /resume command"""
        await self.orchestrator.resume()
        await update.message.reply_text("▶️ Trading resumed")

    async def _handle_panic(self, update, context):
        """Handle /panic command"""
        await update.message.reply_text("🚨 EMERGENCY STOP INITIATED!")

        # Emergency stop
        if hasattr(self.orchestrator, 'execution_module'):
            await self.orchestrator.execution_module.close_all_positions()

        await self.orchestrator.stop()

    async def _handle_why(self, update, context):
        """Handle /why command"""
        symbol = context.args[0] if context.args else "BTC/USDT"

        # TODO: Retrieve last decision explanation
        message = f"Explaining last decision for {symbol}...\n\n" \
                 f"This feature is coming soon!"

        await update.message.reply_text(message)

    async def _handle_message(self, update, context):
        """Handle natural language messages"""
        text = update.message.text.lower()

        # Simple intent matching
        if "status" in text or "how" in text:
            await self._handle_status(update, context)
        elif "pause" in text or "stop" in text:
            await self._handle_pause(update, context)
        elif "resume" in text or "start" in text:
            await self._handle_resume(update, context)
        else:
            await update.message.reply_text(
                "I didn't understand that. Try /status, /start, /pause, or /resume"
            )
