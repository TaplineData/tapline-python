from __future__ import annotations

from .._models import BaseModel
from .response_enums import (
    AudioExtValue,
    ContainerValue,
    DynamicRangeValue,
    ExtValue,
    ProtocolValue,
    VideoExtValue,
)

__all__ = ["FormatItem", "FormatsResponse"]


class FormatItem(BaseModel):
    """One downloadable stream of a video.

    YouTube describes each format with whatever attributes apply to it, so
    every field is optional: a format that carries no video reports no
    ``height``, an adaptive format reports no ``container``, and so on.
    """

    format_id: str | None = None
    """YouTube's identifier for this stream, such as ``"137"``."""

    format_note: str | None = None
    """Quality label, such as ``"1080p"`` or ``"medium"``."""

    ext: ExtValue | None = None

    protocol: ProtocolValue | None = None

    acodec: str | None = None
    """Audio codec, or ``"none"`` for a video-only format."""

    vcodec: str | None = None
    """Video codec, or ``"none"`` for an audio-only format."""

    url: str | None = None
    """Direct media URL. Signed by YouTube and short-lived."""

    width: int | None = None

    height: int | None = None

    fps: float | None = None

    audio_ext: AudioExtValue | None = None

    video_ext: VideoExtValue | None = None

    vbr: float | None = None
    """Video bitrate in kbps."""

    abr: float | None = None
    """Audio bitrate in kbps."""

    tbr: float | None = None
    """Total bitrate in kbps."""

    resolution: str | None = None
    """``"1920x1080"``, or ``"audio only"`` for an audio-only format."""

    aspect_ratio: float | None = None

    filesize: int | None = None
    """Bytes, when YouTube states the exact size."""

    filesize_approx: int | None = None
    """Bytes, estimated from bitrate and duration."""

    asr: int | None = None
    """Audio sample rate in Hz."""

    audio_channels: int | None = None

    quality: int | None = None
    """yt-dlp's relative quality ranking. Higher is better."""

    has_drm: bool | None = None

    language: str | None = None
    """BCP-47 tag of this stream's audio track."""

    language_preference: int | None = None

    preference: int | None = None

    dynamic_range: DynamicRangeValue | None = None

    container: ContainerValue | None = None

    source_preference: int | None = None

    format: str | None = None
    """Human-readable summary combining ``format_id`` and ``format_note``."""


class FormatsResponse(BaseModel):
    """Response of ``youtube.formats``."""

    video_id: str

    format_count: int

    formats: list[FormatItem]
    """Storyboard formats are filtered out server-side."""
