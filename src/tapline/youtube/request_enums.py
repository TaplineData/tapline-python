"""Enums that travel into a request, listing every value the API accepts.

These are closed. A value outside the enum is one the server would reject
anyway, so it is a client bug and should fail here rather than over the wire.

Each enum is paired with a ``<Name>Param`` alias that adds the same values
spelled as plain strings, and that alias — not the bare enum — is what the
endpoint parameters are annotated with. So ``sort=SearchSort.VIEW_COUNT`` and
``sort="view_count"`` are the same call, one of them costs no import, and
``sort="view_kount"`` still fails the type check. The enum stays exported for
comparisons, for iteration, and as the readable spelling of a default.

An alias whose members drift from its enum's would silently reopen the set it
closes, so ``tests/test_youtube_params.py`` asserts the two still agree, that
every enum here has one, and that every endpoint parameter uses it.

Enums that arrive on a response are opened instead — see
:mod:`tapline.youtube.response_enums`.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, TypeAlias

__all__ = [
    "ChannelContentType",
    "ChannelContentTypeParam",
    "CommentSortOrder",
    "CommentSortOrderParam",
    "Feature",
    "FeatureParam",
    "SearchSort",
    "SearchSortParam",
    "SearchType",
    "SearchTypeParam",
    "SubtitleFormat",
    "SubtitleFormatParam",
    "SubtitleSource",
    "SubtitleSourceParam",
    "UploadDate",
    "UploadDateParam",
    "VideoDuration",
    "VideoDurationParam",
]


class SearchSort(str, Enum):
    """Order in which YouTube search results are ranked."""

    RELEVANCE = "relevance"
    UPLOAD_DATE = "upload_date"
    VIEW_COUNT = "view_count"
    RATING = "rating"


SearchSortParam: TypeAlias = (
    SearchSort | Literal["relevance", "upload_date", "view_count", "rating"]
)


class UploadDate(str, Enum):
    """Upload-recency window to restrict search results to."""

    LAST_HOUR = "last_hour"
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    THIS_YEAR = "this_year"


UploadDateParam: TypeAlias = (
    UploadDate | Literal["last_hour", "today", "this_week", "this_month", "this_year"]
)


class SearchType(str, Enum):
    """Result kind to restrict a search to.

    The kind a result comes back as is
    :class:`~tapline.youtube.SearchResultType`, which currently lists the same
    members and is open where this is closed.
    """

    VIDEO = "video"
    CHANNEL = "channel"
    PLAYLIST = "playlist"
    MOVIE = "movie"


SearchTypeParam: TypeAlias = SearchType | Literal["video", "channel", "playlist", "movie"]


class VideoDuration(str, Enum):
    """Duration band to restrict video search results to."""

    UNDER_4_MIN = "under_4_min"
    FOUR_TO_20_MIN = "4_to_20_min"
    OVER_20_MIN = "over_20_min"


VideoDurationParam: TypeAlias = VideoDuration | Literal["under_4_min", "4_to_20_min", "over_20_min"]


class Feature(str, Enum):
    """Feature flag a search result must carry."""

    LIVE = "live"
    FOUR_K = "4k"
    HD = "hd"
    SUBTITLES = "subtitles"
    CREATIVE_COMMONS = "creative_commons"
    THREE_SIXTY = "360"
    VR180 = "vr180"
    THREE_D = "3d"
    HDR = "hdr"
    LOCATION = "location"
    PURCHASED = "purchased"


FeatureParam: TypeAlias = (
    Feature
    | Literal[
        "live",
        "4k",
        "hd",
        "subtitles",
        "creative_commons",
        "360",
        "vr180",
        "3d",
        "hdr",
        "location",
        "purchased",
    ]
)


class SubtitleFormat(str, Enum):
    """Document format a subtitle track is served in.

    The only enum here that also comes back on a response, where
    :data:`~tapline.youtube.SubtitleFormatValue` opens it.
    """

    SRT = "srt"
    VTT = "vtt"
    JSON3 = "json3"
    TTML = "ttml"
    TXT = "txt"


SubtitleFormatParam: TypeAlias = SubtitleFormat | Literal["srt", "vtt", "json3", "ttml", "txt"]


class SubtitleSource(str, Enum):
    """Caption-track provenance: human-authored versus machine-generated."""

    ANY = "any"
    MANUAL = "manual"
    AUTO = "auto"


SubtitleSourceParam: TypeAlias = SubtitleSource | Literal["any", "manual", "auto"]


class CommentSortOrder(str, Enum):
    """Order in which a video's comments are fetched."""

    TOP = "top"
    NEW = "new"


CommentSortOrderParam: TypeAlias = CommentSortOrder | Literal["top", "new"]


class ChannelContentType(str, Enum):
    """Tab of a channel's uploads to list."""

    VIDEOS = "videos"
    SHORTS = "shorts"
    STREAMS = "streams"


ChannelContentTypeParam: TypeAlias = ChannelContentType | Literal["videos", "shorts", "streams"]
