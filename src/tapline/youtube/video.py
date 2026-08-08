from __future__ import annotations

from pydantic import Field

from .._models import BaseModel
from .heatmap import HeatmapItem
from .response_enums import AvailabilityValue, LiveStatusValue, MediaTypeValue
from .thumbnail import ThumbnailItem

__all__ = ["ChapterItem", "VideoListItem", "VideoMetadataResponse"]


class ChapterItem(BaseModel):
    """One creator-defined chapter of a video."""

    start_time: float
    """Seconds from the start of the video."""

    end_time: float
    """Seconds from the start of the video."""

    title: str


class VideoListItem(BaseModel):
    """A video as it appears inside a channel or playlist listing.

    Listings come from YouTube's own index rather than from the video page, so
    every field but the identifier can be missing for any given entry.
    """

    video_id: str | None

    title: str | None

    url: str | None

    duration: int | None = None
    """Seconds. Absent entirely from listings YouTube serves without durations,
    such as a channel's shorts tab."""

    view_count: int | None

    channel: str | None

    channel_id: str | None

    channel_url: str | None

    thumbnail: str | None
    """URL of the preferred thumbnail, the first entry of ``thumbnails``."""

    thumbnails: list[ThumbnailItem] | None

    live_status: LiveStatusValue | None

    channel_is_verified: bool | None


class VideoMetadataResponse(BaseModel):
    """Response of ``youtube.metadata``.

    Passing ``fields`` to the endpoint projects the response: it comes back
    with ``video_id`` plus only the keys you asked for, and every other key is
    absent rather than null. ``video_id`` is therefore the only field
    guaranteed to be present, and the rest default here so a projection parses.

    Use :attr:`model_fields_set` to tell a field the server omitted from one it
    sent as ``null``, and ``model_dump(exclude_unset=True)`` to get back
    exactly the keys the server sent.
    """

    video_id: str

    title: str | None = None

    fulltitle: str | None = None
    """Title before yt-dlp strips any live-broadcast decoration."""

    description: str | None = None

    duration: int | None = None
    """Seconds."""

    duration_string: str | None = None
    """Human-readable duration, such as ``"12:07"``."""

    upload_date: str | None = None
    """``YYYY-MM-DD``."""

    timestamp: int | None = None
    """Unix seconds for ``upload_date``."""

    release_timestamp: int | None = None
    """Unix seconds a premiere or stream was scheduled for."""

    release_date: str | None = None
    """``YYYY-MM-DD``."""

    view_count: int | None = None

    like_count: int | None = None

    comment_count: int | None = None

    handle: str | None = None
    """Channel handle, such as ``"@mkbhd"``."""

    handle_url: str | None = None

    channel: str | None = None

    channel_id: str | None = None

    channel_url: str | None = None

    channel_follower_count: int | None = None

    channel_is_verified: bool | None = None

    thumbnail: str | None = None
    """URL of the preferred thumbnail, the first entry of ``thumbnails``."""

    thumbnails: list[ThumbnailItem] = Field(default_factory=list)

    width: int | None = None

    height: int | None = None

    categories: list[str] | None = None

    tags: list[str] = Field(default_factory=list)

    live_status: LiveStatusValue | None = None

    availability: AvailabilityValue | None = None

    age_limit: int | None = None

    playable_in_embed: bool | None = None

    webpage_url: str | None = None

    original_url: str | None = None
    """The URL the video was resolved from, which may be a shorts or share link."""

    language: str | None = None
    """BCP-47 tag of the video's primary language."""

    chapters: list[ChapterItem] | None = None

    heatmap: list[HeatmapItem] | None = None

    concurrent_view_count: int | None = None
    """Viewers watching right now. Set only while a stream is live."""

    location: str | None = None

    license: str | None = None

    media_type: MediaTypeValue | None = None
