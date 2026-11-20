
import type { AnalysisResult, Experiment, Measurement, Source } from './schemas'

export interface ExperimentView {
  id: string
  title: string
  summary: string
  category: string
  platform: string
  program: string
  status: string
  statusKey: string
  isMock: boolean
  sourceIds: string[]
  source: string
  lastUpdated: string
  limitations: string[]
  availableMeasurements: string[]

  fuel: string | null
  temperatureMin: number | null
  temperatureMax: number | null
  pressure: number | null
  pressureMax: number | null
  conditionsLoaded: boolean

  experiment: Experiment
  measurements: Measurement[]
  sources: Source[]
  analysis: AnalysisResult | null
}
