"""The API namespaces hanging off a client, one module per product."""

from __future__ import annotations

from .airbnb import Airbnb, SyncAirbnb
from .gmgn import Gmgn, SyncGmgn
from .youtube import SyncYouTube, YouTube

__all__ = ["Airbnb", "Gmgn", "SyncAirbnb", "SyncGmgn", "SyncYouTube", "YouTube"]
