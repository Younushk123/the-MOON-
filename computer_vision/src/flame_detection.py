import cv2
import numpy as np
from scipy.optimize import least_squares
from .preprocessing import preprocess_frame
RANSAC_CONFIG = {
    "blue_threshold": 4.0,
    "min_component_area": 150,
    "min_radius": 55,
    "max_radius": 145,
    "iterations": 800,
    "distance_tolerance": 6.0,
    "min_angular_coverage": 0.60,
    "angular_bins": 36
}

def circle_from_points(points):
    p1, p2, p3 = points.astype(np.float64)

    matrix = 2 * np.array([
        p2 - p1,
        p3 - p1
    ])

    values = np.array([
        np.dot(p2, p2) - np.dot(p1, p1),
        np.dot(p3, p3) - np.dot(p1, p1)
    ])

    try:
        center = np.linalg.solve(matrix, values)
        radius = np.linalg.norm(center - p1)

        return center[0], center[1], radius

    except np.linalg.LinAlgError:
        return None

def evaluate_circle(points, circle, config):
    cx, cy, radius = circle

    distances = np.sqrt(
        (points[:, 0] - cx) ** 2 +
        (points[:, 1] - cy) ** 2
    )

    residuals = np.abs(distances - radius)

    inliers = (
        residuals <= config["distance_tolerance"]
    )

    if not inliers.any():
        return 0.0, inliers

    angles = np.mod(
        np.arctan2(
            points[inliers, 1] - cy,
            points[inliers, 0] - cx
        ),
        2 * np.pi
    )

    bins = np.floor(
        angles / (2 * np.pi)
        * config["angular_bins"]
    ).astype(int)

    coverage = (
        len(np.unique(bins)) /
        config["angular_bins"]
    )

    return coverage, inliers

def segment_flame_v2(image, config=RANSAC_CONFIG):
    result = preprocess_frame(image)
    signal = result["blue_excess"]

    height, width = signal.shape

    mask = (
        signal >= config["blue_threshold"]
    ).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (3, 3)
    )

    mask = cv2.morphologyEx(
        mask, cv2.MORPH_OPEN, kernel
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_NONE
    )

    fragments = [
        contour.reshape(-1, 2)
        for contour in contours
        if cv2.contourArea(contour)
        >= config["min_component_area"]
    ]

    result.update({
        "threshold_mask": mask,
        "envelope_mask": np.zeros_like(mask),
        "detected": False,
        "ellipse": None,
        "boundary_support": None
    })

    if not fragments:
        return result

    points = np.concatenate(fragments).astype(np.float64)

    if len(points) < 3:
        return result

    rng = np.random.default_rng(42)

    best_circle = None
    best_inliers = None
    best_score = -np.inf

    for _ in range(config["iterations"]):
        indices = rng.choice(len(points), 3, replace=False)

        circle = circle_from_points(points[indices])

        if circle is None:
            continue

        cx, cy, radius = circle

        if not (
            config["min_radius"]
            <= radius
            <= config["max_radius"]
        ):
            continue

        if not (
            0.25 * width <= cx <= 0.75 * width
            and 0.20 * height <= cy <= 0.80 * height
        ):
            continue

        if not (
            radius < cx < width - radius
            and radius < cy < height - radius
        ):
            continue

        coverage, inliers = evaluate_circle(
            points, circle, config
        )

        if coverage < config["min_angular_coverage"]:
            continue

        score = (
            coverage
            + 0.15 * inliers.mean()
            + 0.10 * radius / config["max_radius"]
        )

        if score > best_score:
            best_score = score
            best_circle = circle
            best_inliers = inliers

    if best_circle is None:
        return result

    inlier_points = points[best_inliers]

    def residual_function(parameters):
        cx, cy, radius = parameters

        return np.sqrt(
            (inlier_points[:, 0] - cx) ** 2 +
            (inlier_points[:, 1] - cy) ** 2
        ) - radius

    refined = least_squares(
        residual_function,
        best_circle,
        loss="soft_l1",
        f_scale=3.0
    )

    cx, cy, radius = refined.x

    if not (
        config["min_radius"] <= radius <= config["max_radius"]
        and radius < cx < width - radius
        and radius < cy < height - radius
    ):
        return result

    coverage, _ = evaluate_circle(
        points, (cx, cy, radius), config
    )

    if coverage < config["min_angular_coverage"]:
        return result

    envelope = np.zeros_like(mask)

    cv2.circle(
        envelope,
        (round(cx), round(cy)),
        round(radius),
        255,
        -1
    )

    result.update({
        "detected": True,
        "envelope_mask": envelope,
        "ellipse": (
            (float(cx), float(cy)),
            (float(2 * radius), float(2 * radius)),
            0.0
        ),
        "radius_pixels": float(radius),
        "boundary_support": float(coverage)
    })

    return result

PARTIAL_CONFIG = {
    "angular_bins": 72,
    "minimum_arc_deg": 60,
    "minimum_signal": 3.0,
    "noise_multiplier": 3.0,
    "maximum_reference_distance": 45
}

def detect_partial_boundary(rgb, frame_index, reliable_frames):
    config = PARTIAL_CONFIG

    reference = reliable_frames.iloc[
        (
            reliable_frames["frame_index"]
            - frame_index
        ).abs().argmin()
    ]

    distance = abs(
        reference["frame_index"] - frame_index
    )

    result = {
        "frame_index": frame_index,
        "reference_frame": int(reference["frame_index"]),
        "detected": False,
        "coverage_pct": 0.0,
        "longest_arc_deg": 0.0,
        "status": "insufficient_evidence",
        "points": np.empty((0, 2))
    }

    if distance > config["maximum_reference_distance"]:
        result["status"] = "outside_tracking_window"
        return result

    cx = float(reference["centroid_x"])
    cy = float(reference["centroid_y"])
    radius = float(reference["radius_pixels"])

    image = rgb.astype(np.float32)

    signal = image[:, :, 2] - image[:, :, 0]

    signal = cv2.GaussianBlur(
        signal, (5, 5), 0
    )

    bins = config["angular_bins"]

    angles = np.linspace(
        0, 2 * np.pi,
        bins,
        endpoint=False
    )

    radii = np.linspace(
        radius * 0.70,
        radius * 1.50,
        100
    )

    map_x = (
        cx + np.cos(angles[:, None]) * radii[None, :]
    ).astype(np.float32)

    map_y = (
        cy + np.sin(angles[:, None]) * radii[None, :]
    ).astype(np.float32)

    profiles = cv2.remap(
        signal,
        map_x,
        map_y,
        cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT
    )

    search_indices = np.where(
        (radii >= radius * 0.80) &
        (radii <= radius * 1.20)
    )[0]

    background = profiles[
        :, radii >= radius * 1.30
    ]

    baseline = np.median(
        background, axis=1
    )

    noise = 1.4826 * np.median(
        np.abs(background - baseline[:, None]),
        axis=1
    )

    peak_indices = search_indices[
        np.argmax(
            profiles[:, search_indices],
            axis=1
        )
    ]

    row_indices = np.arange(bins)

    peak_values = profiles[
        row_indices,
        peak_indices
    ]

    prominence = peak_values - baseline

    supported = (
        (
            prominence >= np.maximum(
                config["minimum_signal"],
                config["noise_multiplier"] * noise
            )
        )
        & (peak_values >= config["minimum_signal"])
        & (peak_indices > search_indices[0])
        & (peak_indices < search_indices[-1])
    )

    longest_run = 0
    longest_end = 0
    current_run = 0

    for i, value in enumerate(np.tile(supported, 2)):
        current_run = current_run + 1 if value else 0

        if current_run > longest_run:
            longest_run = current_run
            longest_end = i

    longest_run = min(longest_run, bins)

    arc_indices = np.arange(
        longest_end - longest_run + 1,
        longest_end + 1
    ) % bins

    longest_arc = longest_run * (360 / bins)

    detected = (
        longest_arc >= config["minimum_arc_deg"]
    )

    points = np.column_stack([
        map_x[row_indices, peak_indices],
        map_y[row_indices, peak_indices]
    ])[arc_indices]

    result.update({
        "detected": bool(detected),
        "coverage_pct": float(supported.mean() * 100),
        "longest_arc_deg": float(longest_arc),
        "status": (
            "candidate_visible_arc"
            if detected
            else "insufficient_evidence"
        ),
        "points": points
    })

    return result
