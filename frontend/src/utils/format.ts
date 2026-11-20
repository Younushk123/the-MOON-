
import { CONDITION_UNITS } from '../config/env'

export function humanize(value: unknown): string {
  const text = String(value ?? '').replace(/[_-]+/g, ' ').trim()
  return text ? text.replace(/\b\w/g, (c) => c.toUpperCase()) : ''
}

export const isNum = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)

export function formatNumber(value: number | null | undefined): string {
  return isNum(value) ? String(Math.round(value * 10000) / 10000) : '—'
}

export function formatRange(min: number | null, max: number | null, unit = ''): string {
  if (min == null && max == null) return '—'
  const suffix = unit ? ` ${unit}` : ''
  if (min == null || max == null || min === max) return `${formatNumber(min ?? max)}${suffix}`
  return `${formatNumber(min)}–${formatNumber(max)}${suffix}`
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
}

export function formatTimestamp(value: string | number | null | undefined): string {
  return value == null || value === '' ? '—' : String(value)
}

export function formatCondition(key: keyof typeof CONDITION_UNITS, value: number | string | null | undefined): string {
  if (value == null || value === '') return '—'
  const unit = CONDITION_UNITS[key]
  return unit ? `${value} ${unit}` : String(value)
}
