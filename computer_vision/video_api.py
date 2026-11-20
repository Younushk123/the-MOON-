import argparse
import json
from pathlib import Path

from .src.backend_output import export_video_result
from .src.video_analysis import analyze_video


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a video with the PSI-69 FLEX profile.")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--media-id", required=True)
    args = parser.parse_args()

    try:
        analysis = analyze_video(args.video)
        result, _ = export_video_result(
            args.video,
            analysis["timeline"],
            experiment_id="PSI-69",
            media_id=args.media_id,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2

    print(json.dumps(result, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
