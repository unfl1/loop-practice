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
    expected_count = summary.get("completed_iterations") or summary.get("requested_iterations")
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

    return RunData(run_dir=run_dir, summary=summary, reference_asset=reference_asset, iterations=iterations)


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
    return 0 if number is None else max(0, min(100, round(number * 100)))


def best_iteration(data: RunData) -> IterationResult:
    summary_best = data.summary.get("best_iteration")
    if summary_best is not None:
        for iteration in data.iterations:
            if iteration.iteration == int(summary_best):
                return iteration
    return max(data.iterations, key=lambda item: score(item.evaluation.get("overall_score")) or -1)


def image_box(asset: str | None, label: str, missing: str = "아직 실행 결과 없음") -> str:
    if asset:
        return f'<div class="image-frame"><img src="{escape(asset)}" alt="{escape(label)}"></div>'
    return f'<div class="no-data">{escape(missing)}</div>'


def metric(label: str, value: object) -> str:
    return f"""
    <div class="metric">
      <span>{escape(label)}</span>
      <div class="track"><i style="width:{pct(value)}%"></i></div>
      <b>{score_text(value)}</b>
    </div>
    """


def first_priority(iteration: IterationResult) -> str:
    items = iteration.evaluation.get("priority_differences", [])
    return str(items[0]) if items else "핵심 수정사항 기록 없음"


def iteration_card(iteration: IterationResult | None, title: str) -> str:
    if iteration is None:
        return f"""
        <article class="result-card empty">
          <h3>{escape(title)}</h3>
          <div class="no-data">아직 실행 결과 없음</div>
        </article>
        """
    ev = iteration.evaluation
    return f"""
    <article class="result-card">
      <h3>Iteration {iteration.iteration}</h3>
      {image_box(iteration.image_asset, f"Iteration {iteration.iteration}")}
      {metric("content", ev.get("content_similarity_score"))}
      {metric("style", ev.get("sketch_style_score"))}
      {metric("overall", ev.get("overall_score"))}
      <p class="priority">{escape(first_priority(iteration))}</p>
    </article>
    """


def score_rows(iterations: list[IterationResult], key: str) -> str:
    rows = []
    for item in iterations:
        value = item.evaluation.get(key)
        rows.append(
            f"""
            <div class="chart-row">
              <span>Iter {item.iteration}</span>
              <div class="track"><i style="width:{pct(value)}%"></i></div>
              <b>{score_text(value)}</b>
            </div>
            """
        )
    return '<div class="chart">' + "".join(rows) + "</div>"


def line_chart(iterations: list[IterationResult], key: str, label: str) -> str:
    values = [score(item.evaluation.get(key)) for item in iterations]
    points = [
        (index, value)
        for index, value in enumerate(values)
        if value is not None
    ]
    if not points:
        return '<div class="no-data compact">아직 실행 결과 없음</div>'

    width = 520
    height = 170
    pad_x = 28
    pad_y = 24
    usable_w = width - pad_x * 2
    usable_h = height - pad_y * 2
    max_index = max(1, len(iterations) - 1)

    def xy(index: int, value: float) -> tuple[float, float]:
        x = pad_x + usable_w * (index / max_index)
        y = pad_y + usable_h * (1 - max(0, min(1, value)))
        return x, y

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in (xy(i, v) for i, v in points))
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4"><title>Iter {iterations[i].iteration}: {v:.2f}</title></circle>'
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


def pill_items(items: list[str], limit: int = 4) -> str:
    if not items:
        return '<div class="no-data compact">아직 실행 결과 없음</div>'
    return '<div class="insight-list">' + "".join(
        f"<p>{escape(str(item))}</p>" for item in items[:limit]
    ) + "</div>"


def run_payload(data: RunData) -> dict:
    return {
        "runName": data.run_dir.name,
        "referenceAsset": data.reference_asset,
        "summary": data.summary,
        "iterations": [
            {
                "iteration": item.iteration,
                "imageAsset": item.image_asset,
                "nextPrompt": item.next_prompt,
                "evaluation": item.evaluation,
            }
            for item in data.iterations
        ],
    }


def fixed_slides() -> list[str]:
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
          <header><p class="eyebrow">Prompt Engineering</p><h2>AI에게 어떻게 잘 시킬 것인가?</h2></header>
          <div class="explain">
            <p>원하는 결과를 얻기 위해 역할, 목표, 제약조건, 출력 형식, 예시를 지시문 안에 설계한다.</p>
            <p>좋은 Prompt는 한 번의 AI 호출 품질을 크게 바꾸지만, 결과 판단과 재작성은 여전히 사람에게 남는다.</p>
          </div>
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
          <div class="explain">
            <p>Prompt가 지시문 자체를 다룬다면, Context는 모델이 판단할 때 필요한 주변 정보를 설계한다.</p>
            <p>정보가 부족하면 좋은 지시문이 있어도 모델은 파일, 상태, 이전 결정, 참고자료를 알 수 없다.</p>
          </div>
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
          <div class="explain">
            <p>Harness는 AI Agent가 실제 작업을 수행하고 결과를 확인할 수 있는 실행 무대다.</p>
            <p>파일을 고치고, 테스트를 돌리고, 로그를 읽고, 브라우저에서 결과를 보는 행동이 가능해진다.</p>
          </div>
          <div class="harness-shell">
            <div class="agent-core">AI Agent</div>
            <div class="tool-ring">
              <span>File System</span><span>Git</span><span>Test</span><span>Browser</span>
              <span>API</span><span>Logs</span><span>Tools</span><span>Permissions</span>
            </div>
          </div>
          <p class="lead">Prompt가 “무엇을 할지”를 알려준다면, Harness는 “어디서, 어떤 도구와 규칙으로 일할지”를 제공한다.</p>
        </section>
        """,
        """
        <section class="slide spread">
          <header><p class="eyebrow">Loop Engineering</p><h2>결과를 보고 AI가 다시 일하게 하려면?</h2></header>
          <div class="explain">
            <p>Loop는 같은 작업을 무작정 여러 번 돌리는 것이 아니다.</p>
            <p>이전 결과를 평가하고, 그 평가가 다음 실행의 입력을 바꾸도록 설계하는 구조다.</p>
          </div>
          <div class="loop-diagram">
            <div class="node">Goal</div><div class="arrow">→</div>
            <div class="node mint">Generator</div><div class="arrow">→</div>
            <div class="node">Result</div><div class="arrow">→</div>
            <div class="node violet">Evaluator</div><div class="arrow">→</div>
            <div class="node">Feedback</div><div class="arrow">→</div>
            <div class="node mint">Refiner</div><div class="arrow">↺</div>
          </div>
          <div class="callout">Loop Engineering은 여러 번 실행하는 것이 아니라, 이전 결과의 평가가 다음 실행의 입력을 바꾸는 구조다.</div>
        </section>
        """,
        """
        <section class="slide spread">
          <header><p class="eyebrow">Compare</p><h2>Harness Engineering vs Loop Engineering</h2></header>
          <div class="compare">
            <article class="card"><p class="stage-tag">Harness = 작업 환경</p><h3>AI가 일할 수 있게 만든다</h3><ul><li>Tools</li><li>File System</li><li>Test / Browser / Logs</li><li>Permissions</li></ul></article>
            <article class="card"><p class="stage-tag">Loop = 반복 과정</p><h3>AI가 결과를 바탕으로 계속 개선하게 만든다</h3><ul><li>Evaluation</li><li>Feedback</li><li>Retry</li><li>Best Result</li></ul></article>
          </div>
          <div class="relationship">Harness 위에서 Loop가 동작한다.</div>
        </section>
        """,
        """
        <section class="slide spread">
          <header><p class="eyebrow">Demo Question</p><h2>Loop를 실제로 만들면 결과가 정말 개선될까?</h2></header>
          <div class="demo-goals">
            <article><b>Input</b><p>실제 포메라니안 사진</p></article>
            <article><b>Start</b><p>일부러 단순한 스케치</p></article>
            <article><b>Evaluate</b><p>원본과 구조 차이 비교</p></article>
            <article><b>Refine</b><p>다음 prompt에 일부만 반영</p></article>
          </div>
          <p class="lead">스케치 스타일은 유지하면서 얼굴 비율, 귀, 눈, 코, 자세, 실루엣이 가까워지는지 확인한다.</p>
        </section>
        """,
        """
        <section class="slide transition-slide center">
          <div>
            <p class="eyebrow">Live Demo</p>
            <h2>이제 직접 Loop Engineering을 돌려보겠습니다</h2>
          </div>
          <div class="flow demo-flow">
            <div class="node">Original Photo</div><div class="arrow">→</div>
            <div class="node mint">Generator</div><div class="arrow">→</div>
            <div class="node">Simple Sketch</div><div class="arrow">→</div>
            <div class="node violet">Evaluator</div><div class="arrow">→</div>
            <div class="node">Feedback</div><div class="arrow">→</div>
            <div class="node mint">Prompt Refiner</div><div class="arrow">↺</div>
          </div>
        </section>
        """,
    ]


def dynamic_slides(data: RunData) -> list[str]:
    iterations = data.iterations
    best = best_iteration(data)
    first = next((item for item in iterations if item.iteration == 1), iterations[0])
    last = iterations[-1]
    selected = [
        ("First", first),
        ("Best", best),
        ("Last", last),
    ]
    comparison_cards = "".join(
        f"""
        <article class="result-card">
          <h3>{label} · Iteration {item.iteration}</h3>
          {image_box(item.image_asset, f"{label} iteration")}
          {metric("overall", item.evaluation.get("overall_score"))}
          <p class="priority">{escape(first_priority(item))}</p>
        </article>
        """
        for label, item in selected
    )

    return [
        f"""
        <section class="slide timeline-slide spread">
          <header>
            <p class="eyebrow">Interactive Timeline · {escape(data.run_dir.name)}</p>
            <h2>Iteration을 움직이며 결과를 비교합니다</h2>
          </header>
          <div class="timeline-layout">
            <aside class="original-panel">
              <h3>Original Photo</h3>
              {image_box(data.reference_asset, "Original Photo", "원본 이미지 없음")}
            </aside>
            <section class="iteration-panel">
              <div class="iteration-head">
                <div><p class="stage-tag">Selected Iteration</p><h3 id="timeline-title">Iteration</h3></div>
                <div class="score-chip" id="timeline-overall">overall</div>
              </div>
              <div class="image-frame"><img id="timeline-image" src="" alt="Selected iteration"></div>
              <div class="timeline-metrics">
                <div>{metric("content", 0)}</div>
                <div>{metric("style", 0)}</div>
                <div>{metric("overall", 0)}</div>
              </div>
            </section>
          </div>
          <div class="slider-wrap">
            <span>Iteration 1</span>
            <input id="iteration-slider" type="range" min="1" max="{len(iterations)}" value="1" step="1">
            <span>Iteration {len(iterations)}</span>
          </div>
          <div class="timeline-details">
            <article><h3>Priority Differences</h3><div id="timeline-priority"></div></article>
            <article><h3>Next Prompt</h3><pre id="timeline-prompt"></pre></article>
          </div>
        </section>
        """,
        f"""
        <section class="slide spread">
          <header><p class="eyebrow">Experiment Summary</p><h2>첫 iteration, best iteration, 마지막 iteration</h2></header>
          <div class="summary-grid">
            <article class="result-card"><h3>Original</h3>{image_box(data.reference_asset, "Original Photo", "원본 이미지 없음")}</article>
            {comparison_cards}
          </div>
        </section>
        """,
        f"""
        <section class="slide spread">
          <header><p class="eyebrow">Score Movement</p><h2>점수는 실제 변화만 보여줍니다</h2></header>
          <div class="score-grid">
            <article class="card score-card"><h3>content_similarity_score</h3>{line_chart(iterations, "content_similarity_score", "content similarity")}{score_rows(iterations, "content_similarity_score")}</article>
            <article class="card score-card"><h3>sketch_style_score</h3>{line_chart(iterations, "sketch_style_score", "sketch style")}{score_rows(iterations, "sketch_style_score")}</article>
            <article class="card score-card"><h3>overall_score</h3>{line_chart(iterations, "overall_score", "overall")}{score_rows(iterations, "overall_score")}</article>
          </div>
        </section>
        """,
        f"""
        <section class="slide spread">
          <header><p class="eyebrow">Result Analysis</p><h2>Loop의 장점과 한계</h2></header>
          <div class="compare">
            <article class="card"><h3>개선된 요소</h3>{pill_items(best.evaluation.get("matched_points", []))}</article>
            <article class="card"><h3>아직 어려운 요소</h3>{pill_items(best.evaluation.get("differences", []))}</article>
          </div>
          <div class="callout">Loop는 항상 한 방향으로 좋아지는 것이 아니다. 한 요소를 수정하면 다른 요소가 흔들릴 수 있고, Evaluator와 Feedback 설계에 따라 수렴 속도가 달라진다.</div>
        </section>
        """,
        """
        <section class="slide center conclusion-slide">
          <div>
            <p class="eyebrow">Conclusion</p>
            <h2>좋은 AI 시스템은<br>좋은 한 번의 답보다<br>좋은 반복 구조를 가진다.</h2>
          </div>
          <div class="conclusion-strip">
            <span>Prompt: 좋은 지시</span>
            <span>Context: 좋은 정보</span>
            <span>Harness: 좋은 환경</span>
            <span>Loop: 좋은 반복</span>
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
        """
        <section class="slide center conclusion-slide">
          <div>
            <p class="eyebrow">Conclusion</p>
            <h2>좋은 AI 시스템은<br>좋은 반복 구조를 가진다.</h2>
          </div>
        </section>
        """,
    ]


def build_html(data: RunData | None, reason: str = "no successful complete run found") -> str:
    slides = fixed_slides() + (dynamic_slides(data) if data else no_data_slides(reason))
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

