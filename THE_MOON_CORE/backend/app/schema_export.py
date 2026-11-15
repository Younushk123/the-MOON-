"""Export JSON Schema files from the Pydantic models (the validation authority).

    python -m app.schema_export            # writes to <repo>/shared/schemas/
    python -m app.schema_export OUT_DIR

tests/test_schema_export.py fails if the files are out of date with the models.
"""

import json
import sys
from pathlib import Path

from pydantic import BaseModel

from app.models.analysis import AnalysisRequest, AnalysisResult, Comparison, ComparisonRequest
from app.models.experiment import Experiment, Measurement, Source
from app.models.insight import AskRequest, Insight, InsightRequest
from app.models.vision import CVResult, VisionRequest

DEFAULT_OUT_DIR = Path(__file__).resolve().parents[3] / "shared" / "schemas"
SUFFIX = ".schema.json"

MODELS: dict[str, type[BaseModel]] = {
    "experiment": Experiment,
    "measurement": Measurement,
    "source": Source,
    "analysis_result": AnalysisResult,
    "comparison": Comparison,
    "insight": Insight,
    "cv_result": CVResult,
    "analysis_request": AnalysisRequest,
    "comparison_request": ComparisonRequest,
    "insight_request": InsightRequest,
    "assistant_ask_request": AskRequest,
    "vision_request": VisionRequest,
}


def generate() -> dict[str, str]:
    """Map of file name -> JSON Schema text."""
    files = {}
    for name, model in MODELS.items():
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", **model.model_json_schema()}
        files[f"{name}{SUFFIX}"] = json.dumps(schema, indent=2) + "\n"
    return files


def export(out_dir: Path = DEFAULT_OUT_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = generate()
    for stale in out_dir.glob(f"*{SUFFIX}"):
        if stale.name not in files:
            stale.unlink()
    written = []
    for name, text in files.items():
        path = out_dir / name
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)
    return written


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT_DIR
    for p in export(target):
        print(p)
