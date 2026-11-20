
import type { AnalysisResult, Experiment, Measurement, Source } from '../types/schemas'
import type { ExperimentView } from '../types/view'
import { isNum } from '../utils/format'
import { getStatusMeta } from '../utils/status'

const minOf = (values: number[]) => (values.length ? Math.min(...values) : null)
const maxOf = (values: number[]) => (values.length ? Math.max(...values) : null)

export function buildExperimentView(
  experiment: Experiment,
  measurements: Measurement[] | undefined,
  analysis: AnalysisResult | null | undefined,
  sourcesById: Map<string, Source>,
): ExperimentView {
  const meas = measurements ?? []
  const temps = meas.map((m) => m.conditions?.temperature).filter(isNum)
  const pressures = meas.map((m) => m.conditions?.pressure).filter(isNum)
  const fuels = [...new Set(meas.map((m) => m.conditions?.fuel).filter((f): f is string => !!f))]
  const sourceIds = experiment.source_ids ?? []
  const sources = sourceIds.map((id) => sourcesById.get(id)).filter((s): s is Source => !!s)
  const meta = getStatusMeta(experiment.data_status)

  return {
    id: experiment.experiment_id,
    title: experiment.name,
    summary: experiment.description,
    category: experiment.investigation,
    platform: experiment.platform,
    program: experiment.program,
    status: meta.label,
    statusKey: experiment.data_status,
    isMock: experiment.data_status === 'mock',
    sourceIds,
    source: sourceIds.map((id) => sourcesById.get(id)?.title ?? id).join(', '),
    lastUpdated: experiment.last_updated,
    limitations: experiment.limitations ?? [],
    availableMeasurements: experiment.available_measurements ?? [],

    fuel: fuels.length ? fuels.join(', ') : null,
    temperatureMin: minOf(temps),
    temperatureMax: maxOf(temps),
    pressure: minOf(pressures),
    pressureMax: maxOf(pressures),
    conditionsLoaded: measurements !== undefined,

    experiment,
    measurements: meas,
    sources,
    analysis: analysis ?? null,
  }
}

export function buildExperimentViews(
  experiments: Experiment[],
  measurementsById: Record<string, Measurement[]>,
  analysisById: Record<string, AnalysisResult>,
  sources: Source[],
): ExperimentView[] {
  const sourcesById = new Map(sources.map((s) => [s.source_id, s]))
  return experiments.map((e) =>
    buildExperimentView(e, measurementsById[e.experiment_id], analysisById[e.experiment_id], sourcesById),
  )
}
