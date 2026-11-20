import unittest
import tempfile
from pathlib import Path
import importlib.util
import numpy as np


@unittest.skipUnless(importlib.util.find_spec('cv2'), 'OpenCV not installed')
class AlgorithmTests(unittest.TestCase):
    def test_circle_fit(self):
        from computer_vision.src.flame_detection import circle_from_points
        self.assertTrue(np.allclose(circle_from_points(np.array([[7,4],[2,9],[-3,4]])), (2,4,5)))

    def test_red_image(self):
        import cv2
        from computer_vision.src.image_analysis import analyze_image
        from computer_vision.src.backend_output import export_image_result
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.png'
            image = np.zeros((100,100,3),dtype=np.uint8)
            image[20:40,20:50,2]=200
            self.assertTrue(cv2.imwrite(str(path),image))
            df, decoded, red, blue = analyze_image(path)
            self.assertEqual(int(df.iloc[0]['area_pixels']),600)
            self.assertEqual(int(df.iloc[4]['area_pixels']),0)
            result = export_image_result(decoded,red)
            self.assertEqual(result['features']['area_pixels'],600)

    def test_blank_frame(self):
        from computer_vision.src.flame_detection import segment_flame_v2
        result = segment_flame_v2(np.zeros((540,960,3),dtype=np.uint8))
        self.assertFalse(result['detected'])

    def test_core_detection(self):
        from computer_vision.src.feature_extraction import detect_luminous_cores
        rgb = np.zeros((540,960,3),dtype=np.uint8)
        rgb[180:190,470:480] = 255
        self.assertEqual(detect_luminous_cores(rgb)[0]['area_pixels'],100)
