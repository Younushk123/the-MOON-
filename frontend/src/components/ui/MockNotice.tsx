import { MOCK_BANNER_TEXT, USE_MOCK } from '../../config/env'

/** Visible whenever mock data is active or a record is flagged data_status = "mock". */
export default function MockNotice({ force = false, className = 'mock-notice' }: { force?: boolean; className?: string }) {
  if (!USE_MOCK && !force) return null
  return <p className={className}>{MOCK_BANNER_TEXT}</p>
}
