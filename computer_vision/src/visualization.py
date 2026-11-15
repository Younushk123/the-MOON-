import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from .video_analysis import open_video

NAVY = (42, 23, 15)
WHITE = (245, 245, 245)
MUTED = (160, 148, 130)
CYAN = (238, 211, 34)
YELLOW = (21, 204, 250)
ORANGE = (22, 115, 249)
GREEN = (129, 185, 16)


def put_text(image, text, x, y, scale=0.5,
             color=WHITE, thickness=1):

    cv2.putText(
        image,
        str(text),
        (int(x), int(y)),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA
    )


def format_value(value, decimals=0):
    if pd.isna(value):
        return "N/A"

    return f"{value:,.{decimals}f}"


def render_video(video_path, analysis, output_path):
    integrated_df = analysis['timeline']
    frame_visual_data = analysis['visuals']
    if len(frame_visual_data) != len(integrated_df):
        raise ValueError('Run analyze_video with keep_visuals=True')
    analysis_lookup = integrated_df.set_index('frame_index')
    cap, fps = open_video(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    PANEL_WIDTH, HEADER_HEIGHT, FOOTER_HEIGHT = 340, 60, 40
    canvas_width, canvas_height = width + PANEL_WIDTH, height + HEADER_HEIGHT + FOOTER_HEIGHT
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*'mp4v'), fps, (canvas_width, canvas_height))
    if not writer.isOpened():
        cap.release()
        writer.release()
        raise ValueError('Cannot open output video writer')
    index = 0
    try:
        while True:
            success, frame = cap.read()
            if not success:
                break
            row = analysis_lookup.loc[index]
            visuals = frame_visual_data[index]

            overlay = frame.copy()

            if row["envelope_measurement_eligible"]:

                center = (
                    int(round(row["envelope_centroid_x"])),
                    int(round(row["envelope_centroid_y"]))
                )

                radius = int(
                    round(row["envelope_radius_pixels"])
                )

                cv2.circle(
                    overlay, center, radius,
                    CYAN, 2, cv2.LINE_AA
                )

                cv2.drawMarker(
                    overlay, center, CYAN,
                    cv2.MARKER_CROSS,
                    12, 1
                )

            for point in visuals["partial_points"]:
                cv2.circle(
                    overlay,
                    tuple(np.round(point).astype(int)),
                    2,
                    GREEN,
                    -1
                )

            for source in visuals["sources"]:
                x, y, w, h = source["bbox"]

                color = (
                    CYAN if source["region"] == "central"
                    else ORANGE
                )

                cv2.rectangle(
                    overlay,
                    (x, y),
                    (x + w, y + h),
                    color,
                    1
                )

            for core in visuals["cores"]:
                x, y, w, h = core["bbox"]

                cv2.rectangle(
                    overlay,
                    (x, y),
                    (x + w, y + h),
                    YELLOW,
                    2
                )

            if visuals["red_contours"]:
                cv2.drawContours(
                    overlay,
                    visuals["red_contours"],
                    -1,
                    ORANGE,
                    2
                )

            canvas = np.full(
                (canvas_height, canvas_width, 3),
                NAVY,
                dtype=np.uint8
            )

            canvas[
                HEADER_HEIGHT:HEADER_HEIGHT + height,
                :width
            ] = overlay

            put_text(
                canvas,
                "THE MOON | FLEX Visual Intelligence",
                22, 38,
                0.85, WHITE, 2
            )

            panel_x = width + 22

            put_text(
                canvas,
                "EXPERIMENT ANALYSIS",
                panel_x, 90,
                0.58, CYAN, 2
            )

            status = row["quality_status"]

            if row["envelope_measurement_eligible"]:
                status = "Quality-screened envelope"
            elif pd.notna(row["partial_boundary_detected"]) and bool(
                row["partial_boundary_detected"]
            ):
                status = "Candidate partial boundary"
            elif pd.notna(row["red_area_t40"]):
                status = "Later luminous region"
            elif row["quality_status"] == "blank_frame":
                status = "Blank frame"
            elif row["source_analysis_status"] == "apparatus_phase_not_evaluated":
                status = "Apparatus phase"
            else:
                status = "No reliable envelope"

            metrics = [
                ("Frame", f"{index + 1:03d} / {len(integrated_df)}"),
                ("Playback time", f"{index / fps:.2f} s"),
                ("Visual status", status),
                (
                    "Envelope diameter",
                    format_value(
                        row["envelope_diameter_pixels"], 1
                    ) + " px"
                    if pd.notna(row["envelope_diameter_pixels"])
                    else "N/A"
                ),
                (
                    "Envelope area",
                    format_value(
                        row["envelope_area_pixels"]
                    ) + " px^2"
                    if pd.notna(row["envelope_area_pixels"])
                    else "N/A"
                ),
                (
                    "Partial arc",
                    format_value(row["partial_arc_deg"], 0)
                    + " deg"
                    if pd.notna(row["partial_arc_deg"])
                    else "N/A"
                ),
                (
                    "Luminous candidates",
                    format_value(row["compact_source_count"])
                ),
                (
                    "High-intensity cores",
                    format_value(row["luminous_core_count"])
                ),
                (
                    "Red area | Threshold 40",
                    format_value(row["red_area_t40"])
                    + " px^2"
                    if pd.notna(row["red_area_t40"])
                    else "N/A"
                )
            ]

            y = 120

            for label, value in metrics:
                put_text(
                    canvas, label,
                    panel_x, y,
                    0.38, MUTED
                )

                put_text(
                    canvas, value,
                    panel_x, y + 20,
                    0.48, WHITE
                )

                y += 48

            footer_y = HEADER_HEIGHT + height + 25

            put_text(
                canvas,
                "Source: NASA GSFC | FLEX | PSI-69 | Pixel-space measurements | Not calibrated",
                20, footer_y,
                0.48, WHITE
            )

            writer.write(canvas)

            index += 1
    finally:
        cap.release()
        writer.release()
    if index != len(integrated_df):
        raise ValueError('Incomplete annotated render')
    return index
