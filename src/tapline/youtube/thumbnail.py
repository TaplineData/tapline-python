from __future__ import annotations

from .._models import BaseModel

__all__ = ["ThumbnailItem"]


class ThumbnailItem(BaseModel):
    """One thumbnail image, largest first in the lists that carry it.

    Every field is nullable. Tapline copies each key straight out of what
    YouTube published, and one image described without a URL would otherwise
    reject the whole response it arrived in.
    """

    url: str | None

    width: int | None
    """Pixel width, or ``None`` when YouTube did not report one."""

    height: int | None
    """Pixel height, or ``None`` when YouTube did not report one."""
