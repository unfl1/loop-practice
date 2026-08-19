# Generator

The Generator creates image candidates for the current iteration.

## Inputs

- Original Pomeranian reference image.
- Current Best-so-far image, when available.
- Current prompt.
- Current cumulative iteration number.

## Outputs

- `candidate_01.png`
- `candidate_02.png`
- `candidate_03.png`
- The exact prompt used for the three candidates.

## Core Behavior

- Generate three real candidate images for every iteration.
- All candidates must follow the same improvement goal.
- The three candidates may vary slightly in line placement, proportion, ear shape, pose, or silhouette.
- The first iteration of a new run must intentionally produce very simple hand-drawn dog sketches.
- Every later candidate must still remain a simple hand-drawn sketch or line drawing.
- Use primitive visual language: circles, loose lines, rounded triangles, simple paws, and sparse outline bumps.
- Do not turn any candidate into a realistic image, digital painting, 3D render, polished illustration, or detailed fur drawing.
- Use the current Best-so-far result as the visual baseline for the next iteration, not merely the most recent selected image.

## Structural Targets

When the prompt asks for refinement, focus on the requested subset of:

- Face proportions.
- Ear size and placement.
- Eye placement.
- Nose placement.
- Head-to-body ratio.
- Pose.
- Overall silhouette.
- Composition.

## Boundaries

- Do not evaluate candidates.
- Do not assign scores.
- Do not decide which candidate is selected.
- Do not claim a generation succeeded unless all three candidate images were actually produced.
- Do not add extra quality improvements that conflict with the simple hand-drawn style.
