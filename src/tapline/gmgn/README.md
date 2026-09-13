# GMGN with the Tapline Python SDK

Use the GMGN client to find tokens, check security and market data, inspect holders and traders, and analyze wallets.

[Package guide](../../../README.md) · [GMGN API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=gmgn_readme#/gmgn)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=gmgn_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=gmgn_readme).

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

### Discovery and rankings

| Method | Key inputs | Returns |
| --- | --- | --- |
| `gas_price_list` | none | `GetGasPriceListResponse`: chain gas, priority/MEV tips, confirmation estimates, native USD prices |
| `hot_searches` | `requests` by chain | `GetHotSearchesResponse`: search-volume token rankings |
| `live_twitch_kol` | none | `GetLiveTwitchKolResponse`: live known-influencer Twitch channels by chain |
| `major_coin_prices` | `symbols` | `GetMajorCoinPricesResponse`: spot price per requested symbol |
| `trending_tokens` | `requests` by chain, interval, filters, launchpads, limit | `GetTrendingTokensResponse`: one leaderboard bucket per request |
| `activity_rank_info` | `chain` | `GetActivityRankInfoResponse`: trading-competition window and leaderboard |
| `bluechip_rank` | `chain`; optional `interval`, `limit`, `filters` | `GetBluechipRankResponse`: tokens ranked by blue-chip-holder share |
| `dex_trades_polling` | `chain`; optional `window` | `GetDexTradesPollingResponse`: DEX, launchpad, and protocol activity totals |
| `launchpad_tax_policy` | `chain` | `GetLaunchpadTaxPolicyResponse`: launchpad tax and trading-limit rules |
| `new_pairs` | `chain`; optional `interval`, `limit`, `order_by`, `filters`, `launchpad_platforms` | `GetNewPairsResponse`: new pairs with liquidity and launchpad data |
| `search` | `chain`, `q` | `SearchTokensResponse`: matching tokens and wallets |
| `similar_coin_extremes` | `chain`, `symbol`, `name`, `token_address` | `GetSimilarCoinExtremesResponse`: earliest and highest-market-cap lookalikes |
| `similar_coins` | `chain`, `symbol`, `name`, `token_address`; optional `order_by` | `GetSimilarCoinsResponse`: related names and symbols |
| `swap_rankings` | `chain`; optional `timeframe`, `platforms` | `GetSwapRankingsResponse`: tokens ranked by non-wash swap activity |
| `token_signals` | `chain`, `groups` | `GetTokenSignalsResponse`: tokens firing configured surge signals |
| `top_callers` | `chain`; optional `window` | `GetTopCallersResponse`: wallets ranked by public-call returns |
| `wallet_rankings` | `chain`; optional `period`, `order_by` | `GetWalletRankingsResponse`: smart-money leaderboard and daily profit history |

### Batch token profiles and prices

| Method | Key inputs | Returns |
| --- | --- | --- |
| `multi_token_full_info` | `chain`, `addresses` | `GetMultiTokenFullInfoResponse`: pool, security, creator, rug, trade, and ATH data |
| `multi_token_info` | `chain`, `addresses` | `GetMultiTokenInfoResponse`: batch token profiles |
| `multi_window_token_info` | `chain`, `addresses` | `GetMultiWindowTokenInfoResponse`: profiles and price movement across windows |
| `token_info_brief` | `chain`, `addresses` | `GetTokenInfoBriefResponse`: compact metadata, supply, liquidity, launchpad, honeypot flags |
| `token_prices` | `chain`, `addresses` | `GetTokenPricesResponse`: current batch prices |

### Token markets and trades

| Method | Key inputs | Returns |
| --- | --- | --- |
| `agged_token_trades` | `chain`, `token_address`; optional `period`, `tag` | `GetAggedTokenTradesResponse`: trades bucketed by time and wallet |
| `token_candles` | `chain`, `token_address`; optional `resolution`, `from_timestamp`, `to_timestamp`, `limit` | `GetTokenCandlesResponse`: price OHLCV |
| `mcap_candles` | `chain`, `token_address`; optional `resolution`, `limit` | `GetTokenMcapCandlesResponse`: market-cap OHLCV |
| `trades` | `chain`, `token_address`; optional `maker`, `cursor` | `GetTokenTradesResponse`: newest individual trades |
| `token_trades_v2` | `chain`, `token_address`; optional `maker`, `cursor` | `GetTokenTradesV2Response`: 50-trade multi-region page with maker tags |
| `token_trends` | `chain`, `token_address`; optional `trends_types` | `GetTokenTrendsResponse`: holder-structure time series |

### Token security, social, fees, and developer data

| Method | Key inputs | Returns |
| --- | --- | --- |
| `dev_created_tokens` | `chain`, `wallet_address` | `GetDevCreatedTokensResponse`: tokens launched by a developer and their ATHs |
| `token_ai_narrative` | `chain`, `token_address` | `GetTokenAiNarrativeResponse`: generated token narrative |
| `token_bundler_stat` | `chain`, `token_address` | `GetTokenBundlerStatResponse`: bundler wallets, swaps, holdings, ratios, volume |
| `token_community_messages` | `chain`, `token_address`; optional `limit` | `GetTokenCommunityMessagesResponse`: GMGN feed messages and authors |
| `token_dev_info` | `chain`, `token_address` | `GetTokenDevInfoResponse`: creator status, holdings, promotion, and launch history |
| `token_fee_distribution` | `chain`, `token_address` | `GetTokenFeeDistributionResponse`: launchpad fee split and claims |
| `token_fee_info` | `chain`, `token_address` | `GetTokenFeeInfoResponse`: pool fees plus security and launchpad summary |
| `live_preview` | `chain`, `token_address` | `GetLiveTokenPreviewResponse`: token live-stream card |
| `token_logo_history` | `chain`, `token_address` | `GetTokenLogoHistoryResponse`: historical logos and timestamps |
| `pool_fee_info` | `chain`, `token_address` | `GetTokenPoolFeeInfoResponse`: fee setup for every trading pool |
| `recommend_slippage` | `chain`, `token_address` | `GetRecommendSlippageResponse`: buy/sell slippage, tax flag, volatility |
| `security` | `chain`, `token_address` | `GetTokenSecurityResponse`: contract checks and launchpad |
| `socials` | `chain`, `token_address` | `GetTokenSocialsResponse`: social links, votes, and rug check |
| `stats` | `chain`, `token_address` | `GetTokenStatsResponse`: holder quality, concentration, bots, creator share |
| `website_info` | `chain`, `token_address` | `GetWebsiteInfoResponse`: declared URL, resolved IP, first-seen time |

### Holders, traders, and liquidity

| Method | Key inputs | Returns |
| --- | --- | --- |
| `token_holder_extra_info` | `chain`, `token_address`, `wallet_addresses` | `GetTokenHolderExtraInfoResponse`: holder funding trails, balances, ages, tags |
| `holder_stat` | `chain`, `token_address` | `GetTokenHolderStatResponse`: holder cohort counts |
| `holders` | `chain`, `token_address`; optional `limit`, `cost`, `order_by`, `direction`, `tag`, `cursor` | `GetTokenHoldersResponse`: sortable, filterable holder page |
| `liquidity` | `chain`, `token_address`; optional `limit`, `cursor` | `GetTokenLiquidityResponse`: add/remove events on Solana |
| `token_liquidity_stats` | `chain`, `token_address` | `GetTokenLiquidityStatsResponse`: liquidity-provider cohort counts |
| `token_liquidity_trend` | `chain`, `token_address` | `GetTokenLiquidityTrendResponse`: pool size and count on Solana |
| `top_buyers` | `chain`, `token_address` | `GetTopBuyersResponse`: earliest large buyers and current status |
| `trader_stat` | `chain`, `token_address` | `GetTokenTraderStatResponse`: trader cohort counts |
| `traders` | `chain`, `token_address`; optional `limit`, `order_by`, `direction`, `tag`, `cursor` | `GetTokenTradersResponse`: ranked, filterable trader page |
| `wallet_tags_stat` | `chain`, `token_address` | `GetTokenWalletTagsStatResponse`: wallet cohort counts among holders |

### Wallet analytics

| Method | Key inputs | Returns |
| --- | --- | --- |
| `agged_token_transfers` | `chain`, `token_address`, `wallet_address`; optional `period` | `GetAggedTokenTransfersResponse`: wallet transfers bucketed by time |
| `native_transfer` | `chain`, `wallet_address` | `GetNativeTransferResponse`: native-token funding transfer |
| `smart_money_wallet_info` | `chain`, `wallet_address` | `GetSmartMoneyWalletInfoResponse`: labels, socials, aggregate performance |
| `wallet_activity` | `chain`, `wallet_address`; optional `limit`, `type`, `cursor` | `GetWalletActivityResponse`: swaps and liquidity events |
| `wallet_chain_balances` | `chain`, `wallet_address` | `GetWalletChainBalancesResponse`: native balance and token count across chains |
| `wallet_common_stat` | `chain`, `wallet_address` | `GetWalletCommonStatResponse`: identity, provenance, socials, funder |
| `wallet_pnl` | `chain`, `wallet_address`; optional `period` | `GetSmartMoneyWalletResponse`: full smart-money P&L and risk flags |
| `wallet_stat` | `chain`, `wallet_address`; optional `period` | `GetWalletStatResponse`: broadly available wallet P&L window |

## Find tokens and rankings

```python
from tapline import SyncTaplineClient
from tapline.gmgn import Chain, TrendingChainRequest, TrendingInterval

with SyncTaplineClient() as tapline:
    trending = tapline.gmgn.trending_tokens(
        requests=[
            TrendingChainRequest(
                chain=Chain.SOL,
                interval=TrendingInterval.FIELD_1H,
                limit=20,
            )
        ]
    )
    matches = tapline.gmgn.search("sol", q="bonk")
    new_pairs = tapline.gmgn.new_pairs("sol", interval="1h", limit=20)
    wallets = tapline.gmgn.wallet_rankings("sol", period="7d")

print([coin.symbol for coin in matches.data.coins])
print(len(trending.data), len(new_pairs.data.pairs), len(wallets.data.rank))
```

## Check token security and price history

```python
from tapline import SyncTaplineClient

TOKEN = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"

with SyncTaplineClient() as tapline:
    security = tapline.gmgn.security("sol", TOKEN)
    candles = tapline.gmgn.token_candles("sol", TOKEN, resolution="1h", limit=48)
    prices = tapline.gmgn.token_prices("sol", addresses=[TOKEN])

print(security.data.security)
print(len(candles.data.list_), len(prices.data.list_))
```

## Inspect holders, traders, and liquidity

```python
from tapline import SyncTaplineClient

TOKEN = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"

with SyncTaplineClient() as tapline:
    holders = tapline.gmgn.holders("sol", TOKEN, limit=20)
    traders = tapline.gmgn.traders("sol", TOKEN, limit=20)
    liquidity = tapline.gmgn.liquidity("sol", TOKEN, limit=20)

print(len(holders.data.list_), len(traders.data.list_), len(liquidity.data.history))
```

`liquidity` and `token_liquidity_trend` are Solana-only. Use `token_liquidity_stats` for cohort coverage on other supported chains.

## Analyze a wallet

```python
from tapline import SyncTaplineClient

WALLET = "suqh5sHtr8HyJ7q8scBimULPkPpA557prMG47xCHQfK"

with SyncTaplineClient() as tapline:
    pnl = tapline.gmgn.wallet_stat("sol", WALLET, period="7d")
    activity = tapline.gmgn.wallet_activity("sol", WALLET, limit=20)
    identity = tapline.gmgn.wallet_common_stat("sol", WALLET)

print(pnl.data.realized_profit, pnl.data.realized_profit_pnl)
print(len(activity.data.activities), identity.data.name)
```

`wallet_pnl` and `smart_money_wallet_info` use GMGN's narrower smart-money backend. `wallet_stat` covers every GMGN chain and is the general fallback.

Pass cursor values back unchanged when you fetch another page.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). The [GMGN API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=gmgn_readme#/gmgn) lists the inputs, response fields, limits, and credit cost for each method.
