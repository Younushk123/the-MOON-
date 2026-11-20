import json
import hashlib
import unittest
from pathlib import Path
import pandas as pd
from computer_vision.src.backend_output import records, representative_row, make_result

REF = Path(__file__).resolve().parents[1] / 'outputs' / 'reference'


class ReferenceTests(unittest.TestCase):
    def test_timeline(self):
        obj = json.loads((REF / 'flex_frame_timeline.json').read_text())
        frames = obj['frames']
        self.assertEqual(len(frames), 693)
        self.assertEqual([r['frame_index'] for r in frames], list(range(693)))
        self.assertEqual(sum(r['envelope_measurement_eligible'] for r in frames), 148)
        self.assertEqual(sum(r['partial_boundary_detected'] is True for r in frames), 27)
        self.assertEqual(sum(r['red_area_t40'] is not None for r in frames), 401)
        self.assertTrue(all(r['envelope_area_pixels'] is None for r in frames if not r['envelope_measurement_eligible']))

    def test_observation_counts(self):
        self.assertEqual(len(pd.read_csv(REF / 'flex_integrated_luminous_sources.csv')), 999)
        self.assertEqual(len(pd.read_csv(REF / 'flex_integrated_luminous_cores.csv')), 660)

    def test_representative_frame(self):
        row = representative_row(pd.read_csv(REF / 'flex_integrated_analysis.csv'))
        self.assertEqual(int(row['frame_index']), 184)

    def test_canonical_outputs(self):
        summary = json.loads((REF / 'flex_backend_output.json').read_text())
        for item, filename in zip(summary['cv_results'], ['flex_video_cv_result.json', 'flex_image_cv_result.json']):
            self.assertEqual(item, json.loads((REF / filename).read_text()))
            self.assertEqual(item['calibration_status'], 'not_calibrated')
            self.assertLessEqual(item['features']['area_pixels'], item['features']['width_pixels'] * item['features']['height_pixels'])
            self.assertTrue(item['limitations'])
        self.assertEqual(summary['representative_frame_index'], 184)

    def test_json_null_and_boolean(self):
        result = records(pd.DataFrame([{'a': float('nan'), 'b': False}]))
        self.assertEqual(result, [{'a': None, 'b': False}])

    def test_result_ids(self):
        result = make_result('CV-1','EXP-1','MEDIA-1', {'area_pixels':1}, 'test', ['test'], ['S-1'])
        self.assertEqual(result['source_ids'], ['S-1'])
        self.assertTrue(result['detected'])

    def test_archived_validation(self):
        report = json.loads((REF / 'flex_json_validation.json').read_text())
        self.assertEqual((report['passed'],report['failed']), (46,0))

    def test_reference_hashes(self):
        manifest = json.loads((REF / 'manifest.json').read_text())
        for item in manifest['files']:
            if item['file'].startswith('results/'):
                path = REF / Path(item['file']).name
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),item['sha256'])


if __name__ == '__main__':
    unittest.main()
