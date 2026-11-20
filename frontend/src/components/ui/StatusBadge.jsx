import { getStatusMeta } from '../../utils/status'

/**
 * Accepts either a display label (legacy callers) or a raw schema value such as
 * Experiment.data_status via `statusKey`. Unknown values are shown humanized.
 */
export default function StatusBadge({ status, statusKey }) {
  const meta = getStatusMeta(statusKey ?? status)
  return <span className={`status-badge ${meta.tone}`}>{meta.label}</span>
}
