# THE MOON | FLEX Computer Vision

Computer vision contribution by Muhammad Ahsan for the NASA Space Apps Challenge — Flame in Freefall. This is the standalone refactor of the supplied FLEX notebook, not a new detector.

## Scope

The video profile targets the specific published FLEX recording (960 × 540, 30 FPS, 693 frames). It uses the original blue-minus-red RANSAC circle, phase gating, quality screening, reference-assisted partial arcs, compact luminous candidates, intensity cores and later red-signal analysis. The independent still-image path uses the original multilevel red/blue-excess analysis. This profile is retrospective, not a real-time or arbitrary-video detector. Geometry, thresholds, ROI and baseline frames are recording-specific.

## Installation and execution

From the directory containing `computer_vision/`:

```bash
python -m pip install -r computer_vision/requirements.txt
python -m unittest discover -s computer_vision/tests -v
python -m computer_vision --video /path/to/flex_combustion_test.mp4 --image /path/to/flex_companion_image.jpg --output computer_vision/outputs/generated --annotate
```

For image-only testing, omit `--video` and `--annotate`. The command is offline after installing dependencies and obtaining the original media. `--annotate` writes an MP4V preview; existing Kaggle H.264 annotated videos are in the separately supplied deliverables ZIP. Do not use any annotated or `flex_integrated_raw.mp4` export as source video (it is an annotated intermediate).

The original full notebook and 66 MB analysis deliverables ZIP are separate supplied artifacts. A source-only notebook is included here so the GitHub repository can remain lightweight. Keep the full original notebook and archive outside Git unless the team agrees on storage.

## API

```python
from computer_vision.src.video_analysis import analyze_video
from computer_vision.src.image_analysis import analyze_image
from computer_vision.src.backend_output import export_video_result, export_image_result

analysis = analyze_video('flex_combustion_test.mp4')
video_result, representative_frame = export_video_result('flex_combustion_test.mp4', analysis['timeline'])
table, image, red, blue = analyze_image('flex_companion_image.jpg')
image_result = export_image_result(image, red)
```

Inner image processing functions accept RGB uint8 arrays unless explicitly documented otherwise. `analyze_image` returns the decoded BGR image for backend brightness measurement. `analyze_video` returns timeline, sources, cores, temporal and quality DataFrames, FPS and optional render metadata.

## Data source

- NASA investigation: https://psi.nasa.gov/physci/repo/data/investigations/PSI-69
- NASA Scientific Visualization Studio: https://svs.gsfc.nasa.gov/11318/
- Original video: https://svs.gsfc.nasa.gov/vis/a010000/a011300/a011318/ISS_FlexFlame-540-MASTER_high.mp4
- Original still: https://svs.gsfc.nasa.gov/vis/a010000/a011300/a011318/pf1-1280.jpg

Download these files into a local data directory using the names given in the command. They are not redistributed in this source package.

## Outputs and integration

`outputs/reference/` contains original, unchanged CSV/JSON outputs from the Kaggle run. Generated results are written to the user-selected output directory. Use separate media-level CV result JSON objects for the team schema and `flex_frame_timeline.json` for the 693-frame series. The summary JSON is a convenience bundle, not itself the canonical CV result schema. Null values are intentional for unavailable measurements.

Defaults are provisional: PSI-69, MEDIA-001, MEDIA-002 and empty source IDs. The backend owner must confirm actual IDs and schema compatibility. Use `--experiment-id`, `--video-media-id`, `--image-media-id`, `--video-source-id` and `--image-source-id` to supply the registry values. Source IDs may be repeated. Do not treat an empty source list as a verified source mapping. The backend endpoint integration is not tested here. For image-only data with no detected red region, the result has `detected: false` and an empty feature object; confirm this case with the team's canonical schema before exposing it in the API.

## Reference results

693 frames, 148 quality-screened envelope estimates, 27 supplementary candidate partial arcs, 999 compact-source observations, 660 high-intensity core observations and 401 later red-region analyzed frames. Preliminary detection performance: 26/27 correct on the evaluable subset (96.30% accuracy). It is not an independent cross-experiment benchmark. Counts are observations per frame, not unique physical objects. The original notebook's 46 JSON checks passed; this source package also includes independent reference tests and optional OpenCV tests.

## Scientific limitations

Measurements are pixels and relative digital intensity; no millimeter, temperature or radiometric calibration is available. Circles are model assumptions and cannot establish physical flame circularity. Red and bright structures may include apparatus or reflections. A missing envelope is not proof of extinction. Playback time is not calibrated experimental time. Partial arcs use nearby quality-screened frames, including possible future frames. Source regions and phases cannot be generalized without further validation.

## Reproduction status

Original notebook outputs were verified against the archive manifest. Python syntax, CLI help and reference-output tests were checked locally. The current environment does not contain OpenCV and could not download the official media; fresh image/video algorithm execution and exact parity against the original recording remain to be run where those inputs and dependencies are available (e.g. Kaggle). See `HANDOVER.md`.
