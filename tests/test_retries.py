"""When the client retries, how long it waits, and when it gives up.

No test here waits for real: the ``sleeps`` fixture records the delays the
transport asked for and pins the jitter, so the schedule itself is asserted.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx
import pytest

from conftest import VIDEO_ID, Engine, MockAPI, SleepRecorder
from tapline import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
    NotFoundError,
)
from tapline import _base_client as base_client

SUCCESS = {"video_id": VIDEO_ID}

RETRYABLE_STATUSES = [408, 409, 429, 500, 502, 503]
TERMINAL_STATUSES = [400, 401, 402, 403, 404, 422]

RETRYABLE_SEND_FAILURES: list[httpx.RequestError] = [
    httpx.ConnectTimeout("connect timed out"),
    httpx.ReadTimeout("read timed out"),
    httpx.WriteTimeout("write timed out"),
    httpx.PoolTimeout("no free connection"),
    httpx.ConnectError("no route"),
    httpx.ReadError("connection reset"),
    httpx.WriteError("broken pipe"),
    httpx.CloseError("close failed"),
    httpx.RemoteProtocolError("server disconnected"),
    httpx.ProxyError("proxy refused"),
    httpx.DecodingError("corrupt gzip"),
]

TERMINAL_SEND_FAILURES: list[httpx.RequestError] = [
    httpx.UnsupportedProtocol("no such scheme"),
    httpx.LocalProtocolError("malformed"),
    httpx.TooManyRedirects("Exceeded maximum allowed redirects."),
]


def by_type(error: httpx.RequestError) -> str:
    return type(error).__name__


def ok() -> httpx.Response:
    return httpx.Response(200, json=SUCCESS)


def concrete_send_failures() -> set[type[httpx.RequestError]]:
    """Every leaf of ``httpx.RequestError``, the closed set ``send`` can raise."""

    def leaves(cls: type[httpx.RequestError]) -> set[type[httpx.RequestError]]:
        subclasses = cls.__subclasses__()
        if not subclasses:
            return {cls}
        return {leaf for subclass in subclasses for leaf in leaves(subclass)}

    return leaves(httpx.RequestError)


def http_date(seconds_from_now: float) -> str:
    return format_datetime(
        datetime.now(timezone.utc) + timedelta(seconds=seconds_from_now), usegmt=True
    )


class TestWhatIsRetried:
    @pytest.mark.parametrize("status", RETRYABLE_STATUSES)
    async def test_a_retryable_status_is_retried(
        self,
        api: MockAPI,
        make_engine: Callable[..., Engine],
        sleeps: list[float],
        status: int,
    ) -> None:
        engine = make_engine(max_retries=2)
        api.respond(httpx.Response(status), ok())

        result = await engine.call("metadata", VIDEO_ID)

        assert result.video_id == VIDEO_ID
        assert api.attempts == 2
        assert sleeps == [0.5]

    @pytest.mark.parametrize("status", TERMINAL_STATUSES)
    async def test_a_terminal_status_is_not_retried(
        self,
        api: MockAPI,
        make_engine: Callable[..., Engine],
        sleeps: list[float],
        status: int,
    ) -> None:
        engine = make_engine(max_retries=2)
        api.respond(httpx.Response(status, json={"code": "nope", "message": "no"}))

        with pytest.raises(APIStatusError, match="nope"):
            await engine.call("metadata", VIDEO_ID)

        assert api.attempts == 1
        assert sleeps == []

    async def test_retries_are_exhausted_then_the_error_is_raised(
        self, api: MockAPI, make_engine: Callable[..., Engine], sleeps: list[float]
    ) -> None:
        engine = make_engine(max_retries=2)
        api.respond(*[httpx.Response(503, json={"code": "upstream_blocked"})] * 3)

        with pytest.raises(InternalServerError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert excinfo.value.code == "upstream_blocked"
        assert api.attempts == 3
        assert sleeps == [0.5, 1.0]

    async def test_max_retries_zero_disables_retrying(
        self, api: MockAPI, make_engine: Callable[..., Engine], sleeps: list[float]
    ) -> None:
        engine = make_engine(max_retries=0)
        api.respond(httpx.Response(500))

        with pytest.raises(InternalServerError):
            await engine.call("metadata", VIDEO_ID)

        assert api.attempts == 1
        assert sleeps == []

    async def test_authentication_and_timeout_survive_a_retry(
        self, api: MockAPI, make_engine: Callable[..., Engine], sleeps: list[float]
    ) -> None:
        engine = make_engine(max_retries=2)
        api.respond(httpx.Response(429), httpx.Response(429), ok())

        await engine.call("metadata", VIDEO_ID, timeout=4.0)

        assert api.attempts == 3
        assert all("X-API-Key" in request.headers for request in api.requests)
        assert [request.extensions["timeout"]["read"] for request in api.requests] == [4.0] * 3
        assert len({str(request.url) for request in api.requests}) == 1
        assert sleeps == [0.5, 1.0]


class TestSendFailures:
    """Every way ``httpx`` can fail a send, and whether resending could help.

    The catalogue is the point: ``send`` raises nothing but an
    ``httpx.RequestError``, so covering its leaves covers the transport's whole
    failure surface. Two of them — ``TooManyRedirects`` and ``DecodingError`` —
    are not ``TransportError``s, and are provoked for real in ``test_errors.py``.
    """

    def test_the_catalogue_covers_every_failure_httpx_can_raise(self) -> None:
        """A failure httpx adds and this file does not classify fails here first."""
        catalogued = {type(error) for error in RETRYABLE_SEND_FAILURES + TERMINAL_SEND_FAILURES}

        assert concrete_send_failures() == catalogued

    @pytest.mark.parametrize("error", RETRYABLE_SEND_FAILURES, ids=by_type)
    async def test_a_send_failure_that_may_pass_next_time_is_retried(
        self,
        api: MockAPI,
        make_engine: Callable[..., Engine],
        sleeps: list[float],
        error: httpx.RequestError,
    ) -> None:
        engine = make_engine(max_retries=1)
        api.respond(error, ok())

        result = await engine.call("metadata", VIDEO_ID)

        assert result.video_id == VIDEO_ID
        assert api.attempts == 2
        assert sleeps == [0.5]

    @pytest.mark.parametrize("error", TERMINAL_SEND_FAILURES, ids=by_type)
    async def test_a_send_failure_that_cannot_change_is_not_retried(
        self,
        api: MockAPI,
        make_engine: Callable[..., Engine],
        sleeps: list[float],
        error: httpx.RequestError,
    ) -> None:
        """The resend would be the same request to the same server.

        The script holds a failure for every attempt the budget would allow, so
        a regression that retried is counted here rather than running it dry.
        """
        engine = make_engine(max_retries=2)
        api.respond(error, error, error)

        with pytest.raises(APIConnectionError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert excinfo.value.__cause__ is error
        assert api.attempts == 1
        assert sleeps == []

    async def test_a_connection_error_survives_its_retries(
        self, api: MockAPI, make_engine: Callable[..., Engine], sleeps: list[float]
    ) -> None:
        engine = make_engine(max_retries=1)
        api.respond(httpx.ConnectError("no route"), httpx.ConnectError("no route"))

        with pytest.raises(APIConnectionError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert "no route" in str(excinfo.value)
        assert excinfo.value.request.url.path.endswith("/metadata")
        assert api.attempts == 2
        assert sleeps == [0.5]

    async def test_a_timeout_is_retried_and_reported_as_a_timeout(
        self, api: MockAPI, make_engine: Callable[..., Engine], sleeps: list[float]
    ) -> None:
        engine = make_engine(max_retries=1)
        api.respond(httpx.ReadTimeout("too slow"), httpx.ReadTimeout("too slow"))

        with pytest.raises(APITimeoutError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert isinstance(excinfo.value, APIConnectionError)
        assert api.attempts == 2
        assert sleeps == [0.5]


class TestBackoff:
    async def test_the_delay_doubles_and_is_capped(
        self, api: MockAPI, make_engine: Callable[..., Engine], sleeps: list[float]
    ) -> None:
        engine = make_engine(max_retries=6)
        api.respond(*[httpx.Response(500)] * 7)

        with pytest.raises(InternalServerError):
            await engine.call("metadata", VIDEO_ID)

        assert sleeps == [0.5, 1.0, 2.0, 4.0, 8.0, 8.0]

    async def test_jitter_only_ever_shortens_the_delay(
        self,
        api: MockAPI,
        make_engine: Callable[..., Engine],
        sleeps: list[float],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(base_client, "random", lambda: 1.0)
        engine = make_engine(max_retries=1)
        api.respond(httpx.Response(500), ok())

        await engine.call("metadata", VIDEO_ID)

        assert sleeps == [0.375]


class TestRetryAfter:
    async def test_a_numeric_retry_after_is_honored(
        self, api: MockAPI, make_engine: Callable[..., Engine], sleeps: list[float]
    ) -> None:
        engine = make_engine(max_retries=1)
        api.respond(httpx.Response(429, headers={"Retry-After": "1.5"}), ok())

        await engine.call("metadata", VIDEO_ID)

        assert sleeps == [1.5]

    async def test_an_http_date_retry_after_is_honored(
        self, api: MockAPI, make_engine: Callable[..., Engine], sleeps: list[float]
    ) -> None:
        engine = make_engine(max_retries=1)
        api.respond(httpx.Response(503, headers={"Retry-After": http_date(30)}), ok())

        await engine.call("metadata", VIDEO_ID)

        assert len(sleeps) == 1
        assert 25.0 < sleeps[0] <= 30.0

    @pytest.mark.parametrize(
        "retry_after",
        ["3600", "0", "-5", "tomorrow", http_date(-30)],
        ids=["too-far-off", "zero", "negative", "unparseable", "in-the-past"],
    )
    async def test_an_unusable_retry_after_falls_back_to_backoff(
        self,
        api: MockAPI,
        make_engine: Callable[..., Engine],
        sleeps: list[float],
        retry_after: str,
    ) -> None:
        engine = make_engine(max_retries=1)
        api.respond(httpx.Response(429, headers={"Retry-After": retry_after}), ok())

        await engine.call("metadata", VIDEO_ID)

        assert sleeps == [0.5]

    async def test_retry_after_applies_to_that_attempt_alone(
        self, api: MockAPI, make_engine: Callable[..., Engine], sleeps: list[float]
    ) -> None:
        engine = make_engine(max_retries=2)
        api.respond(
            httpx.Response(429, headers={"Retry-After": "2"}),
            httpx.Response(429),
            ok(),
        )

        await engine.call("metadata", VIDEO_ID)

        assert sleeps == [2.0, 1.0]


async def test_a_client_closed_during_the_backoff_stops_the_retry(
    api: MockAPI, make_engine: Callable[..., Engine], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A retry waits seconds, and another task may close the client inside them.

    The closure check therefore guards every attempt, not just the first: sending
    into a closed pool is httpx's bare ``RuntimeError``, not a ``RequestError``.
    """
    engine = make_engine(max_retries=2)
    api.respond(httpx.Response(500), ok(), ok())
    waited: list[float] = []

    def close(delay: float) -> None:
        waited.append(delay)
        engine.client.close()

    async def aclose(delay: float) -> None:
        waited.append(delay)
        await engine.aclose()

    monkeypatch.setattr(base_client, "random", lambda: 0.0)
    monkeypatch.setattr(base_client, "time", SleepRecorder(time, close))
    monkeypatch.setattr(base_client, "asyncio", SleepRecorder(asyncio, aclose))

    with pytest.raises(APIConnectionError, match="the client is closed"):
        await engine.call("metadata", VIDEO_ID)

    assert api.attempts == 1
    assert waited == [0.5]


async def test_a_retry_budget_does_not_leak_across_calls(
    api: MockAPI, make_engine: Callable[..., Engine], sleeps: list[float]
) -> None:
    engine = make_engine(max_retries=1)
    api.respond(
        httpx.Response(500),
        ok(),
        httpx.Response(404, json={"code": "not_found", "message": "gone"}),
    )

    await engine.call("metadata", VIDEO_ID)
    with pytest.raises(NotFoundError):
        await engine.call("metadata", VIDEO_ID)

    assert api.attempts == 3
    assert sleeps == [0.5]
