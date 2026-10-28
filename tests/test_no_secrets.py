"""No key-like string anywhere in the repo, and no .env file tracked by git."""
import re
import subprocess
from pathlib import Path

PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-or-v1-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[=:]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"),
]
SKIP_DIRS = {".git", ".venv", "venv", "runs", "mlruns", "data", "models", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules"}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yaml", ".yml", ".json", ".cfg", ".ini", ".sh", ".ps1", ".sql", ".env", ".example", ".html", ".js", ".ts"}


def _files(root: Path):
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file() and (p.suffix in TEXT_SUFFIXES or p.name.startswith(".env")):
            yield p


def test_no_secret_like_strings(repo_root):
    hits = []
    for p in _files(repo_root):
        if p.name == "test_no_secrets.py":
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in PATTERNS:
            if pat.search(text):
                hits.append(f"{p.relative_to(repo_root)}: {pat.pattern[:30]}")
    assert not hits, "secret-like strings found:\n" + "\n".join(hits)


def test_no_env_file_tracked(repo_root):
    if not (repo_root / ".git").exists():
        return
    r = subprocess.run(["git", "ls-files"], cwd=repo_root, capture_output=True, text=True)
    tracked = [x for x in r.stdout.splitlines() if Path(x).name == ".env" or Path(x).name.startswith(".env.") and not x.endswith(".example")]
    assert not tracked, f".env tracked by git: {tracked}"
