"""The API namespaces hanging off a client, one module per product."""

from __future__ import annotations

from .youtube import SyncYouTube, YouTube

__all__ = ["SyncYouTube", "YouTube"]
