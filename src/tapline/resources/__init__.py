"""The API namespaces hanging off a client, one module per product."""

from __future__ import annotations

from .airbnb import Airbnb, SyncAirbnb
from .geckoterminal import Geckoterminal, SyncGeckoterminal
from .gmgn import Gmgn, SyncGmgn
from .goplus import Goplus, SyncGoplus
from .ponsfamily import Ponsfamily, SyncPonsfamily
from .twitter import SyncTwitter, Twitter
from .youtube import SyncYouTube, YouTube

__all__ = [
    "Airbnb",
    "Geckoterminal",
    "Gmgn",
    "Goplus",
    "Ponsfamily",
    "SyncAirbnb",
    "SyncGeckoterminal",
    "SyncGmgn",
    "SyncGoplus",
    "SyncPonsfamily",
    "SyncTwitter",
    "SyncYouTube",
    "Twitter",
    "YouTube",
]
