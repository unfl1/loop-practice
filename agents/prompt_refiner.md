# Prompt Refiner

The Prompt Refiner converts the Evaluator result into the next generation prompt.

## Inputs

- Current prompt.
- Evaluator result.
- Current iteration number.

## Output

- Next prompt for the following iteration.

## Core Rules

- Reflect only the Evaluator's `priority_differences`.
- Preserve elements listed as already matching unless they conflict with a higher-priority correction.
- Keep the prompt focused and concise.
- Do not let the prompt grow with unnecessary repeated instructions.
- Do not add realistic fur detail, advanced shading, digital painting language, 3D rendering language, or high-detail illustration language.
- Keep the output style simple, hand-drawn, and line-based.

## Refinement Limits

Iterations 1-2:

- Apply up to 2 priority differences.
- Focus on large structure, such as face/body ratio, ear size and placement, overall silhouette, and pose.

Iterations 3-4:

- Apply up to 3 priority differences.
- Preserve the improved large structure.
- Add selected refinements such as eye position, nose position, or composition when included by the Evaluator.

Iterations 5 and later:

- Apply up to 5 priority differences.
- More actively adjust face proportions, ears, eyes, nose, silhouette, pose, and composition when selected by the Evaluator.
- The line drawing may become slightly more precise, but it must still look like a simple sketch.

## Prompt Style

The next prompt should:

- Name the simple sketch style clearly.
- Mention the selected structural changes.
- Keep the existing successful traits.
- Avoid asking for high realism or polished rendering.
- Stay short enough to make each iteration's intent easy to explain during a presentation.
