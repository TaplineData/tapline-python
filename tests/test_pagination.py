"""Walking a cursor-paginated endpoint with ``pages``, through both engines.

``pages`` is the one public method the resources inherit rather than declare,
so it is exercised here against the same scripted API the endpoints use: the
cursors it puts on the wire, where it stops, and what it has not yet fetched.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from typing import Any
from urllib.parse import parse_qsl

import httpx

from conftest import VIDEO_ID, Engine, MockAPI
from tapline import CursorCompletion
from tapline.youtube import CommentSortOrder

COMMENT_ID = "UgxKREWxIgDrw8w2e_Z4AaABAg"


def comments(next_cursor: str | None, *, completion: str | None = None) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "video_id": VIDEO_ID,
            "returned_count": 0,
            "threads": [],
            "pagination": {"next_cursor": next_cursor, "completion": completion},
        },
    )


def replies(next_cursor: str | None, *, completion: str | None = None) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "video_id": VIDEO_ID,
            "comment_id": COMMENT_ID,
            "returned_count": 0,
            "replies": [],
            "pagination": {"next_cursor": next_cursor, "completion": completion},
        },
    )


def cursors_sent(api: MockAPI) -> list[str | None]:
    """The ``cursor`` each request carried, ``None`` where it carried none."""
    return [dict(parse_qsl(request.url.query.decode())).get("cursor") for request in api.requests]


def walk(engine: Engine, fetch: Callable[[str], Any], *, cursor: str = "") -> Any:
    """Start a walk on whichever engine is under test, without advancing it."""
    youtube: Any = engine.client.youtube
    return youtube.pages(fetch, cursor=cursor)


async def collect(pages: Any) -> list[Any]:
    if isinstance(pages, AsyncGenerator):
        return [page async for page in pages]
    return list(pages)


async def take_one(pages: Any) -> Any:
    """The first page of a walk, abandoning the rest without exhausting it."""
    if isinstance(pages, AsyncGenerator):
        page = await anext(pages)
        await pages.aclose()
        return page
    page = next(pages)
    pages.close()
    return page


class TestWalk:
    async def test_a_walk_follows_each_cursor_to_the_end(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(comments("c1"), comments("c2"), comments(None, completion="exhausted"))

        pages = await collect(
            walk(engine, lambda cursor: engine.client.youtube.comments(VIDEO_ID, cursor=cursor))
        )

        assert cursors_sent(api) == [None, "c1", "c2"]
        assert [page.video_id for page in pages] == [VIDEO_ID] * 3
        assert pages[-1].pagination.completion is CursorCompletion.EXHAUSTED

    async def test_a_walk_stops_at_the_depth_limit_the_server_reports(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(comments("c1"), comments(None, completion="depth_limit"))

        pages = await collect(
            walk(engine, lambda cursor: engine.client.youtube.comments(VIDEO_ID, cursor=cursor))
        )

        assert len(pages) == 2
        assert pages[-1].pagination.completion is CursorCompletion.DEPTH_LIMIT

    async def test_a_single_page_walk_sends_one_request(self, api: MockAPI, engine: Engine) -> None:
        api.respond(comments(None, completion="exhausted"))

        pages = await collect(
            walk(engine, lambda cursor: engine.client.youtube.comments(VIDEO_ID, cursor=cursor))
        )

        assert len(pages) == 1
        assert api.attempts == 1

    async def test_a_walk_starts_from_the_cursor_it_is_given(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(replies("r2"), replies(None, completion="exhausted"))

        await collect(
            walk(
                engine,
                lambda cursor: engine.client.youtube.comment_replies(
                    VIDEO_ID, COMMENT_ID, cursor=cursor
                ),
                cursor="r1",
            )
        )

        assert cursors_sent(api) == ["r1", "r2"]

    async def test_a_walk_requests_nothing_until_it_is_advanced(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(comments("c1"), comments(None, completion="exhausted"))

        pages = walk(engine, lambda cursor: engine.client.youtube.comments(VIDEO_ID, cursor=cursor))
        assert api.attempts == 0

        page = await take_one(pages)

        assert api.attempts == 1
        assert page.pagination.next_cursor == "c1"

    async def test_a_walk_passes_the_endpoint_its_own_arguments(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(comments(None, completion="exhausted"))

        await collect(
            walk(
                engine,
                lambda cursor: engine.client.youtube.comments(
                    VIDEO_ID, sort=CommentSortOrder.NEW, limit=5, cursor=cursor
                ),
            )
        )

        assert api.query == "sort=new&limit=5"
