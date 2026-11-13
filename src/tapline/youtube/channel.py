from __future__ import annotations

from .._models import BaseModel
from .._pagination import CursorPagination
from .response_enums import ChannelContentTypeValue
from .thumbnail import ThumbnailItem
from .video import VideoListItem

__all__ = ["ChannelResponse", "ChannelVideoItem", "ChannelVideosResponse"]


class ChannelResponse(BaseModel):
    """Response of ``youtube.channel``."""

    channel_id: str
    """Canonical ``UC…`` ID, falling back to the reference you asked for when
    YouTube does not report one."""

    channel: str | None
    """Display name."""

    channel_url: str | None

    handle: str | None
    """Channel handle, such as ``"@mkbhd"``."""

    handle_url: str | None

    description: str | None

    links: list[str] | None
    """Bio links from the channel's About panel. ``None`` on Tapline's fallback
    scraper."""

    facebook_profile_id: str | None
    """Facebook ID the channel linked, usually the page's username."""

    channel_follower_count: int | None

    video_count: int | None

    view_count: int | None
    """Total views across the channel's videos."""

    is_verified: bool | None

    joined_date: str | None
    """``YYYY-MM-DD``."""

    tags: list[str]

    country: str | None
    """Country from the channel's About panel, in English."""

    thumbnail: str | None
    """URL of the preferred avatar, the first entry of ``thumbnails``."""

    thumbnails: list[ThumbnailItem]

    banner: str | None
    """URL of the channel's banner image, widest size."""

    available_content_types: list[ChannelContentTypeValue] | None
    """Which of the videos, shorts and streams tabs the channel has, each one a
    valid ``content_type`` for ``youtube.channel_videos``. ``None`` when Tapline's
    fallback scraper cannot tell the tabs apart."""

    content_tab_count: int | None
    """How many of those tabs the channel has."""

    playlist_count: int | None
    """Deprecated alias of ``content_tab_count``: it counts content tabs, not
    playlists."""


class ChannelVideoItem(VideoListItem):
    """A video as it appears on one of a channel's videos, shorts or streams tabs."""

    published_time_text: str | None
    """Publish date as the channel page labels it, such as ``"2 days ago"``.
    ``None`` on shorts."""

    channel_handle: str | None
    """Channel handle, such as ``"@veritasium"``."""

    content_type: ChannelContentTypeValue
    """The tab the video was listed on."""

    channel_thumbnail: str | None
    """URL of the channel's profile picture."""


class ChannelVideosResponse(BaseModel):
    """Response of ``youtube.channel_videos``."""

    channel_id: str

    returned_count: int

    videos: list[ChannelVideoItem]

    pagination: CursorPagination
