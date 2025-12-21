"""
Telegram Bot - Natural Language Control Interface
"""

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
    - /analyze [symbol] - Run full multi-agent analysis
    - /propose [symbol] - Create a trade proposal (paper/live gated)
    - /approve [proposal_id] - Approve a proposal (required for live by default)
    - /execute [proposal_id] - Execute an approved proposal
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.bot = None
        self.enabled = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.channel_service = None

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
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
            from interfaces.channel_service import ChannelService

            # Create bot
            self.bot = Application.builder().token(self.token).build()

            # Shared channel service (Telegram + web share the same orchestrator instance)
            execution_module = getattr(self.orchestrator, "execution_module", None)
            compliance_module = getattr(self.orchestrator, "compliance_module", None)
            self.channel_service = ChannelService(
                orchestrator=self.orchestrator,
                execution_module=execution_module,
                compliance_module=compliance_module,
            )

            # Register handlers
            self.bot.add_handler(CommandHandler("start", self._handle_start))
            self.bot.add_handler(CommandHandler("status", self._handle_status))
            self.bot.add_handler(CommandHandler("pause", self._handle_pause))
            self.bot.add_handler(CommandHandler("resume", self._handle_resume))
            self.bot.add_handler(CommandHandler("panic", self._handle_panic))
            self.bot.add_handler(CommandHandler("why", self._handle_why))
            self.bot.add_handler(CommandHandler("analyze", self._handle_analyze))
            self.bot.add_handler(CommandHandler("propose", self._handle_propose))
            self.bot.add_handler(CommandHandler("approve", self._handle_approve))
            self.bot.add_handler(CommandHandler("execute", self._handle_execute))

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
        """Handle /why command - Explain last trading decision"""
        symbol = context.args[0] if context.args else "BTC/USDT"

        # Get decision history from orchestrator
        if not hasattr(self.orchestrator, 'decision_history'):
            await update.message.reply_text(
                "⚠️ Decision history not available"
            )
            return

        decision_history = self.orchestrator.decision_history
        last_decision = decision_history.get_last_decision(symbol)

        if not last_decision:
            # Try to find any recent decision
            all_symbols = decision_history.get_all_symbols()
            if all_symbols:
                available = ', '.join(all_symbols[:5])
                await update.message.reply_text(
                    f"❌ No decisions found for {symbol}\n\n"
                    f"Try: {available}"
                )
            else:
                await update.message.reply_text(
                    "❌ No trading decisions recorded yet.\n\n"
                    "Start trading first with /start"
                )
            return

        # Format and send explanation
        explanation = decision_history.format_decision_explanation(last_decision)
        await update.message.reply_text(explanation, parse_mode='Markdown')

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

    async def _handle_analyze(self, update, context):
        symbol = context.args[0] if context.args else "BTC/USDT"
        try:
            if not self.channel_service:
                await update.message.reply_text("⚠️ Channel service not available")
                return

            resp = await self.channel_service.handle(
                StructuredRequest(
                    channel=Channel.telegram,
                    intent=Intent.analyze,
                    symbol=symbol,
                    preferences=UserPreferences(
                        risk_profile=os.getenv("RISK_PROFILE", "conservative"),
                        mode=os.getenv("MODE", "paper"),
                        permissions=ExecutionPermissions(
                            allow_paper=True,
                            allow_live=(os.getenv("MODE", "paper") == "live"),
                            require_manual_approval_live=os.getenv("REQUIRE_MANUAL_APPROVAL", "true").lower() == "true",
                        ),
                    ),
                )
            )
            await update.message.reply_text(resp.message)
        except Exception as e:
            await update.message.reply_text(f"❌ Analyze failed: {e}")

    async def _handle_propose(self, update, context):
        symbol = context.args[0] if context.args else "BTC/USDT"
        try:
            if not self.channel_service:
                await update.message.reply_text("⚠️ Channel service not available")
                return

            resp = await self.channel_service.handle(
                StructuredRequest(
                    channel=Channel.telegram,
                    intent=Intent.propose_trade,
                    symbol=symbol,
                    preferences=UserPreferences(
                        risk_profile=os.getenv("RISK_PROFILE", "conservative"),
                        mode=os.getenv("MODE", "paper"),
                        permissions=ExecutionPermissions(
                            allow_paper=True,
                            allow_live=(os.getenv("MODE", "paper") == "live"),
                            require_manual_approval_live=os.getenv("REQUIRE_MANUAL_APPROVAL", "true").lower() == "true",
                        ),
                    ),
                )
            )
            if resp.proposal:
                p = resp.proposal
                await update.message.reply_text(
                    f"{resp.message}\n\nProposal ID: `{p.proposal_id}`\n"
                    f"Requires approval: {p.requires_manual_approval}\n"
                    f"Approve: /approve {p.proposal_id}\n"
                    f"Execute: /execute {p.proposal_id}",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(resp.message)
        except Exception as e:
            await update.message.reply_text(f"❌ Propose failed: {e}")

    async def _handle_approve(self, update, context):
        proposal_id = context.args[0] if context.args else None
        if not proposal_id:
            await update.message.reply_text("Usage: /approve <proposal_id>")
            return
        try:
            if not self.channel_service:
                await update.message.reply_text("⚠️ Channel service not available")
                return
            proposal = self.channel_service.approve_proposal(proposal_id)
            await update.message.reply_text(f"✅ Approved {proposal.proposal_id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Approve failed: {e}")

    async def _handle_execute(self, update, context):
        proposal_id = context.args[0] if context.args else None
        if not proposal_id:
            await update.message.reply_text("Usage: /execute <proposal_id>")
            return
        try:
            if not self.channel_service:
                await update.message.reply_text("⚠️ Channel service not available")
                return
            result = await self.channel_service.execute_proposal(proposal_id)
            await update.message.reply_text(f"✅ Executed: {result}")
        except Exception as e:
            await update.message.reply_text(f"❌ Execute failed: {e}")
