"""What the response models accept, reject, and preserve.

The payloads below are hand-written to state one shape each — a nullable field
left null, an unknown enum value, a projected metadata record. Real captured
responses are replayed separately, in ``test_fixture_payloads``.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from conftest import extras
from tapline import CursorCompletion, CursorPagination
from tapline.youtube import (
    ChannelResponse,
    ChannelVideosResponse,
    CommentsResponse,
    Ext,
    FormatItem,
    FormatsResponse,
    HeatmapResponse,
    Json3Transcript,
    LiveStatus,
    PlaylistResponse,
    Protocol,
    RepliesResponse,
    SearchResponse,
    SearchResultType,
    SubtitleFormat,
    SubtitleResponse,
    SubtitleTracksResponse,
    VideoMetadataResponse,
)

VIDEO_ID = "dQw4w9WgXcQ"
CHANNEL_ID = "UCuAXFkgsw1L7xaCfnd5JJOw"
THUMBNAIL = {"url": f"https://i.ytimg.com/vi/{VIDEO_ID}/hqdefault.jpg", "width": 480, "height": 360}

SEARCH_RESULT = {
    "result_type": "video",
    "id": VIDEO_ID,
    "title": "Rick Astley - Never Gonna Give You Up",
    "url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
    "duration": 212,
    "view_count": 1_600_000_000,
    "channel": "Rick Astley",
    "channel_id": CHANNEL_ID,
    "channel_url": f"https://www.youtube.com/channel/{CHANNEL_ID}",
    "thumbnail": THUMBNAIL["url"],
    "thumbnails": [THUMBNAIL],
    "description": None,
    "live_status": "not_live",
    "channel_is_verified": True,
}

SEARCH = {"query": "rick astley", "returned_count": 1, "results": [SEARCH_RESULT]}

CHANNEL = {
    "channel_id": CHANNEL_ID,
    "channel": "Rick Astley",
    "channel_url": f"https://www.youtube.com/channel/{CHANNEL_ID}",
    "handle": "@RickAstleyYT",
    "handle_url": "https://www.youtube.com/@RickAstleyYT",
    "description": "Official YouTube channel.",
    "channel_follower_count": 4_600_000,
    "tags": ["music"],
    "thumbnail": THUMBNAIL["url"],
    "thumbnails": [THUMBNAIL],
    "playlist_count": 12,
}

CHANNEL_VIDEOS = {
    "channel_id": CHANNEL_ID,
    "returned_count": 1,
    "videos": [
        {
            "video_id": VIDEO_ID,
            "title": "A short",
            "url": f"https://www.youtube.com/shorts/{VIDEO_ID}",
            "view_count": 1000,
            "channel": "Rick Astley",
            "channel_id": CHANNEL_ID,
            "channel_url": f"https://www.youtube.com/channel/{CHANNEL_ID}",
            "thumbnail": THUMBNAIL["url"],
            "thumbnails": [THUMBNAIL],
            "live_status": None,
            "channel_is_verified": None,
        }
    ],
    "pagination": {"next_cursor": "4qmFsgKPARIY", "completion": None},
}

PLAYLIST = {
    "playlist_id": "PLbpi6ZahtOH6Blw3RGYpWkSByi_T7Rygb",
    "title": "Greatest Hits",
    "description": None,
    "channel": "Rick Astley",
    "channel_id": CHANNEL_ID,
    "channel_url": f"https://www.youtube.com/channel/{CHANNEL_ID}",
    "handle": "@RickAstleyYT",
    "handle_url": "https://www.youtube.com/@RickAstleyYT",
    "thumbnail": THUMBNAIL["url"],
    "thumbnails": [THUMBNAIL],
    "view_count": 99,
    "modified_date": "2024-11-02",
    "total_count": 40,
    "webpage_url": "https://www.youtube.com/playlist?list=PLbpi6ZahtOH6Blw3RGYpWkSByi_T7Rygb",
    "returned_count": 0,
    "entries": [],
}

METADATA = {
    "video_id": VIDEO_ID,
    "title": "Rick Astley - Never Gonna Give You Up",
    "duration": 212,
    "duration_string": "3:32",
    "upload_date": "2009-10-25",
    "view_count": 1_600_000_000,
    "like_count": 18_000_000,
    "thumbnails": [THUMBNAIL],
    "tags": ["rick astley"],
    "live_status": "not_live",
    "availability": "public",
    "media_type": "video",
    "chapters": [{"start_time": 0.0, "end_time": 42.5, "title": "Intro"}],
    "heatmap": [{"start_time": 0.0, "end_time": 2.12, "value": 1.0}],
}

SUBTITLE_TRACKS = {
    "video_id": VIDEO_ID,
    "manual_count": 1,
    "auto_count": 1,
    "manual": [
        {
            "language": "en",
            "language_name": "English",
            "formats": ["srt", "vtt", "json3", "ttml", "txt"],
        }
    ],
    "auto": [{"language": "pt-BR", "language_name": None, "formats": ["srt", "txt"]}],
}

SUBTITLE_METADATA = {
    "video_id": VIDEO_ID,
    "title": "Rick Astley - Never Gonna Give You Up",
    "channel": "Rick Astley",
    "channel_id": CHANNEL_ID,
    "duration": 212,
}

SUBTITLES = {
    "transcript": "1\n00:00:01,040 --> 00:00:03,040\nWe're no strangers\n",
    "is_auto_generated": True,
    "metadata": SUBTITLE_METADATA,
}

JSON3_TRANSCRIPT = {
    "wireMagic": "pb3",
    "pens": [{"bO": 0}],
    "wsWinStyles": [{"mhModeHint": 2}],
    "wpWinPositions": [{"apPoint": 6}],
    "events": [
        {
            "tStartMs": 1040,
            "dDurationMs": 2000,
            "wWinId": 1,
            "segs": [{"utf8": "We're no strangers", "tOffsetMs": 0, "acAsrConf": 255}],
        }
    ],
}

COMMENTS = {
    "video_id": VIDEO_ID,
    "returned_count": 1,
    "threads": [
        {
            "comment": {
                "comment_id": "UgxKREWxIgDrw8w2e_Z4AaABAg",
                "text": "Never gonna give you up",
                "like_count": 4200,
                "dislike_count": None,
                "timestamp": 1_699_000_000,
                "published_at": "3 years ago",
                "is_pinned": False,
                "is_favorited": True,
                "author": "@someone",
                "author_id": CHANNEL_ID,
                "author_thumbnail": THUMBNAIL["url"],
                "author_url": f"https://www.youtube.com/channel/{CHANNEL_ID}",
                "author_is_verified": False,
                "author_is_uploader": False,
                "html": "<b>Never</b> gonna give you up",
            },
            "replies_cursor": "Eg0SC2RRdzR3OVdnWGNR",
        }
    ],
    "pagination": {"next_cursor": None, "completion": "depth_limit"},
}

REPLIES = {
    "video_id": VIDEO_ID,
    "comment_id": "UgxKREWxIgDrw8w2e_Z4AaABAg",
    "returned_count": 0,
    "replies": [],
    "pagination": {"next_cursor": None, "completion": "exhausted"},
}

NULL_FORMAT: dict[str, Any] = {
    "format_id": None,
    "format_note": None,
    "ext": None,
    "protocol": None,
    "acodec": None,
    "vcodec": None,
    "url": None,
    "width": None,
    "height": None,
    "fps": None,
    "audio_ext": None,
    "video_ext": None,
    "vbr": None,
    "abr": None,
    "tbr": None,
    "resolution": None,
    "aspect_ratio": None,
    "filesize": None,
    "filesize_approx": None,
    "asr": None,
    "audio_channels": None,
    "quality": None,
    "has_drm": None,
    "language": None,
    "language_preference": None,
    "preference": None,
    "dynamic_range": None,
    "container": None,
    "source_preference": None,
    "format": None,
}
"""Every key ``FormatItem`` declares, all null, spelled out rather than derived
from the model — a field the model drops has to fail somewhere."""

FORMATS = {
    "video_id": VIDEO_ID,
    "format_count": 2,
    "formats": [
        {
            "format_id": "140",
            "format_note": "medium",
            "ext": "m4a",
            "protocol": "https",
            "acodec": "mp4a.40.2",
            "vcodec": "none",
            "url": "https://rr3---sn-example.googlevideo.com/videoplayback",
            "width": None,
            "height": None,
            "fps": None,
            "audio_ext": "m4a",
            "video_ext": "none",
            "vbr": None,
            "abr": 129.469,
            "tbr": 129.469,
            "resolution": "audio only",
            "aspect_ratio": None,
            "filesize": 3_432_338,
            "filesize_approx": None,
            "asr": 44100,
            "audio_channels": 2,
            "quality": 3,
            "has_drm": False,
            "language": "en",
            "language_preference": 10,
            "preference": None,
            "dynamic_range": None,
            "container": "m4a_dash",
            "source_preference": -1,
            "format": "140 - audio only (medium)",
        },
        NULL_FORMAT,
    ],
}

HEATMAP = {
    "video_id": VIDEO_ID,
    "heatmap": [
        {"start_time": 0.0, "end_time": 2.12, "value": 1.0},
        {"start_time": 2.12, "end_time": 4.24, "value": 0.42},
    ],
}

RESPONSES: dict[str, tuple[type[BaseModel], dict[str, Any]]] = {
    "search": (SearchResponse, SEARCH),
    "channel": (ChannelResponse, CHANNEL),
    "channel_videos": (ChannelVideosResponse, CHANNEL_VIDEOS),
    "playlist": (PlaylistResponse, PLAYLIST),
    "metadata": (VideoMetadataResponse, METADATA),
    "subtitles": (SubtitleResponse, SUBTITLES),
    "subtitle_tracks": (SubtitleTracksResponse, SUBTITLE_TRACKS),
    "comments": (CommentsResponse, COMMENTS),
    "comment_replies": (RepliesResponse, REPLIES),
    "formats": (FormatsResponse, FORMATS),
    "heatmap": (HeatmapResponse, HEATMAP),
}


class TestEveryResponse:
    @pytest.mark.parametrize("endpoint", list(RESPONSES), ids=list(RESPONSES))
    def test_a_representative_payload_survives_a_round_trip(self, endpoint: str) -> None:
        model, payload = RESPONSES[endpoint]

        parsed = model.model_validate(payload)

        assert parsed.model_dump(mode="json", exclude_unset=True) == payload

    @pytest.mark.parametrize("endpoint", list(RESPONSES), ids=list(RESPONSES))
    def test_a_representative_payload_declares_every_field_it_carries(self, endpoint: str) -> None:
        model, payload = RESPONSES[endpoint]

        assert extras(model.model_validate(payload), model.__name__) == []

    def test_search_results_arrive_typed(self) -> None:
        result = SearchResponse.model_validate(SEARCH).results[0]

        assert result.result_type is SearchResultType.VIDEO
        assert result.live_status is LiveStatus.NOT_LIVE
        assert result.duration == 212
        assert result.thumbnails is not None
        assert result.thumbnails[0].width == 480

    def test_a_listing_entry_may_omit_its_duration(self) -> None:
        video = ChannelVideosResponse.model_validate(CHANNEL_VIDEOS).videos[0]

        assert video.duration is None
        assert "duration" not in video.model_fields_set

    def test_pagination_arrives_typed(self) -> None:
        comments = CommentsResponse.model_validate(COMMENTS)

        assert comments.pagination.next_cursor is None
        assert comments.pagination.completion is CursorCompletion.DEPTH_LIMIT
        assert comments.threads[0].replies_cursor == "Eg0SC2RRdzR3OVdnWGNR"

    def test_subtitle_track_formats_arrive_typed(self) -> None:
        tracks = SubtitleTracksResponse.model_validate(SUBTITLE_TRACKS)

        assert tracks.manual[0].formats == list(SubtitleFormat)
        assert tracks.auto[0].formats == [SubtitleFormat.SRT, SubtitleFormat.TXT]

    def test_a_thumbnail_without_a_url_does_not_reject_the_response(self) -> None:
        blank = {"url": None, "width": None, "height": None}

        parsed = ChannelResponse.model_validate({**CHANNEL, "thumbnails": [blank, THUMBNAIL]})

        assert parsed.thumbnails[0].url is None
        assert parsed.thumbnails[1].url == THUMBNAIL["url"]

    def test_a_heatmap_may_be_absent(self) -> None:
        empty = HeatmapResponse.model_validate({"video_id": VIDEO_ID, "heatmap": None})

        assert empty.heatmap is None

    def test_heatmap_slices_arrive_as_floats(self) -> None:
        heatmap = HeatmapResponse.model_validate(HEATMAP).heatmap

        assert heatmap is not None
        assert [slice_.value for slice_ in heatmap] == [1.0, 0.42]
        assert heatmap[1].start_time == heatmap[0].end_time

    def test_every_format_field_may_be_null(self) -> None:
        formats = FormatsResponse.model_validate(FORMATS)

        assert formats.formats[0].ext is Ext.M4A
        assert formats.formats[0].protocol is Protocol.HTTPS
        assert formats.formats[1].format_id is None
        assert formats.formats[1].model_dump() == NULL_FORMAT


class TestSubtitleTranscript:
    def test_an_srt_transcript_stays_a_string(self) -> None:
        response = SubtitleResponse.model_validate(SUBTITLES)

        assert isinstance(response.transcript, str)
        assert response.transcript.startswith("1\n")
        assert response.is_auto_generated is True
        assert response.metadata.duration == 212

    def test_a_json3_transcript_becomes_an_object(self) -> None:
        response = SubtitleResponse.model_validate(
            {
                "transcript": JSON3_TRANSCRIPT,
                "is_auto_generated": True,
                "metadata": SUBTITLE_METADATA,
            }
        )

        assert isinstance(response.transcript, Json3Transcript)
        assert response.transcript.wireMagic == "pb3"
        assert response.transcript.events[0].tStartMs == 1040
        assert response.transcript.events[0].segs[0].utf8 == "We're no strangers"
        assert response.transcript.events[0].segs[0].acAsrConf == 255


class TestUpstreamChange:
    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("ext", "avi"),
            ("protocol", "https+https"),
            ("audio_ext", "opus"),
            ("video_ext", "av01"),
            ("dynamic_range", "HDR27"),
            ("container", "flv_dash"),
        ],
    )
    def test_an_unknown_format_enum_arrives_verbatim(self, field: str, value: str) -> None:
        parsed = FormatItem.model_validate({field: value})

        assert getattr(parsed, field) == value
        assert type(getattr(parsed, field)) is str

    @pytest.mark.parametrize(
        ("field", "value"),
        [("live_status", "is_premiering"), ("availability", "gifted"), ("media_type", "podcast")],
    )
    def test_an_unknown_video_enum_arrives_verbatim(self, field: str, value: str) -> None:
        parsed = VideoMetadataResponse.model_validate({"video_id": VIDEO_ID, field: value})

        assert getattr(parsed, field) == value
        assert type(getattr(parsed, field)) is str

    def test_a_known_value_still_arrives_as_an_enum_member(self) -> None:
        parsed = FormatItem.model_validate({"ext": "mp4", "protocol": "https"})

        assert parsed.ext is Ext.MP4
        assert parsed.protocol is Protocol.HTTPS

    def test_an_unknown_field_is_kept_rather_than_dropped(self) -> None:
        parsed = HeatmapResponse.model_validate({**HEATMAP, "sampling_rate": 100})

        assert parsed.model_extra == {"sampling_rate": 100}
        assert parsed.model_dump()["sampling_rate"] == 100

    def test_a_new_search_result_type_does_not_reject_the_search(self) -> None:
        payload = {**SEARCH, "results": [{**SEARCH_RESULT, "result_type": "podcast"}]}

        result = SearchResponse.model_validate(payload).results[0]

        assert result.result_type == "podcast"
        assert type(result.result_type) is str

    def test_a_new_cursor_completion_does_not_reject_the_page(self) -> None:
        parsed = CursorPagination.model_validate({"next_cursor": None, "completion": "time_limit"})

        assert parsed.completion == "time_limit"
        assert type(parsed.completion) is str

    def test_a_newly_served_subtitle_format_does_not_reject_the_track_list(self) -> None:
        track = {"language": "en", "language_name": None, "formats": ["srt", "srv3"]}

        parsed = SubtitleTracksResponse.model_validate({**SUBTITLE_TRACKS, "auto": [track]})

        assert parsed.auto[0].formats == [SubtitleFormat.SRT, "srv3"]


class TestMetadataProjection:
    def test_a_projected_payload_parses(self) -> None:
        parsed = VideoMetadataResponse.model_validate({"video_id": VIDEO_ID, "title": "A title"})

        assert parsed.video_id == VIDEO_ID
        assert parsed.title == "A title"
        assert parsed.view_count is None
        assert parsed.thumbnails == []

    def test_an_omitted_field_is_distinguishable_from_a_null_one(self) -> None:
        parsed = VideoMetadataResponse.model_validate(
            {"video_id": VIDEO_ID, "title": None, "duration": 212}
        )

        assert parsed.model_fields_set == {"video_id", "title", "duration"}
        assert parsed.model_dump(exclude_unset=True) == {
            "video_id": VIDEO_ID,
            "title": None,
            "duration": 212,
        }

    def test_video_id_is_the_one_field_a_projection_cannot_drop(self) -> None:
        with pytest.raises(ValidationError):
            VideoMetadataResponse.model_validate({"title": "A title"})
