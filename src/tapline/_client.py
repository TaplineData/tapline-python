"""The Tapline clients.

:class:`TaplineClient` is awaitable and :class:`SyncTaplineClient` blocks.
Async is the unprefixed name because that is how the API is expected to be
called: every endpoint fetches from its upstream site live, so a caller almost
always wants several in flight at once. Each client carries one namespace per
service (``airbnb``, ``birdeye``, ``geckoterminal``, ``gmgn``, ``goplus``, ``imovelweb``,
``instagram``, ``linkedin``, ``pinterest``, ``ponsfamily``, ``pumpfun``, ``tiktok``,
``twitter``, ``youtube``, ``zillow``),
all sharing its API key, connection pool and retry policy.
"""

from __future__ import annotations

import os

import httpx

from ._base_client import AsyncAPIClient, SyncAPIClient
from ._constants import DEFAULT_MAX_RETRIES
from ._types import Headers, NotGiven, Timeout, not_given
from .resources import (
    Airbnb,
    Birdeye,
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

__all__ = ["SyncTaplineClient", "TaplineClient"]


def _resolve_base_url(base_url: str | httpx.URL | None) -> str | httpx.URL | None:
    """The explicit argument, else ``TAPLINE_BASE_URL``, else ``None`` for the API root."""
    if base_url is not None:
        return base_url
    return os.environ.get("TAPLINE_BASE_URL")


class TaplineClient(AsyncAPIClient):
    """An awaitable client for the Tapline API.

    ::

        from tapline import TaplineClient

        tapline = TaplineClient(api_key=api_key)
        results = await tapline.youtube.search(query="game of thrones")

    The client owns a connection pool, so build one and keep it. Release it
    with ``await tapline.close()``, or scope it to a block::

        async with TaplineClient(api_key=api_key) as tapline:
            comments = await tapline.youtube.comments(video_id=video_id)
    """

    airbnb: Airbnb
    """The Airbnb endpoints."""

    birdeye: Birdeye
    """The Birdeye endpoints."""

    geckoterminal: Geckoterminal
    """The GeckoTerminal endpoints."""

    gmgn: Gmgn
    """The GMGN endpoints."""

    goplus: Goplus
    """The GoPlus Security endpoints."""

    imovelweb: Imovelweb
    """The imovelweb endpoints."""

    instagram: Instagram
    """The Instagram endpoints."""

    linkedin: Linkedin
    """The LinkedIn endpoints."""

    pinterest: Pinterest
    """The Pinterest endpoints."""

    ponsfamily: Ponsfamily
    """The Pons Family endpoints."""

    pumpfun: Pumpfun
    """The pump.fun endpoints."""

    tiktok: Tiktok
    """The TikTok endpoints."""

    twitter: Twitter
    """The Twitter (X) endpoints."""

    youtube: YouTube
    """The YouTube endpoints."""

    zillow: Zillow
    """The Zillow endpoints."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | NotGiven | None = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Headers | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Construct an awaitable Tapline client.

        Args:
            api_key: Your API key. Read from the ``TAPLINE_API_KEY``
                environment variable when omitted.
            base_url: Overrides the API root, for pointing the client at a
                proxy or a local server. A path prefix is kept and every request
                is mounted under it; a query string is refused, because each
                request writes its own. Read from the ``TAPLINE_BASE_URL``
                environment variable when omitted.
            timeout: Applies to every request that does not override it.
                Defaults to 60 seconds, 10 of them for connecting; ``None``
                waits indefinitely.
            max_retries: How many times a request may be retried after a
                connection failure, a 429, or a 5xx. Pass 0 to disable retries.
            default_headers: Headers to add to every request. They override the
                library's own where the names collide.
            http_client: An ``httpx.AsyncClient`` to send through, for custom
                proxies, transports, or connection limits. Closing this client
                closes it.

        Raises:
            MissingAPIKeyError: No key was passed and ``TAPLINE_API_KEY`` is
                unset.
            ValueError: ``base_url`` is not a URL or carries a query string, or
                ``max_retries`` is negative.
        """
        super().__init__(
            api_key=api_key,
            base_url=_resolve_base_url(base_url),
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            http_client=http_client,
        )
        self.airbnb = Airbnb(self)
        self.birdeye = Birdeye(self)
        self.geckoterminal = Geckoterminal(self)
        self.gmgn = Gmgn(self)
        self.goplus = Goplus(self)
        self.imovelweb = Imovelweb(self)
        self.instagram = Instagram(self)
        self.linkedin = Linkedin(self)
        self.pinterest = Pinterest(self)
        self.ponsfamily = Ponsfamily(self)
        self.pumpfun = Pumpfun(self)
        self.tiktok = Tiktok(self)
        self.twitter = Twitter(self)
        self.youtube = YouTube(self)
        self.zillow = Zillow(self)


class SyncTaplineClient(SyncAPIClient):
    """A blocking client for the Tapline API.

    ::

        from tapline import SyncTaplineClient

        tapline = SyncTaplineClient(api_key=api_key)
        results = tapline.youtube.search(query="game of thrones")

    The client owns a connection pool, so build one and keep it. Release it
    with ``tapline.close()``, or scope it to a block::

        with SyncTaplineClient(api_key=api_key) as tapline:
            comments = tapline.youtube.comments(video_id=video_id)
    """

    airbnb: SyncAirbnb
    """The Airbnb endpoints."""

    birdeye: SyncBirdeye
    """The Birdeye endpoints."""

    geckoterminal: SyncGeckoterminal
    """The GeckoTerminal endpoints."""

    gmgn: SyncGmgn
    """The GMGN endpoints."""

    goplus: SyncGoplus
    """The GoPlus Security endpoints."""

    imovelweb: SyncImovelweb
    """The imovelweb endpoints."""

    instagram: SyncInstagram
    """The Instagram endpoints."""

    linkedin: SyncLinkedin
    """The LinkedIn endpoints."""

    pinterest: SyncPinterest
    """The Pinterest endpoints."""

    ponsfamily: SyncPonsfamily
    """The Pons Family endpoints."""

    pumpfun: SyncPumpfun
    """The pump.fun endpoints."""

    tiktok: SyncTiktok
    """The TikTok endpoints."""

    twitter: SyncTwitter
    """The Twitter (X) endpoints."""

    youtube: SyncYouTube
    """The YouTube endpoints."""

    zillow: SyncZillow
    """The Zillow endpoints."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | NotGiven | None = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Headers | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Construct a blocking Tapline client.

        Args:
            api_key: Your API key. Read from the ``TAPLINE_API_KEY``
                environment variable when omitted.
            base_url: Overrides the API root, for pointing the client at a
                proxy or a local server. A path prefix is kept and every request
                is mounted under it; a query string is refused, because each
                request writes its own. Read from the ``TAPLINE_BASE_URL``
                environment variable when omitted.
            timeout: Applies to every request that does not override it.
                Defaults to 60 seconds, 10 of them for connecting; ``None``
                waits indefinitely.
            max_retries: How many times a request may be retried after a
                connection failure, a 429, or a 5xx. Pass 0 to disable retries.
            default_headers: Headers to add to every request. They override the
                library's own where the names collide.
            http_client: An ``httpx.Client`` to send through, for custom
                proxies, transports, or connection limits. Closing this client
                closes it.

        Raises:
            MissingAPIKeyError: No key was passed and ``TAPLINE_API_KEY`` is
                unset.
            ValueError: ``base_url`` is not a URL or carries a query string, or
                ``max_retries`` is negative.
        """
        super().__init__(
            api_key=api_key,
            base_url=_resolve_base_url(base_url),
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            http_client=http_client,
        )
        self.airbnb = SyncAirbnb(self)
        self.birdeye = SyncBirdeye(self)
        self.geckoterminal = SyncGeckoterminal(self)
        self.gmgn = SyncGmgn(self)
        self.goplus = SyncGoplus(self)
        self.imovelweb = SyncImovelweb(self)
        self.instagram = SyncInstagram(self)
        self.linkedin = SyncLinkedin(self)
        self.pinterest = SyncPinterest(self)
        self.ponsfamily = SyncPonsfamily(self)
        self.pumpfun = SyncPumpfun(self)
        self.tiktok = SyncTiktok(self)
        self.twitter = SyncTwitter(self)
        self.youtube = SyncYouTube(self)
        self.zillow = SyncZillow(self)
