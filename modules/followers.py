"""
followers.py — Follower Management Operations
===============================================
High-level follower actions: list, unfollow with safety delays,
selective unfollow, batch unfollow, progress reporting, and stop support.
"""

from __future__ import annotations

import random
import time
from typing import Optional

from modules.client import InstagramClient, UserDict
from modules.display import (
    console, section, success, error, warning, info, action,
    user_table, make_progress, countdown, random_delay, confirm,
    parse_selection, press_enter, divider,
)
from modules.logger import log_action
from modules.settings import load_settings


# ─── List helpers ─────────────────────────────────────────────────────────────

def display_followers(client: InstagramClient) -> None:
    """Fetch and display the user's follower list."""
    section("Your Followers")
    info("Fetching followers … this may take a moment.")
    try:
        users = client.get_followers(use_cache=False)
        if not users:
            warning("No followers found.")
            return
        console.print(user_table(users, title=f"Followers  ({len(users):,})"))
        console.print(f"\n  [bold green]Total followers: {len(users):,}[/bold green]")
        log_action(f"Listed {len(users)} followers")
    except Exception as exc:
        error(f"Could not fetch followers: {exc}")
        log_action(f"Error fetching followers: {exc}", level="error")


def display_following(client: InstagramClient) -> None:
    """Fetch and display the accounts the user follows."""
    section("Accounts You Follow")
    info("Fetching following list …")
    try:
        users = client.get_following(use_cache=False)
        if not users:
            warning("You are not following anyone.")
            return
        console.print(user_table(users, title=f"Following  ({len(users):,})"))
        console.print(f"\n  [bold green]Total following: {len(users):,}[/bold green]")
        log_action(f"Listed {len(users)} following")
    except Exception as exc:
        error(f"Could not fetch following list: {exc}")
        log_action(f"Error fetching following: {exc}", level="error")


def display_non_followers(client: InstagramClient) -> None:
    """Show accounts the user follows that do NOT follow back."""
    section("Non-Followers")
    info("Computing non-followers …")
    try:
        users = client.get_non_followers()
        if not users:
            success("Everyone you follow follows you back! 🎉")
            return
        console.print(user_table(users, title=f"Non-Followers  ({len(users):,})"))
        console.print(f"\n  [bold yellow]They don't follow you back: {len(users):,}[/bold yellow]")
        log_action(f"Listed {len(users)} non-followers")
    except Exception as exc:
        error(f"Could not compute non-followers: {exc}")
        log_action(f"Error fetching non-followers: {exc}", level="error")


def display_mutual_followers(client: InstagramClient) -> None:
    """Show accounts that follow each other mutually."""
    section("Mutual Followers")
    info("Computing mutual followers …")
    try:
        users = client.get_mutual_followers()
        if not users:
            warning("No mutual followers found.")
            return
        console.print(user_table(users, title=f"Mutual Followers  ({len(users):,})"))
        console.print(f"\n  [bold cyan]Mutual: {len(users):,}[/bold cyan]")
        log_action(f"Listed {len(users)} mutual followers")
    except Exception as exc:
        error(f"Could not compute mutual followers: {exc}")
        log_action(f"Error fetching mutual followers: {exc}", level="error")


# ─── Core unfollow engine ─────────────────────────────────────────────────────

def _unfollow_list(
    client: InstagramClient,
    users: list[UserDict],
    settings: dict,
    label: str = "Unfollowing",
) -> tuple[int, int]:
    """
    Unfollow every user in *users* with safety delays.

    Returns (succeeded, failed) counts.
    Stops early if the user presses Ctrl-C or the session limit is reached.
    """
    max_actions = settings.get("max_unfollows_per_session", 50)
    min_d       = settings.get("min_delay", 20)
    max_d       = settings.get("max_delay", 90)
    random_on   = settings.get("random_delay_enabled", True)

    to_process = users[:max_actions]
    skipped    = len(users) - len(to_process)

    if skipped:
        warning(
            f"Session limit is {max_actions}. "
            f"{skipped} user(s) will be skipped this run."
        )

    succeeded = 0
    failed    = 0

    console.print(
        f"\n  [dim]Delays: {min_d}–{max_d}s  |  "
        f"Max this session: {max_actions}  |  "
        f"Press [bold]Ctrl-C[/bold] to stop safely[/dim]\n"
    )

    with make_progress() as progress:
        task = progress.add_task(f"[cyan]{label}", total=len(to_process))
        for i, user in enumerate(to_process):
            uid  = user["user_id"]
            uname = user["username"]

            progress.update(task, description=f"[cyan]{label}[/cyan] → @{uname}")

            ok = client.unfollow_user(uid)
            if ok:
                succeeded += 1
                log_action(f"Unfollowed user: @{uname}")
            else:
                failed += 1
                log_action(f"Failed to unfollow: @{uname}", level="warning")

            progress.advance(task)

            # Don't delay after the last item
            if i < len(to_process) - 1:
                delay = random.randint(min_d, max_d) if random_on else min_d
                try:
                    if not countdown(delay):
                        warning("Stopped by user.")
                        break
                except KeyboardInterrupt:
                    warning("Stopped by user (Ctrl-C).")
                    break

    return succeeded, failed


def _show_unfollow_summary(succeeded: int, failed: int) -> None:
    divider()
    console.print(
        f"  [bold green]✔ Unfollowed:[/bold green] {succeeded}   "
        f"[bold red]✘ Failed:[/bold red] {failed}"
    )
    log_action(f"Unfollow batch complete — succeeded: {succeeded}, failed: {failed}")


# ─── Public unfollow actions ──────────────────────────────────────────────────

def unfollow_non_followers(client: InstagramClient) -> None:
    """Auto-unfollow all accounts that don't follow back."""
    section("Unfollow Non-Followers")
    try:
        users = client.get_non_followers()
        if not users:
            success("No non-followers to unfollow.")
            return

        info(f"Found {len(users):,} non-follower(s).")
        settings = load_settings()

        if settings.get("confirm_bulk_actions", True):
            if not confirm(
                f"Unfollow [bold yellow]{len(users)}[/bold yellow] non-follower(s)?",
                default=False,
            ):
                info("Cancelled.")
                return

        s, f = _unfollow_list(client, users, settings, label="Unfollowing non-followers")
        _show_unfollow_summary(s, f)

    except KeyboardInterrupt:
        warning("Unfollow operation interrupted.")
    except Exception as exc:
        error(f"Error during unfollow: {exc}")
        log_action(f"Error during unfollow non-followers: {exc}", level="error")


def unfollow_all(client: InstagramClient) -> None:
    """Unfollow every account in the following list."""
    section("Unfollow Everyone")
    try:
        users = client.get_following(use_cache=True)
        if not users:
            warning("You are not following anyone.")
            return

        info(f"You currently follow {len(users):,} account(s).")
        settings = load_settings()

        console.print(
            "\n  [bold red]⚠  WARNING:[/bold red]  "
            "This will unfollow [bold]ALL[/bold] accounts you follow.\n"
        )
        if not confirm(
            f"Are you absolutely sure you want to unfollow [bold red]{len(users)}[/bold red] account(s)?",
            default=False,
        ):
            info("Cancelled.")
            return

        # Second confirmation for a destructive bulk action
        if not confirm("Confirm again — this cannot be undone:", default=False):
            info("Cancelled.")
            return

        s, f = _unfollow_list(client, users, settings, label="Unfollowing everyone")
        _show_unfollow_summary(s, f)

    except KeyboardInterrupt:
        warning("Unfollow operation interrupted.")
    except Exception as exc:
        error(f"Error during unfollow all: {exc}")
        log_action(f"Error during unfollow all: {exc}", level="error")


def selective_unfollow(client: InstagramClient) -> None:
    """Display a numbered list and let the user choose who to unfollow."""
    section("Selective Unfollow")
    try:
        info("Fetching following list …")
        users = client.get_following(use_cache=True)
        if not users:
            warning("You are not following anyone.")
            return

        console.print(user_table(users, title=f"Following  ({len(users):,})"))
        console.print(
            "\n  [dim]Enter numbers/ranges to select users.[/dim]"
            "  [dim]Examples:[/dim] [bold yellow]1,3,5[/bold yellow]  "
            "[bold yellow]2-7[/bold yellow]  [bold yellow]all[/bold yellow]\n"
        )

        raw = console.input("  [bold cyan]Selection:[/bold cyan]  ").strip()
        if not raw:
            info("No selection made. Returning to menu.")
            return

        indices = parse_selection(raw, len(users))
        if not indices:
            warning("No valid users selected.")
            return

        selected = [users[i] for i in indices]
        info(f"{len(selected)} user(s) selected:")
        for u in selected[:10]:
            console.print(f"    [dim]•[/dim] @{u['username']}")
        if len(selected) > 10:
            console.print(f"    [dim]  … and {len(selected) - 10} more[/dim]")

        settings = load_settings()
        if not confirm(f"\n  Unfollow these [bold yellow]{len(selected)}[/bold yellow] user(s)?", default=False):
            info("Cancelled.")
            return

        s, f = _unfollow_list(client, selected, settings, label="Unfollowing selected")
        _show_unfollow_summary(s, f)

    except KeyboardInterrupt:
        warning("Selective unfollow interrupted.")
    except Exception as exc:
        error(f"Error during selective unfollow: {exc}")
        log_action(f"Error during selective unfollow: {exc}", level="error")