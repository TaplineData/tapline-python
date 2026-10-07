# Pinterest with the Tapline Python SDK

Use the Pinterest client to read public Pinterest data as pinterest.com shows it to logged-out visitors: pin search, one pin with every image size, its video and idea-pin pages, a user's boards, and the pins on a board. No Pinterest account is needed.

[Package guide](../../../README.md) · [Pinterest API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=pinterest_readme#/pinterest)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=pinterest_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=pinterest_readme).

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
| `search_pins` | `query`, `cursor` | 1 | `PinterestSearchResponse`: `pins` (Pinterest's search result objects plus an absolute `url`) and `cursor` |
| `get_pin` | `url`: a pin URL on any Pinterest domain, or a `pin.it` share link | 1 | `PinterestPinResponse`: the pin's GraphQL object in camelCase (`entityId`, `title`, `pinner`, `board`, `images_<size>` and `imageSpec_<size>`, `videos`, `storyPinData`, `aggregatedPinData`) |
| `get_user_boards` | `handle`, `cursor` | 1 | `PinterestUserBoardsResponse`: `boards` (name, relative `url`, counts, owner, cover images) and `cursor` |
| `get_board` | `url`: a board URL, or the relative `url` from `get_user_boards`; `cursor` | 1 | `PinterestBoardResponse`: `pins` in board order and `cursor` |

Each body is Pinterest's own data in the layout Scrape Creators returns, with `success`, `credits_charged` and `credits_remaining` at the top level. `trim` and `cache_max_age` are accepted for Scrape Creators compatibility and change nothing: every call returns the full body and is charged.

## Search pins and page through the results

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    cursor = None
    while True:
        page = tapline.pinterest.search_pins(query="italian pot roast", cursor=cursor)
        for pin in page.pins:
            username = pin.pinner.username if pin.pinner else None
            original = pin.images["orig"].url if pin.images and "orig" in pin.images else None
            print(pin.id, pin.url, pin.title, username, original)
        cursor = page.cursor
        if cursor is None:
            break
```

Pinterest sends up to 25 pins per page and the count varies, so keep paging while `cursor` is not `None`. A pin can show up on two pages. Most queries return related pins even without an exact match, but a query with no matches returns an empty first page, and that call is charged. Pinterest leaves keys out when a pin has nothing for them, so most search and board pin fields can be `None`: a pin uploaded without a link has no `link`.

## Read a pin

```python
with SyncTaplineClient() as tapline:
    pin = tapline.pinterest.get_pin(url="https://pin.it/2u9bHtUx6")

print(pin.entityId, pin.title, pin.link, pin.pinner.username, pin.imageSpec_orig.url)
print(pin.aggregatedPinData.aggregatedStats.saves, pin.repinCount, pin.createdAt)
if pin.videos:
    print("video", pin.videos.videoList.v720P.url, pin.videos.duration)
if pin.storyPinData:
    for story_page in pin.storyPinData.pages:
        print("idea pin page", len(story_page.blocks))
```

`entityId` is the numeric pin id; `id` is Pinterest's base64 node id, so join pins from `get_pin` with search or board pins on `entityId`. Pinterest's `isVideo` is `False` on some video pins, so test `videos` instead. A `pin.it` link is followed to its pin before the lookup, at no extra charge.

## List a user's boards, then read one

```python
with SyncTaplineClient() as tapline:
    boards = tapline.pinterest.get_user_boards(handle="broadstbullycom")
    for board in boards.boards:
        print(board.name, board.url, board.pin_count, board.follower_count)
    if boards.boards and boards.boards[0].url:
        page = tapline.pinterest.get_board(url=boards.boards[0].url)
        for pin in page.pins:
            print(pin.id, pin.title, pin.link or "uploaded, no link")
```

Boards come most recently pinned to first, up to 25 per page. A board's `url` is relative (`/broadstbullycom/nhl-hockey/`) and `get_board` takes it as it is. Board pins carry `link=None` when the pin was uploaded without one, and Pinterest sends no `pin_join` for them.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors).

- A pin, user or board Pinterest does not have raises `NotFoundError` (404, `not_found`). So does a `pin.it` link that leads to a board or nowhere. The call is charged.
- A cursor Pinterest does not recognise raises `InvalidCursorError` (400, `invalid_cursor`), and is not charged.
- A malformed URL or handle, a Pinterest page name such as `search` used as a handle, or a profile tab such as `/_created/` used as a board raises `UnprocessableEntityError` (422) before any fetch, and is not charged.
- Upstream failures raise `InternalServerError` (503) and are not charged.

Every response reports `credits_charged` and `credits_remaining`, your balance after the call. The [Pinterest API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=pinterest_readme#/pinterest) lists every field.
