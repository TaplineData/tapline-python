from __future__ import annotations

import json
from typing import Any, Literal, cast, get_args

import httpx
from typing_extensions import TypedDict, override

from ._constants import REQUEST_ID_HEADER

__all__ = [
    "APIConnectionError",
    "APIError",
    "APIResponseValidationError",
    "APIStatusError",
    "APITimeoutError",
    "AuthenticationError",
    "BadRequestError",
    "ErrorCode",
    "ErrorDetail",
    "InsufficientCreditsError",
    "InternalServerError",
    "InvalidCursorError",
    "MissingAPIKeyError",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
    "TaplineError",
    "UnprocessableEntityError",
]

ErrorCode = Literal[
    "upstream_blocked",
    "upstream_unavailable",
    "upstream_response_invalid",
    "invalid_url_scheme",
    "invalid_url_host",
    "unauthenticated",
    "forbidden",
    "resource_forbidden",
    "not_found",
    "rate_limited",
    "invalid_request",
    "invalid_cursor",
    "insufficient_credits",
    "internal_error",
]
"""Every machine-readable ``code`` a Tapline error envelope can carry.

The server defines these itself and the set is closed, so this is the one place
they are enumerated: :class:`APIStatusError.code` is ``None`` for anything else,
including the bodies proxies and load balancers write.
"""

_ERROR_CODES: tuple[ErrorCode, ...] = get_args(ErrorCode)

_MAX_FALLBACK_MESSAGE_LENGTH = 200
_TRUNCATION_SUFFIX = " …"


class ErrorDetail(TypedDict, total=False):
    """One field-level diagnostic from an error envelope's ``details``.

    A 422 carries one entry per parameter that failed validation, shaped like a
    pydantic error. Every other status that populates ``details`` sends a single
    entry holding only ``msg``.
    """

    type: str | None
    loc: list[str | int] | None
    msg: str | None
    input: Any
    ctx: dict[str, Any] | None


class TaplineError(Exception):
    """Base class for every error this library raises."""


class MissingAPIKeyError(TaplineError):
    """Raised while constructing a client when no API key is available."""


class APIError(TaplineError):
    """Base class for every way a request can fail.

    Catch this for "this call did not work", whatever the reason. It excludes
    :class:`MissingAPIKeyError`, which is a configuration mistake raised by the
    constructor before anything is sent.
    """

    message: str

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class APIResponseValidationError(APIError):
    """Raised when a successful response does not match the expected schema.

    The API answered, so the failure is a contract mismatch rather than a
    caller mistake: report ``request_id`` when filing it.
    """

    response: httpx.Response
    status_code: int
    request_id: str | None

    def __init__(self, response: httpx.Response, message: str) -> None:
        super().__init__(message)
        self.response = response
        self.status_code = response.status_code
        self.request_id = response.headers.get(REQUEST_ID_HEADER)

    @override
    def __str__(self) -> str:
        return _with_request_id(self.message, self.request_id)


class APIConnectionError(APIError):
    """Raised when a request never yielded a response the client could read.

    Every way ``httpx`` can fail a request lands here: nothing answered, the
    answer did not arrive in time (:class:`APITimeoutError`), the redirects
    never ended, or the body could not be decoded. So does the one failure that
    precedes the send — a client that has already been closed.
    """

    request: httpx.Request

    def __init__(self, request: httpx.Request, *, message: str) -> None:
        super().__init__(message)
        self.request = request

    @override
    def __str__(self) -> str:
        return f"{self.message} ({self.request.method} {self.request.url})"


class APITimeoutError(APIConnectionError):
    """Raised when a request exceeded its timeout, including every retry.

    The message names the ``httpx`` timeout it came from, which is what says
    whether the deadline was hit connecting (the network never let us in) or
    reading (Tapline accepted the request and was still scraping).
    """


class APIStatusError(APIError):
    """Raised when the API answers with a non-2xx status.

    Attributes:
        status_code: The HTTP status.
        code: The :data:`ErrorCode` from the error envelope, e.g.
            ``resource_forbidden``. ``None`` when the body was not a Tapline
            error envelope (a proxy or load balancer answered instead), and
            also when it named a code released after this client version —
            ``body`` and ``str()`` still carry that one verbatim.
        message: The human-readable explanation.
        request_id: Identifier to quote when reporting the failure.
        domain: The product the failure came from, e.g. ``youtube``.
        details: Field-level diagnostics, populated for validation failures.
        response: The raw ``httpx`` response.
        body: The decoded response body — a ``dict`` for an error envelope, the
            raw text when the body was not JSON, ``None`` when it was empty.
    """

    status_code: int
    code: ErrorCode | None
    request_id: str | None
    domain: str | None
    details: list[ErrorDetail] | None
    response: httpx.Response
    body: object | None

    def __init__(
        self,
        message: str,
        *,
        response: httpx.Response,
        code: ErrorCode | None,
        request_id: str | None,
        domain: str | None,
        details: list[ErrorDetail] | None,
        body: object | None,
    ) -> None:
        super().__init__(message)
        self.response = response
        self.status_code = response.status_code
        self.code = code
        self.request_id = request_id
        self.domain = domain
        self.details = details
        self.body = body

    @override
    def __str__(self) -> str:
        prefix = str(self.status_code)
        # Quote the code the server sent, not the one this version recognises.
        sent_code = _text_field(self.body, "code")
        if sent_code:
            prefix += f" {sent_code}"
        if self.domain:
            prefix += f" [{self.domain}]"
        return _with_request_id(f"{prefix}: {self.message}", self.request_id)


class BadRequestError(APIStatusError):
    """400 — the request itself is malformed. Codes: ``invalid_request``,
    ``invalid_cursor``, ``invalid_url_scheme``, ``invalid_url_host``."""


class InvalidCursorError(BadRequestError):
    """400 ``invalid_cursor`` — the pagination cursor is malformed, expired, or
    bound to a different resource.

    Cursors expire during long walks, so this is routine rather than
    exceptional: restart the walk from the first page.
    """


class AuthenticationError(APIStatusError):
    """401 ``unauthenticated`` — the API key is missing or invalid."""


class InsufficientCreditsError(APIStatusError):
    """402 ``insufficient_credits`` — the account cannot pay for this request."""


class PermissionDeniedError(APIStatusError):
    """403 — access is refused. ``forbidden`` means no subscription grants access
    to the product; ``resource_forbidden`` means the YouTube resource itself is
    private, age-gated, members-only, or region-blocked."""


class NotFoundError(APIStatusError):
    """404 ``not_found`` — no such video, channel, playlist, or subtitle track."""


class UnprocessableEntityError(APIStatusError):
    """422 ``invalid_request`` — a parameter failed server-side validation.
    ``details`` names the offending fields."""


class RateLimitError(APIStatusError):
    """429 ``rate_limited`` — too many requests. Retried automatically, honoring
    ``Retry-After``, until ``max_retries`` is exhausted."""


class InternalServerError(APIStatusError):
    """5xx — the failure is on the server side. ``internal_error`` (500) is a
    Tapline fault; ``upstream_unavailable`` / ``upstream_response_invalid`` (502)
    and ``upstream_blocked`` (503) mean YouTube is refusing to cooperate."""


_STATUS_ERRORS: dict[int, type[APIStatusError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    402: InsufficientCreditsError,
    403: PermissionDeniedError,
    404: NotFoundError,
    422: UnprocessableEntityError,
    429: RateLimitError,
}

_CODE_ERRORS: dict[tuple[int, ErrorCode], type[APIStatusError]] = {
    (400, "invalid_cursor"): InvalidCursorError,
}


def make_status_error(response: httpx.Response) -> APIStatusError:
    """Build the most specific error class for a non-2xx response.

    The error code refines the status where a status alone is ambiguous, and
    anything that is not a Tapline error envelope still yields a typed error
    carrying the raw body and the request id from the response headers.
    """
    body = _decode_body(response)
    code = _error_code(body)
    error_class = _error_class(response.status_code, code)
    return error_class(
        _text_field(body, "message") or _fallback_message(response, body),
        response=response,
        code=code,
        request_id=_text_field(body, "request_id") or response.headers.get(REQUEST_ID_HEADER),
        domain=_text_field(body, "domain"),
        details=_details(body),
        body=body,
    )


def make_request_error(error: httpx.RequestError, request: httpx.Request) -> APIConnectionError:
    """Translate an ``httpx`` request failure into a library error.

    ``httpx.RequestError`` is every way sending can fail, so translating the
    base class is what keeps a raw ``httpx`` exception from reaching a caller.
    """
    cause = f"{type(error).__name__}: {error}" if str(error) else type(error).__name__
    if isinstance(error, httpx.TimeoutException):
        return APITimeoutError(request, message=f"Request timed out — {cause}")
    return APIConnectionError(request, message=f"Request failed — {cause}")


def _error_class(status_code: int, code: ErrorCode | None) -> type[APIStatusError]:
    if code is not None and (refined := _CODE_ERRORS.get((status_code, code))):
        return refined
    if status_code >= 500:
        return InternalServerError
    return _STATUS_ERRORS.get(status_code, APIStatusError)


def _decode_body(response: httpx.Response) -> object | None:
    text = response.text.strip()
    if not text:
        return None
    try:
        decoded: object = json.loads(text)
    except ValueError:
        return text
    return decoded


def _error_code(body: object) -> ErrorCode | None:
    code = _text_field(body, "code")
    return next((known for known in _ERROR_CODES if known == code), None)


def _fallback_message(response: httpx.Response, body: object | None) -> str:
    if isinstance(body, str):
        return _shorten(body)
    return response.reason_phrase or f"HTTP {response.status_code}"


def _shorten(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= _MAX_FALLBACK_MESSAGE_LENGTH:
        return collapsed
    keep = _MAX_FALLBACK_MESSAGE_LENGTH - len(_TRUNCATION_SUFFIX)
    return collapsed[:keep] + _TRUNCATION_SUFFIX


def _with_request_id(message: str, request_id: str | None) -> str:
    return f"{message} (request_id={request_id})" if request_id else message


def _text_field(body: object, key: str) -> str | None:
    value = body.get(key) if isinstance(body, dict) else None
    return value if isinstance(value, str) else None


def _details(body: object) -> list[ErrorDetail] | None:
    details = body.get("details") if isinstance(body, dict) else None
    if not isinstance(details, list):
        return None
    return [cast("ErrorDetail", entry) for entry in details if isinstance(entry, dict)]
