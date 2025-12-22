"""
SIGMAX CLI - Interactive shell mode.

Provides a REPL interface for natural conversation with SIGMAX.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from pathlib import Path

from cli.client import SigmaxClient
from cli.config import get_config
from cli.formatting import format_analysis, format_proposal

console = Console()

# Command completer
COMMANDS = [
    "analyze",
    "status",
    "propose",
    "approve",
    "execute",
    "proposals",
    "help",
    "exit",
    "quit",
    "config",
    "clear",
]

completer = WordCompleter(COMMANDS, ignore_case=True)

# Shell style
shell_style = Style.from_dict({
    "prompt": "#00aa00 bold",
})


class SigmaxShell:
    """Interactive SIGMAX shell."""

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize shell."""
        config = get_config()
        self.api_url = api_url or config.get("api_url", "http://localhost:8000")
        self.api_key = api_key or config.get("api_key")

        if not self.api_key:
            console.print("[bold red]Warning:[/bold red] No API key configured")
            console.print("Run: [cyan]config set api_key YOUR_KEY[/cyan]")

        self.client = SigmaxClient(api_url=self.api_url, api_key=self.api_key)

        # History file
        history_dir = Path.home() / ".sigmax"
        history_dir.mkdir(exist_ok=True)
        self.history = FileHistory(str(history_dir / "shell_history.txt"))

    async def handle_command(self, command: str):
        """Handle a shell command."""
        command = command.strip()

        if not command:
            return

        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:]

        # Built-in commands
        if cmd in ["exit", "quit"]:
            console.print("[yellow]Goodbye![/yellow]")
            return False

        elif cmd == "help":
            self._show_help()

        elif cmd == "clear":
            console.clear()

        elif cmd == "config":
            self._handle_config(args)

        # Analysis commands
        elif cmd == "analyze":
            if not args:
                console.print("[red]Usage: analyze <symbol> [--risk <profile>][/red]")
                return

            symbol = args[0]
            risk = "conservative"

            # Parse options
            if "--risk" in args:
                idx = args.index("--risk")
                if idx + 1 < len(args):
                    risk = args[idx + 1]

            await self._analyze(symbol, risk)

        elif cmd == "status":
            await self._status()

        elif cmd == "propose":
            if not args:
                console.print("[red]Usage: propose <symbol> [--risk <profile>][/red]")
                return

            symbol = args[0]
            risk = "conservative"

            if "--risk" in args:
                idx = args.index("--risk")
                if idx + 1 < len(args):
                    risk = args[idx + 1]

            await self._propose(symbol, risk)

        elif cmd == "approve":
            if not args:
                console.print("[red]Usage: approve <proposal_id>[/red]")
                return

            await self._approve(args[0])

        elif cmd == "execute":
            if not args:
                console.print("[red]Usage: execute <proposal_id>[/red]")
                return

            await self._execute(args[0])

        elif cmd == "proposals":
            await self._list_proposals()

        else:
            # Natural language query (future enhancement)
            console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            console.print("Type 'help' for available commands")

        return True

    async def _analyze(self, symbol: str, risk: str):
        """Analyze a symbol."""
        console.print(f"[bold cyan]Analyzing {symbol}...[/bold cyan]")

        try:
            # Use streaming for interactive feel
            async for event in self.client.analyze_stream(symbol, risk, "paper"):
                if event["type"] == "step":
                    console.print(f"  [dim]{event['step']}[/dim]")
                elif event["type"] == "final":
                    console.print()
                    format_analysis(event, "text")
                elif event["type"] == "error":
                    console.print(f"[red]Error: {event['error']}[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    async def _status(self):
        """Show status."""
        try:
            status = await self.client.get_status()
            console.print(f"[bold]Status:[/bold] {status.get('status', 'unknown')}")
            console.print(f"[bold]Active Trades:[/bold] {status.get('active_trades', 0)}")
            console.print(f"[bold]PnL:[/bold] ${status.get('pnl', 0):.2f}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    async def _propose(self, symbol: str, risk: str):
        """Create trade proposal."""
        console.print(f"[bold cyan]Creating proposal for {symbol}...[/bold cyan]")

        try:
            proposal = await self.client.propose_trade(symbol, risk, "paper")
            format_proposal(proposal, "text")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    async def _approve(self, proposal_id: str):
        """Approve proposal."""
        console.print(f"[bold cyan]Approving {proposal_id}...[/bold cyan]")

        try:
            proposal = await self.client.approve_proposal(proposal_id)
            console.print("[green]✓ Approved[/green]")
            format_proposal(proposal, "text")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    async def _execute(self, proposal_id: str):
        """Execute proposal."""
        console.print(f"[bold yellow]Execute {proposal_id}?[/bold yellow] (yes/no): ", end="")

        confirm = input().strip().lower()
        if confirm != "yes":
            console.print("[yellow]Cancelled[/yellow]")
            return

        console.print(f"[bold cyan]Executing {proposal_id}...[/bold cyan]")

        try:
            result = await self.client.execute_proposal(proposal_id)
            console.print("[green]✓ Executed[/green]")
            console.print(f"Result: {result}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    async def _list_proposals(self):
        """List all proposals."""
        try:
            proposals = await self.client.list_proposals()

            if not proposals:
                console.print("[yellow]No proposals found[/yellow]")
                return

            console.print(f"[bold]Proposals ({len(proposals)}):[/bold]")
            for pid, proposal in proposals.items():
                status = "✓" if proposal.get("approved") else "⏳"
                console.print(
                    f"  {status} [cyan]{pid[:16]}...[/cyan] "
                    f"{proposal.get('symbol')} {proposal.get('action', '').upper()} "
                    f"${proposal.get('notional_usd', 0):.2f}"
                )
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _handle_config(self, args):
        """Handle config command."""
        if not args:
            from cli.config import list_config

            config = list_config()
            console.print("[bold]Configuration:[/bold]")
            for key, value in config.items():
                # Mask sensitive values
                if "key" in key.lower() or "secret" in key.lower():
                    value = value[:8] + "..." if value and len(str(value)) > 8 else "***"
                console.print(f"  [cyan]{key}[/cyan] = {value}")
        elif args[0] == "set" and len(args) >= 3:
            from cli.config import set_config

            key = args[1]
            value = args[2]
            set_config(key, value)
            console.print(f"[green]✓ Set {key}[/green]")
        else:
            console.print("[red]Usage: config [set <key> <value>][/red]")

    def _show_help(self):
        """Show help message."""
        help_text = """
# SIGMAX Shell Commands

## Analysis
- **analyze <symbol>** [--risk <profile>]  Analyze a trading pair
- **status**                                Show current status

## Trading
- **propose <symbol>** [--risk <profile>]  Create trade proposal
- **approve <proposal_id>**                 Approve a proposal
- **execute <proposal_id>**                 Execute a proposal
- **proposals**                             List all proposals

## Configuration
- **config**                                Show configuration
- **config set <key> <value>**              Set configuration value

## Shell
- **help**                                  Show this help
- **clear**                                 Clear screen
- **exit**                                  Exit shell

## Examples
```
analyze BTC/USDT
analyze ETH/USDT --risk balanced
propose SOL/USDT --risk aggressive
approve PROP-123
execute PROP-123
```
"""
        console.print(Markdown(help_text))


def start_shell(api_url: Optional[str] = None, api_key: Optional[str] = None):
    """Start interactive shell."""
    shell = SigmaxShell(api_url=api_url, api_key=api_key)
    session = PromptSession(
        history=shell.history,
        completer=completer,
        style=shell_style,
    )

    console.print("[dim]Type 'help' for commands, 'exit' to quit[/dim]\n")

    while True:
        try:
            # Get input
            command = session.prompt("sigmax> ")

            # Handle command
            result = asyncio.run(shell.handle_command(command))

            # Exit if requested
            if result is False:
                break

        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            continue
        except EOFError:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
