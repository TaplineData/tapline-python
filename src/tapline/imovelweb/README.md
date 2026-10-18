# imovelweb with the Tapline Python SDK

Use the imovelweb client to read imovelweb.com.br, Brazil's QuintoAndar-owned property portal: search homes and commercial property for sale, rent, short stays, auction and new developments, plot a search on a map, read full listings, and get each agency's phone numbers and buyer ratings.

[Package guide](../../../README.md) · [imovelweb API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=imovelweb_readme#/imovelweb)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=imovelweb_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=imovelweb_readme).

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

Search and map take the same filters: `operation` (`sale`, `rent`, `season`, `auction`, `development`), `location_id`, property type and subtype, price, condo fee, bedrooms, bathrooms, parking, total and usable area, building age, publication date, publisher type (`all`, `company`, `owner`) or id, amenities, media, a keyword, `development_stage` for developments, and `without_guarantor` and `price_includes_condo_fee` for rentals.

| Method | Key inputs | Returns | Credits |
| --- | --- | --- | --- |
| `list_locations` | `query`, `limit` (up to 10) | state, city and neighbourhood ids to search with | 1 |
| `list_listings` | the filters, `sort`, `cursor` | 30 listings per page with prices, condo fee, areas, rooms, address, coordinates, photos, the agency and the advertiser's WhatsApp number | 2 |
| `map_listings` | the filters | up to 100 map markers, the count imovelweb can place, the viewport and the location's outline | 1 |
| `get_listing` | `posting_id` | the full listing: description, every photo and floor plan, amenities, prices, coordinates, publication date, a development's units | 2 |
| `list_similar_listings` | `posting_id`, `limit` | listings imovelweb shows as similar | 1 |
| `list_listing_publishers` | `posting_id` | every agency advertising the same property | 1 |
| `get_publisher` | `publisher_id` | an agency's profile: phone numbers as +55 numbers, address, year joined, active listing count and buyer ratings | 2 |

Paged methods cost their credits per page, not per item.

## Find a location id

```python
suggestions = tapline.imovelweb.list_locations(query="pinheiros")
for location in suggestions.locations:
    print(location.id, location.level, location.label)
```

`V1-Z-52` is Pinheiros in São Paulo. Pass several ids to `location_id` and listings in any of them match.

## Page through rentals

```python
cursor = ""
while True:
    page = tapline.imovelweb.list_listings(
        operation="rent", location_id=["V1-Z-52"], min_bedrooms=2, cursor=cursor
    )
    for listing in page.listings:
        print(listing.id, listing.title, listing.publisher.name, listing.whatsapp)
    if page.pagination.next_cursor is None:
        break
    cursor = page.pagination.next_cursor
```

## Get an agency's phone numbers

```python
agency = tapline.imovelweb.get_publisher("15460167")
print(agency.name, agency.phone_numbers, agency.address)
if agency.ratings:
    print(agency.ratings.average, agency.ratings.review_count)
```

Take the id from `publisher.id` on a search listing.

## Read the response

- Records use this API's names and decoded values. `property_type`, `ad_tier`, amenities and the location levels are enums; `operations` has one entry per operation a listing is offered for, each with its price as `amount`, `currency` (`BRL`) and imovelweb's `display` text; `whatsapp` and `phone_numbers` are +55 numbers.
- Each record keeps the fields this API does not decode under `raw`, in imovelweb's own names. Fields typed `Any` there were null in every answer imovelweb gave us, so their shape is unknown.
- `pagination.completion` is `exhausted` at the end, or `depth_limit` at page 1,000 (30,000 listings). Narrow the filters to reach the rest.
- About a fifth of search listings hide their map position (`location.latitude` is `None`). `get_listing` usually still has coordinates.
- `publisher.type` is `owner` for an owner selling directly. Owners have no profile, so their `publisher.url` is `None`, `get_publisher` answers 404 for them, and the listing's `whatsapp` is their contact.
- `get_listing` gives only the first digits of the agency's phone (`publisher.partial_phone`). `get_publisher` has every number.
- An amenity this API does not name comes back with `amenity` set to `None`, plus imovelweb's `id` and `label`.
- `ratings` is `None` when imovelweb keeps no statistics for an agency. An unrated agency has `None` for `review_count`, `average` and `recommend_percent`, and no `questions`.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). Validation errors (an unknown enum value, a subtype without its type, a minimum above its maximum, a cursor this API did not issue) are not charged. A location id imovelweb does not know answers 400 `invalid_request` naming it, and is not charged. `map_listings` answers 400 on filters imovelweb's map cannot run across the whole country or a state; narrow to a city or neighbourhood. It answers 422 to `max_age="launching_soon"`, which imovelweb's map cannot run anywhere; `list_listings` takes it. An unknown listing or publisher id answers 404 and is charged.

The [imovelweb API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=imovelweb_readme#/imovelweb) lists the inputs, response fields, and credit cost for each method.
