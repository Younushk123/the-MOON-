# Integration handover

## Backend team

- Confirm canonical experiment ID (NASA investigation PSI-69 versus internal experiment registry), media IDs and source IDs.
- Validate `outputs/reference/flex_video_cv_result.json` and `flex_image_cv_result.json` with the actual backend model. Keep the timeline as a separate payload or file.
- Use `src/backend_output.py` to regenerate media-level results with confirmed IDs; the CLI supports configurable IDs.
- Confirm the semantics of `detected`: video = a quality-screened circular envelope; still = a red-excess luminous candidate, not necessarily a flame.
- If exposing an analysis endpoint, test a real request and response, invalid media, missing IDs, no-detection responses, and transport limits. Do not use the exploratory algorithm on arbitrary experiments without validation.

## CV developer

- Install dependencies in the target environment.
- Run all tests, including OpenCV tests, then run the CLI against the original NASA files.
- Compare generated outputs to the reference files using `python -m computer_vision.compare_reference --generated computer_vision/outputs/generated`.
- Keep the original .ipynb and full output ZIP as provenance. This source package is not a replacement for either original.
- Push only after successful reproduction and coordination with the team. No remote repository was modified.

## Status

- Original Kaggle experiment: completed; 46/46 local JSON checks passed.
- Supplied ZIP: 47 entries, including 44 file-manifest records; archive CRC and all 44 SHA-256 hashes verified. This differs from the displayed 48-entry count; the supplied archive is internally consistent.
- Source modules: extracted and compiled; no Kaggle globals or paths in modules.
- Fresh local execution: eight reference tests passed. Four image/algorithm tests skipped because OpenCV is missing; actual original media are not included and the download was unavailable.
- Backend registry and endpoint validation: pending.
