"""Tests for the headless packaged-build smoke check."""

from collections.abc import Callable
from http import HTTPStatus
from unittest.mock import patch

import pytest

import main

Response = tuple[int, bytes] | Exception

INDEX = b'<html><body><div id="app"></div>'
INDEX_WITH_ASSET = (
    INDEX + b'<script src="/assets/index-abc123.js"></script></body></html>'
)
ASSET_BODY = b"console.log(1)"


def _responses(*results: Response) -> Callable[..., tuple[int, bytes]]:
    """Build a _fetch replacement that returns each result in turn."""
    queue: list[Response] = list(results)

    def fake_fetch(url: str, timeout: float = 2.0) -> tuple[int, bytes]:
        result = queue.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    return fake_fetch


def test_self_check_passes_when_bundle_is_served() -> None:
    """Serving index.html plus its referenced asset is a healthy build."""
    fetch = _responses(
        (HTTPStatus.OK, INDEX_WITH_ASSET),
        (HTTPStatus.OK, ASSET_BODY),
    )

    with patch.object(main, "_fetch", fetch):
        main.self_check(port=1234)


def test_self_check_retries_until_the_server_is_ready() -> None:
    """The backend starts in a thread, so early connections are expected to fail."""
    fetch = _responses(
        ConnectionRefusedError("not up yet"),
        (HTTPStatus.OK, INDEX_WITH_ASSET),
        (HTTPStatus.OK, ASSET_BODY),
    )

    with patch.object(main, "_fetch", fetch), patch.object(main.time, "sleep"):
        main.self_check(port=1234)


def test_self_check_rejects_a_non_ok_status() -> None:
    """A server that answers but errors must not pass the gate."""
    fetch = _responses((HTTPStatus.INTERNAL_SERVER_ERROR, b""))

    with patch.object(main, "_fetch", fetch), pytest.raises(RuntimeError, match="500"):
        main.self_check(port=1234)


def test_self_check_rejects_a_page_without_the_bundled_ui() -> None:
    """Routing alone is not enough; the built index must be served."""
    fetch = _responses((HTTPStatus.OK, b"<html><body>placeholder</body></html>"))

    with (
        patch.object(main, "_fetch", fetch),
        pytest.raises(RuntimeError, match="bundled UI"),
    ):
        main.self_check(port=1234)


def test_self_check_rejects_an_index_without_assets() -> None:
    """An index that references no asset means web/ was not embedded."""
    fetch = _responses((HTTPStatus.OK, INDEX))

    with (
        patch.object(main, "_fetch", fetch),
        pytest.raises(RuntimeError, match="no bundled asset"),
    ):
        main.self_check(port=1234)


def test_self_check_rejects_a_missing_asset() -> None:
    """A referenced asset that 404s means the payload is incomplete."""
    fetch = _responses(
        (HTTPStatus.OK, INDEX_WITH_ASSET),
        (HTTPStatus.NOT_FOUND, b""),
    )

    with (
        patch.object(main, "_fetch", fetch),
        pytest.raises(RuntimeError, match="404"),
    ):
        main.self_check(port=1234)


def test_self_check_gives_up_when_the_server_never_starts() -> None:
    """A backend that never binds must fail the build rather than hang."""

    def always_refused(url: str, timeout: float = 2.0) -> tuple[int, bytes]:
        raise ConnectionRefusedError("never up")

    with (
        patch.object(main, "_fetch", always_refused),
        patch.object(main.time, "sleep"),
        pytest.raises(RuntimeError, match="ConnectionRefusedError"),
    ):
        main.self_check(port=1234, timeout=0.05)
