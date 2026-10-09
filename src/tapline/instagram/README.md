# Instagram with the Tapline Python SDK

Use the Instagram client to read public profiles, posts, reels, comments, highlights, audio pages, popular topics, profile embeds, and exact post counts. Responses follow Scrape Creators' Instagram contracts so an existing integration can migrate by changing its client and base URL.

[Package guide](../../../README.md) · [Instagram API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=instagram_readme#/instagram)

## Get started

```sh
pip install tapline
export TAPLINE_API_KEY="your-api-key"
```

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    profile = tapline.instagram.get_profile(handle="nike")

print(profile.data.user.username, profile.data.user.edge_followed_by.count)
```

Both `SyncTaplineClient` and the async `TaplineClient` read `TAPLINE_API_KEY`. You can also pass `api_key=` explicitly.

## Endpoints

| Method | Main inputs | Credits |
| --- | --- | --- |
| `get_profile` | `handle`, `trim` | 1 |
| `get_basic_profile` | `user_id` | 1 |
| `get_post_count` | `handle` | 1 |
| `get_post` | `url`, `region`, `include_play_count`, `trim` | 2 |
| `get_post_comments` | `url`, `cursor` | 1 |
| `get_user_posts` | `handle`, `next_max_id`, `trim` | 1 |
| `get_user_reels` | `handle` or `user_id`, `max_id`, `trim` | 1 |
| `get_highlights` | `handle` or `user_id` | 1 |
| `get_highlight_detail` | `id` | 1 |
| `get_audio_reels` | `audio_id`, `cursor` | 1 |
| `search_popular` | `query`, `cursor` | 2 |
| `get_embed` | `handle` | 1 |

The Python SDK uses `user_id`; it sends Scrape Creators' `userId` wire name where that endpoint requires it.

## Read a post and comments

```python
url = "https://www.instagram.com/reel/Dd9Etk7R91I/"

with SyncTaplineClient() as tapline:
    post = tapline.instagram.get_post(url=url)
    comments = tapline.instagram.get_post_comments(url=url)

print(post.data.xdt_shortcode_media.shortcode)
for comment in comments.comments:
    print(comment.user.username, comment.text)
```

`include_play_count=False` skips the extra lookup used to enrich video posts. `region` selects a two-letter exit country and defaults to the US. `download_media` accepts only `False`; Tapline returns Instagram's media URLs and does not re-host files.

## Paginate posts and reels

```python
with SyncTaplineClient() as tapline:
    first = tapline.instagram.get_user_posts(handle="nike")
    if first.next_max_id:
        second = tapline.instagram.get_user_posts(
            handle="nike",
            next_max_id=first.next_max_id,
        )
        print(len(second.items))

    reels = tapline.instagram.get_user_reels(handle="nike")
    if reels.paging_info and reels.paging_info.max_id:
        tapline.instagram.get_user_reels(
            handle="nike",
            max_id=reels.paging_info.max_id,
        )
```

Pass the returned cursor back unchanged. Invalid cursors fail before charging.

## Availability and errors

Upstream failures return 503 without charging. Invalid input returns 400 or 422 before a fetch; missing public resources return 404.

Tapline omits Scrape Creators' top-level success and credit metadata. See the [package guide](../../../README.md#handle-errors) for typed exceptions.
