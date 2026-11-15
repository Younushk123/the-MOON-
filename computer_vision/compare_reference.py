import argparse
from pathlib import Path
import json
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description='Compare a fresh FLEX run against the archived run')
    parser.add_argument('--generated', type=Path, required=True)
    args = parser.parse_args()
    reference = Path(__file__).parent / 'outputs' / 'reference'
    files = ['flex_integrated_analysis.csv','flex_integrated_luminous_sources.csv',
             'flex_integrated_luminous_cores.csv','flex_quality_controlled_features.csv',
             'flex_temporal_features.csv','flex_static_image_analysis.csv']
    failures = []
    for name in files:
        try:
            old = pd.read_csv(reference / name)
            new = pd.read_csv(args.generated / name)
            pd.testing.assert_frame_equal(old, new, check_dtype=False, rtol=1e-5, atol=1e-5)
            print('PASS', name)
        except (AssertionError, OSError, ValueError) as exc:
            failures.append(name)
            print('FAIL', name, str(exc)[:500])
    for name in ['flex_video_cv_result.json','flex_image_cv_result.json']:
        try:
            old = json.loads((reference / name).read_text())
            new = json.loads((args.generated / name).read_text())
            assert old['features'] == new['features'], 'Feature mismatch'
            assert old['detected'] == new['detected'], 'Detection mismatch'
            print('PASS', name)
        except (AssertionError, OSError, ValueError) as exc:
            failures.append(name)
            print('FAIL', name, str(exc)[:500])
    if failures:
        raise SystemExit(f'{len(failures)} comparison(s) failed')


if __name__ == '__main__':
    main()
