"""
export.py — Data Export Module
================================
Exports follower/following/non-follower lists to CSV, JSON, or TXT files.
All exports land in the `exports/` directory with timestamped filenames.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from modules.client import InstagramClient, UserDict
from modules.display import (
    console, section, success, error, info, warning, action, confirm,
    show_menu, menu_choice,
)
from modules.logger import log_action

EXPORT_DIR = Path("exports")
ExportFormat = Literal["csv", "json", "txt"]


# ─── File writers ─────────────────────────────────────────────────────────────

def _write_csv(path: Path, users: list[UserDict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["user_id", "username", "full_name"])
        writer.writeheader()
        writer.writerows(users)


def _write_json(path: Path, users: list[UserDict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(users, fh, indent=2, ensure_ascii=False)


def _write_txt(path: Path, users: list[UserDict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for u in users:
            fh.write(f"@{u['username']}  |  {u['full_name']}  |  {u['user_id']}\n")


_WRITERS = {
    "csv":  _write_csv,
    "json": _write_json,
    "txt":  _write_txt,
}


# ─── Core export ──────────────────────────────────────────────────────────────

def export_list(
    users: list[UserDict],
    list_name: str,
    fmt: ExportFormat,
) -> Path:
    """
    Write *users* to a file of the requested format.
    Returns the output Path.
    """
    EXPORT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{list_name}_{stamp}.{fmt}"
    path = EXPORT_DIR / filename

    _WRITERS[fmt](path, users)
    return path


# ─── Interactive export menu ──────────────────────────────────────────────────

def export_menu(client: InstagramClient) -> None:
    """Full interactive export workflow."""
    while True:
        section("Export User Lists")

        show_menu(
            "What to Export",
            [
                ("Followers List",      ""),
                ("Following List",      ""),
                ("Non-Followers List",  ""),
                ("Back",               ""),
            ],
        )
        choice = menu_choice(4)
        if choice == 4:
            return

        # ── Pick the list ──────────────────────────────────────────────
        action("Fetching data …")
        try:
            if choice == 1:
                users     = client.get_followers(use_cache=True)
                list_name = "followers"
            elif choice == 2:
                users     = client.get_following(use_cache=True)
                list_name = "following"
            else:
                users     = client.get_non_followers()
                list_name = "non_followers"
        except Exception as exc:
            error(f"Could not fetch list: {exc}")
            continue

        if not users:
            warning("The selected list is empty — nothing to export.")
            continue

        info(f"{len(users):,} user(s) will be exported.")

        # ── Pick the format ────────────────────────────────────────────
        show_menu(
            "Export Format",
            [
                ("CSV  (.csv)",  "Spreadsheet-compatible"),
                ("JSON (.json)", "Machine-readable"),
                ("TXT  (.txt)",  "Plain text, one per line"),
                ("Back",        ""),
            ],
        )
        fmt_choice = menu_choice(4)
        if fmt_choice == 4:
            continue

        fmt: ExportFormat = {1: "csv", 2: "json", 3: "txt"}[fmt_choice]  # type: ignore

        # ── Write ──────────────────────────────────────────────────────
        try:
            out = export_list(users, list_name, fmt)
            success(f"Exported {len(users):,} users → [bold]{out}[/bold]")
            log_action(f"Exported {list_name} ({len(users)} users) as {fmt} → {out}")
        except Exception as exc:
            error(f"Export failed: {exc}")
            log_action(f"Export error: {exc}", level="error")

        console.print()
        if not confirm("Export another list?", default=False):
            return