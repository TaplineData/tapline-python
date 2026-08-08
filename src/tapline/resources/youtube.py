"""The eleven YouTube endpoints, in awaitable and blocking form.

Each endpoint's path and query parameters are built once, by the private
``_search``, ``_channel``, … functions below. Both resources call the same
builder, so the twins differ only in ``await``.
"""

from __future__ import annotations

from collections.abc import Sequence

from .._base_client import encode_path
from .._resource import AsyncAPIResource, Request, SyncAPIResource
from .._types import NotGiven, Timeout, not_given
from ..youtube import (
    ChannelContentType,
    ChannelContentTypeParam,
    ChannelResponse,
    ChannelVideosResponse,
    CommentSortOrder,
    CommentSortOrderParam,
    CommentsResponse,
    FeatureParam,
    FormatsResponse,
    HeatmapResponse,
    PlaylistResponse,
    RepliesResponse,
    SearchResponse,
    SearchSort,
    SearchSortParam,
    SearchTypeParam,
    SubtitleFormat,
    SubtitleFormatParam,
    SubtitleResponse,
    SubtitleSource,
    SubtitleSourceParam,
    SubtitleTracksResponse,
    UploadDateParam,
    VideoDurationParam,
    VideoMetadataResponse,
)

__all__ = ["SyncYouTube", "YouTube"]

_PREFIX = "/api/v1/youtube"


def _search(
    *,
    query: str,
    limit: int,
    country: str | None,
    sort: SearchSortParam,
    upload_date: UploadDateParam | None,
    search_type: SearchTypeParam | None,
    duration: VideoDurationParam | None,
    features: Sequence[FeatureParam] | None,
) -> Request[SearchResponse]:
    return Request(
        _PREFIX + "/search",
        SearchResponse,
        {
            "query": query,
            "limit": limit,
            "country": country,
            "sort": sort,
            "upload_date": upload_date,
            "search_type": search_type,
            "duration": duration,
            "features": features,
        },
    )


def _channel(channel_id: str) -> Request[ChannelResponse]:
    return Request(
        encode_path(_PREFIX + "/channels/{channel_id}", channel_id=channel_id),
        ChannelResponse,
    )


def _channel_videos(
    channel_id: str,
    *,
    limit: int,
    content_type: ChannelContentTypeParam,
    cursor: str,
) -> Request[ChannelVideosResponse]:
    return Request(
        encode_path(_PREFIX + "/channels/{channel_id}/videos", channel_id=channel_id),
        ChannelVideosResponse,
        {"limit": limit, "content_type": content_type, "cursor": cursor or None},
    )


def _playlist(playlist_id: str, *, limit: int) -> Request[PlaylistResponse]:
    return Request(
        encode_path(_PREFIX + "/playlist/{playlist_id}", playlist_id=playlist_id),
        PlaylistResponse,
        {"limit": limit},
    )


def _comma_joined(fields: str | Sequence[str] | None) -> str | None:
    """Render a projection the way the server reads it, as one joined string."""
    return fields if fields is None or isinstance(fields, str) else ",".join(fields)


def _metadata(
    video_id: str,
    *,
    fields: str | Sequence[str] | None,
) -> Request[VideoMetadataResponse]:
    return Request(
        encode_path(_PREFIX + "/videos/{video_id}/metadata", video_id=video_id),
        VideoMetadataResponse,
        {"fields": _comma_joined(fields)},
    )


def _subtitles(
    video_id: str,
    *,
    language: str,
    subtitle_format: SubtitleFormatParam,
    source: SubtitleSourceParam,
) -> Request[SubtitleResponse]:
    return Request(
        encode_path(_PREFIX + "/videos/{video_id}/subtitles", video_id=video_id),
        SubtitleResponse,
        {"language": language, "subtitle_format": subtitle_format, "source": source},
    )


def _subtitle_tracks(video_id: str) -> Request[SubtitleTracksResponse]:
    return Request(
        encode_path(_PREFIX + "/videos/{video_id}/subtitles/tracks", video_id=video_id),
        SubtitleTracksResponse,
    )


def _comments(
    video_id: str,
    *,
    sort: CommentSortOrderParam,
    limit: int,
    cursor: str,
) -> Request[CommentsResponse]:
    return Request(
        encode_path(_PREFIX + "/videos/{video_id}/comments", video_id=video_id),
        CommentsResponse,
        {"sort": sort, "limit": limit, "cursor": cursor or None},
    )


def _comment_replies(
    video_id: str,
    comment_id: str,
    *,
    cursor: str,
    limit: int,
) -> Request[RepliesResponse]:
    return Request(
        encode_path(
            _PREFIX + "/videos/{video_id}/comments/{comment_id}/replies",
            video_id=video_id,
            comment_id=comment_id,
        ),
        RepliesResponse,
        {"cursor": cursor, "limit": limit},
    )


def _formats(video_id: str) -> Request[FormatsResponse]:
    return Request(
        encode_path(_PREFIX + "/videos/{video_id}/formats", video_id=video_id),
        FormatsResponse,
    )


def _heatmap(video_id: str) -> Request[HeatmapResponse]:
    return Request(
        encode_path(_PREFIX + "/videos/{video_id}/heatmap", video_id=video_id),
        HeatmapResponse,
    )


class YouTube(AsyncAPIResource):
    """The YouTube endpoints, awaitable.

    Reached as :attr:`~tapline.TaplineClient.youtube`::

        tapline = TaplineClient(api_key=api_key)
        comments = await tapline.youtube.comments(video_id="dQw4w9WgXcQ")

    Anywhere a method takes a ``video_id`` or ``channel_id`` it also takes the
    URL you copied out of the browser; the server resolves it. Anywhere one
    takes an enum it also takes that enum's value as a plain string, so
    ``sort=SearchSort.VIEW_COUNT`` and ``sort="view_count"`` are one call.

    :meth:`channel_videos`, :meth:`comments`, and :meth:`comment_replies` are
    cursor-paginated and return one page per call; :meth:`pages` walks one of
    them to its end.

    Every method raises ``AuthenticationError`` when the API key is rejected,
    ``InsufficientCreditsError`` when the account cannot pay for the call,
    ``RateLimitError`` once automatic retries are exhausted, and
    ``InternalServerError`` when Tapline or YouTube itself fails. The
    per-method ``Raises:`` sections list only what is particular to that
    endpoint.
    """

    async def search(
        self,
        *,
        query: str,
        limit: int = 10,
        country: str | None = None,
        sort: SearchSortParam = SearchSort.RELEVANCE,
        upload_date: UploadDateParam | None = None,
        search_type: SearchTypeParam | None = None,
        duration: VideoDurationParam | None = None,
        features: Sequence[FeatureParam] | None = None,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> SearchResponse:
        """Search YouTube and return matching results. Costs 2 credits.

        Args:
            query: Search text, 1–200 characters. Surrounding whitespace is
                stripped, and the stripped form comes back as ``query``.
            limit: Maximum results to return (1–20).
            country: ISO 3166-1 alpha-2 code to search from, such as ``"BR"``.
                Omit to let YouTube pick the region.
            sort: Rank order — ``relevance``, ``upload_date``, ``view_count``,
                or ``rating``.
            upload_date: Restrict results to an upload-recency window —
                ``last_hour``, ``today``, ``this_week``, ``this_month``, or
                ``this_year``.
            search_type: Restrict results to a single kind — ``video``,
                ``channel``, ``playlist``, or ``movie``. Omit for every kind.
            duration: Restrict video results to a duration band —
                ``under_4_min``, ``4_to_20_min``, or ``over_20_min``.
            features: Features every result must carry, such as ``hd`` or
                ``subtitles``; :class:`~tapline.youtube.Feature` lists all
                eleven. Sent as one repeated query parameter per feature.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.SearchResponse`. A search that matched
            nothing returns an empty ``results``, not an error.

        Raises:
            UnprocessableEntityError: ``query``, ``limit``, or ``country`` is
                outside the range the server accepts.
        """
        return await self._send(
            _search(
                query=query,
                limit=limit,
                country=country,
                sort=sort,
                upload_date=upload_date,
                search_type=search_type,
                duration=duration,
                features=features,
            ),
            timeout=timeout,
        )

    async def channel(
        self,
        channel_id: str,
        *,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> ChannelResponse:
        """Get a channel's public profile and statistics. Costs 3 credits.

        Args:
            channel_id: Channel ID (``UC…``), ``@handle``, or a channel URL
                using ``/channel/``, ``/@``, ``/c/``, or ``/user/``. A URL may
                not carry a content tab or a query string.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.ChannelResponse`: display name, handle,
            description, subscriber count, avatars, and playlist count.

        Raises:
            NotFoundError: No such channel.
            UnprocessableEntityError: ``channel_id`` is not a channel ID,
                handle, or supported URL.
        """
        return await self._send(_channel(channel_id), timeout=timeout)

    async def channel_videos(
        self,
        channel_id: str,
        *,
        limit: int = 30,
        content_type: ChannelContentTypeParam = ChannelContentType.VIDEOS,
        cursor: str = "",
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> ChannelVideosResponse:
        """List a channel's uploads, one cursor page at a time. Costs 2 credits.

        Args:
            channel_id: Channel ID (``UC…``), ``@handle``, or channel URL, as
                for :meth:`channel`. Use the same reference for every page.
            limit: Maximum items to return from this page (1–30). The cursor
                still advances by YouTube's full page.
            content_type: Which tab to list — ``videos``, ``shorts``, or
                ``streams``. Ignored when ``cursor`` is set, because the cursor
                carries the walk's tab.
            cursor: ``pagination.next_cursor`` from the previous page. Leave
                empty for the first page.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.ChannelVideosResponse`, one page of a
            walk. Pass its ``pagination.next_cursor`` back as ``cursor`` until
            that comes back ``None``, or hand the whole walk to :meth:`pages`.
            The last page's ``pagination.completion`` says whether the channel
            ran out (``exhausted``) or the cursor outgrew its 8,000-character
            cap (``depth_limit``).

        Raises:
            NotFoundError: No such channel.
            InvalidCursorError: ``cursor`` is malformed, expired, or belongs to
                another channel.
            UnprocessableEntityError: ``channel_id`` is not a channel ID,
                handle, or supported URL.
        """
        return await self._send(
            _channel_videos(
                channel_id,
                limit=limit,
                content_type=content_type,
                cursor=cursor,
            ),
            timeout=timeout,
        )

    async def playlist(
        self,
        playlist_id: str,
        *,
        limit: int = 50,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> PlaylistResponse:
        """Get a public playlist and its videos. Costs 2 credits.

        Args:
            playlist_id: Playlist ID, 2–150 characters of ``A-Z``, ``a-z``,
                ``0-9``, ``_``, and ``-``.
            limit: Maximum entries to return (1–100). ``total_count`` reports
                how many the playlist actually holds.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.PlaylistResponse`, with the videos in
            ``entries``.

        Raises:
            NotFoundError: No such playlist.
            PermissionDeniedError: The playlist is private.
            UnprocessableEntityError: ``playlist_id`` is malformed.
        """
        return await self._send(_playlist(playlist_id, limit=limit), timeout=timeout)

    async def metadata(
        self,
        video_id: str,
        *,
        fields: str | Sequence[str] | None = None,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> VideoMetadataResponse:
        """Get public metadata for a video. Costs 2 credits.

        Args:
            video_id: Eleven-character video ID, or a ``watch?v=``,
                ``youtu.be/``, ``shorts/``, ``embed/``, or ``live/`` URL.
            fields: Projection of the record to return, named by the fields of
                :class:`~tapline.youtube.VideoMetadataResponse` — either a
                sequence of names or an already comma-joined string.
                ``video_id`` always comes back. Omit for the whole record.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.VideoMetadataResponse`. Under a projection
            the unselected keys are absent rather than null, so use
            ``model_fields_set`` to tell them from fields the server sent as
            ``None``.

        Raises:
            NotFoundError: No such video, or it has been removed.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
            UnprocessableEntityError: ``fields`` names a key that is not part
                of the metadata record, or ``video_id`` is not an ID or a
                supported URL.
        """
        return await self._send(_metadata(video_id, fields=fields), timeout=timeout)

    async def subtitles(
        self,
        video_id: str,
        *,
        language: str = "en",
        subtitle_format: SubtitleFormatParam = SubtitleFormat.SRT,
        source: SubtitleSourceParam = SubtitleSource.ANY,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> SubtitleResponse:
        """Get a video's subtitles as a transcript document. Costs 2 credits.

        Args:
            video_id: Video ID or supported video URL, as for :meth:`metadata`.
            language: Language tag of the track, such as ``"en"``, ``"pt-BR"``,
                ``"es-419"``, or ``"zh-Hans"``. ``"orig"`` asks for the video's
                original audio language, and a ``-orig`` suffix (``"en-orig"``)
                for that language's untranslated track. Call
                :meth:`subtitle_tracks` for the tags a video actually has.
            subtitle_format: Document format — ``srt``, ``vtt``, ``json3``,
                ``ttml``, or ``txt`` for the cue text alone, one line per cue.
            source: Which track to serve — ``manual`` (human-authored),
                ``auto`` (machine-generated), or ``any``, which prefers manual
                and falls back to auto.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.SubtitleResponse` whose ``transcript`` is
            a :class:`~tapline.youtube.Json3Transcript` for ``json3`` and a
            ``str`` for every other format.

        Raises:
            NotFoundError: The video has no track matching ``language``,
                ``source``, and ``subtitle_format``.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
            UnprocessableEntityError: ``language`` is not a registered
                language tag.
        """
        return await self._send(
            _subtitles(
                video_id,
                language=language,
                subtitle_format=subtitle_format,
                source=source,
            ),
            timeout=timeout,
        )

    async def subtitle_tracks(
        self,
        video_id: str,
        *,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> SubtitleTracksResponse:
        """List the subtitle tracks a video has. Costs 2 credits.

        Args:
            video_id: Video ID or supported video URL, as for :meth:`metadata`.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.SubtitleTracksResponse`, splitting the
            tracks into ``manual`` and ``auto``. Each track's ``language`` and
            ``formats`` feed straight into :meth:`subtitles`.

        Raises:
            NotFoundError: No such video, or it has been removed.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
        """
        return await self._send(_subtitle_tracks(video_id), timeout=timeout)

    async def comments(
        self,
        video_id: str,
        *,
        sort: CommentSortOrderParam = CommentSortOrder.TOP,
        limit: int = 20,
        cursor: str = "",
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> CommentsResponse:
        """Get a video's comment threads, one cursor page at a time. Costs 2 credits.

        Args:
            video_id: Video ID or supported video URL, as for :meth:`metadata`.
            sort: Comment order — ``top`` or ``new``. Pinned threads surface
                first either way. Ignored when ``cursor`` is set, because the
                cursor carries the walk's sort.
            limit: Maximum threads to return from this page (1–20). The cursor
                still advances by YouTube's full 20-thread page.
            cursor: ``pagination.next_cursor`` from the previous page. Leave
                empty for the first page.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.CommentsResponse`, one page of a walk.
            Pass its ``pagination.next_cursor`` back as ``cursor`` until that
            comes back ``None``, or hand the whole walk to :meth:`pages`;
            sorting by ``top`` stops at roughly 1,200 comments with
            ``completion="depth_limit"``. Each thread carries a
            ``replies_cursor`` for :meth:`comment_replies`.

        Raises:
            NotFoundError: No such video, or it has been removed.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
            InvalidCursorError: ``cursor`` is malformed, expired, or belongs to
                another video.
        """
        return await self._send(
            _comments(video_id, sort=sort, limit=limit, cursor=cursor),
            timeout=timeout,
        )

    async def comment_replies(
        self,
        video_id: str,
        comment_id: str,
        *,
        cursor: str,
        limit: int = 20,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> RepliesResponse:
        """Get replies to a comment, one cursor page at a time. Costs 2 credits.

        Args:
            video_id: Video ID or supported video URL, as for :meth:`metadata`.
            comment_id: Top-level comment ID, 5–150 characters of ``A-Z``,
                ``a-z``, ``0-9``, ``_``, ``.``, and ``-``.
            cursor: Required. The ``replies_cursor`` of a
                :class:`~tapline.youtube.CommentThread` for the first page, then
                ``pagination.next_cursor`` for each page after it. There is no
                replies endpoint without a cursor: a comment with no replies
                has ``replies_cursor=None``.
            limit: Maximum replies to return from this page (1–20). The cursor
                still advances by YouTube's full reply page, currently ten.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.RepliesResponse`, one page of a walk.
            Pass its ``pagination.next_cursor`` back as ``cursor`` until that
            comes back ``None``, or hand the whole walk to :meth:`pages`,
            starting it from ``replies_cursor``.

        Raises:
            InvalidCursorError: ``cursor`` is malformed, expired, or belongs to
                another video or comment.
            NotFoundError: No such video, or it has been removed.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
        """
        return await self._send(
            _comment_replies(video_id, comment_id, cursor=cursor, limit=limit),
            timeout=timeout,
        )

    async def formats(
        self,
        video_id: str,
        *,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> FormatsResponse:
        """List the streams YouTube offers for a video. Costs 2 credits.

        Args:
            video_id: Video ID or supported video URL, as for :meth:`metadata`.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.FormatsResponse`, storyboard formats
            excluded. Each ``url`` is signed by YouTube and expires in hours.

        Raises:
            NotFoundError: No such video, or it has been removed.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
        """
        return await self._send(_formats(video_id), timeout=timeout)

    async def heatmap(
        self,
        video_id: str,
        *,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> HeatmapResponse:
        """Get the replay heatmap for a video. Costs 2 credits.

        Args:
            video_id: Video ID or supported video URL, as for :meth:`metadata`.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.HeatmapResponse`. ``heatmap`` scores
            equal slices of the timeline — a hundred of them — by replay
            intensity, and is ``None`` for the many videos YouTube publishes
            no heatmap for, which is not an error.

        Raises:
            NotFoundError: No such video, or it has been removed.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
        """
        return await self._send(_heatmap(video_id), timeout=timeout)


class SyncYouTube(SyncAPIResource):
    """The YouTube endpoints, blocking.

    Reached as :attr:`~tapline.SyncTaplineClient.youtube`::

        tapline = SyncTaplineClient(api_key=api_key)
        comments = tapline.youtube.comments(video_id="dQw4w9WgXcQ")

    Anywhere a method takes a ``video_id`` or ``channel_id`` it also takes the
    URL you copied out of the browser; the server resolves it. Anywhere one
    takes an enum it also takes that enum's value as a plain string, so
    ``sort=SearchSort.VIEW_COUNT`` and ``sort="view_count"`` are one call.

    :meth:`channel_videos`, :meth:`comments`, and :meth:`comment_replies` are
    cursor-paginated and return one page per call; :meth:`pages` walks one of
    them to its end.

    Every method raises ``AuthenticationError`` when the API key is rejected,
    ``InsufficientCreditsError`` when the account cannot pay for the call,
    ``RateLimitError`` once automatic retries are exhausted, and
    ``InternalServerError`` when Tapline or YouTube itself fails. The
    per-method ``Raises:`` sections list only what is particular to that
    endpoint.
    """

    def search(
        self,
        *,
        query: str,
        limit: int = 10,
        country: str | None = None,
        sort: SearchSortParam = SearchSort.RELEVANCE,
        upload_date: UploadDateParam | None = None,
        search_type: SearchTypeParam | None = None,
        duration: VideoDurationParam | None = None,
        features: Sequence[FeatureParam] | None = None,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> SearchResponse:
        """Search YouTube and return matching results. Costs 2 credits.

        Args:
            query: Search text, 1–200 characters. Surrounding whitespace is
                stripped, and the stripped form comes back as ``query``.
            limit: Maximum results to return (1–20).
            country: ISO 3166-1 alpha-2 code to search from, such as ``"BR"``.
                Omit to let YouTube pick the region.
            sort: Rank order — ``relevance``, ``upload_date``, ``view_count``,
                or ``rating``.
            upload_date: Restrict results to an upload-recency window —
                ``last_hour``, ``today``, ``this_week``, ``this_month``, or
                ``this_year``.
            search_type: Restrict results to a single kind — ``video``,
                ``channel``, ``playlist``, or ``movie``. Omit for every kind.
            duration: Restrict video results to a duration band —
                ``under_4_min``, ``4_to_20_min``, or ``over_20_min``.
            features: Features every result must carry, such as ``hd`` or
                ``subtitles``; :class:`~tapline.youtube.Feature` lists all
                eleven. Sent as one repeated query parameter per feature.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.SearchResponse`. A search that matched
            nothing returns an empty ``results``, not an error.

        Raises:
            UnprocessableEntityError: ``query``, ``limit``, or ``country`` is
                outside the range the server accepts.
        """
        return self._send(
            _search(
                query=query,
                limit=limit,
                country=country,
                sort=sort,
                upload_date=upload_date,
                search_type=search_type,
                duration=duration,
                features=features,
            ),
            timeout=timeout,
        )

    def channel(
        self,
        channel_id: str,
        *,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> ChannelResponse:
        """Get a channel's public profile and statistics. Costs 3 credits.

        Args:
            channel_id: Channel ID (``UC…``), ``@handle``, or a channel URL
                using ``/channel/``, ``/@``, ``/c/``, or ``/user/``. A URL may
                not carry a content tab or a query string.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.ChannelResponse`: display name, handle,
            description, subscriber count, avatars, and playlist count.

        Raises:
            NotFoundError: No such channel.
            UnprocessableEntityError: ``channel_id`` is not a channel ID,
                handle, or supported URL.
        """
        return self._send(_channel(channel_id), timeout=timeout)

    def channel_videos(
        self,
        channel_id: str,
        *,
        limit: int = 30,
        content_type: ChannelContentTypeParam = ChannelContentType.VIDEOS,
        cursor: str = "",
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> ChannelVideosResponse:
        """List a channel's uploads, one cursor page at a time. Costs 2 credits.

        Args:
            channel_id: Channel ID (``UC…``), ``@handle``, or channel URL, as
                for :meth:`channel`. Use the same reference for every page.
            limit: Maximum items to return from this page (1–30). The cursor
                still advances by YouTube's full page.
            content_type: Which tab to list — ``videos``, ``shorts``, or
                ``streams``. Ignored when ``cursor`` is set, because the cursor
                carries the walk's tab.
            cursor: ``pagination.next_cursor`` from the previous page. Leave
                empty for the first page.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.ChannelVideosResponse`, one page of a
            walk. Pass its ``pagination.next_cursor`` back as ``cursor`` until
            that comes back ``None``, or hand the whole walk to :meth:`pages`.
            The last page's ``pagination.completion`` says whether the channel
            ran out (``exhausted``) or the cursor outgrew its 8,000-character
            cap (``depth_limit``).

        Raises:
            NotFoundError: No such channel.
            InvalidCursorError: ``cursor`` is malformed, expired, or belongs to
                another channel.
            UnprocessableEntityError: ``channel_id`` is not a channel ID,
                handle, or supported URL.
        """
        return self._send(
            _channel_videos(
                channel_id,
                limit=limit,
                content_type=content_type,
                cursor=cursor,
            ),
            timeout=timeout,
        )

    def playlist(
        self,
        playlist_id: str,
        *,
        limit: int = 50,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> PlaylistResponse:
        """Get a public playlist and its videos. Costs 2 credits.

        Args:
            playlist_id: Playlist ID, 2–150 characters of ``A-Z``, ``a-z``,
                ``0-9``, ``_``, and ``-``.
            limit: Maximum entries to return (1–100). ``total_count`` reports
                how many the playlist actually holds.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.PlaylistResponse`, with the videos in
            ``entries``.

        Raises:
            NotFoundError: No such playlist.
            PermissionDeniedError: The playlist is private.
            UnprocessableEntityError: ``playlist_id`` is malformed.
        """
        return self._send(_playlist(playlist_id, limit=limit), timeout=timeout)

    def metadata(
        self,
        video_id: str,
        *,
        fields: str | Sequence[str] | None = None,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> VideoMetadataResponse:
        """Get public metadata for a video. Costs 2 credits.

        Args:
            video_id: Eleven-character video ID, or a ``watch?v=``,
                ``youtu.be/``, ``shorts/``, ``embed/``, or ``live/`` URL.
            fields: Projection of the record to return, named by the fields of
                :class:`~tapline.youtube.VideoMetadataResponse` — either a
                sequence of names or an already comma-joined string.
                ``video_id`` always comes back. Omit for the whole record.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.VideoMetadataResponse`. Under a projection
            the unselected keys are absent rather than null, so use
            ``model_fields_set`` to tell them from fields the server sent as
            ``None``.

        Raises:
            NotFoundError: No such video, or it has been removed.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
            UnprocessableEntityError: ``fields`` names a key that is not part
                of the metadata record, or ``video_id`` is not an ID or a
                supported URL.
        """
        return self._send(_metadata(video_id, fields=fields), timeout=timeout)

    def subtitles(
        self,
        video_id: str,
        *,
        language: str = "en",
        subtitle_format: SubtitleFormatParam = SubtitleFormat.SRT,
        source: SubtitleSourceParam = SubtitleSource.ANY,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> SubtitleResponse:
        """Get a video's subtitles as a transcript document. Costs 2 credits.

        Args:
            video_id: Video ID or supported video URL, as for :meth:`metadata`.
            language: Language tag of the track, such as ``"en"``, ``"pt-BR"``,
                ``"es-419"``, or ``"zh-Hans"``. ``"orig"`` asks for the video's
                original audio language, and a ``-orig`` suffix (``"en-orig"``)
                for that language's untranslated track. Call
                :meth:`subtitle_tracks` for the tags a video actually has.
            subtitle_format: Document format — ``srt``, ``vtt``, ``json3``,
                ``ttml``, or ``txt`` for the cue text alone, one line per cue.
            source: Which track to serve — ``manual`` (human-authored),
                ``auto`` (machine-generated), or ``any``, which prefers manual
                and falls back to auto.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.SubtitleResponse` whose ``transcript`` is
            a :class:`~tapline.youtube.Json3Transcript` for ``json3`` and a
            ``str`` for every other format.

        Raises:
            NotFoundError: The video has no track matching ``language``,
                ``source``, and ``subtitle_format``.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
            UnprocessableEntityError: ``language`` is not a registered
                language tag.
        """
        return self._send(
            _subtitles(
                video_id,
                language=language,
                subtitle_format=subtitle_format,
                source=source,
            ),
            timeout=timeout,
        )

    def subtitle_tracks(
        self,
        video_id: str,
        *,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> SubtitleTracksResponse:
        """List the subtitle tracks a video has. Costs 2 credits.

        Args:
            video_id: Video ID or supported video URL, as for :meth:`metadata`.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.SubtitleTracksResponse`, splitting the
            tracks into ``manual`` and ``auto``. Each track's ``language`` and
            ``formats`` feed straight into :meth:`subtitles`.

        Raises:
            NotFoundError: No such video, or it has been removed.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
        """
        return self._send(_subtitle_tracks(video_id), timeout=timeout)

    def comments(
        self,
        video_id: str,
        *,
        sort: CommentSortOrderParam = CommentSortOrder.TOP,
        limit: int = 20,
        cursor: str = "",
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> CommentsResponse:
        """Get a video's comment threads, one cursor page at a time. Costs 2 credits.

        Args:
            video_id: Video ID or supported video URL, as for :meth:`metadata`.
            sort: Comment order — ``top`` or ``new``. Pinned threads surface
                first either way. Ignored when ``cursor`` is set, because the
                cursor carries the walk's sort.
            limit: Maximum threads to return from this page (1–20). The cursor
                still advances by YouTube's full 20-thread page.
            cursor: ``pagination.next_cursor`` from the previous page. Leave
                empty for the first page.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.CommentsResponse`, one page of a walk.
            Pass its ``pagination.next_cursor`` back as ``cursor`` until that
            comes back ``None``, or hand the whole walk to :meth:`pages`;
            sorting by ``top`` stops at roughly 1,200 comments with
            ``completion="depth_limit"``. Each thread carries a
            ``replies_cursor`` for :meth:`comment_replies`.

        Raises:
            NotFoundError: No such video, or it has been removed.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
            InvalidCursorError: ``cursor`` is malformed, expired, or belongs to
                another video.
        """
        return self._send(
            _comments(video_id, sort=sort, limit=limit, cursor=cursor),
            timeout=timeout,
        )

    def comment_replies(
        self,
        video_id: str,
        comment_id: str,
        *,
        cursor: str,
        limit: int = 20,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> RepliesResponse:
        """Get replies to a comment, one cursor page at a time. Costs 2 credits.

        Args:
            video_id: Video ID or supported video URL, as for :meth:`metadata`.
            comment_id: Top-level comment ID, 5–150 characters of ``A-Z``,
                ``a-z``, ``0-9``, ``_``, ``.``, and ``-``.
            cursor: Required. The ``replies_cursor`` of a
                :class:`~tapline.youtube.CommentThread` for the first page, then
                ``pagination.next_cursor`` for each page after it. There is no
                replies endpoint without a cursor: a comment with no replies
                has ``replies_cursor=None``.
            limit: Maximum replies to return from this page (1–20). The cursor
                still advances by YouTube's full reply page, currently ten.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.RepliesResponse`, one page of a walk.
            Pass its ``pagination.next_cursor`` back as ``cursor`` until that
            comes back ``None``, or hand the whole walk to :meth:`pages`,
            starting it from ``replies_cursor``.

        Raises:
            InvalidCursorError: ``cursor`` is malformed, expired, or belongs to
                another video or comment.
            NotFoundError: No such video, or it has been removed.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
        """
        return self._send(
            _comment_replies(video_id, comment_id, cursor=cursor, limit=limit),
            timeout=timeout,
        )

    def formats(
        self,
        video_id: str,
        *,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> FormatsResponse:
        """List the streams YouTube offers for a video. Costs 2 credits.

        Args:
            video_id: Video ID or supported video URL, as for :meth:`metadata`.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.FormatsResponse`, storyboard formats
            excluded. Each ``url`` is signed by YouTube and expires in hours.

        Raises:
            NotFoundError: No such video, or it has been removed.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
        """
        return self._send(_formats(video_id), timeout=timeout)

    def heatmap(
        self,
        video_id: str,
        *,
        timeout: float | Timeout | NotGiven | None = not_given,
    ) -> HeatmapResponse:
        """Get the replay heatmap for a video. Costs 2 credits.

        Args:
            video_id: Video ID or supported video URL, as for :meth:`metadata`.
            timeout: Overrides the client's timeout for this request.

        Returns:
            A :class:`~tapline.youtube.HeatmapResponse`. ``heatmap`` scores
            equal slices of the timeline — a hundred of them — by replay
            intensity, and is ``None`` for the many videos YouTube publishes
            no heatmap for, which is not an error.

        Raises:
            NotFoundError: No such video, or it has been removed.
            PermissionDeniedError: The video is private, age-gated,
                members-only, or blocked in the server's region.
        """
        return self._send(_heatmap(video_id), timeout=timeout)
