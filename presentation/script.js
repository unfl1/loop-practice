const slides = Array.from(document.querySelectorAll(".slide"));
const progress = document.querySelector(".progress");
let current = 0;

function show(index) {
  current = Math.max(0, Math.min(slides.length - 1, index));
  slides.forEach((slide, slideIndex) => {
    slide.classList.toggle("active", slideIndex === current);
  });
  if (progress) progress.textContent = `${current + 1} / ${slides.length}`;
}

document.addEventListener("keydown", (event) => {
  const nextKeys = ["ArrowRight", "ArrowDown", "PageDown", " "];
  const prevKeys = ["ArrowLeft", "ArrowUp", "PageUp"];
  if (nextKeys.includes(event.key)) {
    event.preventDefault();
    show(current + 1);
  }
  if (prevKeys.includes(event.key)) {
    event.preventDefault();
    show(current - 1);
  }
});

function scoreText(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : "N/A";
}

function scoreWidth(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 0;
  return Math.max(0, Math.min(100, Math.round(number * 100)));
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
  const overall = document.getElementById("timeline-overall");
  const priority = document.getElementById("timeline-priority");
  const prompt = document.getElementById("timeline-prompt");
  const metricSlots = Array.from(document.querySelectorAll(".timeline-metrics > div"));

  slider.min = 1;
  slider.max = iterations.length;
  slider.value = 1;

  function render(index) {
    const item = iterations[index];
    const evaluation = item.evaluation || {};
    title.textContent = `Iteration ${item.iteration}`;
    image.src = item.imageAsset;
    image.alt = `Iteration ${item.iteration}`;
    overall.textContent = `overall ${scoreText(evaluation.overall_score)}`;

    renderMetric(metricSlots[0], "content", evaluation.content_similarity_score);
    renderMetric(metricSlots[1], "style", evaluation.sketch_style_score);
    renderMetric(metricSlots[2], "overall", evaluation.overall_score);
    renderPriority(priority, evaluation.priority_differences || []);
    prompt.textContent = item.nextPrompt || "기록된 next_prompt가 없습니다.";
  }

  slider.addEventListener("input", () => render(Number(slider.value) - 1));
  render(0);
}

initTimeline();
show(0);
