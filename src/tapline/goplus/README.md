# GoPlus Security with the Tapline Python SDK

Use the GoPlus client to check a token before you trade or list it: honeypot and tax flags, owner and mint powers, top holders, and liquidity for EVM tokens and Solana mints.

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
| `get_evm_token_security` | `chain_id` (`"1"` Ethereum, `"56"` BNB Chain, `"8453"` Base, `"4663"` Robinhood Chain), `address` | `GetEvmTokenSecurityResponse`: honeypot, tax, owner, mint and proxy flags, top holders, LP holders, DEX pools, CEX listings |
| `get_solana_token_security` | `mint` | `GetSolanaTokenSecurityResponse`: mint, freeze, close and metadata authorities, Token-2022 transfer fee and hook, top holders, DEX pools |

## Check an EVM token

```python
from tapline import SyncTaplineClient

address = "0x6982508145454ce325ddbe47a25d4ec3d2311933"

with SyncTaplineClient() as tapline:
    security = tapline.goplus.get_evm_token_security("1", address)

token = (security.result or {})[address]
print(token.token_symbol, token.is_honeypot, token.buy_tax, token.sell_tax)
```

## Check a Solana mint

```python
from tapline import SyncTaplineClient

mint = "66UokDvAUWuT8DiX1JxAyisx3uo4nErZYQocXTowQm2G"

with SyncTaplineClient() as tapline:
    security = tapline.goplus.get_solana_token_security(mint)

token = (security.result or {})[mint]
symbol = token.metadata.symbol if token.metadata else None
mint_authority_live = token.mintable.status if token.mintable else None
print(symbol, mint_authority_live)
```

## Read the response

The response is GoPlus's own envelope:

- `code` is `1` for complete data, `2` for partial data (retry in about 15 seconds for the rest), and `3` when the address has no contract code.
- `result` is keyed by the lowercased EVM address or by the Solana mint.
- Values are strings. `"0"` and `"1"` are flags, and `""` means GoPlus does not know. Do not read `""` as zero.
- GoPlus leaves out fields it has no value for, so every field is optional.

## Handle errors and check costs

Failed calls raise the errors described in the [package guide](../../../README.md#handle-errors). Calls that fail upstream are not charged. The [GoPlus API reference](https://tapline.sh/docs?utm_source=python_client&utm_medium=referral&utm_campaign=developer_acquisition&utm_content=goplus_readme#/goplus) lists the inputs, response fields, and credit cost for each method.

Powered by GoPlus Security.
