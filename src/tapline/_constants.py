from __future__ import annotations

import platform

import httpx

from ._version import __version__

API_KEY_ENV_VAR = "TAPLINE_API_KEY"
API_KEY_HEADER = "X-API-Key"
REQUEST_ID_HEADER = "X-Request-ID"

DEFAULT_BASE_URL = "https://api.tapline.sh"

# Every endpoint proxies YouTube in-band: a cold search runs ~8s, subtitles and
# comment walks longer. A conventional 10s default would time out valid requests.
DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)
DEFAULT_MAX_RETRIES = 2
DEFAULT_CONNECTION_LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20)

# What `httpx.Client()` times out at when nobody passed `timeout=`, so a caller
# who supplied a client carrying this value did not choose it. See
# `_base_client._resolve_timeout`.
HTTPX_DEFAULT_TIMEOUT = httpx.Timeout(5.0)

INITIAL_RETRY_DELAY = 0.5
MAX_RETRY_DELAY = 8.0

# Beyond this, obeying `Retry-After` would stall the caller longer than a
# failure would; fall back to bounded backoff instead.
MAX_HONORED_RETRY_AFTER = 60.0

USER_AGENT = f"tapline-python/{__version__} (python/{platform.python_version()})"
