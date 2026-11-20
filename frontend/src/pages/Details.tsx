import { useMemo } from 'react'
import { ArrowLeft, FileText, PlusCircle, ScanEye } from 'lucide-react'
import StatusBadge from '../components/ui/StatusBadge'
import StateNotice from '../components/ui/StateNotice'
import MockNotice from '../components/ui/MockNotice'
import Tag, { type TagTone } from '../components/ui/Tag'
import { ENABLE_VISION } from '../config/env'
import { useAsyncData } from '../hooks/useAsyncData'
import { getExperiment, getMeasurements } from '../services/api'
import { buildExperimentView } from '../services/adapters'
import type { Source } from '../types/schemas'
import { formatCondition, formatDate, formatRange, formatNumber, formatTimestamp, humanize, isNum } from '../utils/format'
import { getStatusMeta } from '../utils/status'

const toneOf = (value: string): TagTone => {
  const t = getStatusMeta(value).tone
  return t === 'validated' ? 'good' : t === 'review' ? 'warn' : t === 'mock' ? 'mock' : 'bad'
}

function SourceItem({ id, source }: { id: string; source?: Source }) {
  if (!source) {
    return (
      <div className="schema-source-item">
        <strong>{id}</strong>
        <small>Source record not provided by the API. Only the source_id is available.</small>
      </div>
    )
  }
  return (
    <div className="schema-source-item">
      <strong>{source.title}</strong>
      <small>
        {source.source_id} · {source.publisher} · {humanize(source.source_type)}
        {source.publication_date ? ` · ${formatDate(source.publication_date)}` : ''}
      </small>
      <div className="schema-chips">
        <Tag tone={toneOf(source.verification_status)}>{humanize(source.verification_status)}</Tag>
        <Tag tone={source.ingestion_status === 'ingested' ? 'good' : 'warn'}>{humanize(source.ingestion_status)}</Tag>
        <Tag tone={source.access_status === 'accessible' ? 'info' : 'warn'}>Access: {humanize(source.access_status)}</Tag>
      </div>
      {source.url ? (
        <a href={source.url} target="_blank" rel="noreferrer">{source.url}</a>
      ) : (
        <small>No URL recorded.</small>
      )}
    </div>
  )
}

export default function Details({ experiment, sources = [], sourcesProvided = false, setPage }: any) {
  const experimentId: string | undefined = experiment?.id

 
  const detail = useAsyncData(
    async (signal) => {
      const [record, measurements] = await Promise.all([
        getExperiment(experimentId as string, signal),
        getMeasurements(experimentId as string, signal),
      ])
      return { record, measurements: Array.isArray(measurements) ? measurements : [] }
    },
    [experimentId],
    Boolean(experimentId),
  )

  const sourcesById = useMemo(() => new Map<string, Source>(sources.map((s: Source) => [s.source_id, s])), [sources])

  const view = useMemo(
    () => (detail.data ? buildExperimentView(detail.data.record, detail.data.measurements, null, sourcesById) : null),
    [detail.data, sourcesById],
  )

  if (!experiment) {
    return (
      <div className="page">
        <h1>Experiment details</h1>
        <p>Select an experiment from the Explorer first.</p>
        <button className="secondary-button" onClick={() => setPage('Explorer')}>
          <ArrowLeft size={15} /> Back to Explorer
        </button>
      </div>
    )
  }

  // Header uses the already-loaded list record until the detail response arrives.
  const head = view ?? experiment
  const measurements = view?.measurements ?? []
  const flowValues = measurements.map((m) => m.conditions?.flow_velocity).filter(isNum)
  const hasUnresolved = (view?.sourceIds ?? []).some((id: string) => !sourcesById.has(id))
  const anyNotIngested = (view?.sources ?? []).some((s) => s.ingestion_status !== 'ingested')

  return (
    <div className="page">
      <button className="text-button back-button" onClick={() => setPage('Explorer')}>
        <ArrowLeft size={15} /> Back to Explorer
      </button>

      <div className="page-heading">
        <div>
          <p className="eyebrow">EXPERIMENT RECORD · {head.id}</p>
          <h1>{head.title}</h1>
          <p>{head.summary}</p>
        </div>
        <StatusBadge status={head.status} statusKey={head.statusKey} />
      </div>

      {detail.status === 'error' && (
        <StateNotice kind="error" title="Could not load experiment details" message={detail.error} onRetry={detail.reload} />
      )}

      {detail.status !== 'error' && (
        <div className="detail-grid">
          <section className="panel detail-panel">
            <div className="panel-title">
              <h3>Experimental conditions</h3>
            </div>

            {detail.status === 'loading' || !view ? (
              <StateNotice kind="loading" title="Loading experiment record…" />
            ) : (
              <>
                {[
                  ['Experiment ID', view.id],
                  ['Investigation', view.category || '—'],
                  ['Program', view.program || '—'],
                  ['Platform', view.platform || '—'],
                  ['Fuel', view.fuel ?? '—'],
                  ['Temperature', formatRange(view.temperatureMin, view.temperatureMax, 'K')],
                  ['Pressure', formatRange(view.pressure, view.pressureMax, 'atm')],
                  ...(flowValues.length
                    ? [['Flow velocity', formatCondition('flow_velocity', Math.min(...flowValues))]]
                    : []),
                  ['Data status', view.status],
                  ['Last updated', formatDate(view.lastUpdated)],
                ].map(([k, v]) => (
                  <div className="detail-row" key={k}>
                    <span>{k}</span>
                    <strong>{v}</strong>
                  </div>
                ))}

                {view.availableMeasurements.length > 0 && (
                  <>
                    <h4 className="schema-subheading">Available measurements</h4>
                    <div className="schema-meta-row">
                      {view.availableMeasurements.map((name: string) => (
                        <Tag key={name}>{humanize(name)}</Tag>
                      ))}
                    </div>
                  </>
                )}

                {view.limitations.length > 0 && (
                  <>
                    <h4 className="schema-subheading">Limitations</h4>
                    <ul className="schema-list">
                      {view.limitations.map((item: string) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </>
                )}
              </>
            )}
          </section>

          <section className="panel detail-panel">
            <div className="panel-title">
              <FileText size={17} />
              <h3>Measurements & provenance</h3>
            </div>

            {detail.status === 'loading' || !view ? (
              <StateNotice kind="loading" title="Loading measurements…" />
            ) : measurements.length === 0 ? (
              <StateNotice
                kind="empty"
                title="No measurements available"
                message="The API returned no measurement records for this experiment."
              />
            ) : (
              <div className="schema-table-wrap is-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Variable</th>
                      <th>Value</th>
                      <th>Unit</th>
                      <th>Timestamp</th>
                      <th>Source</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {measurements.map((m) => (
                      <tr key={m.measurement_id} title={m.notes?.join(' ') || undefined}>
                        <td>{humanize(m.variable)}</td>
                        <td>{formatNumber(m.value)}</td>
                        <td>{m.unit || '—'}</td>
                        <td>{formatTimestamp(m.timestamp)}</td>
                        <td>{m.source_id}</td>
                        <td>
                          <Tag tone={toneOf(m.measurement_status)}>{humanize(m.measurement_status)}</Tag>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {view && (
              <>
                <h4 className="schema-subheading">Sources</h4>
                {view.sourceIds.length === 0 ? (
                  <StateNotice kind="empty" title="No sources listed" message="This experiment has no source_ids." />
                ) : (
                  view.sourceIds.map((id: string) => <SourceItem key={id} id={id} source={sourcesById.get(id)} />)
                )}

                {(anyNotIngested || hasUnresolved || !sourcesProvided) && (
                  <div className="notice-box">
                    <FileText size={17} />
                    <span>
                      Listing a source is not proof that its file has been downloaded, parsed or inspected.
                      Treat sources that are not marked “Ingested” as references only.
                    </span>
                  </div>
                )}
              </>
            )}

            <MockNotice force={Boolean(view?.isMock)} />

            <button className="secondary-button" onClick={() => setPage('Comparison')}>
              <PlusCircle size={15} /> Compare experiments
            </button>

            {ENABLE_VISION && (
              <>
                <h4 className="schema-subheading">Microgravity Flame Explorer · Computer Vision</h4>
                <p className="cv-details-hint">
                  FLEX image and video analysis is kept separate from this PSI-159 experiment record.
                </p>
                <button className="secondary-button" onClick={() => setPage('Computer Vision')}>
                  <ScanEye size={15} /> Open Flame Explorer
                </button>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
