"""YouTube's json3 caption document.

Field names are YouTube's own keys, verbatim and camel-cased, so a transcript
survives a round trip through ``model_dump()`` and stays readable next to
YouTube's payloads. Everything is optional: json3 omits any key it has nothing
to say about, which is most of them on most cues.
"""

from __future__ import annotations

from pydantic import Field

from .._models import BaseModel

__all__ = ["Json3Event", "Json3Segment", "Json3Transcript"]


class Json3Segment(BaseModel):
    """One run of text within a caption event."""

    utf8: str | None = None
    """The text itself. A lone ``"\\n"`` marks a line break."""

    tOffsetMs: int | None = None
    """Milliseconds after the event's ``tStartMs`` that this run appears."""

    acAsrConf: int | None = None
    """Speech-recognition confidence, 0 to 255. Auto-generated tracks only."""

    isSpeakerChange: int | None = None
    """``1`` where a new speaker takes over, which YouTube also marks with a
    leading ``">>"`` in :attr:`utf8`. Auto-generated tracks only."""


class Json3Event(BaseModel):
    """One caption cue."""

    tStartMs: int | None = None
    """Milliseconds from the start of the video."""

    dDurationMs: int | None = None

    id: int | None = None

    wWinId: int | None = None
    """Window this cue is drawn in."""

    wpWinPosId: int | None = None
    """Index into the transcript's ``wpWinPositions``."""

    wsWinStyleId: int | None = None
    """Index into the transcript's ``wsWinStyles``."""

    aAppend: int | None = None
    """``1`` when this cue appends to the previous one instead of replacing it."""

    segs: list[Json3Segment] = Field(default_factory=list)


class Json3Transcript(BaseModel):
    """A full json3 caption track.

    Returned by ``youtube.subtitles`` when ``subtitle_format`` is
    :attr:`~tapline.youtube.SubtitleFormat.JSON3`.
    """

    wireMagic: str | None = None
    """Format marker, always ``"pb3"`` so far."""

    pens: list[dict[str, object]] = Field(default_factory=list)
    """Text styles, referenced by index from a segment. YouTube documents no
    schema for these blobs and mixes colours in as strings, so the values stay
    untyped rather than rejecting a transcript nobody reads them from."""

    wsWinStyles: list[dict[str, object]] = Field(default_factory=list)

    wpWinPositions: list[dict[str, object]] = Field(default_factory=list)

    events: list[Json3Event] = Field(default_factory=list)
