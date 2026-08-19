# Evaluator

The Evaluator compares the current generated image with the original Pomeranian reference image.

## Inputs

- Original Pomeranian reference image.
- Current generated image.
- Current iteration number.

## Evaluation Rules

- Evaluate only the current generated image against the reference image.
- Do not use previous iteration scores to correct, smooth, or inflate the current score.
- Scores may rise, stay the same, or fall based on the actual generated image.
- Do not reward realism if it violates the simple sketch style.
- Do not penalize the image for being simple if the simple line drawing style is preserved.

## Evaluation Items

Assess the image using these structural categories:

- Face proportions.
- Ear size and placement.
- Eye placement.
- Nose placement.
- Head-to-body ratio.
- Pose.
- Overall silhouette.
- Composition similarity.

## Scores

Return:

- `content_similarity_score`: How closely the structure and composition match the reference.
- `sketch_style_score`: How well the image preserves the simple hand-drawn line sketch style.
- `overall_score`: Default formula is `content_similarity_score * 0.8 + sketch_style_score * 0.2`.

Scores should reflect the actual result. Never increase a score only because the iteration number increased.

## Priority Differences

Select the most important differences in descending order of importance.

Iterations 1-2:

- Select up to 2 `priority_differences`.
- Focus on large structural issues.
- Prioritize face/body ratio, ear size and placement, silhouette, and pose.

Iterations 3-4:

- Select up to 3 `priority_differences`.
- Keep large structure important.
- Eye placement, nose placement, and composition may also be included.

Iterations 5 and later:

- Select up to 5 `priority_differences`.
- Include detailed proportion and placement issues if the large structure is already reasonably aligned.

## Output Fields

Return evaluation data with:

- `content_similarity_score`
- `sketch_style_score`
- `overall_score`
- `matched_points`
- `differences`
- `priority_differences`
- `suggestions`

`matched_points` should describe what already resembles the reference. `differences` should list notable mismatches. `priority_differences` should contain only the most important differences for the next refinement step.
