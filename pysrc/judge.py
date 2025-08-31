"""Provides utility functions for checking and converting CPH problem.

Functions:
- task_checker: Compares output with the expected answer for a test case.
- cph2testcase: Converts CPH problem JSON to a testcase dictionary.
"""


def task_checker(ouput: str, answer: str) -> bool:
    """Check if the output matches the expected answer for a test case.

    Args:
        ouput (str): The output string to check.
        answer (str): The expected answer string.

    Returns:
        bool: True if the output matches the answer, False otherwise.

    """
    oup = list(filter(bool, ouput.split()))
    ans = list(filter(bool, answer.split()))
    if len(oup) != len(ans):
        return False
    return all(i.strip() == j.strip() for i, j in zip(oup, ans, strict=False))


def cph2testcase(cph_json: dict) -> dict:
    """Convert a CPH problem JSON to a testcase dictionary.

    Args:
        cph_json (dict): The CPH problem JSON.

    Returns:
        dict: A dictionary containing the problem information and test cases.

    """
    tests = []
    for i, v in enumerate(cph_json.get("tests", []), start=1):
        tests.append(
            {
                "id": i,
                "input": v.get("input", ""),
                "answer": v.get("output", ""),
            },
        )
    return {
        "name": cph_json.get("name", "Unnamed"),
        "tests": tests,
        "memoryLimit": cph_json.get("memoryLimit", 1024),
        "timeLimit": cph_json.get("timeLimit", 3000) / 1000,
    }
