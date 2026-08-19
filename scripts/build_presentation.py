"""Build presentation/index.html from the latest successful run output."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUTS_DIR = ROOT / "inputs"
OUTPUTS_DIR = ROOT / "outputs"
PRESENTATION_DIR = ROOT / "presentation"
ASSETS_DIR = PRESENTATION_DIR / "assets"
LATEST_RUN_ASSETS_DIR = ASSETS_DIR / "latest-run"
INDEX_PATH = PRESENTATION_DIR / "index.html"
BEST_OF_N_SCHEMA_VERSION = "best_of_n_v1"


@dataclass
class IterationResult:
    iteration: int
    image_asset: str
    best_so_far_asset: str
    evaluation: dict
    next_prompt: str
    iteration_score: float | None
    best_so_far_score: float | None
    best_updated: bool
    selected_candidate: str
    candidate_assets: dict[str, str] = field(default_factory=dict)


@dataclass
class RunData:
    run_dir: Path
    summary: dict
    reference_asset: str | None
    iterations: list[IterationResult]
    schema_version: str


@dataclass
class BuildResult:
    updated: bool
    run_dir: Path | None
    iterations: int
    reason: str


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def score(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def score_text(value: object) -> str:
    number = score(value)
    return "N/A" if number is None else f"{number:.2f}"


def pct(value: object) -> int:
    number = score(value)
    if number is None:
        return 0
    normalized = number * 100 if number <= 1 else number
    return max(0, min(100, round(normalized)))


def reference_image() -> Path | None:
    for name in ("pomeranian.png", "pomeranian.jpg", "pomeranian.jpeg"):
        path = INPUTS_DIR / name
        if path.exists():
            return path
    return None


def run_dirs_newest_first() -> list[Path]:
    return sorted(
        [path for path in OUTPUTS_DIR.glob("run_*") if path.is_dir()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def summary_is_successful(summary: dict) -> bool:
    if summary.get("status") != "completed":
        return False
    requested = summary.get("requested_iterations")
    completed = summary.get("completed_iterations")
    return requested == completed and completed not in (None, 0)


def is_best_of_n(summary: dict) -> bool:
    return summary.get("schema_version") == BEST_OF_N_SCHEMA_VERSION


def iteration_number(folder: Path) -> int:
    return int(folder.name.split("_", 1)[1])


def iteration_dirs(run_dir: Path, summary: dict) -> list[Path]:
    pattern = "iteration_*" if is_best_of_n(summary) else "iter_*"
    return sorted([path for path in run_dir.glob(pattern) if path.is_dir()], key=iteration_number)


def run_has_required_iteration_files(run_dir: Path, summary: dict) -> bool:
    dirs = iteration_dirs(run_dir, summary)
    expected_count = summary.get("completed_iterations") or summary.get("requested_iterations")
    if expected_count is not None and len(dirs) != int(expected_count):
        return False
    if not dirs:
        return False

    for folder in dirs:
        if is_best_of_n(summary):
            required = [
                folder / "candidate_01.png",
                folder / "candidate_02.png",
                folder / "candidate_03.png",
                folder / "selected.png",
                folder / "prompt.txt",
                folder / "evaluation.json",
                folder / "next_prompt.txt",
            ]
        else:
            required = [
                folder / "generated.png",
                folder / "prompt.txt",
                folder / "evaluation.json",
                folder / "next_prompt.txt",
            ]
        if any(not path.exists() for path in required):
            return False
    return True


def latest_successful_run() -> tuple[Path | None, dict | None]:
    for run_dir in run_dirs_newest_first():
        summary_path = run_dir / "summary.json"
        if not summary_path.exists():
            continue
        summary = read_json(summary_path)
        if summary_is_successful(summary) and run_has_required_iteration_files(run_dir, summary):
            return run_dir, summary
    return None, None


def reset_latest_run_assets() -> None:
    LATEST_RUN_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for path in LATEST_RUN_ASSETS_DIR.iterdir():
        if path.is_file():
            path.unlink()


def copy_latest_asset(source: Path | None, name: str) -> str | None:
    if source is None or not source.exists():
        return None
    shutil.copy2(source, LATEST_RUN_ASSETS_DIR / name)
    return f"assets/latest-run/{name}"


def candidate_score(candidate: dict) -> float | None:
    return score(candidate.get("overall_score"))


def selected_candidate_entry(evaluation: dict) -> dict:
    selected = evaluation.get("selected_candidate")
    candidates = evaluation.get("candidates", [])
    if selected:
        for candidate in candidates:
            if candidate.get("id") == selected:
                return candidate
    if candidates:
        return max(candidates, key=lambda item: candidate_score(item) or -1)
    return evaluation


def legacy_iteration_score(evaluation: dict) -> float | None:
    return score(evaluation.get("overall_score"))


def load_best_of_n_iteration(
    folder: Path,
    evaluation: dict,
    best_asset_by_iteration: dict[int, str],
) -> IterationResult:
    iteration = int(evaluation.get("iteration", iteration_number(folder)))
    selected_candidate = str(evaluation.get("selected_candidate") or "candidate_01")
    image_asset = copy_latest_asset(folder / "selected.png", f"iteration_{iteration:03d}_selected.png")
    if image_asset is None:
        raise FileNotFoundError(folder / "selected.png")

    candidate_assets: dict[str, str] = {}
    for candidate_id in ("candidate_01", "candidate_02", "candidate_03"):
        asset = copy_latest_asset(folder / f"{candidate_id}.png", f"iteration_{iteration:03d}_{candidate_id}.png")
        if asset:
            candidate_assets[candidate_id] = asset

    best_iteration = int(evaluation.get("best_iteration") or iteration)
    best_asset = best_asset_by_iteration.get(best_iteration, image_asset)
    return IterationResult(
        iteration=iteration,
        image_asset=image_asset,
        best_so_far_asset=best_asset,
        evaluation=evaluation,
        next_prompt=read_text(folder / "next_prompt.txt"),
        iteration_score=score(evaluation.get("selected_score")),
        best_so_far_score=score(evaluation.get("best_so_far_score")),
        best_updated=bool(evaluation.get("best_updated")),
        selected_candidate=selected_candidate,
        candidate_assets=candidate_assets,
    )


def load_legacy_iteration(folder: Path, evaluation: dict, running_best: IterationResult | None) -> IterationResult:
    iteration = int(evaluation.get("iteration", iteration_number(folder)))
    image_asset = copy_latest_asset(folder / "generated.png", f"iter_{iteration:03d}_generated.png")
    if image_asset is None:
        raise FileNotFoundError(folder / "generated.png")

    current_score = legacy_iteration_score(evaluation)
    previous_best = running_best.best_so_far_score if running_best else None
    best_updated = previous_best is None or (current_score is not None and current_score > previous_best)
    best_asset = image_asset if best_updated or running_best is None else running_best.best_so_far_asset
    best_score = current_score if best_updated else previous_best
    return IterationResult(
        iteration=iteration,
        image_asset=image_asset,
        best_so_far_asset=best_asset,
        evaluation=evaluation,
        next_prompt=read_text(folder / "next_prompt.txt"),
        iteration_score=current_score,
        best_so_far_score=best_score,
        best_updated=best_updated,
        selected_candidate="legacy_generated",
    )


def load_successful_run(run_dir: Path, summary: dict) -> RunData:
    reset_latest_run_assets()
    reference_asset = copy_latest_asset(reference_image(), "original_pomeranian.png")
    iterations: list[IterationResult] = []
    schema_version = summary.get("schema_version") or "legacy_single_image"

    if is_best_of_n(summary):
        selected_assets: dict[int, str] = {}
        raw: list[tuple[Path, dict]] = []
        for folder in iteration_dirs(run_dir, summary):
            evaluation = read_json(folder / "evaluation.json")
            iteration = int(evaluation.get("iteration", iteration_number(folder)))
            selected_asset = copy_latest_asset(folder / "selected.png", f"iteration_{iteration:03d}_selected.png")
            if selected_asset is None:
                raise FileNotFoundError(folder / "selected.png")
            selected_assets[iteration] = selected_asset
            raw.append((folder, evaluation))

        for folder, evaluation in raw:
            iterations.append(load_best_of_n_iteration(folder, evaluation, selected_assets))
    else:
        running_best: IterationResult | None = None
        for folder in iteration_dirs(run_dir, summary):
            evaluation = read_json(folder / "evaluation.json")
            item = load_legacy_iteration(folder, evaluation, running_best)
            if item.best_updated:
                running_best = item
            iterations.append(item)

    return RunData(
        run_dir=run_dir,
        summary=summary,
        reference_asset=reference_asset,
        iterations=iterations,
        schema_version=schema_version,
    )


def metric(label: str, value: object) -> str:
    return f"""
    <div class="metric">
      <span>{escape(label)}</span>
      <div class="track"><i style="width:{pct(value)}%"></i></div>
      <b>{score_text(value)}</b>
    </div>
    """


def image_box(asset: str | None, label: str, missing: str = "아직 실행 결과 없음") -> str:
    if asset:
        return f'<div class="image-frame"><img src="{escape(asset)}" alt="{escape(label)}"></div>'
    return f'<div class="no-data">{escape(missing)}</div>'


def selected_eval(iteration: IterationResult) -> dict:
    return selected_candidate_entry(iteration.evaluation)


def first_priority(iteration: IterationResult) -> str:
    items = iteration.evaluation.get("priority_differences", [])
    return str(items[0]) if items else "핵심 수정사항 기록 없음"


def line_chart_from_values(values: list[float | None], label: str) -> str:
    points = [(index, value) for index, value in enumerate(values) if value is not None]
    if not points:
        return '<div class="no-data compact">아직 실행 결과 없음</div>'

    width, height, pad_x, pad_y = 520, 170, 28, 24
    usable_w = width - pad_x * 2
    usable_h = height - pad_y * 2
    max_index = max(1, len(values) - 1)

    def xy(index: int, value: float) -> tuple[float, float]:
        x = pad_x + usable_w * (index / max_index)
        normalized = value if value <= 1 else value / 100
        y = pad_y + usable_h * (1 - max(0, min(1, normalized)))
        return x, y

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in (xy(i, v) for i, v in points))
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4"><title>Iter {i + 1}: {v:.2f}</title></circle>'
        for i, v in points
        for x, y in [xy(i, v)]
    )
    return f"""
    <svg class="line-chart" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)} score line chart">
      <line x1="{pad_x}" y1="{height - pad_y}" x2="{width - pad_x}" y2="{height - pad_y}" class="axis"></line>
      <line x1="{pad_x}" y1="{pad_y}" x2="{pad_x}" y2="{height - pad_y}" class="axis"></line>
      <polyline points="{polyline}" class="series"></polyline>
      {dots}
    </svg>
    """


def score_rows(iterations: list[IterationResult], value_getter) -> str:
    rows = []
    for item in iterations:
        value = value_getter(item)
        rows.append(
            f"""<div class="chart-row">
              <span>Iter {item.iteration}</span>
              <div class="track"><i style="width:{pct(value)}%"></i></div>
              <b>{score_text(value)}</b>
            </div>"""
        )
    return '<div class="chart">' + "".join(rows) + "</div>"


def pill_items(items: list[str], limit: int = 4) -> str:
    if not items:
        return '<div class="no-data compact">아직 실행 결과 없음</div>'
    return '<div class="insight-list">' + "".join(
        f"<p>{escape(str(item))}</p>" for item in items[:limit]
    ) + "</div>"


def best_iteration(data: RunData) -> IterationResult:
    summary_best = data.summary.get("best_iteration")
    if summary_best is not None:
        for item in data.iterations:
            if item.iteration == int(summary_best):
                return item
    return max(data.iterations, key=lambda item: item.best_so_far_score or -1)


def run_payload(data: RunData) -> dict:
    return {
        "runName": data.run_dir.name,
        "schemaVersion": data.schema_version,
        "referenceAsset": data.reference_asset,
        "summary": data.summary,
        "iterations": [
            {
                "iteration": item.iteration,
                "imageAsset": item.image_asset,
                "bestSoFarAsset": item.best_so_far_asset,
                "nextPrompt": item.next_prompt,
                "evaluation": item.evaluation,
                "iterationScore": item.iteration_score,
                "bestSoFarScore": item.best_so_far_score,
                "bestUpdated": item.best_updated,
                "selectedCandidate": item.selected_candidate,
                "candidateAssets": item.candidate_assets,
            }
            for item in data.iterations
        ],
    }


def fixed_slides_legacy() -> list[str]:
    return [
        """
        <section class="slide title-slide center">
          <div class="title-mark">Loop</div>
          <div>
            <p class="eyebrow">AI System Design</p>
            <h1>Loop Engineering</h1>
            <p class="title-sub">한 번 잘 시키는 것에서,<br>반복 구조를 설계하는 것으로</p>
          </div>
        </section>
        """,
        """
        <section class="slide spread">
          <header><p class="eyebrow">Expansion Map</p><h2>AI를 사용하는 관점의 확장</h2></header>
          <div class="evolution">
            <article class="phase"><b>01</b><h3>Prompt</h3><p>좋은 지시가 필요했다.</p><em>무엇을 말할까?</em></article>
            <article class="phase"><b>02</b><h3>Context</h3><p>좋은 지시만으로는 부족했다.</p><em>무엇을 보여줄까?</em></article>
            <article class="phase"><b>03</b><h3>Harness</h3><p>정보만으로는 실행이 부족했다.</p><em>어디서 일하게 할까?</em></article>
            <article class="phase"><b>04</b><h3>Loop</h3><p>한 번의 실행만으로는 개선이 부족했다.</p><em>무엇을 다시 하게 할까?</em></article>
          </div>
          <p class="lead">지시문 설계에서 시작해, 맥락과 작업 환경, 그리고 반복 구조까지 확장된다.</p>
        </section>
        """,
        """
        <section class="slide spread">
          <header><p class="eyebrow">Loop Upgrade</p><h2>Best-of-N + Best-so-far</h2></header>
          <div class="flow big-flow">
            <div class="node mint">3 Candidates</div><div class="arrow">→</div>
            <div class="node violet">Independent Evaluation</div><div class="arrow">→</div>
            <div class="node">Selected</div><div class="arrow">→</div>
            <div class="node mint">Best-so-far</div><div class="arrow">↺</div>
          </div>
          <div class="callout">현재 iteration은 흔들릴 수 있지만, 전체 Best-so-far는 실제로 관측된 최고 결과를 유지한다.</div>
        </section>
        """,
        """
        <section class="slide spread">
          <header><p class="eyebrow">Prompt Engineering</p><h2>AI에게 어떻게 잘 시킬 것인가?</h2></header>
          <div class="flow big-flow">
            <div class="node">사람</div><div class="arrow">→</div>
            <div class="node mint">Prompt</div><div class="arrow">→</div>
            <div class="node violet">AI</div><div class="arrow">→</div>
            <div class="node">결과</div>
          </div>
          <div class="callout">결과가 마음에 들지 않으면 사람이 판단하고, 사람이 다시 프롬프트를 수정한다.</div>
        </section>
        """,
        """
        <section class="slide spread">
          <header><p class="eyebrow">Context Engineering</p><h2>AI가 판단하도록 무엇을 보여줄 것인가?</h2></header>
          <div class="context-map">
            <div class="center-node">AI</div>
            <span>사용자 요구</span><span>이전 대화</span><span>참고 문서</span><span>검색 결과</span>
            <span>메모리</span><span>코드</span><span>현재 상태</span><span>도구 결과</span>
          </div>
          <p class="lead">질문은 “어떻게 말할까?”에서 “무엇을 보여줄까?”로 넓어진다.</p>
        </section>
        """,
        """
        <section class="slide spread">
          <header><p class="eyebrow">Harness Engineering</p><h2>AI가 어떤 환경에서 일하게 할 것인가?</h2></header>
          <div class="harness-shell">
            <div class="agent-core">AI Agent</div>
            <div class="tool-ring">
              <span>File System</span><span>Git</span><span>Test</span><span>Browser</span>
              <span>API</span><span>Logs</span><span>Tools</span><span>Permissions</span>
            </div>
          </div>
          <p class="lead">Harness는 AI가 실제로 작업하고 결과를 확인할 수 있는 실행 무대다.</p>
        </section>
        """,
        """
        <section class="slide spread">
          <header><p class="eyebrow">Loop Engineering</p><h2>결과를 보고 AI가 다시 일하게 하려면?</h2></header>
          <div class="loop-diagram">
            <div class="node">Best Result</div><div class="arrow">→</div>
            <div class="node mint">Generator</div><div class="arrow">→</div>
            <div class="node">Candidates</div><div class="arrow">→</div>
            <div class="node violet">Evaluator</div><div class="arrow">→</div>
            <div class="node">Feedback</div><div class="arrow">→</div>
            <div class="node mint">Refiner</div><div class="arrow">↺</div>
          </div>
          <div class="callout">이전 최고 결과를 기준으로 다시 생성하기 때문에 수렴이 더 안정적이다.</div>
        </section>
        """,
        """
        <section class="slide spread">
          <header><p class="eyebrow">Demo Question</p><h2>단순 스케치 스타일을 유지하면서 더 안정적으로 수렴할 수 있을까?</h2></header>
          <div class="demo-goals">
            <article><b>Input</b><p>실제 포메라니안 사진</p></article>
            <article><b>Generate</b><p>후보 3장</p></article>
            <article><b>Select</b><p>iteration best</p></article>
            <article><b>Keep</b><p>best-so-far</p></article>
          </div>
          <p class="lead">현재 점수는 내려갈 수 있지만, 최고 결과는 유지되며 다음 prompt의 기준이 된다.</p>
        </section>
        """,
        """
        <section class="slide transition-slide center">
          <div>
            <p class="eyebrow">Live Demo</p>
            <h2>Best result에서 후보 3장을 만들고,<br>가장 좋은 결과만 다음 기준으로 남깁니다</h2>
          </div>
          <div class="flow demo-flow">
            <div class="node">Best-so-far</div><div class="arrow">→</div>
            <div class="node mint">3 Candidates</div><div class="arrow">→</div>
            <div class="node violet">Evaluate</div><div class="arrow">→</div>
            <div class="node">Selected</div><div class="arrow">→</div>
            <div class="node mint">Update Best</div><div class="arrow">↺</div>
          </div>
        </section>
        """,
    ]


def fixed_slides_v2() -> list[str]:
    """Return the durable theory chapters; only result chapters are run-driven."""
    return [
        """
        <section class="slide title-slide center">
          <div class="title-mark">Loop</div>
          <div><p class="eyebrow">AI System Design</p><h1>Loop Engineering</h1>
          <p class="title-sub">한 번 잘 시키는 것에서,<br>결과가 다음 실행을 바꾸는 구조로</p></div>
        </section>
        """,
        """
        <section class="slide spread evolution-slide">
          <header><p class="eyebrow">Expansion Map</p><h2>Prompt → Context → Harness → Loop</h2></header>
          <p class="lead">공식적인 역사나 우열이 아니라, AI에게 맡기는 범위를 넓힐 때 추가되는 설계 관점입니다.</p>
          <div class="narrative cols-2">
            <article><h3>왜 관점이 넓어지는가</h3><p>좋은 지시는 방향을 정하지만 판단에 필요한 정보까지 채우지는 못합니다. 정보를 충분히 줘도 실제 파일과 도구에 접근하지 못하면 행동할 수 없고, 행동이 가능해도 결과를 평가해 다시 시도하는 구조는 별도로 설계해야 합니다.</p></article>
            <article><h3>네 관점이 맡는 역할</h3><p>Prompt는 행동 방향을, Context는 판단 재료를, Harness는 실행과 관찰이 가능한 공간을 제공합니다. Loop는 실행 결과 이후 무엇을 평가하고 기억하며 다음 입력을 어떻게 바꿀지 결정합니다.</p></article>
          </div>
          <div class="evolution">
            <article class="phase"><b>01 · Prompt</b><h3>어떻게 지시할까?</h3><p>역할, 목표, 제약과 출력 형식을 설계해 해야 할 일을 분명하게 만듭니다.</p><em>없는 정보까지 제공하지는 못합니다.</em></article>
            <article class="phase"><b>02 · Context</b><h3>무엇을 보여줄까?</h3><p>문서, 대화, 코드와 현재 상태처럼 판단에 필요한 정보를 제공합니다.</p><em>정보만으로 실제 행동할 수는 없습니다.</em></article>
            <article class="phase"><b>03 · Harness</b><h3>어디서 일하게 할까?</h3><p>파일, Git, 테스트, 로그와 권한을 연결해 작업과 관찰을 가능하게 합니다.</p><em>한 번의 행동이 자동 개선을 뜻하지는 않습니다.</em></article>
            <article class="phase"><b>04 · Loop</b><h3>무엇을 다시 하게 할까?</h3><p>평가와 피드백을 다음 입력에 반영해 반복이 개선을 만들게 합니다.</p><em>평가가 다음 실행을 실제로 바꿉니다.</em></article>
          </div>
          <div class="callout">Prompt는 방향, Context는 판단 재료, Harness는 행동 공간, Loop는 결과 이후의 다음 행동을 설계합니다.</div>
        </section>
        """,
        """
        <section class="slide spread concept-slide">
          <header><p class="eyebrow">Prompt Engineering</p><h2>AI에게 어떻게 잘 시킬 것인가?</h2></header>
          <div class="question">핵심 질문 · “AI에게 무엇을, 어떤 조건으로 수행하라고 말할 것인가?”</div>
          <div class="narrative cols-2">
            <article><h3>무엇인가</h3><p>Prompt Engineering은 AI가 원하는 방향으로 응답하도록 지시문의 구조와 표현을 설계하는 접근입니다. 역할, 목표, 배경, 제약조건, 출력 형식과 예시를 조합해 해야 할 일을 명확하게 만듭니다.</p></article>
            <article><h3>왜 필요한가</h3><p>지시가 모호하면 같은 모델도 서로 다른 결과를 냅니다. 좋은 Prompt는 성공 기준과 작업 경계를 선명하게 해 불필요한 추측을 줄이고 결과의 일관성을 높입니다.</p></article>
          </div>
          <div class="flow big-flow"><div class="node">Human</div><div class="arrow">→</div><div class="node mint">Prompt</div><div class="arrow">→</div><div class="node violet">AI</div><div class="arrow">→</div><div class="node">Result</div><div class="arrow">→</div><div class="node">판단·수정</div><div class="arrow">↺</div></div>
          <div class="callout">한계 · Prompt는 행동 방향을 바꾸지만 모델에게 없는 정보를 만들어 주지는 않습니다. 결과가 부족하면 사람이 직접 판단하고 Prompt를 다시 고쳐야 합니다.</div>
        </section>
        """,
        """
        <section class="slide spread concept-slide">
          <header><p class="eyebrow">Context Engineering</p><h2>AI가 판단할 때 무엇을 보여줄 것인가?</h2></header>
          <div class="question">핵심 질문 · “이 판단을 정확히 하려면 지금 어떤 정보를 함께 제공해야 하는가?”</div>
          <div class="narrative cols-2">
            <article><h3>Prompt와의 차이</h3><p>Prompt는 AI에게 무엇을 하라고 말하는 지시입니다. Context는 그 지시를 수행할 때 참고하는 사용자 요구, 이전 대화, 문서, 코드, 검색 결과, 메모리와 현재 상태입니다.</p></article>
            <article><h3>해결하는 문제</h3><p>Context가 빠지면 기존 요구를 놓치거나 잘못된 가정을 하고 현재 프로젝트와 맞지 않는 답을 만들 수 있습니다. 같은 Prompt도 무엇을 함께 보여주느냐에 따라 판단 품질이 달라집니다.</p></article>
          </div>
          <div class="context-map"><div class="center-node">AI</div><span>사용자 요구</span><span>이전 대화</span><span>참고 문서</span><span>검색 결과</span><span>메모리</span><span>코드</span><span>현재 상태</span><span>Tool 결과</span></div>
          <div class="callout">관점은 “어떻게 말할까?”에서 “무엇을 알고 판단하게 할까?”로 넓어집니다. 그러나 충분히 알아도 행동할 환경이 없다면 작업 범위는 제한됩니다.</div>
        </section>
        """,
        """
        <section class="slide spread concept-slide harness-slide">
          <header><p class="eyebrow">Harness Engineering</p><h2>AI가 어떤 환경에서 실제로 일하게 할 것인가?</h2></header>
          <div class="question">핵심 질문 · “AI에게 어떤 도구, 관찰 수단과 권한을 가진 작업 환경을 줄 것인가?”</div>
          <div class="narrative cols-2">
            <article><h3>답변에서 행동으로</h3><p>Harness Engineering은 AI가 텍스트를 생성하는 데서 끝나지 않고 실제 작업을 수행하고 그 결과를 관찰하도록 주변 실행 환경을 설계하는 것입니다. Prompt와 Context를 현실의 행동으로 연결합니다.</p></article>
            <article><h3>검증 가능한 작업</h3><p>파일 저장, 테스트 실행, 브라우저 확인, 로그 분석과 버전 관리를 연결하면 실행 결과를 근거로 다음 결정을 내릴 수 있습니다. 권한은 가능한 행동의 범위와 안전 경계를 정합니다.</p></article>
          </div>
          <div class="harness-shell"><div class="agent-core">AI Agent</div><div class="tool-ring"><span>Tools · 실행 행동</span><span>File System · 읽기/수정</span><span>Git · 변경 이력</span><span>Test · 결과 검증</span><span>Logs · 실패 관찰</span><span>Browser · 화면 확인</span><span>Permissions · 행동 경계</span><span>Execution · 코드 실행</span></div></div>
          <div class="flow agent-flow"><div class="node">코드 작성</div><div class="arrow">→</div><div class="node">파일 저장</div><div class="arrow">→</div><div class="node mint">테스트</div><div class="arrow">→</div><div class="node violet">로그 확인</div><div class="arrow">→</div><div class="node">코드 수정</div></div>
          <div class="callout">Harness는 Loop의 기반이 됩니다. Evaluator가 테스트와 로그를 읽어 다음 행동을 결정하려면 결과를 실제로 관찰할 수 있어야 하기 때문입니다.</div>
        </section>
        """,
        """
        <section class="slide spread concept-slide loop-slide">
          <header><p class="eyebrow">Loop Engineering</p><h2>평가 결과가 다음 실행을 바꾸게 하려면?</h2></header>
          <p class="lead">Loop Engineering은 같은 작업을 여러 번 실행하는 것이 아니라, 이전 실행을 평가하고 그 결과가 다음 실행의 입력을 바꾸도록 반복 구조 자체를 설계하는 것입니다.</p>
          <div class="loop-diagram"><div class="node">Goal</div><div class="arrow">→</div><div class="node mint">Generator</div><div class="arrow">→</div><div class="node">Result</div><div class="arrow">→</div><div class="node violet">Evaluator</div><div class="arrow">→</div><div class="node">Feedback</div><div class="arrow">→</div><div class="node mint">Refiner</div><div class="arrow">↺</div></div>
          <div class="loop-elements"><article><b>Goal</b><p>개선 목표</p></article><article><b>Generator / Actor</b><p>생성과 행동</p></article><article><b>Evaluator</b><p>목표와 비교</p></article><article><b>Feedback</b><p>차이 전달</p></article><article><b>Refiner</b><p>다음 지시 변환</p></article><article><b>State</b><p>결과와 iteration 유지</p></article><article><b>Stop Condition</b><p>목표·횟수·비용</p></article><article><b>Best Result</b><p>최고 결과 보존</p></article></div>
          <div class="repeat-compare"><article><h3>단순 반복</h3><p>같은 Prompt → 실행 → 같은 Prompt → 실행</p><em>결과가 다음 입력을 바꾸지 않습니다.</em></article><article><h3>Loop Engineering</h3><p>실행 → 평가 → Feedback → Prompt 변경 → 재실행</p><em>핵심은 횟수가 아니라 피드백의 영향입니다.</em></article></div>
        </section>
        """,
        """
        <section class="slide spread relationship-slide">
          <header><p class="eyebrow">Harness vs Loop</p><h2>작업 환경과 반복 구조는 다른 질문에 답합니다</h2></header>
          <div class="compare narrative"><article><h3>Harness Engineering</h3><p>AI가 사용할 도구, 파일 접근, 테스트, 로그, 실행 환경과 권한을 설계합니다. 핵심 질문은 “AI에게 어떤 작업 환경을 줄 것인가?”입니다.</p><ul><li>무엇을 실행하고 관찰할 수 있는가?</li><li>어떤 권한과 안전 경계를 가지는가?</li></ul></article><article><h3>Loop Engineering</h3><p>결과 이후 평가, Feedback, 상태 유지, 종료 조건과 최고 결과 보존을 설계합니다. 핵심 질문은 “결과 이후 무엇을 다시 하게 할 것인가?”입니다.</p><ul><li>무엇을 다음 실행에 전달하는가?</li><li>언제 멈추고 무엇을 기억하는가?</li></ul></article></div>
          <div class="harness-boundary"><span>Harness Environment</span><div class="flow"><div class="node mint">Generator</div><div class="arrow">→</div><div class="node violet">Evaluator</div><div class="arrow">→</div><div class="node">Refiner</div><div class="arrow">↺</div></div><p>Harness가 작업 기반을 제공하고, 그 환경 안에서 Loop가 결과를 관찰하며 다음 행동을 결정합니다.</p></div>
        </section>
        """,
        """
        <section class="slide spread demo-intro-slide">
          <header><p class="eyebrow">Demo Transition</p><h2>Loop를 반복하면 실제로 목표에 더 가까워질까?</h2></header>
          <div class="narrative cols-2"><article><h3>왜 이 실험인가</h3><p>실제 포메라니안 사진을 고정 원본으로 두고 첫 결과는 일부러 단순한 손그림으로 제한합니다. 형태 차이가 분명해 평가와 피드백이 다음 결과를 어떻게 바꾸는지 관찰하기 좋습니다.</p></article><article><h3>무엇을 검증하는가</h3><p>이미지 모델의 절대 성능을 자랑하려는 것이 아닙니다. Evaluator가 찾은 구조적 차이를 Prompt Refiner가 다음 입력에 반영할 때 실제 결과가 어떻게 달라지는지 확인합니다.</p></article></div>
          <div class="flow demo-flow"><div class="node">Original Photo</div><div class="arrow">→</div><div class="node mint">Generator</div><div class="arrow">→</div><div class="node">Simple Sketch</div><div class="arrow">→</div><div class="node violet">Evaluator</div><div class="arrow">→</div><div class="node">Feedback</div><div class="arrow">→</div><div class="node mint">Prompt Refiner</div><div class="arrow">↺</div></div>
          <div class="demo-goals"><article><b>Generate</b><p>매 iteration 후보 3장을 생성합니다.</p></article><article><b>Evaluate</b><p>원본과 구조적 차이를 독립 평가합니다.</p></article><article><b>Select</b><p>현재 최고 후보를 선택합니다.</p></article><article><b>Remember</b><p>Best-so-far를 다음 기준으로 보존합니다.</p></article></div>
          <div class="callout">관찰 포인트 · 반복 횟수가 아니라 평가 결과가 실제 다음 Prompt와 생성 결과에 반영되는지를 봅니다.</div>
        </section>
        """,
    ]


def result_card(item: IterationResult, label: str) -> str:
    return f"""
    <article class="result-card">
      <h3>{escape(label)} · Iteration {item.iteration}</h3>
      {image_box(item.image_asset, label)}
      {metric("iteration", item.iteration_score)}
      {metric("best", item.best_so_far_score)}
      <p class="priority">{escape(first_priority(item))}</p>
    </article>
    """


def dynamic_slides(data: RunData) -> list[str]:
    iterations = data.iterations
    best = best_iteration(data)
    first = iterations[0]
    last = iterations[-1]
    iteration_values = [item.iteration_score for item in iterations]
    best_values = [item.best_so_far_score for item in iterations]

    return [
        f"""
        <section class="slide timeline-slide spread result-slide">
          <header>
            <p class="eyebrow">Interactive Timeline · {escape(data.run_dir.name)}</p>
            <h2>Selected result와 Best-so-far를 함께 봅니다</h2>
          </header>
          <div class="timeline-layout">
            <aside class="original-panel">
              <h3>Original Photo</h3>
              {image_box(data.reference_asset, "Original Photo", "원본 이미지 없음")}
            </aside>
            <section class="iteration-panel">
              <div class="iteration-head">
                <div><p class="stage-tag">Selected Iteration</p><h3 id="timeline-title">Iteration</h3></div>
                <div class="score-chip" id="timeline-overall">score</div>
              </div>
              <div class="comparison-pair">
                <article>
                  <h3>Selected image</h3>
                  <div class="image-frame"><img id="timeline-image" src="" alt="Selected iteration"></div>
                </article>
                <article>
                  <h3>Best-so-far image</h3>
                  <div class="image-frame"><img id="timeline-best-image" src="" alt="Best-so-far iteration"></div>
                </article>
              </div>
              <div class="timeline-metrics">
                <div>{metric("overall", 0)}</div>
                <div>{metric("best-so-far", 0)}</div>
                <div>{metric("structure", 0)}</div>
                <div>{metric("sketch style", 0)}</div>
              </div>
            </section>
          </div>
          <div class="slider-wrap">
            <span>Iteration 1</span>
            <input id="iteration-slider" type="range" min="1" max="{len(iterations)}" value="1" step="1">
            <span>Iteration {len(iterations)}</span>
          </div>
          <div class="timeline-details">
            <article><h3>Selection</h3><div id="timeline-selection"></div></article>
            <article><h3>Priority Differences</h3><div id="timeline-priority"></div></article>
            <article><h3>Feedback</h3><div id="timeline-feedback"></div></article>
            <article><h3>Next Prompt</h3><pre id="timeline-prompt"></pre></article>
          </div>
        </section>
        """,
        f"""
        <section class="slide spread result-slide">
          <header><p class="eyebrow">Results Overview</p><h2>Original, First, Best-so-far, Last</h2></header>
          <p class="lead">첫 결과와 마지막 결과만 비교하지 않고, 지금까지 관찰된 최고 결과를 함께 봅니다. 마지막 iteration이 항상 최고라는 보장은 없기 때문에 Best-so-far를 별도로 보존합니다.</p>
          <div class="summary-grid">
            <article class="result-card"><h3>Original</h3>{image_box(data.reference_asset, "Original Photo", "원본 이미지 없음")}</article>
            {result_card(first, "First")}
            {result_card(best, "Best")}
            {result_card(last, "Last")}
          </div>
        </section>
        """,
        f"""
        <section class="slide spread result-slide">
          <header><p class="eyebrow">Score Movement</p><h2>현재 점수와 Best-so-far 점수</h2></header>
          <div class="score-grid">
            <article class="card score-card"><h3>Iteration score</h3>{line_chart_from_values(iteration_values, "iteration")}{score_rows(iterations, lambda item: item.iteration_score)}</article>
            <article class="card score-card"><h3>Best-so-far score</h3>{line_chart_from_values(best_values, "best so far")}{score_rows(iterations, lambda item: item.best_so_far_score)}</article>
            <article class="card score-card"><h3>Update events</h3>{pill_items([f"Iter {item.iteration}: {'updated' if item.best_updated else 'kept'} · selected {item.selected_candidate}" for item in iterations], limit=len(iterations))}</article>
          </div>
        </section>
        """,
        f"""
        <section class="slide spread result-slide">
          <header><p class="eyebrow">Result Analysis</p><h2>Best-of-N이 보여주는 것</h2></header>
          <div class="compare">
            <article class="card"><h3>Best에서 맞은 요소</h3>{pill_items(selected_eval(best).get("matched_points", best.evaluation.get("matched_points", [])))}</article>
            <article class="card"><h3>아직 어려운 요소</h3>{pill_items(selected_eval(best).get("differences", best.evaluation.get("differences", [])))}</article>
          </div>
          <div class="callout">Iteration score는 흔들릴 수 있지만 Best-so-far는 실제 최고 결과를 유지한다. 그래서 다음 생성 기준이 덜 흔들린다.</div>
        </section>
        """,
        """
        <section class="slide center conclusion-slide">
          <div>
            <p class="eyebrow">Conclusion</p>
            <h2>좋은 Loop는<br>생성만 반복하지 않고<br>선택과 기억을 함께 설계한다.</h2>
          </div>
          <div class="conclusion-strip">
            <span>3 Candidates</span>
            <span>Independent Evaluation</span>
            <span>Selected Result</span>
            <span>Best-so-far</span>
          </div>
        </section>
        """,
    ]


def no_data_slides(reason: str) -> list[str]:
    return [
        f"""
        <section class="slide spread">
          <header><p class="eyebrow">Experiment Results</p><h2>실험 결과</h2></header>
          <div class="no-data">아직 실행 결과 없음</div>
          <p class="lead">{escape(reason)}</p>
        </section>
        """,
    ]


def build_html(data: RunData | None, reason: str = "no successful complete run found") -> str:
    slides = fixed_slides_v2() + (dynamic_slides(data) if data else no_data_slides(reason))
    payload = run_payload(data) if data else {"runName": None, "referenceAsset": None, "summary": {}, "iterations": []}
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Loop Engineering</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <main class="deck">
    {''.join(slides)}
  </main>
  <div class="progress"></div>
  <script id="run-data" type="application/json">{data_json}</script>
  <script src="script.js"></script>
</body>
</html>
"""


def build_presentation() -> BuildResult:
    run_dir, summary = latest_successful_run()
    if run_dir is None or summary is None:
        return BuildResult(False, None, 0, "no successful complete run found")

    PRESENTATION_DIR.mkdir(parents=True, exist_ok=True)
    data = load_successful_run(run_dir, summary)
    INDEX_PATH.write_text(build_html(data), encoding="utf-8")
    return BuildResult(True, run_dir, len(data.iterations), "presentation updated")


def main() -> None:
    result = build_presentation()
    print(f"Updated: {result.updated}")
    print(f"Run: {result.run_dir if result.run_dir else 'none'}")
    print(f"Iterations included: {result.iterations}")
    print(f"Reason: {result.reason}")


if __name__ == "__main__":
    main()
