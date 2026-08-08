from __future__ import annotations

from .._models import BaseModel
from .thumbnail import ThumbnailItem
from .video import VideoListItem

__all__ = ["PlaylistResponse"]


class PlaylistResponse(BaseModel):
    """Response of ``youtube.playlist``."""

    playlist_id: str

    title: str | None

    description: str | None

    channel: str | None
    """Display name of the channel that owns the playlist."""

    channel_id: str | None

    channel_url: str | None

    handle: str | None
    """Owner's channel handle, such as ``"@mkbhd"``."""

    handle_url: str | None

    thumbnail: str | None
    """URL of the preferred thumbnail, the first entry of ``thumbnails``."""

    thumbnails: list[ThumbnailItem]

    view_count: int | None

    modified_date: str | None
    """``YYYY-MM-DD``."""

    total_count: int | None
    """Videos in the playlist, which exceeds ``returned_count`` when ``limit``
    cuts the listing short."""

    webpage_url: str | None

    returned_count: int

    entries: list[VideoListItem]
