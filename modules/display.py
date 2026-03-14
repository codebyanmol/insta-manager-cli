"""
display.py — Terminal UI Module (Rich)
========================================
All console rendering lives here: banners, menus, tables, progress bars,
status messages, and user-input helpers.  Import `console` elsewhere for
any ad-hoc printing so the theme stays consistent.
"""

import time
import random
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich import box

# ─── Shared console instance (import this everywhere) ─────────────────────────
console = Console()

# ─── Colour palette (centralised for easy theming) ────────────────────────────
C = {
    "primary":   "cyan",
    "secondary": "bright_blue",
    "success":   "green",
    "warning":   "yellow",
    "error":     "red",
    "muted":     "dim white",
    "accent":    "magenta",
    "title":     "bold cyan",
    "header":    "bold white",
    "number":    "bright_yellow",
}


# ─── Banner ───────────────────────────────────────────────────────────────────

def show_banner() -> None:
    """Print the application header banner."""
    console.print()
    art = Text(justify="center")
    art.append("  ██╗███╗   ██╗███████╗████████╗ █████╗      \n", style="bold cyan")
    art.append("  ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗     \n", style="bold cyan")
    art.append("  ██║██╔██╗ ██║███████╗   ██║   ███████║     \n", style="bold blue")
    art.append("  ██║██║╚██╗██║╚════██║   ██║   ██╔══██║     \n", style="bold blue")
    art.append("  ██║██║ ╚████║███████║   ██║   ██║  ██║     \n", style="bold magenta")
    art.append("  ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝     \n", style="bold magenta")
    art.append("         MANAGER  CLI  v1.0.0                 ", style="dim white")
    console.print(Panel(art, border_style="cyan", padding=(0, 4)))
    console.print()


# ─── Section headings / dividers ──────────────────────────────────────────────

def section(title: str) -> None:
    console.print()
    console.print(Rule(f"[bold cyan] {title} [/bold cyan]", style="cyan"))
    console.print()


def divider() -> None:
    console.print(Rule(style="dim"))


# ─── Status helpers ───────────────────────────────────────────────────────────

def success(msg: str) -> None:
    console.print(f"  [bold green]✔[/bold green]  {msg}")

def error(msg: str) -> None:
    console.print(f"  [bold red]✘[/bold red]  [red]{msg}[/red]")

def warning(msg: str) -> None:
    console.print(f"  [bold yellow]⚠[/bold yellow]  [yellow]{msg}[/yellow]")

def info(msg: str) -> None:
    console.print(f"  [bold cyan]ℹ[/bold cyan]  {msg}")

def action(msg: str) -> None:
    console.print(f"  [bold magenta]→[/bold magenta]  {msg}")


# ─── Menu renderer ────────────────────────────────────────────────────────────

def show_menu(title: str, options: list[tuple[str, str]], status_line: str = "") -> None:
    """
    Render a numbered menu inside a Rich Panel.

    options: list of (label, description) tuples — description may be empty.
    """
    t = Table.grid(padding=(0, 2))
    t.add_column(style="bold bright_yellow", width=4)
    t.add_column(style="bold white")
    t.add_column(style="dim white")

    for idx, (label, desc) in enumerate(options, 1):
        t.add_row(f"[{idx}]", label, desc)

    subtitle = f"[dim]{status_line}[/dim]" if status_line else ""
    console.print(Panel(t, title=f"[bold cyan]{title}[/bold cyan]",
                        subtitle=subtitle, border_style="cyan",
                        padding=(1, 3)))


# ─── Input helpers ────────────────────────────────────────────────────────────

def prompt(label: str, default: str = "") -> str:
    """Generic text prompt."""
    tag = f"[bold cyan]{label}[/bold cyan]"
    if default:
        tag += f" [dim](default: {default})[/dim]"
    console.print(f"  {tag}", end="  ")
    val = input("").strip()
    return val if val else default


def menu_choice(max_choice: int) -> int:
    """Ask the user to pick a menu number; loops until valid."""
    while True:
        raw = prompt("Choice")
        if raw.isdigit() and 1 <= int(raw) <= max_choice:
            return int(raw)
        error(f"Please enter a number between 1 and {max_choice}.")


def confirm(question: str, default: bool = False) -> bool:
    """Yes/No confirmation prompt."""
    suffix = "[Y/n]" if default else "[y/N]"
    console.print(f"  [bold yellow]?[/bold yellow]  {question} [dim]{suffix}[/dim]  ", end="")
    raw = input("").strip().lower()
    if raw == "":
        return default
    return raw in ("y", "yes")


def parse_selection(raw: str, max_idx: int) -> list[int]:
    """
    Parse a human selection string into a sorted list of 0-based indices.
    Accepts: "all", "1,3,5", "2-7", "1,4-6,9"
    Returns 0-based indices.
    """
    if raw.strip().lower() == "all":
        return list(range(max_idx))

    indices: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if "-" in part:
            lo, _, hi = part.partition("-")
            if lo.isdigit() and hi.isdigit():
                lo_i, hi_i = int(lo) - 1, int(hi) - 1
                indices.update(range(max(0, lo_i), min(max_idx, hi_i + 1)))
        elif part.isdigit():
            i = int(part) - 1
            if 0 <= i < max_idx:
                indices.add(i)
    return sorted(indices)


# ─── Table builders ───────────────────────────────────────────────────────────

def user_table(users: list[dict], title: str = "Users",
               extra_cols: list[str] | None = None) -> Table:
    """Build a Rich Table from a list of user dicts."""
    tbl = Table(title=f"[bold cyan]{title}[/bold cyan]",
                box=box.ROUNDED, border_style="cyan",
                header_style="bold white", show_lines=False,
                row_styles=["", "dim"])
    tbl.add_column("#",            style="bright_yellow", width=5, justify="right")
    tbl.add_column("Username",     style="bold white",    min_width=22)
    tbl.add_column("Full Name",    style="white",         min_width=22)
    if extra_cols:
        for col in extra_cols:
            tbl.add_column(col, style="dim white")

    for i, u in enumerate(users, 1):
        row = [str(i), u.get("username", "—"), u.get("full_name", "—")]
        if extra_cols:
            for col in extra_cols:
                row.append(str(u.get(col.lower(), "—")))
        tbl.add_row(*row)

    return tbl


def stats_panel(info: dict) -> None:
    """Print account stats in a 2-column info panel."""
    g = Table.grid(padding=(0, 4))
    g.add_column(style="dim cyan",  width=24)
    g.add_column(style="bold white")

    rows = [
        ("Username",           f"@{info.get('username', '—')}"),
        ("Full Name",          info.get("full_name", "—")),
        ("Bio",                info.get("biography", "—") or "—"),
        ("Followers",          f"{info.get('follower_count', 0):,}"),
        ("Following",          f"{info.get('following_count', 0):,}"),
        ("Posts",              f"{info.get('media_count', 0):,}"),
        ("Non-Followers",      f"{info.get('non_followers', 0):,}"),
        ("Mutual Followers",   f"{info.get('mutual_count', 0):,}"),
        ("Account Type",       "Private" if info.get("is_private") else "Public"),
    ]
    for label, value in rows:
        g.add_row(f"{label}:", value)

    console.print(Panel(g, title="[bold cyan]Account Information[/bold cyan]",
                        border_style="cyan", padding=(1, 3)))


# ─── Progress / countdown ─────────────────────────────────────────────────────

def make_progress() -> Progress:
    """Return a configured Rich Progress bar for batch operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[bold white]{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )


def countdown(seconds: int, label: str = "Next action in") -> bool:
    """
    Show a live countdown. Returns False if interrupted by Ctrl-C,
    True if countdown completed normally.
    """
    try:
        for remaining in range(seconds, 0, -1):
            console.print(
                f"  [dim]{label}[/dim] [bold yellow]{remaining:3d}s[/bold yellow]",
                end="\r",
            )
            time.sleep(1)
        console.print(" " * 50, end="\r")   # clear the line
        return True
    except KeyboardInterrupt:
        console.print()
        warning("Countdown interrupted — stopping automation.")
        return False


def random_delay(min_s: int, max_s: int) -> bool:
    """Sleep for a random number of seconds in [min_s, max_s]. Returns False on interrupt."""
    secs = random.randint(min_s, max_s)
    return countdown(secs)


# ─── Misc ─────────────────────────────────────────────────────────────────────

def clear() -> None:
    """Print blank lines to visually separate sections."""
    console.print("\n" * 1)


def press_enter() -> None:
    console.print("\n  [dim]Press Enter to continue…[/dim]  ", end="")
    input("")