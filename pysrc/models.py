from pydantic import BaseModel


class Problem(BaseModel):
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
