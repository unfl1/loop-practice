# Workflow

This project runs a Loop Engineering workflow for refining a Pomeranian sketch.

## Run Continuation

A short request such as "루프 N번해" means "run N additional iterations".

Default behavior:

- Continue the latest successful completed Best-of-N run when one exists.
- If the latest successful run uses the legacy single-image format, preserve it and start a new Best-of-N run.
- Start from the existing last iteration number + 1 when continuing a Best-of-N run.
- Use the latest `next_prompt.txt` as the next iteration's `prompt.txt`.
- Preserve all existing iteration folders.
- Recompute `summary.json` for the full cumulative Best-of-N run after the requested additional iterations complete.

Create a new run when there is no successful Best-of-N run or when the user explicitly asks to start a new run.

## Loop

Each Best-of-N iteration follows this sequence:

```text
original image + current best result + current prompt
-> Generator
-> candidate_01.png, candidate_02.png, candidate_03.png
-> Evaluator
-> independent candidate evaluations
-> select iteration best as selected.png
-> compare selected score with previous best-so-far
-> update or keep best-so-far
-> Prompt Refiner
-> next_prompt.txt
-> next iteration
```

The original Pomeranian photo remains the fixed reference for every iteration.

## Iteration Steps

1. Determine whether to continue the latest successful Best-of-N run or create a new Best-of-N run.
2. Determine the next cumulative iteration number.
3. Use the current Best-so-far image as the baseline when available.
4. Generate three real candidate images.
5. Save all three candidates and the exact prompt used.
6. Evaluate each candidate independently against the reference image.
7. Select the candidate with the highest actual `overall_score`.
8. Save the selected candidate as `selected.png`.
9. Compare `selected_score` with `previous_best_score`.
10. Update Best-so-far only if the selected candidate is better.
11. Save `evaluation.json`.
12. Create `next_prompt.txt` from the selected candidate's priority differences.
13. Continue until the requested additional iteration count is completed.

## Best-so-far Rule

Current iteration scores may decrease. Best-so-far scores must not decrease because the system keeps the previous best result when the current selected candidate is not better.

This monotonic best curve must come from selection, not score manipulation.

Example:

```text
Iteration score: 57 -> 64 -> 61 -> 70 -> 68 -> 75
Best-so-far:     57 -> 64 -> 64 -> 70 -> 70 -> 75
```

## Run Completion

A continuation is successful only when every requested additional iteration completes and all required files are saved.

After a successful continuation:

1. Ensure all cumulative iteration folders remain under the same `outputs/run_...` folder.
2. Generate or update `summary.json` for the full cumulative run.
3. Rebuild the presentation once from the latest successful run.
4. Copy only presentation-required actual assets into `presentation/assets/latest-run/`.
5. Keep `outputs/` out of Git because it is local experiment history.
6. Check `git status`.
7. Verify that no sensitive information or unexpected files are commit candidates.
8. Commit once if there are changes.
9. Push once to `origin/main`.
10. Let GitHub Pages publish the presentation after the final push.

Default post-loop commit message:

```text
chore: update loop experiment results
```

## Failure Rules

- If the requested additional iteration count is not fully completed, do not update the presentation.
- If any candidate image generation, evaluation, selection, or storage step fails, do not automatically push.
- Do not automatically commit or push a failed or partial continuation.
- If sensitive information or unexpected files appear in commit candidates, do not push; report the issue to the user.
- Do not record failed or skipped steps as successful.
- Do not overwrite or delete previous successful iteration results to hide a failure.

## Refinement Strength

The refinement scope grows according to the actual cumulative iteration number.

Iterations 1-2:

- Use up to 2 priority differences.
- Focus on major structural differences.
- Prioritize face/body ratio, ear size and placement, silhouette, and pose.

Iterations 3-4:

- Use up to 3 priority differences.
- Keep the larger structure stable.
- Add eye placement, nose placement, and composition changes when needed.

Iterations 5 and later:

- Use up to 5 priority differences.
- Refine several structural elements together when useful.
- The drawing can use slightly more precise lines, but must remain a simple sketch.

## Stop Conditions

The loop stops when one of these conditions is met:

- The requested additional iteration count is reached.
- An execution error prevents the next step from being completed.
- A target score is reached, if a target score is explicitly configured.

If a stop condition happens before all requested additional iterations complete, treat the continuation as incomplete unless the user explicitly configured that stop condition as successful.
