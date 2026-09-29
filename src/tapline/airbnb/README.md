# Airbnb with the Tapline Python SDK

Use the Airbnb client to find stays, check prices and availability, and read listing details and reviews.

[Package guide](../../../README.md) · [Airbnb API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=airbnb_readme#/airbnb)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=airbnb_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=airbnb_readme).

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

### Discovery

| Method | Key inputs | Returns |
| --- | --- | --- |
| `search_locations` | `query`; optional `language` | `ParsedAutocompleteResponse` with suggestions and `place_id` values |
| `search` | one of `place_id`, `query`, center/radius, or bounding box; optional dates, guests, price, rooms, amenities, cancellation, currency, cursor | `ParsedSearchResponse` with listings and pagination |

### Listing data

| Method | Key inputs | Returns |
| --- | --- | --- |
| `get_price` | `room_id`, `check_in`, `check_out`; optional `adults`, `currency` | `ParsedPriceResponse` with stay and nightly pricing |
| `get_calendar` | `room_id`, `month`, `year`; optional `count`, `currency` | `ParsedCalendarResponse` with day-level availability |
| `get_details` | `room_id` | `ParsedDetailsResponse` with listing, host, amenities, policies, and media |
| `get_reviews` | `room_id`; optional `limit`, `offset`, `sort` | `ParsedReviewsResponse` with ratings and review text |

## Find a listing and check a stay

```python
from datetime import date, timedelta

from tapline import SyncTaplineClient

check_in = date.today() + timedelta(days=60)
check_out = check_in + timedelta(days=4)

with SyncTaplineClient() as tapline:
    places = tapline.airbnb.search_locations(query="London")
    place_id = places.suggestions[0].place_id
    if place_id is None:
        raise RuntimeError("Airbnb returned a location without a place_id")

    results = tapline.airbnb.search(place_id=place_id, adults=2)
    room_id = results.listings[0].room_id
    if room_id is None:
        raise RuntimeError("Airbnb returned a listing without a room_id")

    price = tapline.airbnb.get_price(
        room_id=room_id,
        check_in=check_in.isoformat(),
        check_out=check_out.isoformat(),
        adults=2,
    )
    calendar = tapline.airbnb.get_calendar(
        room_id=room_id,
        month=check_in.month,
        year=check_in.year,
    )
    details = tapline.airbnb.get_details(room_id=room_id)
    reviews = tapline.airbnb.get_reviews(room_id=room_id, limit=10)

print(price.available, price.requested_stay_total)
print(calendar.months[0].days[0].available)
print(details.title, details.rating_summary)
print(reviews.total_count)
```

`price.breakdown` lists each nightly line Airbnb quoted as `nights`, `unit_price` and `total`. It is empty for unavailable dates and monthly quotes. Discounts are in `price.rate_details.discounts`.

Airbnb can silently fall back to USD for unsupported display currencies; treat the response currency as authoritative. A listing found by search may later be removed or made unavailable.

## Search filters

```python
from tapline import SyncTaplineClient
from tapline.airbnb import AmenityFilter

with SyncTaplineClient() as tapline:
    results = tapline.airbnb.search(
        query="Rio de Janeiro",
        adults=2,
        min_bedrooms=1,
        price_max=300,
        amenities=[AmenityFilter.WIFI, AmenityFilter.AIR_CONDITIONING],
        free_cancellation=True,
    )
```

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). The [Airbnb API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=airbnb_readme#/airbnb) lists the inputs, response fields, limits, and credit cost for each method.
