# Workflow

This project runs a Loop Engineering workflow for refining a Pomeranian sketch.

## Run Boundary

A user's requested iteration count is treated as one complete run.

Example:

```text
루프 10번해 = one run containing 10 iterations
```

Intermediate iterations are not separate Git publish points. Do not commit or push while the requested run is still in progress.

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

1. Start with the reference image and the current prompt.
2. The Generator creates a simple sketch image.
3. Save the generated image and the exact prompt used.
4. The Evaluator compares the generated image against the reference.
5. Save the evaluation result.
6. The Prompt Refiner creates the next prompt using only the selected priority differences.
7. Save the next prompt.
8. Continue to the next iteration unless a stop condition or failure occurs.

## Run Completion

A run is successful only when every requested iteration completes and all required files are saved.

After a successful run:

1. Save all iteration folders under `outputs/run_...`.
2. Generate `summary.json` inside that run folder.
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

- If the requested iteration count is not fully completed, do not update the presentation.
- If image generation, evaluation, or storage fails, do not automatically push.
- Do not automatically commit or push a failed run.
- If sensitive information or unexpected files appear in commit candidates, do not push; report the issue to the user.
- Do not record failed or skipped steps as successful.

## Refinement Strength

The refinement scope grows over time.

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

- The requested iteration count is reached.
- An execution error prevents the next step from being completed.
- A target score is reached, if a target score is explicitly configured.

If a stop condition happens before all requested iterations complete, treat the run as incomplete unless the user explicitly configured that stop condition as successful.
