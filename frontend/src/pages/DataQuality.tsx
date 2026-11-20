import { useMemo, useState } from 'react'
import {
  Database,
  FileText,
  BookOpen,
  Check,
  CircleAlert,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  X,
  LoaderCircle,
  AlertTriangle,
} from 'lucide-react'
import StateNotice from '../components/ui/StateNotice'
import MockNotice from '../components/ui/MockNotice'
import { USE_MOCK } from '../config/env'
import type { AnalysisResult, Source } from '../types/schemas'
import { humanize } from '../utils/format'
import '../styles/DataQuality.css'


const QUALITY_CRITERIA = [
  {
    id: 'completeness',
    label: 'Data completeness',
    description: 'Every experiment has an analysis result with data_quality.missing_values = 0.',
  },
  {
    id: 'credibility',
    label: 'Source credibility',
    description: 'Every experiment lists at least one source_id.',
  },
  {
    id: 'consistency',
    label: 'Format consistency',
    description: 'Every analysis reports data_quality.validation_passed = true.',
  },
  {
    id: 'validity',
    label: 'Scientific validity',
    description: 'Requires verification against original scientific sources.',
  },
  {
    id: 'traceability',
    label: 'Traceability',
    description: 'Every analysis result references at least one source_id.',
  },
]


const STATUS_CONFIG = [
  { id: 'validated', label: 'Validation passed', color: '#27c9e7' },
  { id: 'under-review', label: 'Passed with warnings', color: '#f2b65d' },
  { id: 'incomplete', label: 'Failed / missing values', color: '#ef7777' },
  { id: 'unknown', label: 'No analysis', color: '#668ac0' },
]

function categorize(analysis: AnalysisResult | null) {
  if (!analysis) return 'unknown'
  const quality = analysis.data_quality
  if (!quality || !quality.validation_passed || quality.missing_values > 0) return 'incomplete'
  if (quality.warnings.length > 0) return 'under-review'
  return 'validated'
}

function calculateQuality(experiments) {
  const total = experiments.length
  const counts = { validated: 0, 'under-review': 0, incomplete: 0, unknown: 0 }
  experiments.forEach((experiment) => {
    counts[categorize(experiment.analysis)] += 1
  })

  const percentages = {}
  Object.keys(counts).forEach((status) => {
    percentages[status] = total ? Math.round((counts[status] / total) * 100) : 0
  })


  const analysed = experiments.filter((item) => item.analysis)
  const passed = analysed.filter((item) => item.analysis.data_quality?.validation_passed).length

  return {
    total,
    analysed: analysed.length,
    overall: analysed.length ? Math.round((passed / analysed.length) * 100) : null,
    counts,
    percentages,
  }
}

function calculateCriteria(experiments) {
  if (!experiments.length) {
    return QUALITY_CRITERIA.map((criterion) => ({ ...criterion, passed: false, available: false }))
  }

  const analysed = experiments.filter((item) => item.analysis)
  const hasAnalyses = analysed.length > 0

  const completeness =
    analysed.length === experiments.length &&
    analysed.every((item) => item.analysis.data_quality.missing_values === 0)
  const credibility = experiments.every((item) => item.sourceIds.length > 0)
  const consistency =
    hasAnalyses && analysed.every((item) => item.analysis.data_quality.validation_passed)
  const traceability =
    hasAnalyses && analysed.every((item) => item.analysis.source_ids.length > 0)

  return QUALITY_CRITERIA.map((criterion) => {
    switch (criterion.id) {
      case 'completeness':
        return { ...criterion, passed: completeness, available: hasAnalyses }
      case 'credibility':
        return { ...criterion, passed: credibility, available: true }
      case 'consistency':
        return { ...criterion, passed: consistency, available: hasAnalyses }
      case 'traceability':
        return { ...criterion, passed: traceability, available: hasAnalyses }
      default:
      
        return { ...criterion, passed: false, available: false }
    }
  })
}


function buildSourceCards(sources: Source[], experiments) {
  const known = new Set(sources.map((s) => s.source_id))
  const cards = sources.map((s) => ({
    id: s.source_id,
    name: s.title,
    description: `${s.publisher} · ${humanize(s.source_type)} · ${humanize(s.ingestion_status)}`,
    category: humanize(s.verification_status),
    primary: s.verification_status !== 'unverified',
    icon: s.source_type === 'dataset' ? 'nasa' : s.source_type === 'research_paper' ? 'research' : 'literature',
    url: s.url,
  }))
  const unresolved = [...new Set(experiments.flatMap((e) => e.sourceIds))].filter((id: string) => !known.has(id))
  unresolved.forEach((id: string) =>
    cards.push({
      id,
      name: id,
      description: 'Source record not provided by the API',
      category: 'Unknown',
      primary: false,
      icon: 'research',
      url: null,
    }),
  )
  return cards
}

function getSourceIcon(icon) {
  if (icon === 'nasa') return <Database size={25} />
  if (icon === 'literature') return <BookOpen size={25} />
  return <FileText size={25} />
}

function SourceCard({ source }) {
  const content = (
    <>
      <span className={`dq-source-icon dq-source-icon-${source.icon || 'research'}`}>
        {getSourceIcon(source.icon)}
      </span>

      <span className="dq-source-copy">
        <strong>{source.name || 'Unnamed source'}</strong>
        <small>
          {source.description ||
            source.type ||
            'No source description available'}
        </small>
      </span>

      <span
        className={`dq-source-badge ${
          source.primary ? 'is-primary' : 'is-secondary'
        }`}
      >
        {source.category || 'Other'}
      </span>

      {source.url && <ExternalLink className="dq-source-external" size={16} />}
    </>
  )

  if (source.url) {
    return (
      <a
        className="dq-source-card"
        href={source.url}
        target="_blank"
        rel="noreferrer"
      >
        {content}
      </a>
    )
  }

  return <div className="dq-source-card">{content}</div>
}

function QualityChart({ quality }) {
  const segments = STATUS_CONFIG.map((status) => ({
    ...status,
    percentage: quality.percentages[status.id] || 0,
  }))

  let cursor = 0

  const gradient = segments
    .map((segment) => {
      const start = cursor
      cursor += segment.percentage
      return `${segment.color} ${start}% ${cursor}%`
    })
    .join(', ')

  return (
    <div className="dq-chart-layout">
      <div
        className="dq-donut"
        style={{
          '--dq-donut-gradient': gradient || '#1a3656 0% 100%',
        }}
        role="img"
        aria-label={`Validation pass rate ${quality.overall ?? 'not available'} percent`}
      >
        <div className="dq-donut-inner">
          <strong>{quality.overall == null ? '—' : `${quality.overall}%`}</strong>
          <span>Validation Pass Rate</span>
        </div>
      </div>

      <div className="dq-legend">
        {segments.map((segment) => (
          <div className="dq-legend-row" key={segment.id}>
            <span
              className="dq-legend-dot"
              style={{ background: segment.color }}
            />
            <span className="dq-legend-label">{segment.label}</span>
            <strong>{segment.percentage}%</strong>
          </div>
        ))}
      </div>
    </div>
  )
}

function DetailedReport({ quality, criteria, experiments, onClose }) {
  return (
    <div
      className="dq-modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <section
        className="dq-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dq-report-title"
      >
        <header className="dq-modal-header">
          <div>
            <span className="dq-eyebrow">DATA QUALITY</span>
            <h2 id="dq-report-title">Detailed Quality Report</h2>
          </div>

          <button
            type="button"
            className="dq-close-button"
            onClick={onClose}
            aria-label="Close report"
          >
            <X size={19} />
          </button>
        </header>

        <div className="dq-report-summary">
          <div>
            <span>Experiment records</span>
            <strong>{quality.total}</strong>
          </div>
          <div>
            <span>Validation pass rate</span>
            <strong>{quality.overall == null ? '—' : `${quality.overall}%`}</strong>
          </div>
        </div>

        <h3 className="dq-report-subheading">Quality Criteria</h3>

        <div className="dq-report-list">
          {criteria.map((criterion) => (
            <div className="dq-report-item" key={criterion.id}>
              <span
                className={`dq-report-status ${
                  criterion.passed
                    ? 'is-passed'
                    : criterion.available
                      ? 'is-warning'
                      : 'is-unknown'
                }`}
              >
                {criterion.passed ? (
                  <Check size={15} />
                ) : (
                  <CircleAlert size={15} />
                )}
              </span>

              <div>
                <strong>{criterion.label}</strong>
                <p>{criterion.description}</p>
                <small>
                  {!criterion.available
                    ? 'Requires manual/source verification'
                    : criterion.passed
                      ? 'All records pass this basic check'
                      : 'Some records need review'}
                </small>
              </div>
            </div>
          ))}
        </div>

        <h3 className="dq-report-subheading">Analysis Warnings & Limitations</h3>

        <div className="dq-report-list">
          {experiments.filter((e) => e.analysis).length === 0 && (
            <p className="dq-empty-state">No analysis results are available.</p>
          )}
          {experiments
            .filter((e) => e.analysis)
            .map((e) => (
              <div className="dq-report-item" key={e.id}>
                <span
                  className={`dq-report-status ${
                    e.analysis.data_quality.validation_passed ? 'is-passed' : 'is-warning'
                  }`}
                >
                  {e.analysis.data_quality.validation_passed ? <Check size={15} /> : <CircleAlert size={15} />}
                </span>
                <div>
                  <strong>
                    {e.id} · {e.analysis.analysis_id}
                  </strong>
                  <p>
                    Missing values: {e.analysis.data_quality.missing_values} · Validation{' '}
                    {e.analysis.data_quality.validation_passed ? 'passed' : 'failed'}
                  </p>
                  {[...e.analysis.data_quality.warnings, ...e.analysis.limitations].map((item) => (
                    <small key={item}>{item}</small>
                  ))}
                </div>
              </div>
            ))}
        </div>

        <p className="dq-report-disclaimer">
          This report summarises the analysis results and data_quality fields returned for each experiment. It does not
          independently verify scientific accuracy or replace source review.
        </p>

        <button
          type="button"
          className="dq-report-done"
          onClick={onClose}
        >
          Close Report
        </button>
      </section>
    </div>
  )
}

export default function DataQuality({
  experiments = [],
  sources = [],
  sourcesProvided = false,
  onRefresh,
  refreshing = false,
}: any) {
  const [showReport, setShowReport] = useState(false)

  const sourceList = useMemo(() => buildSourceCards(sources, experiments), [sources, experiments])
  const quality = useMemo(() => calculateQuality(experiments), [experiments])
  const criteria = useMemo(() => calculateCriteria(experiments), [experiments])

  const loading = refreshing
  const displayQuality = quality
  const displayCounts = quality.counts
  const chartQuality = quality

  return (
    <main className="data-quality-page">
      <header className="dq-page-heading">
        <div>
          <h1>Data Sources and Data Quality</h1>
          <p>
            Understand where the data comes from and how reliable it is.
          </p>
        </div>

        <button
          type="button"
          className="dq-refresh-button"
          onClick={() => onRefresh?.()}
          disabled={!onRefresh || loading}
          title="Reload experiments, measurements and analysis results"
          
        >
          {loading ? (
            <LoaderCircle className="dq-spin" size={16} />
          ) : (
            <RefreshCw size={16} />
          )}
          <span>{loading ? 'Refreshing' : 'Refresh Data'}</span>
        </button>
      </header>

      {USE_MOCK && (
        <div className="dq-mode-notice">
          <Database size={16} />
          <span>
            <strong>Demo mode:</strong> source cards and analysis results come from the mock
            backend. They are synthetic and not NASA findings.
          </span>
        </div>
      )}

      {!USE_MOCK && !sourcesProvided && (
        <div className="dq-mode-notice">
          <Database size={16} />
          <span>
            <strong>Source records unavailable:</strong> the API contract has no endpoint that
            returns Source objects yet, so only source IDs referenced by experiments are listed.
          </span>
        </div>
      )}

      <div className="dq-main-grid">
        {/* DATA SOURCES */}
        <section className="dq-panel dq-sources-panel">
          <div className="dq-panel-heading">
            <div>
              <span className="dq-panel-kicker">SOURCE DIRECTORY</span>
              <h2>Data Sources</h2>
            </div>
            <span className="dq-count-badge">{sourceList.length}</span>
          </div>

          <div className="dq-source-list">
            {sourceList.length ? (
              sourceList.map((source, index) => (
                <SourceCard
                  source={{
                    ...source,
                    icon:
                      source.icon ||
                      (index === 0
                        ? 'nasa'
                        : index === 2
                          ? 'literature'
                          : 'research'),
                  }}
                  key={source.id || source.name || index}
                />
              ))
            ) : (
              <p className="dq-empty-state">
                No data sources have been provided.
              </p>
            )}
          </div>

          <div className="dq-source-footer">
            <span className="dq-footer-indicator" />
            <span>{sourceList.length} source record(s) available</span>
          </div>
        </section>

       
        <section className="dq-panel dq-overview-panel">
          <div className="dq-panel-heading">
            <div>
              <span className="dq-panel-kicker">DATASET HEALTH</span>
              <h2>Data Quality Overview</h2>
            </div>

            <span className="dq-status-pill">
              {loading ? 'Updating' : USE_MOCK ? 'Demo' : 'Live API'}
            </span>
          </div>

          {experiments.length ? (
            quality.analysed ? (
              <QualityChart quality={chartQuality} />
            ) : (
              <StateNotice
                kind={loading ? 'loading' : 'empty'}
                title={loading ? 'Running analysis…' : 'No analysis results yet'}
                message={
                  loading
                    ? undefined
                    : 'Data-quality figures come from POST /api/v1/analysis. None were returned.'
                }
              />
            )
          ) : (
            <div className="dq-no-data">
              <Database size={29} />
              <strong>No experiment records</strong>
              <p>
                Connect the experiment dataset to calculate quality metrics.
              </p>
            </div>
          )}

          <div className="dq-overview-footer">
            <div>
              <span>Experiment records</span>
              <strong>{quality.total}</strong>
            </div>
            <div>
              <span>Needs review</span>
              <strong>
                {(displayCounts['under-review'] || 0) +
                  (displayCounts.incomplete || 0) +
                  (displayCounts.unknown || 0)}
              </strong>
            </div>
          </div>
        </section>

        {/* QUALITY CRITERIA */}
        <section className="dq-panel dq-criteria-panel">
          <div className="dq-panel-heading">
            <div>
              <span className="dq-panel-kicker">VALIDATION CHECKLIST</span>
              <h2>Quality Criteria</h2>
            </div>
          </div>

          <div className="dq-criteria-list">
            {criteria.map((criterion) => (
              <div
                className="dq-criterion"
                key={criterion.id}
                title={criterion.description}
              >
                <span
                  className={`dq-criterion-icon ${
                    criterion.passed
                      ? 'is-passed'
                      : criterion.available
                        ? 'is-warning'
                        : 'is-unknown'
                  }`}
                >
                  {criterion.passed ? (
                    <Check size={16} />
                  ) : (
                    <CircleAlert size={16} />
                  )}
                </span>

                <span className="dq-criterion-label">
                  {criterion.label}
                </span>

                <span className="dq-criterion-state">
                  {!criterion.available
                    ? 'Check'
                    : criterion.passed
                      ? 'Pass'
                      : 'Review'}
                </span>
              </div>
            ))}
          </div>

          <div className="dq-criteria-note">
            <ShieldCheck size={18} />
            <p>
              <strong>Quality matters</strong>
              <span>
                Basic field checks cannot establish scientific validity on
                their own.
              </span>
            </p>
          </div>

          <button
            type="button"
            className="dq-report-button"
            onClick={() => setShowReport(true)}
          >
            <FileText size={17} />
            View Detailed Report
          </button>
        </section>
      </div>

      <footer className="dq-page-footer">
        <span>
          <span className="dq-footer-indicator" />
          Data quality monitoring
        </span>
        <span>Values depend on the available dataset</span>
        <MockNotice className="dq-mock-note" />
      </footer>

      {showReport && (
        <DetailedReport
          quality={displayQuality}
          criteria={criteria}
          experiments={experiments}
          onClose={() => setShowReport(false)}
        />
      )}
    </main>
  )
}