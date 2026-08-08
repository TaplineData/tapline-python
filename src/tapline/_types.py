from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Literal, TypeAlias

import httpx
from typing_extensions import override

__all__ = [
    "Headers",
    "NotGiven",
    "PrimitiveQueryValue",
    "Query",
    "QueryValue",
    "Timeout",
    "not_given",
]

Timeout: TypeAlias = httpx.Timeout
Headers: TypeAlias = Mapping[str, str]

PrimitiveQueryValue: TypeAlias = str | int | float | bool | Enum
QueryValue: TypeAlias = PrimitiveQueryValue | Sequence[PrimitiveQueryValue] | None
Query: TypeAlias = Mapping[str, QueryValue]


class NotGiven:
    """Sentinel for arguments whose ``None`` is itself a meaningful value.

    ``timeout=None`` disables the timeout, so "fall back to the client default"
    needs a value of its own::

        client.get(path, cast_to=Model)              # client default timeout
        client.get(path, cast_to=Model, timeout=5)   # 5s for this request
        client.get(path, cast_to=Model, timeout=None)  # wait indefinitely
    """

    def __bool__(self) -> Literal[False]:
        return False

    @override
    def __repr__(self) -> str:
        return "not_given"


not_given = NotGiven()
