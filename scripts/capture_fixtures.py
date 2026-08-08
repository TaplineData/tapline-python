"""Capture real API payloads into ``tests/fixtures/youtube`` and index them.

Tapline's demo endpoints run the same interactor and return the same response
types as the authenticated ones, so they pin the models against production
without an API key or credits. They are capped at five requests per IP per
endpoint per day, so a fixture already captured from the API is never
refetched::

    uv run python scripts/capture_fixtures.py            # everything missing
    uv run python scripts/capture_fixtures.py formats    # one fixture

Requests go out through plain httpx. A fixture parsed by the models it exists
to test would prove nothing.

Targets are chosen for the awkward cases, not for tidiness: a video with
chapters and one with a heatmap (YouTube's player bar carries one or the
other, never both), a channel by ``UC…`` ID and one by ``@handle``, a shorts
tab that omits ``duration`` outright, an auto-generated transcript, which
carries per-segment keys a manual one never does, a projected metadata record,
and searches filtered down to each result type.

``manifest.json`` records where every fixture in the directory came from.
Fixtures it attributes to something other than this script — ``comment_replies``
has no demo route at all — are left alone.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import httpx

BASE_URL = "https://api.tapline.sh"
DEMO_PREFIX = "/api/v1/youtube/demo"
FIXTURE_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "youtube"
MANIFEST = FIXTURE_DIR / "manifest.json"

# YouTube is proxied live, and a cold channel walk can take most of a minute.
TIMEOUT = httpx.Timeout(180.0, connect=15.0)

CHAPTERED_VIDEO = "wt4p2oalmRY"
"""Veritasium: ten chapters, a manual English track, thousands of comments."""

DIARIZED_VIDEO = "bo4ebVkhp28"
"""Two speakers in 55 seconds, so its auto transcript marks speaker changes."""

SHORT_VIDEO = "jNQXAC9IVRw"
"""The first YouTube video: 19 seconds, so its json3 transcript stays legible."""

REPLAYED_VIDEO = "dQw4w9WgXcQ"
"""Watched enough to have a heatmap, which most videos do not."""

HDR_VIDEO = "LXb3EKWsInQ"
"""HDR10 alongside SDR, and every container and audio extension in one call."""

VERITASIUM_ID = "UCHnyfMqiRRG1u-2MsSQLbXA"
VERITASIUM_UPLOADS = "UUHnyfMqiRRG1u-2MsSQLbXA"
MKBHD_ID = "UCBJycsmduvYEL83R_U4JriQ"

ParamValue = str | int | Sequence[str]


@dataclass(frozen=True)
class Capture:
    """One fixture: where it comes from and what it has to validate into.

    Attributes:
        name: Fixture file stem under ``tests/fixtures/youtube``.
        method: The ``tapline.youtube`` method that returns this shape.
        model: Class in :mod:`tapline.youtube` the payload must parse into.
        template: Demo path below :data:`DEMO_PREFIX`, with ``{}`` placeholders.
        segments: Path segment values, percent-encoded before substitution.
        params: Query parameters; a sequence repeats its key.
    """

    name: str
    method: str
    model: str
    template: str
    segments: Mapping[str, str] = field(default_factory=dict)
    params: Mapping[str, ParamValue] = field(default_factory=dict)

    @property
    def path(self) -> str:
        encoded = {name: quote(value, safe="") for name, value in self.segments.items()}
        return DEMO_PREFIX + self.template.format(**encoded)


# Ordered so every endpoint's first fixture is attempted before any endpoint's
# second: the daily cap is per endpoint, so breadth survives a partial run.
CAPTURES: tuple[Capture, ...] = (
    Capture(
        name="search",
        method="search",
        model="SearchResponse",
        template="/search",
        params={"query": "veritasium", "limit": 8},
    ),
    Capture(
        name="channel_by_id",
        method="channel",
        model="ChannelResponse",
        template="/channels/{channel_id}",
        segments={"channel_id": VERITASIUM_ID},
    ),
    Capture(
        name="channel_videos",
        method="channel_videos",
        model="ChannelVideosResponse",
        template="/channels/{channel_id}/videos",
        segments={"channel_id": "@veritasium"},
        params={"limit": 5},
    ),
    Capture(
        name="playlist",
        method="playlist",
        model="PlaylistResponse",
        template="/playlist/{playlist_id}",
        segments={"playlist_id": VERITASIUM_UPLOADS},
        params={"limit": 5},
    ),
    Capture(
        name="metadata",
        method="metadata",
        model="VideoMetadataResponse",
        template="/videos/{video_id}/metadata",
        segments={"video_id": CHAPTERED_VIDEO},
    ),
    Capture(
        name="subtitle_tracks",
        method="subtitle_tracks",
        model="SubtitleTracksResponse",
        template="/videos/{video_id}/subtitles/tracks",
        segments={"video_id": CHAPTERED_VIDEO},
    ),
    Capture(
        name="subtitles_srt",
        method="subtitles",
        model="SubtitleResponse",
        template="/videos/{video_id}/subtitles",
        segments={"video_id": CHAPTERED_VIDEO},
        params={"language": "en", "subtitle_format": "srt", "source": "manual"},
    ),
    Capture(
        name="comments",
        method="comments",
        model="CommentsResponse",
        template="/videos/{video_id}/comments",
        segments={"video_id": CHAPTERED_VIDEO},
        params={"sort": "top", "limit": 10},
    ),
    Capture(
        name="formats",
        method="formats",
        model="FormatsResponse",
        template="/videos/{video_id}/formats",
        segments={"video_id": HDR_VIDEO},
    ),
    Capture(
        name="heatmap",
        method="heatmap",
        model="HeatmapResponse",
        template="/videos/{video_id}/heatmap",
        segments={"video_id": REPLAYED_VIDEO},
    ),
    Capture(
        name="search_filtered",
        method="search",
        model="SearchResponse",
        template="/search",
        params={
            "query": "drone footage",
            "limit": 5,
            "sort": "view_count",
            "search_type": "video",
            "duration": "over_20_min",
            "features": ("hd", "4k"),
        },
    ),
    Capture(
        name="channel_by_handle",
        method="channel",
        model="ChannelResponse",
        template="/channels/{channel_id}",
        segments={"channel_id": "@mkbhd"},
    ),
    Capture(
        name="channel_videos_shorts",
        method="channel_videos",
        model="ChannelVideosResponse",
        template="/channels/{channel_id}/videos",
        segments={"channel_id": MKBHD_ID},
        params={"content_type": "shorts", "limit": 5},
    ),
    Capture(
        name="subtitles_json3",
        method="subtitles",
        model="SubtitleResponse",
        template="/videos/{video_id}/subtitles",
        segments={"video_id": SHORT_VIDEO},
        params={"language": "en", "subtitle_format": "json3", "source": "manual"},
    ),
    Capture(
        name="metadata_fields",
        method="metadata",
        model="VideoMetadataResponse",
        template="/videos/{video_id}/metadata",
        segments={"video_id": CHAPTERED_VIDEO},
        params={"fields": "title,view_count,chapters"},
    ),
    Capture(
        name="metadata_heatmap",
        method="metadata",
        model="VideoMetadataResponse",
        template="/videos/{video_id}/metadata",
        segments={"video_id": REPLAYED_VIDEO},
    ),
    Capture(
        name="search_movies",
        method="search",
        model="SearchResponse",
        template="/search",
        params={"query": "free movies", "limit": 5, "search_type": "movie"},
    ),
    Capture(
        name="channel_videos_streams",
        method="channel_videos",
        model="ChannelVideosResponse",
        template="/channels/{channel_id}/videos",
        segments={"channel_id": MKBHD_ID},
        params={"content_type": "streams", "limit": 5},
    ),
    Capture(
        name="subtitles_json3_auto",
        method="subtitles",
        model="SubtitleResponse",
        template="/videos/{video_id}/subtitles",
        segments={"video_id": DIARIZED_VIDEO},
        params={"language": "en", "subtitle_format": "json3", "source": "auto"},
    ),
)


def fixture_path(name: str) -> Path:
    return FIXTURE_DIR / f"{name}.json"


def load_manifest() -> dict[str, dict[str, str]]:
    if not MANIFEST.exists():
        return {}
    loaded: dict[str, dict[str, str]] = json.loads(MANIFEST.read_text())
    return loaded


def write_manifest(entries: dict[str, dict[str, str]]) -> None:
    ordered = {name: entries[name] for name in sorted(entries)}
    MANIFEST.write_text(json.dumps(ordered, indent=2) + "\n")


def already_captured(spec: Capture, manifest: Mapping[str, Mapping[str, str]]) -> bool:
    """Whether this fixture is on disk *and* came from the API.

    A fixture recorded against another source is one this script never made,
    so the daily cap has not been spent on it and it is worth spending now.
    """
    entry = manifest.get(spec.name)
    return fixture_path(spec.name).exists() and entry is not None and entry["source"] == BASE_URL


def capture(client: httpx.Client, spec: Capture) -> dict[str, str]:
    """Fetch one payload and write it to disk, returning its manifest entry."""
    response = client.get(spec.path, params=dict(spec.params))
    response.raise_for_status()
    fixture_path(spec.name).write_text(
        json.dumps(response.json(), indent=2, ensure_ascii=False) + "\n"
    )
    return {
        "method": spec.method,
        "model": spec.model,
        "source": BASE_URL,
        "url": str(response.request.url),
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "names",
        nargs="*",
        choices=[spec.name for spec in CAPTURES],
        help="Fixtures to capture. Defaults to every one that is missing.",
    )
    args = parser.parse_args(argv)
    wanted = set(args.names) or {spec.name for spec in CAPTURES}

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    failures: list[str] = []

    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
        for spec in CAPTURES:
            if spec.name not in wanted:
                continue
            if already_captured(spec, manifest):
                print(f"skip     {spec.name} (already captured)")
                continue
            try:
                manifest[spec.name] = capture(client, spec)
            except httpx.HTTPStatusError as err:
                # A 429 is the daily demo cap, not a client defect: report the
                # gap rather than retrying into it.
                failures.append(spec.name)
                status, body = err.response.status_code, err.response.text[:200]
                print(f"FAILED   {spec.name} — HTTP {status} {body}")
            except httpx.HTTPError as err:
                failures.append(spec.name)
                print(f"FAILED   {spec.name} — {type(err).__name__}: {err}")
            else:
                size = fixture_path(spec.name).stat().st_size
                print(f"captured {spec.name} ({size:,} bytes)")

    write_manifest(manifest)
    if failures:
        print(f"\n{len(failures)} of {len(wanted)} failed: {', '.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
