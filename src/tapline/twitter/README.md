# Twitter (X) with the Tapline Python SDK

Use the Twitter client to read public X data as x.com shows it to logged-out visitors: a profile with its pinned and newest posts, one post with its media, quote, parent and top replies, and an X Community with its top posts. No X account is needed.

[Package guide](../../../README.md) · [Twitter API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=twitter_readme#/twitter)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=twitter_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=twitter_readme).

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

| Method | Key inputs | Credits | Returns |
| --- | --- | --- | --- |
| `get_user_profile` | `screen_name` (handle without `@`) | 1 | `TwitterProfileResponse`: `user`, `pinned_tweet`, `tweets` (the 4 or 5 newest original posts) |
| `get_user_profile_by_id` | `user_id` | 1 | the same `TwitterProfileResponse` |
| `get_tweet` | `tweet_id` | 1 | `TwitterTweetDetailResponse`: `tweet`, `parent_tweets`, `replies` (the top replies x.com shows logged-out) |
| `get_community` | `community_id` | 2 | `TwitterCommunityResponse`: `community`, `tweets` (the 20 posts x.com ranks by likes) |

Each call returns a fixed window. x.com offers no further pages to logged-out visitors, so there is no cursor.

## Read a profile

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    profile = tapline.twitter.get_user_profile("nasa")

user = profile.user
print(user.id, user.name, user.followers_count, user.is_blue_verified, user.bio_url)
for tweet in profile.tweets:
    print(tweet.created_at, tweet.like_count, tweet.view_count, tweet.text[:80])
```

A protected account returns its profile with `is_protected` set and no posts.

## Read a post

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    detail = tapline.twitter.get_tweet("2106870968048386134")

tweet = detail.tweet
links = {url.url: url.expanded_url for url in tweet.urls}
for media in tweet.media:
    best = max((v for v in media.variants if v.bitrate), key=lambda v: v.bitrate, default=None)
    print(media.type, media.media_url, best.url if best else None)
if tweet.quoted_tweet:
    print("quotes", tweet.quoted_tweet.url)
```

`text` keeps X's `t.co` links; `urls` maps each one to its expanded URL, and the trailing media link maps to the media page. `parent_tweets` holds the post a reply answers. Follow `in_reply_to_tweet_id` to walk further up.

## Read a community

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    page = tapline.twitter.get_community("1493446837214187523")

print(page.community.name, page.community.member_count, page.community.creator)
for tweet in page.tweets:
    print(tweet.author.screen_name, tweet.like_count)
```

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors).

- An account, post, or community x.com does not show raises `NotFoundError` (404, `not_found`). x.com answers the same way for deleted accounts and for live accounts it hides from logged-out visitors. The call is charged.
- A suspended account raises `PermissionDeniedError` (403, `resource_forbidden`). The call is charged.
- A malformed handle or id, or one of x.com's own page names such as `explore`, raises `UnprocessableEntityError` (422) before any fetch, and is not charged.
- Upstream failures and x.com's login wall raise a 5xx error and are not charged.

The [Twitter API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=twitter_readme#/twitter) lists every field.
