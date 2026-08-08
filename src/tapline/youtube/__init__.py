"""Every type the YouTube endpoints send and accept.

::

    from tapline import SyncTaplineClient
    from tapline.youtube import SearchResponse, SearchSort

    with SyncTaplineClient() as tapline:
        results: SearchResponse = tapline.youtube.search(
            query="game of thrones", sort=SearchSort.VIEW_COUNT
        )

One module per API keeps names such as :class:`SearchResponse` and
:class:`SearchSort` free for the next API to use as well. The names shared by
every API — the clients, the exception hierarchy, :class:`~tapline.BaseModel`
and :class:`~tapline.CursorPagination` — stay at the root, in :mod:`tapline`.

``tapline.youtube`` the module is where the types live; ``tapline.youtube`` the
attribute on a client is where the eleven methods live.
"""

from __future__ import annotations

from .channel import ChannelResponse, ChannelVideosResponse
from .comment import CommentItem, CommentsResponse, CommentThread, RepliesResponse
from .format import FormatItem, FormatsResponse
from .heatmap import HeatmapItem, HeatmapResponse
from .json3 import Json3Event, Json3Segment, Json3Transcript
from .playlist import PlaylistResponse
from .request_enums import (
    ChannelContentType,
    ChannelContentTypeParam,
    CommentSortOrder,
    CommentSortOrderParam,
    Feature,
    FeatureParam,
    SearchSort,
    SearchSortParam,
    SearchType,
    SearchTypeParam,
    SubtitleFormat,
    SubtitleFormatParam,
    SubtitleSource,
    SubtitleSourceParam,
    UploadDate,
    UploadDateParam,
    VideoDuration,
    VideoDurationParam,
)
from .response_enums import (
    AudioExt,
    AudioExtValue,
    Availability,
    AvailabilityValue,
    Container,
    ContainerValue,
    DynamicRange,
    DynamicRangeValue,
    Ext,
    ExtValue,
    LiveStatus,
    LiveStatusValue,
    MediaType,
    MediaTypeValue,
    Protocol,
    ProtocolValue,
    SearchResultType,
    SearchResultTypeValue,
    SubtitleFormatValue,
    VideoExt,
    VideoExtValue,
)
from .search import SearchResponse, SearchResultItem
from .subtitle import (
    SubtitleMetadata,
    SubtitleResponse,
    SubtitleTrackItem,
    SubtitleTracksResponse,
)
from .thumbnail import ThumbnailItem
from .video import ChapterItem, VideoListItem, VideoMetadataResponse

__all__ = [
    "AudioExt",
    "AudioExtValue",
    "Availability",
    "AvailabilityValue",
    "ChannelContentType",
    "ChannelContentTypeParam",
    "ChannelResponse",
    "ChannelVideosResponse",
    "ChapterItem",
    "CommentItem",
    "CommentSortOrder",
    "CommentSortOrderParam",
    "CommentThread",
    "CommentsResponse",
    "Container",
    "ContainerValue",
    "DynamicRange",
    "DynamicRangeValue",
    "Ext",
    "ExtValue",
    "Feature",
    "FeatureParam",
    "FormatItem",
    "FormatsResponse",
    "HeatmapItem",
    "HeatmapResponse",
    "Json3Event",
    "Json3Segment",
    "Json3Transcript",
    "LiveStatus",
    "LiveStatusValue",
    "MediaType",
    "MediaTypeValue",
    "PlaylistResponse",
    "Protocol",
    "ProtocolValue",
    "RepliesResponse",
    "SearchResponse",
    "SearchResultItem",
    "SearchResultType",
    "SearchResultTypeValue",
    "SearchSort",
    "SearchSortParam",
    "SearchType",
    "SearchTypeParam",
    "SubtitleFormat",
    "SubtitleFormatParam",
    "SubtitleFormatValue",
    "SubtitleMetadata",
    "SubtitleResponse",
    "SubtitleSource",
    "SubtitleSourceParam",
    "SubtitleTrackItem",
    "SubtitleTracksResponse",
    "ThumbnailItem",
    "UploadDate",
    "UploadDateParam",
    "VideoDuration",
    "VideoDurationParam",
    "VideoExt",
    "VideoExtValue",
    "VideoListItem",
    "VideoMetadataResponse",
]
