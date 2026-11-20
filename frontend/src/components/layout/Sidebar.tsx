
import {
  BarChart3,
  BrainCircuit,
  Database,
  ScanEye,
  House,
  Search,
  Settings,
  X,
} from 'lucide-react'

const nav = [
  ['Overview', 'Overview', House],
  ['Experiment Explorer', 'Explorer', Search],
  ['Comparison', 'Comparison', BarChart3],
  ['AI Insights', 'AI Insights', BrainCircuit],
  ['Data Sources', 'Data Quality', Database],
  ['Microgravity Flame Explorer', 'Computer Vision', ScanEye],
]

export default function Sidebar({
  page,
  setPage,
  isMobileOpen = false,
  setIsMobileOpen = () => {},
}) {
  const handleNavigation = (key) => {
    setPage(key)
    setIsMobileOpen(false)
  }

  return (
    <>
      {isMobileOpen && (
        <button
          className="sidebar-overlay"
          onClick={() => setIsMobileOpen(false)}
          aria-label="Close menu"
        />
      )}

      <aside
        className={`sidebar ${
          isMobileOpen ? 'mobile-sidebar-open' : ''
        }`}
      >
        <div className="brand">
          <div className="nasa-mark">NASA</div>

          <div>
            <strong>THE MOON</strong>
          </div>

          <button
            type="button"
            className="mobile-sidebar-close"
            onClick={() => setIsMobileOpen(false)}
            aria-label="Close menu"
          >
            <X size={22} />
          </button>
        </div>

        <nav>
          {nav.map(([label, key, Icon]) => (
            <button
              type="button"
              key={key}
              onClick={() => handleNavigation(key)}
              className={`nav-item ${
                page === key ? 'active' : ''
              }`}
            >
              <Icon size={17} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <button
          type="button"
          className={`nav-item settings-link ${
            page === 'Settings' ? 'active' : ''
          }`}
          onClick={() => handleNavigation('Settings')}
        >
          <Settings size={17} />
          <span>Settings</span>
        </button>

        <div className="sidebar-footer">
          Better data.
          <br />
          Safer space missions.
        </div>
      </aside>
    </>
  )
}