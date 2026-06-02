#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    ".env.example",
    ".gitattributes",
    ".gitignore",
    "README.md",
    "SKILL.md",
    "requirements.txt",
    "requirements-dev.txt",
    "start_windows.ps1",
    "start.sh",
    "backend/server.py",
    "backend/app/main.py",
    "backend/requirements.txt",
    "frontend/index.html",
    "frontend/style.css",
    "knowledge/term_kb.json",
    "docs/competition/README.md",
    "docs/competition/demo-script.md",
    "docs/competition/scoring-map.md",
    "tools/bootstrap_openclaw_env.py",
    "tools/check_api_smoke.py",
    "tools/check_term_kb.py",
    "tools/openclaw_ai_from_zero.py",
]


SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-or-v1-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|llm_api_key|kimi_api_key)\s*=\s*['\"]?[A-Za-z0-9_-]{20,}"),
]


class ScriptExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_script = False
        self._current: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script":
            attr_map = {name.lower(): value for name, value in attrs}
            script_type = (attr_map.get("type") or "text/javascript").lower()
            src = attr_map.get("src")
            if not src and script_type in {"text/javascript", "application/javascript", "module"}:
                self._in_script = True
                self._current = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_script:
            self._in_script = False
            script = "".join(self._current).strip()
            if script:
                self.scripts.append(script)

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._current.append(data)


def run(cmd: list[str], *, cwd: Path = ROOT, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)


def git_files() -> list[str]:
    result = run(["git", "ls-files"], timeout=20)
    if result.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def add_result(results: list[tuple[str, bool, str]], name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


def check_required_files(results: list[tuple[str, bool, str]]) -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    add_result(results, "required-files", not missing, ", ".join(missing))


def check_python_version(results: list[tuple[str, bool, str]]) -> None:
    version = sys.version_info
    ok = (version.major, version.minor) >= (3, 10)
    add_result(results, "python-version", ok, f"{version.major}.{version.minor}.{version.micro}")


def check_requirements(results: list[tuple[str, bool, str]]) -> None:
    root_req = (ROOT / "requirements.txt").read_text(encoding="utf-8").strip()
    backend_req = (ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8").strip()
    ok = "-r backend/requirements.txt" in root_req and "fastapi" in backend_req.lower()
    add_result(results, "requirements", ok, "root requirements should include backend/requirements.txt")


def check_git_hygiene(results: list[tuple[str, bool, str]]) -> None:
    tracked = git_files()
    if not tracked:
        add_result(results, "git-hygiene", True, "git metadata unavailable; skipped tracked-file checks")
        return

    forbidden = []
    for path in tracked:
        lower = path.lower()
        if not (ROOT / path).exists():
            continue
        if lower == ".env" or (lower.startswith(".env.") and lower != ".env.example"):
            forbidden.append(path)
        if lower.endswith(".bak") or ".bak" in lower:
            forbidden.append(path)
        if lower.startswith("data/") or "__pycache__" in lower or lower.endswith(".pyc"):
            forbidden.append(path)
    add_result(results, "git-hygiene", not forbidden, ", ".join(forbidden))


def check_gitignore(results: list[tuple[str, bool, str]]) -> None:
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    required = [".env", ".env.*", ".venv/", "data/", "*.bak", ".codex-remote-attachments/", "competition_document.md"]
    missing = [item for item in required if item not in text]
    add_result(results, "gitignore", not missing, ", ".join(missing))


def check_no_secrets(results: list[tuple[str, bool, str]]) -> None:
    tracked = git_files()
    if not tracked:
        tracked = [
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in ROOT.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and ".venv" not in path.parts
            and "data" not in path.parts
            and path.name != ".env"
        ]

    findings: list[str] = []
    for relative in tracked:
        path = ROOT / relative
        lower = relative.lower()
        if lower == ".env" or (lower.startswith(".env.") and lower != ".env.example"):
            findings.append(relative)
            continue
        if not path.exists() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".pdf", ".zip"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(relative)
                break
    add_result(results, "secret-scan", not findings, ", ".join(sorted(set(findings))))


def check_start_scripts(results: list[tuple[str, bool, str]]) -> None:
    bad_tokens = ["鈥", "馃", "鉁", "�"]
    problems: list[str] = []
    for relative in ["start_windows.ps1", "start.sh"]:
        text = (ROOT / relative).read_text(encoding="utf-8")
        if any(token in text for token in bad_tokens):
            problems.append(f"{relative}: mojibake marker")
        if ".venv" not in text or "requirements.txt" not in text:
            problems.append(f"{relative}: missing venv/install flow")
    add_result(results, "start-scripts", not problems, "; ".join(problems))


def check_term_kb(results: list[tuple[str, bool, str]]) -> None:
    result = run([sys.executable, "tools/check_term_kb.py"], timeout=60)
    add_result(results, "term-kb", result.returncode == 0, (result.stdout or result.stderr).strip())


def check_backend_import(results: list[tuple[str, bool, str]]) -> None:
    script = "import sys; sys.path.insert(0, 'backend'); from app.main import create_app; app=create_app(); print(app.title)"
    result = run([sys.executable, "-c", script], timeout=40)
    add_result(results, "backend-import", result.returncode == 0, (result.stdout or result.stderr).strip())


def iter_inline_scripts(index_html: Path) -> Iterable[str]:
    parser = ScriptExtractor()
    parser.feed(index_html.read_text(encoding="utf-8"))
    return parser.scripts


def check_frontend_js(results: list[tuple[str, bool, str]], strict: bool) -> None:
    node = shutil.which("node")
    if not node:
        add_result(results, "frontend-js", not strict, "node not found; skipped")
        return

    scripts = list(iter_inline_scripts(ROOT / "frontend" / "index.html"))
    with tempfile.TemporaryDirectory() as tmp:
        failures: list[str] = []
        for index, script in enumerate(scripts, 1):
            path = Path(tmp) / f"inline-{index}.js"
            path.write_text(script, encoding="utf-8")
            result = run([node, "--check", str(path)], timeout=30)
            if result.returncode != 0:
                failures.append(result.stderr.strip() or result.stdout.strip())
    add_result(results, "frontend-js", not failures, "\n".join(failures))


def check_api_health(results: list[tuple[str, bool, str]], base_url: str | None, strict: bool) -> None:
    if not base_url:
        add_result(results, "api-health", True, "no --base-url supplied; skipped")
        return
    try:
        import httpx
    except ImportError:
        add_result(results, "api-health", False, "httpx is not installed")
        return

    try:
        response = httpx.get(f"{base_url.rstrip('/')}/api/health", timeout=10.0)
        data = response.json()
    except Exception as exc:
        add_result(results, "api-health", False, str(exc))
        return
    ok = response.status_code == 200 and data.get("status") == "ok" and data.get("termCount", 0) > 0
    add_result(results, "api-health", ok, str(data))


def print_results(results: list[tuple[str, bool, str]]) -> None:
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        suffix = f" - {detail}" if detail else ""
        print(f"{status} {name}{suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether AI-From-Zero is ready for a clean public release.")
    parser.add_argument("--base-url", default="", help="Optional running service URL, for example http://127.0.0.1:8080")
    parser.add_argument("--strict", action="store_true", help="Fail optional checks instead of skipping them.")
    args = parser.parse_args()

    os.chdir(ROOT)
    results: list[tuple[str, bool, str]] = []
    check_python_version(results)
    check_required_files(results)
    check_requirements(results)
    check_gitignore(results)
    check_git_hygiene(results)
    check_no_secrets(results)
    check_start_scripts(results)
    check_term_kb(results)
    check_backend_import(results)
    check_frontend_js(results, strict=args.strict)
    check_api_health(results, base_url=args.base_url or None, strict=args.strict)

    print_results(results)
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
