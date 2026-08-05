"""Application entry point for TIE."""

import argparse
import logging
import platform
import re
import time
import urllib.request
from collections.abc import Sequence
from http import HTTPStatus
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
    parser.add_argument(
        "--self-check",
        action="store_true",
        help=(
            "Start the backend, confirm it serves the bundled UI, then exit. "
            "Headless smoke test for packaged builds; never opens a window."
        ),
    )
    return parser.parse_args(argv)


def _fetch(url: str, timeout: float = 2.0) -> tuple[int, bytes]:
    """Fetch a URL from the local server, returning its status and body."""
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
        return response.status, response.read()


def self_check(port: int, timeout: float = 60.0) -> None:
    """Verify the packaged backend serves the bundled UI, then return.

    Exercises the whole launch path except the window itself, which CI runners
    have no display for. Everything that has actually broken a build so far
    surfaces here: import-time failures, modules missing from the binary, and an
    incomplete `web/` payload.

    Args:
        port (int): Port the main server was started on.
        timeout (float): Seconds to wait for the server to become ready.

    Raises:
        RuntimeError: If the server never serves the bundled UI in time.

    """
    root = f"http://127.0.0.1:{port}/"
    deadline = time.monotonic() + timeout
    last_error = "server never became ready"

    while time.monotonic() < deadline:
        try:
            status, body = _fetch(root)
        except OSError as error:
            last_error = f"GET / raised {type(error).__name__}: {error}"
            time.sleep(0.5)
            continue

        if status != HTTPStatus.OK:
            last_error = f"GET / returned {status}"
            break
        if b'<div id="app">' not in body:
            last_error = "GET / did not return the bundled UI"
            break

        # Prove web/ was embedded, not just that the routes exist.
        asset = re.search(rb'src="(/assets/[^"]+\.js)"', body)
        if asset is None:
            last_error = "GET / referenced no bundled asset"
            break

        asset_path = asset.group(1).decode()
        asset_status, asset_body = _fetch(f"http://127.0.0.1:{port}{asset_path}")
        if asset_status != HTTPStatus.OK or not asset_body:
            last_error = f"GET {asset_path} returned {asset_status}"
            break

        logger.info(
            f"Self-check passed: index.html and {asset_path} "
            f"({len(asset_body)} bytes) served from the bundle",
        )
        return

    msg = f"Self-check failed: {last_error}"
    raise RuntimeError(msg)


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
        if args.self_check:
            self_check(web.port)
        elif platform.system() == "Windows":
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
