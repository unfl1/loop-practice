# Output Format

New Best-of-N runs use `iteration_...` folders. Existing legacy `iter_...` runs are preserved and may still be read by the presentation builder for historical display, but new runs should use the structure below.

Example:

```text
outputs/
  run_20260820_120000/
    summary.json
    iteration_01/
      candidate_01.png
      candidate_02.png
      candidate_03.png
      selected.png
      prompt.txt
      evaluation.json
      next_prompt.txt
    iteration_02/
      ...
```

`outputs/` is local experiment history and must not be committed to Git.

## Iteration Files

Each `iteration_...` folder contains:

- `candidate_01.png`: First generated candidate.
- `candidate_02.png`: Second generated candidate.
- `candidate_03.png`: Third generated candidate.
- `selected.png`: Copy of the best candidate for the current iteration.
- `prompt.txt`: The exact prompt used to generate the three candidates.
- `evaluation.json`: Candidate evaluations, selected candidate, and Best-so-far status.
- `next_prompt.txt`: The next prompt created by the Prompt Refiner.

Do not create these files for steps that did not actually complete.

## evaluation.json

`evaluation.json` must include at least:

```json
{
  "iteration": 1,
  "candidates": [
    {
      "id": "candidate_01",
      "file": "candidate_01.png",
      "face_ratio_score": 0.0,
      "ear_score": 0.0,
      "eye_position_score": 0.0,
      "nose_position_score": 0.0,
      "head_body_ratio_score": 0.0,
      "pose_score": 0.0,
      "silhouette_score": 0.0,
      "composition_score": 0.0,
      "sketch_style_score": 0.0,
      "shape_similarity_score": 0.0,
      "overall_score": 0.0,
      "matched_points": [],
      "differences": []
    }
  ],
  "selected_candidate": "candidate_01",
  "selected_score": 0.0,
  "previous_best_score": null,
  "best_updated": true,
  "best_so_far_score": 0.0,
  "best_iteration": 1,
  "best_candidate": "candidate_01",
  "priority_differences": [],
  "suggestions": []
}
```

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

Scores must be based on the actual current candidate. They must not be raised only because the iteration number increased.

## Best-so-far Fields

- `selected_candidate`: Highest scoring candidate in the current iteration.
- `selected_score`: `overall_score` of the selected candidate.
- `previous_best_score`: Best score before the current iteration, or `null` for iteration 1.
- `best_updated`: Whether the current selected candidate replaced the previous best.
- `best_so_far_score`: Best score after the current iteration. This value must never decrease.
- `best_iteration`: Iteration that owns the current Best-so-far result.
- `best_candidate`: Candidate id that owns the current Best-so-far result.

## summary.json

At the end of a successful Best-of-N run or successful continuation, `summary.json` should include cumulative run-level information:

```json
{
  "status": "completed",
  "schema_version": "best_of_n_v1",
  "stop_reason": "requested_iterations_completed",
  "requested_iterations": 6,
  "completed_iterations": 6,
  "iteration_scores": [],
  "best_so_far_scores": [],
  "best_iteration": 1,
  "best_candidate": "candidate_01",
  "final_best_score": 0.0
}
```

Field meanings:

- `status`: Run status, such as `completed` or `failed`.
- `schema_version`: Use `best_of_n_v1` for new runs.
- `stop_reason`: Why the loop stopped.
- `requested_iterations`: Total cumulative iteration count expected in the run after the latest successful request.
- `completed_iterations`: Total cumulative iteration count actually completed in the run.
- `iteration_scores`: Selected candidate score history.
- `best_so_far_scores`: Monotonic Best-so-far score history.
- `best_iteration`: Iteration with the final Best-so-far result.
- `best_candidate`: Candidate id with the final Best-so-far result.
- `final_best_score`: Final Best-so-far score.

Only successful complete runs should be used to rebuild and publish the presentation. A partial continuation must not update `summary.json` to `completed`, rebuild the presentation, commit, or push.

## Presentation Assets

When a successful run or continuation finishes, copy only the actual assets required by the presentation into:

```text
presentation/assets/latest-run/
```

For Best-of-N runs, presentation assets should include selected images, Best-so-far images, and candidate images only when they are actually used by the deck.

Do not copy the entire `outputs/` folder into `presentation/`.
Do not create fake images, fake scores, fake candidates, or fake iteration data for the presentation.
