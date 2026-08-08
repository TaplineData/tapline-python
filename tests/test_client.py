"""Construction, configuration, and what the two engines put on the wire."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import httpx
import pytest

import tapline
from conftest import TEST_API_KEY, VIDEO_ID, ClientClass, Engine, MockAPI, captured, endpoints_of
from tapline import MissingAPIKeyError, SyncTaplineClient, TaplineClient
from tapline._constants import DEFAULT_TIMEOUT
from tapline.resources.youtube import SyncYouTube, YouTube

ENV_VAR = "TAPLINE_API_KEY"
README = Path(__file__).parents[1] / "README.md"

METADATA_BODY = {"video_id": VIDEO_ID}
METADATA_PATH = f"/api/v1/youtube/videos/{VIDEO_ID}/metadata"

HttpClientClass = type[httpx.Client] | type[httpx.AsyncClient]

ENDPOINTS = (
    "search",
    "channel",
    "channel_videos",
    "playlist",
    "metadata",
    "subtitles",
    "subtitle_tracks",
    "comments",
    "comment_replies",
    "formats",
    "heatmap",
)


def ok(body: object = METADATA_BODY) -> httpx.Response:
    return httpx.Response(200, json=body)


def documented_snippet(heading: str) -> str:
    """The first fenced Python block under a README heading."""
    section = README.read_text().split(f"\n## {heading}\n", 1)[1]
    return section.split("```python\n", 1)[1].split("```", 1)[0]


@pytest.fixture
def http_client_class(client_class: ClientClass) -> HttpClientClass:
    """The httpx client the engine under test accepts."""
    return httpx.AsyncClient if client_class is TaplineClient else httpx.Client


class TestAPIKey:
    def test_missing_api_key_raises_naming_the_env_var(
        self, client_class: ClientClass, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv(ENV_VAR, raising=False)

        with pytest.raises(MissingAPIKeyError) as excinfo:
            client_class()

        assert ENV_VAR in str(excinfo.value)
        assert "api_key" in str(excinfo.value)
        assert isinstance(excinfo.value, tapline.TaplineError)

    def test_api_key_read_from_the_environment(
        self, client_class: ClientClass, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(ENV_VAR, "key-from-env")

        assert client_class().api_key == "key-from-env"

    def test_explicit_api_key_beats_the_environment(
        self, client_class: ClientClass, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(ENV_VAR, "key-from-env")

        assert client_class(api_key="key-from-argument").api_key == "key-from-argument"

    def test_empty_env_var_is_not_a_key(
        self, client_class: ClientClass, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(ENV_VAR, "")

        with pytest.raises(MissingAPIKeyError):
            client_class()

    async def test_api_key_is_sent_as_a_header(self, api: MockAPI, engine: Engine) -> None:
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID)

        assert api.request.headers["X-API-Key"] == TEST_API_KEY
        assert "authorization" not in api.request.headers


class TestHeaders:
    async def test_default_headers(self, api: MockAPI, engine: Engine) -> None:
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID)

        headers = api.request.headers
        assert headers["Accept"] == "application/json"
        assert headers["User-Agent"].startswith(f"tapline-python/{tapline.__version__} ")

    async def test_custom_headers_are_merged_not_clobbered(
        self, api: MockAPI, make_engine: Callable[..., Engine]
    ) -> None:
        engine = make_engine(default_headers={"X-Trace-Id": "trace-1"}, max_retries=0)
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID)

        assert api.request.headers["X-Trace-Id"] == "trace-1"
        assert api.request.headers["X-API-Key"] == TEST_API_KEY
        assert api.request.headers["Accept"] == "application/json"

    async def test_a_custom_header_wins_on_a_name_collision(
        self, api: MockAPI, make_engine: Callable[..., Engine]
    ) -> None:
        engine = make_engine(default_headers={"User-Agent": "my-app/2.0"}, max_retries=0)
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID)

        assert api.request.headers["User-Agent"] == "my-app/2.0"


class TestBaseURL:
    async def test_default_base_url(self, api: MockAPI, engine: Engine) -> None:
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID)

        assert str(api.request.url) == f"https://api.tapline.sh{METADATA_PATH}"

    @pytest.mark.parametrize(
        "base_url",
        ["http://localhost:8000", "http://localhost:8000/"],
    )
    async def test_base_url_override_normalizes_the_trailing_slash(
        self, api: MockAPI, make_engine: Callable[..., Engine], base_url: str
    ) -> None:
        engine = make_engine(base_url=base_url, max_retries=0)
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID)

        assert engine.client.base_url.raw_path == b"/"
        assert str(api.request.url) == f"http://localhost:8000{METADATA_PATH}"

    @pytest.mark.parametrize(
        "base_url",
        ["https://proxy.example.com/tapline", "https://proxy.example.com/tapline/"],
    )
    async def test_base_url_may_carry_a_path_prefix(
        self, api: MockAPI, make_engine: Callable[..., Engine], base_url: str
    ) -> None:
        engine = make_engine(base_url=base_url, max_retries=0)
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID)

        assert engine.client.base_url.raw_path == b"/tapline/"
        assert str(api.request.url) == f"https://proxy.example.com/tapline{METADATA_PATH}"

    async def test_a_path_prefix_survives_a_request_that_carries_parameters(
        self, api: MockAPI, make_engine: Callable[..., Engine]
    ) -> None:
        """The prefix belongs to the path, the parameters to the query; neither eats the other."""
        engine = make_engine(base_url="https://proxy.example.com/tapline", max_retries=0)
        api.respond(ok(captured("search")))

        await engine.call("search", query="game of thrones", limit=5)

        assert api.path == "/tapline/api/v1/youtube/search"
        assert api.query == "query=game+of+thrones&limit=5&sort=relevance"

    @pytest.mark.parametrize(
        "base_url",
        [
            "https://proxy.example.com/gw?token=abc",
            "https://proxy.example.com/?token=abc",
            "https://proxy.example.com?token=abc",
        ],
    )
    def test_a_base_url_carrying_a_query_string_is_rejected(
        self, client_class: ClientClass, base_url: str
    ) -> None:
        """httpx folds a query into ``raw_path``, so joining a path onto one swallows it whole.

        Refused at construction rather than merged: the query of every request is
        written from the parameters its endpoint declares, and a caller's gateway
        credential travels in ``default_headers`` or in their own ``http_client``.
        """
        with pytest.raises(ValueError, match="carries a query string") as excinfo:
            client_class(api_key=TEST_API_KEY, base_url=base_url)

        assert "default_headers" in str(excinfo.value)

    def test_a_base_url_query_string_is_rejected_from_the_environment_too(
        self, client_class: ClientClass, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TAPLINE_BASE_URL", "https://proxy.example.com/gw?token=abc")

        with pytest.raises(ValueError, match="carries a query string"):
            client_class(api_key=TEST_API_KEY)


class TestTimeout:
    def test_default_timeout(self, client_class: ClientClass) -> None:
        assert client_class(api_key=TEST_API_KEY).timeout == DEFAULT_TIMEOUT

    async def test_default_timeout_reaches_the_request(self, api: MockAPI, engine: Engine) -> None:
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID)

        assert api.request.extensions["timeout"] == {
            "connect": 10.0,
            "read": 60.0,
            "write": 60.0,
            "pool": 60.0,
        }

    async def test_a_client_timeout_of_none_waits_indefinitely(
        self, api: MockAPI, make_engine: Callable[..., Engine]
    ) -> None:
        engine = make_engine(timeout=None)
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID)

        assert engine.client.timeout is None
        assert api.request.extensions["timeout"] == {
            "connect": None,
            "read": None,
            "write": None,
            "pool": None,
        }

    async def test_per_request_timeout_overrides_the_client(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID, timeout=1.5)

        assert api.request.extensions["timeout"] == {
            "connect": 1.5,
            "read": 1.5,
            "write": 1.5,
            "pool": 1.5,
        }

    async def test_per_request_timeout_of_none_waits_indefinitely(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID, timeout=None)

        assert api.request.extensions["timeout"] == {
            "connect": None,
            "read": None,
            "write": None,
            "pool": None,
        }

    async def test_a_supplied_http_client_keeps_its_own_timeout(
        self, make_engine: Callable[..., Engine], http_client_class: HttpClientClass
    ) -> None:
        engine = make_engine(http_client=http_client_class(timeout=httpx.Timeout(3.0)))

        assert engine.client.timeout == httpx.Timeout(3.0)

    async def test_a_supplied_http_client_carrying_httpxs_own_default_does_not_shorten_it(
        self, api: MockAPI, make_engine: Callable[..., Engine], http_client_class: HttpClientClass
    ) -> None:
        """A bare client carries httpx's 5s, which nobody chose and a cold call outlives."""
        engine = make_engine(http_client=http_client_class())
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID)

        assert engine.client.timeout == DEFAULT_TIMEOUT
        assert api.request.extensions["timeout"] == {
            "connect": 10.0,
            "read": 60.0,
            "write": 60.0,
            "pool": 60.0,
        }

    async def test_an_explicit_timeout_beats_a_supplied_http_client(
        self, make_engine: Callable[..., Engine], http_client_class: HttpClientClass
    ) -> None:
        engine = make_engine(timeout=9.0, http_client=http_client_class(timeout=httpx.Timeout(3.0)))

        assert engine.client.timeout == 9.0


class TestHTTPClientFlavour:
    """A caller's ``http_client`` must match the engine it is handed to.

    The annotations already reject the mismatch statically, so these two ignores
    are what lets the test reach the runtime guard that catches unchecked callers.
    """

    def test_the_sync_client_rejects_an_async_http_client(self) -> None:
        with pytest.raises(TypeError, match=r"http_client is an httpx\.AsyncClient"):
            SyncTaplineClient(
                api_key=TEST_API_KEY,
                http_client=httpx.AsyncClient(),  # type: ignore[arg-type]
            )

    def test_the_async_client_rejects_a_sync_http_client(self) -> None:
        with pytest.raises(TypeError, match=r"http_client is an httpx\.Client"):
            TaplineClient(
                api_key=TEST_API_KEY,
                http_client=httpx.Client(),  # type: ignore[arg-type]
            )


class TestLifecycle:
    def test_default_max_retries(self, client_class: ClientClass) -> None:
        assert client_class(api_key=TEST_API_KEY).max_retries == 2

    def test_negative_max_retries_is_rejected(self, client_class: ClientClass) -> None:
        with pytest.raises(ValueError, match="max_retries"):
            client_class(api_key=TEST_API_KEY, max_retries=-1)

    async def test_async_context_manager_closes_the_connection_pool(self) -> None:
        async with TaplineClient(api_key=TEST_API_KEY) as client:
            assert client.is_closed is False

        assert client.is_closed is True

    def test_sync_context_manager_closes_the_connection_pool(self) -> None:
        with SyncTaplineClient(api_key=TEST_API_KEY) as client:
            assert client.is_closed is False

        assert client.is_closed is True

    async def test_close_releases_the_connection_pool(self, engine: Engine) -> None:
        await engine.aclose()

        assert engine.client.is_closed is True

    async def test_a_supplied_http_client_is_the_one_used(
        self, api: MockAPI, make_engine: Callable[..., Engine], http_client_class: HttpClientClass
    ) -> None:
        http_client = http_client_class()
        engine = make_engine(http_client=http_client)
        api.respond(ok())

        await engine.call("metadata", VIDEO_ID)

        assert engine.client._client is http_client
        assert api.attempts == 1


class TestNamespace:
    async def test_the_async_client_carries_the_async_resource(self) -> None:
        async with TaplineClient(api_key=TEST_API_KEY) as client:
            assert isinstance(client.youtube, YouTube)

    def test_the_sync_client_carries_the_sync_resource(self) -> None:
        with SyncTaplineClient(api_key=TEST_API_KEY) as client:
            assert isinstance(client.youtube, SyncYouTube)

    def test_the_resources_expose_the_same_eleven_endpoints(self) -> None:
        assert endpoints_of(YouTube) == set(ENDPOINTS)
        assert endpoints_of(SyncYouTube) == set(ENDPOINTS)

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_the_twins_share_a_signature_and_a_docstring(self, endpoint: str) -> None:
        awaitable = getattr(YouTube, endpoint)
        blocking = getattr(SyncYouTube, endpoint)

        assert inspect.signature(awaitable) == inspect.signature(blocking)
        assert awaitable.__doc__ == blocking.__doc__
        assert inspect.iscoroutinefunction(awaitable)
        assert not inspect.iscoroutinefunction(blocking)

    def test_the_twins_share_the_inherited_pages_walk(self) -> None:
        """``pages`` is the one public method the endpoint parity above cannot reach.

        Its two loops are written out separately, so only the parameters and the
        one docstring they share are the same object of comparison.
        """

        def shape(walk: Callable[..., object]) -> list[tuple[str, object, object]]:
            return [
                (name, parameter.kind, parameter.default)
                for name, parameter in inspect.signature(walk).parameters.items()
            ]

        assert shape(YouTube.pages) == shape(SyncYouTube.pages)
        assert SyncYouTube.pages.__doc__ is not None
        assert YouTube.pages.__doc__ == SyncYouTube.pages.__doc__


class TestPublicSurface:
    def test_every_exported_name_resolves(self) -> None:
        missing = [name for name in tapline.__all__ if not hasattr(tapline, name)]

        assert missing == []

    @pytest.mark.parametrize(
        "module", [tapline._exceptions, tapline._pagination], ids=["errors", "pagination"]
    )
    def test_the_root_re_exports_every_public_name(self, module: ModuleType) -> None:
        """A private module is not a place to import from, so the root has to carry its names."""
        assert [name for name in module.__all__ if name not in tapline.__all__] == []

    def test_no_youtube_name_is_re_exported_at_the_root(self) -> None:
        """A second API gets to have its own SearchResponse without renaming YouTube's."""
        assert [name for name in tapline.youtube.__all__ if name in tapline.__all__] == []

    def test_server_internal_types_are_not_shipped(self) -> None:
        internal = {"RawYTDLPInfo", "RawCommentsPage", "CommentsPage", "SrtResult"}

        assert internal.isdisjoint(dir(tapline.youtube))

    async def test_calls_can_be_in_flight_together(self, api: MockAPI) -> None:
        api.respond(ok(), ok())

        async with TaplineClient(api_key=TEST_API_KEY) as client:
            first, second = await asyncio.gather(
                client.youtube.metadata(VIDEO_ID),
                client.youtube.metadata(VIDEO_ID),
            )

        assert (first.video_id, second.video_id) == (VIDEO_ID, VIDEO_ID)
        assert api.attempts == 2

    def test_the_documented_usage_works(
        self,
        api: MockAPI,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Runs the README's own snippet, so the docs cannot drift from the client."""
        subtitles = captured("subtitles_srt")
        monkeypatch.setenv(ENV_VAR, TEST_API_KEY)
        api.respond(ok(subtitles))

        exec(documented_snippet("Get a transcript"), {})

        assert api.path == (
            "/api/v1/youtube/videos/"
            "https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DjNQXAC9IVRw/subtitles"
        )
        assert api.query == "language=en&subtitle_format=txt&source=any"
        assert subtitles["transcript"] in capsys.readouterr().out
