"""Pydantic settings every Tapline response model is built on, whatever API it came from."""

from __future__ import annotations

from typing import ClassVar

import pydantic
from pydantic import ConfigDict
from pydantic.fields import FieldInfo

__all__ = ["PREFER_ENUM", "BaseModel"]


class BaseModel(pydantic.BaseModel):
    """Base class for every Tapline response model.

    Fields the server sends but this client version does not declare are kept
    instead of dropped, so a Tapline release that adds a field cannot break an
    installed client. Read them through :attr:`model_extra`, or as plain
    attributes.

    :attr:`model_fields_set` names the fields the server actually sent. That is
    the reliable way to tell an omitted field from one the server sent as
    ``null`` — it matters for the ``fields`` projection on
    :class:`~tapline.youtube.VideoMetadataResponse`.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")


PREFER_ENUM: FieldInfo = pydantic.Field(union_mode="left_to_right")
"""Pydantic's smart union would match ``str`` first and strip every enum member."""
