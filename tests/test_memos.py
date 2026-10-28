"""Each memo has the six headings, at most 600 words, and every number with a decimal point or a
percent sign traces to the case's results JSON within rounding."""
import json
import re

import pytest

CASES = {"01_funnel_retention": "case1", "02_experiment_readout": "case2", "03_metric_definition_review": "case3"}
HEADINGS = ["Question", "Data", "Method", "Result", "Recommendation", "Caveats"]
NUMBER = re.compile(r"(?<![\w.])(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+\.\d+|-?\d+)(\s?%)?")


def _values(obj, out):
    if isinstance(obj, dict):
        for v in obj.values():
            _values(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _values(v, out)
    elif isinstance(obj, bool):
        return
    elif isinstance(obj, (int, float)):
        out.append(float(obj))


def _matches(shown: float, decimals: int, pool: list[float]) -> bool:
    tol = 0.5 * 10 ** (-decimals) + 1e-9
    for v in pool:
        for cand in (v, v * 100, v / 100):
            if abs(cand - shown) <= tol:
                return True
    return False


@pytest.mark.parametrize("folder,key", list(CASES.items()))
def test_memo_structure_and_numbers(repo_root, folder, key):
    memo = (repo_root / "cases" / folder / "memo.md").read_text(encoding="utf-8")
    for h in HEADINGS:
        assert re.search(rf"^##\s+{h}\b", memo, re.M), f"{folder}: heading {h} missing"
    words = len(memo.split())
    assert words <= 600, f"{folder}: memo has {words} words"
    assert ";" not in memo, f"{folder}: semicolon in memo"
    res = json.loads((repo_root / "results" / f"{key}.json").read_text(encoding="utf-8"))
    pool: list[float] = []
    _values(res["numbers"], pool)
    _values(res["tables"], pool)
    missing = []
    for m in NUMBER.finditer(memo):
        raw, pct = m.group(1), m.group(2)
        if "." not in raw and not pct:
            continue
        shown = float(raw.replace(",", ""))
        decimals = len(raw.split(".")[1]) if "." in raw else 0
        if not _matches(shown, decimals, pool):
            missing.append(m.group(0))
    assert not missing, f"{folder}: numbers not found in results/{key}.json: {missing}"
    print(f"{folder}: {words} words")
