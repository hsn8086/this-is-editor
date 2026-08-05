"""Pytest configuration and fixtures for the TIE project.

This module provides shared fixtures and configuration for all tests.
"""

import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to the Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Isolate the user data directory before any ``pysrc`` module is imported.
#
# ``pysrc.user_data`` resolves the platform config/data/log directories at import
# time and ``pysrc.config`` immediately merges the on-disk ``config.json`` into the
# default config dict *in place*. Without this, the suite reads (and creates) the
# developer's real configuration, so a stale local config silently changes the
# "default" values under test and makes results machine-dependent.
#
# An explicitly provided value wins, so a developer can still point the suite at a
# specific directory.
if not os.environ.get("TIE_DEV_USER_DATA_DIR"):
    _isolated_user_data_dir = tempfile.mkdtemp(prefix="tie-test-userdata-")
    os.environ["TIE_DEV_USER_DATA_DIR"] = _isolated_user_data_dir
    atexit.register(shutil.rmtree, _isolated_user_data_dir, ignore_errors=True)


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for tests.

    Args:
        tmp_path: Pytest's built-in temporary directory fixture.

    Returns:
        Path to a temporary directory.

    """
    return tmp_path


@pytest.fixture
def sample_code() -> str:
    """Provide a sample code for testing.

    Returns:
        A simple Python code string.

    """
    return "print('Hello, World!')"


@pytest.fixture
def sample_config() -> dict[str, object]:
    """Provide a sample configuration dictionary.

    Returns:
        A dictionary representing a minimal configuration.

    """
    return {
        "editor": {
            "aceMain": {
                "fontSize": {
                    "display": "Font Size",
                    "value": 14,
                    "i18n": "editor.fontSize",
                },
            },
            "tie": {
                "theme": {
                    "display": "Theme",
                    "value": "tie-light",
                    "i18n": "editor.theme",
                },
            },
        },
        "programmingLanguages": {},
        "keyboardShortcuts": {},
    }
