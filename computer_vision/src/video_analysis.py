from pathlib import Path
import cv2
import numpy as np
import pandas as pd
from .flame_detection import segment_flame_v2, detect_partial_boundary
from .feature_extraction import (extract_flame_features, detect_refined_sources,
    detect_luminous_cores, red_signal, analyze_red_regions)

QC_CONFIG = {
    "analysis_start_s": 2.5,
    "min_reliable_coverage_pct": 80.0
}

def quality_control(temporal_df):
    qc_df = temporal_df.copy()

    qc_df["quality_status"] = "not_detected"

    blank = qc_df["analysis_status"].eq("blank_frame")

    detected = qc_df["detected"].eq(True)

    pre_analysis = (
        qc_df["playback_time_s"] <
        QC_CONFIG["analysis_start_s"]
    )

    weak_boundary = (
        qc_df["angular_coverage_pct"] <
        QC_CONFIG["min_reliable_coverage_pct"]
    )

    qc_df.loc[blank, "quality_status"] = "blank_frame"

    qc_df.loc[
        detected & pre_analysis,
        "quality_status"
    ] = "excluded_pre_analysis"

    qc_df.loc[
        detected & ~pre_analysis & weak_boundary,
        "quality_status"
    ] = "uncertain_boundary"

    qc_df.loc[
        detected & ~pre_analysis & ~weak_boundary,
        "quality_status"
    ] = "quality_screened"

    qc_df["measurement_eligible"] = (
        qc_df["quality_status"].eq("quality_screened")
    )


    return qc_df

def open_video(path):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not cap.isOpened() or not np.isfinite(fps) or fps <= 0:
        cap.release()
        raise ValueError(f'Cannot decode video or invalid FPS: {path}')
    return cap, fps

def read_baseline(path):
    cap, _ = open_video(path)
    signals = []
    try:
        for index in range(278, 286):
            cap.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = cap.read()
            if not ok:
                raise ValueError('FLEX baseline requires original frames 278–285')
            signals.append(red_signal(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    finally:
        cap.release()
    return np.median(signals, axis=0).astype(np.float32)

def analyze_video(path, keep_visuals=False):
    cap, fps = open_video(path)
    expected = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    temporal_records = []
    if (width, height) != (960, 540) or abs(fps - 30) > 0.05 or expected != 693:
        cap.release()
        raise ValueError('FLEX profile requires original 960x540, 30 fps, 693-frame footage; do not use annotated exports')
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            index = len(temporal_records)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            sample = {'frame_index': index, 'timestamp': index / fps, 'image': rgb}
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            if gray.max() <= 8:
                result = {'detected': None}
                status = 'blank_frame'
            else:
                result = segment_flame_v2(rgb)
                status = 'envelope_detected' if result['detected'] else 'no_reliable_envelope'
            features = extract_flame_features(sample, result)
            features['analysis_status'] = status
            temporal_records.append(features)
    finally:
        cap.release()
    if len(temporal_records) != expected:
        raise ValueError(f'Incomplete video decode: {len(temporal_records)} of {expected}')
    temporal_df = pd.DataFrame(temporal_records)
    qc_df = quality_control(temporal_df)
    reliable_frames = qc_df[qc_df['measurement_eligible'].eq(True)].dropna(subset=['centroid_x','centroid_y','radius_pixels'])
    if reliable_frames.empty:
        raise ValueError('No reliable envelope reference: input does not support the FLEX profile')
    baseline_signal = read_baseline(path)
    qc_lookup = qc_df.set_index('frame_index')
    integrated_records, integrated_sources, integrated_cores = [], [], []
    frame_visual_data = {}
    cap, _ = open_video(path)
    index = 0
    try:
        while True:
            success, frame = cap.read()
            if not success:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            time_s = index / fps
            qc = qc_lookup.loc[index]

            blank = qc["quality_status"] == "blank_frame"

            eligible = bool(qc["measurement_eligible"])

            record = {
                "frame_index": index,
                "playback_time_s": time_s,
                "quality_status": qc["quality_status"],
                "envelope_measurement_eligible": eligible,
                "envelope_area_pixels": (
                    qc["area_pixels"] if eligible else None
                ),
                "envelope_diameter_pixels": (
                    qc["diameter_pixels"] if eligible else None
                ),
                "envelope_radius_pixels": (
                    qc["radius_pixels"] if eligible else None
                ),
                "envelope_centroid_x": (
                    qc["centroid_x"] if eligible else None
                ),
                "envelope_centroid_y": (
                    qc["centroid_y"] if eligible else None
                ),
                "boundary_brightness_mean": (
                    qc["boundary_brightness_mean"]
                    if eligible else None
                ),
                "partial_boundary_detected": None,
                "partial_coverage_pct": None,
                "partial_arc_deg": None,
                "compact_source_count": None,
                "luminous_core_count": None,
                "source_analysis_status": "not_evaluated",
                "red_area_t15": None,
                "red_area_t25": None,
                "red_area_t40": None,
                "red_area_t55": None,
                "calibration_status": "not_calibrated"
            }

            sources = []
            cores = []
            partial_points = np.empty((0, 2))
            red_contours = []

            if not blank:

                if not eligible and 2.5 <= time_s < 9.5:
                    partial = detect_partial_boundary(
                        rgb, index, reliable_frames
                    )

                    if partial["status"] != "outside_tracking_window":
                        record["partial_boundary_detected"] = (
                            partial["detected"]
                        )

                        record["partial_coverage_pct"] = (
                            partial["coverage_pct"]
                        )

                        record["partial_arc_deg"] = (
                            partial["longest_arc_deg"]
                        )

                        if partial["detected"]:
                            partial_points = partial["points"]

                if time_s < 9.5:
                    sources, source_status = (
                        detect_refined_sources(rgb, index, fps)
                    )

                    record["source_analysis_status"] = source_status

                    if source_status == "analyzed":
                        record["compact_source_count"] = len(sources)

                    if 2.5 <= time_s:
                        cores = detect_luminous_cores(
                            rgb, threshold=200
                        )

                        record["luminous_core_count"] = len(cores)

                else:
                    record["source_analysis_status"] = (
                        "diffuse_glow_analysis"
                    )

                    red_measurements, red_contours = (
                        analyze_red_regions(rgb, baseline_signal)
                    )

                    record.update(red_measurements)

            for source_id, source in enumerate(sources, 1):
                integrated_sources.append({
                    "frame_index": index,
                    "playback_time_s": time_s,
                    "source_id": source_id,
                    **source
                })

            for core_id, core in enumerate(cores, 1):
                integrated_cores.append({
                    "frame_index": index,
                    "playback_time_s": time_s,
                    "core_id": core_id,
                    **core
                })

            if keep_visuals:
                frame_visual_data[index] = {
                    "sources": sources,
                    "cores": cores,
                    "partial_points": partial_points,
                    "red_contours": red_contours
                }

            integrated_records.append(record)

            index += 1
    finally:
        cap.release()
    if index != expected:
        raise ValueError('Incomplete second video pass')
    return {'timeline': pd.DataFrame(integrated_records), 'sources': pd.DataFrame(integrated_sources),
            'cores': pd.DataFrame(integrated_cores), 'temporal': temporal_df, 'quality': qc_df,
            'visuals': frame_visual_data, 'fps': fps}
