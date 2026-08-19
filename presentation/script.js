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
  if (event.key === "ArrowRight") {
    event.preventDefault();
    show(current + 1);
  }
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    show(current - 1);
  }
});

show(0);
