# Output Format

Each iteration should be saved in its own folder under `outputs/`.

Example:

```text
outputs/
└── iter_001/
    ├── generated.png
    ├── prompt.txt
    ├── evaluation.json
    └── next_prompt.txt
```

## Iteration Files

`generated.png`

The generated image for the iteration.

`prompt.txt`

The exact prompt used to generate `generated.png`.

`evaluation.json`

The Evaluator result for the generated image.

`next_prompt.txt`

The next prompt created by the Prompt Refiner.

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

At the end of a run, `outputs/summary.json` should include:

```json
{
  "status": "completed",
  "stop_reason": "max_iterations_reached",
  "best_iteration": 1,
  "content_similarity_scores": [],
  "sketch_style_scores": [],
  "overall_scores": []
}
```

Field meanings:

- `status`: Run status, such as `completed`, `stopped`, or `failed`.
- `stop_reason`: Why the loop stopped.
- `best_iteration`: Iteration with the best actual overall score.
- `content_similarity_scores`: Content similarity score history.
- `sketch_style_scores`: Sketch style score history.
- `overall_scores`: Overall score history.
