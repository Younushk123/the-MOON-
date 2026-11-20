import argparse
from pathlib import Path
from .src.backend_output import records, write_json, export_image_result, export_video_result


def main():
    parser = argparse.ArgumentParser(description='THE MOON FLEX offline computer vision pipeline')
    parser.add_argument('--video', type=Path)
    parser.add_argument('--image', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--experiment-id', default='PSI-69')
    parser.add_argument('--video-media-id', default='MEDIA-001')
    parser.add_argument('--image-media-id', default='MEDIA-002')
    parser.add_argument('--video-source-id', action='append', default=[])
    parser.add_argument('--image-source-id', action='append', default=[])
    parser.add_argument('--annotate', action='store_true')
    args = parser.parse_args()
    if not args.video and not args.image:
        parser.error('Specify --video and/or --image')
    if args.annotate and not args.video:
        parser.error('--annotate requires --video')
    args.output.mkdir(parents=True, exist_ok=True)
    result_list, static_records = [], []
    summary = {'experiment_id': args.experiment_id, 'source_urls': [
        'https://psi.nasa.gov/physci/repo/data/investigations/PSI-69', 'https://svs.gsfc.nasa.gov/11318/']}
    if args.video:
        from .src.video_analysis import analyze_video
        analysis = analyze_video(args.video, keep_visuals=args.annotate)
        for key, filename in {'timeline':'flex_integrated_analysis.csv', 'sources':'flex_integrated_luminous_sources.csv',
            'cores':'flex_integrated_luminous_cores.csv', 'quality':'flex_quality_controlled_features.csv',
            'temporal':'flex_temporal_features.csv'}.items():
            analysis[key].to_csv(args.output / filename, index=False)
        timeline = analysis['timeline']
        result, index = export_video_result(args.video, timeline, experiment_id=args.experiment_id,
            media_id=args.video_media_id, source_ids=args.video_source_id)
        result_list.append(result)
        write_json(args.output / 'flex_video_cv_result.json', result)
        write_json(args.output / 'flex_frame_timeline.json', {'experiment_id': args.experiment_id,
            'media_id': args.video_media_id, 'total_frames': len(timeline),
            'calibration_status':'not_calibrated', 'frames': records(timeline)})
        summary.update(total_processed_frames=len(timeline), quality_screened_measurements=int(timeline['envelope_measurement_eligible'].sum()),
                       representative_frame_index=index)
        if args.annotate:
            from .src.visualization import render_video
            render_video(args.video, analysis, args.output / 'flex_integrated_annotated.mp4')
    if args.image:
        from .src.image_analysis import analyze_image
        df, image, red, blue = analyze_image(args.image)
        df.to_csv(args.output / 'flex_static_image_analysis.csv', index=False)
        static_records = records(df)
        result = export_image_result(image, red, experiment_id=args.experiment_id,
            media_id=args.image_media_id, source_ids=args.image_source_id)
        result_list.append(result)
        write_json(args.output / 'flex_image_cv_result.json', result)
    summary.update(cv_results=result_list, static_image_multilevel_analysis=static_records)
    write_json(args.output / 'flex_backend_output.json', summary)
    print(f'Exported {len(result_list)} CV results to {args.output}')


if __name__ == '__main__':
    main()
