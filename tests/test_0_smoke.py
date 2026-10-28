"""The smoke run must finish in under 10 minutes and regenerate results/."""
import json
import os
import subprocess
import sys
import time


def test_smoke_runs_and_writes_results(repo_root, pkg_name):
    env = dict(os.environ, PYTHONPATH=str(repo_root / "src"))
    t0 = time.time()
    r = subprocess.run([sys.executable, "-m", pkg_name, "smoke"], cwd=repo_root, env=env, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    assert time.time() - t0 < 600
    smoke = json.loads((repo_root / "results" / "smoke.json").read_text(encoding="utf-8"))
    assert smoke.get("smoke_ok") == "yes"
    assert (repo_root / "results" / "readme_numbers.json").exists()
