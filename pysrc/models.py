"""Defines the data models for the application.

It includes the `Problem` class, which represents the structure of a problem
with various attributes such as name, group, URL, limits, and test details.
"""

from pydantic import BaseModel


class Problem(BaseModel):
    """Represents a problem with various attributes.

    Attributes
    ----------
    name : str
        The name of the problem.
    group : str | None
        The group to which the problem belongs.
    url : str | None
        The URL of the problem.
    interactive : bool | None
        Indicates if the problem is interactive.
    memoryLimit : int | None
        The memory limit for the problem in megabytes.
    timeLimit : int | None
        The time limit for the problem in milliseconds.
    tests : list[dict]
        A list of test cases for the problem.
    testType : str | None
        The type of tests used for the problem.
    input : dict | None
        The input format for the problem.
    output : dict | None
        The output format for the problem.
    languages : dict | None
        The programming languages supported for the problem.
    batch : dict | None
        Batch-specific details for the problem.

    """

    name: str
    group: str | None
    url: str | None
    interactive: bool | None
    memoryLimit: int | None
    timeLimit: int | None
    tests: list[dict] = []
    testType: str | None
    input: dict | None
    output: dict | None
    languages: dict | None
    batch: dict | None
