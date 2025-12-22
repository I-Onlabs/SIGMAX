"""
SIGMAX CLI - Main entry point.

Usage:
    sigmax analyze BTC/USDT --risk balanced
    sigmax status --format json
    sigmax shell  # Interactive mode
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.commands import (
    analyze_command,
    status_command,
    propose_command,
    approve_command,
    execute_command,
    list_proposals_command,
    config_command,
)
from cli.shell import start_shell

app = typer.Typer(
    name="sigmax",
    help="SIGMAX - Autonomous Multi-Agent AI Crypto Trading OS",
    add_completion=False,
)

console = Console()


@app.command("analyze")
def analyze(
    symbol: str = typer.Argument(..., help="Trading pair (e.g., BTC/USDT)"),
    risk: str = typer.Option("conservative", "--risk", help="Risk profile: conservative, balanced, aggressive"),
    mode: str = typer.Option("paper", "--mode", help="Trading mode: paper or live"),
    format: str = typer.Option("text", "--format", help="Output format: json, table, text"),
    stream: bool = typer.Option(False, "--stream", "-s", help="Stream analysis progress"),
    quantum: bool = typer.Option(True, help="Enable quantum portfolio optimization"),
):
    """
    Analyze a trading pair and get AI recommendation.

    Examples:
        sigmax analyze BTC/USDT
        sigmax analyze ETH/USDT --risk balanced
        sigmax analyze SOL/USDT --risk aggressive --stream
        sigmax analyze BTC/USDT --no-quantum  # Use classical optimization
    """
    analyze_command(symbol=symbol, risk=risk, mode=mode, format=format, stream=stream, quantum=quantum)


@app.command("status")
def status(
    format: str = typer.Option("text", "--format", help="Output format: json, table, text"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed status"),
):
    """
    Show current SIGMAX status.

    Examples:
        sigmax status
        sigmax status --format json
        sigmax status --verbose
    """
    status_command(format=format, verbose=verbose)


@app.command("propose")
def propose(
    symbol: str = typer.Argument(..., help="Trading pair (e.g., BTC/USDT)"),
    size: Optional[float] = typer.Option(None, "--size", help="Position size in USD"),
    risk: str = typer.Option("conservative", "--risk", help="Risk profile"),
    mode: str = typer.Option("paper", "--mode", help="Trading mode: paper or live"),
    format: str = typer.Option("text", "--format", help="Output format: json, table, text"),
    quantum: bool = typer.Option(True, help="Enable quantum portfolio optimization"),
):
    """
    Create a trade proposal.

    Examples:
        sigmax propose BTC/USDT
        sigmax propose ETH/USDT --size 100
        sigmax propose SOL/USDT --risk balanced --mode live
        sigmax propose BTC/USDT --no-quantum  # Use classical optimization
    """
    propose_command(symbol=symbol, size=size, risk=risk, mode=mode, format=format, quantum=quantum)


@app.command("approve")
def approve(
    proposal_id: str = typer.Argument(..., help="Proposal ID to approve"),
    format: str = typer.Option("text", "--format", help="Output format: json, table, text"),
):
    """
    Approve a trade proposal.

    Examples:
        sigmax approve PROP-123
        sigmax approve PROP-456 --format json
    """
    approve_command(proposal_id=proposal_id, format=format)


@app.command("execute")
def execute(
    proposal_id: str = typer.Argument(..., help="Proposal ID to execute"),
    format: str = typer.Option("text", "--format", help="Output format: json, table, text"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """
    Execute an approved trade proposal.

    Examples:
        sigmax execute PROP-123
        sigmax execute PROP-456 --force
    """
    if not force:
        confirm = typer.confirm(f"Execute proposal {proposal_id}?")
        if not confirm:
            console.print("[yellow]Execution cancelled[/yellow]")
            raise typer.Abort()

    execute_command(proposal_id=proposal_id, format=format)


@app.command("proposals")
def list_proposals(
    format: str = typer.Option("table", "--format", help="Output format: json, table, text"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status: pending, approved, executed"),
):
    """
    List all trade proposals.

    Examples:
        sigmax proposals
        sigmax proposals --status pending
        sigmax proposals --format json
    """
    list_proposals_command(format=format, status_filter=status)


@app.command("config")
def config(
    action: str = typer.Argument(..., help="Action: get, set, list"),
    key: Optional[str] = typer.Argument(None, help="Configuration key"),
    value: Optional[str] = typer.Argument(None, help="Configuration value"),
):
    """
    Manage CLI configuration.

    Examples:
        sigmax config list
        sigmax config get api_key
        sigmax config set api_key sk-xxx
    """
    config_command(action=action, key=key, value=value)


@app.command("shell")
def shell(
    api_url: Optional[str] = typer.Option(None, "--api-url", help="API endpoint URL"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key"),
):
    """
    Start interactive shell mode.

    Examples:
        sigmax shell
        sigmax shell --api-url http://localhost:8000
    """
    console.print(
        Panel.fit(
            "[bold cyan]SIGMAX Interactive Shell[/bold cyan]\n"
            "Type 'help' for commands, 'exit' to quit",
            border_style="cyan",
        )
    )
    start_shell(api_url=api_url, api_key=api_key)


@app.command("version")
def version():
    """Show SIGMAX CLI version."""
    from cli import __version__

    console.print(f"[bold cyan]SIGMAX CLI[/bold cyan] version [green]{__version__}[/green]")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
