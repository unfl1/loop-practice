const slides = Array.from(document.querySelectorAll(".slide"));
const progress = document.querySelector(".progress");
let current = 0;
let isProgrammaticScroll = false;

function clampSlideIndex(index) {
  return Math.max(0, Math.min(slides.length - 1, index));
}

function updateProgress() {
  slides.forEach((slide, slideIndex) => {
    slide.classList.toggle("active", slideIndex === current);
  });
  if (progress) progress.textContent = `${current + 1} / ${slides.length}`;
}

function scrollToSlide(index) {
  current = clampSlideIndex(index);
  updateProgress();
  isProgrammaticScroll = true;
  slides[current].scrollIntoView({ behavior: "smooth", block: "start" });
  window.setTimeout(() => {
    isProgrammaticScroll = false;
  }, 700);
}

function nearestSlideIndex() {
  const anchor = window.scrollY + Math.min(window.innerHeight * 0.32, 260);
  let visibleSection = 0;
  slides.forEach((slide, index) => {
    if (slide.offsetTop <= anchor) visibleSection = index;
  });
  return visibleSection;
}

function syncCurrentSlide() {
  if (isProgrammaticScroll) return;
  const nextCurrent = nearestSlideIndex();
  if (nextCurrent !== current) {
    current = nextCurrent;
    updateProgress();
  }
}

function eventStartedInInteractiveControl(event) {
  const target = event.target;
  if (!(target instanceof Element)) return false;
  return Boolean(target.closest("input, textarea, select, button, [contenteditable='true']"));
}

document.addEventListener("keydown", (event) => {
  if (eventStartedInInteractiveControl(event)) return;

  const nextKeys = ["ArrowRight", "ArrowDown", "PageDown", " "];
  const prevKeys = ["ArrowLeft", "ArrowUp", "PageUp"];
  if (nextKeys.includes(event.key)) {
    event.preventDefault();
    scrollToSlide(current + 1);
  }
  if (prevKeys.includes(event.key)) {
    event.preventDefault();
    scrollToSlide(current - 1);
  }
});

window.addEventListener("scroll", syncCurrentSlide, { passive: true });

function scoreText(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : "N/A";
}

function scoreWidth(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 0;
  const normalized = number <= 1 ? number * 100 : number;
  return Math.max(0, Math.min(100, Math.round(normalized)));
}

function renderMetric(container, label, value) {
  container.replaceChildren();

  const metric = document.createElement("div");
  metric.className = "metric";

  const labelNode = document.createElement("span");
  labelNode.textContent = label;

  const track = document.createElement("div");
  track.className = "track";
  const fill = document.createElement("i");
  fill.style.width = `${scoreWidth(value)}%`;
  track.appendChild(fill);

  const valueNode = document.createElement("b");
  valueNode.textContent = scoreText(value);

  metric.append(labelNode, track, valueNode);
  container.appendChild(metric);
}

function renderPriority(container, differences) {
  container.replaceChildren();
  if (!differences.length) {
    const empty = document.createElement("p");
    empty.textContent = "기록된 priority difference가 없습니다.";
    container.appendChild(empty);
    return;
  }

  const list = document.createElement("ul");
  differences.forEach((text) => {
    const item = document.createElement("li");
    item.textContent = text;
    list.appendChild(item);
  });
  container.appendChild(list);
}

function initTimeline() {
  const dataNode = document.getElementById("run-data");
  const slider = document.getElementById("iteration-slider");
  if (!dataNode || !slider) return;

  const data = JSON.parse(dataNode.textContent || "{}");
  const iterations = data.iterations || [];
  if (!iterations.length) return;

  const title = document.getElementById("timeline-title");
  const image = document.getElementById("timeline-image");
  const bestImage = document.getElementById("timeline-best-image");
  const overall = document.getElementById("timeline-overall");
  const selection = document.getElementById("timeline-selection");
  const priority = document.getElementById("timeline-priority");
  const feedback = document.getElementById("timeline-feedback");
  const prompt = document.getElementById("timeline-prompt");
  const metricSlots = Array.from(document.querySelectorAll(".timeline-metrics > div"));

  slider.min = 1;
  slider.max = iterations.length;
  slider.value = 1;

  function render(index) {
    const item = iterations[index];
    const evaluation = item.evaluation || {};
    const candidate = selectedCandidateEvaluation(evaluation, item.selectedCandidate);
    title.textContent = `Iteration ${item.iteration}`;
    image.src = item.imageAsset;
    image.alt = `Iteration ${item.iteration}`;
    if (bestImage) {
      bestImage.src = item.bestSoFarAsset || item.imageAsset;
      bestImage.alt = `Best-so-far at iteration ${item.iteration}`;
    }
    overall.textContent = `iteration ${scoreText(item.iterationScore)}`;

    renderMetric(metricSlots[0], "overall", item.iterationScore);
    renderMetric(metricSlots[1], "best-so-far", item.bestSoFarScore);
    renderMetric(metricSlots[2], "structure", candidate.shape_similarity_score ?? evaluation.content_similarity_score);
    renderMetric(metricSlots[3], "sketch style", candidate.sketch_style_score ?? evaluation.sketch_style_score);
    renderSelection(selection, item);
    renderPriority(priority, evaluation.priority_differences || []);
    renderPriority(feedback, evaluation.suggestions || []);
    prompt.textContent = item.nextPrompt || "기록된 next_prompt가 없습니다.";
  }

  slider.addEventListener("input", () => render(Number(slider.value) - 1));
  render(0);
}

function selectedCandidateEvaluation(evaluation, selectedCandidate) {
  const candidates = evaluation.candidates || [];
  return candidates.find((candidate) => candidate.id === selectedCandidate) || candidates[0] || evaluation;
}

function renderSelection(container, item) {
  if (!container) return;
  container.replaceChildren();

  const status = document.createElement("p");
  status.textContent = item.bestUpdated
    ? "이번 selected candidate가 Best-so-far를 갱신했습니다."
    : "이번 selected candidate보다 이전 Best-so-far가 더 좋아서 기존 best를 유지했습니다.";

  const details = document.createElement("p");
  details.textContent = `selected: ${item.selectedCandidate || "N/A"} · iteration score: ${scoreText(item.iterationScore)} · best-so-far: ${scoreText(item.bestSoFarScore)}`;

  container.append(status, details);
}

initTimeline();
current = nearestSlideIndex();
updateProgress();
