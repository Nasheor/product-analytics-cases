"""The derived-data folders carry licence notes naming the dataset licence, and no raw file is tracked."""
import subprocess


def test_derived_licence_notes(repo_root):
    olist = (repo_root / "data" / "derived" / "olist" / "LICENCE").read_text(encoding="utf-8")
    assert "CC BY-NC-SA 4.0" in olist and "Olist" in olist
    upworthy = (repo_root / "data" / "derived" / "upworthy" / "LICENCE").read_text(encoding="utf-8")
    assert "CC BY 4.0" in upworthy and "Upworthy" in upworthy


def test_licence_check_has_dataset_rows(repo_root):
    text = (repo_root / "LICENCE_CHECK.md").read_text(encoding="utf-8")
    assert "brazilian-ecommerce" in text and "CC BY-NC-SA 4.0" in text
    assert "osf.io/jd64p" in text and "CC BY 4.0" in text


def test_no_raw_file_tracked(repo_root):
    if not (repo_root / ".git").exists():
        return
    r = subprocess.run(["git", "ls-files"], cwd=repo_root, capture_output=True, text=True)
    raw = [x for x in r.stdout.splitlines() if x.startswith("data/raw/")]
    assert not raw, f"raw files tracked by git: {raw}"
