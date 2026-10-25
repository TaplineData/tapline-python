# Facebook Ad Library with the Tapline Python SDK

Use the Facebook Ad Library client to search Meta's Ad Library, read ads, their versions and who paid for them, look up advertisers and their audiences, and read the political and issue ads report. Pages, posts and groups are in the [Facebook client](../facebook/README.md).

[Package guide](../../../README.md) · [Facebook Ad Library API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=facebook_ad_library_readme#/facebook_ad_library)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=facebook_ad_library_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=facebook_ad_library_readme).

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
| `search_ads` | `query` or `page_id`, `cursor`, `match`, `country`, `status`, `ad_type`, `media_type`, `platforms`, `languages`, `delivered_after`, `delivered_before`, `sort` | 10 Ad Library ads per page | 3 |
| `get_ad` | `ad_id`, `country` | one ad | 3 |
| `get_ad_transparency` | `ad_id`, `page_id`, `country` | who paid for an ad, whom it reached in the EU, UK and Brazil, and its political audience | 3 |
| `search_advertisers` | `query`, `country`, `ad_type` | advertisers matching a name | 3 |
| `get_advertiser` | `page_id`, `country` | an advertiser's Ad Library profile and its first active ads | 3 |
| `get_advertiser_audience` | `page_id`, `period` | how an advertiser targeted its political and issue ads | 3 |
| `list_ad_versions` | `collation_id`, `country`, `cursor` | every version of an ad under one creative | 3 |
| `get_ad_report` | `country`, `period`, `date` | the political and issue ads report for a country; a 503 with `Retry-After` means retry after that many seconds | 3 |
| `list_ad_report_advertisers` | `country`, `period`, `query`, `sort`, `cursor`, `date` | 20 report advertisers per page | 3 |

Paged methods cost their credits per page.

## Search ads and follow their versions

```python
ads = tapline.facebook_ad_library.search_ads(query="running shoes", country="GB")
for ad in ads.ads:
    print(ad.ad_archive_id, ad.page.name, ad.collation.count)

cursor = ads.pagination.next_cursor
if cursor:
    more = tapline.facebook_ad_library.search_ads(
        query="running shoes", country="GB", cursor=cursor
    )
    print(len(more.ads))

first = ads.ads[0]
if first.collation.id:
    versions = tapline.facebook_ad_library.list_ad_versions(first.collation.id, country="GB")
    print(versions.total_count, len(versions.ads))
```

Pass `page_id` instead of `query` to list one advertiser's ads. A cursor works only with the method and inputs that issued it.

## Read an advertiser and the political ads report

```python
advertiser = tapline.facebook_ad_library.get_advertiser("15087023444", country="US")
print(advertiser.page.name, advertiser.ads.total_count)

report = tapline.facebook_ad_library.get_ad_report(country="US", period="last_30_days")
print(report.lifetime.total_ads, report.lifetime.total_spend.formatted)
top = tapline.facebook_ad_library.list_ad_report_advertisers(country="US", period="last_30_days")
for row in top.advertisers:
    print(row.page.name, row.paid_for_by, row.total_spend.formatted)
```

## Read the response

- Facebook's enum values arrive as `{code, label}`: `code` is Facebook's value and `label` says what it means.
- `get_advertiser_audience` answers empty lists for advertisers without political or issue ads.
- Facebook can take two minutes to build a `lifelong` report. The API answers within 90 seconds, with an uncharged 503 `upstream_unavailable` and `Retry-After` while Facebook is still building it. The client retries, and once the report is ready a retry is served from the cache. `get_ad_report` waits 120 seconds by default instead of the client's timeout.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). Validation errors are not charged: both or neither of `query` and `page_id`, `match` with `page_id`, or a cursor from another method or other inputs. An ad, advertiser or collation id Facebook does not know answers 404 and is charged. When Facebook refuses every proxy attempt the call answers 503 and is not charged.

The [Facebook Ad Library API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=facebook_ad_library_readme#/facebook_ad_library) lists the inputs, response fields, and credit cost for each method.
