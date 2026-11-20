import cv2
import numpy as np
ROI_BOUNDS = (0.32, 0.20, 0.67, 0.75)

def extract_roi(image, bounds=ROI_BOUNDS):
    height, width = image.shape[:2]

    x1 = int(bounds[0] * width)
    y1 = int(bounds[1] * height)
    x2 = int(bounds[2] * width)
    y2 = int(bounds[3] * height)

    return image[y1:y2, x1:x2].copy(), (x1, y1, x2, y2)

def gamma_correction(image, gamma=0.45):
    table = np.array([
        ((i / 255.0) ** gamma) * 255
        for i in range(256)
    ]).astype(np.uint8)

    return cv2.LUT(image, table)

def preprocess_frame(image):
    roi, bounds = extract_roi(image)

    denoised = cv2.GaussianBlur(roi, (5, 5), 0)

    red = denoised[:, :, 0].astype(np.float32)
    green = denoised[:, :, 1].astype(np.float32)
    blue = denoised[:, :, 2].astype(np.float32)

    blue_excess = blue - red

    enhanced = gamma_correction(denoised)

    return {
        "roi": roi,
        "bounds": bounds,
        "denoised": denoised,
        "enhanced": enhanced,
        "blue_excess": blue_excess
    }
