import json
from pathlib import Path
import pandas as pd


def records(df):
    return json.loads(df.to_json(orient='records', double_precision=10))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def representative_row(timeline):
    eligible = timeline[timeline['quality_status'].eq('quality_screened')]
    if eligible.empty:
        raise ValueError('No eligible envelope measurement')
    return eligible.loc[(eligible['envelope_diameter_pixels'] - eligible['envelope_diameter_pixels'].median()).abs().idxmin()]


def make_result(result_id, experiment_id, media_id, features, method, limitations, source_ids):
    return {'cv_result_id': result_id, 'experiment_id': experiment_id,
            'media_id': media_id, 'processing_status': 'success',
            'detected': features is not None, 'features': features or {},
            'method': method, 'calibration_status': 'not_calibrated',
            'limitations': limitations, 'source_ids': list(source_ids)}


def export_image_result(image, red_signal, *, experiment_id='PSI-69', media_id='MEDIA-002', source_ids=()):
    import cv2
    import numpy as np
    candidate = (red_signal >= 25).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(candidate, connectivity=8)
    features = None
    if count > 1:
        label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        mask = labels == label
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        features = {'area_pixels': int(mask.sum()), 'width_pixels': int(stats[label, cv2.CC_STAT_WIDTH]),
                    'height_pixels': int(stats[label, cv2.CC_STAT_HEIGHT]), 'brightness_mean': round(float(gray[mask].mean()), 4)}
    return make_result('CV-FLEX-002', experiment_id, media_id, features,
        'red_excess_connected_component_segmentation',
        ['Detected region is a luminous candidate, not a confirmed flame.',
         'Largest connected component at red-excess threshold 25.',
         'Segmentation is threshold dependent.', 'Apparatus-related illumination may be included.',
         'Physical dimensions and temperature are unavailable.'], source_ids)


def export_video_result(path, timeline, *, experiment_id='PSI-69', media_id='MEDIA-001', source_ids=()):
    import cv2
    import numpy as np
    row = representative_row(timeline)
    index = int(row['frame_index'])
    cap = cv2.VideoCapture(str(path))
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = cap.read()
        if not ok:
            raise ValueError('Representative video frame could not be decoded')
    finally:
        cap.release()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mask = np.zeros(gray.shape, dtype=np.uint8)
    center = (round(float(row['envelope_centroid_x'])), round(float(row['envelope_centroid_y'])))
    radius = round(float(row['envelope_radius_pixels']))
    cv2.circle(mask, center, radius, 255, -1)
    _, _, w, h = cv2.boundingRect(mask)
    features = {'area_pixels': int(np.count_nonzero(mask)), 'width_pixels': int(w),
                'height_pixels': int(h), 'brightness_mean': round(float(gray[mask > 0].mean()), 4)}
    result = make_result('CV-FLEX-001', experiment_id, media_id, features, 'phase_gated_ransac_circle',
        [f'Features describe representative video frame {index}.', 'Geometry is estimated using a circular model.',
         'Pixel measurements are not physical dimensions.', 'Brightness represents grayscale digital intensity.',
         'Playback time is not calibrated experimental time.'], source_ids)
    return result, index
