import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_entry_files_exist():
    required = [
        "README.md",
        "SKILL.md",
        "requirements.txt",
        "backend/requirements.txt",
        "start_windows.ps1",
        "start.sh",
        "tools/check_release_readiness.py",
        "tools/check_api_smoke.py",
        "frontend/index.html",
        "frontend/style.css",
        "knowledge/term_kb.json",
        "docs/competition/README.md",
        "docs/competition/demo-script.md",
        "docs/competition/scoring-map.md",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    assert not missing


def test_root_requirements_delegates_to_backend_requirements():
    assert "-r backend/requirements.txt" in (ROOT / "requirements.txt").read_text(encoding="utf-8")


def test_gitignore_blocks_local_runtime_files():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in [".env", ".env.*", ".venv/", "data/", "*.bak"]:
        assert pattern in text


def test_start_scripts_are_portable_text():
    bad_tokens = ["鈥", "馃", "鉁", "�"]
    for relative in ["start_windows.ps1", "start.sh"]:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert ".venv" in text
        assert "requirements.txt" in text
        assert not any(token in text for token in bad_tokens)


def test_tracked_files_do_not_include_local_backups():
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True)
    tracked = result.stdout.splitlines()
    forbidden = [
        path for path in tracked
        if (ROOT / path).exists()
        and (
            path == ".env"
            or (path.startswith(".env.") and path != ".env.example")
            or path.endswith(".bak")
            or ".bak" in path
            or path.startswith("data/")
            or "__pycache__" in path
            or path.endswith(".pyc")
        )
    ]
    assert forbidden == []
