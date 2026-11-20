import { useCallback, useEffect, useMemo, useState } from 'react'
import { getExperiments, getKnownSources, getMeasurements, runAnalysis } from '../services/api'
import { buildExperimentViews } from '../services/adapters'
import type { AnalysisResult, Experiment, Measurement, Source } from '../types/schemas'
import { mapWithConcurrency } from '../utils/async'

const CONCURRENCY = 4

export function useDashboardData() {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [error, setError] = useState('')
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [sourcesProvided, setSourcesProvided] = useState(false)
  const [measurementsById, setMeasurementsById] = useState<Record<string, Measurement[]>>({})
  const [analysisById, setAnalysisById] = useState<Record<string, AnalysisResult>>({})
  const [enriching, setEnriching] = useState(false)
  const [warnings, setWarnings] = useState<string[]>([])
  const [tick, setTick] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    const { signal } = controller

    async function load() {
      setStatus('loading')
      setError('')
      setWarnings([])
      try {
        const [list, known] = await Promise.all([getExperiments(signal), getKnownSources()])
        if (signal.aborted) return
        const safeList = Array.isArray(list) ? list : []
        setExperiments(safeList)
        setSources(known.sources)
        setSourcesProvided(known.provided)
        setMeasurementsById({})
        setAnalysisById({})
        setStatus('success')

        if (!safeList.length) return
        setEnriching(true)

        const results = await mapWithConcurrency(safeList, CONCURRENCY, async (exp) => {
          const [m, a] = await Promise.allSettled([
            getMeasurements(exp.experiment_id, signal),
            runAnalysis({ experiment_id: exp.experiment_id, analysis_type: 'statistical_summary' }, signal),
          ])
          return { id: exp.experiment_id, m, a }
        })
        if (signal.aborted) return

        const nextMeasurements: Record<string, Measurement[]> = {}
        const nextAnalysis: Record<string, AnalysisResult> = {}
        let measurementFailures = 0
        let analysisFailures = 0

        results.forEach(({ id, m, a }) => {
          if (m.status === 'fulfilled' && Array.isArray(m.value)) nextMeasurements[id] = m.value
          else measurementFailures += 1
          if (a.status === 'fulfilled' && a.value) nextAnalysis[id] = a.value
          else analysisFailures += 1
        })

        setMeasurementsById(nextMeasurements)
        setAnalysisById(nextAnalysis)
        const notes: string[] = []
        if (measurementFailures) notes.push(`Measurements could not be loaded for ${measurementFailures} experiment(s); condition fields may be blank.`)
        if (analysisFailures) notes.push(`Analysis could not be loaded for ${analysisFailures} experiment(s); data-quality figures are incomplete.`)
        setWarnings(notes)
      } catch (err: any) {
        if (signal.aborted || err?.name === 'AbortError') return
        setError(err?.message || 'Could not load experiment records.')
        setStatus('error')
      } finally {
        if (!signal.aborted) setEnriching(false)
      }
    }

    load()
    return () => controller.abort()
  }, [tick])

  const views = useMemo(
    () => buildExperimentViews(experiments, measurementsById, analysisById, sources),
    [experiments, measurementsById, analysisById, sources],
  )
  const analyses = useMemo(() => Object.values(analysisById), [analysisById])
  const reload = useCallback(() => setTick((value) => value + 1), [])

  return { status, error, experiments: views, analyses, sources, sourcesProvided, enriching, warnings, reload }
}
