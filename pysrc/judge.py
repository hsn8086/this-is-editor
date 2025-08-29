

def task_checker(ouput: str, answer: str) -> bool:
    oup = list(filter(bool, ouput.split()))
    ans = list(filter(bool, answer.split()))
    if len(oup)!=len(ans):
        return False
    for i, j in zip(oup, ans):
        if i.strip() != j.strip():
            return False
    return True


def cph2testcase(cph_json: dict) -> dict:
    tests = []
    for i, v in enumerate(cph_json.get("tests", []), start=1):
        tests.append(
            {
                "id": i,
                "input": v.get("input", ""),
                "answer": v.get("output", ""),
            }
        )
    return {
        "name": cph_json.get("name", "Unnamed"),
        "tests": tests,
        "memoryLimit": cph_json.get("memoryLimit", 1024),
        "timeLimit": cph_json.get("timeLimit", 3000) / 1000,
    }
