"""Unit tests for the config module.

This module contains unit tests for the merge_meta and merge functions
in the config module.
"""

from pysrc.config import merge, merge_meta


class TestMergeMeta:
    """Tests for the merge_meta function."""

    def test_basic_merge_with_display(self) -> None:
        """Test basic merge with display metadata."""
        cfg_meta = {
            "fontSize": {
                "display": "Font Size",
                "i18n": "setting.fontSize",
            },
        }
        config = {"fontSize": 14}
        result = merge_meta(cfg_meta, config)

        assert result["fontSize"]["value"] == 14
        assert result["fontSize"]["display"] == "Font Size"
        assert result["fontSize"]["i18n"] == "setting.fontSize"

    def test_nested_merge_with_display(self) -> None:
        """Test nested merge with display metadata."""
        cfg_meta = {
            "editor": {
                "aceMain": {
                    "fontSize": {
                        "display": "Font Size",
                        "i18n": "setting.editor.aceMain.fontSize",
                    },
                },
            },
        }
        config = {"editor": {"aceMain": {"fontSize": 16}}}
        result = merge_meta(cfg_meta, config)

        assert result["editor"]["aceMain"]["fontSize"]["value"] == 16
        assert result["editor"]["aceMain"]["fontSize"]["display"] == "Font Size"

    def test_missing_config_value(self) -> None:
        """Test when config value is missing."""
        cfg_meta = {
            "fontSize": {
                "display": "Font Size",
                "i18n": "setting.fontSize",
            },
        }
        config = {}
        result = merge_meta(cfg_meta, config)

        assert result["fontSize"]["value"] is None

    def test_non_display_metadata(self) -> None:
        """Test non-display metadata is handled correctly."""
        cfg_meta = {
            "editor": {
                "aceMain": {
                    "fontSize": {
                        "display": "Font Size",
                        "i18n": "setting.editor.aceMain.fontSize",
                    },
                },
            },
        }
        config = {"editor": {"aceMain": {"fontSize": 14}}}
        result = merge_meta(cfg_meta, config)

        # The nested dict without "display" should be recursively processed
        assert "fontSize" in result["editor"]["aceMain"]

    def test_enum_in_display(self) -> None:
        """Test that enum values are preserved."""
        cfg_meta = {
            "theme": {
                "display": "Theme",
                "i18n": "setting.theme",
                "enum": ["light", "dark", "system"],
            },
        }
        config = {"theme": "dark"}
        result = merge_meta(cfg_meta, config)

        assert result["theme"]["value"] == "dark"
        assert result["theme"]["enum"] == ["light", "dark", "system"]

    def test_multiple_keys(self) -> None:
        """Test merging multiple keys."""
        cfg_meta = {
            "fontSize": {
                "display": "Font Size",
                "i18n": "setting.fontSize",
            },
            "fontFamily": {
                "display": "Font Family",
                "i18n": "setting.fontFamily",
            },
        }
        config = {"fontSize": 14, "fontFamily": "monospace"}
        result = merge_meta(cfg_meta, config)

        assert result["fontSize"]["value"] == 14
        assert result["fontFamily"]["value"] == "monospace"

    def test_deeply_nested(self) -> None:
        """Test deeply nested configuration."""
        cfg_meta = {
            "programmingLanguages": {
                "python": {
                    "executable": {
                        "display": "Python: Executable",
                        "i18n": "setting.python.executable",
                    },
                },
            },
        }
        config = {"programmingLanguages": {"python": {"executable": "python3"}}}
        result = merge_meta(cfg_meta, config)

        assert (
            result["programmingLanguages"]["python"]["executable"]["value"] == "python3"
        )

    def test_empty_cfg_meta(self) -> None:
        """Test with empty cfg_meta."""
        cfg_meta = {}
        config = {"key": "value"}
        result = merge_meta(cfg_meta, config)
        assert result == {}

    def test_empty_config(self) -> None:
        """Test with empty config."""
        cfg_meta = {
            "key": {
                "display": "Key",
                "i18n": "key",
            },
        }
        config = {}
        result = merge_meta(cfg_meta, config)
        assert result["key"]["value"] is None


class TestMerge:
    """Tests for the merge function."""

    def test_basic_merge(self) -> None:
        """Test basic dictionary merge."""
        a = {"x": 1, "y": 2}
        b = {"y": 3, "z": 4}
        result = merge(a, b)

        assert result["x"] == 1
        assert result["y"] == 3
        assert result["z"] == 4

    def test_nested_merge(self) -> None:
        """Test nested dictionary merge."""
        a = {"x": 1, "y": {"z": 2}}
        b = {"y": {"w": 3}}
        result = merge(a, b)

        assert result["x"] == 1
        assert result["y"]["z"] == 2
        assert result["y"]["w"] == 3

    def test_overwrite_value(self) -> None:
        """Test that b overwrites a's values."""
        a = {"key": "old_value"}
        b = {"key": "new_value"}
        result = merge(a, b)

        assert result["key"] == "new_value"

    def test_merge_modifies_in_place(self) -> None:
        """Test that merge modifies the first dictionary in place."""
        a = {"x": 1}
        b = {"y": 2}
        result = merge(a, b)

        assert result is a
        assert a["x"] == 1
        assert a["y"] == 2

    def test_empty_dicts(self) -> None:
        """Test with empty dictionaries."""
        a = {}
        b = {"x": 1}
        result = merge(a, b)

        assert result == {"x": 1}

    def test_empty_second_dict(self) -> None:
        """Test when second dictionary is empty."""
        a = {"x": 1}
        b = {}
        result = merge(a, b)

        assert result == {"x": 1}

    def test_both_empty(self) -> None:
        """Test when both dictionaries are empty."""
        a = {}
        b = {}
        result = merge(a, b)

        assert result == {}

    def test_deep_merge(self) -> None:
        """Test deeply nested merge."""
        a = {
            "level1": {
                "level2": {
                    "level3": "value3",
                    "extra": "keep",
                },
            },
        }
        b = {
            "level1": {
                "level2": {
                    "level3": "new_value",
                    "new_key": "new_value",
                },
            },
        }
        result = merge(a, b)

        assert result["level1"]["level2"]["level3"] == "new_value"
        assert result["level1"]["level2"]["extra"] == "keep"
        assert result["level1"]["level2"]["new_key"] == "new_value"

    def test_list_value_replacement(self) -> None:
        """Test that list values are replaced, not merged."""
        a = {"key": [1, 2, 3]}
        b = {"key": [4, 5]}
        result = merge(a, b)

        assert result["key"] == [4, 5]

    def test_non_dict_to_dict_merge(self) -> None:
        """Test merging when a has dict but b has non-dict value."""
        a = {"key": {"nested": "value"}}
        b = {"key": "simple_value"}
        result = merge(a, b)

        assert result["key"] == "simple_value"

    def test_dict_to_non_dict_merge(self) -> None:
        """Test merging when a has non-dict but b has dict value."""
        a = {"key": "simple_value"}
        b = {"key": {"nested": "value"}}
        result = merge(a, b)

        assert result["key"] == {"nested": "value"}

    def test_multiple_top_level_keys(self) -> None:
        """Test multiple keys at top level."""
        a = {"a": 1, "b": 2, "c": 3}
        b = {"b": 20, "c": 30, "d": 40}
        result = merge(a, b)

        assert result["a"] == 1
        assert result["b"] == 20
        assert result["c"] == 30
        assert result["d"] == 40
