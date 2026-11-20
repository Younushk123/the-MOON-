import { ScanEye } from 'lucide-react'
import type { CvResult } from '../../types/schemas'
import { humanize } from '../../utils/format'
import Tag from './Tag'

/** Optional computer-vision result (Section 4.7). Always shows calibration status and limitations. */
export default function CvResultCard({ result }: { result: CvResult }) {
  const f = result.features
  const isImageAnalysis = result.method === 'red_excess_connected_component_segmentation'
  const detectionLabel =
    result.detected === null
      ? 'Detection unavailable'
      : result.detected
        ? isImageAnalysis
          ? 'Luminous region found'
          : 'Flame detected'
        : isImageAnalysis
          ? 'No luminous region found'
          : 'No flame detected'

  return (
    <div className="schema-block">
      <div className="schema-block-title">
        <ScanEye size={16} />
        <strong>Computer vision result</strong>
        <Tag tone={result.detected === true ? 'good' : 'warn'}>{detectionLabel}</Tag>
        <Tag tone="warn">{humanize(result.calibration_status)}</Tag>
      </div>
      <div className="detail-row"><span>Result / media</span><strong>{result.cv_result_id} · {result.media_id}</strong></div>
      <div className="detail-row"><span>Method / status</span><strong>{result.method ? humanize(result.method) : '—'} · {humanize(result.processing_status)}</strong></div>
      <div className="detail-row"><span>Area</span><strong>{f.area_pixels ?? '—'} px²</strong></div>
      <div className="detail-row"><span>Width × height</span><strong>{f.width_pixels ?? '—'} × {f.height_pixels ?? '—'} px</strong></div>
      <div className="detail-row"><span>Mean brightness</span><strong>{f.brightness_mean ?? '—'}</strong></div>
      {result.limitations.length > 0 && (
        <ul className="schema-list">{result.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
      )}
    </div>
  )
}
