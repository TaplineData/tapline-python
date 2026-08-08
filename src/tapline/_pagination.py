"""Tapline's cursor protocol, which every paginated endpoint of every API shares."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, TypeAlias

from ._models import PREFER_ENUM, BaseModel

__all__ = ["CursorCompletion", "CursorCompletionValue", "CursorPagination"]


class CursorCompletion(str, Enum):
    """Why a cursor-paginated endpoint stopped handing out cursors."""

    EXHAUSTED = "exhausted"
    """Everything upstream had was returned."""

    DEPTH_LIMIT = "depth_limit"
    """Tapline stopped at its paging depth cap; more exists but is unreachable."""


CursorCompletionValue: TypeAlias = Annotated[CursorCompletion | str, PREFER_ENUM]
"""Open form of :class:`CursorCompletion`: a new stop reason arrives verbatim."""


class CursorPagination(BaseModel):
    """Where to resume a cursor-paginated endpoint."""

    next_cursor: str | None
    """Pass back as ``cursor`` for the next page. ``None`` on the last page."""

    completion: CursorCompletionValue | None
    """Set only on the last page, explaining why it is the last."""
