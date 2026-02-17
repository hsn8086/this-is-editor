"""Smoke tests for the backend.

This module contains basic smoke tests to verify the test infrastructure
is working correctly and can import modules.
"""

from pathlib import Path

import pytest


class TestModels:
    """Tests for the models module."""

    def test_import_models(self) -> None:
        """Test that models module can be imported."""
        from pysrc import models

        assert models is not None

    def test_problem_model(self) -> None:
        """Test Problem model creation."""
        from pysrc.models import Problem

        problem = Problem(
            name="Test Problem",
            group="test",
            url=None,
            interactive=False,
            memoryLimit=256,
            timeLimit=1000,
            tests=[],
            testType="normal",
            input=None,
            output=None,
            languages=None,
            batch=None,
        )

        assert problem.name == "Test Problem"
        assert problem.memoryLimit == 256
        assert problem.timeLimit == 1000


class TestUtils:
    """Tests for the utils module."""

    def test_import_utils(self) -> None:
        """Test that utils module can be imported."""
        from pysrc import utils

        assert utils is not None


class TestConfig:
    """Tests for the config module."""

    def test_import_config(self) -> None:
        """Test that config module can be imported."""
        from pysrc import config

        assert config is not None


class TestLang:
    """Tests for the langs module."""

    def test_import_langs(self) -> None:
        """Test that langs module can be imported."""
        from pysrc import langs

        assert langs is not None


class TestPytestInfrastructure:
    """Test that pytest infrastructure is working correctly."""

    def test_temp_dir_fixture(self, temp_dir: Path) -> None:
        """Test the temp_dir fixture."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()

    def test_sample_code_fixture(self, sample_code: str) -> None:
        """Test the sample_code fixture."""
        assert isinstance(sample_code, str)
        assert len(sample_code) > 0

    def test_sample_config_fixture(self, sample_config: dict[str, object]) -> None:
        """Test the sample_config fixture."""
        assert isinstance(sample_config, dict)
        assert "editor" in sample_config

    @pytest.mark.unit
    def test_unit_marker(self) -> None:
        """Test that unit marker works."""
        assert True

    @pytest.mark.asyncio
    async def test_async_support(self) -> None:
        """Test that async tests work."""
        result = await _asyncio_coro()
        assert result == "async"


async def _asyncio_coro() -> str:
    """Helper async function for testing."""
    return "async"
