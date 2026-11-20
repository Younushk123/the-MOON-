# Data Schema

Canonical Pydantic models in `backend/app/models/` are the validation authority. JSON Schema exports are
generated in `shared/schemas/`.

Core entities are experiments, measurements, sources, analysis results, comparisons, insights, vision
results, and vision jobs.

Illustrative data in `shared/sample_data/` is clearly not NASA data. PSI-159 CSV records are imported as
unverified local data. PSI-69 video and image outputs are pixel-based measurements and are not physical
calibrations.
