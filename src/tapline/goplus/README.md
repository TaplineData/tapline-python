# GoPlus Security with the Tapline Python SDK

Use the GoPlus client to check a token before you trade or list it: honeypot and tax flags, owner and mint powers, top holders, and liquidity for EVM and Tron tokens and Solana mints.

[Package guide](../../../README.md) · [GoPlus API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=goplus_readme#/goplus)

## Get started

[Create a Tapline account](https://tapline.sh/sign-up?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=goplus_readme) and create an API key on the [API keys page](https://tapline.sh/dashboard?tab=api-keys&utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=goplus_readme).

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

Each call costs 3 credits.

| Method | Key inputs | Returns |
| --- | --- | --- |
| `get_evm_token_security` | `chain_id` (`"1"` Ethereum, `"56"` BNB Chain, `"137"` Polygon, `"8453"` Base, `"42161"` Arbitrum, and 38 more in `GoplusChainId`), `address` | `GetEvmTokenSecurityResponse`: honeypot, tax, owner, mint and proxy flags, top holders, LP holders, DEX pools, CEX listings |
| `get_solana_token_security` | `mint` | `GetSolanaTokenSecurityResponse`: mint, freeze, close and metadata authorities, Token-2022 transfer fee and hook, top holders, DEX pools |
| `get_tron_token_security` | `address` (base58, starts with `T`) | `GetTronTokenSecurityResponse`: honeypot, tax, owner and mint flags, blacklist, top holders, CEX listings |

## Check an EVM token

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

`chain_id` takes any of the 43 EVM chains GoPlus supports. `GoplusChainId` in `tapline.goplus` names them all, so `GoplusChainId.ARBITRUM` works in place of `"42161"`.

## Check a Solana mint

```python
from tapline import SyncTaplineClient

mint = "66UokDvAUWuT8DiX1JxAyisx3uo4nErZYQocXTowQm2G"

with SyncTaplineClient() as tapline:
    security = tapline.goplus.get_solana_token_security(mint)

token = (security.result or {}).get(mint)
if token is None:
    print("GoPlus has no data for this mint")
else:
    symbol = token.metadata.symbol if token.metadata else None
    mint_authority_live = token.mintable.status if token.mintable else None
    print(symbol, mint_authority_live)
```

## Check a Tron token

```python
from tapline import SyncTaplineClient

address = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"

with SyncTaplineClient() as tapline:
    security = tapline.goplus.get_tron_token_security(address)

token = (security.result or {}).get(address)
if token is None:
    print("GoPlus has no token at this address")
else:
    print(token.token_symbol, token.is_honeypot, token.is_blacklisted, token.trust_list)
```

## Read the response

The response is GoPlus's own envelope, returned unchanged:

- `code` is `1` for complete data and `2` for partial data. After a `2`, ask again in about 15 seconds for the rest. Code `3` also passes through as it is.
- `result` is keyed by the lowercased EVM address, by the Solana mint, or by the Tron address in its original case. Look up a Tron token with the exact string you sent, and never lowercase a Tron address.
- `result` is empty when GoPlus has no token at that address on that chain, such as an Ethereum token queried on chain `"56"` or an EVM wallet address. That call still costs 3 credits.
- Security flags are strings. `"1"` means yes, `"0"` means no, and `""` means GoPlus does not know. Do not read `""` as `"0"`.
- A Tron token has the same fields as an EVM token. `trust_list` is `"1"` for a token GoPlus marks as trusted. It appears on Tron tokens and on some EVM tokens.
- `is_contract`, `is_locked`, `malicious_address`, and `trusted_token` are `0` or `1` integers, and `burn_percent` is a float.
- GoPlus leaves out fields it has no value for, so every field is optional.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). Calls that fail upstream are not charged, including these two:

- An address GoPlus rejects, such as a Solana wallet or another account that is not a token, raises `BadRequestError` with status 400 and code `invalid_request`.
- If GoPlus rate-limits the last proxy attempt, the call raises `RateLimitError` with status 429 and code `rate_limited`. The client retries a 429 on its own before it raises.

The [GoPlus API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=goplus_readme#/goplus) lists the inputs, response fields, and credit cost for each method.

Powered by GoPlus Security.
