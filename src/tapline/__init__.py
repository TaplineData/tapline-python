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
    geckoterminal,
    gmgn,
    goplus,
    instagram,
    pinterest,
    ponsfamily,
    pumpfun,
    resources,
    tiktok,
    twitter,
    youtube,
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
    Geckoterminal,
    Gmgn,
    Goplus,
    Instagram,
    Pinterest,
    Ponsfamily,
    Pumpfun,
    SyncAirbnb,
    SyncBirdeye,
    SyncGeckoterminal,
    SyncGmgn,
    SyncGoplus,
    SyncInstagram,
    SyncPinterest,
    SyncPonsfamily,
    SyncPumpfun,
    SyncTiktok,
    SyncTwitter,
    SyncYouTube,
    Tiktok,
    Twitter,
    YouTube,
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
    "Geckoterminal",
    "Gmgn",
    "Goplus",
    "Headers",
    "Instagram",
    "InsufficientCreditsError",
    "InternalServerError",
    "InvalidCursorError",
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
    "SyncGeckoterminal",
    "SyncGmgn",
    "SyncGoplus",
    "SyncInstagram",
    "SyncPinterest",
    "SyncPonsfamily",
    "SyncPumpfun",
    "SyncTaplineClient",
    "SyncTiktok",
    "SyncTwitter",
    "SyncYouTube",
    "TaplineClient",
    "TaplineError",
    "Tiktok",
    "Timeout",
    "Twitter",
    "UnprocessableEntityError",
    "YouTube",
    "__title__",
    "__version__",
    "airbnb",
    "birdeye",
    "geckoterminal",
    "gmgn",
    "goplus",
    "instagram",
    "not_given",
    "pinterest",
    "ponsfamily",
    "pumpfun",
    "resources",
    "tiktok",
    "twitter",
    "youtube",
]
