"""
client.py — Instagram Client Wrapper
======================================
Wraps instagrapi.Client to provide a clean, cache-aware API used by the
rest of the application.  Converts raw instagrapi models into plain dicts
so the rest of the code stays decoupled from the library's data classes.
"""

from __future__ import annotations

from typing import Optional
from instagrapi import Client
from instagrapi.exceptions import UserNotFound, PrivateAccount


# ─── Type alias ───────────────────────────────────────────────────────────────
UserDict = dict  # {"user_id": str, "username": str, "full_name": str}


class InstagramClient:
    """Thin, cache-aware wrapper around instagrapi.Client."""

    def __init__(self) -> None:
        self._cl = Client()
        self._user_id: Optional[str] = None
        self._username: Optional[str] = None

        # In-memory cache so we don't hammer the API on every menu visit
        self._followers_cache: Optional[list[UserDict]] = None
        self._following_cache: Optional[list[UserDict]] = None

    # ── Raw instagrapi client (for auth module) ────────────────────────────
    @property
    def raw(self) -> Client:
        return self._cl

    # ── Identity ──────────────────────────────────────────────────────────
    @property
    def username(self) -> str:
        return self._username or ""

    def set_logged_in(self, username: str) -> None:
        """Called by auth module after a successful login."""
        self._username = username
        try:
            info = self._cl.user_info_by_username(username)
            self._user_id = str(info.pk)
        except Exception:
            # Fall back to the cached value on the client object
            self._user_id = str(getattr(self._cl, "user_id", ""))

    # ── Account info ──────────────────────────────────────────────────────
    def get_account_info(self) -> dict:
        """Return a plain dict with account statistics."""
        if not self._user_id:
            raise RuntimeError("Not logged in.")
        info = self._cl.user_info(self._user_id)

        # Compute derived stats using cached lists
        followers  = self.get_followers(use_cache=True)
        following  = self.get_following(use_cache=True)
        follower_ids = {u["user_id"] for u in followers}
        following_ids = {u["user_id"] for u in following}
        mutual_count = len(follower_ids & following_ids)
        non_followers = len(following_ids - follower_ids)

        return {
            "username":        info.username,
            "full_name":       info.full_name or "",
            "biography":       info.biography or "",
            "follower_count":  info.follower_count,
            "following_count": info.following_count,
            "media_count":     info.media_count,
            "is_private":      info.is_private,
            "non_followers":   non_followers,
            "mutual_count":    mutual_count,
        }

    # ── Followers / Following ─────────────────────────────────────────────
    def get_followers(self, use_cache: bool = True) -> list[UserDict]:
        """Return a list of followers as plain dicts."""
        if use_cache and self._followers_cache is not None:
            return self._followers_cache
        if not self._user_id:
            raise RuntimeError("Not logged in.")
        raw = self._cl.user_followers(self._user_id)
        self._followers_cache = [_to_dict(u) for u in raw.values()]
        return self._followers_cache

    def get_following(self, use_cache: bool = True) -> list[UserDict]:
        """Return a list of accounts the user follows as plain dicts."""
        if use_cache and self._following_cache is not None:
            return self._following_cache
        if not self._user_id:
            raise RuntimeError("Not logged in.")
        raw = self._cl.user_following(self._user_id)
        self._following_cache = [_to_dict(u) for u in raw.values()]
        return self._following_cache

    def refresh_cache(self) -> None:
        """Clear the in-memory cache to force a fresh API pull."""
        self._followers_cache = None
        self._following_cache = None

    # ── Derived lists ─────────────────────────────────────────────────────
    def get_non_followers(self) -> list[UserDict]:
        """Accounts you follow that do NOT follow you back."""
        following  = self.get_following(use_cache=True)
        follower_ids = {u["user_id"] for u in self.get_followers(use_cache=True)}
        return [u for u in following if u["user_id"] not in follower_ids]

    def get_mutual_followers(self) -> list[UserDict]:
        """Accounts that follow you and that you follow back."""
        followers = self.get_followers(use_cache=True)
        following_ids = {u["user_id"] for u in self.get_following(use_cache=True)}
        return [u for u in followers if u["user_id"] in following_ids]

    # ── Actions ───────────────────────────────────────────────────────────
    def unfollow_user(self, user_id: str) -> bool:
        """
        Unfollow a single user.  Returns True on success, False on failure.
        Invalidates the following cache on success.
        """
        try:
            result = self._cl.user_unfollow(int(user_id))
            if result:
                # Remove from cache immediately so derived lists stay accurate
                if self._following_cache is not None:
                    self._following_cache = [
                        u for u in self._following_cache if u["user_id"] != user_id
                    ]
            return bool(result)
        except Exception:
            return False

    def is_alive(self) -> bool:
        """Quick check that the session is still valid."""
        try:
            self._cl.get_timeline_feed()
            return True
        except Exception:
            return False


# ─── Private helper ───────────────────────────────────────────────────────────

def _to_dict(user) -> UserDict:
    """Convert an instagrapi UserShort (or User) model to a plain dict."""
    return {
        "user_id":   str(user.pk),
        "username":  user.username,
        "full_name": getattr(user, "full_name", "") or "",
    }