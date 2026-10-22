# Expedia with the Tapline Python SDK

Use the Expedia client to read expedia.com: search hotels and vacation homes for your dates and guests, read a hotel's details, reviews, rooms and price calendar, and find things to do in a city or near a hotel.

[Package guide](../../../README.md) · [Expedia API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=expedia_readme#/expedia)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=expedia_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=expedia_readme).

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

Stays take `check_in` and `check_out` (`YYYY-MM-DD`, at most 28 nights), `adults` (default 2) and `children_ages`, one age per child. Prices are in USD.

| Method | Key inputs | Returns | Credits |
| --- | --- | --- | --- |
| `search_locations` | `query`, `limit` (up to 10) | cities, neighborhoods, airports and landmarks with the `region_id` to search with | 1 |
| `search_hotels` | `region_id`, the stay, `sort`, price, star rating, guest rating, property type, amenity and meal-plan filters, `cursor` | 25 hotels per page with price, guest rating, coordinates, badges, photos and a booking link | 4 |
| `get_hotel` | `hotel_id` | name, star rating, region, address, coordinates, guest rating with category scores, an AI review summary, amenities, accessibility, policies, photos | 2 |
| `list_hotel_reviews` | `hotel_id`, `sort`, `traveler_type`, `cursor` | 10 reviews per page with score, text, date, stay, author, traveler type, liked and disliked topics, photos and replies | 2 |
| `list_hotel_rooms` | `hotel_id`, the stay, `region_id` | every room with its rate plans: extras such as breakfast, prices per payment option, cancellation terms, and Expedia's price signal when you pass the region | 3 |
| `get_hotel_calendar` | `hotel_id`, optional stay | each day's nightly price, and for vacation homes whether you can check in or out and the night limits | 2 |
| `search_activities` | `region_id`, `start_date`, `end_date`, `sort`, `cursor` | 20 things to do per page with price, rating, duration and a link | 2 |
| `list_hotel_activities` | `hotel_id`, `start_date`, `end_date`, `sort`, `cursor` | 20 things to do per page near the hotel, with the distance to each | 2 |
| `get_activity` | `activity_id`, optional `start_date` and `end_date` | description, address, what's included, available dates, ticket prices and the latest 10 reviews | 2 |

Paged methods cost their credits per page, not per item.

## Find a region and search it

```python
locations = tapline.expedia.search_locations(query="new york")
region = next(location for location in locations.locations if location.type == "CITY")

page = tapline.expedia.search_hotels(
    region_id=region.region_id,
    check_in="2026-12-14",
    check_out="2026-12-16",
    star_ratings=[4, 5],
    sort="price_low_to_high",
)
for hotel in page.hotels:
    if hotel.price:
        print(hotel.id, hotel.name, hotel.price.total.amount, hotel.guest_rating.score)
```

`2621` is New York City. Follow `page.pagination.next_cursor` with the same inputs for the next 25.

## Price the rooms of one hotel

```python
rooms = tapline.expedia.list_hotel_rooms(
    hotel_id="19681371", check_in="2026-12-14", check_out="2026-12-16", adults=2
)
for room in rooms.rooms:
    for plan in room.rate_plans:
        for price in plan.prices:
            print(
                room.name,
                plan.id,
                price.payment_model,
                price.total.formatted,
                plan.cancellation_policy,
            )
```

## Plan around a stay

```python
calendar = tapline.expedia.get_hotel_calendar(hotel_id="105590218")
bookable = [day for day in calendar.days if day.check_in_status == "valid"]
if bookable:
    print(bookable[0].date, bookable[0].price, bookable[0].max_nights)

nearby = tapline.expedia.list_hotel_activities(
    hotel_id="19681371", start_date="2026-12-14", end_date="2026-12-16"
)
for activity in nearby.activities:
    print(activity.name, activity.distance, activity.price.current.formatted if activity.price else None)
```

## Read the response

- `price.total` is the whole stay with taxes and fees, as an exact amount. `price.nightly` is Expedia's displayed nightly rate before taxes, rounded to whole dollars.
- `price` is `None` on a search card when Expedia shows no bookable rate for your dates or party.
- Search cards carry coordinates but no star rating; `get_hotel` has it.
- `subtitles` on a search card are Expedia's heading lines as shown: a neighborhood for hotels, "Entire home by Vrbo" for many vacation homes.
- `total_count` is Expedia's own estimate and can move when you add filters.
- `strikethrough` is the whole stay's earlier total, comparable with `total`, not with `nightly`.
- An empty `cancellation_policy` means the plan is non-refundable. `extras` names what a plan adds, such as `Breakfast` or `No extras`.
- No rooms means the dates aren't bookable; `get_hotel_calendar` shows which dates are. A room Expedia cannot sell for your party comes back with empty `rate_plans`.
- `price_insight` needs the hotel's `region_id` (from `get_hotel`) and is still `None` for some stays.
- On a calendar, `has_daily_availability` is `True` for vacation homes, which report each day's `available`, statuses and night limits. Hotel calendars carry prices only. The stay dates move the window only when they lie past the default range.
- `traveler_types` are Expedia's labels, such as `Traveled with partner`.
- `distance` is filled only by `list_hotel_activities`. Activity scores use the same 10-point scale as hotels.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). Validation errors (past or over-long dates, an unknown enum value, a minimum price above its maximum, a cursor this API did not issue) are not charged. An unknown hotel answers 404 on every hotel method, and an unknown activity on `get_activity`; both are charged. Blocks and upstream failures answer 503 and are not charged.

The [Expedia API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=expedia_readme#/expedia) lists the inputs, response fields, and credit cost for each method.
