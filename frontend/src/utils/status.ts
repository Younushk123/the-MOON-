
import { humanize } from './format'

export type StatusTone = 'validated' | 'review' | 'incomplete' | 'mock'

const KNOWN: Record<string, { label: string; tone: StatusTone }> = {
  mock: { label: 'Mock', tone: 'mock' },
  illustrative: { label: 'Illustrative', tone: 'mock' },
  content_verified: { label: 'Content verified', tone: 'validated' },
  metadata_verified: { label: 'Metadata verified', tone: 'review' },
  unverified: { label: 'Unverified', tone: 'incomplete' },
  validated: { label: 'Validated', tone: 'validated' },
  'under review': { label: 'Under Review', tone: 'review' },
  incomplete: { label: 'Incomplete', tone: 'incomplete' },
}

export function getStatusMeta(status: unknown): { label: string; tone: StatusTone } {
  const raw = String(status ?? '').trim()
  if (!raw) return { label: 'Unknown', tone: 'incomplete' }
  const key = raw.toLowerCase().replace(/_/g, ' ')
  return KNOWN[raw.toLowerCase()] ?? KNOWN[key] ?? { label: humanize(raw), tone: 'review' }
}
