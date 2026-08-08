"""Typer CLI / interactive REPL for the terminal assistant.

This file is the user-facing shell:
- load settings
- wire confirm / on_tool callbacks into the agent
- read prompts in a loop and print answers

Business logic (tools + agent loop) lives in tools.py and agent.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from terminal_assistant.agent import TerminalAgent
from terminal_assistant.config import load_settings

# invoke_without_command=True → `python -m terminal_assistant` runs the callback
# directly (no subcommand required).
app = typer.Typer(
    add_completion=False,
    help="Local AI terminal assistant with tool calling.",
    invoke_without_command=True,
)
console = Console()


def _format_args(args: dict[str, Any]) -> str:
    """Compact args for display; truncate long write content."""
    display = dict(args)
    if "content" in display and isinstance(display["content"], str):
        text = display["content"]
        if len(text) > 80:
            display["content"] = text[:77] + "..."
    try:
        return json.dumps(display, ensure_ascii=False)
    except TypeError:
        return str(display)


def _on_tool(name: str, args: dict[str, Any]) -> None:
    """Print each tool call so you can see the agent loop live."""
    console.print(f"[dim]→ {name}({_format_args(args)})[/dim]")


def _confirm(name: str, args: dict[str, Any]) -> bool:
    """Ask before destructive tools (write_file / execute_shell_command)."""
    console.print(
        Panel.fit(
            f"[bold]{name}[/bold]\n{_format_args(args)}",
            title="Confirm tool",
            border_style="yellow",
        )
    )
    # Default False = safer; user must explicitly approve
    return Confirm.ask("Allow this action?", default=False)


@app.callback()
def main(
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace root (default: current directory).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Start an interactive session with the AI terminal assistant."""
    settings = load_settings(workspace=workspace)
    agent = TerminalAgent(
        settings=settings,
        console=console,
        confirm=_confirm,
        on_tool=_on_tool,
    )

    console.print(
        Panel.fit(
            f"[bold]AI Terminal Assistant (TAM)[/bold]\n"
            f"workspace: {settings.workspace}\n"
            f"model: {settings.model}\n"
            f"Type a question, or quit / exit / q. clear resets history.",
            border_style="cyan",
        )
    )

    # --- REPL loop ------------------------------------------------------
    while True:
        try:
            user_text = Prompt.ask("[bold cyan]You[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            # Ctrl+C / Ctrl+D should exit cleanly
            console.print("\nBye.")
            raise typer.Exit(0) from None

        text = user_text.strip()
        if not text:
            continue
        lowered = text.lower()
        if lowered in {"quit", "exit", "q"}:
            console.print("Bye.")
            raise typer.Exit(0)
        if lowered == "clear":
            # Drop prior turns so the next question starts a fresh context
            agent.clear_history()
            console.print("[dim]Conversation cleared.[/dim]")
            continue

        try:
            answer = agent.run_turn(text)
        except Exception as exc:  # noqa: BLE001 — show API/network errors cleanly
            console.print(f"[red]Error:[/red] {exc}")
            continue

        console.print(f"[bold green]Assistant[/bold green]> {answer}")


if __name__ == "__main__":
    app()
