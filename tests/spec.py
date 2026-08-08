"""The published Tapline contract, reduced to what a client can get wrong.

``tests/fixtures/openapi/youtube.json`` is :func:`project` applied to the
YouTube half of https://api.tapline.sh/openapi.json, and is checked in so the
parity tests run on every checkout rather than only where a copy of the full
spec happens to sit. It keeps the facts that bind a client — path templates,
query parameter names, which are required, their defaults, the response model,
the credit price, the error codes each status documents — and drops the prose,
so rewording a description cannot fail a test.
The live-marked ``test_the_checked_in_spec_still_matches_the_published_one``
refetches the spec and asserts this projection still holds; ``python tests/spec.py``
rewrites the file when it does not.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

FIXTURE = Path(__file__).parent / "fixtures" / "openapi" / "youtube.json"
SPEC_URL = "https://api.tapline.sh/openapi.json"

CREDIT_PRICE = re.compile(r"Credits: (\d+) per request\.")


@dataclass(frozen=True)
class SpecPath:
    """One YouTube path, as the published spec declares it."""

    template: str
    credits: int | None
    response_model: str
    query_params: Mapping[str, Any]
    required: frozenset[str]
    errors: frozenset[tuple[int, str]]
    """Every ``(status, code)`` pair the spec documents this path can answer with."""

    @property
    def path_params(self) -> tuple[str, ...]:
        """The path parameters, in the order they appear in the URL."""
        return tuple(re.findall(r"\{([^}]+)\}", self.template))

    @property
    def is_demo(self) -> bool:
        return "/youtube/demo/" in self.template

    @property
    def authenticated_twin(self) -> str:
        """The keyed path a demo path shadows."""
        return self.template.replace("/youtube/demo/", "/youtube/")

    def matches(self, path: str) -> bool:
        """Whether a request path is an instance of this template."""
        segments = [re.escape(part) for part in re.split(r"\{[^}]+\}", self.template)]
        return re.fullmatch("[^/]+".join(segments), path) is not None


def error_codes(responses: Mapping[str, Any]) -> dict[str, list[str]]:
    """The ``code`` each documented failure status can carry, by status.

    The spec states them as named response examples; the 200 carries a single
    unnamed ``example``, so it drops out on its own.
    """
    return {
        status: sorted(examples)
        for status, response in responses.items()
        if (examples := response["content"]["application/json"].get("examples"))
    }


def project(document: Any) -> dict[str, dict[str, Any]]:
    """The YouTube paths of an OpenAPI document, reduced to the binding facts."""
    projected = {}
    for template, operations in document["paths"].items():
        if "/youtube/" not in template:
            continue
        operation = operations["get"]
        parameters = operation.get("parameters", [])
        query = [parameter for parameter in parameters if parameter["in"] == "query"]
        price = CREDIT_PRICE.search(operation["description"])
        schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
        projected[template] = {
            "credits": int(price.group(1)) if price else None,
            "response_model": schema["$ref"].rsplit("/", maxsplit=1)[-1],
            "query_params": {
                parameter["name"]: parameter["schema"].get("default") for parameter in query
            },
            "required": [parameter["name"] for parameter in query if parameter.get("required")],
            "errors": error_codes(operation["responses"]),
        }
    return projected


def checked_in() -> dict[str, dict[str, Any]]:
    """The projection this repo carries, as :func:`project` produced it."""
    projection: dict[str, dict[str, Any]] = json.loads(FIXTURE.read_text())["paths"]
    return projection


def youtube_paths() -> tuple[SpecPath, ...]:
    """Every YouTube path the checked-in projection declares, demo ones included."""
    return tuple(
        SpecPath(
            template=template,
            credits=path["credits"],
            response_model=path["response_model"],
            query_params=path["query_params"],
            required=frozenset(path["required"]),
            errors=frozenset(
                (int(status), code) for status, codes in path["errors"].items() for code in codes
            ),
        )
        for template, path in checked_in().items()
    )


if __name__ == "__main__":
    FIXTURE.write_text(
        json.dumps(
            {
                "source": SPEC_URL,
                "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "paths": project(httpx.get(SPEC_URL, timeout=30.0).raise_for_status().json()),
            },
            indent=2,
        )
        + "\n"
    )
