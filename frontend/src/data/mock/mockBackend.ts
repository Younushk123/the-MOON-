import type {
  AnalysisRequest,
  AnalysisResult,
  ApiEnvelope,
  AskRequest,
  Comparison,
  ComparedVariable,
  ComparisonRequest,
  CvResult,
  Experiment,
  Insight,
  InsightRequest,
  Measurement,
  VisionRequest,
} from '../../types/schemas'
import { QUICK_QUESTIONS } from '../quickQuestions'
import { mockExperiments } from './experiments'
import { mockMeasurements } from './measurements'

const OK = 'Request completed successfully.'
const ok = <T,>(data: T, message = OK): ApiEnvelope<T> => ({ success: true, data, message })
const fail = (message: string, error_code: string): ApiEnvelope<never> => ({
  success: false,
  data: null,
  message,
  error_code,
})

const MOCK_INSIGHT_LIMITATION =
  'MOCK RESPONSE generated in the browser. No RAG pipeline or NASA source was queried.'

const round = (n: number, d = 3) => Math.round(n * 10 ** d) / 10 ** d
const mean = (values: number[]) => values.reduce((a, b) => a + b, 0) / values.length
const findExperiment = (id: string) => mockExperiments.find((e) => e.experiment_id === id)
const measurementsOf = (id: string) => mockMeasurements.filter((m) => m.experiment_id === id)
const tail = (id: string) => id.slice(-3)

/* ---------- POST /analysis ---------- */
const MOCK_WARNINGS: Record<string, string[]> = {
  'MOCK-EX-002': ['Mock warning: this record has no per-sample timestamps.'],
}

function buildAnalysis(req: AnalysisRequest): ApiEnvelope<AnalysisResult> {
  const exp = findExperiment(req?.experiment_id)
  if (!exp) return fail('Experiment not found.', 'EXPERIMENT_NOT_FOUND')

  const meas = measurementsOf(exp.experiment_id)
  const groups = new Map<string, { variable: string; unit: string; values: number[] }>()
  meas.forEach((m) => {
    if (m.value == null) return
    const key = `${m.variable}|${m.unit}`
    if (!groups.has(key)) groups.set(key, { variable: m.variable, unit: m.unit, values: [] })
    groups.get(key)!.values.push(m.value)
  })

  const missing = meas.filter((m) => m.value == null).length
  const warnings = [...(MOCK_WARNINGS[exp.experiment_id] ?? [])]
  if (meas.length === 0) warnings.push('No measurements are available for this experiment.')

  return ok({
    analysis_id: `MOCK-ANALYSIS-${tail(exp.experiment_id)}`,
    experiment_id: exp.experiment_id,
    analysis_type: req.analysis_type ?? 'statistical_summary',
    status: meas.length ? 'success' : 'failed',
    results: [...groups.values()].map((g) => ({
      metric: 'mean',
      variable: g.variable,
      value: round(mean(g.values)),
      unit: g.unit,
    })),
    data_quality: {
      missing_values: missing,
      validation_passed: meas.length > 0 && missing === 0,
      warnings,
    },
    source_ids: exp.source_ids,
    limitations: ['MOCK: computed from illustrative measurements, not from NASA data.'],
  })
}

/* ---------- POST /comparison ---------- */
function buildComparison(req: ComparisonRequest): ApiEnvelope<Comparison> {
  const ids = [...new Set(req?.experiment_ids ?? [])]
  if (ids.length < 2) return fail('At least two experiment_ids are required.', 'INVALID_REQUEST')
  const unknown = ids.filter((id) => !findExperiment(id))
  if (unknown.length) return fail(`Experiment not found: ${unknown.join(', ')}`, 'EXPERIMENT_NOT_FOUND')

  const scoped = mockMeasurements.filter((m) => ids.includes(m.experiment_id))
  const variables = req.variables?.length ? req.variables : [...new Set(scoped.map((m) => m.variable))]

  const compared: ComparedVariable[] = variables.map((variable) => {
    const rows = scoped.filter((m) => m.variable === variable)
    const missingIn = ids.filter((id) => !rows.some((m) => m.experiment_id === id))
    const units = [...new Set(rows.map((m) => m.unit))]
    const unit = units[0] ?? ''

    if (missingIn.length)
      return { variable, unit, comparable: false, reason: `No ${variable} measurements for: ${missingIn.join(', ')}.` }
    if (units.length > 1)
      return { variable, unit, comparable: false, reason: `Units differ (${units.join(' vs ')}).` }
    if (variable !== 'oxygen_concentration') {
      const pressures = [...new Set(rows.map((m) => m.conditions.pressure))]
      if (pressures.length > 1)
        return { variable, unit, comparable: false, reason: 'Conditions or measurement definitions are not sufficiently matched (pressure differs).' }
    }
    return { variable, unit, comparable: true, reason: 'Units and relevant conditions are compatible (mock rule).' }
  })

  const comparableCount = compared.filter((c) => c.comparable).length
  const status = comparableCount === 0 ? 'not_comparable' : comparableCount === compared.length ? 'success' : 'partial'

  const findings = compared
    .filter((c) => c.comparable)
    .map((c) => {
      const parts = ids.map((id) => {
        const vals = scoped.filter((m) => m.experiment_id === id && m.variable === c.variable && m.value != null).map((m) => m.value as number)
        return `${id}: ${round(mean(vals))} ${c.unit}`
      })
      return `MOCK: mean ${c.variable} — ${parts.join('; ')}.`
    })

  const warnings = ['MOCK comparison: results are synthetic and not NASA findings.']
  if (comparableCount < compared.length || compared.length === 0)
    warnings.unshift('Do not interpret incompatible measurements as a direct comparison.')

  return ok({
    comparison_id: `MOCK-COMP-${ids.map(tail).join('-')}`,
    experiment_ids: ids,
    status,
    compared_variables: compared,
    findings,
    warnings,
    source_ids: [...new Set(ids.flatMap((id) => findExperiment(id)?.source_ids ?? []))],
  })
}

/* ---------- POST /assistant/ask  and  POST /insights ---------- */
function scopeExperiments(ids?: string[]): Experiment[] {
  const list = ids?.length ? ids.map(findExperiment).filter(Boolean) as Experiment[] : mockExperiments
  return list
}

function buildAsk(req: AskRequest): ApiEnvelope<Insight> {
  if (!req?.question?.trim()) return fail('A question is required.', 'INVALID_REQUEST')
  const scope = scopeExperiments(req.experiment_ids)
  const key = QUICK_QUESTIONS.find((q) => q.label === req.question)?.id
  const evidence = scope.slice(0, 3).map((e) => ({
    source_id: e.source_ids[0] ?? '',
    experiment_id: e.experiment_id,
    evidence_text: `[MOCK] ${e.description}`,
    url: null,
  }))
  const base = {
    insight_id: `MOCK-INSIGHT-${key ?? 'custom'}`,
    question: req.question,
    confidence: 'not_assessed',
  }

  const scopedMeasurements = mockMeasurements.filter((m) => scope.some((e) => e.experiment_id === m.experiment_id))
  const fuels = [...new Set(scopedMeasurements.map((m) => m.conditions.fuel).filter(Boolean))]

  switch (key) {
    case 'differences':
      return ok({ ...base, claim: `MOCK RESPONSE: the illustrative records list different fuels (${fuels.join(', ') || 'none'}) and pressure conditions. This describes mock fields only; it says nothing about real combustion behaviour.`, supporting_evidence: evidence, fire_safety_relevance: 'Not assessed for mock data.', limitations: [MOCK_INSIGHT_LIMITATION], evidence_status: 'partially_supported' })
    case 'temperature':
      return ok({ ...base, claim: 'MOCK RESPONSE: the available evidence does not support a claim about how temperature affects combustion rate.', supporting_evidence: [], fire_safety_relevance: 'Not assessed: insufficient evidence.', limitations: [MOCK_INSIGHT_LIMITATION, 'No indexed passage or table supports this question (demonstrates abstention).'], evidence_status: 'insufficient_evidence' })
    case 'safety':
      return ok({ ...base, claim: 'MOCK RESPONSE: illustrative records cannot support a spacecraft fire-safety conclusion.', supporting_evidence: evidence, fire_safety_relevance: 'Fire-safety conclusions require verified NASA sources, which are not connected in mock mode.', limitations: [MOCK_INSIGHT_LIMITATION], evidence_status: 'partially_supported' })
    case 'summary':
      return ok({ ...base, claim: `MOCK RESPONSE: the mock dataset in scope has ${scope.length} experiment record(s) and ${scopedMeasurements.length} illustrative measurement record(s).`, supporting_evidence: evidence, fire_safety_relevance: 'Not assessed for mock data.', limitations: [MOCK_INSIGHT_LIMITATION], evidence_status: 'partially_supported' })
    case 'next-steps':
      return ok({ ...base, claim: 'MOCK RESPONSE: replace mock records with inspected NASA files, keep units and test conditions attached, and only compare experiments whose conditions match.', supporting_evidence: [], fire_safety_relevance: 'Not assessed for mock data.', limitations: [MOCK_INSIGHT_LIMITATION], evidence_status: 'partially_supported' })
    default:
      return ok({ ...base, claim: 'MOCK RESPONSE: no indexed evidence supports an answer to this question.', supporting_evidence: [], fire_safety_relevance: 'Not assessed: insufficient evidence.', limitations: [MOCK_INSIGHT_LIMITATION], evidence_status: 'insufficient_evidence' })
  }
}

function buildInsight(req: InsightRequest): ApiEnvelope<Insight> {
  const analysis = buildAnalysis({ experiment_id: req?.experiment_id })
  if (!analysis.success) return analysis
  if (analysis.data.analysis_id !== req.analysis_id) return fail('Analysis not found.', 'ANALYSIS_NOT_FOUND')
  const exp = findExperiment(req.experiment_id) as Experiment
  const summary = analysis.data.results.map((r) => `mean ${r.variable} = ${r.value} ${r.unit}`).join('; ')
  return ok({
    insight_id: `MOCK-INSIGHT-${tail(exp.experiment_id)}`,
    question: req.question,
    claim: `MOCK RESPONSE: analysis ${analysis.data.analysis_id} reports ${summary || 'no results'}. These are illustrative values.`,
    supporting_evidence: exp.source_ids.map((sid) => ({ source_id: sid, experiment_id: exp.experiment_id, evidence_text: `[MOCK] ${exp.description}`, url: null })),
    fire_safety_relevance: 'Not assessed for mock data.',
    limitations: [MOCK_INSIGHT_LIMITATION],
    confidence: 'not_assessed',
    evidence_status: analysis.data.results.length ? 'partially_supported' : 'insufficient_evidence',
  })
}

/* ---------- POST /vision/analyze ---------- */
function buildVision(req: VisionRequest): ApiEnvelope<CvResult> {
  if (!req?.experiment_id) return fail('experiment_id is required.', 'INVALID_REQUEST')
  return ok({
    cv_result_id: 'MOCK-CV-001',
    experiment_id: req.experiment_id,
    media_id: req.media_id ?? 'MOCK-MEDIA-001',
    processing_status: 'success',
    detected: true,
    features: { area_pixels: 12500, width_pixels: 140, height_pixels: 210, brightness_mean: 185 },
    method: 'image_processing',
    calibration_status: 'not_calibrated',
    limitations: ['Pixel measurements are not physical flame dimensions.', 'MOCK RESULT: format example only; no real media was analysed.'],
    source_ids: [],
  })
}

/* ---------- Router ---------- */
export function mockRoute(method: string, path: string, body: any): ApiEnvelope<unknown> {
  const route = path.replace(/^\/api\/v1/, '').replace(/\/+$/, '') || '/'
  const m = method.toUpperCase()
  let match: RegExpMatchArray | null

  if (m === 'GET' && route === '/health') return ok({ status: 'ok', mode: 'mock' })
  if (m === 'GET' && route === '/experiments') return ok(mockExperiments)
  if (m === 'GET' && (match = route.match(/^\/experiments\/([^/]+)\/measurements$/))) {
    const id = decodeURIComponent(match[1])
    return findExperiment(id) ? ok<Measurement[]>(measurementsOf(id)) : fail('Experiment not found.', 'EXPERIMENT_NOT_FOUND')
  }
  if (m === 'GET' && (match = route.match(/^\/experiments\/([^/]+)$/))) {
    const exp = findExperiment(decodeURIComponent(match[1]))
    return exp ? ok(exp) : fail('Experiment not found.', 'EXPERIMENT_NOT_FOUND')
  }
  if (m === 'POST' && route === '/analysis') return buildAnalysis(body)
  if (m === 'POST' && route === '/comparison') return buildComparison(body)
  if (m === 'POST' && route === '/insights') return buildInsight(body)
  if (m === 'POST' && route === '/assistant/ask') return buildAsk(body)
  if (m === 'POST' && route === '/vision/analyze') return buildVision(body)
  return fail(`Mock backend has no route for ${m} ${path}.`, 'NOT_FOUND')
}
