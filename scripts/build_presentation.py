"""Build presentation/index.html from the latest successful run output."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUTS_DIR = ROOT / "inputs"
OUTPUTS_DIR = ROOT / "outputs"
PRESENTATION_DIR = ROOT / "presentation"
ASSETS_DIR = PRESENTATION_DIR / "assets"
LATEST_RUN_ASSETS_DIR = ASSETS_DIR / "latest-run"
INDEX_PATH = PRESENTATION_DIR / "index.html"


@dataclass
class IterationResult:
    iteration: int
    image_asset: str
    evaluation: dict
    next_prompt: str


@dataclass
class RunData:
    run_dir: Path
    summary: dict
    reference_asset: str | None
    iterations: list[IterationResult]


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
    if requested is not None or completed is not None:
        return requested == completed and completed not in (None, 0)
    return True


def iteration_dirs(run_dir: Path) -> list[Path]:
    return sorted([path for path in run_dir.glob("iter_*") if path.is_dir()])


def run_has_required_iteration_files(run_dir: Path, summary: dict) -> bool:
    dirs = iteration_dirs(run_dir)
    requested = summary.get("requested_iterations")
    completed = summary.get("completed_iterations")
    expected_count = completed or requested
    if expected_count is not None and len(dirs) != int(expected_count):
        return False

    for folder in dirs:
        required = [
            folder / "generated.png",
            folder / "prompt.txt",
            folder / "evaluation.json",
            folder / "next_prompt.txt",
        ]
        if any(not path.exists() for path in required):
            return False
    return bool(dirs)


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


def load_successful_run(run_dir: Path, summary: dict) -> RunData:
    reset_latest_run_assets()
    reference_asset = copy_latest_asset(reference_image(), "original_pomeranian.png")
    iterations: list[IterationResult] = []

    for folder in iteration_dirs(run_dir):
        evaluation = read_json(folder / "evaluation.json")
        iteration = int(evaluation.get("iteration", len(iterations) + 1))
        image_asset = copy_latest_asset(folder / "generated.png", f"iter_{iteration:03d}_generated.png")
        if image_asset is None:
            raise FileNotFoundError(f"{folder}/generated.png")
        iterations.append(
            IterationResult(
                iteration=iteration,
                image_asset=image_asset,
                evaluation=evaluation,
                next_prompt=read_text(folder / "next_prompt.txt"),
            )
        )

    return RunData(
        run_dir=run_dir,
        summary=summary,
        reference_asset=reference_asset,
        iterations=iterations,
    )


def score(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def score_metric(label: str, value: object) -> str:
    value_num = score(value)
    if value_num is None:
        return f"""
        <div class="metric">
          <p>{escape(label)}</p>
          <div class="track"><span style="width:0%"></span></div>
          <p>N/A</p>
        </div>
        """
    pct = max(0, min(100, round(value_num * 100)))
    return f"""
    <div class="metric">
      <p>{escape(label)}</p>
      <div class="track"><span style="width:{pct}%"></span></div>
      <p>{value_num:.2f}</p>
    </div>
    """


def image_box(asset: str | None, label: str, missing: str = "아직 실행 결과 없음") -> str:
    if asset:
        return f'<div class="image-frame"><img src="{escape(asset)}" alt="{escape(label)}"></div>'
    return f'<div class="no-data">{escape(missing)}</div>'


def first_priority(iteration: IterationResult) -> str:
    items = iteration.evaluation.get("priority_differences", [])
    return str(items[0]) if items else "핵심 수정사항 기록 없음"


def best_iteration(data: RunData) -> IterationResult:
    summary_best = data.summary.get("best_iteration")
    if summary_best is not None:
        for iteration in data.iterations:
            if iteration.iteration == int(summary_best):
                return iteration
    return max(data.iterations, key=lambda item: score(item.evaluation.get("overall_score")) or -1)


def result_card(title: str, iteration: IterationResult | None) -> str:
    if iteration is None:
        return f"""
        <div class="result-card">
          <h3>{escape(title)}</h3>
          <div class="no-data">아직 실행 결과 없음</div>
        </div>
        """
    ev = iteration.evaluation
    return f"""
    <div class="result-card">
      <h3>Iteration {iteration.iteration}</h3>
      {image_box(iteration.image_asset, f"Iteration {iteration.iteration}")}
      {score_metric("content", ev.get("content_similarity_score"))}
      {score_metric("style", ev.get("sketch_style_score"))}
      {score_metric("overall", ev.get("overall_score"))}
      <p class="priority">{escape(first_priority(iteration))}</p>
      <div class="prompt-box">{escape(iteration.next_prompt)}</div>
    </div>
    """


def score_rows(iterations: list[IterationResult], key: str) -> str:
    rows = []
    for iteration in iterations:
        value = score(iteration.evaluation.get(key))
        pct = 0 if value is None else max(0, min(100, round(value * 100)))
        text = "N/A" if value is None else f"{value:.2f}"
        rows.append(
            f"""
            <div class="chart-row">
              <p>Iter {iteration.iteration}</p>
              <div class="track"><span style="width:{pct}%"></span></div>
              <p>{text}</p>
            </div>
            """
        )
    return '<div class="chart">' + "".join(rows) + "</div>"


def pill_list(items: list[str]) -> str:
    if not items:
        return '<div class="no-data">아직 실행 결과 없음</div>'
    return '<div class="grid cols-2">' + "".join(
        f'<div class="card soft"><p>{escape(str(item))}</p></div>' for item in items[:4]
    ) + "</div>"


def fixed_slides() -> list[str]:
    return [
        """
        <section class="slide center">
          <div>
            <div class="eyebrow">AI System Design</div>
            <h1>Loop Engineering</h1>
            <p class="title-sub">한 번 잘 시키는 것에서,<br>반복 구조를 설계하는 것으로</p>
          </div>
          <div class="footer">Codex demo presentation</div>
        </section>
        """,
        """
        <section class="slide spread">
          <div><div class="eyebrow">Evolution</div><h2>AI 시스템 설계의 발전 흐름</h2></div>
          <div class="evolution">
            <div class="card"><div class="stage-tag">Prompt</div><h3>잘 시키기</h3><p>한 번의 지시를 더 정확하게 만든다.</p></div>
            <div class="card"><div class="stage-tag">Context</div><h3>잘 보여주기</h3><p>AI가 판단할 수 있는 정보를 함께 제공한다.</p></div>
            <div class="card"><div class="stage-tag">Harness</div><h3>일할 환경 만들기</h3><p>도구와 파일, 검증 환경을 설계한다.</p></div>
            <div class="card"><div class="stage-tag">Loop</div><h3>다시 시도하게 하기</h3><p>결과를 보고 다음 행동을 바꾼다.</p></div>
          </div>
        </section>
        """,
        """
        <section class="slide spread">
          <div><div class="eyebrow">Prompt Engineering</div><h2>AI에게 어떻게 잘 시킬 것인가?</h2></div>
          <div class="flow">
            <div class="node">사람</div><div class="arrow">→</div>
            <div class="node mint">Prompt</div><div class="arrow">→</div>
            <div class="node violet">AI</div><div class="arrow">→</div>
            <div class="node">결과</div>
          </div>
          <p class="lead">한계: 결과가 마음에 들지 않으면 사람이 다시 프롬프트를 고친다.</p>
        </section>
        """,
        """
        <section class="slide spread">
          <div><div class="eyebrow">Context Engineering</div><h2>AI에게 어떤 정보를 보여줄 것인가?</h2></div>
          <div class="grid cols-3">
            <div class="card"><h3>사용자 요구</h3><p>이번 작업의 목표와 제약</p></div>
            <div class="card"><h3>이전 대화</h3><p>이미 합의된 방향과 상태</p></div>
            <div class="card"><h3>참고자료</h3><p>이미지, 문서, 예시 결과</p></div>
            <div class="card"><h3>메모리</h3><p>반복 중 유지해야 할 정보</p></div>
            <div class="card"><h3>도구</h3><p>AI가 사용할 수 있는 능력</p></div>
            <div class="card"><h3>규칙</h3><p>역할, 금지 조건, 출력 형식</p></div>
          </div>
          <p class="lead">Prompt 자체에서 Context 설계로 확장된다.</p>
        </section>
        """,
        """
        <section class="slide spread">
          <div><div class="eyebrow">Harness Engineering</div><h2>AI가 어떤 환경에서 일하게 할 것인가?</h2></div>
          <div class="grid cols-3">
            <div class="card"><h3>File System</h3><p>입력과 산출물을 남긴다.</p></div>
            <div class="card"><h3>Git</h3><p>변경을 추적한다.</p></div>
            <div class="card"><h3>Test</h3><p>동작을 검증한다.</p></div>
            <div class="card"><h3>Browser</h3><p>결과를 직접 확인한다.</p></div>
            <div class="card"><h3>Logs</h3><p>실행 과정을 기록한다.</p></div>
            <div class="card"><h3>Tools</h3><p>생성, 비교, 저장을 수행한다.</p></div>
          </div>
        </section>
        """,
        """
        <section class="slide spread">
          <div><div class="eyebrow">Loop Engineering</div><h2>AI가 결과를 보고 다시 일하게 하려면?</h2></div>
          <div class="loop-cycle">
            <div class="node">생성</div><div class="node mint">평가</div><div class="node violet">피드백</div><div class="node">수정</div><div class="node mint">재생성</div>
          </div>
          <p class="lead">사람이 하던 반복 개선 과정을 시스템 안에 넣는다.</p>
        </section>
        """,
        """
        <section class="slide spread">
          <div><div class="eyebrow">Compare</div><h2>Harness Engineering vs Loop Engineering</h2></div>
          <div class="compare">
            <div class="card"><div class="stage-tag">Harness = 작업 환경</div><h3>AI가 안정적으로 행동할 수 있는 조건</h3><p>도구, 파일, 테스트, 브라우저, 로그를 갖춘 실행 무대다.</p></div>
            <div class="card"><div class="stage-tag">Loop = 반복 과정</div><h3>AI가 결과를 보고 다음 행동을 바꾸는 구조</h3><p>평가, 피드백, 수정, 재생성을 반복하는 개선 흐름이다.</p></div>
          </div>
          <div class="relation"><div class="node">Harness</div><div class="arrow">위에서</div><div class="node mint">Loop가 동작한다</div></div>
        </section>
        """,
        """
        <section class="slide spread">
          <div><div class="eyebrow">Demo</div><h2>이번 데모 소개</h2></div>
          <div class="grid cols-2">
            <div class="card"><h3>입력</h3><p>실제 포메라니안 사진</p></div>
            <div class="card"><h3>첫 결과</h3><p>일부러 매우 단순한 스케치</p></div>
            <div class="card"><h3>Evaluator</h3><p>원본과 생성 이미지의 차이를 평가</p></div>
            <div class="card"><h3>Prompt Refiner</h3><p>다음 생성 지시를 작게 수정</p></div>
          </div>
          <p class="lead">반복할수록 원본 형태에 가까워지는지 확인한다.</p>
        </section>
        """,
        """
        <section class="slide spread">
          <div><div class="eyebrow">Live Transition</div><h2>이제 직접 돌려보겠습니다</h2></div>
          <div class="flow">
            <div class="node">Original Photo</div><div class="arrow">→</div>
            <div class="node mint">Generator</div><div class="arrow">→</div>
            <div class="node">Simple Sketch</div><div class="arrow">→</div>
            <div class="node violet">Evaluator</div><div class="arrow">→</div>
            <div class="node">Feedback</div><div class="arrow">→</div>
            <div class="node mint">Prompt Refiner</div><div class="arrow">→</div>
            <div class="node">Generator</div>
          </div>
        </section>
        """,
    ]


def dynamic_slides(data: RunData) -> list[str]:
    iterations = data.iterations
    best = best_iteration(data)
    first = next((item for item in iterations if item.iteration == 1), iterations[0])
    selected = [next((item for item in iterations if item.iteration == n), None) for n in (1, 3, 5)]
    if best not in selected:
        selected.append(best)
    result_cards = "".join(result_card(label, item) for label, item in zip(["Iteration 1", "Iteration 3", "Iteration 5", "Best"], selected))

    return [
        f"""
        <section class="slide spread">
          <div><div class="eyebrow">Results · {escape(data.run_dir.name)}</div><h2>실제 Iteration 결과</h2></div>
          <div class="result-grid">
            <div class="result-card"><h3>Original</h3>{image_box(data.reference_asset, "Original Photo", "원본 이미지 없음")}<p class="priority">실제 입력 이미지</p></div>
            {result_cards}
          </div>
        </section>
        """,
        f"""
        <section class="slide spread">
          <div><div class="eyebrow">Scores</div><h2>점수 변화</h2></div>
          <div class="grid cols-3">
            <div class="card"><h3>Content Similarity</h3>{score_rows(iterations, "content_similarity_score")}</div>
            <div class="card"><h3>Sketch Style</h3>{score_rows(iterations, "sketch_style_score")}</div>
            <div class="card"><h3>Overall</h3>{score_rows(iterations, "overall_score")}</div>
          </div>
        </section>
        """,
        f"""
        <section class="slide spread">
          <div><div class="eyebrow">Before / After</div><h2>첫 시도와 best iteration 비교</h2></div>
          <div class="grid cols-3">
            <div class="result-card"><h3>Original</h3>{image_box(data.reference_asset, "Original", "원본 이미지 없음")}</div>
            <div class="result-card"><h3>First Iteration</h3>{image_box(first.image_asset, "First Iteration")}</div>
            <div class="result-card"><h3>Best Iteration</h3>{image_box(best.image_asset, "Best Iteration")}{score_metric("overall", best.evaluation.get("overall_score"))}</div>
          </div>
        </section>
        """,
        f"""
        <section class="slide spread">
          <div><div class="eyebrow">Analysis</div><h2>결과 분석</h2></div>
          <div class="grid cols-2">
            <div class="card"><h3>개선된 부분</h3>{pill_list(best.evaluation.get("matched_points", []))}</div>
            <div class="card"><h3>아직 어려운 부분</h3>{pill_list(best.evaluation.get("differences", []))}</div>
          </div>
          <p class="lead">점수는 항상 증가하지 않을 수 있다. Loop의 장점은 실제 결과를 보고 다음 시도를 좁히는 데 있다.</p>
        </section>
        """,
        f"""
        <section class="slide spread">
          <div><div class="eyebrow">Run Summary</div><h2>최신 run 요약</h2></div>
          <div class="grid cols-3">
            <div class="card"><div class="stage-tag">status</div><h3>{escape(str(data.summary.get("status", "N/A")))}</h3></div>
            <div class="card"><div class="stage-tag">stop reason</div><h3>{escape(str(data.summary.get("stop_reason", "N/A")))}</h3></div>
            <div class="card"><div class="stage-tag">best iteration</div><h3>{escape(str(data.summary.get("best_iteration", best.iteration)))}</h3></div>
          </div>
        </section>
        """,
    ]


def build_html(data: RunData) -> str:
    slides = fixed_slides() + dynamic_slides(data)
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
