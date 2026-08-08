from __future__ import annotations

from .._models import BaseModel
from .._pagination import CursorPagination

__all__ = ["CommentItem", "CommentThread", "CommentsResponse", "RepliesResponse"]


class CommentItem(BaseModel):
    """One comment, top-level or reply.

    Every field is nullable: YouTube omits authorship and engagement counts
    from comments it serves in a reduced form.
    """

    comment_id: str | None

    text: str | None
    """Comment body as plain text."""

    like_count: int | None

    dislike_count: int | None
    """YouTube stopped publishing this; expect ``None``."""

    timestamp: int | None
    """Unix seconds the comment was posted."""

    published_at: str | None
    """YouTube's relative phrasing, such as ``"3 years ago"``."""

    is_pinned: bool | None

    is_favorited: bool | None
    """Hearted by the uploader."""

    author: str | None

    author_id: str | None

    author_thumbnail: str | None

    author_url: str | None

    author_is_verified: bool | None

    author_is_uploader: bool | None

    html: str | None
    """Comment body with YouTube's markup, including links and emoji images."""


class CommentThread(BaseModel):
    """A top-level comment and the handle to its replies."""

    comment: CommentItem

    replies_cursor: str | None
    """Pass as ``cursor`` to ``youtube.comment_replies``. ``None`` when the
    comment has no replies."""


class CommentsResponse(BaseModel):
    """Response of ``youtube.comments``."""

    video_id: str

    returned_count: int

    threads: list[CommentThread]

    pagination: CursorPagination


class RepliesResponse(BaseModel):
    """Response of ``youtube.comment_replies``."""

    video_id: str

    comment_id: str

    returned_count: int

    replies: list[CommentItem]

    pagination: CursorPagination
