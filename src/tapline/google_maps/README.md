# Google Maps with the Tapline Python SDK

Use the Google Maps client to search places, read a place with its reviews, photos, owner posts and popular times, get directions and search suggestions, find the address at a point, and read contributors, shared lists, Street View panoramas, area traffic and weather.

[Package guide](../../../README.md) · [Google Maps API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=google_maps_readme#/google_maps)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=google_maps_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=google_maps_readme).

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

Every method except `get_place_ids` and `get_share_link` takes `hl`, the language of the answer's text (`en` by default), and `gl`, the region that sets ranking, currency and units (`us` by default).

| Method | Key inputs | Returns | Credits |
| --- | --- | --- | --- |
| `search` | `query`, `latitude` and `longitude`, `zoom`, `open_now`, `min_rating`, `limit` (up to 100), `cursor` | places for a Maps search | 3 |
| `get_place` | `feature_id` | one place | 2 |
| `get_place_by_cid` | `cid` | one place | 2 |
| `get_place_ids` | `place_id` | the feature id and CID for a Google place id | 2 |
| `list_reviews` | `feature_id`, `sort`, `limit` (up to 60), `cursor` | a page of a place's reviews | 2 |
| `list_photos` | `feature_id`, `category`, `limit` (up to 10), `cursor` | a page of photos from one photo tab | 1 |
| `list_posts` | `feature_id` | a business's latest owner posts, up to 10 | 1 |
| `get_photo` | `photo_id` | one photo or video | 1 |
| `get_directions` | `origin`, `destination`, `travel_mode` | routes between two places | 2 |
| `list_suggestions` | `query`, `latitude` and `longitude` | places and queries for partly typed text | 1 |
| `get_contributor` | `contributor_id`, `limit` (up to 50) | a contributor's profile with their latest reviews and photos | 4 |
| `reverse_geocode` | `latitude`, `longitude` | the address and place at a coordinate | 1 |
| `get_popular_times` | `kgmid` | a place's busyness by hour for each day | 7 |
| `get_list` | `list_id` | a public shared list and its places | 1 |
| `get_share_link` | `code` | the place or list a `maps.app.goo.gl` link opens | 1 |
| `get_panorama` | `pano_id` | one Street View panorama | 1 |
| `list_panoramas_near` | `latitude`, `longitude` | the Street View panoramas near a coordinate | 1 |
| `get_traffic` | `south`, `west`, `north`, `east` (`west` above `east` crosses 180°) | the traffic summary for a box up to 1 degree a side | 1 |
| `get_weather` | `latitude`, `longitude` | the current weather at a coordinate | 1 |

Paged methods cost their credits per page, not per item.

## Search places

```python
cursor = ""
for _ in range(3):
    page = tapline.google_maps.search(
        query="coffee in Austin TX", open_now=True, min_rating=4.5, cursor=cursor
    )
    for place in page.results:
        print(place.name, place.rating, place.review_count, place.feature_id)
    if page.pagination.next_cursor is None:
        break
    cursor = page.pagination.next_cursor
```

## Read a place and its newest reviews

```python
jos_coffee = "0x8644b4fda2c12fd5:0x66b58cb4722b37b"

place = tapline.google_maps.get_place(jos_coffee)
print(place.name, place.address, place.rating, place.open_status)

reviews = tapline.google_maps.list_reviews(jos_coffee, sort="newest")
for review in reviews.reviews:
    print(review.rating, review.created_at, review.text)
```

## Get directions

```python
directions = tapline.google_maps.get_directions(
    origin="Austin-Bergstrom International Airport",
    destination="Jo's Coffee South Congress, Austin, TX",
    travel_mode="transit",
)
for route in directions.routes:
    if route.duration:
        print(route.name, route.duration.text)
```

## Read the response

- Places are keyed by `feature_id` (`0x…:0x…`). `get_place_by_cid` and `get_place_ids` look a place up by its CID or Google place id; only `ChIJ…` place ids resolve, so address and coordinate ids answer 404. `get_popular_times` takes the `kgmid` from a search result or a place.
- Paged methods return `pagination`. Pass `pagination.next_cursor` back as `cursor` until it is null. A cursor works only for the search or place that issued it.
- Google reranks search results between calls, so later pages leave out places earlier pages returned and can miss a few that moved.
- Some text is read only in English: hotel check-in and check-out times on `search` and the place methods, and `typical_visit` and `social_posts` on `get_popular_times`.
- `get_weather` answers in °F for `gl="us"` and in °C for most other regions.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). Validation errors and cursors this API did not issue are not charged, and neither is a 503 when Google blocks every attempt. An id Google does not know answers 404 and is charged. `list_reviews` and `list_posts` can't tell an unknown place from one with no reviews or posts: both answer an empty page, and the call is charged.

The [Google Maps API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=google_maps_readme#/google_maps) lists the inputs, response fields, and credit cost for each method.
