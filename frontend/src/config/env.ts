
const env = import.meta.env

export const USE_MOCK: boolean =
  String(env.VITE_USE_MOCK_DATA ?? 'true').trim() !== 'false'

export const API_BASE_URL: string = String(
  env.VITE_API_BASE_URL ?? (env.DEV ? 'http://127.0.0.1:8000' : ''),
)
  .trim()
  .replace(/\/+$/, '')
  .replace(/\/api(\/v1)?$/, '')
export const API_PREFIX = '/api/v1'

export const REQUEST_TIMEOUT_MS =
  Number(env.VITE_API_TIMEOUT_MS) || 15000

export const RAG_REQUEST_TIMEOUT_MS =
  Number(env.VITE_RAG_TIMEOUT_MS) || 120000

export const VISION_REQUEST_TIMEOUT_MS =
  Number(env.VITE_VISION_TIMEOUT_MS) || 150000

export const MOCK_LATENCY_MS =
  Number(env.VITE_MOCK_LATENCY_MS ?? 250)

/**
 * Optional computer-vision integration.
 * Off by default.
 */
export const ENABLE_VISION: boolean =
  String(env.VITE_ENABLE_VISION ?? 'false').trim() === 'true'

/**
 * Units for MeasurementConditions.
 * K and atm are used for display only.
 */
export const CONDITION_UNITS = {
  temperature: 'K',
  pressure: 'atm',
  flow_velocity: '',
} as const

export const MOCK_BANNER_TEXT =
  'Mock data — illustrative records generated for interface development. Not verified NASA findings.'
