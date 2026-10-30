# Facebook with the Tapline Python SDK

Use the Facebook client to read public pages and profiles, posts, photos, videos, reels and comments, events and public groups. The Ad Library and Marketplace have their own clients: [Facebook Ad Library](../facebook_ad_library/README.md) and [Facebook Marketplace](../facebook_marketplace/README.md).

[Package guide](../../../README.md) · [Facebook API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=facebook_readme#/facebook)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=facebook_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=facebook_readme).

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

| Method | Inputs | Returns | Credits |
| --- | --- | --- | --- |
| `resolve_url` | `url` | the ids a facebook.com URL points to | 3 |
| `look_up_page` | `username` | the page behind a username | 3 |
| `get_page` | `profile_id` | a page or profile header with its tabs | 3 |
| `get_page_intro` | `profile_id` | the Intro card | 3 |
| `get_page_about` | `profile_id`, `collection_id` | one About section | 5 |
| `list_page_posts` | `profile_id`, `cursor` | 3 posts per page, newest first | 6 |
| `list_page_photos` | `profile_id`, `collection_id`, `cursor` | photos, or albums | 3 |
| `list_page_videos` | `page_id`, `cursor` | 9 videos per page | 3 |
| `list_page_events` | `profile_id`, `collection_id`, `cursor` | upcoming or past events | 3 |
| `list_page_followers` | `profile_id` | the first followers Facebook shows | 3 |
| `list_page_following` | `profile_id`, `collection_id` | the first pages and profiles a page follows | 3 |
| `get_post` | `story_id` | one post with its first comments | 4 |
| `get_photo` | `photo_id` | one photo with its first comments | 4 |
| `get_video` | `video_id` | one video with playable URLs and its first comments | 4 |
| `get_reel` | `reel_id` | one reel | 3 |
| `list_comments` | `feedback_id`, `sort`, `cursor` | comments on a post, photo, video or reel | 3 |
| `list_comment_replies` | `comment_id`, `cursor` | 10 replies per page | 3 |
| `list_hashtag_posts` | `hashtag` | the top posts for a hashtag | 3 |
| `search_videos` | `query`, `cursor` | public videos and reels | 6 |
| `list_live_videos` |  | live videos Facebook Watch features | 3 |
| `search_events` | `query`, `cursor`, `date`, `start_date`, `end_date`, `category_id`, `city_id` | public events | 3 |
| `list_city_events` | `city_id`, `cursor` | 12 suggested events per page in a city | 3 |
| `get_event` | `event_id` | an event's header card | 3 |
| `get_event_about` | `event_id` | an event's About section | 3 |
| `get_group` | `group_id` | a public group's header | 3 |
| `get_group_about` | `group_id` | a public group's About tab | 3 |
| `list_group_posts` | `group_id`, `sort`, `cursor` | 3 posts per page | 5 |
| `list_group_photos` | `group_id`, `cursor` | 8 photos per page | 3 |
| `list_group_events` | `group_id` | upcoming and recent past events | 3 |

Paged methods cost their credits per page.

## Turn a URL into ids

```python
resolved = tapline.facebook.resolve_url(url="https://www.facebook.com/NASA")
if resolved.ids.profile_id:
    page = tapline.facebook.get_page(resolved.ids.profile_id)
    print(page.name, page.metrics.follower_count_approx)
    for tab in page.tabs or []:
        print(tab.tab_key, [c.collection_id for c in tab.collections])
```

Pages have two ids. `profile_id` is what the `/pages/{profile_id}` methods take; `page_id` is the id `list_page_videos` and the [Ad Library client](../facebook_ad_library/README.md) take, and `get_page` returns both. A tab's `collection_id` picks an About section, the albums view of photos or the past events.

## Page through posts and comments

```python
cursor = ""
while True:
    posts = tapline.facebook.list_page_posts("100044561550831", cursor=cursor)
    for post in posts.posts:
        print(post.created_at, post.text)
    if posts.pagination.next_cursor is None:
        break
    cursor = posts.pagination.next_cursor

latest = tapline.facebook.list_page_posts("100044561550831")
first = latest.posts[0]
if first.feedback_id:
    comments = tapline.facebook.list_comments(feedback_id=first.feedback_id)
    for comment in comments.comments:
        if comment.id and comment.replies_cursor:
            replies = tapline.facebook.list_comment_replies(
                comment.id, cursor=comment.replies_cursor
            )
            print(comment.text, len(replies.replies))
```

A cursor works only with the method and inputs that issued it.

## Read the response

- Facebook's enum values arrive as `{code, label}`: `code` is Facebook's value and `label` says what it means.
- `get_page` returns a `FacebookPage`. `look_up_page` and the Ad Library's ad cards, advertisers, advertiser suggestions and report rows wrap one in `.page`. Fields only some of them fill, such as `tabs`, are optional.
- `list_page_followers`, `list_page_following` and `list_hashtag_posts` return only the first page Facebook shows; there is no cursor.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). Validation errors are not charged: `date` with a date range, or a cursor from another method or other inputs. An id Facebook has no public page for answers 404 and is charged. When Facebook refuses every proxy attempt the call answers 503 and is not charged.

The [Facebook API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=facebook_readme#/facebook) lists the inputs, response fields, and credit cost for each method.
