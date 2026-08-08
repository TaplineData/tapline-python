from __future__ import annotations

import httpx
import pytest
from examples.youtube.download_video_comments import log_comments

from conftest import TEST_API_KEY, VIDEO_ID, MockAPI
from tapline import SyncTaplineClient

COMMENT_ID = "UgxKREWxIgDrw8w2e_Z4AaABAg"


def comment(comment_id: str, author: str, text: str) -> dict[str, object]:
    return {
        "comment_id": comment_id,
        "text": text,
        "like_count": None,
        "dislike_count": None,
        "timestamp": None,
        "published_at": None,
        "is_pinned": None,
        "is_favorited": None,
        "author": author,
        "author_id": None,
        "author_thumbnail": None,
        "author_url": None,
        "author_is_verified": None,
        "author_is_uploader": None,
        "html": None,
    }


def comments_page() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "video_id": VIDEO_ID,
            "returned_count": 1,
            "threads": [
                {
                    "comment": comment(COMMENT_ID, "Alice", "Top-level comment"),
                    "replies_cursor": "reply-page-1",
                }
            ],
            "pagination": {"next_cursor": None, "completion": "exhausted"},
        },
    )


def replies_page() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "video_id": VIDEO_ID,
            "comment_id": COMMENT_ID,
            "returned_count": 1,
            "replies": [
                comment(f"{COMMENT_ID}.reply", "Bob", "Reply"),
            ],
            "pagination": {"next_cursor": None, "completion": "exhausted"},
        },
    )


def missing_comments() -> httpx.Response:
    return httpx.Response(
        404,
        json={
            "code": "not_found",
            "message": "The requested resource was not found.",
            "domain": "youtube",
            "request_id": "comments-request-id",
        },
    )


def test_logs_comments_and_their_replies(
    api: MockAPI,
    caplog: pytest.LogCaptureFixture,
) -> None:
    api.respond(comments_page(), replies_page())

    with (
        SyncTaplineClient(api_key=TEST_API_KEY, max_retries=0) as tapline,
        caplog.at_level("INFO"),
    ):
        counts = log_comments(tapline, VIDEO_ID)

    assert counts == (1, 1)
    assert "Alice: Top-level comment" in caplog.text
    assert "  Bob: Reply" in caplog.text
    assert api.attempts == 2


def test_logs_a_warning_when_comments_are_unavailable(
    api: MockAPI,
    caplog: pytest.LogCaptureFixture,
) -> None:
    api.respond(missing_comments())

    with (
        SyncTaplineClient(api_key=TEST_API_KEY, max_retries=0) as tapline,
        caplog.at_level("INFO"),
    ):
        counts = log_comments(tapline, VIDEO_ID)

    assert counts == (0, 0)
    assert f"Comments or replies unavailable for {VIDEO_ID}; stopping" in caplog.text
    assert api.attempts == 1
