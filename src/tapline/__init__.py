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
    expedia,
    geckoterminal,
    gmgn,
    goplus,
    imovelweb,
    instagram,
    linkedin,
    pinterest,
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
    Expedia,
    Geckoterminal,
    Gmgn,
    Goplus,
    Imovelweb,
    Instagram,
    Linkedin,
    Pinterest,
    Ponsfamily,
    Pumpfun,
    SyncAirbnb,
    SyncBirdeye,
    SyncExpedia,
    SyncGeckoterminal,
    SyncGmgn,
    SyncGoplus,
    SyncImovelweb,
    SyncInstagram,
    SyncLinkedin,
    SyncPinterest,
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
    "CursorCompletion",
    "CursorCompletionValue",
    "CursorPagination",
    "ErrorCode",
    "ErrorDetail",
    "Expedia",
    "Geckoterminal",
    "Gmgn",
    "Goplus",
    "Headers",
    "Imovelweb",
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
    "Ponsfamily",
    "Pumpfun",
    "RateLimitError",
    "SyncAirbnb",
    "SyncBirdeye",
    "SyncExpedia",
    "SyncGeckoterminal",
    "SyncGmgn",
    "SyncGoplus",
    "SyncImovelweb",
    "SyncInstagram",
    "SyncLinkedin",
    "SyncPinterest",
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
    "expedia",
    "geckoterminal",
    "gmgn",
    "goplus",
    "imovelweb",
    "instagram",
    "linkedin",
    "not_given",
    "pinterest",
    "ponsfamily",
    "pumpfun",
    "resources",
    "tiktok",
    "twitter",
    "youtube",
    "zillow",
]
