"""Post-loop workflow: rebuild presentation, then commit and push once."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_presentation import build_presentation

DEFAULT_COMMIT_MESSAGE = "chore: update loop experiment results"
SENSITIVE_PATTERN = re.compile(
    r"(api[_ -]?key|token|password|secret|private[_ -]?key|access[_ -]?key)\s*[:=]\s*['\"][^'\"]{8,}",
    re.IGNORECASE,
)
EXPECTED_COMMIT_PREFIXES = (
    ".env.example",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "agents/",
    "config.py",
    "docs/",
    "inputs/",
    "main.py",
    "presentation/",
    "requirements.txt",
    "scripts/",
    "src/",
)
FORBIDDEN_COMMIT_PREFIXES = (
    ".env",
    ".venv/",
    "outputs/",
    "__pycache__/",
)


@dataclass
class PostLoopResult:
    completed: bool
    committed: bool
    pushed: bool
    message: str


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def git_status_porcelain() -> list[str]:
    result = run_git(["status", "--porcelain"])
    return [line for line in result.stdout.splitlines() if line.strip()]


def changed_paths() -> list[str]:
    paths: set[str] = set()
    for line in git_status_porcelain():
        if len(line) > 3:
            paths.add(line[3:].strip().replace("\\", "/"))
    return sorted(paths)


def unexpected_paths(paths: list[str]) -> list[str]:
    unexpected: list[str] = []
    for path in paths:
        if path.startswith(FORBIDDEN_COMMIT_PREFIXES):
            unexpected.append(path)
            continue
        if not path.startswith(EXPECTED_COMMIT_PREFIXES):
            unexpected.append(path)
    return unexpected


def tracked_text_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        full_path = ROOT / path
        if not full_path.is_file():
            continue
        if full_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            continue
        files.append(full_path)
    return files


def files_with_sensitive_terms(paths: list[str]) -> list[str]:
    flagged: list[str] = []
    for file_path in tracked_text_files(paths):
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if SENSITIVE_PATTERN.search(text):
            flagged.append(str(file_path.relative_to(ROOT)).replace("\\", "/"))
    return flagged


def run_post_loop(commit_message: str = DEFAULT_COMMIT_MESSAGE) -> PostLoopResult:
    build_result = build_presentation()
    if not build_result.updated:
        return PostLoopResult(False, False, False, build_result.reason)

    paths = changed_paths()
    if not paths:
        return PostLoopResult(True, False, False, "presentation already up to date")

    unexpected = unexpected_paths(paths)
    if unexpected:
        return PostLoopResult(
            False,
            False,
            False,
            "unexpected commit candidates: " + ", ".join(unexpected),
        )

    sensitive = files_with_sensitive_terms(paths)
    if sensitive:
        return PostLoopResult(
            False,
            False,
            False,
            "sensitive terms found in: " + ", ".join(sensitive),
        )

    run_git(["add", *paths])
    staged = run_git(["diff", "--cached", "--name-only"]).stdout.splitlines()
    if not staged:
        return PostLoopResult(True, False, False, "no staged changes")

    run_git(["commit", "-m", commit_message])
    run_git(["push", "origin", "main"])
    return PostLoopResult(True, True, True, "post-loop changes pushed to origin/main")


def main() -> None:
    result = run_post_loop()
    print(f"completed={result.completed}")
    print(f"committed={result.committed}")
    print(f"pushed={result.pushed}")
    print(result.message)


if __name__ == "__main__":
    main()
