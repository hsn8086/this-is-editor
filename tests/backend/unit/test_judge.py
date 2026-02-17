"""Unit tests for the judge module.

This module contains unit tests for the task_checker and cph2testcase functions
in the judge module.
"""

from pysrc.judge import cph2testcase, task_checker


class TestTaskChecker:
    """Tests for the task_checker function."""

    def test_exact_match(self) -> None:
        """Test that exact match returns True."""
        output = "hello world"
        answer = "hello world"
        assert task_checker(output, answer) is True

    def test_whitespace_filtering(self) -> None:
        """Test that whitespace is filtered correctly."""
        output = "hello   world"
        answer = "hello world"
        assert task_checker(output, answer) is True

    def test_multiple_spaces(self) -> None:
        """Test multiple spaces between words are filtered."""
        output = "a   b   c"
        answer = "a b c"
        assert task_checker(output, answer) is True

    def test_empty_output(self) -> None:
        """Test that empty output returns False when answer is not empty."""
        output = ""
        answer = "hello"
        assert task_checker(output, answer) is False

    def test_empty_answer(self) -> None:
        """Test that non-empty output returns False when answer is empty."""
        output = "hello"
        answer = ""
        assert task_checker(output, answer) is False

    def test_both_empty(self) -> None:
        """Test that both empty returns True."""
        output = ""
        answer = ""
        assert task_checker(output, answer) is True

    def test_different_lengths(self) -> None:
        """Test that different token counts returns False."""
        output = "hello world"
        answer = "hello"
        assert task_checker(output, answer) is False

    def test_different_content(self) -> None:
        """Test that different content returns False."""
        output = "hello world"
        answer = "hello there"
        assert task_checker(output, answer) is False

    def test_leading_trailing_whitespace(self) -> None:
        """Test that leading and trailing whitespace is handled."""
        output = "  hello world  "
        answer = "hello world"
        assert task_checker(output, answer) is True

    def test_newlines_as_whitespace(self) -> None:
        """Test that newlines are treated as whitespace."""
        output = "hello\nworld"
        answer = "hello world"
        assert task_checker(output, answer) is True

    def test_tabs_as_whitespace(self) -> None:
        """Test that tabs are treated as whitespace."""
        output = "hello\tworld"
        answer = "hello world"
        assert task_checker(output, answer) is True

    def test_mixed_whitespace(self) -> None:
        """Test mixed whitespace characters."""
        output = "  hello \n world \t "
        answer = "hello world"
        assert task_checker(output, answer) is True

    def test_multiple_test_cases_format(self) -> None:
        """Test with multiple lines simulating multiple test case outputs."""
        output = "42\n100\n200"
        answer = "42 100 200"
        # The function splits by whitespace, so this tests the filtering
        oup = list(filter(bool, output.split()))
        ans = list(filter(bool, answer.split()))
        assert len(oup) == 3
        assert len(ans) == 3

    def test_strip_each_token(self) -> None:
        """Test that each token is stripped."""
        output = "  hello  world  "
        answer = "hello world"
        oup = list(filter(bool, output.split()))
        ans = list(filter(bool, answer.split()))
        assert all(i.strip() == j.strip() for i, j in zip(oup, ans, strict=False))


class TestCph2testcase:
    """Tests for the cph2testcase function."""

    def test_basic_conversion(self) -> None:
        """Test basic JSON to testcase conversion."""
        cph_json = {
            "name": "Test Problem",
            "tests": [
                {"input": "1 2", "output": "3"},
                {"input": "2 3", "output": "5"},
            ],
            "memoryLimit": 1024,
            "timeLimit": 1000,
        }
        result = cph2testcase(cph_json)

        assert result["name"] == "Test Problem"
        assert len(result["tests"]) == 2
        assert result["tests"][0]["id"] == 1
        assert result["tests"][0]["input"] == "1 2"
        assert result["tests"][0]["answer"] == "3"
        assert result["tests"][1]["id"] == 2
        assert result["tests"][1]["input"] == "2 3"
        assert result["tests"][1]["answer"] == "5"
        assert result["memoryLimit"] == 1024
        assert result["timeLimit"] == 1.0

    def test_default_values(self) -> None:
        """Test default values when fields are missing."""
        cph_json = {
            "name": "Default Problem",
            "tests": [{"input": "test", "output": "result"}],
        }
        result = cph2testcase(cph_json)

        assert result["name"] == "Default Problem"
        assert result["memoryLimit"] == 1024
        assert result["timeLimit"] == 3.0  # 3000ms / 1000 = 3.0

    def test_empty_tests(self) -> None:
        """Test with empty tests array."""
        cph_json = {"name": "Empty Tests", "tests": []}
        result = cph2testcase(cph_json)

        assert result["name"] == "Empty Tests"
        assert result["tests"] == []

    def test_missing_test_fields(self) -> None:
        """Test when test case is missing input or output."""
        cph_json = {
            "name": "Partial Tests",
            "tests": [
                {"input": "1"},
                {"output": "result"},
                {},
            ],
        }
        result = cph2testcase(cph_json)

        assert len(result["tests"]) == 3
        assert result["tests"][0]["input"] == "1"
        assert result["tests"][0]["answer"] == ""
        assert result["tests"][1]["input"] == ""
        assert result["tests"][1]["answer"] == "result"
        assert result["tests"][2]["input"] == ""
        assert result["tests"][2]["answer"] == ""

    def test_time_limit_conversion(self) -> None:
        """Test time limit conversion from milliseconds to seconds."""
        cph_json = {
            "name": "Time Test",
            "tests": [],
            "timeLimit": 500,
        }
        result = cph2testcase(cph_json)
        assert result["timeLimit"] == 0.5

    def test_missing_name(self) -> None:
        """Test when name is missing."""
        cph_json = {"tests": [{"input": "test", "output": "result"}]}
        result = cph2testcase(cph_json)

        assert result["name"] == "Unnamed"

    def test_multiple_test_ids(self) -> None:
        """Test that test IDs are sequential starting from 1."""
        cph_json = {
            "name": "Sequential IDs",
            "tests": [
                {"input": "a", "output": "1"},
                {"input": "b", "output": "2"},
                {"input": "c", "output": "3"},
                {"input": "d", "output": "4"},
                {"input": "e", "output": "5"},
            ],
        }
        result = cph2testcase(cph_json)

        for i, test in enumerate(result["tests"], start=1):
            assert test["id"] == i
