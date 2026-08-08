"""Every captured payload, replayed through the model that has to hold it.

``tests/fixtures/youtube`` holds real API responses — see ``manifest.json`` for
what produced each one, and ``scripts/capture_fixtures.py`` to refresh them.
The assertions here are the two that catch model drift:

* nothing lands in :attr:`~pydantic.BaseModel.model_extra`, which would mean
  the API returns a field the model does not declare;
* ``model_dump(exclude_unset=True)`` reproduces the payload exactly, which
  would fail if a field were renamed, retyped, or silently dropped.

These are the checks that found ``Json3Segment.isSpeakerChange``.

Most payloads were captured from the unauthenticated ``/demo/`` routes, which
spend no credits. What makes them evidence about the keyed routes the client
actually calls is that the published spec declares the same response model for
both — asserted below, so a server that ever split the two fails here instead
of leaving these tests green against the wrong contract.
"""

from __future__ import annotations

import typing
from typing import Any
from urllib.parse import urlsplit

import pydantic
import pytest

from conftest import CAPTURES, captured, endpoints_of, extras
from spec import SpecPath, youtube_paths
from tapline.resources.youtube import YouTube

MANIFEST = captured("manifest")
SPEC_PATHS = {path.template: path for path in youtube_paths()}


def returned_model(method: str) -> type[pydantic.BaseModel]:
    """The model the client validates that endpoint's responses into."""
    returns: type[pydantic.BaseModel] = typing.get_type_hints(getattr(YouTube, method))["return"]
    return returns


def capture_source(url: str) -> SpecPath:
    """The published path a capture was taken from."""
    path = urlsplit(url).path
    matches = [candidate for candidate in SPEC_PATHS.values() if candidate.matches(path)]
    assert len(matches) == 1, f"{url} matched {len(matches)} spec paths"
    return matches[0]


@pytest.fixture(params=sorted(MANIFEST), ids=sorted(MANIFEST))
def capture(request: pytest.FixtureRequest) -> tuple[type[pydantic.BaseModel], Any]:
    """One captured payload, paired with the model the endpoint it came from returns."""
    entry = MANIFEST[request.param]
    model = returned_model(entry["method"])
    assert model.__name__ == entry["model"], request.param
    return model, captured(request.param)


def test_a_captured_payload_parses(capture: tuple[type[pydantic.BaseModel], Any]) -> None:
    model, payload = capture
    model.model_validate(payload)


def test_a_captured_payload_declares_every_field_it_carries(
    capture: tuple[type[pydantic.BaseModel], Any],
) -> None:
    model, payload = capture
    assert extras(model.model_validate(payload), model.__name__) == []


def test_a_captured_payload_survives_a_round_trip(
    capture: tuple[type[pydantic.BaseModel], Any],
) -> None:
    model, payload = capture
    parsed = model.model_validate(payload)

    assert parsed.model_dump(mode="json", exclude_unset=True) == payload


@pytest.mark.parametrize("name", sorted(MANIFEST))
def test_a_capture_carries_the_model_its_keyed_route_returns(name: str) -> None:
    entry = MANIFEST[name]
    source = capture_source(entry["url"])
    keyed = SPEC_PATHS[source.authenticated_twin]

    assert source.response_model == keyed.response_model
    assert keyed.response_model == entry["model"]


def test_every_fixture_on_disk_is_in_the_manifest() -> None:
    on_disk = {path.stem for path in CAPTURES.glob("*.json")} - {"manifest"}

    assert on_disk == set(MANIFEST)


def test_every_endpoint_has_a_captured_payload() -> None:
    assert {entry["method"] for entry in MANIFEST.values()} == endpoints_of(YouTube)
