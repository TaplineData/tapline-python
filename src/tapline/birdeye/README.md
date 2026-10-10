# Birdeye with the Tapline Python SDK

Use the Birdeye client to read birdeye.so's token and wallet data: market overviews, security checks, trades, candles, pools, trending tokens and launchpad listings on Solana and seven EVM chains, plus trader leaderboards and wallet PnL.

[Package guide](../../../README.md) · [Birdeye API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=birdeye_readme#/birdeye)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=birdeye_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=birdeye_readme).

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

Token routes take `solana`, `ethereum`, `base`, `bsc`, `arbitrum`, `avalanche`, `optimism` or `polygon`. The PnL routes take `solana`, `ethereum`, `base` or `bsc`. Holders, first buyers, portfolio and net-worth history are Solana only.

| Method | Key inputs | Returns | Credits |
| --- | --- | --- | --- |
| `get_token_overview` | `chain`, `address` | price, market cap, liquidity, supply, holders, socials, and buy, sell, volume and wallet counts per window | 1 |
| `get_token_security` | `chain`, `address` | security checks grouped by severity, with birdeye and GoPlus results keyed by row `index` | 1 |
| `list_token_trades` | `chain`, `address`, `side`, `limit` (up to 50), `cursor` | trade and liquidity events, newest first | 1 |
| `get_token_ohlcv` | `chain`, `address`, `interval` (`1s` to `1mo`), `count` (up to 1000), `to` | parallel `o`, `h`, `l`, `c`, `v`, `t` arrays | 1 |
| `list_token_markets` | `chain`, `address`, `sort_by`, `order` | up to 300 pools with venue, liquidity and 24h volume | 1 |
| `list_top_traders` | `chain` (PnL chains), `address`, `sort_by`, `order`, `limit`, `cursor` | wallets ranked by PnL on the token | 2 |
| `list_trending_tokens` | `chain` or `all` | birdeye's 20 trending tokens | 1 |
| `list_new_listings` | `chain`, `stage` (`new`, `final_curve`, `migrated`) | up to 30 launchpad tokens | 1 |
| `list_leaderboard` | `chain` (PnL chains), `interval`, `sort_by`, `order`, `limit`, `cursor` | the trader leaderboard | 2 |
| `get_wallet_pnl_summary` | `chain` (PnL chains), `wallet`, `period` | realized, unrealized and total PnL, volumes, trade counts, return buckets | 2 |
| `list_wallet_tokens` | `chain` (PnL chains), `wallet`, `sort_by`, `order`, `limit`, `cursor` | per-token PnL for every token the wallet traded | 2 |
| `list_wallet_transactions` | `chain` (PnL chains), `wallet`, `token`, `limit`, `cursor` | the wallet's swaps, newest first | 2 |
| `list_token_holders` | `address` (Solana) | top 100 holders with net worth, SOL balance and funding source | 2 |
| `list_first_buyers` | `address` (Solana) | the first buyers and what each did since | 2 |
| `list_wallet_portfolio` | `wallet` (Solana), `limit`, `cursor` | current holdings by USD value and the wallet's total | 2 |
| `get_net_worth_history` | `wallet` (Solana), `interval` (`1h`, `1d`), `count` (up to 90) | net worth points, newest first | 2 |

Paged methods cost their credits per page, not per item.

## Read a token's overview

```python
overview = tapline.birdeye.get_token_overview(
    "solana", "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN"
)
print(overview.symbol, overview.price, overview.liquidity, overview.holder)
```

## Page through trades

```python
cursor = ""
while True:
    page = tapline.birdeye.list_token_trades(
        "solana", "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN", side="buy", cursor=cursor
    )
    for trade in page.items:
        print(trade.txHash, trade.volumeUSD)
    if page.pagination.next_cursor is None:
        break
    cursor = page.pagination.next_cursor
```

## Read a wallet's PnL

```python
summary = tapline.birdeye.get_wallet_pnl_summary(
    "base", "0x3304e22ddaa22bcdc5fca2269b418046ae7b566a", period="7d"
)
print(summary.total_pnl, summary.realized_pnl, summary.tx_count)
```

## Read the response

- Paged methods return `items` and `pagination`. Pass `pagination.next_cursor` back as `cursor` until it is null. `pagination.completion` is `exhausted` at the end, or `depth_limit` where birdeye stops serving deeper pages (trades stop after offset 9,000).
- The trade tape moves while you page, so dedupe trades by `id`.
- EVM addresses may be sent in any case; the API checksums them for birdeye.
- birdeye leaves out fields that are zero, false or empty on the wallet and trader methods, so read them as optional.
- Counts and unix times on the wallet methods arrive as strings, as birdeye sends them. Parse them before you compare.
- An unknown token answers 404 on `get_token_overview` and an empty list on the list methods. Both are charged.

## Handle errors and check costs

Failed calls throw the errors described in the [package guide](../../../README.md#handle-errors). Validation errors (a Solana address on an EVM chain, an unknown enum value, a cursor this API did not issue) are not charged. When birdeye has not computed a token's security checks yet, `get_token_security` fails with status 503 and is not charged; retry in a minute.

The [Birdeye API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=birdeye_readme#/birdeye) lists the inputs, response fields, and credit cost for each method.
