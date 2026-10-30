"""The official Python client for the Tapline API.

::

    import asyncio
    import os

    from tapline import TaplineClient
    from tapline.youtube import SearchSort


    async def main() -> None:
        async with TaplineClient(api_key=os.environ["TAPLINE_API_KEY"]) as tapline:
            comments = await tapline.youtube.comments(video_id="dQw4w9WgXcQ")
            results = await tapline.youtube.search(
                query="game of thrones", sort=SearchSort.VIEW_COUNT
            )

        print(comments.threads[0].comment.text, results.results[0].title)


    asyncio.run(main())

:class:`TaplineClient` is awaitable; :class:`SyncTaplineClient` is its blocking
twin. This module carries what every API has in common — the two clients, the
exception hierarchy, :class:`BaseModel` and the cursor protocol. An API's own
enums and response models live in its own module, so that ``SearchResponse``
means one thing under :mod:`tapline.youtube` and can mean another under the
next API Tapline adds.
"""

from . import (
    airbnb,
    birdeye,
    brave_search,
    expedia,
    facebook,
    facebook_ad_library,
    facebook_marketplace,
    geckoterminal,
    gmgn,
    goplus,
    imovelweb,
    indeed,
    instagram,
    linkedin,
    pinterest,
    pinterest_v2,
    ponsfamily,
    pumpfun,
    resources,
    tiktok,
    twitter,
    youtube,
    zillow,
)
from ._client import SyncTaplineClient, TaplineClient
from ._exceptions import (
    APIConnectionError,
    APIError,
    APIResponseValidationError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ErrorCode,
    ErrorDetail,
    InsufficientCreditsError,
    InternalServerError,
    InvalidCursorError,
    MissingAPIKeyError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    TaplineError,
    UnprocessableEntityError,
)
from ._models import BaseModel
from ._pagination import CursorCompletion, CursorCompletionValue, CursorPagination
from ._types import Headers, NotGiven, Timeout, not_given
from ._version import __title__, __version__
from .resources import (
    Airbnb,
    Birdeye,
    BraveSearch,
    Expedia,
    Facebook,
    FacebookAdLibrary,
    FacebookMarketplace,
    Geckoterminal,
    Gmgn,
    Goplus,
    Imovelweb,
    Indeed,
    Instagram,
    Linkedin,
    Pinterest,
    PinterestV2,
    Ponsfamily,
    Pumpfun,
    SyncAirbnb,
    SyncBirdeye,
    SyncBraveSearch,
    SyncExpedia,
    SyncFacebook,
    SyncFacebookAdLibrary,
    SyncFacebookMarketplace,
    SyncGeckoterminal,
    SyncGmgn,
    SyncGoplus,
    SyncImovelweb,
    SyncIndeed,
    SyncInstagram,
    SyncLinkedin,
    SyncPinterest,
    SyncPinterestV2,
    SyncPonsfamily,
    SyncPumpfun,
    SyncTiktok,
    SyncTwitter,
    SyncYouTube,
    SyncZillow,
    Tiktok,
    Twitter,
    YouTube,
    Zillow,
)

__all__ = [
    "APIConnectionError",
    "APIError",
    "APIResponseValidationError",
    "APIStatusError",
    "APITimeoutError",
    "Airbnb",
    "AuthenticationError",
    "BadRequestError",
    "BaseModel",
    "Birdeye",
    "BraveSearch",
    "CursorCompletion",
    "CursorCompletionValue",
    "CursorPagination",
    "ErrorCode",
    "ErrorDetail",
    "Expedia",
    "Facebook",
    "FacebookAdLibrary",
    "FacebookMarketplace",
    "Geckoterminal",
    "Gmgn",
    "Goplus",
    "Headers",
    "Imovelweb",
    "Indeed",
    "Instagram",
    "InsufficientCreditsError",
    "InternalServerError",
    "InvalidCursorError",
    "Linkedin",
    "MissingAPIKeyError",
    "NotFoundError",
    "NotGiven",
    "PermissionDeniedError",
    "Pinterest",
    "PinterestV2",
    "Ponsfamily",
    "Pumpfun",
    "RateLimitError",
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
    "SyncTaplineClient",
    "SyncTiktok",
    "SyncTwitter",
    "SyncYouTube",
    "SyncZillow",
    "TaplineClient",
    "TaplineError",
    "Tiktok",
    "Timeout",
    "Twitter",
    "UnprocessableEntityError",
    "YouTube",
    "Zillow",
    "__title__",
    "__version__",
    "airbnb",
    "birdeye",
    "brave_search",
    "expedia",
    "facebook",
    "facebook_ad_library",
    "facebook_marketplace",
    "geckoterminal",
    "gmgn",
    "goplus",
    "imovelweb",
    "indeed",
    "instagram",
    "linkedin",
    "not_given",
    "pinterest",
    "pinterest_v2",
    "ponsfamily",
    "pumpfun",
    "resources",
    "tiktok",
    "twitter",
    "youtube",
    "zillow",
]
