"""Application entry point for TIE."""

import argparse
import logging
import platform
from collections.abc import Sequence
from pathlib import Path

from loguru import logger

from pysrc.runtime import configure_dev_user_data_dir


def absolute_path(value: str) -> Path:
    """Expand and resolve a command-line path."""
    return Path(value).expanduser().resolve()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse TIE command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument(
        "--dev-user-data-dir",
        type=absolute_path,
        help=(
            "Store TIE data, config, and logs under this directory. "
            "Intended for isolated development and environment-scan testing."
        ),
    )
    return parser.parse_args(argv)


class InterceptHandler(logging.Handler):
    """Redirect standard logging records to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Forward a standard logging record to Loguru."""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def main(argv: Sequence[str] | None = None) -> None:
    """Start the TIE backend and desktop window."""
    args = parse_args(argv)
    configure_dev_user_data_dir(args.dev_user_data_dir)

    import webview  # noqa: PLC0415

    from pysrc import web  # noqa: PLC0415
    from pysrc.user_data import user_log_dir  # noqa: PLC0415

    logger.add(
        user_log_dir / "this_is_editor.log",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        level="DEBUG" if args.debug else "INFO",
    )
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    server, thread, server_recver, thread_recver = web.start_server()
    try:
        if platform.system() == "Windows":
            webview.start(gui="edgechromium", debug=args.debug)
        else:
            webview.start(debug=args.debug)
    finally:
        web.shutdown_runtime()
        web.should_exit = True
        server.should_exit = True
        server_recver.should_exit = True

        logger.info("Shutting down server...")
        thread.join()
        thread_recver.join()
        logger.info("Server shut down successfully.")


if __name__ == "__main__":
    main()
