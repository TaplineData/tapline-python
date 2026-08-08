from __future__ import annotations

from .._models import BaseModel
from .json3 import Json3Transcript
from .response_enums import SubtitleFormatValue

__all__ = [
    "SubtitleMetadata",
    "SubtitleResponse",
    "SubtitleTrackItem",
    "SubtitleTracksResponse",
]


class SubtitleTrackItem(BaseModel):
    """One language a video has captions in."""

    language: str
    """BCP-47 tag to pass as ``language`` to ``youtube.subtitles``."""

    language_name: str | None
    """YouTube's own label, such as ``"English (auto-generated)"``."""

    formats: list[SubtitleFormatValue]
    """Formats this track can be served in, to pass as ``subtitle_format`` to
    ``youtube.subtitles``. Always includes ``srt`` and ``txt``, which Tapline
    derives from whatever YouTube publishes."""


class SubtitleTracksResponse(BaseModel):
    """Response of ``youtube.subtitle_tracks``."""

    video_id: str

    manual_count: int

    auto_count: int

    manual: list[SubtitleTrackItem]
    """Human-authored tracks."""

    auto: list[SubtitleTrackItem]
    """Machine-generated tracks."""


class SubtitleMetadata(BaseModel):
    """The bit of video metadata that comes back alongside a transcript."""

    video_id: str

    title: str | None

    channel: str | None

    channel_id: str | None

    duration: int | None
    """Seconds."""


class SubtitleResponse(BaseModel):
    """Response of ``youtube.subtitles``."""

    transcript: str | Json3Transcript
    """The captions, in the ``subtitle_format`` that was requested.

    A :class:`~tapline.youtube.Json3Transcript` when the request asked for
    :attr:`~tapline.youtube.SubtitleFormat.JSON3`, and a ``str`` for every other
    format — ``srt``, ``vtt``, ``ttml`` and ``txt``. Branch on
    ``isinstance(transcript, str)`` to narrow it.
    """

    is_auto_generated: bool
    """Whether the served track was machine-generated."""

    metadata: SubtitleMetadata
