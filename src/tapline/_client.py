"""The Tapline clients.

:class:`TaplineClient` is awaitable and :class:`SyncTaplineClient` blocks.
Async is the unprefixed name because that is how the API is expected to be
called: eleven endpoints that each proxy YouTube live, so a caller almost
always wants several in flight at once.
"""

from __future__ import annotations

import os

import httpx

from ._base_client import AsyncAPIClient, SyncAPIClient
from ._constants import DEFAULT_MAX_RETRIES
from ._types import Headers, NotGiven, Timeout, not_given
from .resources import SyncYouTube, YouTube

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

    youtube: YouTube
    """The YouTube endpoints."""

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
        self.youtube = YouTube(self)


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

    youtube: SyncYouTube
    """The YouTube endpoints."""

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
        self.youtube = SyncYouTube(self)
