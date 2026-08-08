from __future__ import annotations

from .._models import BaseModel
from .response_enums import LiveStatusValue, SearchResultTypeValue
from .thumbnail import ThumbnailItem

__all__ = ["SearchResponse", "SearchResultItem"]


class SearchResultItem(BaseModel):
    """One search hit.

    ``result_type`` decides which of the remaining fields carry anything: a
    channel hit has no duration or view count, a playlist hit has no live
    status, and so on.
    """

    result_type: SearchResultTypeValue

    id: str | None
    """Video, channel or playlist ID, according to ``result_type``."""

    title: str | None

    url: str | None

    duration: int | None
    """Seconds."""

    view_count: int | None

    channel: str | None

    channel_id: str | None

    channel_url: str | None

    thumbnail: str | None
    """URL of the preferred thumbnail, the first entry of ``thumbnails``."""

    thumbnails: list[ThumbnailItem] | None

    description: str | None

    live_status: LiveStatusValue | None

    channel_is_verified: bool | None


class SearchResponse(BaseModel):
    """Response of ``youtube.search``."""

    query: str
    """The query as searched, after stripping."""

    returned_count: int

    results: list[SearchResultItem]
