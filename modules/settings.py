"""
settings.py — Automation Settings Module
==========================================
Persists user-configurable automation parameters to settings.json.
Provides helpers to load, save, and update individual keys.
"""

import json
from pathlib import Path
from typing import Any

SETTINGS_FILE = Path("settings.json")

# Default values used on first run or for any missing key
DEFAULTS: dict[str, Any] = {
    "min_delay":                  20,    # seconds – minimum pause between actions
    "max_delay":                  90,    # seconds – maximum pause between actions
    "max_unfollows_per_session":  50,    # hard cap per automation run
    "random_delay_enabled":       True,  # randomise delay within [min, max]
    "logging_enabled":            True,  # write actions to log file
    "confirm_bulk_actions":       True,  # ask user before batch unfollow
}


# ─── Public API ───────────────────────────────────────────────────────────────

def load_settings() -> dict[str, Any]:
    """Load settings from disk, merging with defaults for any missing keys."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                saved = json.load(fh)
            merged = DEFAULTS.copy()
            merged.update(saved)
            return merged
        except (json.JSONDecodeError, OSError):
            pass           # fall through to defaults on corrupt file
    return DEFAULTS.copy()


def save_settings(settings: dict[str, Any]) -> None:
    """Persist *settings* dictionary to disk."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2)


def update_setting(key: str, value: Any) -> dict[str, Any]:
    """Update a single *key* in the stored settings and return the full dict."""
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
    return settings


def reset_settings() -> dict[str, Any]:
    """Restore all settings to their factory defaults."""
    save_settings(DEFAULTS.copy())
    return DEFAULTS.copy()