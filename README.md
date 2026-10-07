# tapline

Use `tapline` to collect live data from YouTube, Airbnb, GMGN, GeckoTerminal, GoPlus Security, Pons Family, and Twitter (X) in Python.

[![PyPI](https://img.shields.io/pypi/v/tapline)](https://pypi.org/project/tapline/)
[![Python](https://img.shields.io/pypi/pyversions/tapline)](https://pypi.org/project/tapline/)
[![License](https://img.shields.io/pypi/l/tapline)](https://github.com/TaplineData/tapline-python/blob/main/LICENSE)

## What you can do

| Service | Use it to | Full guide |
| --- | --- | --- |
| YouTube | Get transcripts, search videos, read video and channel details, list playlists, collect comments, inspect formats, and read replay heatmaps | [YouTube guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/youtube/README.md) |
| Airbnb | Find locations and listings, check prices and availability, and read listing details and reviews | [Airbnb guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/airbnb/README.md) |
| GMGN | Find tokens, check security and market data, inspect holders and traders, and analyze wallets | [GMGN guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/gmgn/README.md) |
| GeckoTerminal | Find pools, read candlesticks and swaps, inspect holders and traders, and follow market trends | [GeckoTerminal guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/geckoterminal/README.md) |
| GoPlus Security | Check EVM and Tron tokens and Solana mints for honeypots, taxes, owner and mint powers, holders, and liquidity | [GoPlus guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/goplus/README.md) |
| Pons Family | Browse and search launches, read token markets, trades and holders, follow wallets and creator fees, and read the memestock forum | [Pons Family guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/ponsfamily/README.md) |
| Twitter (X) | Read public X profiles with their pinned and newest posts, single posts with media, quotes and top replies, and X Communities | [Twitter guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/twitter/README.md) |

One API key and credit balance work across all seven services.

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=main_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=main_readme).

Install the package and save your key in `TAPLINE_API_KEY`:

```sh
pip install tapline
export TAPLINE_API_KEY="your-api-key"
```

Pass a key from your environment or secret manager as `api_key=` when you create either the blocking or async client:

```python
import os

from tapline import SyncTaplineClient, TaplineClient

api_key = os.environ["TAPLINE_API_KEY"]
sync_tapline = SyncTaplineClient(api_key=api_key)
async_tapline = TaplineClient(api_key=api_key)
```

If you omit `api_key`, both clients read `TAPLINE_API_KEY`. Python 3.10 or newer is required.

## Get a transcript

```python
import os

from tapline import SyncTaplineClient

with SyncTaplineClient(api_key=os.environ["TAPLINE_API_KEY"]) as tapline:
    subtitles = tapline.youtube.subtitles(
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        language="en",
        subtitle_format="txt",
    )

print(subtitles.transcript)
```

See the [YouTube guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/youtube/README.md) for search, metadata, channels, playlists, comments, formats, and replay heatmaps.

## Search Airbnb listings

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    places = tapline.airbnb.search_locations(query="London")
    place_id = places.suggestions[0].place_id
    if place_id is None:
        raise RuntimeError("Airbnb returned a location without a place_id")
    results = tapline.airbnb.search(
        place_id=place_id,
        adults=2,
    )

for listing in results.listings:
    print(listing.room_id, listing.name)
```

Listing IDs can stop resolving when a host removes a property. See the [Airbnb guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/airbnb/README.md) for prices, availability, details, reviews, and search filters.

## Search GMGN token data

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    results = tapline.gmgn.search("sol", q="bonk")

for token in results.data.coins[:5]:
    print(token.symbol, token.address)
```

See the [GMGN guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/gmgn/README.md) for discovery, rankings, security, candles, holders, traders, liquidity, and wallet analytics.

## Discover GeckoTerminal pools

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    pools = tapline.geckoterminal.network_latest_pools("solana")

for pool in pools.data[:5]:
    print(pool.attributes.address, pool.attributes.name)
```

See the [GeckoTerminal guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/geckoterminal/README.md) for pool, token, trend, and developer history data.

## Check token security with GoPlus

```python
from tapline import SyncTaplineClient

address = "0x6982508145454ce325ddbe47a25d4ec3d2311933"

with SyncTaplineClient() as tapline:
    security = tapline.goplus.get_evm_token_security("1", address)

token = (security.result or {}).get(address)
if token is None:
    print("GoPlus has no token at this address on this chain")
else:
    print(token.token_symbol, token.is_honeypot, token.buy_tax, token.sell_tax)
```

The first argument, `chain_id`, takes any of the 43 EVM chains GoPlus supports, such as `"56"` for BNB Chain or `"42161"` for Arbitrum. `result` is empty when GoPlus has no token at that address on that chain. Each call costs 3 credits, even one that comes back empty. `""` means GoPlus does not know a value, so do not read it as zero. See the [GoPlus guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/goplus/README.md) for Solana mints, Tron tokens, and how to read the response.

## Browse Pons Family launches

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    board = tapline.ponsfamily.list_launches(sort="volume", page_size=5)

active = board.active.items if board.active else None
for launch in active or []:
    print(launch.symbol, launch.token, launch.marketCapUsd)
```

See the [Pons Family guide](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/ponsfamily/README.md) for token markets, charts, holders, wallets, creator fees, and the memestock forum.

## Go beyond the free tier

Your free account starts with 500 credits and can use every live endpoint. When you need more credits or higher rate limits, choose a paid plan under [Billing](https://tapline.sh/dashboard?tab=billing&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=main_readme). Your API key and code stay the same.

## Async client

Every service method has the same name and arguments on `TaplineClient`; only the call becomes awaitable.

```python
import asyncio

from tapline import TaplineClient


async def main() -> None:
    async with TaplineClient() as tapline:
        metadata = await tapline.youtube.metadata("dQw4w9WgXcQ")
        print(metadata.title)


asyncio.run(main())
```

## Handle errors

Failed requests raise an `APIStatusError`. Use its status, error code, and request ID to decide what to do or to contact support.

```python
from tapline import APIStatusError, SyncTaplineClient

try:
    with SyncTaplineClient() as tapline:
        tapline.youtube.metadata("not-a-video")
except APIStatusError as error:
    print(error.status_code, error.code, error.request_id)
```

Authentication, credit, rate-limit, timeout, and connection failures also have their own exception classes. The client retries temporary network and server failures.

## Full API reference

Use the [Tapline API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=main_readme) to check inputs, response fields, and the credit cost of each call.

- [YouTube](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/youtube/README.md)
- [Airbnb](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/airbnb/README.md)
- [GMGN](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/gmgn/README.md)
- [GeckoTerminal](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/geckoterminal/README.md)
- [GoPlus Security](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/goplus/README.md)
- [Pons Family](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/ponsfamily/README.md)
- [Twitter (X)](https://github.com/TaplineData/tapline-python/blob/main/src/tapline/twitter/README.md)

## License

MIT
