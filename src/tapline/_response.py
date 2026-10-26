"""Build response objects without validating or coercing the API's values."""

from __future__ import annotations

from enum import Enum
from types import UnionType
from typing import Annotated, TypeVar, Union, cast, get_args, get_origin

from pydantic import BaseModel

_ResponseT = TypeVar("_ResponseT")


def construct_response(value: object, response_type: type[_ResponseT]) -> _ResponseT:
    """Keep model attributes where the JSON shape permits, and raw values elsewhere."""
    return cast(_ResponseT, _construct_value(value, response_type))


def _construct_value(value: object, annotation: object) -> object:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Annotated:
        return _construct_value(value, args[0])
    if origin in (Union, UnionType):
        member = max(args, key=lambda candidate: _shape_score(value, candidate))
        return _construct_value(value, member) if _shape_score(value, member)[0] else value
    if origin is list and isinstance(value, list):
        return [_construct_value(item, args[0]) for item in cast(list[object], value)]
    if origin is dict and isinstance(value, dict):
        return {
            key: _construct_value(item, args[1])
            for key, item in cast(dict[str, object], value).items()
        }
    if isinstance(annotation, type):
        if issubclass(annotation, BaseModel):
            annotation.model_rebuild()
            if annotation.__pydantic_root_model__:
                root = _construct_value(value, annotation.model_fields["root"].annotation)
                return annotation.model_construct(root=root)
            if isinstance(value, dict):
                data = cast(dict[str, object], value)
                values = dict(data)
                fields_set = set(data)
                for name, field in annotation.model_fields.items():
                    key = field.alias if field.alias in data else name
                    if key in data:
                        values[key] = _construct_value(data[key], field.annotation)
                        fields_set.discard(key)
                        fields_set.add(name)
                    elif field.is_required():
                        values[name] = None
                return annotation.model_construct(_fields_set=fields_set, **values)
        elif issubclass(annotation, Enum):
            return next((member for member in annotation if member.value == value), value)
    return value


def _shape_score(value: object, annotation: object) -> tuple[int, int]:
    """Choose a union wrapper by JSON kind and known keys, never by field validity.

    Full and trimmed responses share fields. Prefer the model naming more of
    the supplied keys, including nested keys, then fewer missing required keys.
    Ties retain the declared union order. No score can reject a response.
    """
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Annotated:
        return _shape_score(value, args[0])
    if origin in (Union, UnionType):
        return max(_shape_score(value, member) for member in args)
    if origin is list:
        if isinstance(value, list):
            scores = [_shape_score(item, args[0]) for item in cast(list[object], value)]
            return 1 + sum(score[0] for score in scores), sum(score[1] for score in scores)
        return 0, 0
    if origin is dict:
        return int(isinstance(value, dict)), 0
    if isinstance(annotation, type):
        if issubclass(annotation, BaseModel):
            annotation.model_rebuild()
            if annotation.__pydantic_root_model__:
                return _shape_score(value, annotation.model_fields["root"].annotation)
            if isinstance(value, dict):
                data = cast(dict[str, object], value)
                matched, missing = 1, 0
                for name, field in annotation.model_fields.items():
                    key = field.alias if field.alias in data else name
                    if key in data:
                        nested_matched, nested_missing = _shape_score(data[key], field.annotation)
                        matched += 1 + nested_matched
                        missing += nested_missing
                    elif field.is_required():
                        missing -= 1
                return matched, missing
        elif issubclass(annotation, Enum):
            return (2 if any(member.value == value for member in annotation) else 0), 0
        else:
            return int(type(value) is annotation), 0
    return 0, 0
