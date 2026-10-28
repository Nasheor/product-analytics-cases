"""Every number, table and figure in results/<case>.json names a SQL file in the case's sql/ folder,
a function defined in the case's analysis.py, or a ``module.function()`` defined in the package under
src/, and that source exists."""
import ast
import json

import pytest

CASES = {"01_funnel_retention": "case1", "02_experiment_readout": "case2", "03_metric_definition_review": "case3"}


def _functions(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _package_functions(repo_root, pkg_name):
    out = set()
    for p in (repo_root / "src" / pkg_name).glob("*.py"):
        out |= {f"{p.stem}.{fn}" for fn in _functions(p)}
    return out


@pytest.mark.parametrize("folder,key", list(CASES.items()))
def test_every_result_has_a_named_source(repo_root, pkg_name, folder, key):
    case_dir = repo_root / "cases" / folder
    res = json.loads((repo_root / "results" / f"{key}.json").read_text(encoding="utf-8"))
    sql_files = {p.name for p in (case_dir / "sql").glob("*.sql")}
    funcs = _functions(case_dir / "analysis.py") | _package_functions(repo_root, pkg_name)
    bad = []
    for section in ("numbers", "tables", "figures"):
        for k, item in res[section].items():
            src = item.get("source", "")
            parts = [s.strip() for s in src.split("+")]
            ok = all((s.startswith("sql/") and s[4:] in sql_files) or (s.endswith("()") and s[:-2] in funcs) for s in parts)
            if not src or not ok:
                bad.append(f"{section}.{k}: {src!r}")
    assert not bad, f"{folder}: results without a named source: {bad}"
    for k, fig in res["figures"].items():
        assert (repo_root / fig["file"]).exists(), f"{folder}: figure file missing for {k}"
