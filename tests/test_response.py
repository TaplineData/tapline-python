"""Non-validating construction preserves the model interface for captured responses."""

from __future__ import annotations

import importlib
import json
from enum import Enum
from pathlib import Path
from typing import Any

import pydantic
import pytest

from conftest import CAPTURES, captured
from tapline._models import BaseModel
from tapline._response import construct_response
from test_fixture_payloads import returned_model


def captured_responses() -> list[Any]:
    cases = []
    for path in sorted(Path(__file__).parent.glob("test_fixture_payloads_*.py")):
        module = importlib.import_module(path.stem)
        for stem in module.cases(negative=False):
            response_type = module.RESPONSES[stem.split(".", 1)[0]]
            payload_path = module.FIXTURES / f"{stem}.json"
            cases.append(pytest.param(response_type, payload_path, id=f"{path.stem}:{stem}"))
    for name, entry in captured("manifest").items():
        cases.append(
            pytest.param(returned_model(entry["method"]), CAPTURES / f"{name}.json", id=name)
        )
    return cases


def assert_model_types(expected: object, actual: object) -> None:
    """Callers keep the same nested model and enum classes for conforming payloads."""
    if isinstance(expected, pydantic.BaseModel):
        assert type(actual) is type(expected)
        for name in expected.model_fields_set:
            assert_model_types(getattr(expected, name), getattr(actual, name))
    elif isinstance(expected, list):
        assert isinstance(actual, list)
        assert len(actual) == len(expected)
        for expected_item, actual_item in zip(expected, actual, strict=True):
            assert_model_types(expected_item, actual_item)
    elif isinstance(expected, dict):
        assert isinstance(actual, dict)
        assert actual.keys() == expected.keys()
        for key in expected:
            assert_model_types(expected[key], actual[key])
    elif isinstance(expected, Enum):
        assert actual is expected


@pytest.mark.parametrize(("response_type", "payload_path"), captured_responses())
def test_captured_response_keeps_its_values_and_model_interface(
    response_type: type[Any], payload_path: Path
) -> None:
    payload = json.loads(payload_path.read_text())
    adapter: pydantic.TypeAdapter[Any] = pydantic.TypeAdapter(response_type)

    response = construct_response(payload, response_type)

    assert (
        adapter.dump_python(
            response, mode="json", exclude_unset=True, by_alias=True, warnings=False
        )
        == payload
    )
    assert_model_types(adapter.validate_python(payload), response)


class ResponseWithValidators(BaseModel):
    count: int = pydantic.Field(ge=0)

    @pydantic.field_validator("count")
    @classmethod
    def reject_count(cls, _value: int) -> int:
        raise AssertionError("Response construction must not run field validators")

    @pydantic.model_validator(mode="before")
    @classmethod
    def reject_response(cls, _value: object) -> object:
        raise AssertionError("Response construction must not run model validators")


@pytest.mark.parametrize("count", [-1, "42", None, {"unexpected": "object"}])
def test_response_construction_never_runs_validators(count: object) -> None:
    response = construct_response({"count": count}, ResponseWithValidators)

    assert response.count == count
