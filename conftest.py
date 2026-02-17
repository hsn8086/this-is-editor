"""Pytest configuration and fixtures for the TIE project.

This module provides shared fixtures and configuration for all tests.
"""

import sys
from pathlib import Path

import pytest

# Add pysrc to the Python path
pysrc_path = Path(__file__).parent.parent / "pysrc"
if str(pysrc_path) not in sys.path:
    sys.path.insert(0, str(pysrc_path))


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
