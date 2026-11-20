import cv2
import numpy as np
import pandas as pd
from pathlib import Path

def analyze_image(path):
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Cannot decode image: {path}")
    image_name = Path(path).name
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    r, g, b = np.moveaxis(rgb.astype(np.float32), -1, 0)

    red_signal = np.maximum(r - (g + b) / 2, 0)
    blue_signal = np.maximum(b - (r + g) / 2, 0)

    height, width = gray.shape
    total_pixels = height * width

    thresholds = [15, 25, 40, 55]
    records = []

    for name, signal in [
        ("red_excess", red_signal),
        ("blue_excess", blue_signal)
    ]:
        for threshold in thresholds:
            mask = signal >= threshold
            area = int(mask.sum())

            records.append({
                "image_name": image_name,
                "signal_type": name,
                "threshold": threshold,
                "area_pixels": area,
                "image_percentage": round(
                    100 * area / total_pixels, 4
                ),
                "mean_signal": round(
                    float(signal[mask].mean()), 4
                ) if area else None,
                "calibration_status": "not_calibrated",
                "interpretation": "candidate_luminous_region"
            })

    image_test_df = pd.DataFrame(records)


    return image_test_df, image, red_signal, blue_signal
