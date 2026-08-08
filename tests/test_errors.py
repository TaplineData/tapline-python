"""What the client raises: for every failure the API answers with, and for the
failures ``httpx`` raises on its own behalf."""

from __future__ import annotations

from typing import get_args

import httpx
import pytest

from conftest import TEST_API_KEY, VIDEO_ID, ClientClass, Engine, MockAPI
from spec import youtube_paths
from tapline import (
    APIConnectionError,
    APIResponseValidationError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    ErrorCode,
    InsufficientCreditsError,
    InternalServerError,
    InvalidCursorError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    SyncTaplineClient,
    TaplineError,
    UnprocessableEntityError,
)

REQUEST_ID = "req_01JBTAPLINE"
METADATA_PATH = f"/api/v1/youtube/videos/{VIDEO_ID}/metadata"

DOCUMENTED_ERRORS = frozenset(
    error for path in youtube_paths() if not path.is_demo for error in path.errors
)

STATUS_ERRORS = [
    (400, "invalid_request", BadRequestError),
    (400, "invalid_url_scheme", BadRequestError),
    (400, "invalid_url_host", BadRequestError),
    (400, "invalid_cursor", InvalidCursorError),
    (401, "unauthenticated", AuthenticationError),
    (402, "insufficient_credits", InsufficientCreditsError),
    (403, "forbidden", PermissionDeniedError),
    (403, "resource_forbidden", PermissionDeniedError),
    (404, "not_found", NotFoundError),
    (422, "invalid_request", UnprocessableEntityError),
    (429, "rate_limited", RateLimitError),
    (500, "internal_error", InternalServerError),
    (502, "upstream_unavailable", InternalServerError),
    (502, "upstream_response_invalid", InternalServerError),
    (503, "upstream_blocked", InternalServerError),
]


def envelope(
    status: int,
    code: str,
    *,
    message: str = "Something went wrong.",
    request_id: str | None = REQUEST_ID,
    domain: str | None = "youtube",
    details: list[dict[str, object]] | None = None,
) -> httpx.Response:
    body: dict[str, object] = {"code": code, "message": message}
    if request_id is not None:
        body["request_id"] = request_id
    if domain is not None:
        body["domain"] = domain
    if details is not None:
        body["details"] = details
    return httpx.Response(status, json=body)


def undecodable_body() -> httpx.Response:
    """A 200 whose body is not the ``gzip`` its ``Content-Encoding`` promises.

    Streamed rather than eager, so httpx decodes it inside ``send`` — where a
    real one arrives from.
    """
    return httpx.Response(
        200,
        stream=httpx.ByteStream(b"this is not gzip"),
        headers={"Content-Encoding": "gzip"},
    )


class TestStatusMapping:
    @pytest.mark.parametrize(("status", "code", "expected"), STATUS_ERRORS)
    async def test_status_and_code_choose_the_error_class(
        self,
        api: MockAPI,
        engine: Engine,
        status: int,
        code: str,
        expected: type[APIStatusError],
    ) -> None:
        api.respond(envelope(status, code))

        with pytest.raises(APIStatusError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert type(excinfo.value) is expected
        assert excinfo.value.status_code == status
        assert excinfo.value.code == code

    def test_the_table_covers_every_failure_the_spec_documents(self) -> None:
        """Keeps the catalogue honest: a new server error code fails here first."""
        covered = {(status, code) for status, code, _ in STATUS_ERRORS}

        assert DOCUMENTED_ERRORS - covered == set()

    def test_the_table_exercises_every_code_the_client_declares(self) -> None:
        exercised = {code for _, code, _ in STATUS_ERRORS}

        assert set(get_args(ErrorCode)) - exercised == set()

    async def test_a_plain_bad_request_is_not_a_cursor_error(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(envelope(400, "invalid_request"))

        with pytest.raises(BadRequestError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert not isinstance(excinfo.value, InvalidCursorError)

    async def test_an_unmapped_status_stays_the_base_status_error(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(envelope(418, "unbrewable"))

        with pytest.raises(APIStatusError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert type(excinfo.value) is APIStatusError

    def test_the_hierarchy_lets_a_caller_catch_broadly(self) -> None:
        assert issubclass(InvalidCursorError, BadRequestError)
        assert issubclass(BadRequestError, APIStatusError)
        assert issubclass(APIStatusError, TaplineError)
        assert issubclass(APIConnectionError, TaplineError)


class TestErrorEnvelope:
    async def test_the_envelope_is_exposed_on_the_error(self, api: MockAPI, engine: Engine) -> None:
        details: list[dict[str, object]] = [
            {
                "type": "less_than_equal",
                "loc": ["query", "limit"],
                "msg": "Input should be less than or equal to 20",
                "input": 50,
                "ctx": {"le": 20},
            }
        ]
        api.respond(
            envelope(422, "invalid_request", message="limit is out of range", details=details)
        )

        with pytest.raises(UnprocessableEntityError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        error = excinfo.value
        assert error.status_code == 422
        assert error.code == "invalid_request"
        assert error.message == "limit is out of range"
        assert error.request_id == REQUEST_ID
        assert error.domain == "youtube"
        assert error.details == details
        assert error.response.status_code == 422
        assert error.body == {
            "code": "invalid_request",
            "message": "limit is out of range",
            "request_id": REQUEST_ID,
            "domain": "youtube",
            "details": details,
        }

    async def test_request_id_falls_back_to_the_response_header(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(
            httpx.Response(
                500,
                json={"message": "boom"},
                headers={"X-Request-ID": "req_from_header"},
            )
        )

        with pytest.raises(InternalServerError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert excinfo.value.request_id == "req_from_header"
        assert excinfo.value.code is None

    async def test_str_names_the_status_the_code_and_the_request_id(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(envelope(403, "resource_forbidden", message="This video is private."))

        with pytest.raises(PermissionDeniedError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert str(excinfo.value) == (
            f"403 resource_forbidden [youtube]: This video is private. (request_id={REQUEST_ID})"
        )

    async def test_str_degrades_without_an_envelope(self, api: MockAPI, engine: Engine) -> None:
        api.respond(httpx.Response(503))

        with pytest.raises(InternalServerError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert str(excinfo.value) == "503: Service Unavailable"


class TestUnparseableBodies:
    async def test_a_non_json_error_body_does_not_crash(self, api: MockAPI, engine: Engine) -> None:
        api.respond(httpx.Response(502, text="<html>502 Bad Gateway</html>"))

        with pytest.raises(InternalServerError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        error = excinfo.value
        assert error.code is None
        assert error.details is None
        assert error.body == "<html>502 Bad Gateway</html>"
        assert error.message == "<html>502 Bad Gateway</html>"

    async def test_a_long_non_json_body_is_shortened(self, api: MockAPI, engine: Engine) -> None:
        api.respond(httpx.Response(500, text="upstream said no. " * 40))

        with pytest.raises(InternalServerError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert len(excinfo.value.message) <= 200
        assert excinfo.value.message.endswith(" …")

    async def test_an_empty_error_body_falls_back_to_the_reason_phrase(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(httpx.Response(500))

        with pytest.raises(InternalServerError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert excinfo.value.message == "Internal Server Error"
        assert excinfo.value.body is None

    async def test_a_json_error_body_that_is_not_an_envelope(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(httpx.Response(404, json=["not", "an", "envelope"]))

        with pytest.raises(NotFoundError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert excinfo.value.code is None
        assert excinfo.value.message == "Not Found"
        assert excinfo.value.body == ["not", "an", "envelope"]


class TestResponseValidation:
    async def test_a_success_body_that_misses_a_required_field(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(httpx.Response(200, json={}, headers={"X-Request-ID": REQUEST_ID}))

        with pytest.raises(APIResponseValidationError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert excinfo.value.status_code == 200
        assert excinfo.value.request_id == REQUEST_ID
        assert "VideoMetadataResponse" in str(excinfo.value)

    async def test_a_success_body_that_is_not_json(self, api: MockAPI, engine: Engine) -> None:
        api.respond(httpx.Response(200, text="<html>hello</html>"))

        with pytest.raises(APIResponseValidationError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert "not valid JSON" in str(excinfo.value)

    async def test_a_204_is_still_a_validation_failure_not_a_silent_none(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(httpx.Response(204))

        with pytest.raises(APIResponseValidationError):
            await engine.call("metadata", VIDEO_ID)


class TestFailuresHttpxRaisesItself:
    """The failures that come from httpx rather than from the API.

    ``TooManyRedirects`` and ``DecodingError`` are ``httpx.RequestError``s that
    ``httpx.TransportError`` does not cover, ``InvalidURL`` is neither, and a
    closed client is answered with a plain ``RuntimeError``, so each escapes a
    handler written around transport errors. Provoked for real here, because the
    question these answer is whether they can happen at all; how each is retried
    is asserted per engine in ``test_retries.py``.
    """

    async def test_an_undecodable_body_is_a_tapline_error(
        self, api: MockAPI, engine: Engine
    ) -> None:
        api.respond(undecodable_body())

        with pytest.raises(APIConnectionError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert isinstance(excinfo.value, TaplineError)
        assert isinstance(excinfo.value.__cause__, httpx.DecodingError)
        assert "DecodingError" in str(excinfo.value)

    def test_a_redirect_loop_is_a_tapline_error(self, api: MockAPI) -> None:
        """One engine is enough: only a caller-supplied client follows redirects."""
        api.respond(*[httpx.Response(302, headers={"Location": "/api/v1/round"})] * 4)

        with (
            SyncTaplineClient(
                api_key=TEST_API_KEY,
                http_client=httpx.Client(follow_redirects=True, max_redirects=1),
            ) as client,
            pytest.raises(APIConnectionError) as excinfo,
        ):
            client.youtube.metadata(VIDEO_ID)

        assert isinstance(excinfo.value, TaplineError)
        assert isinstance(excinfo.value.__cause__, httpx.TooManyRedirects)

    async def test_calling_a_closed_client_is_a_tapline_error(
        self, api: MockAPI, engine: Engine
    ) -> None:
        """Leaving a ``with`` block and calling anyway is a mistake users make.

        httpx answers it with a bare ``RuntimeError``, which is no
        ``RequestError`` and would pass straight through ``except APIError``.
        """
        await engine.aclose()

        with pytest.raises(APIConnectionError) as excinfo:
            await engine.call("metadata", VIDEO_ID)

        assert isinstance(excinfo.value, TaplineError)
        assert "the client is closed" in str(excinfo.value)
        assert str(excinfo.value).endswith(f"(GET https://api.tapline.sh{METADATA_PATH})")
        assert api.attempts == 0

    def test_a_base_url_httpx_cannot_parse_is_rejected_at_construction(
        self, client_class: ClientClass
    ) -> None:
        """A URL httpx refuses is a bad argument, so it fails like one — and early."""
        with pytest.raises(ValueError, match=r"base_url=.* is not a valid URL") as excinfo:
            client_class(api_key=TEST_API_KEY, base_url="https://api.tapline.sh:not-a-port")

        assert isinstance(excinfo.value.__cause__, httpx.InvalidURL)
