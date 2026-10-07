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
| `get_user_profile` | `screen_name` (handle without `@`) | 1 | `TwitterProfileResponse`: X's User object (`rest_id`, `core`, `legacy`, `location`, `privacy`, `verification`) plus `pinned_tweet` and `tweets` (the 4 or 5 newest original posts) |
| `get_user_profile_by_id` | `user_id` | 1 | the same `TwitterProfileResponse` |
| `get_tweet` | `tweet_id` | 1 | `TwitterTweetDetailResponse`: X's Tweet object (`rest_id`, `core`, `legacy`, `views`, `note_tweet`, `quoted_status_result`) plus `parent_tweets` and `replies` (the top replies x.com shows logged-out) |
| `get_community` | `community_id` | 2 | `TwitterCommunityResponse`: X's Community object (`rest_id`, `name`, `member_count`, `rules`, `creator_results`) plus `tweets` (the 20 posts x.com ranks by likes) |

Each body is X's own object in the layout Scrape Creators returns, with `success`, `credits_charged` and `credits_remaining` at the top level. Each call returns a fixed window. x.com offers no further pages to logged-out visitors, so there is no cursor.

## Read a profile

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    profile = tapline.twitter.get_user_profile("nasa")

print(profile.rest_id, profile.core.name, profile.core.created_at, profile.is_blue_verified)
print(profile.legacy.followers_count, profile.legacy.statuses_count, profile.location.location)
for tweet in profile.tweets:
    print(tweet.url, tweet.legacy.created_at, tweet.legacy.favorite_count, tweet.views.count)
```

A protected account returns its profile with `privacy.protected` set and no posts.

## Read a post

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    post = tapline.twitter.get_tweet("2106870968048386134")

text = post.note_tweet.note_tweet_results.result.text if post.note_tweet else post.legacy.full_text
links = {url.url: url.expanded_url for url in post.legacy.entities.urls or []}
media_items = post.legacy.extended_entities.media if post.legacy.extended_entities else []
for media in media_items:
    variants = media.video_info.variants if media.video_info else []
    best = max((v for v in variants if v.bitrate), key=lambda v: v.bitrate or 0, default=None)
    print(media.type, media.media_url_https, best.url if best else None)
if post.quoted_status_result:
    quoted = post.quoted_status_result.result
    print("quotes", quoted.rest_id, quoted.core.user_results.result.core.screen_name)
```

`legacy.full_text` keeps X's `t.co` links and HTML escapes, and holds X's shortened text for a long post; `note_tweet` carries the full text. `legacy.entities.urls` maps each `t.co` link to its expanded URL. `parent_tweets` holds the post a reply answers. Follow `legacy.in_reply_to_status_id_str` to walk further up. The author under `core.user_results.result` carries only what x.com embeds with posts, plus the join date (`core.created_at`) that Tapline adds. Call `get_user_profile` for the location, banner and bio link.

## Read a community

```python
from tapline import SyncTaplineClient
from tapline.twitter import TwitterCommunityUser

with SyncTaplineClient() as tapline:
    community = tapline.twitter.get_community("1493446837214187523")

creator = community.creator_results.result if community.creator_results else None
creator_core = creator.core if isinstance(creator, TwitterCommunityUser) else None
print(community.name, community.member_count, creator_core.screen_name if creator_core else None)
for tweet in community.tweets:
    print(tweet.user.core.screen_name, tweet.favorite_count, tweet.view_count, tweet.full_text[:80])
```

Community posts come flattened the way Scrape Creators flattens them: a post's `legacy` fields sit at the top level next to `id`, `view_count` and the author as `user`. The community's `created_at` is in Unix milliseconds. x.com sends a suspended or deactivated member as a bare `UserUnavailable`, so `creator_results.result` and each `members_facepile_results[].result` is either a `TwitterCommunityUser` or a `TwitterUnavailableResult`. Check with `isinstance` before reading profile fields.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors).

- An account, post, or community x.com does not show raises `NotFoundError` (404, `not_found`). x.com answers the same way for deleted accounts and for live accounts it hides from logged-out visitors. The call is charged.
- A suspended account raises `PermissionDeniedError` (403, `resource_forbidden`) when looked up by handle, and `NotFoundError` when looked up by id. A post x.com withholds from logged-out visitors, such as one by a protected author, also raises `PermissionDeniedError`. The call is charged.
- A malformed handle or id, or one of x.com's own page names such as `explore`, raises `UnprocessableEntityError` (422) before any fetch, and is not charged.
- Upstream failures and x.com's login wall raise a 5xx error and are not charged.

Every response reports `credits_charged` and `credits_remaining`, your balance after the call. The [Twitter API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=twitter_readme#/twitter) lists every field.
