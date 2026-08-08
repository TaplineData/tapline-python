from __future__ import annotations

import httpx
import pytest
from examples.youtube.download_channel_transcripts import log_transcripts

from conftest import TEST_API_KEY, MockAPI
from tapline import SyncTaplineClient

VIDEO_ID = "dQw4w9WgXcQ"


def channel_page(*, with_video: bool) -> httpx.Response:
    videos = (
        [
            {
                "video_id": VIDEO_ID,
                "title": "Test video",
                "url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
                "view_count": 10,
                "channel": "Test channel",
                "channel_id": "UCtest",
                "channel_url": "https://www.youtube.com/@test",
                "thumbnail": None,
                "thumbnails": [],
                "live_status": None,
                "channel_is_verified": False,
            }
        ]
        if with_video
        else []
    )
    return httpx.Response(
        200,
        json={
            "channel_id": "@test",
            "returned_count": len(videos),
            "videos": videos,
            "pagination": {"next_cursor": None, "completion": "exhausted"},
        },
    )


def transcript() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "transcript": "A short transcript.\n",
            "is_auto_generated": False,
            "metadata": {
                "video_id": VIDEO_ID,
                "title": "Test video",
                "channel": "Test channel",
                "channel_id": "UCtest",
                "duration": 10,
            },
        },
    )


def missing_transcript() -> httpx.Response:
    return httpx.Response(
        404,
        json={
            "code": "not_found",
            "message": "The requested resource was not found.",
            "domain": "youtube",
            "request_id": "transcript-request-id",
        },
    )


def test_logs_transcripts_from_each_channel_tab(
    api: MockAPI,
    caplog: pytest.LogCaptureFixture,
) -> None:
    api.respond(
        channel_page(with_video=True),
        transcript(),
        channel_page(with_video=False),
        channel_page(with_video=False),
    )

    with (
        SyncTaplineClient(api_key=TEST_API_KEY, max_retries=0) as tapline,
        caplog.at_level("INFO"),
    ):
        transcript_count = log_transcripts(tapline, "@test")

    assert transcript_count == 1
    assert "Test video" in caplog.text
    assert "A short transcript." in caplog.text
    assert api.requests[1].url.query.decode() == "language=en&subtitle_format=txt&source=any"
    assert api.attempts == 4


def test_logs_a_warning_and_continues_when_a_transcript_is_missing(
    api: MockAPI,
    caplog: pytest.LogCaptureFixture,
) -> None:
    api.respond(
        channel_page(with_video=True),
        missing_transcript(),
        channel_page(with_video=False),
        channel_page(with_video=False),
    )

    with (
        SyncTaplineClient(api_key=TEST_API_KEY, max_retries=0) as tapline,
        caplog.at_level("INFO"),
    ):
        transcript_count = log_transcripts(tapline, "@test")

    assert transcript_count == 0
    assert f"No transcript found for Test video ({VIDEO_ID}); skipping" in caplog.text
    assert api.attempts == 4
