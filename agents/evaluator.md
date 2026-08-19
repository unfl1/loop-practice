# Evaluator

The Evaluator compares generated candidates with the original Pomeranian reference image.

## Inputs

- Original Pomeranian reference image.
- Three current candidate images.
- Previous Best-so-far score and image, when available.
- Current cumulative iteration number.

## Evaluation Rules

- Evaluate each candidate independently against the reference image.
- Do not use previous candidate scores to correct, smooth, or inflate the current candidate score.
- Do not reward realism if it violates the simple sketch style.
- Do not penalize the image for being simple if the simple line drawing style is preserved.
- Scores may rise, stay the same, or fall based on the actual candidate.

## Candidate Scores

For each candidate, return:

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
- `matched_points`
- `differences`

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

## Best Candidate Selection

- Select the candidate with the highest actual `overall_score`.
- Save that image as `selected.png`.
- Record the selected candidate id in `selected_candidate`.
- Record the selected score in `selected_score`.
- If candidates tie, choose the candidate with better `shape_similarity_score`. If still tied, choose the lowest candidate number.

## Best-so-far

- Compare the current selected candidate with the previous Best-so-far result.
- If `selected_score` is greater than `previous_best_score`, set `best_updated` to `true`.
- If `selected_score` is less than or equal to `previous_best_score`, set `best_updated` to `false` and keep the previous Best-so-far.
- `best_so_far_score` must never decrease.
- Do not change candidate scores to make Best-so-far monotonic; monotonicity comes only from keeping the earlier best result.

## Priority Differences

Select priority differences from the selected candidate only. Do not mix in problems from unselected candidates.

Choose the lowest structural score categories first, then translate them into concrete visual differences.

Iterations 1-2:

- Select up to 2 `priority_differences`.
- Focus on large structural issues.

Iterations 3-4:

- Select up to 3 `priority_differences`.
- Keep large structure important.
- Eye placement, nose placement, and composition may also be included.

Iterations 5 and later:

- Select up to 5 `priority_differences`.
- Include detailed proportion and placement issues if the large structure is already reasonably aligned.

## Output Fields

`evaluation.json` must include:

- `iteration`
- `candidates`
- `selected_candidate`
- `selected_score`
- `previous_best_score`
- `best_updated`
- `best_so_far_score`
- `priority_differences`
- `suggestions`

Each candidate entry should include its score fields, `matched_points`, and `differences`.
