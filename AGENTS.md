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

When the user gives a short execution request such as "루프 5번해", "루프 3번 실행해", or "5 iteration 돌려", interpret the number as the number of additional iterations to run.

Default behavior:

- If a successful completed run already exists, continue that latest successful run.
- Add the requested N iterations after the existing last iteration.
- Example: first "루프 2번해" creates iterations 1-2.
- Example: later "루프 5번해" continues the same run and creates iterations 3-7.
- The final run must retain all existing iteration folders and add the new ones.
- Do not delete, overwrite, or renumber existing iteration results.
- The next iteration number is always the previous last iteration number + 1.
- Use the previous last iteration's `next_prompt.txt` as the next iteration's `prompt.txt`.
- Apply refinement strength using the actual cumulative iteration number.

Create a new run only when the user explicitly asks to start a new run, such as "새 run으로 시작해".

For these short commands:

- Use `inputs/pomeranian.png` as the default reference image.
- Execute the existing loop order for the requested additional iterations:

```text
Generator -> Evaluator -> Prompt Refiner
```

- Follow the role instructions in `agents/generator.md`, `agents/evaluator.md`, and `agents/prompt_refiner.md`.
- Follow the workflow in `docs/WORKFLOW.md`.
- Save outputs using the format defined in `docs/OUTPUT_FORMAT.md`.
- Record only steps that were actually completed.
- Do not invent scores, images, prompts, or successful results.

## Post-loop Workflow

The user's requested additional iteration count is the execution boundary. Do not commit or push during intermediate iterations.

Example: if the latest completed run has iterations 1-2 and the user asks "루프 5번해", iterations 3-7 are the requested additional work. The post-loop workflow may run only after iterations 3-7 complete successfully.

After the requested additional iterations complete successfully:

1. Keep the full cumulative iteration results under the same `outputs/run_...` folder, unless the user explicitly requested a new run.
2. Regenerate `summary.json` for the full cumulative run.
3. Rebuild the presentation exactly once from the latest successful run.
4. Copy or update only the actual result assets needed by the presentation under `presentation/assets/latest-run/`.
5. Keep the entire `outputs/` directory as local experiment history; do not include it in Git.
6. Check `git status`.
7. Confirm that no sensitive information or unexpected files are included in the commit candidates.
8. If there are changes, create exactly one commit.
9. Push exactly once to `origin/main`.
10. GitHub Pages deploys the latest presentation after this final push.

Use this default commit message:

```text
chore: update loop experiment results
```

Failure rules:

- If all requested additional iterations do not complete, do not update the presentation.
- Do not automatically commit or push a failed or partial continuation.
- If image generation, evaluation, or storage fails, do not automatically push.
- If sensitive information or unexpected files are commit candidates, do not push; report the issue to the user first.

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

The number of priority differences depends on the actual cumulative iteration number.

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
