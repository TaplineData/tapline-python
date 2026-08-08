"""The seam between a resource and the engine that sends its requests.

A resource method describes its call as a :class:`Request` — path, response
model, query parameters — and hands it to ``_send``. Every endpoint's request
is therefore built in exactly one place, shared by the blocking and awaitable
resources, which differ only in ``await``.

``pages`` sits alongside ``_send`` and is public: a cursor-paginated endpoint
returns one page per call, and walking one is the same loop every time. No
generator is both blocking and awaitable, so that loop is written twice; its
description is written once and given to both.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

import pydantic

from ._base_client import AsyncAPIClient, SyncAPIClient
from ._pagination import CursorPagination
from ._types import NotGiven, Query, Timeout

__all__ = ["AsyncAPIResource", "CursorPage", "Request", "SyncAPIResource"]

_ModelT = TypeVar("_ModelT", bound=pydantic.BaseModel)


class CursorPage(Protocol):
    """One page of a cursor-paginated response: it says where the walk resumes."""

    @property
    def pagination(self) -> CursorPagination: ...


_PageT = TypeVar("_PageT", bound=CursorPage)


@dataclass(frozen=True)
class Request(Generic[_ModelT]):
    """One endpoint call, described independently of how it is sent.

    Attributes:
        path: Request path, already percent-encoded by
            :func:`~tapline._base_client.encode_path`.
        cast_to: Model the response body is validated into.
        params: Query parameters, with the caller's values left raw.
    """

    path: str
    cast_to: type[_ModelT]
    params: Query | None = None


class SyncAPIResource:
    """Base for a resource bound to a blocking client."""

    _client: SyncAPIClient

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client

    def _send(
        self,
        request: Request[_ModelT],
        *,
        timeout: float | Timeout | NotGiven | None,
    ) -> _ModelT:
        return self._client.get(
            request.path,
            cast_to=request.cast_to,
            params=request.params,
            timeout=timeout,
        )

    @staticmethod
    def pages(
        fetch: Callable[[str], _PageT],
        *,
        cursor: str = "",
    ) -> Iterator[_PageT]:
        """Walk a cursor-paginated endpoint to its end, one request per page::

            for page in tapline.youtube.pages(
                lambda cursor: tapline.youtube.comments(video_id, cursor=cursor)
            ):
                threads.extend(page.threads)

        On :class:`~tapline.TaplineClient` the same walk is an async generator,
        driven with ``async for``.

        Args:
            fetch: Calls the endpoint for one cursor and returns that page.
            cursor: Cursor the walk starts from. Leave it empty where an empty
                cursor means the first page. ``comment_replies`` has no such
                page: start it from a thread's ``replies_cursor``, or the
                server rejects the empty cursor.

        Yields:
            Each page in turn, ending with the one whose
            ``pagination.next_cursor`` is ``None``. That page's
            ``pagination.completion`` says whether the walk ran out or stopped
            at Tapline's paging depth cap.

        Nothing is requested until the iterator is advanced, and every page
        costs the endpoint's credits again.
        """
        while True:
            page = fetch(cursor)
            yield page
            if page.pagination.next_cursor is None:
                return
            cursor = page.pagination.next_cursor


class AsyncAPIResource:
    """Base for a resource bound to an awaitable client."""

    _client: AsyncAPIClient

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client

    async def _send(
        self,
        request: Request[_ModelT],
        *,
        timeout: float | Timeout | NotGiven | None,
    ) -> _ModelT:
        return await self._client.get(
            request.path,
            cast_to=request.cast_to,
            params=request.params,
            timeout=timeout,
        )

    @staticmethod
    async def pages(
        fetch: Callable[[str], Awaitable[_PageT]],
        *,
        cursor: str = "",
    ) -> AsyncIterator[_PageT]:
        while True:
            page = await fetch(cursor)
            yield page
            if page.pagination.next_cursor is None:
                return
            cursor = page.pagination.next_cursor


AsyncAPIResource.pages.__doc__ = SyncAPIResource.pages.__doc__
