# Pons Family with the Tapline Python SDK

Use the Pons Family client to read the pons launchpad on Robinhood Chain: the launch board, token markets, charts, trades and holders, wallet positions, creator fees, and the memestock forum.

[Package guide](../../../README.md) · [Pons Family API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=ponsfamily_readme#/ponsfamily)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=ponsfamily_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=ponsfamily_readme).

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

Pons has two kinds of launch. Every `Launch` carries a `version`: read `v2` (curve) launches with the `get_v2_market_*` methods and `v1` tokens, such as PONS itself, with the `get_market_*` methods.

### Launches and protocol data

| Method | Key inputs | Returns |
| --- | --- | --- |
| `list_launches` | optional `sort`, `age`, `version`, `page`, `page_size`, `include_graduated`, `graduated_page`, `graduated_page_size` | `ListLaunchesResponse`: the active board and a page of graduated launches |
| `search_launches` | optional `q`, `sort`, `age`, `page` | `SearchLaunchesResponse`: launches matching a name, symbol, or address |
| `list_graduations` | none | `list[Graduation]`: every graduation with its block |
| `list_graduated_catalog` | none | `list[Launch]`: graduated tokens as full launch records |
| `list_live_markets` | optional `markets` | `list[LiveMarket]`: price and graduation progress for the launches currently trading |
| `get_analytics` | none | `GetAnalyticsResponse`: launch, volume, and revenue totals plus a daily series |
| `get_eth_price` | none | `GetEthPriceResponse`: the ETH/USD rate pons prices launches with |
| `list_cto_migrations` | none | `ListCtoMigrationsResponse`: community-takeover migrations and their schedules |

### v2 launch markets

| Method | Key inputs | Returns |
| --- | --- | --- |
| `get_v2_market_trades` | `token` | `GetV2MarketTradesResponse`: trades in the launch's quote asset |
| `get_v2_market_chart` | `token`; optional `range` | `GetV2MarketChartResponse`: price and volume points with the quote asset's USD rate |
| `get_v2_market_holders` | `token` | `GetV2MarketHoldersResponse`: ranked holders and supply shares |
| `get_v2_creator_fees` | `token` | `GetV2CreatorFeesResponse`: fee recipient, escrow, and fees earned so far |
| `get_v2_distributor` | `token` | `GetV2DistributorResponse`: holder fee-sharing state and the latest payout epoch |

### v1 token markets

| Method | Key inputs | Returns |
| --- | --- | --- |
| `get_market` | `token`; optional `include_holders` | `GetMarketResponse`: price, market cap, liquidity, recent trades, and price points |
| `get_market_trades` | `token` | `list[MarketTrade]`: the latest buys and sells against the pool |
| `get_market_chart` | `token`; optional `range` | `GetMarketChartResponse`: bucketed price and volume points |
| `get_market_holders` | `token` | `GetMarketHoldersResponse`: ranked holders with balance and PnL |
| `get_market_ath` | `token` | `GetMarketAthResponse`: all-time-high price and its block |
| `get_market_tip` | `token` | `GetMarketTipResponse`: the latest pool price |
| `get_market_burned` | `token` | `GetMarketBurnedResponse`: supply burned, in wei |
| `get_market_order_depth` | `token` | `GetMarketOrderDepthResponse`: resting limit orders bucketed into price bands |
| `get_developer_trades` | `token`, `deployer` | `GetDeveloperTradesResponse`: what the deployer bought, sold, moved, and burned |

### Tokens

| Method | Key inputs | Returns |
| --- | --- | --- |
| `get_token` | `token` | `GetTokenResponse`: supply, socials, pool wiring, and deployer |
| `get_token_images` | `tokens` (up to 100) | `GetTokenImagesResponse`: logo URL keyed by lower-cased token address, in `.root` |
| `get_fee_sharing` | `tokens` (up to 100) | `GetFeeSharingResponse`: whether each token routes creator fees to holders |
| `get_creator_holdings` | `pairs` of `CreatorHoldingPair(token=..., deployer=...)` (up to 100) | `GetCreatorHoldingsResponse`: the share of supply each deployer still holds |

### Wallets

| Method | Key inputs | Returns |
| --- | --- | --- |
| `get_wallet_positions` | `address` | `GetWalletPositionsResponse`: open and closed positions, trade activity, and PnL totals |
| `get_portfolio_chart` | `address`; optional `range` | `GetPortfolioChartResponse`: portfolio value over time |
| `get_profile` | `address` | `GetProfileResponse`: launches the wallet deployed or earns fees from, with claimable fees |
| `get_wallet_identities` | `addresses` (up to 100) | `GetWalletIdentitiesResponse`: public pons usernames, avatars, and bios |

### Memestock forum

| Method | Key inputs | Returns |
| --- | --- | --- |
| `list_forum_posts` | optional `sort`, `community` | `ListForumPostsResponse`: the forum feed |
| `get_forum_post` | `post_id` | `GetForumPostResponse`: one post with its votes and community |
| `get_forum_post_comments` | `post_id`; optional `sort` | `GetForumPostCommentsResponse`: the comment thread, replies nested |
| `list_forum_communities` | optional `rank`, `limit` | `ListForumCommunitiesResponse`: token communities ranked by market cap or burn |
| `get_forum_community` | `slug` | `GetForumCommunityResponse`: one community's supply, burn, and market cap |
| `get_forum_holding` | `token`, `wallet` | `GetForumHoldingResponse`: a wallet's balance and the posting tier it earns |
| `get_forum_market` | none | `GetForumMarketResponse`: US market session, community ticker rows, and tracked equities |

## Browse the launch board

```python
from tapline import SyncTaplineClient
from tapline.ponsfamily import LaunchSort

with SyncTaplineClient() as tapline:
    board = tapline.ponsfamily.list_launches(sort=LaunchSort.VOLUME, page_size=10)
    found = tapline.ponsfamily.search_launches(q="pons")

active = board.active.items if board.active else None
for launch in active or []:
    print(launch.symbol, launch.version, launch.token, launch.marketCapUsd)
print(found.total)
```

## Read a v2 launch's market

```python
from tapline import SyncTaplineClient

TOKEN = "0xD5f1afEA47b1A9eab414D2ee740cF1d6d039E725"

with SyncTaplineClient() as tapline:
    chart = tapline.ponsfamily.get_v2_market_chart(TOKEN, range="1d")
    trades = tapline.ponsfamily.get_v2_market_trades(TOKEN)
    holders = tapline.ponsfamily.get_v2_market_holders(TOKEN)

print(chart.quoteSymbol, len(chart.points or []))
for trade in (trades.trades or [])[:5]:
    print(trade.side, trade.account, trade.tokenAmount)
print(holders.holdersCount)
```

## Follow a wallet

```python
from tapline import SyncTaplineClient

WALLET = "0x42e9c498135431a48796B5fFe2CBC3d7A1811927"

with SyncTaplineClient() as tapline:
    positions = tapline.ponsfamily.get_wallet_positions(WALLET)
    chart = tapline.ponsfamily.get_portfolio_chart(WALLET, range="7d")

if positions.totals:
    print(positions.totals.portfolioValueUsd, positions.totals.totalPnlUsd)
for position in positions.positions or []:
    print(position.symbol, position.state, position.valueUsd)
print(chart.changePct)
```

## Read the memestock forum

```python
from tapline import SyncTaplineClient

with SyncTaplineClient() as tapline:
    feed = tapline.ponsfamily.list_forum_posts(sort="top")
    for post in (feed.posts or [])[:3]:
        if post.id:
            thread = tapline.ponsfamily.get_forum_post_comments(post.id)
            print(post.title, post.communitySymbol, len(thread.comments or []))
```

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). The [Pons Family API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=ponsfamily_readme#/ponsfamily) lists the inputs, response fields, limits, and credit cost for each method.
