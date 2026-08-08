"""The request each of the eleven endpoints builds, and its parity with the spec.

Every endpoint appears once in :data:`ENDPOINTS`, which states the exact path and
query string the client is expected to produce — once with every parameter set
away from its default, once with only the required ones. Those expectations are
checked against the wire (through both engines) and, separately, against the
contract the server publishes (see :mod:`spec`): the path, the parameter names,
which are required, the defaults, and the credit price. A parameter the server
accepts and the client cannot send — or a default or a price that has drifted —
fails here without anyone updating a list.

The enum parameters are held to the same standard by :class:`TestEnumArguments`:
the ``<Name>Param`` alias each one is annotated through has to keep listing
exactly its enum's values, so the two ways to spell a filter cannot drift apart.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, get_args, get_origin, get_type_hints
from urllib.parse import parse_qsl

import httpx
import pytest

from conftest import VIDEO_ID, Engine, MockAPI, endpoints_of
from spec import SPEC_URL, SpecPath, checked_in, project, youtube_paths
from tapline import not_given
from tapline.resources.youtube import SyncYouTube, YouTube
from tapline.youtube import (
    ChannelContentType,
    CommentSortOrder,
    Feature,
    SearchSort,
    SearchType,
    SubtitleFormat,
    SubtitleSource,
    UploadDate,
    VideoDuration,
    request_enums,
)

PREFIX = "/api/v1/youtube"

CHANNEL_ID = "UCBJycsmduvYEL83R_U4JriQ"
PLAYLIST_ID = "PLbpi6ZahtOH6Blw3RGYpWkSByi_T7Rygb"
COMMENT_ID = "UgxKREWxIgDrw8w2e_Z4AaABAg"
COMMENT_CURSOR = "Eg0SC2RRdzR3OVdnWGNR"
WATCH_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
ENCODED_WATCH_URL = "https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DdQw4w9WgXcQ"

PAGINATION = {"next_cursor": None, "completion": None}


@dataclass(frozen=True)
class Endpoint:
    """One endpoint, and the request it is expected to build."""

    method: str
    path: str
    response: dict[str, Any]
    args: tuple[str, ...] = ()
    required: dict[str, Any] = field(default_factory=dict)
    optional: dict[str, Any] = field(default_factory=dict)
    default_query: str = ""
    explicit_query: str = ""

    @property
    def explicit_call(self) -> dict[str, Any]:
        return {**self.required, **self.optional}


ENDPOINTS = (
    Endpoint(
        method="search",
        path=f"{PREFIX}/search",
        response={"query": "game of thrones", "returned_count": 0, "results": []},
        required={"query": "game of thrones"},
        optional={
            "limit": 5,
            "country": "BR",
            "sort": SearchSort.VIEW_COUNT,
            "upload_date": UploadDate.THIS_WEEK,
            "search_type": SearchType.VIDEO,
            "duration": VideoDuration.OVER_20_MIN,
            "features": [Feature.HD, Feature.FOUR_K],
        },
        default_query="query=game+of+thrones&limit=10&sort=relevance",
        explicit_query=(
            "query=game+of+thrones&limit=5&country=BR&sort=view_count"
            "&upload_date=this_week&search_type=video&duration=over_20_min"
            "&features=hd&features=4k"
        ),
    ),
    Endpoint(
        method="channel",
        path=f"{PREFIX}/channels/%40mkbhd",
        response={
            "channel_id": CHANNEL_ID,
            "channel": "Marques Brownlee",
            "channel_url": None,
            "handle": "@mkbhd",
            "handle_url": None,
            "description": None,
            "channel_follower_count": None,
            "tags": [],
            "thumbnail": None,
            "thumbnails": [],
            "playlist_count": None,
        },
        args=("@mkbhd",),
    ),
    Endpoint(
        method="channel_videos",
        path=f"{PREFIX}/channels/{CHANNEL_ID}/videos",
        response={
            "channel_id": CHANNEL_ID,
            "returned_count": 0,
            "videos": [],
            "pagination": PAGINATION,
        },
        args=(CHANNEL_ID,),
        optional={
            "limit": 10,
            "content_type": ChannelContentType.SHORTS,
            "cursor": "4qmFsgKPARIY==",
        },
        default_query="limit=30&content_type=videos",
        explicit_query="limit=10&content_type=shorts&cursor=4qmFsgKPARIY%3D%3D",
    ),
    Endpoint(
        method="playlist",
        path=f"{PREFIX}/playlist/{PLAYLIST_ID}",
        response={
            "playlist_id": PLAYLIST_ID,
            "title": None,
            "description": None,
            "channel": None,
            "channel_id": None,
            "channel_url": None,
            "handle": None,
            "handle_url": None,
            "thumbnail": None,
            "thumbnails": [],
            "view_count": None,
            "modified_date": None,
            "total_count": None,
            "webpage_url": None,
            "returned_count": 0,
            "entries": [],
        },
        args=(PLAYLIST_ID,),
        optional={"limit": 100},
        default_query="limit=50",
        explicit_query="limit=100",
    ),
    Endpoint(
        method="metadata",
        path=f"{PREFIX}/videos/{ENCODED_WATCH_URL}/metadata",
        response={"video_id": VIDEO_ID},
        args=(WATCH_URL,),
        optional={"fields": ["title", "view_count"]},
        explicit_query="fields=title%2Cview_count",
    ),
    Endpoint(
        method="subtitles",
        path=f"{PREFIX}/videos/{VIDEO_ID}/subtitles",
        response={
            "transcript": "1\n00:00:00,000 --> 00:00:01,000\nhello\n",
            "is_auto_generated": False,
            "metadata": {
                "video_id": VIDEO_ID,
                "title": None,
                "channel": None,
                "channel_id": None,
                "duration": None,
            },
        },
        args=(VIDEO_ID,),
        optional={
            "language": "pt-BR",
            "subtitle_format": SubtitleFormat.JSON3,
            "source": SubtitleSource.MANUAL,
        },
        default_query="language=en&subtitle_format=srt&source=any",
        explicit_query="language=pt-BR&subtitle_format=json3&source=manual",
    ),
    Endpoint(
        method="subtitle_tracks",
        path=f"{PREFIX}/videos/{VIDEO_ID}/subtitles/tracks",
        response={
            "video_id": VIDEO_ID,
            "manual_count": 0,
            "auto_count": 0,
            "manual": [],
            "auto": [],
        },
        args=(VIDEO_ID,),
    ),
    Endpoint(
        method="comments",
        path=f"{PREFIX}/videos/{VIDEO_ID}/comments",
        response={
            "video_id": VIDEO_ID,
            "returned_count": 0,
            "threads": [],
            "pagination": PAGINATION,
        },
        args=(VIDEO_ID,),
        optional={"sort": CommentSortOrder.NEW, "limit": 15, "cursor": COMMENT_CURSOR},
        default_query="sort=top&limit=20",
        explicit_query=f"sort=new&limit=15&cursor={COMMENT_CURSOR}",
    ),
    Endpoint(
        method="comment_replies",
        path=f"{PREFIX}/videos/{VIDEO_ID}/comments/{COMMENT_ID}/replies",
        response={
            "video_id": VIDEO_ID,
            "comment_id": COMMENT_ID,
            "returned_count": 0,
            "replies": [],
            "pagination": PAGINATION,
        },
        args=(VIDEO_ID, COMMENT_ID),
        required={"cursor": COMMENT_CURSOR},
        optional={"limit": 10},
        default_query=f"cursor={COMMENT_CURSOR}&limit=20",
        explicit_query=f"cursor={COMMENT_CURSOR}&limit=10",
    ),
    Endpoint(
        method="formats",
        path=f"{PREFIX}/videos/{VIDEO_ID}/formats",
        response={"video_id": VIDEO_ID, "format_count": 0, "formats": []},
        args=(VIDEO_ID,),
    ),
    Endpoint(
        method="heatmap",
        path=f"{PREFIX}/videos/{VIDEO_ID}/heatmap",
        response={"video_id": VIDEO_ID, "heatmap": None},
        args=(VIDEO_ID,),
    ),
)

BY_METHOD = {endpoint.method: endpoint for endpoint in ENDPOINTS}


def signature_of(method: str) -> inspect.Signature:
    """The awaitable signature; ``test_client`` asserts the blocking twin matches."""
    return inspect.signature(getattr(YouTube, method))


def path_arguments(method: str) -> tuple[str, ...]:
    """The path parameters an endpoint takes, in the order it takes them."""
    return tuple(
        name
        for name, parameter in signature_of(method).parameters.items()
        if parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD and name != "self"
    )


PATH_ARGUMENTS = tuple(
    (endpoint, position, name)
    for endpoint in ENDPOINTS
    for position, name in enumerate(path_arguments(endpoint.method))
)
"""Every ``(endpoint, position, name)`` a caller can put a value of its own into."""


@pytest.fixture(params=ENDPOINTS, ids=lambda endpoint: endpoint.method)
def endpoint(request: pytest.FixtureRequest) -> Endpoint:
    """Each endpoint in turn."""
    spec: Endpoint = request.param
    return spec


class TestRequestBuilding:
    async def test_an_explicit_call_builds_the_expected_request(
        self, api: MockAPI, engine: Engine, endpoint: Endpoint
    ) -> None:
        api.respond(httpx.Response(200, json=endpoint.response))

        await engine.call(endpoint.method, *endpoint.args, **endpoint.explicit_call)

        assert api.request.method == "GET"
        assert api.path == endpoint.path
        assert api.query == endpoint.explicit_query
        assert {key for key, _ in parse_qsl(api.query)} == set(endpoint.explicit_call)

    async def test_a_default_call_builds_the_expected_request(
        self, api: MockAPI, engine: Engine, endpoint: Endpoint
    ) -> None:
        api.respond(httpx.Response(200, json=endpoint.response))

        await engine.call(endpoint.method, *endpoint.args, **endpoint.required)

        assert api.path == endpoint.path
        assert api.query == endpoint.default_query

    async def test_a_list_parameter_repeats_rather_than_joining(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(httpx.Response(200, json=BY_METHOD["search"].response))

        await engine.call("search", query="x", features=[Feature.HD, Feature.FOUR_K])

        assert parse_qsl(api.query, keep_blank_values=True) == [
            ("query", "x"),
            ("limit", "10"),
            ("sort", "relevance"),
            ("features", "hd"),
            ("features", "4k"),
        ]

    async def test_an_omitted_optional_parameter_is_not_sent(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(httpx.Response(200, json=BY_METHOD["metadata"].response))

        await engine.call("metadata", VIDEO_ID, fields=None)

        assert api.query == ""

    async def test_an_empty_cursor_is_dropped(self, api: MockAPI, engine: Engine) -> None:
        api.respond(httpx.Response(200, json=BY_METHOD["comments"].response))

        await engine.call("comments", VIDEO_ID, cursor="")

        assert api.query == "sort=top&limit=20"

    @pytest.mark.parametrize(
        "fields", [["title", "view_count"], ("title", "view_count"), "title,view_count"]
    )
    async def test_a_projection_is_joined_the_way_the_server_reads_it(
        self, api: MockAPI, engine: Engine, fields: str | Sequence[str]
    ) -> None:
        api.respond(httpx.Response(200, json=BY_METHOD["metadata"].response))

        await engine.call("metadata", VIDEO_ID, fields=fields)

        assert api.query == "fields=title%2Cview_count"

    @pytest.mark.parametrize(
        ("identifier", "encoded"),
        [
            (WATCH_URL, ENCODED_WATCH_URL),
            ("https://youtu.be/dQw4w9WgXcQ", "https%3A%2F%2Fyoutu.be%2FdQw4w9WgXcQ"),
            ("a b/c", "a%20b%2Fc"),
            ("a?b=c", "a%3Fb%3Dc"),
            ("a#b", "a%23b"),
            ("../heatmap", "..%2Fheatmap"),
            ("%2e%2e", "%252e%252e"),
            ("...", "..."),
            (".hidden", ".hidden"),
        ],
    )
    async def test_a_video_id_is_encoded_into_a_single_path_segment(
        self, api: MockAPI, engine: Engine, identifier: str, encoded: str
    ) -> None:
        api.respond(httpx.Response(200, json=BY_METHOD["heatmap"].response))

        await engine.call("heatmap", identifier)

        assert api.path == f"{PREFIX}/videos/{encoded}/heatmap"

    async def test_a_handle_is_encoded_into_the_path(self, api: MockAPI, engine: Engine) -> None:
        api.respond(httpx.Response(200, json=BY_METHOD["channel_videos"].response))

        await engine.call("channel_videos", "@mkbhd")

        assert api.path == f"{PREFIX}/channels/%40mkbhd/videos"

    async def test_every_endpoint_honors_a_per_request_timeout(
        self, api: MockAPI, engine: Engine, endpoint: Endpoint
    ) -> None:
        api.respond(httpx.Response(200, json=endpoint.response))

        await engine.call(endpoint.method, *endpoint.args, **endpoint.required, timeout=1.25)

        assert api.request.extensions["timeout"] == {
            "connect": 1.25,
            "read": 1.25,
            "write": 1.25,
            "pool": 1.25,
        }


REQUEST_ENUMS = tuple(
    value
    for value in vars(request_enums).values()
    if isinstance(value, type)
    and issubclass(value, Enum)
    and value.__module__ == request_enums.__name__
)
"""Every enum a request can carry, discovered rather than listed."""


def nested_in(hint: object) -> Iterator[object]:
    """An annotation, and every argument nested anywhere inside it."""
    yield hint
    for argument in get_args(hint):
        yield from nested_in(argument)


def enums_in(parts: tuple[object, ...]) -> set[type[Enum]]:
    """The request enums an annotation's flattened parts mention."""
    return {enum for enum in REQUEST_ENUMS if any(part is enum for part in parts)}


def literals_in(parts: tuple[object, ...]) -> set[object]:
    """Every value the ``Literal``\\ s among an annotation's flattened parts admit."""
    return {value for part in parts if get_origin(part) is Literal for value in get_args(part)}


def enum_parameters(method: str) -> dict[str, tuple[object, ...]]:
    """Each parameter of an endpoint whose type mentions a request enum, flattened."""
    flattened = {
        name: tuple(nested_in(hint))
        for name, hint in get_type_hints(getattr(YouTube, method)).items()
    }
    return {name: parts for name, parts in flattened.items() if enums_in(parts)}


ENUM_ENDPOINTS = tuple(endpoint for endpoint in ENDPOINTS if enum_parameters(endpoint.method))


def plainly_spelled(value: Any) -> Any:
    """The same argument with every enum member written as the string it encodes to."""
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, list):
        return [plainly_spelled(item) for item in value]
    return value


class TestEnumArguments:
    """An enum argument is also spellable as the plain string it encodes to.

    Each enum is annotated through a ``<Name>Param`` alias that unions it with a
    ``Literal`` of its own values, because no type checker can derive one from an
    enum. That ``Literal`` is therefore written out by hand, and these pin it to
    the enum it was copied from.
    """

    def test_four_endpoints_take_an_enum(self) -> None:
        """Pins what the tests below reach, so none of them can go quietly vacuous."""
        assert {endpoint.method for endpoint in ENUM_ENDPOINTS} == {
            "search",
            "channel_videos",
            "subtitles",
            "comments",
        }

    @pytest.mark.parametrize("enum", REQUEST_ENUMS, ids=lambda enum: enum.__name__)
    def test_a_param_alias_lists_exactly_the_values_of_its_enum(self, enum: type[Enum]) -> None:
        widened, spellable = get_args(getattr(request_enums, f"{enum.__name__}Param"))

        assert widened is enum
        assert get_args(spellable) == tuple(member.value for member in enum)

    @pytest.mark.parametrize("endpoint", ENUM_ENDPOINTS, ids=lambda endpoint: str(endpoint.method))
    def test_every_enum_parameter_admits_them(self, endpoint: Endpoint) -> None:
        """The widened alias has to reach the signature, not merely exist."""
        for name, parts in enum_parameters(endpoint.method).items():
            values = {member.value for enum in enums_in(parts) for member in enum}

            assert values <= literals_in(parts), f"{endpoint.method}({name}=…)"

    @pytest.mark.parametrize("endpoint", ENUM_ENDPOINTS, ids=lambda endpoint: str(endpoint.method))
    async def test_a_plain_string_builds_the_request_the_enum_builds(
        self, api: MockAPI, engine: Engine, endpoint: Endpoint
    ) -> None:
        api.respond(httpx.Response(200, json=endpoint.response))
        arguments = {name: plainly_spelled(value) for name, value in endpoint.explicit_call.items()}

        await engine.call(endpoint.method, *endpoint.args, **arguments)

        assert api.query == endpoint.explicit_query


class TestPathTraversal:
    """No caller-supplied identifier may leave the segment it was written into.

    A ``.`` or ``..`` that reached the URL would be resolved away rather than
    sent, so the request would arrive at an endpoint the caller never named —
    ``/videos/../heatmap`` is ``/heatmap``. ``encode_path`` refuses both.
    """

    def test_a_dot_segment_in_a_url_retargets_the_request(self) -> None:
        """The hazard itself, so the guard below is pinned to a real behaviour."""
        assert httpx.URL(f"https://api.tapline.sh{PREFIX}/videos/../heatmap").path == (
            f"{PREFIX}/heatmap"
        )
        assert httpx.URL(f"https://api.tapline.sh{PREFIX}/videos/./heatmap").path == (
            f"{PREFIX}/videos/heatmap"
        )

    @pytest.mark.parametrize("identifier", [".", ".."], ids=["dot", "dot-dot"])
    @pytest.mark.parametrize(
        ("endpoint", "position", "name"),
        PATH_ARGUMENTS,
        ids=[f"{endpoint.method}-{name}" for endpoint, _, name in PATH_ARGUMENTS],
    )
    async def test_a_dot_segment_is_refused_before_anything_is_sent(
        self,
        api: MockAPI,
        engine: Engine,
        endpoint: Endpoint,
        position: int,
        name: str,
        identifier: str,
    ) -> None:
        arguments = list(endpoint.args)
        arguments[position] = identifier

        with pytest.raises(ValueError, match=name):
            await engine.call(endpoint.method, *arguments, **endpoint.required)

        assert api.attempts == 0

    async def test_an_empty_identifier_still_names_the_endpoint_it_was_meant_for(
        self, api: MockAPI, engine: Engine
    ) -> None:
        """An empty segment is the server's 404 to give, not a different route."""
        api.respond(httpx.Response(200, json=BY_METHOD["heatmap"].response))

        await engine.call("heatmap", "")

        assert api.path == f"{PREFIX}/videos//heatmap"


class TestCommentRepliesCursor:
    async def test_calling_without_a_cursor_fails(self, engine: Engine) -> None:
        with pytest.raises(TypeError, match="cursor"):
            await engine.call("comment_replies", VIDEO_ID, COMMENT_ID)

    @pytest.mark.parametrize(
        "method",
        [YouTube.comment_replies, SyncYouTube.comment_replies],
        ids=["async", "sync"],
    )
    def test_the_signature_makes_the_cursor_required(self, method: Callable[..., Any]) -> None:
        cursor = inspect.signature(method).parameters["cursor"]

        assert cursor.default is inspect.Parameter.empty
        assert cursor.kind is inspect.Parameter.KEYWORD_ONLY
        assert cursor.annotation == "str"


def wire_value(value: Any) -> str | None:
    """The form a default takes in a query string, or ``None`` for no default."""
    if value is None:
        return None
    return str(value.value) if isinstance(value, Enum) else str(value)


@pytest.fixture(scope="module")
def spec_paths() -> tuple[SpecPath, ...]:
    """The keyed paths — the demo ones are a separate, unauthenticated surface."""
    return tuple(path for path in youtube_paths() if not path.is_demo)


@pytest.fixture(scope="module")
def spec_for(spec_paths: tuple[SpecPath, ...]) -> Callable[[Endpoint], SpecPath]:
    """Finds the one spec path an endpoint's request lands on."""

    def lookup(endpoint: Endpoint) -> SpecPath:
        matches = [path for path in spec_paths if path.matches(endpoint.path)]
        assert len(matches) == 1, f"{endpoint.path} matched {len(matches)} spec paths"
        return matches[0]

    return lookup


class TestSpecParity:
    def test_the_client_covers_every_path_exactly_once(
        self, spec_paths: tuple[SpecPath, ...], spec_for: Callable[[Endpoint], SpecPath]
    ) -> None:
        reached = [spec_for(endpoint).template for endpoint in ENDPOINTS]

        assert sorted(reached) == sorted(path.template for path in spec_paths)

    def test_every_path_reached_is_a_method_the_client_exposes(self) -> None:
        """Closes the bijection: spec path ↔ table entry ↔ public method."""
        assert set(BY_METHOD) == endpoints_of(YouTube)

    def test_path_parameters_match_the_spec(
        self, endpoint: Endpoint, spec_for: Callable[[Endpoint], SpecPath]
    ) -> None:
        positional = path_arguments(endpoint.method)

        assert positional == spec_for(endpoint).path_params
        assert len(endpoint.args) == len(positional)

    def test_query_parameters_match_the_spec(
        self, endpoint: Endpoint, spec_for: Callable[[Endpoint], SpecPath]
    ) -> None:
        parameters = signature_of(endpoint.method).parameters
        keyword_only = {
            name
            for name, parameter in parameters.items()
            if parameter.kind is inspect.Parameter.KEYWORD_ONLY and name != "timeout"
        }

        assert keyword_only == set(spec_for(endpoint).query_params)
        assert keyword_only == set(endpoint.explicit_call)
        assert parameters["timeout"].default is not_given, "excluded above, so pinned here"

    def test_required_parameters_match_the_spec(
        self, endpoint: Endpoint, spec_for: Callable[[Endpoint], SpecPath]
    ) -> None:
        without_a_default = {
            name
            for name, parameter in signature_of(endpoint.method).parameters.items()
            if parameter.kind is inspect.Parameter.KEYWORD_ONLY
            and parameter.default is inspect.Parameter.empty
        }

        assert without_a_default == set(spec_for(endpoint).required)
        assert without_a_default == set(endpoint.required)

    def test_defaults_match_the_spec(
        self, endpoint: Endpoint, spec_for: Callable[[Endpoint], SpecPath]
    ) -> None:
        parameters = signature_of(endpoint.method).parameters
        spec = spec_for(endpoint)

        for name, spec_default in spec.query_params.items():
            if name in spec.required:
                continue
            assert wire_value(parameters[name].default) == wire_value(spec_default), name

    def test_every_optional_parameter_is_exercised_away_from_its_default(
        self, endpoint: Endpoint
    ) -> None:
        parameters = signature_of(endpoint.method).parameters

        for name, value in endpoint.optional.items():
            assert value != parameters[name].default, name

    def test_the_documented_price_is_the_one_the_endpoint_charges(
        self, endpoint: Endpoint, spec_for: Callable[[Endpoint], SpecPath]
    ) -> None:
        summary = (getattr(YouTube, endpoint.method).__doc__ or "").splitlines()[0]

        assert summary.endswith(f"Costs {spec_for(endpoint).credits} credits.")


@pytest.mark.live
def test_the_checked_in_spec_still_matches_the_published_one() -> None:
    """The one thing the parity tests cannot check for themselves: that they are current."""
    published = httpx.get(SPEC_URL, timeout=30.0).raise_for_status().json()

    assert project(published) == checked_in()
