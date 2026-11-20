import { useMemo, useState } from 'react'
import {
  Plus,
  X,
  RotateCcw,
  GitCompareArrows,
  Info,
  CheckCircle2,
  AlertTriangle,
  Ban,
} from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
} from 'recharts'
import StateNotice from '../components/ui/StateNotice'
import Tag from '../components/ui/Tag'
import MockNotice from '../components/ui/MockNotice'
import { useAsyncData } from '../hooks/useAsyncData'
import { compareExperiments } from '../services/api'
import type { Comparison as ComparisonResult, Measurement } from '../types/schemas'
import { formatNumber, formatRange, formatTimestamp, humanize, isNum } from '../utils/format'
import { getStatusMeta } from '../utils/status'
import '../styles/Comparison.css'

const COLORS = [
  '#42c9f5',
  '#f6a545',
  '#30d5b0',
  '#ad9cff',
  '#ff708b',
  '#f4e04d',
  '#7da7ff',
  '#ff9966',
  '#62d26f',
  '#e879f9',
  '#5eead4',
  '#c4b5fd',
]


const FIELD_ROWS = [
  ['Fuel Type', (e) => e.fuel],
  ['Investigation', (e) => e.category],
  [
    'Temperature Range',
    (e) => (e.temperatureMin != null ? formatRange(e.temperatureMin, e.temperatureMax, 'K') : 'N/A'),
  ],
  ['Pressure', (e) => (e.pressure != null ? formatRange(e.pressure, e.pressureMax, 'atm') : 'N/A')],
  ['Platform', (e) => e.platform],
  ['Data Status', (e) => e.status],
  ['Data Source', (e) => e.source],
]

const STATUS_META = {
  success: { label: 'Comparable', Icon: CheckCircle2 },
  partial: { label: 'Partially comparable', Icon: AlertTriangle },
  not_comparable: { label: 'Not comparable', Icon: Ban },
}

const tooltipStyle = {
  contentStyle: {
    backgroundColor: '#071a31',
    border: '1px solid #245078',
    borderRadius: '8px',
    color: '#e8f3ff',
  },
  labelStyle: { color: '#42c9f5' },
  itemStyle: { color: '#e8f3ff' },
  cursor: { fill: 'rgba(66, 201, 245, 0.08)' },
}

function displayValue(value) {
  if (value == null || value === '') return 'N/A'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function getExperimentId(experiment) {
  return String(experiment.id)
}

function getColor(index) {
  return COLORS[index % COLORS.length]
}


function toX(timestamp: Measurement['timestamp']): number | null {
  if (timestamp == null || timestamp === '') return null
  const value = typeof timestamp === 'number' ? timestamp : Date.parse(String(timestamp))
  return Number.isFinite(value) ? value : null
}

const isSynthetic = (m: Measurement) => ['illustrative', 'mock'].includes(String(m.measurement_status))

export default function Comparison({ experiments = [] }) {
  const [selectedIds, setSelectedIds] = useState([])
  const [adding, setAdding] = useState(false)
  const [newId, setNewId] = useState('')
  const [activeTab, setActiveTab] = useState('Overview')

  // No experiments are selected automatically.
  const selected = useMemo(
    () =>
      selectedIds
        .map((id) =>
          experiments.find(
            (experiment) => getExperimentId(experiment) === String(id)
          )
        )
        .filter(Boolean),
    [experiments, selectedIds]
  )

  const available = experiments.filter(
    (experiment) =>
      !selectedIds.includes(getExperimentId(experiment))
  )


  const selectedKey = selectedIds.join('|')
  const requestedVariables = useMemo(
    () => [...new Set(selected.flatMap((e) => e.measurements.map((m) => m.variable)))],
    [selected]
  )
  const comparison = useAsyncData<ComparisonResult>(
    (signal) =>
      compareExperiments(
        {
          experiment_ids: selected.map(getExperimentId),
          ...(requestedVariables.length ? { variables: requestedVariables } : {}),
        },
        signal
      ),
    [selectedKey, requestedVariables.join('|')],
    selected.length >= 2
  )
  const result = comparison.data

  const comparableVariables = useMemo(
    () => (result?.compared_variables ?? []).filter((item) => item.comparable),
    [result]
  )

  const valuesFor = (experiment, variable) =>
    experiment.measurements.filter((m: Measurement) => m.variable === variable)


  const timeSeriesVariable = useMemo(
    () =>
      comparableVariables.find((item) =>
        selected.some((e) => valuesFor(e, item.variable).some((m) => toX(m.timestamp) != null && isNum(m.value)))
      ) ?? null,
    [comparableVariables, selected]
  )

  const barVariable = useMemo(
    () => comparableVariables.find((item) => item.variable !== timeSeriesVariable?.variable) ?? comparableVariables[0] ?? null,
    [comparableVariables, timeSeriesVariable]
  )

  const temperatureData = useMemo(() => {
    if (!timeSeriesVariable) return []
    const times = new Set<number>()
    selected.forEach((e) =>
      valuesFor(e, timeSeriesVariable.variable).forEach((m) => {
        const x = toX(m.timestamp)
        if (x != null && isNum(m.value)) times.add(x)
      })
    )
    return [...times]
      .sort((x, y) => x - y)
      .map((time) => {
        const row = { time }
        selected.forEach((e) => {
          const point = valuesFor(e, timeSeriesVariable.variable).find((m) => toX(m.timestamp) === time)
          row[getExperimentId(e)] = point && isNum(point.value) ? point.value : null
        })
        return row
      })
  }, [selected, timeSeriesVariable])

  const rateData = useMemo(() => {
    if (!barVariable) return []
    return selected
      .map((e) => {
        const values = valuesFor(e, barVariable.variable).map((m) => m.value).filter(isNum)
        return values.length
          ? { id: getExperimentId(e), rate: values.reduce((x, y) => x + y, 0) / values.length }
          : null
      })
      .filter(Boolean)
  }, [selected, barVariable])

  const plottedSynthetic = useMemo(
    () =>
      selected.some((e) =>
        e.measurements.some(
          (m: Measurement) =>
            isSynthetic(m) &&
            [timeSeriesVariable?.variable, barVariable?.variable].includes(m.variable)
        )
      ),
    [selected, timeSeriesVariable, barVariable]
  )

  function addExperiment() {
    if (!newId || selectedIds.includes(newId)) return

    setSelectedIds((current) => [...current, newId])
    setNewId('')
    setAdding(false)
  }

  function removeExperiment(id) {
    setSelectedIds((current) =>
      current.filter((item) => item !== String(id))
    )
  }

  function resetSelection() {
    setSelectedIds([])
    setActiveTab('Overview')
    setAdding(false)
    setNewId('')
  }

  function clearSelection() {
    setSelectedIds([])
    setAdding(false)
    setNewId('')
  }

  if (experiments.length === 0) {
    return (
      <main className="comparison-page">
        <div className="comparison-empty">
          <GitCompareArrows size={30} />
          <h2>No experiments available</h2>
          <p>Check the experiment data source and try again.</p>
        </div>
      </main>
    )
  }

  return (
    <main className="comparison-page">
      <header className="comparison-header">
        <div className="comparison-heading-copy">
          <span className="comparison-eyebrow">
            RESEARCH TOOLS / ANALYSIS
          </span>
          <h1>Experiment Comparison</h1>
          <p>
            Compare experimental conditions and available results side by side.
          </p>
        </div>

        <button
          className="comparison-button secondary"
          onClick={resetSelection}
          type="button"
        >
          <RotateCcw size={15} />
          Reset
        </button>
      </header>

      <section className="comparison-selector">
        <div className="comparison-selector-heading">
          <div>
            <h2>Selected Experiments</h2>
            <p>
              {selected.length} experiment
              {selected.length === 1 ? '' : 's'} selected
            </p>
          </div>

          <button
            className="comparison-clear"
            onClick={clearSelection}
            disabled={selected.length === 0}
            type="button"
          >
            Clear selection
          </button>
        </div>

        <div className="comparison-selected-list">
          {selected.map((experiment, index) => (
            <article
              className="comparison-selected-card"
              key={getExperimentId(experiment)}
              style={{ '--experiment-color': getColor(index) }}
            >
              <span className="comparison-dot" />

              <div className="comparison-selected-info">
                <strong>{getExperimentId(experiment)}</strong>
                <span title={experiment.title ?? 'Untitled experiment'}>
                  {experiment.title ?? 'Untitled experiment'}
                </span>
              </div>

              <button
                className="comparison-remove"
                type="button"
                onClick={() => removeExperiment(getExperimentId(experiment))}
                aria-label={`Remove ${getExperimentId(experiment)}`}
                title="Remove experiment"
              >
                <X size={16} />
              </button>
            </article>
          ))}

          {selected.length === 0 && (
            <p className="comparison-muted">
              No experiments selected. Add experiments to start comparing.
            </p>
          )}
        </div>

        <div className="comparison-selector-footer">
          {adding ? (
            <div className="comparison-add-controls">
              <select
                aria-label="Select experiment"
                value={newId}
                onChange={(event) => setNewId(event.target.value)}
              >
                <option value="">Choose an experiment...</option>

                {available.map((experiment) => (
                  <option
                    key={getExperimentId(experiment)}
                    value={getExperimentId(experiment)}
                  >
                    {getExperimentId(experiment)} —{' '}
                    {experiment.title ?? 'Untitled experiment'}
                  </option>
                ))}
              </select>

              <button
                className="comparison-button primary"
                onClick={addExperiment}
                disabled={!newId}
                type="button"
              >
                Add
              </button>

              <button
                className="comparison-button secondary"
                onClick={() => {
                  setAdding(false)
                  setNewId('')
                }}
                type="button"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              className="comparison-button primary"
              onClick={() => setAdding(true)}
              disabled={available.length === 0}
              type="button"
            >
              <Plus size={16} />
              Add Experiment
            </button>
          )}

          <span className="comparison-selection-hint">
            Select two or more experiments to compare their results.
          </span>
        </div>
      </section>

      <nav className="comparison-tabs" aria-label="Comparison sections">
        {['Overview', 'Conditions', 'Measurements', 'Charts', 'Summary'].map(
          (tab) => (
            <button
              key={tab}
              type="button"
              className={activeTab === tab ? 'active' : ''}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          )
        )}
      </nav>

      {selected.length < 2 ? (
        <section className="comparison-empty">
          <GitCompareArrows size={30} />
          <h2>Select at least two experiments</h2>
          <p>
            Add at least two experiments to view conditions and charts.
            Your selection will appear here once you add them.
          </p>

          {available.length > 0 && (
            <button
              className="comparison-button primary"
              onClick={() => setAdding(true)}
              type="button"
            >
              <Plus size={16} />
              Add Experiment
            </button>
          )}
        </section>
      ) : (
        <>
          {/* Comparison schema: status, per-variable reasons and warnings */}
          {comparison.status === 'loading' && (
            <StateNotice kind="loading" title="Checking whether these experiments can be compared…" />
          )}

          {comparison.status === 'error' && (
            <StateNotice
              kind="error"
              title="Comparison request failed"
              message={comparison.error}
              onRetry={comparison.reload}
            />
          )}

          {result && (
            <div className={`schema-banner is-${result.status}`} role="status">
              {(() => {
                const { Icon } = STATUS_META[result.status] ?? STATUS_META.not_comparable
                return <Icon size={17} />
              })()}
              <div>
                <strong>
                  Comparison status: {STATUS_META[result.status]?.label ?? humanize(result.status)}
                </strong>
                {result.compared_variables.length === 0 && (
                  <div>No comparable variables were reported for this selection.</div>
                )}
                {result.warnings.length > 0 && (
                  <ul>
                    {result.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}

          {(activeTab === 'Overview' || activeTab === 'Conditions') && (
            <section className="comparison-panel conditions-panel">
              <div className="comparison-panel-heading">
                <div>
                  <h2>Key Conditions</h2>
                  <p>Experimental parameters compared side by side</p>
                </div>
                <span className="comparison-panel-tag">
                  {selected.length} experiments
                </span>
              </div>

              <div className="comparison-table-scroll">
                <table className="comparison-table">
                  <thead>
                    <tr>
                      <th>Parameter</th>
                      {selected.map((experiment, index) => (
                        <th key={getExperimentId(experiment)}>
                          <span
                            className="comparison-column-id"
                            style={{ color: getColor(index) }}
                          >
                            {getExperimentId(experiment)}
                          </span>
                          <small>
                            {experiment.title ?? 'Untitled experiment'}
                          </small>
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {FIELD_ROWS.map(([label, getValue]) => (
                      <tr key={label}>
                        <td>{label}</td>
                        {selected.map((experiment) => (
                          <td key={getExperimentId(experiment)}>
                            {displayValue(getValue(experiment))}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {(activeTab === 'Overview' || activeTab === 'Charts') && (
            <section className="comparison-panel chart-panel temperature-panel">
              <div className="comparison-panel-heading">
                <div>
                  <h2>{timeSeriesVariable ? humanize(timeSeriesVariable.variable) : 'Measurements over time'}</h2>
                  <p>Recorded values over time for every selected experiment</p>
                </div>
                <span className="comparison-unit">
                  {timeSeriesVariable?.unit || 'Unit per source'}
                </span>
              </div>

              {timeSeriesVariable && temperatureData.length > 0 ? (
                <div className="comparison-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={temperatureData}
                      margin={{ top: 15, right: 20, left: 0, bottom: 8 }}
                    >
                      <CartesianGrid stroke="#183653" strokeDasharray="3 3" />
                      <XAxis
                        dataKey="time"
                        type="number"
                        domain={['dataMin', 'dataMax']}
                        stroke="#91a9c5"
                        tick={{ fontSize: 11 }}
                        tickLine={{ stroke: '#36536e' }}
                        label={{
                          value: 'Timestamp (as recorded)',
                          position: 'insideBottom',
                          offset: -2,
                          fill: '#91a9c5',
                          fontSize: 11,
                        }}
                      />
                      <YAxis
                        stroke="#91a9c5"
                        tick={{ fontSize: 11 }}
                        tickLine={{ stroke: '#36536e' }}
                        width={48}
                        domain={['auto', 'auto']}
                      />
                      <Tooltip {...tooltipStyle} />
                      <Legend />

                      {selected.map((experiment, index) => {
                        const id = getExperimentId(experiment)

                        return (
                          <Line
                            key={id}
                            type="monotone"
                            dataKey={id}
                            name={id}
                            stroke={getColor(index)}
                            strokeWidth={2.5}
                            dot={{ r: 3 }}
                            activeDot={{ r: 5 }}
                            connectNulls={false}
                            isAnimationActive={false}
                          />
                        )
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="comparison-chart-empty">
                  <Info size={19} />
                  <strong>
                    {result && comparableVariables.length === 0
                      ? 'No comparable variables to plot'
                      : 'No timestamped measurements available'}
                  </strong>
                  <span>
                    {result && comparableVariables.length === 0
                      ? 'The comparison result marks these measurements as not directly comparable, so they are not plotted together.'
                      : 'Charts need comparable variables with timestamped values from the API.'}
                  </span>
                </div>
              )}

              {plottedSynthetic && timeSeriesVariable && (
                <div className="comparison-demo-note">
                  <Info size={15} />
                  <span>
                    Plotted values are illustrative mock measurements. They are not scientific
                    results or NASA findings.
                  </span>
                </div>
              )}
            </section>
          )}

          {(activeTab === 'Overview' ||
            activeTab === 'Charts' ||
            activeTab === 'Measurements') && (
            <section className="comparison-panel chart-panel rate-panel">
              <div className="comparison-panel-heading">
                <div>
                  <h2>{barVariable ? `Mean ${humanize(barVariable.variable)}` : 'Recorded values'}</h2>
                  <p>Mean of the available recorded values per experiment</p>
                </div>
                <span className="comparison-unit">{barVariable?.unit || 'Unit per source'}</span>
              </div>

              {rateData.length > 0 ? (
                <div className="comparison-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={rateData}
                      margin={{ top: 15, right: 15, left: 0, bottom: 8 }}
                    >
                      <CartesianGrid stroke="#183653" strokeDasharray="3 3" />
                      <XAxis
                        dataKey="id"
                        stroke="#91a9c5"
                        tick={{ fontSize: 11 }}
                      />
                      <YAxis
                        stroke="#91a9c5"
                        tick={{ fontSize: 11 }}
                        width={48}
                      />
                      <Tooltip {...tooltipStyle} />
                      <Bar
                        dataKey="rate"
                        name={barVariable ? `Mean ${humanize(barVariable.variable)}` : 'Value'}
                        radius={[5, 5, 0, 0]}
                      >
                        {rateData.map((entry) => {
                          const index = selected.findIndex(
                            (experiment) =>
                              getExperimentId(experiment) === entry.id
                          )

                          return (
                            <Cell
                              key={entry.id}
                              fill={getColor(index < 0 ? 0 : index)}
                            />
                          )
                        })}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="comparison-chart-empty">
                  <Info size={19} />
                  <strong>No comparable values available</strong>
                  <span>
                    This chart needs a variable the comparison result marks as comparable,
                    with recorded values in every selected experiment.
                  </span>
                </div>
              )}

              <p className="comparison-chart-note">
                Units come from the measurement records; none are assumed.
              </p>
            </section>
          )}

          {activeTab === 'Measurements' && (
            <section className="comparison-panel measurements-panel">
              <div className="comparison-panel-heading">
                <div>
                  <h2>Available Measurements</h2>
                  <p>Measurement records for the selected experiments</p>
                </div>
              </div>

              <div className="comparison-table-scroll">
                <table className="comparison-table measurements-table">
                  <thead>
                    <tr>
                      <th>Experiment</th>
                      <th>Variable</th>
                      <th>Value</th>
                      <th>Unit</th>
                      <th>Timestamp</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.flatMap((experiment, index) =>
                      experiment.measurements.length === 0
                        ? [
                            <tr key={`${getExperimentId(experiment)}-none`}>
                              <td>
                                <span style={{ color: getColor(index) }}>
                                  {getExperimentId(experiment)}
                                </span>
                              </td>
                              <td colSpan={5}>No measurements available</td>
                            </tr>,
                          ]
                        : experiment.measurements.map((m: Measurement) => (
                            <tr key={m.measurement_id}>
                              <td>
                                <span style={{ color: getColor(index) }}>
                                  {getExperimentId(experiment)}
                                </span>
                              </td>
                              <td>{humanize(m.variable)}</td>
                              <td>{formatNumber(m.value)}</td>
                              <td>{m.unit || '—'}</td>
                              <td>{formatTimestamp(m.timestamp)}</td>
                              <td>{getStatusMeta(m.measurement_status).label}</td>
                            </tr>
                          ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {activeTab === 'Summary' && (
            <section className="comparison-panel comparison-summary">
              <div className="comparison-panel-heading">
                <div>
                  <h2>Comparison Summary</h2>
                  <p>
                    Review available values without inferring scientific
                    conclusions.
                  </p>
                </div>
              </div>

              {result && (
                <>
                  <div className="comparison-summary-row">
                    <strong>Compared variables</strong>
                    <span className={result.status === 'success' ? '' : 'is-different'}>
                      {STATUS_META[result.status]?.label ?? humanize(result.status)}
                    </span>
                    <div>
                      {result.compared_variables.length === 0 && <span>None reported</span>}
                      {result.compared_variables.map((item) => (
                        <span key={item.variable}>
                          <Tag tone={item.comparable ? 'good' : 'bad'}>
                            {item.comparable ? 'Comparable' : 'Not comparable'}
                          </Tag>{' '}
                          <b>{humanize(item.variable)}</b>
                          {item.unit ? ` (${item.unit})` : ''} — {item.reason}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="comparison-summary-row">
                    <strong>Findings</strong>
                    <span>{result.findings.length ? `${result.findings.length} reported` : 'None reported'}</span>
                    <div>
                      {result.findings.map((finding) => (
                        <span key={finding}>{finding}</span>
                      ))}
                    </div>
                  </div>

                  <div className="comparison-summary-row">
                    <strong>Source IDs</strong>
                    <span>{result.source_ids.length} referenced</span>
                    <div>
                      <span>{result.source_ids.join(', ') || 'None'}</span>
                    </div>
                  </div>
                </>
              )}

              {FIELD_ROWS.map(([label, getValue]) => {
                const values = selected.map((experiment) =>
                  displayValue(getValue(experiment))
                )
                const different = new Set(values).size > 1

                return (
                  <div className="comparison-summary-row" key={label}>
                    <strong>{label}</strong>

                    <span className={different ? 'is-different' : ''}>
                      {different ? 'Values differ' : 'Same available value'}
                    </span>

                    <div>
                      {selected.map((experiment, index) => (
                        <span key={getExperimentId(experiment)}>
                          <b style={{ color: getColor(index) }}>
                            {getExperimentId(experiment)}:
                          </b>{' '}
                          {displayValue(getValue(experiment))}
                        </span>
                      ))}
                    </div>
                  </div>
                )
              })}
            </section>
          )}

          <MockNotice />
        </>
      )}
    </main>
  )
}
