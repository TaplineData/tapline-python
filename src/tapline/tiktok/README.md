# TikTok with the Tapline Python SDK

Use the TikTok client to read public profiles, videos, comments, followers, sounds, hashtags, collections, captions, search suggestions, and regional trending feeds. No TikTok account is needed.

[Package guide](../../../README.md) · [TikTok API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=tiktok_readme#/tiktok)

## Get started

```sh
pip install tapline
export TAPLINE_API_KEY="your-api-key"
```

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    profile = tapline.tiktok.get_profile(handle="stoolpresidente")
    print(profile.user.uniqueId, profile.statsV2.followerCount)
```

## Common calls

```python
post = "https://www.tiktok.com/@stoolpresidente/video/7517114944362499342"

with SyncTaplineClient() as tapline:
    video = tapline.tiktok.get_video(url=post)
    comments = tapline.tiktok.get_comments(url=post)
    transcript = tapline.tiktok.get_transcript(url=post, language="en")
    trending = tapline.tiktok.get_trending_feed(region="US")

print(video.root.aweme_detail.statistics.play_count)
```

Methods whose response can be full or trimmed return a Pydantic root model; read the selected body through `.root`. Pass `trim=True` for the smaller Scrape Creators-compatible provider-data branch. Tapline omits Scrape Creators' top-level status and credit metadata. Use each response's `cursor`, `max_cursor`, or `min_time` in the next call while `has_more` is true.

Every method costs one credit. Missing or private targets raise typed 404 or 403 errors and are charged; invalid input is rejected before charging; temporary upstream failures raise a 503 error and are refunded. A transcript can return 404 when TikTok has no captions for that video.
