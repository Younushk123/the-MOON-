
import { useState } from 'react'
import Sidebar from './components/layout/Sidebar.tsx'
import Topbar from './components/layout/Topbar.tsx'
import Overview from './pages/Overview'
import Explorer from './pages/Explorer.tsx'
import Comparison from './pages/Comparison.tsx'
import AIInsights from './pages/AIInsights.tsx'
import ComputerVision from './pages/ComputerVision.tsx'
import DataQuality from './pages/DataQuality.tsx'
import Details from './pages/Details.tsx'
import Settings from './pages/Settings.tsx'
import { useDashboardData } from './hooks/useDashboardData'
import { useAsyncData } from './hooks/useAsyncData'
import { getHealth } from './services/api'
import { USE_MOCK } from './config/env'
import StateNotice from './components/ui/StateNotice'
import { Atom } from 'lucide-react'

export default function App() {
  const [page, setPage] = useState('Overview')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  function navigate(next) {
    setPage(next)
    setIsMobileOpen(false)
  }

  const {
    status,
    error,
    experiments,
    analyses,
    sources,
    sourcesProvided,
    enriching,
    warnings,
    reload,
  } = useDashboardData()
  const loading = status === 'loading'

  // GET /api/v1/health — only shown in the footer; never blocks the UI.
  const health = useAsyncData((signal) => getHealth(signal), [])

  let content

  if (loading) {
    content = (
      <div className="loading-state">
        <Atom size={28} />
        <p>Loading experiment records…</p>
      </div>
    )
  } else if (error) {
    content = (
      <div className="page">
        <StateNotice
          kind="error"
          title="Could not load experiment records"
          message={error}
          onRetry={reload}
        />
      </div>
    )
  } else {
    switch (page) {
      case 'Explorer':
        content = (
          <Explorer
            experiments={experiments}
            globalSearch={search}
            setPage={navigate}
            setSelected={setSelected}
          />
        )
        break

      case 'Details':
        content = (
          <Details
            experiment={selected}
            sources={sources}
            sourcesProvided={sourcesProvided}
            setPage={navigate}
          />
        )
        break

      case 'Comparison':
        content = <Comparison experiments={experiments} />
        break

      case 'AI Insights':
        content = (
          <AIInsights
            experiments={experiments}
            globalSearch={search}
            setPage={navigate}
            setSelected={setSelected}
          />
        )
        break

      case 'Computer Vision':
        content = <ComputerVision />
        break

      case 'Data Quality':
        content = (
          <DataQuality
            experiments={experiments}
            analyses={analyses}
            sources={sources}
            sourcesProvided={sourcesProvided}
            onRefresh={reload}
            refreshing={enriching}
          />
        )
        break

      case 'Settings':
        content = <Settings />
        break

      default:
        content = (
          <Overview
            experiments={experiments}
            analyses={analyses}
            setPage={navigate}
            setSelected={setSelected}
          />
        )
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        page={page}
        setPage={navigate}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />

      <div className="main-column">
        <Topbar
          search={search}
          setSearch={setSearch}
          setIsMobileOpen={setIsMobileOpen}
        />

        {warnings.length > 0 && (
          <div className="schema-top-warning error-box" role="status">
            {warnings.join(' ')}
          </div>
        )}

        <main>{content}</main>

        <footer className="app-footer">
          <span>THE MOON · Flame in Freefall</span>

          <span>
            {USE_MOCK
              ? 'Mock data prototype · Not official NASA findings'
              : health.status === 'success'
                ? 'Connected to API v1'
                : health.status === 'error'
                  ? 'API health check failed'
                  : 'Checking API…'}
          </span>
        </footer>
      </div>
    </div>
  )
}
