from __future__ import annotations

from .._models import BaseModel

__all__ = ["HeatmapItem", "HeatmapResponse"]


class HeatmapItem(BaseModel):
    """Replay intensity over one slice of a video's timeline."""

    start_time: float
    """Seconds from the start of the video."""

    end_time: float
    """Seconds from the start of the video."""

    value: float
    """Relative replay intensity, ``0.0`` to ``1.0`` across the video."""


class HeatmapResponse(BaseModel):
    """Response of ``youtube.heatmap``."""

    video_id: str

    heatmap: list[HeatmapItem] | None
    """``None`` when YouTube publishes no heatmap for this video."""
