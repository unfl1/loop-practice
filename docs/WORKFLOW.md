# Workflow

This project runs a Loop Engineering workflow for refining a Pomeranian sketch.

## Run Continuation

A short request such as "루프 N번해" means "run N additional iterations".

Default behavior:

- Continue the latest successful completed run when one exists.
- Start from the existing last iteration number + 1.
- Use the previous last iteration's `next_prompt.txt` as the next iteration's `prompt.txt`.
- Preserve all existing iteration folders.
- Recompute `summary.json` for the full cumulative run after the requested additional iterations complete.

Create a new run only when the user explicitly asks to start a new run.

Example:

```text
First request:  루프 2번해  -> iterations 1-2
Second request: 루프 5번해  -> iterations 3-7 in the same run
Final run:      iterations 1-7
```

Intermediate iterations are not separate Git publish points. Do not commit or push while the requested additional iterations are still in progress.

## Loop

Each iteration follows this sequence:

```text
original image + current prompt
-> Generator
-> generated image
-> Evaluator
-> evaluation
-> Prompt Refiner
-> next prompt
-> next iteration
```

The original Pomeranian photo remains the fixed reference for every iteration.

## Iteration Steps

1. Determine whether to continue the latest successful run or create a new run.
2. Determine the next cumulative iteration number.
3. Start with the reference image and the current prompt.
4. The Generator creates a simple sketch image.
5. Save the generated image and the exact prompt used.
6. The Evaluator compares the generated image against the reference.
7. Save the evaluation result.
8. The Prompt Refiner creates the next prompt using only the selected priority differences.
9. Save the next prompt.
10. Continue until the requested additional iteration count is completed.

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
- If image generation, evaluation, or storage fails, do not automatically push.
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
