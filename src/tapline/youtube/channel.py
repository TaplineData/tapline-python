from __future__ import annotations

from .._models import BaseModel
from .._pagination import CursorPagination
from .thumbnail import ThumbnailItem
from .video import VideoListItem

__all__ = ["ChannelResponse", "ChannelVideosResponse"]


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

    channel_follower_count: int | None

    tags: list[str]

    thumbnail: str | None
    """URL of the preferred avatar, the first entry of ``thumbnails``."""

    thumbnails: list[ThumbnailItem]

    playlist_count: int | None


class ChannelVideosResponse(BaseModel):
    """Response of ``youtube.channel_videos``."""

    channel_id: str

    returned_count: int

    videos: list[VideoListItem]

    pagination: CursorPagination
