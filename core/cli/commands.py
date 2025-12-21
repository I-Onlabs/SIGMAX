"""
SIGMAX CLI - Command implementations.

All commands use the ChannelService for consistent behavior across interfaces.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.client import SigmaxClient
from cli.formatting import format_output, format_proposal, format_analysis
from cli.config import get_config, set_config, list_config

console = Console()


def get_client() -> SigmaxClient:
    """Get configured SIGMAX client."""
    config = get_config()
    api_url = config.get("api_url", "http://localhost:8000")
    api_key = config.get("api_key")

    if not api_key:
        console.print("[bold red]Error:[/bold red] API key not configured")
        console.print("Run: [cyan]sigmax config set api_key YOUR_KEY[/cyan]")
        sys.exit(1)

    return SigmaxClient(api_url=api_url, api_key=api_key)


def analyze_command(
    symbol: str,
    risk: str = "conservative",
    mode: str = "paper",
    format: str = "text",
    stream: bool = False,
):
    """Analyze a trading pair."""
    client = get_client()

    if stream:
        # Streaming mode with progress
        console.print(f"[bold cyan]Analyzing {symbol}...[/bold cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Starting analysis...", total=None)

            async def stream_analysis():
                async for event in client.analyze_stream(symbol, risk, mode):
                    if event["type"] == "step":
                        progress.update(task, description=f"{event['step']}")
                    elif event["type"] == "final":
                        progress.update(task, description="Analysis complete", completed=True)
                        return event["data"]
                    elif event["type"] == "error":
                        progress.update(task, description=f"Error: {event['error']}", completed=True)
                        return None

            result = asyncio.run(stream_analysis())

        if result:
            console.print(format_analysis(result, format))
    else:
        # Synchronous mode
        with console.status(f"[bold cyan]Analyzing {symbol}...[/bold cyan]"):
            result = asyncio.run(client.analyze(symbol, risk, mode))

        if result:
            console.print(format_analysis(result, format))


def status_command(format: str = "text", verbose: bool = False):
    """Show SIGMAX status."""
    client = get_client()

    with console.status("[bold cyan]Fetching status...[/bold cyan]"):
        status = asyncio.run(client.get_status())

    if format == "json":
        console.print_json(data=status)
    elif format == "table":
        table = Table(title="SIGMAX Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for key, value in status.items():
            table.add_row(key.replace("_", " ").title(), str(value))

        console.print(table)
    else:  # text
        console.print(Panel.fit(
            f"[bold]Status:[/bold] {status.get('status', 'unknown')}\n"
            f"[bold]Mode:[/bold] {status.get('mode', 'unknown')}\n"
            f"[bold]Active Trades:[/bold] {status.get('active_trades', 0)}\n"
            f"[bold]PnL:[/bold] ${status.get('pnl', 0):.2f}",
            title="[bold cyan]SIGMAX Status[/bold cyan]",
            border_style="cyan",
        ))

        if verbose and "details" in status:
            console.print("\n[bold]Details:[/bold]")
            console.print_json(data=status["details"])


def propose_command(
    symbol: str,
    size: Optional[float] = None,
    risk: str = "conservative",
    mode: str = "paper",
    format: str = "text",
):
    """Create a trade proposal."""
    client = get_client()

    with console.status(f"[bold cyan]Creating proposal for {symbol}...[/bold cyan]"):
        proposal = asyncio.run(client.propose_trade(symbol, risk, mode, size))

    if proposal:
        console.print(format_proposal(proposal, format))


def approve_command(proposal_id: str, format: str = "text"):
    """Approve a trade proposal."""
    client = get_client()

    with console.status(f"[bold cyan]Approving proposal {proposal_id}...[/bold cyan]"):
        proposal = asyncio.run(client.approve_proposal(proposal_id))

    if proposal:
        console.print(f"[green]✓[/green] Proposal {proposal_id} approved")
        console.print(format_proposal(proposal, format))


def execute_command(proposal_id: str, format: str = "text"):
    """Execute an approved trade proposal."""
    client = get_client()

    with console.status(f"[bold cyan]Executing proposal {proposal_id}...[/bold cyan]"):
        result = asyncio.run(client.execute_proposal(proposal_id))

    if result:
        if format == "json":
            console.print_json(data=result)
        else:
            console.print(f"[green]✓[/green] Proposal {proposal_id} executed")
            console.print(Panel.fit(
                f"[bold]Success:[/bold] {result.get('success', False)}\n"
                f"[bold]Result:[/bold] {result.get('result', 'unknown')}",
                title="[bold green]Execution Result[/bold green]",
                border_style="green",
            ))


def list_proposals_command(format: str = "table", status_filter: Optional[str] = None):
    """List all trade proposals."""
    client = get_client()

    with console.status("[bold cyan]Fetching proposals...[/bold cyan]"):
        proposals = asyncio.run(client.list_proposals())

    if not proposals:
        console.print("[yellow]No proposals found[/yellow]")
        return

    # Filter by status if specified
    if status_filter:
        proposals = {
            pid: p
            for pid, p in proposals.items()
            if p.get("status") == status_filter or p.get("approved") == (status_filter == "approved")
        }

    if format == "json":
        console.print_json(data=proposals)
    elif format == "table":
        table = Table(title=f"Trade Proposals ({len(proposals)})")
        table.add_column("ID", style="cyan")
        table.add_column("Symbol", style="yellow")
        table.add_column("Action", style="magenta")
        table.add_column("Size", justify="right")
        table.add_column("Status", style="green")
        table.add_column("Created", style="dim")

        for pid, proposal in proposals.items():
            status = "✓ Approved" if proposal.get("approved") else "Pending"
            table.add_row(
                pid[:12] + "..." if len(pid) > 15 else pid,
                proposal.get("symbol", ""),
                proposal.get("action", "").upper(),
                f"${proposal.get('notional_usd', 0):.2f}",
                status,
                proposal.get("created_at", "")[:19],
            )

        console.print(table)
    else:  # text
        for pid, proposal in proposals.items():
            status = "✓ Approved" if proposal.get("approved") else "⏳ Pending"
            console.print(
                f"[cyan]{pid[:16]}...[/cyan] {proposal.get('symbol')} "
                f"{proposal.get('action', '').upper()} ${proposal.get('notional_usd', 0):.2f} {status}"
            )


def config_command(action: str, key: Optional[str] = None, value: Optional[str] = None):
    """Manage CLI configuration."""
    if action == "list":
        config = list_config()
        table = Table(title="CLI Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")

        for k, v in config.items():
            # Mask sensitive values
            if "key" in k.lower() or "secret" in k.lower() or "token" in k.lower():
                v = v[:8] + "..." if v and len(v) > 8 else "***"
            table.add_row(k, str(v))

        console.print(table)

    elif action == "get":
        if not key:
            console.print("[red]Error: Key required for 'get' action[/red]")
            sys.exit(1)

        value = get_config().get(key)
        if value is None:
            console.print(f"[yellow]Key '{key}' not found[/yellow]")
        else:
            # Mask sensitive values
            if "key" in key.lower() or "secret" in key.lower() or "token" in key.lower():
                value = value[:8] + "..." if len(value) > 8 else "***"
            console.print(f"[cyan]{key}[/cyan] = [green]{value}[/green]")

    elif action == "set":
        if not key or not value:
            console.print("[red]Error: Both key and value required for 'set' action[/red]")
            sys.exit(1)

        set_config(key, value)
        console.print(f"[green]✓[/green] Set [cyan]{key}[/cyan] = [dim]{value[:8]}...[/dim]")

    else:
        console.print(f"[red]Error: Unknown action '{action}'[/red]")
        console.print("Valid actions: list, get, set")
        sys.exit(1)
