"""Entry point and run-planning helpers for the Loop Engineering demo."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from scripts.post_loop import run_post_loop


ROOT = Path(__file__).resolve().parent
INPUT_IMAGE = ROOT / "inputs" / "pomeranian.png"
OUTPUTS_DIR = ROOT / "outputs"
BEST_OF_N_SCHEMA_VERSION = "best_of_n_v1"
INITIAL_PROMPT = (
    "Create an intentionally very simple hand-drawn black line doodle of the "
    "reference Pomeranian puppy on a plain white background. Generate three "
    "candidate sketches with primitive shapes only: a large round head, tiny "
    "seated body, simple rounded-triangle ears, dot eyes, small oval nose, "
    "two short front paws, and tiny side paws. Keep the centered front-facing "
    "seated composition. Make each candidate a quick childlike sketch or "
    "napkin doodle, not polished. No realistic fur, no advanced shading, no "
    "digital painting, no 3D rendering, no color, no text, no watermark."
)


@dataclass(frozen=True)
class RunPlan:
    """Resolved target for a user-requested batch of additional iterations."""

    run_dir: Path
    reference_image: Path
    start_iteration: int
    end_iteration: int
    current_prompt: str
    continuing_existing_run: bool
    schema_version: str = BEST_OF_N_SCHEMA_VERSION


def read_json(path: Path) -> dict:
    """Read a UTF-8 JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def summary_is_successful(summary: dict) -> bool:
    """Return whether a summary describes a complete successful run."""
    if summary.get("status") != "completed":
        return False
    requested = summary.get("requested_iterations")
    completed = summary.get("completed_iterations")
    return requested == completed and completed not in (None, 0)


def summary_uses_best_of_n(summary: dict) -> bool:
    """Return whether a summary belongs to the new Best-of-N schema."""
    return summary.get("schema_version") == BEST_OF_N_SCHEMA_VERSION


def iteration_number(iteration_dir: Path) -> int:
    """Extract the numeric suffix from an iteration directory."""
    return int(iteration_dir.name.split("_", 1)[1])


def iteration_dirs(run_dir: Path) -> list[Path]:
    """Return Best-of-N iteration directories ordered by number."""
    return sorted(
        [path for path in run_dir.glob("iteration_*") if path.is_dir()],
        key=iteration_number,
    )


def run_has_required_iteration_files(run_dir: Path, summary: dict) -> bool:
    """Check that every completed Best-of-N iteration has required outputs."""
    if not summary_uses_best_of_n(summary):
        return False

    dirs = iteration_dirs(run_dir)
    expected_count = int(summary.get("completed_iterations") or 0)
    if not dirs or len(dirs) != expected_count:
        return False

    for folder in dirs:
        required = (
            folder / "candidate_01.png",
            folder / "candidate_02.png",
            folder / "candidate_03.png",
            folder / "selected.png",
            folder / "prompt.txt",
            folder / "evaluation.json",
            folder / "next_prompt.txt",
        )
        if any(not path.exists() for path in required):
            return False
    return True


def latest_successful_run() -> Path | None:
    """Find the newest complete successful Best-of-N run that can continue."""
    candidates = sorted(
        [path for path in OUTPUTS_DIR.glob("run_*") if path.is_dir()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for run_dir in candidates:
        summary_path = run_dir / "summary.json"
        if not summary_path.exists():
            continue
        summary = read_json(summary_path)
        if summary_is_successful(summary) and run_has_required_iteration_files(run_dir, summary):
            return run_dir
    return None


def create_run_dir() -> Path:
    """Create a new Best-of-N run directory."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    run_dir = OUTPUTS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir()
    return run_dir


def prepare_run_plan(additional_iterations: int, *, force_new_run: bool = False) -> RunPlan:
    """Resolve whether to continue a Best-of-N run or start a new one.

    Short commands such as "루프 5번해" should call this with
    `additional_iterations=5` and `force_new_run=False`. The plan continues the
    latest successful Best-of-N run when available. Legacy single-image runs are
    preserved but are not continued under the new strategy.
    """
    if additional_iterations <= 0:
        raise ValueError("additional_iterations must be greater than zero")
    if not INPUT_IMAGE.exists():
        raise FileNotFoundError(INPUT_IMAGE)

    run_dir = None if force_new_run else latest_successful_run()
    if run_dir is None:
        return RunPlan(
            run_dir=create_run_dir(),
            reference_image=INPUT_IMAGE,
            start_iteration=1,
            end_iteration=additional_iterations,
            current_prompt=INITIAL_PROMPT,
            continuing_existing_run=False,
        )

    dirs = iteration_dirs(run_dir)
    last_iteration_dir = dirs[-1]
    last_iteration = iteration_number(last_iteration_dir)
    next_prompt_path = last_iteration_dir / "next_prompt.txt"
    if not next_prompt_path.exists():
        raise FileNotFoundError(next_prompt_path)

    return RunPlan(
        run_dir=run_dir,
        reference_image=INPUT_IMAGE,
        start_iteration=last_iteration + 1,
        end_iteration=last_iteration + additional_iterations,
        current_prompt=next_prompt_path.read_text(encoding="utf-8").strip(),
        continuing_existing_run=True,
    )


def run_loop(additional_iterations: int, *, force_new_run: bool = False) -> Path | None:
    """Placeholder for the future Loop execution logic.

    The implementation should call `prepare_run_plan()` first, generate three
    candidates per requested iteration, select `selected.png`, maintain
    Best-so-far, and return the completed cumulative run directory only after
    every requested iteration is saved successfully.
    """
    _plan = prepare_run_plan(additional_iterations, force_new_run=force_new_run)
    return None


def main() -> None:
    """CLI placeholder for future non-Codex execution."""
    completed_run = None
    if completed_run is not None:
        run_post_loop()


if __name__ == "__main__":
    main()
