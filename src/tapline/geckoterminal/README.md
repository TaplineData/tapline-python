# GeckoTerminal with the Tapline Python SDK

Use the GeckoTerminal client to find pools, screen liquidity, read candlesticks and swaps, inspect traders, and follow market trends.

[Package guide](../../../README.md) · [GeckoTerminal API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=geckoterminal_readme#/geckoterminal)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=geckoterminal_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=geckoterminal_readme).

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

### Networks, search, and trends

| Method | Key inputs | Returns |
| --- | --- | --- |
| `dexes` | optional `network`, `page` | `DexesResponse`: indexed DEXes and activity metrics |
| `global_stats` | none | `GlobalStatsResponse`: 24h volume, pool/network counts, fear-and-greed |
| `networks` | optional `sort` | `NetworksResponse`: indexed chains and native currencies |
| `network_rankings` | optional `page` | `NetworkRankingsResponse`: chain volume, transactions, and pool counts |
| `search` | `query` | `SearchResponse`: tokens, pools, pairs, categories, networks, and DEXes |
| `search_trends` | none | `SearchTrendsResponse`: current user search trends |
| `tags` | optional `page` | `TagsResponse`: token categories and leading tokens |
| `trending_links` | none | `TrendingLinksResponse`: curated trending shortcuts |
| `trending_themes` | optional `network`, `dex`, `more_themes` | `TrendingThemesResponse`: narratives and their driving pools |
| `trends` | optional `network`, `dex` | `TrendsResponse`: top gainers, new pools, and hot pairs |

### Pool discovery

| Method | Key inputs | Returns |
| --- | --- | --- |
| `network_latest_pools` | `network`; optional `page`, `pool_creation_hours_ago_lte` | `NetworkLatestPoolsResponse`: newest pools on one chain |
| `network_pools` | `network`; screener body filters | `NetworkPoolsResponse`: screened pools on one chain or DEX |
| `latest_pools` | optional `page`, `pool_creation_hours_ago_lte` | `LatestPoolsResponse`: newest pools across chains |
| `revival_radar_pools` | none | `RevivalRadarPoolsResponse`: older pools with reaccelerating activity |
| `pools` | screener body filters | `PoolsResponse`: cross-chain pool screener |
| `tag_network_pools` | `tag`, `network`; optional `page` | `TagNetworkPoolsResponse`: category pools on one chain |
| `tag_pools` | `tag`; optional `page` | `TagPoolsResponse`: category pools across chains |

### Pool detail and activity

| Method | Key inputs | Returns |
| --- | --- | --- |
| `candlesticks` | `pool_id`, `pair_id`, `from_timestamp`, `to_timestamp`; optional `resolution`, `currency`, `is_inverted` | `CandlesticksResponse`: OHLCV bars |
| `pool` | `network`, `address`; optional `base_token` | `PoolResponse`: price, reserves, GT score, security, tokens, DEX, developer |
| `pool_related_pools` | `network`, `address` | `PoolRelatedPoolsResponse`: same-base-token pools and liquidity |
| `pool_sender_swaps` | `network`, `address`, `from_timestamp`, `to_timestamp`; optional `pair_id`, `sender`, `include_developer`, `inverted` | `PoolSenderSwapsResponse`: swaps grouped by sender |
| `pool_swaps` | `network`, `address`, `pair_id`; `page_after` or `page_before`; optional `sender`, `inverted` | `PoolSwapsResponse`: individual swaps and cursors |
| `pool_token_info_snapshots` | `network`, `address` | `PoolTokenInfoSnapshotsResponse`: descriptions, socials, metadata for both tokens |

### Token, wallet, and developer data

| Method | Key inputs | Returns |
| --- | --- | --- |
| `token_historical_holders` | `network`, `token_address`; optional `period` | `TokenHistoricalHoldersResponse`: holder-count time series |
| `token_top_holders` | `network`, `token_address` | `TokenTopHoldersResponse`: largest holders and supply shares |
| `token_top_traders` | `token_id` | `TokenTopTradersResponse`: profitable wallets, P&L, buys, sells, balance |
| `wallet_token` | `token_id`, `wallet_address` | `WalletTokenResponse`: one wallet's token position and P&L |
| `token_developer_past_tokens` | `developer_detail_id` | `TokenDeveloperPastTokensResponse`: other tokens from the developer |

## Find new pools

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    market = tapline.geckoterminal.global_stats()
    networks = tapline.geckoterminal.network_rankings()
    new_pools = tapline.geckoterminal.network_latest_pools("solana")

print(market.data.attributes.pools_count)
print([network.attributes.name for network in networks.data])
for pool in new_pools.data[:5]:
    print(pool.attributes.address, pool.attributes.name)
```

## Get candlesticks and swaps

```python
import time

from tapline import SyncTaplineClient

POOL = "Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE"
PAIR_ID = "1770231"
now = int(time.time())

with SyncTaplineClient() as tapline:
    candles = tapline.geckoterminal.candlesticks(
        "162714737",
        PAIR_ID,
        from_timestamp=now - 86_400,
        to_timestamp=now,
        resolution="15",
    )
    swaps = tapline.geckoterminal.pool_swaps(
        "solana",
        POOL,
        pair_id=PAIR_ID,
        page_after=str(now),
    )

for bar in candles.data:
    print(bar.dt, bar.o, bar.h, bar.l, bar.c, bar.v)
print(len(swaps.data))
```

Candlestick timestamps are Unix seconds. `pool_swaps` requires a cursor; start with the current Unix timestamp and continue with the response links.

## Inspect holders and traders

```python
from tapline import SyncTaplineClient

TOKEN = "AfGdjAp9djSaqJxzYo3t6jy8tJA3o2aDPHoZ57Egpump"

with SyncTaplineClient() as tapline:
    holders = tapline.geckoterminal.token_top_holders("solana", TOKEN)
    traders = tapline.geckoterminal.token_top_traders("124704000")

print(len(holders.data.attributes.top_holders))
print(len(traders.data))
```

## Follow trends and developer history

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    trends = tapline.geckoterminal.trends(network="solana")
    themes = tapline.geckoterminal.trending_themes(network="solana")
    history = tapline.geckoterminal.token_developer_past_tokens("13236719")

print(len(trends.data.attributes.new_pools))
print(len(themes.data))
print(history.data.attributes.past_tokens_count)
```

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). The [GeckoTerminal API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=geckoterminal_readme#/geckoterminal) lists the inputs, response fields, limits, and credit cost for each method.
