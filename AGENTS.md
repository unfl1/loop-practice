# Agent Rules

This project uses three roles in a repeated Loop Engineering workflow:

1. Generator
2. Evaluator
3. Prompt Refiner

The orchestrator runs these roles in order for each iteration:

```text
Generator -> Evaluator -> Prompt Refiner
```

The next iteration starts from the `next_prompt.txt` created by the Prompt Refiner.

## Short Run Commands

When the user gives a short execution request such as "루프 5번해", "루프 3번 실행해", or "5 iteration 돌려", interpret the number as the requested iteration count.

For these short commands:

- Use `inputs/pomeranian.png` as the default reference image.
- Create a new run under `outputs/`.
- Execute the existing loop order for the requested number of iterations:

```text
Generator -> Evaluator -> Prompt Refiner
```

- Follow the role instructions in `agents/generator.md`, `agents/evaluator.md`, and `agents/prompt_refiner.md`.
- Follow the workflow in `docs/WORKFLOW.md`.
- Save outputs using the format defined in `docs/OUTPUT_FORMAT.md`.
- Do not reuse or overwrite a previous run unless the user explicitly asks for that.
- Record only steps that were actually completed.
- Do not invent scores, images, prompts, or successful results.

## Role Instructions

Detailed role instructions are stored in:

- `agents/generator.md`
- `agents/evaluator.md`
- `agents/prompt_refiner.md`

Each role should follow its own instruction file and the common rules in this file.

## Common Rules

- Use a real Pomeranian photo as the reference image.
- Keep every generated image in a simple hand-drawn sketch or line drawing style.
- Prefer simple forms such as circles, lines, triangles, and loose outline shapes.
- Do not introduce realistic fur, advanced shading, digital painting, 3D rendering, or polished illustration quality.
- Improve structural similarity over time: face proportions, ear size and placement, eye and nose placement, head-to-body ratio, pose, silhouette, and composition.
- Fix the largest structural differences first.
- Record only results that were actually produced.
- Do not describe a failed or skipped generation as successful.
- Do not invent image files, prompts, evaluations, or scores.

## Scoring Rules

- The Evaluator must judge the current generated image against the reference image.
- The Evaluator must not adjust the current score to match a desired trend.
- Previous iteration scores may be recorded in summaries, but they must not be used to inflate or smooth the current score.
- Scores may increase, stay flat, or decrease depending on the actual result.
- The default overall score formula is:

```text
overall_score = content_similarity_score * 0.8 + sketch_style_score * 0.2
```

## Refinement Strength

The number of priority differences depends on the current iteration number.

Iterations 1-2:

- Select up to 2 `priority_differences`.
- Focus on large structural differences.
- Prioritize face/body ratio, ear size and placement, overall silhouette, and pose.

Iterations 3-4:

- Select up to 3 `priority_differences`.
- Preserve improved large structure.
- Also allow eye placement, nose placement, and composition changes.

Iterations 5 and later:

- Select up to 5 `priority_differences`.
- Adjust more elements together when the large structure is already close.
- Face proportions, ears, eyes, nose, silhouette, pose, and composition may be refined more actively.
- The style must remain a simple sketch, though line shapes may become slightly more precise.
