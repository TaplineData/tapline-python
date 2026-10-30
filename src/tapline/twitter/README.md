# Twitter (X) with the Tapline Python SDK

Use the Twitter client to read public X data as x.com shows it to logged-out visitors: a profile by handle or numeric id, an account's pinned and newest posts, one post with its media and quote, and an X Community with its top posts. No X account is needed.

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
| `get_profile` | `handle` (with or without `@`) or `user_id` | 1 | `TwitterProfileResponse`: the account, with the same fields as a post's `author` |
| `get_user_tweets` | `handle` | 1 | `TwitterUserTweetsResponse`: `tweets`, the pinned post then the newest original posts, 5 in all in samples |
| `get_tweet` | `url` (a post URL) | 1 | `TwitterTweetResponse`: one post with its `author`, `media` and `quoted_post` |
| `get_community` | `url` (a community URL) | 1 | `TwitterCommunityResponse`: the community with its `rules`, `creator` and a preview of `members` |
| `get_community_tweets` | `url` (a community URL) | 1 | `TwitterCommunityTweetsResponse`: `tweets`, the 20 posts x.com ranks by likes |

Every post has the same fields on all three post methods. `id` is X's numeric id, and every timestamp is ISO 8601 UTC, such as `2026-10-04T22:15:57Z`. Each call returns a fixed window. x.com offers no further pages to logged-out visitors, so there is no cursor.

## Read a profile

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    profile = tapline.twitter.get_profile(handle="nasa")

print(profile.id, profile.name, profile.created_at, profile.is_blue_verified)
print(profile.follower_count, profile.post_count, profile.location)
```

Send `handle` or `user_id`, not both. `user_id` is the account's numeric `id`, and it still finds the account after a handle change:

```python
with SyncTaplineClient() as tapline:
    same_account = tapline.twitter.get_profile(user_id=profile.id)
```

## Read an account's posts

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    posts = tapline.twitter.get_user_tweets(handle="nasa")

for tweet in posts.tweets:
    print(tweet.url, tweet.created_at, tweet.favorite_count, tweet.view_count)
```

`tweets` starts with the pinned post, if there is one, and marks it with `is_pinned`. A protected account returns no posts.

## Read a post

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    post = tapline.twitter.get_tweet(url="https://x.com/Seahawks/status/2106870968048386134")

print(post.author.handle, post.created_at, post.text)
links = {url.url: url.expanded_url for url in post.entities.urls or []}
for media in post.media or []:
    best = max(
        (v for v in media.variants or [] if v.bitrate), key=lambda v: v.bitrate or 0, default=None
    )
    print(media.type, media.media_url, best.url if best else None)
if post.quoted_post:
    quoted = post.quoted_post.post
    print("quotes", post.quoted_post.id, quoted.author.handle if quoted else None)
```

`url` takes a post URL on x.com or twitter.com, including `/i/status/<id>` and URLs with trailing segments such as `/photo/1`. `text` decodes X's HTML escapes, keeps its `t.co` links, and holds the full text of a long post. A long post also carries `preview_text`, the shortened version x.com shows first. `entities.urls` maps each `t.co` link to its expanded URL. Follow `reply_to.post_id` to the post a reply answers. The `author` also carries what x.com shows only on profile pages, such as `location`, the join date, the bio, the bio link and the banner. Tapline reads these from the author's profile page at no extra charge, so they can be up to 2 minutes old. It is best-effort, and an author whose profile page fails or is slow keeps only what x.com embeds with posts.

## Read a community

```python
from tapline import SyncTaplineClient
from tapline.twitter import TwitterUser

url = "https://x.com/i/communities/1493446837214187523"
with SyncTaplineClient() as tapline:
    community = tapline.twitter.get_community(url=url)
    posts = tapline.twitter.get_community_tweets(url=url)

creator = community.creator if isinstance(community.creator, TwitterUser) else None
print(community.name, community.member_count, creator.handle if creator else None)
for tweet in posts.tweets:
    print(tweet.author.handle, tweet.favorite_count, tweet.view_count, tweet.text[:80])
```

Tapline returns a suspended or deactivated member as only its `id` and `is_unavailable: true`, so `creator` and each entry in `members` is either a `TwitterUser` or a `TwitterUnavailableUser`. Check with `isinstance` before reading profile fields.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors).

- An account, post, or community x.com does not show raises `NotFoundError` (404, `not_found`). x.com answers the same way for deleted accounts and for live accounts it hides from logged-out visitors. The call is charged.
- A suspended account raises `PermissionDeniedError` (403, `resource_forbidden`) when looked up by handle, and `NotFoundError` when looked up by id. A post x.com withholds from logged-out visitors, such as one by a protected author, also raises `PermissionDeniedError`. The call is charged.
- A malformed handle, id or URL, one of x.com's own page names such as `explore`, or a `get_profile` call with both or neither of `handle` and `user_id` raises `UnprocessableEntityError` (422) before any fetch, and is not charged.
- Upstream failures and x.com's login wall raise `InternalServerError` (503) and are not charged.

The [Twitter API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=twitter_readme#/twitter) lists every response field.
