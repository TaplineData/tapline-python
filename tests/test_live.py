"""End-to-end tests against the real Tapline API.

Deselected by default — ``addopts`` carries ``-m "not live"`` — because they
send real requests and spend real credits. Run them deliberately::

    TAPLINE_API_KEY=… uv run pytest -m live

Set ``TAPLINE_BASE_URL`` to point the run at a server other than production.

Asking for them without a key fails the run rather than skipping it: a live
run that proved nothing must not come back green. A full run sends 36
authenticated requests — two credits each, three for ``channel`` — of which
the rejected-key call is never charged and the ones the API turns down for bad
input are refunded.

The rest of the suite pins request construction against a mock transport and
response parsing against the captured payloads in ``tests/fixtures/youtube``.
What only a live run can prove is that the two halves meet: that the paths and
query parameters this client builds are the ones the deployed API serves, and
that what it serves today still fits the models.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Awaitable, Callable

import pytest
from pydantic import BaseModel

from tapline import (
    AuthenticationError,
    InvalidCursorError,
    NotFoundError,
    SyncTaplineClient,
    TaplineClient,
    UnprocessableEntityError,
)
from tapline.resources.youtube import YouTube
from tapline.youtube import (
    ChannelContentType,
    CommentSortOrder,
    Feature,
    Json3Transcript,
    SearchResultType,
    SearchSort,
    SearchType,
    SubtitleFormat,
    SubtitleSource,
    UploadDate,
    VideoDuration,
)

pytestmark = pytest.mark.live

VIDEO = "wt4p2oalmRY"
"""Veritasium: ten chapters, a manual English track, thousands of comments."""

REPLAYED_VIDEO = "dQw4w9WgXcQ"
"""Watched enough to have a heatmap, which most videos do not."""

CHANNEL = "@veritasium"
PLAYLIST = "UUHnyfMqiRRG1u-2MsSQLbXA"

# Every call asks for the smallest page the endpoint allows. These tests check
# that the wiring holds; a wide page proves nothing extra and costs seconds.
PAGE = 1


@pytest.fixture(scope="session", autouse=True)
def api_key() -> str:
    """The key every test here needs; without it the run fails rather than skipping."""
    key = os.environ.get("TAPLINE_API_KEY")
    if not key:
        pytest.fail("TAPLINE_API_KEY is not set, so the live tests cannot run.")
    return key


@pytest.fixture(scope="session")
def base_url() -> str | None:
    """Points the run at a local server when TAPLINE_BASE_URL is set."""
    return os.environ.get("TAPLINE_BASE_URL")


@pytest.fixture
async def tapline(api_key: str, base_url: str | None) -> AsyncIterator[TaplineClient]:
    async with TaplineClient(api_key=api_key, base_url=base_url, timeout=180.0) as client:
        yield client


async def test_search(tapline: TaplineClient) -> None:
    results = await tapline.youtube.search(query="  game of thrones  ", limit=2)

    assert results.query == "game of thrones"
    assert results.returned_count == len(results.results) <= 2
    assert all(hit.result_type for hit in results.results)


async def test_search_narrowed_by_type_and_features(tapline: TaplineClient) -> None:
    results = await tapline.youtube.search(
        query="drone footage",
        limit=2,
        sort=SearchSort.VIEW_COUNT,
        search_type=SearchType.VIDEO,
        duration=VideoDuration.OVER_20_MIN,
        features=[Feature.HD, Feature.FOUR_K],
    )

    assert {hit.result_type for hit in results.results} <= {SearchResultType.VIDEO}


async def test_channel(tapline: TaplineClient) -> None:
    channel = await tapline.youtube.channel(CHANNEL)

    assert channel.channel_id.startswith("UC")
    assert channel.handle == CHANNEL
    assert channel.channel_follower_count


async def test_channel_videos(tapline: TaplineClient) -> None:
    page = await tapline.youtube.channel_videos(
        CHANNEL,
        limit=PAGE,
        content_type=ChannelContentType.VIDEOS,
    )

    assert page.returned_count == len(page.videos) == PAGE
    assert page.videos[0].video_id
    assert page.pagination.next_cursor or page.pagination.completion


async def test_playlist(tapline: TaplineClient) -> None:
    playlist = await tapline.youtube.playlist(PLAYLIST, limit=2)

    assert playlist.playlist_id == PLAYLIST
    assert playlist.returned_count == len(playlist.entries) <= 2
    assert playlist.total_count is None or playlist.total_count >= playlist.returned_count


async def test_metadata(tapline: TaplineClient) -> None:
    video = await tapline.youtube.metadata(VIDEO)

    assert video.video_id == VIDEO
    assert video.chapters
    assert video.duration
    assert video.thumbnails


async def test_metadata_accepts_a_watch_url(tapline: TaplineClient) -> None:
    video = await tapline.youtube.metadata(f"https://www.youtube.com/watch?v={VIDEO}")

    assert video.video_id == VIDEO


async def test_metadata_projects_the_fields_it_is_given(tapline: TaplineClient) -> None:
    video = await tapline.youtube.metadata(VIDEO, fields=["title", "view_count"])

    assert video.model_fields_set == {"video_id", "title", "view_count"}
    assert video.title


async def test_subtitle_tracks(tapline: TaplineClient) -> None:
    tracks = await tapline.youtube.subtitle_tracks(VIDEO)

    assert tracks.video_id == VIDEO
    assert tracks.manual_count == len(tracks.manual)
    assert tracks.auto_count == len(tracks.auto)
    assert SubtitleFormat.SRT in tracks.manual[0].formats


async def test_subtitles_come_back_as_text(tapline: TaplineClient) -> None:
    subtitles = await tapline.youtube.subtitles(
        VIDEO,
        subtitle_format=SubtitleFormat.SRT,
        source=SubtitleSource.MANUAL,
    )

    assert isinstance(subtitles.transcript, str)
    assert "-->" in subtitles.transcript
    assert subtitles.is_auto_generated is False
    assert subtitles.metadata.video_id == VIDEO


async def test_subtitles_come_back_as_a_document_for_json3(tapline: TaplineClient) -> None:
    subtitles = await tapline.youtube.subtitles(VIDEO, subtitle_format=SubtitleFormat.JSON3)

    assert isinstance(subtitles.transcript, Json3Transcript)
    assert any(segment.utf8 for event in subtitles.transcript.events for segment in event.segs)


async def test_comments(tapline: TaplineClient) -> None:
    page = await tapline.youtube.comments(VIDEO, limit=PAGE)

    assert page.video_id == VIDEO
    assert page.returned_count == len(page.threads) == PAGE
    assert page.threads[0].comment.comment_id


async def test_comment_replies(tapline: TaplineClient) -> None:
    threads = await tapline.youtube.comments(VIDEO, limit=20)
    thread = next(thread for thread in threads.threads if thread.replies_cursor)
    comment_id, cursor = thread.comment.comment_id, thread.replies_cursor
    assert comment_id is not None
    assert cursor is not None

    replies = await tapline.youtube.comment_replies(
        VIDEO,
        comment_id,
        cursor=cursor,
        limit=PAGE,
    )

    assert replies.video_id == VIDEO
    assert replies.comment_id == comment_id
    assert replies.returned_count == len(replies.replies) == PAGE


async def test_comments_paginate_by_cursor(tapline: TaplineClient) -> None:
    first = await tapline.youtube.comments(VIDEO, limit=5)
    cursor = first.pagination.next_cursor
    assert cursor is not None

    second = await tapline.youtube.comments(VIDEO, limit=5, cursor=cursor)

    seen = {thread.comment.comment_id for thread in first.threads}
    assert seen.isdisjoint(thread.comment.comment_id for thread in second.threads)
    assert second.pagination.next_cursor != cursor


async def test_formats(tapline: TaplineClient) -> None:
    formats = await tapline.youtube.formats(VIDEO)

    assert formats.format_count == len(formats.formats)
    assert all(item.url for item in formats.formats)
    assert all(item.format_note != "storyboard" for item in formats.formats)


async def test_heatmap(tapline: TaplineClient) -> None:
    heatmap = await tapline.youtube.heatmap(REPLAYED_VIDEO)

    assert heatmap.video_id == REPLAYED_VIDEO
    assert heatmap.heatmap
    assert all(0.0 <= slice_.value <= 1.0 for slice_ in heatmap.heatmap)
    assert all(
        earlier.end_time == later.start_time
        for earlier, later in zip(heatmap.heatmap, heatmap.heatmap[1:], strict=False)
    )


EVERY_PARAMETER: dict[str, Callable[[YouTube], Awaitable[BaseModel]]] = {
    "search": lambda yt: yt.search(
        query="documentary",
        limit=1,
        country="US",
        sort=SearchSort.RATING,
        upload_date=UploadDate.THIS_YEAR,
        search_type=SearchType.VIDEO,
        duration=VideoDuration.FOUR_TO_20_MIN,
        features=[Feature.HD, Feature.SUBTITLES],
    ),
    "channel": lambda yt: yt.channel(CHANNEL),
    "channel_videos": lambda yt: yt.channel_videos(
        CHANNEL, limit=PAGE, content_type=ChannelContentType.SHORTS, cursor=""
    ),
    "playlist": lambda yt: yt.playlist(PLAYLIST, limit=1),
    "metadata": lambda yt: yt.metadata(VIDEO, fields="title,view_count,duration"),
    "subtitle_tracks": lambda yt: yt.subtitle_tracks(VIDEO),
    "subtitles": lambda yt: yt.subtitles(
        VIDEO, language="en", subtitle_format=SubtitleFormat.VTT, source=SubtitleSource.AUTO
    ),
    "comments": lambda yt: yt.comments(VIDEO, sort=CommentSortOrder.NEW, limit=PAGE, cursor=""),
    "formats": lambda yt: yt.formats(VIDEO),
    "heatmap": lambda yt: yt.heatmap(REPLAYED_VIDEO),
}
"""Every optional parameter at a non-default value, so the API sees each one at least once.

The assertion is that nothing comes back ``422``: a rejected parameter would mean
this client spells a name or a value differently from the server that serves it.
``comment_replies`` is absent because its cursor has to come from a live page;
``test_comment_replies`` exercises its full signature instead.
"""


@pytest.mark.parametrize("endpoint", sorted(EVERY_PARAMETER))
async def test_every_parameter_is_one_the_api_accepts(
    tapline: TaplineClient, endpoint: str
) -> None:
    await EVERY_PARAMETER[endpoint](tapline.youtube)


async def test_an_unknown_playlist_raises_not_found(tapline: TaplineClient) -> None:
    with pytest.raises(NotFoundError) as caught:
        await tapline.youtube.playlist("PLzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")

    assert caught.value.status_code == 404
    assert caught.value.code == "not_found"
    assert caught.value.request_id


async def test_an_unknown_video_is_not_an_error(tapline: TaplineClient) -> None:
    """A well-formed video ID that does not exist comes back 200, not 404.

    yt-dlp answers for any syntactically valid ID, so the API cannot tell an
    unwatchable video from an absent one and returns a record with a synthesised
    title and nothing else. Callers have to test a field, not catch an exception.
    """
    video = await tapline.youtube.metadata("aaaaaaaaaaa")

    assert video.video_id == "aaaaaaaaaaa"
    assert video.duration is None
    assert video.channel_id is None


async def test_a_malformed_cursor_raises_invalid_cursor(tapline: TaplineClient) -> None:
    with pytest.raises(InvalidCursorError) as caught:
        await tapline.youtube.comments(VIDEO, cursor="not-a-real-cursor")

    assert caught.value.status_code == 400
    assert caught.value.code == "invalid_cursor"


async def test_a_cursor_bound_to_another_video_is_rejected(tapline: TaplineClient) -> None:
    page = await tapline.youtube.comments(VIDEO, limit=PAGE)
    assert page.pagination.next_cursor is not None

    with pytest.raises(InvalidCursorError):
        await tapline.youtube.comments(REPLAYED_VIDEO, cursor=page.pagination.next_cursor)


async def test_a_limit_out_of_range_raises_unprocessable(tapline: TaplineClient) -> None:
    with pytest.raises(UnprocessableEntityError) as caught:
        await tapline.youtube.search(query="anything", limit=999)

    assert caught.value.status_code == 422
    assert caught.value.code == "invalid_request"
    assert caught.value.details


async def test_a_rejected_key_raises_authentication_error(base_url: str | None) -> None:
    async with TaplineClient(api_key="not-a-real-key", base_url=base_url, timeout=60.0) as tapline:
        with pytest.raises(AuthenticationError) as caught:
            await tapline.youtube.heatmap(REPLAYED_VIDEO)

    assert caught.value.status_code == 401
    assert caught.value.code == "unauthenticated"


def test_the_blocking_client_reaches_the_api(api_key: str, base_url: str | None) -> None:
    with SyncTaplineClient(api_key=api_key, base_url=base_url, timeout=180.0) as tapline:
        channel = tapline.youtube.channel(CHANNEL)

    assert channel.handle == CHANNEL
