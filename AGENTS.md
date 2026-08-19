# Agent Rules

This project uses three roles in a repeated Loop Engineering workflow:

1. Generator
2. Evaluator
3. Prompt Refiner

The orchestrator keeps this role order:

```text
Generator -> Evaluator -> Prompt Refiner
```

From the next new run onward, each iteration uses Best-of-N candidate generation and Best-so-far selection.

## Short Run Commands

When the user gives a short execution request such as "루프 5번해", "루프 3번 실행해", or "5 iteration 돌려", interpret the number as the number of additional iterations to run.

Default behavior:

- Continue the latest successful completed Best-of-N run when one exists.
- If the latest successful run uses the legacy single-image format, preserve it and start a new Best-of-N run.
- Add the requested N iterations after the existing last iteration in the continued Best-of-N run.
- Do not delete, overwrite, or renumber existing iteration results.
- Use the latest `next_prompt.txt` from the run as the next iteration prompt.
- Apply refinement strength using the actual cumulative iteration number.

Create a new run when:

- No successful completed run exists.
- The latest successful run uses the legacy format.
- The user explicitly asks to start a new run, such as "새 run으로 시작해".

## Per-Iteration Strategy

Each iteration follows this structure:

```text
best result so far
-> generate 3 candidates
-> evaluate each candidate independently
-> select the best candidate for this iteration
-> compare selected candidate with previous best-so-far
-> update or keep best-so-far
-> refine the next prompt from the selected candidate and current best basis
```

Important rules:

- Generate exactly three real candidates before evaluating the iteration.
- Save candidates as `candidate_01.png`, `candidate_02.png`, and `candidate_03.png`.
- Select the highest `overall_score` candidate as `selected.png`.
- The current iteration score may decrease.
- The Best-so-far score must never decrease; keep the previous best when the selected candidate is not better.
- Do not inflate scores to enforce a trend.
- Do not mix problems from unselected candidates into the next prompt.
- The next iteration's improvement basis is the current Best-so-far result, not merely the most recent selected candidate.

## Post-loop Workflow

The user's requested additional iteration count is the execution boundary. Do not commit or push during intermediate iterations.

After the requested additional iterations complete successfully:

1. Keep the full cumulative iteration results under the same `outputs/run_...` folder.
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
- If candidate generation, evaluation, selection, prompt refinement, or storage fails, do not automatically push.
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
- Do not invent image files, prompts, evaluations, selections, or scores.

## Scoring Rules

The Evaluator scores each candidate independently against the original reference image.

Candidate score fields:

- `face_ratio_score`
- `ear_score`
- `eye_position_score`
- `nose_position_score`
- `head_body_ratio_score`
- `pose_score`
- `silhouette_score`
- `composition_score`
- `sketch_style_score`
- `shape_similarity_score`
- `overall_score`

Default formulas:

```text
shape_similarity_score = average(
  face_ratio_score,
  ear_score,
  eye_position_score,
  nose_position_score,
  head_body_ratio_score,
  pose_score,
  silhouette_score,
  composition_score
)

overall_score = shape_similarity_score * 0.85 + sketch_style_score * 0.15
```

Scores may increase, stay flat, or decrease depending on the actual selected result. Best-so-far scores only stay the same or increase because they preserve the best actual result observed so far.

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
