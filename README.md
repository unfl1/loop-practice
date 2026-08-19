# Loop Engineering Pomeranian Sketch Demo

This project is a presentation demo for Loop Engineering with Codex as the main execution actor.

The goal is to start from an intentionally simple dog doodle and iteratively refine it toward a real Pomeranian reference photo. Each iteration should get closer to the reference in structure and composition while preserving a simple hand-drawn line sketch style.

## Goal

- Use a real Pomeranian photo as the reference image.
- Start the first iteration as a very simple hand-drawn doodle.
- Build the drawing from simple shapes such as circles, lines, and triangles.
- Improve toward the reference photo over repeated iterations.
- Focus on face proportions, ear size and placement, eye and nose placement, head-to-body ratio, pose, silhouette, and composition.
- Keep the style simple, sketch-like, and line-drawn throughout the loop.
- Do not introduce realistic fur, advanced shading, digital painting, or 3D rendering.
- Fix the largest structural differences first.
- Do not artificially raise evaluation scores between iterations.

## Loop Flow

Each iteration follows this loop:

```text
reference image + current prompt
-> Generator
-> generated image
-> Evaluator
-> evaluation
-> Prompt Refiner
-> next prompt
-> next iteration
```

The loop records the image, the actual prompt used, the evaluation result, and the next prompt for every iteration.

## Refinement Strategy

Refinement becomes stronger as the loop progresses.

Iterations 1-2 focus on the biggest structural differences. The refiner may apply up to 2 priority differences, usually face/body ratio, ear size and placement, overall silhouette, or pose.

Iterations 3-4 may apply up to 3 priority differences. The loop should preserve the improved large structure while also adjusting elements such as eye placement, nose placement, and composition.

Iterations 5 and later may apply up to 5 priority differences. If the large structure is reasonably aligned, the loop can adjust face proportions, ears, eyes, nose, silhouette, pose, and composition more actively. The sketch style must still stay simple, but line shapes may become slightly more refined.

## Project Structure

```text
loop/
├── README.md
├── AGENTS.md
├── requirements.txt
├── main.py
├── config.py
├── agents/
│   ├── generator.md
│   ├── evaluator.md
│   └── prompt_refiner.md
├── docs/
│   ├── WORKFLOW.md
│   └── OUTPUT_FORMAT.md
├── src/
│   ├── generator.py
│   ├── evaluator.py
│   ├── prompt_refiner.py
│   └── storage.py
├── inputs/
│   └── .gitkeep
└── outputs/
    └── .gitkeep
```

## Inputs and Outputs

Place the original Pomeranian reference photo in `inputs/`.

Iteration results are saved under `outputs/`, with one folder per iteration. Each iteration should contain the generated image, the prompt that produced it, the evaluation JSON, and the next prompt.

## Demo Notes

This repository is intentionally minimal. It is meant to show the loop clearly during a presentation, not to hide the process behind a complex application.

The early iterations should make the improvement process easy to see by changing only a few important structure elements. Later iterations can widen the refinement scope so the sketch converges more quickly toward the reference photo.
