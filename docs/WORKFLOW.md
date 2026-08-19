# Workflow

This project runs a simple Loop Engineering workflow for refining a Pomeranian sketch.

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
8. Continue to the next iteration unless a stop condition is met.

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

- The configured maximum iteration count is reached.
- A target score is reached, if a target score is configured.
- An execution error prevents the next step from being completed.

If an image generation or evaluation step does not actually complete, the result must not be recorded as successful.
