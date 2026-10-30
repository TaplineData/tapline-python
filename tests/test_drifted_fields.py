"""The HTTP client preserves drifted JSON without validating or coercing values.

Each case starts from a captured payload and breaks one field the way a scraped
source does without notice.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, cast

import httpx
import pytest

from conftest import VIDEO_ID, Engine, MockAPI, fetch_market_trades
from tapline.brave_search import BraveSearchPlaceContact, BraveSearchWebPage
from tapline.ponsfamily import MarketTrade
from tapline.tiktok import TikTokCommentsResponse

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
TIKTOK_VIDEO_URL = "https://www.tiktok.com/@tiktok/video/7106594312292453675"


def load_fixture(service: str, stem: str) -> Any:
    return json.loads((FIXTURES / service / f"{stem}.json").read_text())


async def resolve(result: Any) -> Any:
    """The value of a call on either engine."""
    return await result if inspect.isawaitable(result) else result


async def fetch_tiktok_comments(engine: Engine) -> TikTokCommentsResponse:
    comments: TikTokCommentsResponse = await resolve(
        engine.client.tiktok.get_comments(url=TIKTOK_VIDEO_URL)
    )
    return comments


async def test_a_missing_field_reads_as_none_while_the_rest_of_the_response_parses(
    api: MockAPI, engine: Engine
) -> None:
    payload = load_fixture("brave_search", "search.query_local")
    place = payload["locations"]["results"][0]
    del place["contact"]["telephone"]
    api.respond(httpx.Response(200, json=payload))

    page: BraveSearchWebPage = await resolve(engine.client.brave_search.search(query="pizza"))

    assert page.locations is not None
    parsed_place = page.locations.results[0]
    assert parsed_place.title == place["title"]
    assert isinstance(parsed_place.contact, BraveSearchPlaceContact)
    assert cast(object, parsed_place.contact.telephone) is None
    assert parsed_place.contact.model_fields_set == set()
    assert page.model_dump(mode="json", by_alias=True, exclude_unset=True) == payload


async def test_a_field_of_another_type_keeps_its_value(api: MockAPI, engine: Engine) -> None:
    api.respond(
        httpx.Response(
            200, json=[{"side": "buy", "blockNumber": 1}, {"side": "sell", "blockNumber": "late"}]
        )
    )

    trades = await fetch_market_trades(engine)

    assert [type(trade) for trade in trades] == [MarketTrade, MarketTrade]
    assert [trade.side for trade in trades] == ["buy", "sell"]
    assert trades[0].blockNumber == 1
    assert cast(object, trades[1].blockNumber) == "late"
    assert trades[1].model_fields_set == {"side", "blockNumber"}


@pytest.mark.parametrize("payload", [["not", "an", "object"], "text", 42, True, None])
async def test_an_unexpected_top_level_json_kind_is_preserved(
    api: MockAPI, engine: Engine, payload: object
) -> None:
    api.respond(httpx.Response(200, content=json.dumps(payload)))

    assert await engine.call("metadata", VIDEO_ID) == payload


async def test_an_object_where_a_list_belongs_is_preserved(api: MockAPI, engine: Engine) -> None:
    payload = {"side": "buy"}
    api.respond(httpx.Response(200, json=payload))

    assert cast(object, await fetch_market_trades(engine)) == payload


async def test_unexpected_list_items_do_not_discard_the_list(api: MockAPI, engine: Engine) -> None:
    api.respond(httpx.Response(200, json=[{"side": "buy"}, "unexpected", None, [1, 2]]))

    trades = await fetch_market_trades(engine)

    assert isinstance(trades[0], MarketTrade)
    assert trades[0].side == "buy"
    assert cast(object, trades[1:]) == ["unexpected", None, [1, 2]]


async def test_missing_required_fields_do_not_change_the_fields_sent(
    api: MockAPI, engine: Engine
) -> None:
    api.respond(httpx.Response(200, json={"title": "A title"}))

    video = await engine.call("metadata", VIDEO_ID)

    assert video.video_id is None
    assert video.title == "A title"
    assert video.model_fields_set == {"title"}
    assert video.model_dump(exclude_unset=True) == {"title": "A title"}


async def test_fields_are_neither_coerced_nor_dropped(api: MockAPI, engine: Engine) -> None:
    payload = {
        "video_id": 123,
        "duration": "212",
        "channel_is_verified": "false",
        "thumbnails": [{"url": "https://example.com/image", "width": "480"}, "broken"],
        "chapters": "unavailable",
        "future_field": {"items": [1, None, "new"]},
    }
    api.respond(httpx.Response(200, json=payload))

    video = await engine.call("metadata", VIDEO_ID)

    assert video.video_id == 123
    assert video.duration == "212"
    assert video.channel_is_verified == "false"
    assert video.thumbnails[0].width == "480"
    assert video.thumbnails[1] == "broken"
    assert video.chapters == "unavailable"
    assert video.future_field == payload["future_field"]
    assert video.model_dump(mode="json", exclude_unset=True, warnings=False) == payload


async def test_a_tiktok_comments_page_missing_its_cursor_still_parses(
    api: MockAPI, engine: Engine
) -> None:
    payload = load_fixture("tiktok", "get_comments.default")
    del payload["cursor"]
    api.respond(httpx.Response(200, json=payload))

    comments = await fetch_tiktok_comments(engine)

    assert cast(object, comments.cursor) is None
    assert comments.has_more == payload["has_more"]
    assert comments.comments[0].cid == payload["comments"][0]["cid"]
