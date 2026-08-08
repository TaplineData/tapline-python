"""Enums that arrive on a response, each paired with an open ``<Name>Value``.

A value on a response is news, not a client bug. YouTube ships new codecs,
containers and video classes without notice, yt-dlp emits composite values that
were never enumerated (``https+https`` for a merged format), and Tapline itself
can start serving a new subtitle format. Any of those is additive on the server
and must not take down an installed client: rejecting a whole response over one
unrecognised string loses the other few hundred fields that parsed.

So every enum a response can carry is annotated through its ``<Name>Value``
alias. The alias tries the enum first and falls through to a plain ``str``, so a
known value still arrives as a member you can compare and branch on, while an
unrecognised one arrives verbatim. The bare enum is exported for those
comparisons and for ``in`` checks against its members.

Enums that only travel the other way, into a request, are closed — see
:mod:`tapline.youtube.request_enums`. :class:`SubtitleFormat` travels both
ways, so it is declared there and opened here.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, TypeAlias

from .._models import PREFER_ENUM
from .request_enums import SubtitleFormat

__all__ = [
    "AudioExt",
    "AudioExtValue",
    "Availability",
    "AvailabilityValue",
    "Container",
    "ContainerValue",
    "DynamicRange",
    "DynamicRangeValue",
    "Ext",
    "ExtValue",
    "LiveStatus",
    "LiveStatusValue",
    "MediaType",
    "MediaTypeValue",
    "Protocol",
    "ProtocolValue",
    "SearchResultType",
    "SearchResultTypeValue",
    "SubtitleFormatValue",
    "VideoExt",
    "VideoExtValue",
]


class LiveStatus(str, Enum):
    """Live-broadcast status yt-dlp derives for a video."""

    IS_LIVE = "is_live"
    IS_UPCOMING = "is_upcoming"
    WAS_LIVE = "was_live"
    POST_LIVE = "post_live"
    NOT_LIVE = "not_live"


class Availability(str, Enum):
    """Who upstream reports the video as being viewable by."""

    PUBLIC = "public"
    UNLISTED = "unlisted"
    NEEDS_AUTH = "needs_auth"
    PREMIUM_ONLY = "premium_only"
    SUBSCRIBER_ONLY = "subscriber_only"
    PRIVATE = "private"


class MediaType(str, Enum):
    """Class of video YouTube's extractors assign."""

    VIDEO = "video"
    SHORT = "short"
    CLIP = "clip"
    LIVESTREAM = "livestream"


class Ext(str, Enum):
    """Container extension of a format."""

    MP4 = "mp4"
    M4A = "m4a"
    WEBM = "webm"
    MHTML = "mhtml"


class AudioExt(str, Enum):
    """Extension of a format's audio stream; ``none`` marks a video-only format."""

    M4A = "m4a"
    WEBM = "webm"
    NONE = "none"


class VideoExt(str, Enum):
    """Extension of a format's video stream; ``none`` marks an audio-only format."""

    MP4 = "mp4"
    WEBM = "webm"
    NONE = "none"


class Protocol(str, Enum):
    """Transport protocol a format is delivered over.

    Only the atomic protocols are enumerated. A merged format reports a
    composite such as ``https+https``, which arrives as a plain string.
    """

    HTTPS = "https"
    MHTML = "mhtml"
    M3U8_NATIVE = "m3u8_native"
    HTTP_DASH_SEGMENTS = "http_dash_segments"


class DynamicRange(str, Enum):
    """Dynamic range of a format's video stream."""

    SDR = "SDR"
    HDR10 = "HDR10"
    HDR10PLUS = "HDR10+"
    HDR12 = "HDR12"
    HLG = "HLG"
    DV = "DV"


class Container(str, Enum):
    """DASH container reported for a format."""

    M4A_DASH = "m4a_dash"
    MP4_DASH = "mp4_dash"
    WEBM_DASH = "webm_dash"


class SearchResultType(str, Enum):
    """Kind of entity a search result refers to.

    Currently member-for-member the same as
    :class:`~tapline.youtube.SearchType`, which restricts a search to one kind.
    They are separate because one is what you ask for and the other is what
    came back: YouTube can serve a kind that is not offered as a filter.
    """

    VIDEO = "video"
    CHANNEL = "channel"
    PLAYLIST = "playlist"
    MOVIE = "movie"


LiveStatusValue: TypeAlias = Annotated[LiveStatus | str, PREFER_ENUM]
AvailabilityValue: TypeAlias = Annotated[Availability | str, PREFER_ENUM]
MediaTypeValue: TypeAlias = Annotated[MediaType | str, PREFER_ENUM]
ExtValue: TypeAlias = Annotated[Ext | str, PREFER_ENUM]
AudioExtValue: TypeAlias = Annotated[AudioExt | str, PREFER_ENUM]
VideoExtValue: TypeAlias = Annotated[VideoExt | str, PREFER_ENUM]
ProtocolValue: TypeAlias = Annotated[Protocol | str, PREFER_ENUM]
DynamicRangeValue: TypeAlias = Annotated[DynamicRange | str, PREFER_ENUM]
ContainerValue: TypeAlias = Annotated[Container | str, PREFER_ENUM]
SearchResultTypeValue: TypeAlias = Annotated[SearchResultType | str, PREFER_ENUM]
SubtitleFormatValue: TypeAlias = Annotated[SubtitleFormat | str, PREFER_ENUM]
