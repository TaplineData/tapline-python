# YouTube with the Tapline Python SDK

Use the YouTube client to get transcripts, search videos, inspect channels and playlists, and collect comments.

[Package guide](../../../README.md) · [YouTube API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=youtube_readme#/youtube)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=youtube_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=youtube_readme).

Install the package and save your key in `TAPLINE_API_KEY`:

```sh
pip install tapline
export TAPLINE_API_KEY="your-api-key"
```

```python
import os

from tapline import SyncTaplineClient

tapline = SyncTaplineClient(api_key=os.environ["TAPLINE_API_KEY"])
```

The async `TaplineClient` accepts the same `api_key=` argument. If you omit it, both clients read `TAPLINE_API_KEY`.

## What you can do

### Discovery and collections

| Method | Key inputs | Returns |
| --- | --- | --- |
| `search` | `query`; optional `limit`, `country`, `sort`, `upload_date`, `search_type`, `duration`, `features` | `SearchResponse` with videos, channels, playlists, and movies |
| `channel` | `channel_id` or supported channel URL | `ChannelResponse` profile, handle, statistics, and content tabs |
| `channel_videos` | `channel_id`; optional `limit`, `content_type`, `cursor` | `ChannelVideosResponse` page and next cursor |
| `playlist` | `playlist_id`; optional `limit` | `PlaylistResponse` details and videos |

### Video data

| Method | Key inputs | Returns |
| --- | --- | --- |
| `metadata` | `video_id`; optional `fields` | `VideoMetadataResponse` with projected metadata |
| `formats` | `video_id` | `FormatsResponse` with available audio/video streams |
| `heatmap` | `video_id` | `HeatmapResponse` with replay-intensity points, or no heatmap |

### Transcripts and comments

| Method | Key inputs | Returns |
| --- | --- | --- |
| `subtitles` | `video_id`; optional `language`, `subtitle_format`, `source` | `SubtitleResponse` in SRT, VTT, JSON3, TTML, or plain text |
| `subtitle_tracks` | `video_id` | `SubtitleTracksResponse` with manual and automatic tracks |
| `comments` | `video_id`; optional `sort`, `limit`, `cursor` | `CommentsResponse` page of top-level threads |
| `comment_replies` | `video_id`, `comment_id`, required `cursor`; optional `limit` | `RepliesResponse` page and next cursor |

Use `pages(...)` to fetch more results from `channel_videos`, `comments`, and `comment_replies`.

## Get a transcript

```python
from tapline import SyncTaplineClient
from tapline.youtube import SubtitleFormat

with SyncTaplineClient() as tapline:
    tracks = tapline.youtube.subtitle_tracks("jNQXAC9IVRw")
    transcript = tapline.youtube.subtitles(
        "jNQXAC9IVRw",
        language="en",
        subtitle_format=SubtitleFormat.TXT,
    )

print([track.language for track in tracks.manual + tracks.auto])
print(transcript.transcript)
```

`source="any"` prefers a manual track and falls back to automatic captions. Plain text is derived from the caption cues; use `srt`, `vtt`, `json3`, or `ttml` when timing or styling matters.

## Search videos and channels

```python
from tapline import SyncTaplineClient
from tapline.youtube import SearchSort

with SyncTaplineClient() as tapline:
    results = tapline.youtube.search(
        query="learn Python",
        limit=5,
        sort=SearchSort.VIEW_COUNT,
    )
    metadata = tapline.youtube.metadata("dQw4w9WgXcQ", fields=["title", "channel", "view_count"])
    channel = tapline.youtube.channel("@Computerphile2")
    videos = tapline.youtube.channel_videos("@Computerphile2", limit=10)

print([item.title for item in results.results])
print(metadata.title, metadata.view_count)
print(channel.channel, channel.channel_follower_count)
print([video.title for video in videos.videos])
```

## Get comments

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    comments = tapline.youtube.comments("dQw4w9WgXcQ", sort="new")
    for thread in comments.threads:
        print(thread.comment.text)
```

To fetch replies, pass a thread's non-null `replies_cursor` together with its `comment_id` to `comment_replies`. Cursors are tied to the original resource and can expire.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). The [YouTube API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=youtube_readme#/youtube) lists the inputs, response fields, limits, and credit cost for each method.
