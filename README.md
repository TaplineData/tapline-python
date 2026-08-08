# tapline

[![PyPI](https://img.shields.io/pypi/v/tapline.svg)](https://pypi.org/project/tapline/)
[![Python](https://img.shields.io/pypi/pyversions/tapline.svg)](https://pypi.org/project/tapline/)

Tapline is a Python package for working with public YouTube data. It downloads
transcripts and provides data about videos, channels, searches, comments, and
playlists.

You will need Python 3.10 or newer and a Tapline API key. You can get a key at
[tapline.sh](https://tapline.sh).

## Install

```sh
pip install tapline
```

Set your API key as an environment variable:

```sh
export TAPLINE_API_KEY="your-api-key"
```

The examples below read the key from that variable automatically.

You can also pass the key when you create the client:

```python
from tapline import SyncTaplineClient

tapline = SyncTaplineClient(api_key="your-api-key")
```

## Get a transcript

Use `SyncTaplineClient` for a regular Python script:

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    subtitles = tapline.youtube.subtitles(
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        subtitle_format="txt",
    )

    print(subtitles.transcript)
```

The default language is English. Tapline accepts BCP 47 language tags such as
`en`, `pt-BR`, `es-419`, and `zh-Hans`:

```python
subtitles = tapline.youtube.subtitles(
    "jNQXAC9IVRw",
    language="pt-BR",
    subtitle_format="txt",
)
```

Tapline can also return `srt`, `vtt`, `ttml`, or `json3` transcripts.

## Get every transcript from a channel

The [channel transcript example](./examples/youtube/download_channel_transcripts.py)
walks through the Videos, Shorts, and Live tabs and logs each transcript:

```sh
uv run python examples/youtube/download_channel_transcripts.py @Computerphile2
```

You can pass a channel ID, handle, or URL. The script asks for English captions,
preferring a manual track and falling back to an auto-generated track. If a
video has no matching transcript, it logs a warning and moves to the next one.

## Look up a video

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    video = tapline.youtube.metadata("https://youtu.be/dQw4w9WgXcQ")

    print(video.title)
    print(video.view_count)
    print(video.duration)
```

## Search YouTube

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    results = tapline.youtube.search(
        query="learn python",
        limit=5,
    )

    for result in results.results:
        print(result.title)
```

Searches can be narrowed by upload date, duration, result type, country, and
features such as subtitles or 4K video. See the
[Tapline docs](https://tapline.sh/docs) for the available filters.

## Get every comment and reply

The [comments example](./examples/youtube/download_video_comments.py) walks
through all available comment pages and logs each comment and reply:

```sh
uv run python examples/youtube/download_video_comments.py "VIDEO_ID_OR_URL"
```

If comments or replies become unavailable during the walk, the script logs a
warning and stops with the comments it already fetched.

## List subtitle languages

If you do not know which languages a video has, check its subtitle tracks:

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    tracks = tapline.youtube.subtitle_tracks("jNQXAC9IVRw")

    for track in tracks.manual + tracks.auto:
        print(track.language, track.language_name)
```

## Use the async client

For an async application, use `TaplineClient` and `await`:

```python
import asyncio

from tapline import TaplineClient


async def main() -> None:
    async with TaplineClient() as tapline:
        video = await tapline.youtube.metadata("dQw4w9WgXcQ")
        print(video.title)


asyncio.run(main())
```

The sync and async clients have the same YouTube methods.

## IDs, handles, and URLs

You can pass a video ID or a common YouTube video URL wherever a video is
needed:

```python
"dQw4w9WgXcQ"

"https://youtu.be/dQw4w9WgXcQ"
"https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

For channels, you can use a channel ID, handle, or URL:

```python
"UCXuqSBlHAE6Xw-yeJA0Tunw"

"@LinusTechTips"
"https://www.youtube.com/@LinusTechTips"
```

## Other features

The client also supports playlists, stream formats, and YouTube's most-replayed
heatmap. The [Tapline docs](https://tapline.sh/docs) list the available methods
and options.

## License

MIT. See [LICENSE](./LICENSE).
