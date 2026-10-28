"""Each executed notebook has code cells with outputs and no error output."""
import json

import pytest

CASES = ["01_funnel_retention", "02_experiment_readout", "03_metric_definition_review"]


@pytest.mark.parametrize("folder", CASES)
def test_notebook_executed_without_error(repo_root, folder):
    path = repo_root / "cases" / folder / "notebook.ipynb"
    assert path.exists(), f"{folder}: notebook.ipynb missing, run python -m product_analytics_cases run"
    nb = json.loads(path.read_text(encoding="utf-8"))
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert code, f"{folder}: no code cells"
    errors = [o for c in code for o in c.get("outputs", []) if o.get("output_type") == "error"]
    assert not errors, f"{folder}: error outputs {[e.get('ename') for e in errors]}"
    assert any(c.get("execution_count") for c in code), f"{folder}: notebook was not executed"
