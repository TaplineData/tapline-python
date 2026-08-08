"""Shared fixtures: a scripted stand-in for api.tapline.sh, and clients aimed at it.

Anything that would reach the network goes through :class:`MockAPI` — script the
responses the API serves, make the call, then assert on the requests it saw.

The library carries two engines, an awaitable client and a blocking twin, with
their own constructors, retry loops and close methods. Behavioural tests take
the :func:`engine` fixture and therefore run against both.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import time
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import pydantic
import pytest
from respx import MockRouter

from tapline import SyncTaplineClient, TaplineClient
from tapline import _base_client as base_client

TEST_API_KEY = "tapline-test-key"
VIDEO_ID = "dQw4w9WgXcQ"

CAPTURES = Path(__file__).parent / "fixtures" / "youtube"

ClientClass = type[TaplineClient] | type[SyncTaplineClient]


def endpoints_of(resource: type) -> set[str]:
    """The endpoint methods a resource class exposes."""
    return {name for name in vars(resource) if not name.startswith("_")}


def captured(name: str) -> Any:
    """One real API payload from ``tests/fixtures/youtube``."""
    return json.loads((CAPTURES / f"{name}.json").read_text())


def extras(value: Any, trail: str) -> list[str]:
    """Paths of every key a parsed payload carried that no model declares.

    The models accept unknown fields rather than dropping them, so this walk is
    the only thing that can tell a payload the models cover from one they do not.
    """
    if isinstance(value, pydantic.BaseModel):
        found = [f"{trail}.{key}" for key in value.model_extra or {}]
        for name, attribute in value:
            found += extras(attribute, f"{trail}.{name}")
        return found
    if isinstance(value, list):
        return [path for i, item in enumerate(value) for path in extras(item, f"{trail}[{i}]")]
    return []


class MockAPI:
    """The Tapline API, scripted.

    Serves the responses handed to :meth:`respond`, one per attempt, and records
    every request it was sent.
    """

    def __init__(self, router: MockRouter) -> None:
        self._route = router.route()

    def respond(self, *responses: httpx.Response | Exception) -> None:
        """Serve ``responses`` in order, one per attempt."""
        self._route.mock(side_effect=list(responses))

    @property
    def requests(self) -> list[httpx.Request]:
        return [call.request for call in self._route.calls]

    @property
    def attempts(self) -> int:
        return len(self._route.calls)

    @property
    def request(self) -> httpx.Request:
        """The last request the API was sent."""
        return self.requests[-1]

    @property
    def path(self) -> str:
        """Path of the last request, percent-encoding intact.

        ``httpx.URL.path`` decodes, which would turn an encoded ``%2F`` back
        into a separator and hide the very bug these tests look for.
        """
        return self.request.url.raw_path.decode().split("?")[0]

    @property
    def query(self) -> str:
        """Query string of the last request, exactly as it went out."""
        return self.request.url.query.decode()


class Engine:
    """A client of either engine, driven through one awaitable interface."""

    def __init__(self, client: TaplineClient | SyncTaplineClient) -> None:
        self.client = client

    async def call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Invoke a ``youtube`` method, awaiting it when the engine is awaitable."""
        result = getattr(self.client.youtube, method)(*args, **kwargs)
        return await result if inspect.isawaitable(result) else result

    async def aclose(self) -> None:
        result = self.client.close()
        if inspect.isawaitable(result):
            await result


@pytest.fixture
def api(respx_mock: MockRouter) -> MockAPI:
    return MockAPI(respx_mock)


@pytest.fixture(params=[TaplineClient, SyncTaplineClient], ids=["async", "sync"])
def client_class(request: pytest.FixtureRequest) -> ClientClass:
    """Each engine in turn, so every test that takes it runs twice."""
    engine_class: ClientClass = request.param
    return engine_class


@pytest.fixture
async def make_engine(client_class: ClientClass) -> AsyncIterator[Callable[..., Engine]]:
    """Builds clients of the engine under test and closes them afterwards."""
    engines: list[Engine] = []

    def make(**kwargs: Any) -> Engine:
        engine = Engine(client_class(api_key=TEST_API_KEY, **kwargs))
        engines.append(engine)
        return engine

    yield make
    for engine in engines:
        await engine.aclose()


@pytest.fixture
def engine(make_engine: Callable[..., Engine]) -> Engine:
    """A client that does not retry, so a scripted failure surfaces immediately."""
    return make_engine(max_retries=0)


class SleepRecorder:
    """Stands in for a module: records what it is asked to sleep, defers the rest."""

    def __init__(self, module: ModuleType, sleep: Callable[[float], Any]) -> None:
        self._module = module
        self.sleep = sleep

    def __getattr__(self, name: str) -> Any:
        return getattr(self._module, name)


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Records retry delays instead of waiting them out, and pins the jitter.

    Replaces the ``time`` and ``asyncio`` names inside the transport rather than
    the modules themselves, so nothing outside the client under test is touched;
    everything but ``sleep`` still reaches the real module.
    """
    recorded: list[float] = []

    def sleep(delay: float) -> None:
        recorded.append(delay)

    async def async_sleep(delay: float) -> None:
        recorded.append(delay)

    monkeypatch.setattr(base_client, "time", SleepRecorder(time, sleep))
    monkeypatch.setattr(base_client, "asyncio", SleepRecorder(asyncio, async_sleep))
    monkeypatch.setattr(base_client, "random", lambda: 0.0)
    return recorded
