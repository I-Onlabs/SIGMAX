"""
SIGMAX CLI - Output formatting utilities.

Formats data for different output modes: JSON, table, text.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def format_output(data: Any, format: str = "text") -> str:
    """Format data according to specified format."""
    if format == "json":
        return json.dumps(data, indent=2)
    elif format == "table":
        return _format_as_table(data)
    else:  # text
        return _format_as_text(data)


def format_analysis(result: Dict[str, Any], format: str = "text") -> str:
    """Format analysis result."""
    if format == "json":
        console.print_json(data=result)
        return ""

    # Extract key information
    decision = result.get("decision", {})
    action = decision.get("action", "HOLD")
    confidence = decision.get("confidence", 0)
    rationale = decision.get("rationale", "No rationale provided")

    if format == "table":
        table = Table(title="Analysis Result", show_header=True)
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="green")

        table.add_row("Action", f"[bold]{action}[/bold]")
        table.add_row("Confidence", f"{confidence:.1%}")
        table.add_row("Rationale", rationale)

        # Add artifacts if present
        artifacts = result.get("artifacts", [])
        if artifacts:
            table.add_row("", "")  # Separator
            table.add_row("[bold]Artifacts[/bold]", f"{len(artifacts)} items")

        console.print(table)

        # Show artifacts
        for artifact in artifacts:
            _display_artifact(artifact)

    else:  # text
        # Color-code action
        action_color = {
            "BUY": "green",
            "SELL": "red",
            "HOLD": "yellow",
        }.get(action, "white")

        console.print(
            Panel.fit(
                f"[bold]Action:[/bold] [{action_color}]{action}[/{action_color}]\n"
                f"[bold]Confidence:[/bold] {confidence:.1%}\n"
                f"[bold]Rationale:[/bold] {rationale}",
                title="[bold cyan]Analysis Result[/bold cyan]",
                border_style="cyan",
            )
        )

        # Show artifacts
        artifacts = result.get("artifacts", [])
        if artifacts:
            console.print(f"\n[bold]Artifacts ({len(artifacts)}):[/bold]")
            for artifact in artifacts:
                _display_artifact(artifact)

    return ""


def format_proposal(proposal: Dict[str, Any], format: str = "text") -> str:
    """Format trade proposal."""
    if format == "json":
        console.print_json(data=proposal)
        return ""

    pid = proposal.get("proposal_id", "unknown")
    symbol = proposal.get("symbol", "")
    action = proposal.get("action", "")
    size = proposal.get("notional_usd", 0)
    approved = proposal.get("approved", False)
    rationale = proposal.get("rationale", "No rationale")

    if format == "table":
        table = Table(title="Trade Proposal", show_header=False)
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="green")

        table.add_row("Proposal ID", pid)
        table.add_row("Symbol", symbol)
        table.add_row("Action", action.upper())
        table.add_row("Size", f"${size:.2f}")
        table.add_row("Status", "✓ Approved" if approved else "⏳ Pending")
        table.add_row("Rationale", rationale)

        console.print(table)
    else:  # text
        status = "[green]✓ Approved[/green]" if approved else "[yellow]⏳ Pending[/yellow]"
        action_color = "green" if action.lower() == "buy" else "red"

        console.print(
            Panel.fit(
                f"[bold]ID:[/bold] {pid}\n"
                f"[bold]Symbol:[/bold] {symbol}\n"
                f"[bold]Action:[/bold] [{action_color}]{action.upper()}[/{action_color}]\n"
                f"[bold]Size:[/bold] ${size:.2f}\n"
                f"[bold]Status:[/bold] {status}\n"
                f"[bold]Rationale:[/bold] {rationale}",
                title="[bold cyan]Trade Proposal[/bold cyan]",
                border_style="cyan",
            )
        )

    return ""


def _format_as_table(data: Dict[str, Any]) -> str:
    """Format dict as table."""
    table = Table(show_header=True)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    for key, value in data.items():
        table.add_row(key, str(value))

    console.print(table)
    return ""


def _format_as_text(data: Dict[str, Any]) -> str:
    """Format dict as text."""
    for key, value in data.items():
        console.print(f"[cyan]{key}:[/cyan] {value}")
    return ""


def _display_artifact(artifact: Dict[str, Any]):
    """Display a single artifact."""
    artifact_type = artifact.get("type", "unknown")
    title = artifact.get("title", "Artifact")
    content = artifact.get("content", {})

    if artifact_type == "code":
        # Syntax-highlighted code
        code = content.get("code", "")
        language = content.get("language", "python")
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"📝 {title}", border_style="blue"))

    elif artifact_type == "chart" or artifact_type == "data":
        # Tabular data
        if isinstance(content, dict):
            table = Table(title=title, show_header=True)
            for key in content.keys():
                table.add_column(key, style="cyan")

            # Assuming dict of lists
            rows = zip(*content.values())
            for row in rows:
                table.add_row(*[str(v) for v in row])

            console.print(table)
        else:
            console.print(Panel(str(content), title=f"📊 {title}", border_style="blue"))

    else:
        # Generic artifact
        console.print(Panel(str(content), title=f"📄 {title}", border_style="dim"))
