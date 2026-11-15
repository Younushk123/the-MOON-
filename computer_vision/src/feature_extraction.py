import cv2
import numpy as np
from .flame_detection import RANSAC_CONFIG
def extract_flame_features(sample, result):
    features = {
        "frame_index": sample["frame_index"],
        "playback_time_s": round(sample["timestamp"], 4),
        "detected": result["detected"],
        "area_pixels": None,
        "diameter_pixels": None,
        "radius_pixels": None,
        "centroid_x": None,
        "centroid_y": None,
        "angular_coverage_pct": None,
        "boundary_brightness_mean": None,
        "circularity": None,
        "calibration_status": "not_calibrated",
        "method": "ransac_circle"
    }

    if not result["detected"]:
        return features

    cx, cy = result["ellipse"][0]
    radius = result["radius_pixels"]

    x1, y1, _, _ = result["bounds"]

    mask = result["envelope_mask"]

    yy, xx = np.indices(mask.shape)

    distance = np.sqrt(
        (xx - cx) ** 2 + (yy - cy) ** 2
    )

    boundary = (
        (distance >= radius - 5) &
        (distance <= radius + 5) &
        (result["blue_excess"] >=
         RANSAC_CONFIG["blue_threshold"])
    )

    grayscale = cv2.cvtColor(
        result["roi"], cv2.COLOR_RGB2GRAY
    )

    brightness = (
        float(grayscale[boundary].mean())
        if boundary.any()
        else None
    )

    features.update({
        "area_pixels": cv2.countNonZero(mask),
        "diameter_pixels": round(2 * radius, 3),
        "radius_pixels": round(radius, 3),
        "centroid_x": round(cx + x1, 3),
        "centroid_y": round(cy + y1, 3),
        "angular_coverage_pct": round(
            result["boundary_support"] * 100, 2
        ),
        "boundary_brightness_mean": (
            round(brightness, 3)
            if brightness is not None
            else None
        )
    })

    return features

SOURCE_REGIONS = {
    "central": (0.36, 0.20, 0.64, 0.75),
    "upper_external": (0.20, 0.10, 0.36, 0.40),
    "lower_external": (0.66, 0.72, 0.85, 1.00),
    "early_ignition": (0.25, 0.37, 0.62, 0.73)
}

def detect_refined_sources(rgb, frame_index, fps):
    height, width = rgb.shape[:2]

    time_s = frame_index / fps

    if time_s < 0.9:
        return [], "apparatus_phase_not_evaluated"

    image = rgb.astype(np.float32)

    gray = cv2.cvtColor(
        rgb, cv2.COLOR_RGB2GRAY
    )

    red_excess = image[:, :, 0] - (
        image[:, :, 1] + image[:, :, 2]
    ) / 2

    if time_s < 2.5:
        active_regions = ["early_ignition"]
    elif time_s < 4.0:
        active_regions = [
            "central",
            "upper_external",
            "lower_external"
        ]
    else:
        active_regions = ["central"]

    sources = []

    for name in active_regions:
        bounds = SOURCE_REGIONS[name]

        x1 = int(bounds[0] * width)
        y1 = int(bounds[1] * height)
        x2 = int(bounds[2] * width)
        y2 = int(bounds[3] * height)

        roi_gray = gray[y1:y2, x1:x2]

        roi_red = image[
            y1:y2, x1:x2, 0
        ]

        roi_excess = red_excess[
            y1:y2, x1:x2
        ]

        if name == "early_ignition":
            mask = (
                (roi_red >= 45) &
                (roi_excess >= 15)
            ).astype(np.uint8)

        else:
            mask = (
                roi_gray >= 110
            ).astype(np.uint8)

        count, labels, stats, centroids = (
            cv2.connectedComponentsWithStats(
                mask, connectivity=8
            )
        )

        for i in range(1, count):
            x, y, w, h, area = stats[i]

            if area < 6:
                continue

            component = labels == i

            sources.append({
                "region": name,
                "bbox": (
                    int(x + x1),
                    int(y + y1),
                    int(w),
                    int(h)
                ),
                "area_pixels": int(area),
                "centroid_x": float(
                    centroids[i][0] + x1
                ),
                "centroid_y": float(
                    centroids[i][1] + y1
                ),
                "mean_brightness": float(
                    roi_gray[component].mean()
                ),
                "peak_brightness": int(
                    roi_gray[component].max()
                )
            })

    return sources, "analyzed"

def detect_luminous_cores(rgb, threshold=200):
    height, width = rgb.shape[:2]

    x1, y1 = int(width * 0.36), int(height * 0.20)
    x2, y2 = int(width * 0.64), int(height * 0.75)

    gray = cv2.cvtColor(
        rgb, cv2.COLOR_RGB2GRAY
    )

    roi = gray[y1:y2, x1:x2]

    mask = (roi >= threshold).astype(np.uint8)

    count, labels, stats, centroids = (
        cv2.connectedComponentsWithStats(
            mask, connectivity=8
        )
    )

    cores = []

    for i in range(1, count):
        x, y, w, h, area = stats[i]

        if area < 6:
            continue

        cores.append({
            "bbox": (
                int(x + x1),
                int(y + y1),
                int(w),
                int(h)
            ),
            "area_pixels": int(area),
            "centroid_x": float(centroids[i][0] + x1),
            "centroid_y": float(centroids[i][1] + y1),
            "mean_brightness": float(
                roi[labels == i].mean()
            )
        })

    return cores

def red_signal(rgb):
    image = rgb.astype(np.float32)

    return image[:, :, 0] - (
        image[:, :, 1] + image[:, :, 2]
    ) / 2

def segment_luminous_region(rgb, baseline_signal, threshold=8.0):
    height, width = rgb.shape[:2]

    change = red_signal(rgb) - baseline_signal

    change = cv2.GaussianBlur(change, (7, 7), 0)

    search_region = np.zeros(
        (height, width), dtype=np.uint8
    )

    search_region[
        int(height * 0.17):int(height * 0.87),
        int(width * 0.22):int(width * 0.78)
    ] = 1

    mask = (
        (change >= threshold) &
        (search_region == 1)
    ).astype(np.uint8)

    count, labels, stats, _ = (
        cv2.connectedComponentsWithStats(mask)
    )

    final_mask = np.zeros_like(mask)

    if count > 1:
        largest = 1 + np.argmax(
            stats[1:, cv2.CC_STAT_AREA]
        )

        final_mask[labels == largest] = 1

    contours, _ = cv2.findContours(
        final_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    return change, final_mask, contours

RED_THRESHOLDS = [15, 25, 40, 55]

def analyze_red_regions(rgb, baseline_signal):
    signal = red_signal(rgb) - baseline_signal

    signal = cv2.GaussianBlur(
        signal, (7, 7), 0
    )

    measurements = {}
    selected_contours = []

    for threshold in RED_THRESHOLDS:
        mask = (signal >= threshold).astype(np.uint8)

        count, labels, stats, _ = (
            cv2.connectedComponentsWithStats(mask)
        )

        area = 0

        if count > 1:
            largest = 1 + np.argmax(
                stats[1:, cv2.CC_STAT_AREA]
            )

            component = (
                labels == largest
            ).astype(np.uint8)

            area = int(component.sum())

            if threshold == 40:
                selected_contours, _ = cv2.findContours(
                    component,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE
                )

        measurements[f"red_area_t{threshold}"] = area

    return measurements, selected_contours
