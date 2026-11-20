import {
  useEffect,
  useMemo,
  useState,
  type CSSProperties,
  type FormEvent,
} from 'react'
import {
  BrainCircuit,
  FileText,
  ChevronRight,
  Flame,
  Database,
  ShieldCheck,
  Sparkles,
  AlertTriangle,
  X,
  ExternalLink,
  Activity,
} from 'lucide-react'
import StateNotice from '../components/ui/StateNotice'
import Tag, { type TagTone } from '../components/ui/Tag'
import { USE_MOCK } from '../config/env'
import { QUICK_QUESTIONS } from '../data/quickQuestions'
import { useAsyncData } from '../hooks/useAsyncData'
import { askAssistant } from '../services/api'
import type { EvidenceStatus, Insight, SupportingEvidence } from '../types/schemas'
import { formatRange, humanize } from '../utils/format'
import '../styles/AIInsights.css'

const EVIDENCE_TAG: Record<string, { label: string; tone: TagTone }> = {
  supported: { label: 'Evidence supported', tone: 'good' },
  partially_supported: { label: 'Partially supported', tone: 'warn' },
  insufficient_evidence: { label: 'Insufficient evidence', tone: 'bad' },
}

function useDebounced<T>(value: T, delay = 400): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

function EvidenceCard({
  evidence,
  title,
  onClick,
}: {
  evidence: SupportingEvidence
  title: string
  onClick: () => void
}) {
  const body = (
    <>
      <span className="ai-evidence-icon">
        <FileText size={19} />
      </span>

      <span className="ai-evidence-copy">
        <strong>
          {evidence.source_id || 'Source'} · {evidence.experiment_id || 'Experiment'}
        </strong>
        <small>{evidence.evidence_text || title}</small>
      </span>

      {evidence.url ? (
        <ExternalLink className="ai-evidence-arrow" size={17} />
      ) : (
        <ChevronRight className="ai-evidence-arrow" size={17} />
      )}
    </>
  )

  if (evidence.url) {
    return (
      <a className="ai-evidence-item" href={evidence.url} target="_blank" rel="noreferrer">
        {body}
      </a>
    )
  }

  return (
    <button type="button" className="ai-evidence-item" onClick={onClick} aria-label={`View ${title}`}>
      {body}
    </button>
  )
}

function ExperimentDetails({ experiment, onClose }) {
  if (!experiment) return null

  return (
    <div
      className="ai-modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <section
        className="ai-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ai-modal-title"
      >
        <div className="ai-modal-header">
          <div>
            <span className="ai-eyebrow">EXPERIMENT DETAILS</span>
            <h2 id="ai-modal-title">
              {experiment.title || 'Untitled experiment'}
            </h2>
          </div>

          <button
            type="button"
            className="ai-icon-button"
            onClick={onClose}
            aria-label="Close experiment details"
          >
            <X size={20} />
          </button>
        </div>

        <div className="ai-detail-grid">
          <div>
            <span>Experiment ID</span>
            <strong>{experiment.id || 'Not available'}</strong>
          </div>
          <div>
            <span>Fuel</span>
            <strong>{experiment.fuel || 'Not available'}</strong>
          </div>
          <div>
            <span>Temperature</span>
            <strong>{formatRange(experiment.temperatureMin, experiment.temperatureMax, 'K')}</strong>
          </div>
          <div>
            <span>Pressure</span>
            <strong>{formatRange(experiment.pressure, experiment.pressureMax, 'atm')}</strong>
          </div>
          <div>
            <span>Platform</span>
            <strong>{experiment.platform || 'Not available'}</strong>
          </div>
          <div>
            <span>Data status</span>
            <strong>{experiment.status || 'Not available'}</strong>
          </div>
        </div>

        <div className="ai-detail-summary">
          <h3>Record Summary</h3>
          <p>
            {experiment.summary ||
              'No summary is available for this experiment record.'}
          </p>
          <p>
            <strong>Source:</strong> {experiment.source || 'Not provided'}
          </p>
        </div>
      </section>
    </div>
  )
}

export default function AIInsights({
  experiments = [],
  globalSearch = '',
  setPage,
  setSelected,
}: any) {
  const [activeQuestion, setActiveQuestion] = useState('differences')
  const [customQuestion, setCustomQuestion] = useState('')
  const [submittedCustomQuestion, setSubmittedCustomQuestion] = useState('')
  const [selectedExperiment, setSelectedExperiment] = useState(null)
  const [showSupportingData, setShowSupportingData] = useState(false)
  const [showRelatedExperiments, setShowRelatedExperiments] = useState(false)

  const visibleExperiments = useMemo(() => {
    const query = globalSearch.trim().toLowerCase()

    if (!query) return experiments

    return experiments.filter((experiment) =>
      [
        experiment.id,
        experiment.title,
        experiment.fuel,
        experiment.category,
        experiment.source,
        experiment.summary,
        experiment.status,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
        .includes(query),
    )
  }, [experiments, globalSearch])

  const activeQuestionLabel =
    activeQuestion === 'custom'
      ? submittedCustomQuestion
      : QUICK_QUESTIONS.find((question) => question.id === activeQuestion)?.label ||
        QUICK_QUESTIONS[0].label

  // POST /api/v1/assistant/ask  ->  AI / RAG Insight schema
  const scopeKey = useDebounced(visibleExperiments.map((e) => e.id).join('|'))
  const canAskCustom =
    customQuestion.trim().length >= 3 && scopeKey !== ''

  function handleCustomQuestionSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canAskCustom) return

    setSubmittedCustomQuestion(customQuestion.trim())
    setActiveQuestion('custom')
    setShowSupportingData(false)
    setShowRelatedExperiments(false)
  }

  const insightState = useAsyncData<Insight>(
    (signal) =>
      askAssistant({ question: activeQuestionLabel, experiment_ids: scopeKey.split('|') }, signal),
    [activeQuestionLabel, scopeKey],
    scopeKey !== '',
  )
  const insight = insightState.data

  // Share of in-scope experiments that list a source_id AND have at least one measurement.
  const completeness = visibleExperiments.length
    ? Math.round(
        (visibleExperiments.filter((e) => e.sourceIds.length > 0 && e.measurements.length > 0).length /
          visibleExperiments.length) *
          100,
      )
    : 0

  const findExperiment = (id: string) => experiments.find((e) => e.id === id)

  function handleRelatedExperiment(experiment) {
    if (!experiment) return
    setSelectedExperiment(experiment)

    if (typeof setSelected === 'function') {
      setSelected(experiment)
    }
  }

  function handleViewAllExperiments() {
    if (typeof setPage === 'function') {
      setPage('Explorer')
    }
  }

  const evidenceTag = insight ? EVIDENCE_TAG[insight.evidence_status as EvidenceStatus] : undefined

  return (
    <main className="ai-insights-page">
      <header className="ai-page-heading">
        <div>
          <div className="ai-title-row">
            <span className="ai-title-icon">
              <BrainCircuit size={23} />
            </span>
            <h1>AI Insights</h1>
          </div>
          <p>
            Get AI-powered explanations, key findings, and recommendations.
          </p>
        </div>

        <div className="ai-heading-badge">
          <span className="ai-live-dot" />
          {USE_MOCK ? 'Mock Analysis' : 'Evidence-backed'}
        </div>
      </header>

      {globalSearch.trim() && (
        <div className="ai-search-notice">
          <SearchIcon />
          <span>
            Search results for <strong>“{globalSearch}”</strong> ·{' '}
            {visibleExperiments.length} record(s) found
          </span>
        </div>
      )}

      <div className="ai-insights-grid">
        {/* LEFT COLUMN: QUICK QUESTIONS */}
        <aside className="ai-panel ai-questions-panel">
          <div className="ai-panel-heading">
            <h2>Quick Questions</h2>
            <span>{QUICK_QUESTIONS.length}</span>
          </div>

          <div className="ai-question-list">
            {QUICK_QUESTIONS.map((question, index) => (
              <button
                type="button"
                key={question.id}
                className={`ai-question-card ${
                  activeQuestion === question.id ? 'is-active' : ''
                }`}
                onClick={() => {
                  setActiveQuestion(question.id)
                  setShowSupportingData(false)
                  setShowRelatedExperiments(false)
                }}
                aria-pressed={activeQuestion === question.id}
              >
                <span className="ai-question-number">
                  {String(index + 1).padStart(2, '0')}
                </span>

                <span className="ai-question-text">{question.label}</span>

                <ChevronRight
                  className="ai-question-arrow"
                  size={18}
                />
              </button>
            ))}
          </div>

          <form
            className="ai-custom-question"
            onSubmit={handleCustomQuestionSubmit}
          >
            <label htmlFor="ai-custom-question-input">
              Write your own question
            </label>
            <textarea
              id="ai-custom-question-input"
              value={customQuestion}
              onChange={(event) => setCustomQuestion(event.target.value)}
              placeholder="Ask about the selected experiments..."
              rows={3}
              minLength={3}
              maxLength={1000}
              required
            />
            <button
              className="ai-action-button"
              type="submit"
              disabled={!canAskCustom}
            >
              <Sparkles size={15} />
              Ask question
            </button>
          </form>

          <div className="ai-question-footer">
            <Sparkles size={17} />
            <p>Choose a preset or write your own question about the available data.</p>
          </div>
        </aside>

        {/* CENTER COLUMN: ANALYSIS */}
        <section className="ai-panel ai-analysis-panel">
          <div className="ai-panel-heading ai-analysis-heading">
            <div className="ai-analysis-brand">
              <span className="ai-brain-icon">
                <BrainCircuit size={20} />
              </span>
              <div>
                <h2>AI Analysis</h2>
                <span>Evidence-linked insight</span>
              </div>
            </div>

            <span className="ai-mock-tag">{USE_MOCK ? 'MOCK' : 'RAG'}</span>
          </div>

          <div className="ai-selected-question">
            <span className="ai-selected-question-icon">
              <Sparkles size={17} />
            </span>
            <p>{activeQuestionLabel}</p>
            <ChevronRight size={19} />
          </div>

          {scopeKey === '' && (
            <StateNotice
              kind="empty"
              title="No experiment records in scope"
              message={
                globalSearch.trim()
                  ? 'No records match the current search. Clear the search to ask a question.'
                  : 'Load experiment records to ask a question.'
              }
            />
          )}

          {scopeKey !== '' && insightState.status === 'loading' && (
            <StateNotice kind="loading" title="Retrieving evidence…" />
          )}

          {insightState.status === 'error' && (
            <StateNotice
              kind="error"
              title="Could not get an answer"
              message={insightState.error}
              onRetry={insightState.reload}
            />
          )}

          {insight && insightState.status === 'success' && (
            <>
              <div className="schema-meta-row">
                {evidenceTag && <Tag tone={evidenceTag.tone}>{evidenceTag.label}</Tag>}
                <Tag tone="info">Confidence: {humanize(insight.confidence)}</Tag>
                <Tag tone="info">{insight.insight_id}</Tag>
              </div>

              {insight.evidence_status === 'insufficient_evidence' && (
                <div className="schema-banner is-partial" role="status">
                  <AlertTriangle size={17} />
                  <span>
                    The assistant did not find indexed evidence that supports this question, so it
                    makes no claim beyond what is stated below.
                  </span>
                </div>
              )}

              <div className="ai-answer">
                <p className="ai-answer-intro">{insight.claim}</p>

                {insight.supporting_evidence.length > 0 ? (
                  <ol className="ai-answer-list">
                    {insight.supporting_evidence.map((item, index) => (
                      <li key={`${activeQuestion}-${index}`}>
                        <span className="ai-answer-index">{index + 1}</span>
                        <span>
                          <strong>
                            {item.source_id} · {item.experiment_id}:
                          </strong>{' '}
                          {item.evidence_text}
                        </span>
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="ai-empty-state">No supporting evidence was returned for this answer.</p>
                )}
              </div>

              <div className="ai-key-insight">
                <div className="ai-key-insight-icon">
                  <AlertTriangle size={20} />
                </div>
                <div>
                  <h3>Fire-Safety Relevance</h3>
                  <p>{insight.fire_safety_relevance || 'Not provided.'}</p>
                </div>
              </div>

              {insight.limitations.length > 0 && (
                <div className="schema-block">
                  <div className="schema-block-title">
                    <strong>Limitations</strong>
                  </div>
                  <ul className="schema-list">
                    {insight.limitations.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          <div className="ai-analysis-actions">
            <button
              type="button"
              className={`ai-action-button ${
                showSupportingData ? 'is-selected' : ''
              }`}
              onClick={() => setShowSupportingData((current) => !current)}
              aria-expanded={showSupportingData}
            >
              <Database size={16} />
              {showSupportingData ? 'Hide Supporting Data' : 'View Supporting Data'}
            </button>

            <button
              type="button"
              className={`ai-action-button ${
                showRelatedExperiments ? 'is-selected' : ''
              }`}
              onClick={() =>
                setShowRelatedExperiments((current) => !current)
              }
              aria-expanded={showRelatedExperiments}
            >
              <ExternalLink size={16} />
              {showRelatedExperiments
                ? 'Hide Related Experiments'
                : 'Show Related Experiments'}
            </button>
          </div>

          {showSupportingData && (
            <section className="ai-expanded-section">
              <div className="ai-expanded-heading">
                <Database size={17} />
                <h3>Supporting Data</h3>
              </div>

              <p className="ai-expanded-description">
                Values shown below come from the currently available records.
              </p>

              {visibleExperiments.length ? (
                <div className="ai-data-table-wrap">
                  <table className="ai-data-table">
                    <thead>
                      <tr>
                        <th>Experiment</th>
                        <th>Fuel</th>
                        <th>Temperature</th>
                        <th>Pressure</th>
                        <th>Validation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visibleExperiments.map((experiment, index) => (
                        <tr key={experiment.id || index}>
                          <td>{experiment.id || '—'}</td>
                          <td>{experiment.fuel || '—'}</td>
                          <td>{formatRange(experiment.temperatureMin, experiment.temperatureMax, 'K')}</td>
                          <td>{formatRange(experiment.pressure, experiment.pressureMax, 'atm')}</td>
                          <td>
                            {experiment.analysis
                              ? experiment.analysis.data_quality.validation_passed
                                ? 'Passed'
                                : 'Failed'
                              : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="ai-empty-state">
                  No records match the current search.
                </p>
              )}
            </section>
          )}

          {showRelatedExperiments && (
            <section className="ai-expanded-section">
              <div className="ai-expanded-heading">
                <Activity size={17} />
                <h3>Related Experiments</h3>
              </div>

              <div className="ai-related-list">
                {visibleExperiments.length ? (
                  visibleExperiments.map((experiment, index) => (
                    <button
                      type="button"
                      className="ai-related-item"
                      key={experiment.id || index}
                      onClick={() => handleRelatedExperiment(experiment)}
                    >
                      <span className="ai-related-flame">
                        <Flame size={17} />
                      </span>
                      <span>
                        <strong>
                          {experiment.id || 'Experiment'} ·{' '}
                          {experiment.title || 'Untitled experiment'}
                        </strong>
                        <small>
                          {experiment.fuel || 'Fuel not specified'} ·{' '}
                          {formatRange(experiment.temperatureMin, experiment.temperatureMax, 'K')}
                        </small>
                      </span>
                      <ChevronRight size={17} />
                    </button>
                  ))
                ) : (
                  <p className="ai-empty-state">
                    No related records were found.
                  </p>
                )}
              </div>
            </section>
          )}
        </section>

        {/* RIGHT COLUMN: EVIDENCE AND COMPLETENESS */}
        <aside className="ai-panel ai-evidence-panel">
          <div className="ai-panel-heading">
            <h2>Evidence References</h2>
            <span>{insight?.supporting_evidence.length ?? 0}</span>
          </div>

          <div className="ai-evidence-list">
            {insight && insight.supporting_evidence.length > 0 ? (
              insight.supporting_evidence.map((item, index) => (
                <EvidenceCard
                  key={`${item.source_id}-${item.experiment_id}-${index}`}
                  evidence={item}
                  title={item.experiment_id}
                  onClick={() => handleRelatedExperiment(findExperiment(item.experiment_id))}
                />
              ))
            ) : (
              <p className="ai-empty-state">
                {insightState.status === 'loading'
                  ? 'Retrieving evidence…'
                  : 'No evidence references were returned for this question.'}
              </p>
            )}
          </div>

          <div className="ai-evidence-divider" />

          <section className="ai-confidence-section">
            <div className="ai-confidence-heading">
              <h3>Data Completeness</h3>
              <span>
                <ShieldCheck size={16} />
                Dataset
              </span>
            </div>

            <div
              className="ai-confidence-ring"
              style={{ '--confidence-value': `${completeness}%` } as CSSProperties}
              role="img"
              aria-label={`Dataset completeness indicator: ${completeness}%`}
            >
              <div className="ai-confidence-inner">
                <strong>{completeness}%</strong>
                <span>Completeness</span>
              </div>
            </div>

            <p className="ai-confidence-note">
              Share of experiments in scope that list a source and have at least one measurement.
              It is not an AI confidence score; the insight&apos;s own confidence is shown with the
              answer. Verify scientific claims against original sources.
            </p>
          </section>

          <div className="ai-source-note">
            <ShieldCheck size={18} />
            <p>
              <strong>Evidence first</strong>
              <span>
                Results should be checked against the original experiment
                sources.
              </span>
            </p>
          </div>

          <button
            type="button"
            className="ai-view-all-button"
            onClick={handleViewAllExperiments}
          >
            Explore Experiments
            <ChevronRight size={17} />
          </button>
        </aside>
      </div>

      <footer className="ai-page-footer">
        <span>
          <span className="ai-footer-dot" />
          {USE_MOCK ? 'Prototype · Mock analysis' : 'Evidence-backed insights'}
        </span>
        <span>NASA-themed hackathon project</span>
      </footer>

      <ExperimentDetails
        experiment={selectedExperiment}
        onClose={() => setSelectedExperiment(null)}
      />
    </main>
  )
}

function SearchIcon() {
  return <Database size={16} aria-hidden="true" />
}
