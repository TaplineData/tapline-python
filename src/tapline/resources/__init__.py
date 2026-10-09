"""The API namespaces hanging off a client, one module per product."""

from __future__ import annotations

from .airbnb import Airbnb, SyncAirbnb
from .geckoterminal import Geckoterminal, SyncGeckoterminal
from .gmgn import Gmgn, SyncGmgn
from .goplus import Goplus, SyncGoplus
from .pinterest import Pinterest, SyncPinterest
from .ponsfamily import Ponsfamily, SyncPonsfamily
from .pumpfun import Pumpfun, SyncPumpfun
from .twitter import SyncTwitter, Twitter
from .youtube import SyncYouTube, YouTube

__all__ = [
    "Airbnb",
    "Geckoterminal",
    "Gmgn",
    "Goplus",
    "Pinterest",
    "Ponsfamily",
    "Pumpfun",
    "SyncAirbnb",
    "SyncGeckoterminal",
    "SyncGmgn",
    "SyncGoplus",
    "SyncPinterest",
    "SyncPonsfamily",
    "SyncPumpfun",
    "SyncTwitter",
    "SyncYouTube",
    "Twitter",
    "YouTube",
]
