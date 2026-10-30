# Pinterest v2 with the Tapline Python SDK

Use the Pinterest v2 client to read public Pinterest data as pinterest.com shows it to logged-out visitors: pin search, one pin, a user's boards, and the pins on a board. Every method returns the same pin, board and user objects, so code that reads a search pin also reads a board pin. No Pinterest account is needed.

The [Pinterest v1 client](../pinterest/README.md) reads the same four pages at the same prices in Pinterest's own layout. Both stay available.

[Package guide](../../../README.md) · [Pinterest API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=pinterest_v2_readme#/pinterest)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=pinterest_v2_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=pinterest_v2_readme).

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
| `search_pins` | `query`, `cursor` | 1 | `PinterestV2SearchResponse`: `pins`, the refinement `guides` Pinterest suggests, and `cursor` |
| `get_pin` | `url`: a pin URL on any Pinterest domain, or a `pin.it` share link | 1 | `PinterestV2PinResponse`: one pin with its people, board, metrics, images, video and idea-pin pages |
| `get_user_boards` | `handle`, `cursor` | 1 | `PinterestV2UserBoardsResponse`: `boards` and `cursor` |
| `get_board` | `url`: a board URL, such as a board's `url` from `get_user_boards`; `cursor` | 1 | `PinterestV2BoardResponse`: `pins` in board order and `cursor` |

`trim` is accepted on every method and `cache_max_age` on `get_pin`. Neither changes the response, and every successful call is charged.

## Search pins and page through the results

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    cursor = None
    while True:
        page = tapline.pinterest_v2.search_pins(query="italian pot roast", cursor=cursor)
        for pin in page.pins:
            username = pin.pinner.username if pin.pinner else None
            original = next(
                (image.url for image in pin.images or [] if image.variant == "orig"), None
            )
            print(pin.id, pin.url, pin.title, username, original)
        cursor = page.cursor
        if cursor is None:
            break
```

Pinterest sends up to 25 pins per page and the count varies, so keep paging while `cursor` is not `None`. A pin can show up on two pages. A query with no matches returns an empty first page, and that call is charged. `images` lists every size Pinterest has for the pin, each with its `variant` (`236x`, `736x`, `orig`) and, where Pinterest sends them, `width` and `height`.

## Read a pin

```python
with SyncTaplineClient() as tapline:
    pin = tapline.pinterest_v2.get_pin(url="https://pin.it/2u9bHtUx6")

print(pin.id, pin.title, pin.link, pin.media_type, pin.created_at)
pinner = pin.pinner.username if pin.pinner else None
board = pin.board.url if pin.board else None
print(pinner, board, pin.hashtags)
if pin.metrics:
    print(pin.metrics.save_count, pin.metrics.repin_count, pin.metrics.reaction_count)
if pin.video:
    streams = pin.video.variants or []
    stream = next((s for s in streams if s.variant == "v720P"), streams[0] if streams else None)
    print("video", stream.url if stream else None, pin.video.duration_ms)
if pin.story:
    for story_page in pin.story.pages or []:
        print("idea pin page", story_page.id, len(story_page.blocks or []))
```

`id` is the numeric pin id that search and board pins carry too, and `node_id` is Pinterest's base64 node id. People keep their roles: `pinner` saved the pin, `creator` made it, and `origin_pinner`, `promoter` and `link_owner` appear when Pinterest names them. `created_at` is Pinterest's own date text (`Sun, 06 Apr 2025 06:52:37 +0000`). Pinterest leaves keys out when a pin has nothing for them, so every field can be `None`. A `pin.it` link is followed to its pin before the lookup, at no extra charge.

## List a user's boards, then read one

```python
with SyncTaplineClient() as tapline:
    boards = tapline.pinterest_v2.get_user_boards(handle="broadstbullycom")
    for board in boards.boards:
        owner = board.owner.username if board.owner else None
        print(board.name, board.url, board.pin_count, board.follower_count, owner)
    if boards.boards and boards.boards[0].url:
        page = tapline.pinterest_v2.get_board(url=boards.boards[0].url)
        for pin in page.pins:
            saves = pin.metrics.save_count if pin.metrics else None
            print(pin.id, pin.title, pin.link or "uploaded, no link", saves)
```

Boards come most recently pinned to first, about 25 per page. A board's `url` is absolute and `get_board` takes it as it is. A pin uploaded without a link has `link=None`.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors).

- A pin, user or board Pinterest does not have raises `NotFoundError` (404, `not_found`). So does a `pin.it` link that leads to a board or nowhere. The call is charged.
- A cursor Pinterest does not recognise raises `InvalidCursorError` (400, `invalid_cursor`), and is not charged.
- A malformed URL or handle raises `UnprocessableEntityError` (422) before any fetch, and is not charged. So do the `e1_…` ids in search and board results, which Pinterest does not resolve for logged-out visitors.
- Upstream failures raise `InternalServerError` (503) and are not charged.
