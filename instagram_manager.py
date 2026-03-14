#!/usr/bin/env python3
"""
instagram_manager.py — Main Entry Point
==========================================
Instagram Manager CLI v1.0.0

A feature-rich command-line tool for managing your Instagram followers and
following list.  Built with instagrapi + Rich for a clean terminal experience.

Usage:
    python instagram_manager.py

⚠  IMPORTANT DISCLAIMER:
    This tool uses an unofficial, third-party Instagram API client (instagrapi).
    Use it responsibly and sparingly to avoid account restrictions.  Instagram
    may change its private API at any time.  The authors are not responsible
    for any account bans or data loss.

Author:   Instagram Manager CLI Project
License:  MIT
"""

import sys
import os
from pathlib import Path

# ── Dependency check ──────────────────────────────────────────────────────────
def _check_deps() -> None:
    missing = []
    for pkg in ("instagrapi", "rich"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"\n[ERROR] Missing dependencies: {', '.join(missing)}")
        print("Run:  pip install -r requirements.txt\n")
        sys.exit(1)

_check_deps()

# ── Imports (after deps confirmed) ────────────────────────────────────────────
from modules.display import (
    console, show_banner, section, divider, success, error, warning, info,
    action, show_menu, menu_choice, confirm, stats_panel, press_enter, clear,
)
from modules.logger     import log_action, get_log_lines, clear_logs, log_file_path
from modules.settings   import load_settings, save_settings, update_setting, reset_settings
from modules.auth       import (
    login_with_credentials, login_with_session,
    logout, has_saved_session, get_saved_username,
)
from modules.client     import InstagramClient
from modules.followers  import (
    display_followers, display_following, display_non_followers,
    display_mutual_followers, unfollow_non_followers, unfollow_all,
    selective_unfollow,
)
from modules.export     import export_menu

from rich.table  import Table
from rich.panel  import Panel
from rich        import box


# ─── Global client instance ───────────────────────────────────────────────────

_client = InstagramClient()
_current_user: str = ""


# ═════════════════════════════════════════════════════════════════════════════
# AUTH MENU
# ═════════════════════════════════════════════════════════════════════════════

def auth_menu() -> bool:
    """
    Show the login/session menu.
    Returns True if the user is successfully logged in, False to quit.
    """
    global _current_user

    while True:
        show_banner()

        # Build dynamic status line
        saved = has_saved_session()
        saved_user = get_saved_username()
        status = f"Saved session: @{saved_user}" if saved else "No saved session"

        opts = [
            ("Login with Username & Password",  "Fresh login"),
        ]
        if saved:
            opts.append(("Use Saved Session",   f"Resume as @{saved_user}"))
        opts.append(("Exit",                    "Quit the application"))

        show_menu("Authentication", opts, status_line=status)
        choice = menu_choice(len(opts))

        if choice == 1:
            # ── Fresh login ──────────────────────────────────────────────
            try:
                _current_user = login_with_credentials(_client.raw)
                _client.set_logged_in(_current_user)
                return True
            except RuntimeError as exc:
                error(str(exc))
                press_enter()

        elif choice == 2 and saved:
            # ── Restore session ──────────────────────────────────────────
            try:
                _current_user = login_with_session(_client.raw)
                _client.set_logged_in(_current_user)
                return True
            except RuntimeError as exc:
                error(str(exc))
                press_enter()

        else:
            # ── Exit ─────────────────────────────────────────────────────
            console.print("\n  [dim]Goodbye![/dim]\n")
            return False


# ═════════════════════════════════════════════════════════════════════════════
# SETTINGS MENU
# ═════════════════════════════════════════════════════════════════════════════

def settings_menu() -> None:
    """Interactive automation settings editor."""
    while True:
        section("Automation Settings")
        cfg = load_settings()

        # Print current values
        t = Table.grid(padding=(0, 4))
        t.add_column(style="dim cyan", width=28)
        t.add_column(style="bold white")
        t.add_row("Min delay:",               f"{cfg['min_delay']}s")
        t.add_row("Max delay:",               f"{cfg['max_delay']}s")
        t.add_row("Max unfollows/session:",   str(cfg['max_unfollows_per_session']))
        t.add_row("Random delay:",            "✔ Enabled" if cfg['random_delay_enabled'] else "✘ Disabled")
        t.add_row("Logging:",                 "✔ Enabled" if cfg['logging_enabled']       else "✘ Disabled")
        t.add_row("Confirm bulk actions:",    "✔ Yes"     if cfg['confirm_bulk_actions']  else "✘ No")
        console.print(Panel(t, title="[bold cyan]Current Settings[/bold cyan]",
                            border_style="cyan", padding=(1, 3)))

        show_menu(
            "Automation Settings",
            [
                ("Change Min Delay",            f"Currently {cfg['min_delay']}s"),
                ("Change Max Delay",            f"Currently {cfg['max_delay']}s"),
                ("Set Max Unfollows / Session", f"Currently {cfg['max_unfollows_per_session']}"),
                ("Toggle Random Delay",         "On" if cfg['random_delay_enabled'] else "Off"),
                ("Toggle Activity Logging",     "On" if cfg['logging_enabled']       else "Off"),
                ("Toggle Bulk-Action Confirm",  "On" if cfg['confirm_bulk_actions']  else "Off"),
                ("Reset to Defaults",           ""),
                ("Back",                        ""),
            ],
        )
        choice = menu_choice(8)

        if choice == 1:
            raw = console.input("  [bold cyan]New min delay (seconds):[/bold cyan]  ").strip()
            if raw.isdigit() and int(raw) >= 1:
                update_setting("min_delay", int(raw))
                success(f"Min delay set to {raw}s")
            else:
                error("Invalid value — must be a positive integer.")

        elif choice == 2:
            raw = console.input("  [bold cyan]New max delay (seconds):[/bold cyan]  ").strip()
            if raw.isdigit() and int(raw) >= 1:
                update_setting("max_delay", int(raw))
                success(f"Max delay set to {raw}s")
            else:
                error("Invalid value — must be a positive integer.")

        elif choice == 3:
            raw = console.input("  [bold cyan]Max unfollows per session:[/bold cyan]  ").strip()
            if raw.isdigit() and int(raw) >= 1:
                update_setting("max_unfollows_per_session", int(raw))
                success(f"Session limit set to {raw}")
            else:
                error("Invalid value — must be a positive integer.")

        elif choice == 4:
            new_val = not cfg["random_delay_enabled"]
            update_setting("random_delay_enabled", new_val)
            success(f"Random delay {'enabled' if new_val else 'disabled'}.")

        elif choice == 5:
            new_val = not cfg["logging_enabled"]
            update_setting("logging_enabled", new_val)
            success(f"Logging {'enabled' if new_val else 'disabled'}.")

        elif choice == 6:
            new_val = not cfg["confirm_bulk_actions"]
            update_setting("confirm_bulk_actions", new_val)
            success(f"Bulk-action confirm {'enabled' if new_val else 'disabled'}.")

        elif choice == 7:
            if confirm("Reset ALL settings to factory defaults?", default=False):
                reset_settings()
                success("Settings reset to defaults.")

        elif choice == 8:
            return

        press_enter()


# ═════════════════════════════════════════════════════════════════════════════
# ACTIVITY LOGS MENU
# ═════════════════════════════════════════════════════════════════════════════

def logs_menu() -> None:
    """View and manage activity logs."""
    while True:
        section("Activity Logs")
        lines = get_log_lines(max_lines=50)

        if not lines:
            warning("Log file is empty.")
        else:
            info(f"Showing last {len(lines)} log entries  ({log_file_path()})\n")
            for line in lines:
                console.print(f"  [dim]{line.rstrip()}[/dim]")

        console.print()
        show_menu(
            "Log Options",
            [
                ("Refresh Logs",    "Reload the latest entries"),
                ("Clear Logs",      "Erase all log history"),
                ("Back",            ""),
            ],
        )
        choice = menu_choice(3)

        if choice == 1:
            continue   # loop re-reads
        elif choice == 2:
            if confirm("Clear all log history permanently?", default=False):
                clear_logs()
                success("Logs cleared.")
        elif choice == 3:
            return


# ═════════════════════════════════════════════════════════════════════════════
# HELP PANEL
# ═════════════════════════════════════════════════════════════════════════════

def show_help() -> None:
    section("Help & Command Reference")
    help_text = """
[bold cyan]Instagram Manager CLI[/bold cyan] — Quick Reference

[bold white]Navigation[/bold white]
  • Type the [bold yellow]number[/bold yellow] shown beside each option and press Enter.
  • At any selection prompt, pressing [bold yellow]Ctrl-C[/bold yellow] safely cancels an ongoing action.

[bold white]Safety System[/bold white]
  • A random delay is inserted between every unfollow action (default 20–90s).
  • A session cap limits how many unfollows run in one go (default 50).
  • Both values are adjustable in [bold cyan]Automation Settings[/bold cyan].

[bold white]Selective Unfollow[/bold white]
  • Enter individual numbers:  [bold yellow]1,4,7[/bold yellow]
  • Enter ranges:              [bold yellow]2-10[/bold yellow]
  • Mix both:                  [bold yellow]1,3-6,9[/bold yellow]
  • Select all:                [bold yellow]all[/bold yellow]

[bold white]Exporting Data[/bold white]
  • Exports are saved in the [bold]exports/[/bold] directory.
  • Supported formats: [bold]CSV[/bold], [bold]JSON[/bold], [bold]TXT[/bold].

[bold white]Session Storage[/bold white]
  • Sessions are stored in [bold]session.json[/bold] (local machine only).
  • Use "Logout" to delete the session file.

[bold white]Logs[/bold white]
  • All actions are recorded in [bold]logs/instagram_manager.log[/bold].
  • View or clear them from the Activity Logs menu.

[bold white]Important Notice[/bold white]
  [yellow]⚠[/yellow]  This tool uses an unofficial Instagram API.  Use it responsibly
     to avoid account restrictions.  Space out your sessions and avoid
     unfollowing hundreds of accounts in rapid succession.
"""
    console.print(Panel(help_text, border_style="cyan", padding=(1, 3)))


# ═════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ═════════════════════════════════════════════════════════════════════════════

def main_menu() -> None:
    """Primary application loop shown after a successful login."""
    while True:
        show_banner()
        status = f"Logged in as @{_current_user}" if _current_user else "Not logged in"

        show_menu(
            "Instagram Manager",
            [
                ("View Account Information",   "Stats & overview"),
                ("List Followers",             "See who follows you"),
                ("List Following",             "See who you follow"),
                ("Show Non-Followers",         "They don't follow back"),
                ("Show Mutual Followers",      "Both follow each other"),
                ("Unfollow Non-Followers",     "Auto-clean non-followers"),
                ("Unfollow All",               "Remove all following"),
                ("Selective Unfollow",         "Choose who to unfollow"),
                ("Export User Lists",          "CSV / JSON / TXT"),
                ("Automation Settings",        "Delays, limits, options"),
                ("View Activity Logs",         "Review past actions"),
                ("Help",                       "Commands & safety tips"),
                ("Logout",                     "Switch account / clear session"),
                ("Exit",                       "Quit the application"),
            ],
            status_line=status,
        )

        choice = menu_choice(14)

        # ── Dispatch ──────────────────────────────────────────────────────
        if choice == 1:
            _account_info()

        elif choice == 2:
            display_followers(_client)
            press_enter()

        elif choice == 3:
            display_following(_client)
            press_enter()

        elif choice == 4:
            display_non_followers(_client)
            press_enter()

        elif choice == 5:
            display_mutual_followers(_client)
            press_enter()

        elif choice == 6:
            unfollow_non_followers(_client)
            press_enter()

        elif choice == 7:
            unfollow_all(_client)
            press_enter()

        elif choice == 8:
            selective_unfollow(_client)
            press_enter()

        elif choice == 9:
            export_menu(_client)

        elif choice == 10:
            settings_menu()

        elif choice == 11:
            logs_menu()

        elif choice == 12:
            show_help()
            press_enter()

        elif choice == 13:
            _do_logout()
            return   # back to auth menu

        elif choice == 14:
            console.print("\n  [dim]Goodbye![/dim]\n")
            log_action("Application exited normally")
            sys.exit(0)


# ─── Account info helper ──────────────────────────────────────────────────────

def _account_info() -> None:
    section("Account Information")
    info("Loading account data …")
    try:
        data = _client.get_account_info()
        stats_panel(data)
        log_action(f"Viewed account info for @{data.get('username', '?')}")
    except Exception as exc:
        error(f"Could not fetch account info: {exc}")
        log_action(f"Error fetching account info: {exc}", level="error")
    press_enter()


# ─── Logout helper ────────────────────────────────────────────────────────────

def _do_logout() -> None:
    global _current_user
    if confirm("Log out and delete saved session?", default=False):
        logout(_client.raw)
        _current_user = ""
        _client._user_id = None
        _client._username = None
        _client.refresh_cache()
        press_enter()
    else:
        info("Logout cancelled.")


# ═════════════════════════════════════════════════════════════════════════════
# APPLICATION ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Top-level application loop: auth → main menu → repeat until exit."""
    try:
        while True:
            logged_in = auth_menu()
            if not logged_in:
                break
            main_menu()

    except KeyboardInterrupt:
        console.print("\n\n  [dim]Interrupted — goodbye![/dim]\n")
        log_action("Application terminated by keyboard interrupt")
        sys.exit(0)

    except Exception as exc:
        console.print(f"\n  [bold red]Fatal error:[/bold red] {exc}\n")
        log_action(f"Fatal error: {exc}", level="error")
        sys.exit(1)


if __name__ == "__main__":
    main()