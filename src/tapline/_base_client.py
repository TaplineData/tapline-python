"""HTTP transport for the Tapline API — the sync and async engines over httpx.

Resource classes reach the network through exactly one method, ``get``::

    from tapline._base_client import encode_path

    await self._client.get(
        encode_path("/api/v1/youtube/videos/{video_id}/comments", video_id=video_id),
        cast_to=CommentsResponse,
        params={"sort": sort, "limit": limit, "cursor": cursor},
    )

Build paths with :func:`encode_path`: ``video_id`` and ``channel_id`` accept
full YouTube URLs, so an f-string would leak ``/`` and ``?`` into the path.
In ``params``, ``None`` values are dropped, bools become ``true``/``false``,
enums become their value, and lists repeat the key (``features=hd&features=4k``)
because that is what FastAPI parses back into a list.

Neither engine decides anything for itself: :class:`BaseClient` resolves the
configuration, builds the request and validates the response, and
``_RetryBudget`` decides whether and when to send it again. All a twin adds is
how it awaits — the send, the sleep, and the close.

A caller never sees an exception this library did not raise. Once a request
exists, ``send`` fails only with an ``httpx.RequestError`` — the family that
covers a redirect loop and an undecodable body as well as the transport
failures — and every one of them becomes an :class:`APIConnectionError`, resent
only when a resend could land differently. ``httpx.StreamError`` is not in that
family and cannot arise here: it reports misuse of the streaming API, and this
client never streams. The one thing ``send`` raises that is no ``RequestError``
— indeed no ``httpx`` exception at all — is a bare ``RuntimeError`` for a client
that has been closed, so every attempt checks ``is_closed`` before it sends and
raises the closure itself. ``httpx.InvalidURL`` comes before a request exists,
from parsing ``base_url``, and the constructor turns it into the ``ValueError``
a bad argument deserves — as it does a ``base_url`` carrying a query string,
which no request could keep.
"""

from __future__ import annotations

import abc
import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from enum import Enum
from random import random
from types import TracebackType
from typing import ClassVar, Generic, TypeVar
from urllib.parse import quote

import httpx
import pydantic
from typing_extensions import Self, override

from ._constants import (
    API_KEY_ENV_VAR,
    API_KEY_HEADER,
    DEFAULT_BASE_URL,
    DEFAULT_CONNECTION_LIMITS,
    DEFAULT_TIMEOUT,
    HTTPX_DEFAULT_TIMEOUT,
    INITIAL_RETRY_DELAY,
    MAX_HONORED_RETRY_AFTER,
    MAX_RETRY_DELAY,
    USER_AGENT,
)
from ._exceptions import (
    APIConnectionError,
    APIResponseValidationError,
    MissingAPIKeyError,
    make_request_error,
    make_status_error,
)
from ._types import Headers, NotGiven, PrimitiveQueryValue, Query, Timeout, not_given

__all__ = ["AsyncAPIClient", "BaseClient", "SyncAPIClient", "encode_path"]

log: logging.Logger = logging.getLogger(__name__)

_ModelT = TypeVar("_ModelT", bound=pydantic.BaseModel)
_HttpxClientT = TypeVar("_HttpxClientT", bound=httpx.Client | httpx.AsyncClient)

# 408 and 409 are transient server-side conditions; 429 and 5xx are explicitly
# retryable. Every other 4xx describes the request, and will fail identically.
_RETRYABLE_STATUS_CODES = frozenset({408, 409, 429})

# A scheme httpx cannot speak, a request it refuses to put on the wire, or a
# redirect chain that never ended: the resend is the same request to the same
# server, so it fails the same way.
_UNRETRYABLE_REQUEST_ERRORS = (
    httpx.UnsupportedProtocol,
    httpx.LocalProtocolError,
    httpx.TooManyRedirects,
)

# Every character that may stand unescaped in an already-encoded path, `%`
# included so that what `encode_path` wrote survives. `?` and `#` are absent on
# purpose: httpx splits a raw path on them, which would turn the tail of a
# hand-built path into a query string or a fragment.
_SAFE_IN_ENCODED_PATH = "%/!$&'()*+,;=:@"


def encode_path(template: str, /, **segments: str) -> str:
    """Percent-encode ``segments`` into a request path.

    ``encode_path("/videos/{video_id}/formats", video_id="https://youtu.be/x")``
    yields ``/videos/https%3A%2F%2Fyoutu.be%2Fx/formats``, keeping the value
    inside one path segment. Nothing else in ``template`` is touched.

    Raises:
        ValueError: A segment is ``.`` or ``..``. Both are removed when the URL
            is resolved, which would send the request to a different endpoint
            than ``template`` names.
    """
    encoded: dict[str, str] = {}
    for name, value in segments.items():
        segment = quote(value, safe="")
        if segment in (".", ".."):
            raise ValueError(
                f"{name}={value!r} is a dot-segment: URL resolution strips it, so "
                f"the request would not reach {template!r}."
            )
        encoded[name] = segment
    return template.format(**encoded)


def encode_query(params: Query | None) -> tuple[tuple[str, str], ...]:
    """Flatten query parameters into repeated ``(key, value)`` pairs."""
    if params is None:
        return ()
    encoded: list[tuple[str, str]] = []
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, Enum)):
            encoded.append((key, _encode_query_value(value)))
        else:
            encoded.extend((key, _encode_query_value(item)) for item in value)
    return tuple(encoded)


def _encode_query_value(value: PrimitiveQueryValue) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Enum):
        return _encode_query_value(value.value)
    return str(value)


def _should_retry(status_code: int) -> bool:
    return status_code in _RETRYABLE_STATUS_CODES or status_code >= 500


def _retry_delay(attempt: int, headers: httpx.Headers | None) -> float:
    """Seconds to wait before the retry that follows zero-indexed ``attempt``."""
    retry_after = _parse_retry_after(headers) if headers is not None else None
    if retry_after is not None and 0 < retry_after <= MAX_HONORED_RETRY_AFTER:
        return retry_after
    backoff = min(INITIAL_RETRY_DELAY * 2.0**attempt, MAX_RETRY_DELAY)
    # Jitter downwards only, so the cap stays a cap under a thundering herd.
    return backoff * (1 - 0.25 * random())


def _parse_retry_after(headers: httpx.Headers) -> float | None:
    value = headers.get("retry-after")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        pass
    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    return (retry_at - datetime.now(timezone.utc)).total_seconds()


class _RetryBudget:
    """The retries one request has left, and how long each one waits.

    Holds every decision an engine's loop would otherwise make for itself, so
    the two engines carry no retry policy of their own and this one is testable
    without a client.
    """

    def __init__(self, max_retries: int) -> None:
        self._max_retries = max_retries
        self._retries_taken = 0

    @property
    def attempt(self) -> int:
        """The one-based number of the send this budget is about to allow."""
        return self._retries_taken + 1

    def delay_after(self, response: httpx.Response) -> float | None:
        """Seconds to wait before resending, or ``None`` to accept ``response``."""
        if not _should_retry(response.status_code):
            return None
        return self._take(response.headers)

    def delay_after_request_error(self, error: httpx.RequestError) -> float | None:
        """Seconds to wait before resending, or ``None`` to surface the failure."""
        if isinstance(error, _UNRETRYABLE_REQUEST_ERRORS):
            return None
        return self._take(None)

    def _take(self, headers: httpx.Headers | None) -> float | None:
        if self._retries_taken >= self._max_retries:
            return None
        delay = _retry_delay(self._retries_taken, headers)
        self._retries_taken += 1
        return delay


def _resolve_timeout(
    timeout: float | Timeout | NotGiven | None,
    http_client: httpx.Client | httpx.AsyncClient | None,
) -> float | Timeout | None:
    """The timeout every request gets unless it overrides it.

    An explicit ``timeout`` always wins. Failing that, a supplied
    ``http_client`` states the caller's intent — unless it carries httpx's own
    5-second default, which nobody chose and which is shorter than a cold call
    to this API takes, so ``DEFAULT_TIMEOUT`` stands. A caller who does want
    five seconds says so with ``timeout=5.0``.
    """
    if not isinstance(timeout, NotGiven):
        return timeout
    if http_client is None or http_client.timeout == HTTPX_DEFAULT_TIMEOUT:
        return DEFAULT_TIMEOUT
    return http_client.timeout


def _parse_base_url(base_url: str | httpx.URL | None) -> httpx.URL:
    """The root every request path is resolved against, trailing slash included.

    A path prefix is kept, so a gateway may be mounted under one. A query string
    is refused rather than merged: every request writes its own query from the
    parameters its endpoint declares, and there is no second author to reconcile
    it with. A gateway credential belongs in ``default_headers`` or in a
    caller's own ``http_client``, both of which reach every request untouched.

    Raises:
        ValueError: ``base_url`` is not a URL, or carries a query string.
            Request paths are percent-encoded before they are joined on, so this
            is the only URL ``httpx`` gets a chance to reject and the only
            ``httpx.InvalidURL`` to translate.
    """
    try:
        url = httpx.URL(base_url or DEFAULT_BASE_URL)
    except httpx.InvalidURL as err:
        raise ValueError(f"base_url={base_url!r} is not a valid URL: {err}") from err
    if url.query:
        raise ValueError(
            f"base_url={base_url!r} carries a query string. Every request replaces "
            "the query with the parameters its endpoint takes, so nothing of this "
            "one would reach the server. Send a gateway credential in "
            "default_headers, or through an http_client of your own."
        )
    # `raw_path` is the path alone only because the query was refused above: httpx
    # folds `?...` into it, which would swallow the endpoint path joined on next.
    if url.raw_path.endswith(b"/"):
        return url
    return url.copy_with(raw_path=url.raw_path + b"/")


class BaseClient(abc.ABC, Generic[_HttpxClientT]):
    """Configuration, request building, and response validation, shared by both engines."""

    _client: _HttpxClientT
    _httpx_client_class: ClassVar[type[httpx.Client] | type[httpx.AsyncClient]]

    api_key: str
    max_retries: int
    timeout: float | Timeout | None

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str | httpx.URL | None,
        timeout: float | Timeout | NotGiven | None,
        max_retries: int,
        default_headers: Headers | None,
        http_client: _HttpxClientT | None,
    ) -> None:
        resolved_key = api_key if api_key is not None else os.environ.get(API_KEY_ENV_VAR)
        if not resolved_key:
            raise MissingAPIKeyError(
                "No API key supplied. Pass api_key=... when constructing the client, "
                f"or set the {API_KEY_ENV_VAR} environment variable."
            )
        if max_retries < 0:
            raise ValueError(
                f"max_retries must be >= 0, got {max_retries}. Pass 0 to disable retries."
            )
        expected = self._httpx_client_class
        if http_client is not None and not isinstance(http_client, expected):
            raise TypeError(
                f"{type(self).__name__} sends through an httpx.{expected.__name__}, "
                f"but http_client is an httpx.{type(http_client).__name__}. Pass an "
                f"httpx.{expected.__name__}, or use the other client."
            )

        self.api_key = resolved_key
        self.max_retries = max_retries
        self.timeout = _resolve_timeout(timeout, http_client)
        self._base_url = _parse_base_url(base_url)
        self._default_headers = dict(default_headers or {})
        self._client = http_client if http_client is not None else self._new_http_client()

    @abc.abstractmethod
    def _new_http_client(self) -> _HttpxClientT:
        """The httpx client this engine sends through when the caller supplied none."""

    @property
    def base_url(self) -> httpx.URL:
        """The root every request path is resolved against."""
        return self._base_url

    @property
    def is_closed(self) -> bool:
        """Whether the connection pool has been released.

        A closed client cannot be reopened: sending through one raises
        :class:`APIConnectionError`.
        """
        return self._client.is_closed

    def _raise_if_closed(self, request: httpx.Request) -> None:
        """Refuse a send that httpx would answer with a bare ``RuntimeError``."""
        if self._client.is_closed:
            raise APIConnectionError(
                request,
                message=(
                    "Request not sent — the client is closed. A client cannot be used "
                    "after close(), or after the block that closed it"
                ),
            )

    def _headers(self) -> httpx.Headers:
        headers = httpx.Headers(
            {
                API_KEY_HEADER: self.api_key,
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            }
        )
        # httpx.Headers matches names case-insensitively, as HTTP does, so a
        # caller's `user-agent` replaces ours instead of shipping alongside it.
        headers.update(self._default_headers)
        return headers

    def _url_for(self, path: str) -> httpx.URL:
        # raw_path keeps the percent-encoding `encode_path` applied; httpx's
        # `path` accessor would decode it and turn %2F back into a separator. It
        # is query-free because `_parse_base_url` refuses a base_url that has one.
        escaped = quote(path.lstrip("/"), safe=_SAFE_IN_ENCODED_PATH)
        return self._base_url.copy_with(raw_path=self._base_url.raw_path + escaped.encode("ascii"))

    def _build_request(
        self,
        path: str,
        *,
        params: Query | None,
        timeout: float | Timeout | NotGiven | None,
    ) -> httpx.Request:
        return self._client.build_request(
            "GET",
            self._url_for(path),
            params=encode_query(params),
            headers=self._headers(),
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
        )

    def _process_response(self, response: httpx.Response, *, cast_to: type[_ModelT]) -> _ModelT:
        if not response.is_success:
            raise make_status_error(response)
        try:
            payload = response.json()
        except ValueError as err:
            raise APIResponseValidationError(
                response, "The API returned a body that is not valid JSON."
            ) from err
        try:
            return cast_to.model_validate(payload)
        except pydantic.ValidationError as err:
            raise APIResponseValidationError(
                response, f"The API response did not match {cast_to.__name__}:\n{err}"
            ) from err


class SyncAPIClient(BaseClient[httpx.Client]):
    """Blocking transport engine."""

    _httpx_client_class: ClassVar[type[httpx.Client] | type[httpx.AsyncClient]] = httpx.Client

    @override
    def _new_http_client(self) -> httpx.Client:
        return httpx.Client(limits=DEFAULT_CONNECTION_LIMITS)

    def get(
        self,
        path: str,
        *,
        cast_to: type[_ModelT],
        params: Query | None = None,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> _ModelT:
        """Send a ``GET`` request and validate the response body into ``cast_to``.

        Args:
            path: Request path, already percent-encoded by :func:`encode_path`.
                Query parameters go in ``params``, not here.
            cast_to: Model the JSON body is validated into.
            params: Query parameters; see the module docstring for serialization.
            timeout: Overrides the client timeout for this request. ``None``
                waits indefinitely.

        Raises:
            APIStatusError: The API answered with a non-2xx status. Catch a
                subclass (``NotFoundError``, ``RateLimitError``, …) to narrow.
            APIConnectionError: No response the client could read came back —
                a network failure, a timeout, a redirect loop, or a client that
                has been closed.
            APIResponseValidationError: The body did not match ``cast_to``.
        """
        request = self._build_request(path, params=params, timeout=timeout)
        budget = _RetryBudget(self.max_retries)
        while True:
            self._raise_if_closed(request)
            log.debug("Sending %s %s (attempt %d)", request.method, request.url, budget.attempt)
            try:
                response = self._client.send(request)
            except httpx.RequestError as err:
                delay = budget.delay_after_request_error(err)
                if delay is None:
                    raise make_request_error(err, request) from err
            else:
                delay = budget.delay_after(response)
                if delay is None:
                    return self._process_response(response, cast_to=cast_to)
            log.info("Retrying %s in %.2fs", request.url, delay)
            time.sleep(delay)

    def close(self) -> None:
        """Release the underlying httpx client and its connection pool."""
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


class AsyncAPIClient(BaseClient[httpx.AsyncClient]):
    """Awaitable transport engine."""

    _httpx_client_class: ClassVar[type[httpx.Client] | type[httpx.AsyncClient]] = httpx.AsyncClient

    @override
    def _new_http_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(limits=DEFAULT_CONNECTION_LIMITS)

    async def get(
        self,
        path: str,
        *,
        cast_to: type[_ModelT],
        params: Query | None = None,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> _ModelT:
        """Send a ``GET`` request and validate the response body into ``cast_to``.

        Args:
            path: Request path, already percent-encoded by :func:`encode_path`.
                Query parameters go in ``params``, not here.
            cast_to: Model the JSON body is validated into.
            params: Query parameters; see the module docstring for serialization.
            timeout: Overrides the client timeout for this request. ``None``
                waits indefinitely.

        Raises:
            APIStatusError: The API answered with a non-2xx status. Catch a
                subclass (``NotFoundError``, ``RateLimitError``, …) to narrow.
            APIConnectionError: No response the client could read came back —
                a network failure, a timeout, a redirect loop, or a client that
                has been closed.
            APIResponseValidationError: The body did not match ``cast_to``.
        """
        request = self._build_request(path, params=params, timeout=timeout)
        budget = _RetryBudget(self.max_retries)
        while True:
            self._raise_if_closed(request)
            log.debug("Sending %s %s (attempt %d)", request.method, request.url, budget.attempt)
            try:
                response = await self._client.send(request)
            except httpx.RequestError as err:
                delay = budget.delay_after_request_error(err)
                if delay is None:
                    raise make_request_error(err, request) from err
            else:
                delay = budget.delay_after(response)
                if delay is None:
                    return self._process_response(response, cast_to=cast_to)
            log.info("Retrying %s in %.2fs", request.url, delay)
            await asyncio.sleep(delay)

    async def close(self) -> None:
        """Release the underlying httpx client and its connection pool."""
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()
