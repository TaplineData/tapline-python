# Instagram with the Tapline Python SDK

Use the Instagram client to read public profiles, posts, reels, comments, highlights, audio pages, popular topics, profile embeds, and exact post counts. Profiles, posts and `pagination` have the same shape on every route that returns them. Ids are strings, timestamps are ISO 8601, and durations are in seconds.

[Package guide](../../../README.md) · [Instagram API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=instagram_readme#/instagram)

## Get started

```sh
pip install tapline
export TAPLINE_API_KEY="your-api-key"
```

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    profile = tapline.instagram.get_profile(handle="nike").profile

print(profile.handle, profile.follower_count)
```

Both `SyncTaplineClient` and the async `TaplineClient` read `TAPLINE_API_KEY`. You can also pass `api_key=` explicitly.

## Endpoints

| Method | Main inputs | Credits |
| --- | --- | --- |
| `get_profile` | `handle` | 3 |
| `get_basic_profile` | `user_id` | 1 |
| `get_post_count` | `handle` | 1 |
| `get_post` | `url`, `region`, `include_play_count` | 1 |
| `get_post_comments` | `url`, `cursor` | 1 |
| `get_user_posts` | `handle`, `next_max_id` | 3 |
| `get_user_reels` | `handle` or `user_id`, `max_id` | 2 |
| `get_highlights` | `handle` or `user_id` | 1 |
| `get_highlight_detail` | `id` | 1 |
| `get_audio_reels` | `audio_id`, `cursor` | 1 |
| `search_popular` | `query`, `cursor` | 3 |
| `get_embed` | `handle` | 1 |

`get_basic_profile` takes `user_id` and sends it as the `userId` query parameter the endpoint expects.

`get_profile` also returns the first page of recent posts, and `recent_posts_status` says whether that timeline is available, private, or unavailable. `get_profile`, `get_post`, `get_user_posts` and `get_user_reels` accept `trim`, which removes nothing.

## Read a post and comments

```python
url = "https://www.instagram.com/reel/Dd9Etk7R91I/"

with SyncTaplineClient() as tapline:
    post = tapline.instagram.get_post(url=url).post
    comments = tapline.instagram.get_post_comments(url=url).comments

print(post.shortcode, post.taken_at, post.metrics.like_count)
for comment in comments:
    print(comment.created_at, comment.text)
```

`include_play_count=False` skips the extra lookup that fills a video's play count. `region` selects a two-letter exit country and defaults to the US. `download_media` accepts only `False`. Tapline returns Instagram's media URLs and does not re-host files.

## Paginate posts and reels

```python
with SyncTaplineClient() as tapline:
    first = tapline.instagram.get_user_posts(handle="nike")
    if first.pagination.has_more:
        second = tapline.instagram.get_user_posts(
            handle="nike",
            next_max_id=first.pagination.next_cursor,
        )
        print(len(second.posts))

    reels = tapline.instagram.get_user_reels(handle="nike")
    if reels.pagination.has_more:
        tapline.instagram.get_user_reels(
            handle="nike",
            max_id=reels.pagination.next_cursor,
        )
```

Pass `pagination.next_cursor` as `next_max_id` to `get_user_posts`, as `max_id` to `get_user_reels`, and as `cursor` to `get_post_comments`, `get_audio_reels` and `search_popular`. The `recent_posts.pagination.next_cursor` from `get_profile` also works as `next_max_id`. Pass the cursor back unchanged. Invalid cursors fail before charging.

## Availability and errors

Upstream failures return 503 without charging. Invalid input returns 400 or 422 before a fetch; missing public resources return 404.

See the [package guide](../../../README.md#handle-errors) for typed exceptions.
