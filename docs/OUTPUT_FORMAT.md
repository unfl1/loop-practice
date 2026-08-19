# Output Format

All iteration results for one user request are saved inside one run folder.

Example:

```text
outputs/
└── run_20260819_231500/
    ├── summary.json
    ├── iter_001/
    │   ├── generated.png
    │   ├── prompt.txt
    │   ├── evaluation.json
    │   └── next_prompt.txt
    ├── iter_002/
    │   └── ...
    └── iter_010/
        └── ...
```

`outputs/` is local experiment history and must not be committed to Git.

## Iteration Files

Each `iter_...` folder contains:

- `generated.png`: The generated image for the iteration.
- `prompt.txt`: The exact prompt used to generate `generated.png`.
- `evaluation.json`: The Evaluator result for the generated image.
- `next_prompt.txt`: The next prompt created by the Prompt Refiner.

Do not create these files for steps that did not actually complete.

## evaluation.json

`evaluation.json` must include at least:

```json
{
  "iteration": 1,
  "content_similarity_score": 0.0,
  "sketch_style_score": 0.0,
  "overall_score": 0.0,
  "matched_points": [],
  "differences": [],
  "priority_differences": [],
  "suggestions": []
}
```

Field meanings:

- `iteration`: Current iteration number.
- `content_similarity_score`: Structural and compositional similarity to the reference.
- `sketch_style_score`: Preservation of the simple hand-drawn sketch style.
- `overall_score`: Weighted combined score.
- `matched_points`: Elements that already resemble the reference.
- `differences`: Notable mismatches from the reference.
- `priority_differences`: Most important differences selected for the next prompt.
- `suggestions`: Practical guidance for the next refinement.

The default overall score formula is:

```text
overall_score = content_similarity_score * 0.8 + sketch_style_score * 0.2
```

Scores must be based on the actual current output. They must not be raised only because the iteration number increased.

## summary.json

At the end of a successful run, `outputs/run_.../summary.json` should include:

```json
{
  "status": "completed",
  "stop_reason": "requested_iterations_completed",
  "requested_iterations": 10,
  "completed_iterations": 10,
  "best_iteration": 1,
  "content_similarity_scores": [],
  "sketch_style_scores": [],
  "overall_scores": []
}
```

Field meanings:

- `status`: Run status, such as `completed` or `failed`.
- `stop_reason`: Why the loop stopped.
- `requested_iterations`: Number of iterations requested by the user.
- `completed_iterations`: Number of iterations actually completed.
- `best_iteration`: Iteration with the best actual overall score.
- `content_similarity_scores`: Content similarity score history.
- `sketch_style_scores`: Sketch style score history.
- `overall_scores`: Overall score history.

Only successful complete runs should be used to rebuild and publish the presentation.

## Presentation Assets

When a successful run finishes, copy only the actual assets required by the presentation into:

```text
presentation/assets/latest-run/
```

Do not copy the entire `outputs/` folder into `presentation/`.
Do not create fake images, fake scores, or fake iteration data for the presentation.
