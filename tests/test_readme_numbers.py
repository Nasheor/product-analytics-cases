"""Every number in results/readme_numbers.json must appear in README.md, so the README never drifts from the run."""
import json


def test_readme_carries_the_measured_numbers(repo_root):
    numbers = json.loads((repo_root / "results" / "readme_numbers.json").read_text(encoding="utf-8"))
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    assert "## Results" in readme
    missing = [f"{k}={v}" for k, v in numbers.items() if str(v) not in readme]
    assert not missing, "README.md is missing measured values: " + ", ".join(missing)


def test_readme_has_no_semicolons(repo_root):
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    assert ";" not in readme, "no semicolons in Markdown (house style)"
