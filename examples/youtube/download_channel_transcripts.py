from __future__ import annotations

import argparse
import logging

from tapline import NotFoundError, SyncTaplineClient
from tapline.youtube import ChannelContentType

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logging.getLogger().setLevel(logging.WARNING)
    logger.setLevel(logging.INFO)


def log_transcripts(
    tapline: SyncTaplineClient,
    channel: str,
) -> int:
    transcript_count = 0

    for content_type in ChannelContentType:
        # This iterator is exhausted before content_type changes.
        pages = tapline.youtube.pages(
            lambda cursor: tapline.youtube.channel_videos(
                channel,
                content_type=content_type,  # noqa: B023
                cursor=cursor,
            )
        )

        for page in pages:
            for video in page.videos:
                if video.video_id is None:
                    continue

                title = video.title or video.video_id
                try:
                    subtitles = tapline.youtube.subtitles(
                        video.video_id,
                        language="en",
                        subtitle_format="txt",
                        source="any",
                    )
                except NotFoundError as error:
                    logger.warning(
                        "No transcript found for %s (%s); skipping (request_id=%s)",
                        title,
                        video.video_id,
                        error.request_id,
                    )
                    continue

                title = subtitles.metadata.title or title
                logger.info("%s (%s)\n%s", title, video.video_id, subtitles.transcript)
                transcript_count += 1

    return transcript_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Log every transcript from a channel.")
    parser.add_argument("channel", help="A channel ID, handle, or URL")
    args = parser.parse_args()
    configure_logging()

    with SyncTaplineClient() as tapline:
        log_transcripts(tapline, args.channel)


if __name__ == "__main__":
    main()
