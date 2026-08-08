"""Check the models against live authenticated responses, field by field.

The rest of the suite pins request construction against a mock transport and
parsing against captured payloads. Neither can tell you that the models still
describe what the deployed API returns today. This does, by driving the real
client at the real authenticated endpoints and holding each parsed model up
against the raw bytes that produced it::

    TAPLINE_API_KEY=… uv run python scripts/validate_live.py
    TAPLINE_API_KEY=… TAPLINE_BASE_URL=http://localhost:8000 \
        uv run python scripts/validate_live.py

Two failures are reported per endpoint, and they are different bugs:

``undeclared`` is a field the API sent that no model declares, caught in
pydantic's extra bucket at any depth. The response still parsed, so no test
fails, but the client is behind the API and a user reaching for that field
finds nothing.

``dropped`` is a key the raw JSON carries that survives neither as a declared
field nor as an extra — data the client silently loses.

Requests cost credits. One pass over the eleven endpoints spends 25.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections.abc import Awaitable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar, cast

import httpx
from pydantic import BaseModel
from typing_extensions import override

from tapline import TaplineClient
from tapline.youtube import Feature, SearchType, SubtitleFormat

VIDEO = "wt4p2oalmRY"
REPLAYED_VIDEO = "dQw4w9WgXcQ"
CHANNEL = "@veritasium"
CHANNEL_BY_ID = "UCHnyfMqiRRG1u-2MsSQLbXA"
PLAYLIST = "UUHnyfMqiRRG1u-2MsSQLbXA"

_ModelT = TypeVar("_ModelT", bound=BaseModel)


class RecordingTransport(httpx.AsyncBaseTransport):
    """Keeps the raw body of each response so it can be diffed against the model."""

    def __init__(self, inner: httpx.AsyncBaseTransport) -> None:
        self._inner = inner
        self.bodies: list[bytes] = []

    @override
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        response = await self._inner.handle_async_request(request)
        body = await response.aread()
        self.bodies.append(body)
        return httpx.Response(
            status_code=response.status_code,
            headers=response.headers,
            content=body,
            request=request,
        )


def walk_extras(value: object, path: str = "") -> Iterator[str]:
    """Every undeclared field pydantic parked in an extra bucket, with its path."""
    if isinstance(value, BaseModel):
        for key in value.model_extra or {}:
            yield f"{path}.{key}".lstrip(".")
        for name in type(value).model_fields:
            yield from walk_extras(getattr(value, name), f"{path}.{name}".lstrip("."))
    elif isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        for mapping_key, item in mapping.items():
            yield from walk_extras(item, f"{path}[{mapping_key}]")
    elif isinstance(value, (list, tuple)):
        sequence = cast(Sequence[object], value)
        for index, item in enumerate(sequence):
            yield from walk_extras(item, f"{path}[{index}]")


def walk_missing(raw: object, dumped: object, path: str = "") -> Iterator[str]:
    """Every key present in the raw JSON that the round-trip did not reproduce."""
    if isinstance(raw, Mapping):
        if not isinstance(dumped, Mapping):
            yield f"{path} (raw is an object, dump is {type(dumped).__name__})"
            return
        raw_mapping = cast(Mapping[object, object], raw)
        dumped_mapping = cast(Mapping[object, object], dumped)
        for key, item in raw_mapping.items():
            if key not in dumped_mapping:
                yield f"{path}.{key}".lstrip(".")
            else:
                yield from walk_missing(
                    item, dumped_mapping[key], f"{path}.{key}".lstrip(".")
                )
    elif isinstance(raw, list):
        raw_items = cast(list[object], raw)
        dumped_items = cast(list[object], dumped) if isinstance(dumped, list) else None
        if dumped_items is None or len(dumped_items) != len(raw_items):
            seen = len(dumped_items) if dumped_items is not None else "n/a"
            yield f"{path} (list length {len(raw_items)} vs {seen})"
            return
        for index, item in enumerate(raw_items):
            yield from walk_missing(item, dumped_items[index], f"{path}[{index}]")


@dataclass
class Result:
    endpoint: str
    model: str
    undeclared: list[str]
    dropped: list[str]
    note: str = ""

    @property
    def ok(self) -> bool:
        return not self.undeclared and not self.dropped


async def main() -> int:
    key = os.environ.get("TAPLINE_API_KEY")
    if not key:
        print("TAPLINE_API_KEY is not set.", file=sys.stderr)
        return 2
    base_url = os.environ.get("TAPLINE_BASE_URL")

    recorder = RecordingTransport(httpx.AsyncHTTPTransport())
    http_client = httpx.AsyncClient(transport=recorder, timeout=180.0)
    results: list[Result] = []

    async with TaplineClient(api_key=key, base_url=base_url, http_client=http_client) as tapline:
        yt = tapline.youtube

        async def check(
            endpoint: str, awaitable: Awaitable[_ModelT], note: str = ""
        ) -> _ModelT:
            before = len(recorder.bodies)
            model = await awaitable
            raw = json.loads(recorder.bodies[before])
            dumped = model.model_dump(mode="json")
            results.append(
                Result(
                    endpoint=endpoint,
                    model=type(model).__name__,
                    undeclared=sorted(set(walk_extras(model))),
                    dropped=sorted(set(walk_missing(raw, dumped))),
                    note=note,
                )
            )
            return model

        await check("search", yt.search(query="game of thrones", limit=3))
        await check(
            "search (filtered)",
            yt.search(
                query="veritasium",
                limit=2,
                search_type=SearchType.VIDEO,
                features=[Feature.HD],
                country="US",
            ),
            "search_type + repeated features + country",
        )
        await check("channel", yt.channel(CHANNEL), "@handle")
        await check("channel (by id)", yt.channel(CHANNEL_BY_ID), "UC… id")
        await check("channel_videos", yt.channel_videos(CHANNEL, limit=3))
        await check("playlist", yt.playlist(PLAYLIST, limit=3))
        await check("metadata", yt.metadata(VIDEO))
        await check(
            "metadata (url)",
            yt.metadata(f"https://www.youtube.com/watch?v={VIDEO}"),
            "watch URL as a path segment",
        )
        await check(
            "metadata (fields)",
            yt.metadata(VIDEO, fields="title,view_count,duration"),
            "projection",
        )
        await check("subtitle_tracks", yt.subtitle_tracks(VIDEO))
        await check("subtitles (srt)", yt.subtitles(VIDEO))
        await check(
            "subtitles (json3)",
            yt.subtitles(VIDEO, subtitle_format=SubtitleFormat.JSON3),
            "transcript is an object, not a string",
        )
        comments = await check("comments", yt.comments(VIDEO, limit=3))

        reply_target: tuple[str, str] | None = None
        for thread in comments.threads:
            if thread.replies_cursor is not None and thread.comment.comment_id is not None:
                reply_target = (thread.replies_cursor, thread.comment.comment_id)
                break
        if reply_target is not None:
            cursor, comment_id = reply_target
            await check(
                "comment_replies",
                yt.comment_replies(VIDEO, comment_id=comment_id, cursor=cursor, limit=3),
                "cursor taken from a live comments page",
            )
        else:
            results.append(
                Result("comment_replies", "-", [], [], "no thread on this page had replies")
            )

        next_cursor = comments.pagination.next_cursor
        if next_cursor:
            await check(
                "comments (page 2)",
                yt.comments(VIDEO, limit=3, cursor=next_cursor),
                "cursor round-trips through a second page",
            )

        await check("formats", yt.formats(VIDEO))
        await check("heatmap", yt.heatmap(REPLAYED_VIDEO))

    width = max(len(r.endpoint) for r in results)
    print(f"\n{'endpoint':<{width}}  {'model':<24} undeclared  dropped  note")
    print("-" * (width + 62))
    for r in results:
        flag = "ok" if r.ok else "FAIL"
        print(
            f"{r.endpoint:<{width}}  {r.model:<24} "
            f"{len(r.undeclared):>10}  {len(r.dropped):>7}  {r.note or flag}"
        )
    for r in results:
        for field in r.undeclared:
            print(f"\nUNDECLARED  {r.endpoint}: {field}")
        for field in r.dropped:
            print(f"\nDROPPED     {r.endpoint}: {field}")

    failed = [r for r in results if not r.ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} responses round-tripped losslessly.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
