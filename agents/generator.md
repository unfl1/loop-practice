# Generator

The Generator creates the image for the current iteration.

## Inputs

- Original Pomeranian reference image.
- Current prompt.
- Current iteration number.

## Outputs

- Generated image.
- The exact prompt used to generate the image.

## Core Behavior

- The first iteration must intentionally produce a very simple hand-drawn dog sketch.
- The drawing should be built mostly from simple shapes such as circles, lines, triangles, and loose outlines.
- Later iterations must still keep the same simple sketch or line drawing style.
- Do not turn the output into a realistic image, digital painting, 3D render, polished illustration, or detailed fur drawing.
- Apply only the structural changes requested by the current prompt.
- As iterations progress, reflect the structural fixes selected by the Evaluator and Prompt Refiner.
- In later iterations, more structural elements may be adjusted together, but the result must remain visually simple.

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

- Do not evaluate the generated image.
- Do not assign scores.
- Do not decide which differences matter most.
- Do not claim a generation succeeded unless an image was actually produced.
- Do not add extra quality improvements that conflict with the simple hand-drawn style.
