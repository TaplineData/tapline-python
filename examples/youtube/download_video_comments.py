from __future__ import annotations

import argparse
import logging

from tapline import NotFoundError, SyncTaplineClient

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logging.getLogger().setLevel(logging.WARNING)
    logger.setLevel(logging.INFO)


def log_comments(tapline: SyncTaplineClient, video: str) -> tuple[int, int]:
    comment_count = 0
    reply_count = 0
    pages = tapline.youtube.pages(
        lambda cursor: tapline.youtube.comments(video, sort="new", cursor=cursor)
    )

    try:
        for page in pages:
            for thread in page.threads:
                comment = thread.comment
                comment_id = comment.comment_id
                logger.info("%s: %s", comment.author or "Unknown", comment.text or "")
                comment_count += 1

                if thread.replies_cursor is not None and comment_id is not None:
                    selected_comment_id: str = comment_id
                    # This iterator is exhausted before selected_comment_id changes.
                    reply_pages = tapline.youtube.pages(
                        lambda cursor: tapline.youtube.comment_replies(
                            video,
                            selected_comment_id,  # noqa: B023
                            cursor=cursor,
                        ),
                        cursor=thread.replies_cursor,
                    )

                    for reply_page in reply_pages:
                        for reply in reply_page.replies:
                            logger.info("  %s: %s", reply.author or "Unknown", reply.text or "")
                            reply_count += 1
    except NotFoundError as error:
        logger.warning(
            "Comments or replies unavailable for %s; stopping (request_id=%s)",
            video,
            error.request_id,
        )

    return comment_count, reply_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Log every comment and reply from a video.")
    parser.add_argument("video", help="A video ID or URL")
    args = parser.parse_args()
    configure_logging()

    with SyncTaplineClient() as tapline:
        log_comments(tapline, args.video)


if __name__ == "__main__":
    main()
