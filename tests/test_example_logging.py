from __future__ import annotations

import logging
from types import ModuleType

import pytest
from examples.youtube import download_channel_transcripts, download_video_comments


@pytest.mark.parametrize(
    "example",
    [download_channel_transcripts, download_video_comments],
)
def test_only_the_example_enables_info_logs(
    example: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_logger = logging.getLogger()
    httpx_logger = logging.getLogger("httpx")
    monkeypatch.setattr(root_logger, "level", logging.INFO)
    monkeypatch.setattr(httpx_logger, "level", logging.NOTSET)
    monkeypatch.setattr(example.logger, "level", logging.NOTSET)

    example.configure_logging()

    assert example.logger.isEnabledFor(logging.INFO)
    assert not httpx_logger.isEnabledFor(logging.INFO)
