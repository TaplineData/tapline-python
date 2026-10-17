"""The API namespaces hanging off a client, one module per product."""

from __future__ import annotations

from .airbnb import Airbnb, SyncAirbnb
from .birdeye import Birdeye, SyncBirdeye
from .geckoterminal import Geckoterminal, SyncGeckoterminal
from .gmgn import Gmgn, SyncGmgn
from .goplus import Goplus, SyncGoplus
from .instagram import Instagram, SyncInstagram
from .linkedin import Linkedin, SyncLinkedin
from .pinterest import Pinterest, SyncPinterest
from .ponsfamily import Ponsfamily, SyncPonsfamily
from .pumpfun import Pumpfun, SyncPumpfun
from .tiktok import SyncTiktok, Tiktok
from .twitter import SyncTwitter, Twitter
from .youtube import SyncYouTube, YouTube
from .zillow import SyncZillow, Zillow

__all__ = [
    "Airbnb",
    "Birdeye",
    "Geckoterminal",
    "Gmgn",
    "Goplus",
    "Instagram",
    "Linkedin",
    "Pinterest",
    "Ponsfamily",
    "Pumpfun",
    "SyncAirbnb",
    "SyncBirdeye",
    "SyncGeckoterminal",
    "SyncGmgn",
    "SyncGoplus",
    "SyncInstagram",
    "SyncLinkedin",
    "SyncPinterest",
    "SyncPonsfamily",
    "SyncPumpfun",
    "SyncTiktok",
    "SyncTwitter",
    "SyncYouTube",
    "SyncZillow",
    "Tiktok",
    "Twitter",
    "YouTube",
    "Zillow",
]
