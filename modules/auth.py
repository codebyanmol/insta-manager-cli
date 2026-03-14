"""
auth.py — Authentication & Session Management
===============================================
Handles Instagram login (credentials + 2FA), session persistence,
and logout.  All session data is stored in session.json via instagrapi's
built-in serialisation.
"""

import getpass
import json
import os
from pathlib import Path
from typing import Optional

from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword,
    LoginRequired,
    TwoFactorRequired,
    ChallengeRequired,
    PleaseWaitFewMinutes,
    RateLimitError,
)

from modules.display import console, success, error, warning, info, section, action
from modules.logger import log_action

SESSION_FILE = Path("session.json")
CREDS_FILE   = Path(".creds")   # stores only the username (no password stored)


# ─── Session helpers ──────────────────────────────────────────────────────────

def has_saved_session() -> bool:
    return SESSION_FILE.exists() and SESSION_FILE.stat().st_size > 10


def _saved_username() -> str:
    """Return the username stored in the session file (if any)."""
    if SESSION_FILE.exists():
        try:
            data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            return data.get("username", "")
        except Exception:
            pass
    return ""


def _save_username(username: str) -> None:
    """Persist just the username to CREDS_FILE for display purposes."""
    CREDS_FILE.write_text(username, encoding="utf-8")


def get_saved_username() -> str:
    """Return the last-used username from the creds hint file."""
    if CREDS_FILE.exists():
        return CREDS_FILE.read_text(encoding="utf-8").strip()
    return _saved_username()


# ─── Login flows ──────────────────────────────────────────────────────────────

def login_with_credentials(client: Client) -> str:
    """
    Interactive fresh login.  Handles 2FA and simple challenge prompts.
    Returns the logged-in username on success; raises on failure.
    """
    section("Instagram Login")
    console.print("  [dim]Enter your Instagram credentials.[/dim]\n")

    username = console.input("  [bold cyan]Username:[/bold cyan]  ").strip()
    password = getpass.getpass("  Password:  ")

    action(f"Logging in as @{username} …")

    try:
        client.login(username, password)
        _post_login(client, username)
        return username

    except TwoFactorRequired:
        warning("Two-factor authentication required.")
        code = console.input("  [bold yellow]2FA Code:[/bold yellow]  ").strip()
        try:
            client.login(username, password, verification_code=code)
            _post_login(client, username)
            return username
        except Exception as exc:
            raise RuntimeError(f"2FA login failed: {exc}") from exc

    except ChallengeRequired:
        warning("Instagram sent a security challenge.")
        _handle_challenge(client)
        client.login(username, password)
        _post_login(client, username)
        return username

    except BadPassword:
        raise RuntimeError("Incorrect username or password.")

    except PleaseWaitFewMinutes as exc:
        raise RuntimeError(f"Instagram rate-limited this device. Try again later. ({exc})")

    except RateLimitError as exc:
        raise RuntimeError(f"Rate limit hit. Please wait before retrying. ({exc})")

    except Exception as exc:
        raise RuntimeError(f"Login failed: {exc}") from exc


def login_with_session(client: Client) -> str:
    """
    Restore a previously saved session without re-entering credentials.
    Returns the username on success; raises if the session is expired/invalid.
    """
    if not has_saved_session():
        raise RuntimeError("No saved session found. Please log in first.")

    action("Restoring saved session …")
    try:
        client.load_settings(str(SESSION_FILE))
        # Validate that the session is still alive
        client.get_timeline_feed()
        username = get_saved_username() or client.username or "unknown"
        log_action(f"Session restored for @{username}")
        success(f"Logged in as @{username} (saved session)")
        return username

    except LoginRequired:
        raise RuntimeError(
            "Saved session has expired. Please log in with your credentials."
        )
    except Exception as exc:
        raise RuntimeError(f"Could not restore session: {exc}") from exc


def logout(client: Optional[Client] = None) -> None:
    """Log out of Instagram and delete local session/credential files."""
    try:
        if client:
            client.logout()
    except Exception:
        pass

    for f in (SESSION_FILE, CREDS_FILE):
        if f.exists():
            f.unlink()

    log_action("User logged out — session deleted")
    success("Logged out successfully. Session files removed.")


# ─── Private helpers ──────────────────────────────────────────────────────────

def _post_login(client: Client, username: str) -> None:
    """Save session, log the event, and show confirmation."""
    client.dump_settings(str(SESSION_FILE))
    _save_username(username)
    log_action(f"Logged in successfully as @{username}")
    success(f"Logged in as @{username}")


def _handle_challenge(client: Client) -> None:
    """
    Minimal interactive challenge handler.
    Tells the user to verify their account externally and waits.
    """
    warning(
        "Instagram requires identity verification.\n"
        "  Please check your email/phone for a confirmation link,\n"
        "  then press Enter here to continue."
    )
    input("  Press Enter after completing the challenge:  ")