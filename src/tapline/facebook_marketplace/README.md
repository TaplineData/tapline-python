# Facebook Marketplace with the Tapline Python SDK

Use the Facebook Marketplace client to find Marketplace locations, search and browse listings around a point, read a listing with its seller and photos, and map rentals. Pages, posts and groups are in the [Facebook client](../facebook/README.md).

[Package guide](../../../README.md) · [Facebook Marketplace API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=facebook_marketplace_readme#/facebook_marketplace)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=facebook_marketplace_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=facebook_marketplace_readme).

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
| `search_marketplace_locations` | `query` | places with the coordinates Marketplace takes | 3 |
| `search_marketplace` | `query`, `latitude`, `longitude`, `cursor`, `radius_km`, `min_price`, `max_price`, `condition`, `days_since_listed`, `delivery`, `sort` | listings around a point | 3 |
| `get_marketplace_categories` |  | categories and subcategories | 3 |
| `list_marketplace_category_listings` | `category`, `latitude`, `longitude`, `cursor`, `radius_km`, `min_price`, `max_price` | one category's listings around a point | 3 |
| `list_marketplace_feed` | `latitude`, `longitude`, `cursor`, `radius_km` | the Marketplace home feed | 3 |
| `get_marketplace_listing` | `listing_id` | one listing with its seller | 4 |
| `list_marketplace_listing_photos` | `listing_id` | every photo and video of a listing | 3 |
| `list_marketplace_rentals` | `latitude`, `longitude`, `radius_km`, `min_price`, `max_price` | rental map clusters with a count each | 3 |

Paged methods cost their credits per page.

## Search Marketplace

```python
places = tapline.facebook_marketplace.search_marketplace_locations(query="Austin, TX")
austin = places.locations[0]
if austin.latitude is not None and austin.longitude is not None:
    listings = tapline.facebook_marketplace.search_marketplace(
        query="bike", latitude=austin.latitude, longitude=austin.longitude, max_price=300
    )
    for listing in listings.listings:
        print(listing.title, listing.price and listing.price.formatted)
```

`min_price` and `max_price` are whole units of the local currency. A search page can come back empty with a `next_cursor`; keep paging. A cursor works only with the method and inputs that issued it.

## Read a listing

```python
listing = tapline.facebook_marketplace.get_marketplace_listing("4498962133715634")
media = tapline.facebook_marketplace.list_marketplace_listing_photos("4498962133715634")
print(listing.title, len(media.photos), len(media.videos))
```

## Read the response

- Facebook's enum values arrive as `{code, label}`: `code` is Facebook's value and `label` says what it means.
- Listing photos and videos carry their id, image or playable URL, size and thumbnail.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). Validation errors are not charged: `min_price` above `max_price`, or a cursor from another method or other inputs. A listing id Facebook does not know answers 404 and is charged. When Facebook refuses every proxy attempt the call answers 503 and is not charged.

The [Facebook Marketplace API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=facebook_marketplace_readme#/facebook_marketplace) lists the inputs, response fields, and credit cost for each method.
