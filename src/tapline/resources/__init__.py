"""The API namespaces hanging off a client, one module per product."""

from __future__ import annotations

from .airbnb import Airbnb, SyncAirbnb
from .birdeye import Birdeye, SyncBirdeye
from .brave_search import BraveSearch, SyncBraveSearch
from .expedia import Expedia, SyncExpedia
from .facebook import Facebook, SyncFacebook
from .facebook_ad_library import FacebookAdLibrary, SyncFacebookAdLibrary
from .facebook_marketplace import FacebookMarketplace, SyncFacebookMarketplace
from .geckoterminal import Geckoterminal, SyncGeckoterminal
from .gmgn import Gmgn, SyncGmgn
from .goplus import Goplus, SyncGoplus
from .imovelweb import Imovelweb, SyncImovelweb
from .indeed import Indeed, SyncIndeed
from .instagram import Instagram, SyncInstagram
from .linkedin import Linkedin, SyncLinkedin
from .pinterest import Pinterest, SyncPinterest
from .pinterest_v2 import PinterestV2, SyncPinterestV2
from .ponsfamily import Ponsfamily, SyncPonsfamily
from .pumpfun import Pumpfun, SyncPumpfun
from .tiktok import SyncTiktok, Tiktok
from .twitter import SyncTwitter, Twitter
from .youtube import SyncYouTube, YouTube
from .zillow import SyncZillow, Zillow

__all__ = [
    "Airbnb",
    "Birdeye",
    "BraveSearch",
    "Expedia",
    "Facebook",
    "FacebookAdLibrary",
    "FacebookMarketplace",
    "Geckoterminal",
    "Gmgn",
    "Goplus",
    "Imovelweb",
    "Indeed",
    "Instagram",
    "Linkedin",
    "Pinterest",
    "PinterestV2",
    "Ponsfamily",
    "Pumpfun",
    "SyncAirbnb",
    "SyncBirdeye",
    "SyncBraveSearch",
    "SyncExpedia",
    "SyncFacebook",
    "SyncFacebookAdLibrary",
    "SyncFacebookMarketplace",
    "SyncGeckoterminal",
    "SyncGmgn",
    "SyncGoplus",
    "SyncImovelweb",
    "SyncIndeed",
    "SyncInstagram",
    "SyncLinkedin",
    "SyncPinterest",
    "SyncPinterestV2",
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
